"""This file is forked from langgraph/prebuilt/react_agent_executor.py"""

import logging
from typing import Callable, Literal, Optional, Sequence, Type, TypeVar, Union, cast

import tiktoken
from langchain_core.language_models import BaseChatModel, LanguageModelLike
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import (
    Runnable,
    RunnableBinding,
    RunnableConfig,
)
from langchain_core.tools import BaseTool
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.store.base import BaseStore
from langgraph.types import Checkpointer
from langgraph.utils.runnable import RunnableCallable

from abstracts.graph import AgentState, MemoryManager

logger = logging.getLogger(__name__)

StateSchema = TypeVar("StateSchema", bound=AgentState)
StateSchemaType = Type[StateSchema]

STATE_MODIFIER_RUNNABLE_NAME = "StateModifier"

StateModifier = Union[
    SystemMessage,
    str,
    Callable[[StateSchema], Sequence[BaseMessage]],
    Runnable[StateSchema, Sequence[BaseMessage]],
]


def _get_state_modifier_runnable(
    state_modifier: Optional[StateModifier], store: Optional[BaseStore] = None
) -> Runnable:
    state_modifier_runnable: Runnable
    if state_modifier is None:
        state_modifier_runnable = RunnableCallable(
            lambda state: state["messages"], name=STATE_MODIFIER_RUNNABLE_NAME
        )
    elif isinstance(state_modifier, str):
        _system_message: BaseMessage = SystemMessage(content=state_modifier)
        state_modifier_runnable = RunnableCallable(
            lambda state: [_system_message] + state["messages"],
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif isinstance(state_modifier, SystemMessage):
        state_modifier_runnable = RunnableCallable(
            lambda state: [state_modifier] + state["messages"],
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif callable(state_modifier):
        state_modifier_runnable = RunnableCallable(
            state_modifier,
            name=STATE_MODIFIER_RUNNABLE_NAME,
        )
    elif isinstance(state_modifier, Runnable):
        state_modifier_runnable = state_modifier
    else:
        raise ValueError(
            f"Got unexpected type for `state_modifier`: {type(state_modifier)}"
        )

    return state_modifier_runnable


def _should_bind_tools(model: LanguageModelLike, tools: Sequence[BaseTool]) -> bool:
    if not isinstance(model, RunnableBinding):
        return True

    if "tools" not in model.kwargs:
        return True

    bound_tools = model.kwargs["tools"]
    if len(tools) != len(bound_tools):
        raise ValueError(
            "Number of tools in the model.bind_tools() and tools passed to create_react_agent must match"
        )

    tool_names = set(tool.name for tool in tools)
    bound_tool_names = set()
    for bound_tool in bound_tools:
        # OpenAI-style tool
        if bound_tool.get("type") == "function":
            bound_tool_name = bound_tool["function"]["name"]
        # Anthropic-style tool
        elif bound_tool.get("name"):
            bound_tool_name = bound_tool["name"]
        else:
            # unknown tool type so we'll ignore it
            continue

        bound_tool_names.add(bound_tool_name)

    if missing_tools := tool_names - bound_tool_names:
        raise ValueError(f"Missing tools '{missing_tools}' in the model.bind_tools()")

    return False


def _validate_chat_history(
    messages: Sequence[BaseMessage],
) -> None:
    """Validate that all tool calls in AIMessages have a corresponding ToolMessage."""
    all_tool_calls = [
        tool_call
        for message in messages
        if isinstance(message, AIMessage)
        for tool_call in message.tool_calls
    ]
    tool_call_ids_with_results = {
        message.tool_call_id for message in messages if isinstance(message, ToolMessage)
    }
    tool_calls_without_results = [
        tool_call
        for tool_call in all_tool_calls
        if tool_call["id"] not in tool_call_ids_with_results
    ]
    if not tool_calls_without_results:
        return

    error_message = create_error_message(
        message="Found AIMessages with tool_calls that do not have a corresponding ToolMessage. "
        f"Here are the first few of those tool calls: {tool_calls_without_results[:3]}.\n\n"
        "Every tool call (LLM requesting to call a tool) in the message history MUST have a corresponding ToolMessage "
        "(result of a tool invocation to return to the LLM) - this is required by most LLM providers.",
        error_code=ErrorCode.INVALID_CHAT_HISTORY,
    )
    raise ValueError(error_message)


# Cache for tiktoken encoders
_TIKTOKEN_CACHE = {}


def _get_encoder(model_name: str = "gpt-4"):
    """Get cached tiktoken encoder."""
    if model_name not in _TIKTOKEN_CACHE:
        try:
            _TIKTOKEN_CACHE[model_name] = tiktoken.encoding_for_model(model_name)
        except KeyError:
            _TIKTOKEN_CACHE[model_name] = tiktoken.get_encoding("cl100k_base")
    return _TIKTOKEN_CACHE[model_name]


def _count_tokens(messages: Sequence[BaseMessage], model_name: str = "gpt-4") -> int:
    """Count the number of tokens in a list of messages."""
    encoding = _get_encoder(model_name)

    num_tokens = 0
    for message in messages:
        # Every message follows <im_start>{role/name}\n{content}<im_end>\n
        num_tokens += 4

        # Count tokens for basic message attributes
        msg_dict = message.model_dump()
        for key in ["content", "name", "function_call", "role"]:
            value = msg_dict.get(key)
            if value:
                num_tokens += len(encoding.encode(str(value)))

        # Count tokens for tool calls more efficiently
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                # Only encode essential parts of tool_call
                if isinstance(tool_call, dict):
                    for key in ["name", "arguments"]:
                        if key in tool_call:
                            num_tokens += len(encoding.encode(str(tool_call[key])))
                else:
                    # Handle tool_call object if it's not a dict
                    num_tokens += len(encoding.encode(str(tool_call)))

    return num_tokens


def _limit_tokens(
    messages: list[BaseMessage], max_tokens: int = 120000
) -> list[BaseMessage]:
    """Limit the total number of tokens in messages by removing old messages.
    Also merges adjacent HumanMessages as some models don't allow consecutive user messages."""
    original_count = len(messages)
    logger.debug(f"Starting token limiting. Original message count: {original_count}")

    # First merge adjacent HumanMessages
    i = 0
    merge_count = 0
    while i < len(messages) - 1:
        if isinstance(messages[i], HumanMessage) and isinstance(
            messages[i + 1], HumanMessage
        ):
            # Handle different content types
            content1 = messages[i].content
            content2 = messages[i + 1].content

            # Convert to list if string, more memory efficient than always converting
            if not isinstance(content1, list):
                content1 = [content1]
            if not isinstance(content2, list):
                content2 = [content2]

            # Merge the contents
            messages[i].content = content1 + content2

            # Remove the second message
            messages.pop(i + 1)
            merge_count += 1
        else:
            i += 1

    if merge_count > 0:
        logger.debug(f"Merged {merge_count} adjacent human messages")

    token_count = _count_tokens(messages)
    logger.debug(f"Current token count: {token_count}, max allowed: {max_tokens}")

    if token_count <= max_tokens:
        return messages

    # Modify messages in-place instead of creating a copy
    i = 1
    removed_count = 0
    while i < len(messages) and _count_tokens(messages) > max_tokens:
        if not isinstance(messages[i], SystemMessage):
            messages.pop(i)
            removed_count += 1
        else:
            i += 1

    final_token_count = _count_tokens(messages)
    logger.info(
        f"Token limiting complete. Removed {removed_count} messages. "
        f"Final message count: {len(messages)}, "
        f"Final token count: {final_token_count}"
    )

    return messages


def _clean_history_on_error(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Clean message history after model error, keeping only system messages and the last user message."""
    # Keep all system messages
    result = [msg for msg in messages if isinstance(msg, SystemMessage)]
    
    # Find the last user message
    last_user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg
            break
    
    if last_user_msg:
        result.append(last_user_msg)
    
    logger.info(
        f"Cleaned message history after error. "
        f"Kept {len(result)} messages ({len([m for m in result if isinstance(m, SystemMessage)])} system, "
        f"{1 if last_user_msg else 0} user)"
    )
    
    return result


def create_agent(
    model: LanguageModelLike,
    tools: Union[ToolExecutor, Sequence[BaseTool], ToolNode],
    *,
    state_schema: Optional[StateSchemaType] = None,
    state_modifier: Optional[StateModifier] = None,
    memory_manager: Optional[MemoryManager] = None,
    checkpointer: Optional[Checkpointer] = None,
    store: Optional[BaseStore] = None,
    interrupt_before: Optional[list[str]] = None,
    interrupt_after: Optional[list[str]] = None,
    input_token_limit: int = 120000,
    debug: bool = False,
) -> CompiledGraph:
    """Creates a graph that works with a chat model that utilizes tool calling.

    Args:
        model: The `LangChain` chat model that supports tool calling.
        tools: A list of tools, a ToolExecutor, or a ToolNode instance.
            If an empty list is provided, the agent will consist of a single LLM node without tool calling.
        state_schema: An optional state schema that defines graph state.
            Must have `messages` and `is_last_step` keys.
            Defaults to `AgentState` that defines those two keys.
        state_modifier: An optional
            state modifier. This takes full graph state BEFORE the LLM is called and prepares the input to LLM.

            Can take a few different forms:

            - SystemMessage: this is added to the beginning of the list of messages in state["messages"].
            - str: This is converted to a SystemMessage and added to the beginning of the list of messages in state["messages"].
            - Callable: This function should take in full graph state and the output is then passed to the language model.
            - Runnable: This runnable should take in full graph state and the output is then passed to the language model.
        memory_manager: An optional memory manager. This is used for persisting the state of the graph (e.g., as chat memory)
        checkpointer: An optional checkpoint saver object. This is used for persisting
            the state of the graph (e.g., as chat memory) for a single thread (e.g., a single conversation).
        store: An optional store object. This is used for persisting data
            across multiple threads (e.g., multiple conversations / users).
        interrupt_before: An optional list of node names to interrupt before.
            Should be one of the following: "agent", "tools".
            This is useful if you want to add a user confirmation or other interrupt before taking an action.
        interrupt_after: An optional list of node names to interrupt after.
            Should be one of the following: "agent", "tools".
            This is useful if you want to return directly or run additional processing on an output.
        debug: A flag indicating whether to enable debug mode.

    Returns:
        A compiled LangChain runnable that can be used for chat interactions.

    The resulting graph looks like this:

    ``` mermaid
    stateDiagram-v2
        [*] --> Start
        Start --> Agent
        Agent --> Tools : continue
        Tools --> Agent
        Agent --> End : end
        End --> [*]

        classDef startClass fill:#ffdfba;
        classDef endClass fill:#baffc9;
        classDef otherClass fill:#fad7de;

        class Start startClass
        class End endClass
        class Agent,Tools otherClass
    ```

    The "agent" node calls the language model with the messages list (after applying the messages modifier).
    If the resulting AIMessage contains `tool_calls`, the graph will then call the ["tools"][langgraph.prebuilt.tool_node.ToolNode].
    The "tools" node executes the tools (1 tool per `tool_call`) and adds the responses to the messages list
    as `ToolMessage` objects. The agent node then calls the language model again.
    The process repeats until no more `tool_calls` are present in the response.
    The agent then returns the full list of messages as a dictionary containing the key "messages".

    ``` mermaid
        sequenceDiagram
            participant U as User
            participant A as Agent (LLM)
            participant T as Tools
            U->>A: Initial input
            Note over A: Messages modifier + LLM
            loop while tool_calls present
                A->>T: Execute tools
                T-->>A: ToolMessage for each tool_calls
            end
            A->>U: Return final state
    ```
    """

    if state_schema is not None:
        if missing_keys := {"messages", "is_last_step"} - set(
            state_schema.__annotations__
        ):
            raise ValueError(f"Missing required key(s) {missing_keys} in state_schema")

    if isinstance(tools, ToolExecutor):
        tool_classes: Sequence[BaseTool] = tools.tools
        tool_node = ToolNode(tool_classes)
    elif isinstance(tools, ToolNode):
        tool_classes = list(tools.tools_by_name.values())
        tool_node = tools
    else:
        tool_node = ToolNode(tools)
        # get the tool functions wrapped in a tool class from the ToolNode
        tool_classes = list(tool_node.tools_by_name.values())

    tool_calling_enabled = len(tool_classes) > 0

    if _should_bind_tools(model, tool_classes) and tool_calling_enabled:
        model = cast(BaseChatModel, model).bind_tools(tool_classes)

    # we're passing store here for validation
    preprocessor = _get_state_modifier_runnable(state_modifier, store)
    model_runnable = preprocessor | model

    def default_memory_manager(state: AgentState) -> AgentState:
        messages = state["messages"]
        # logger.debug("Before memory manager: %s", messages)

        if len(messages) <= 100:
            return state
        must_delete = len(messages) - 100
        for index, message in enumerate(messages):
            if index < must_delete:
                messages[index] = RemoveMessage(id=message.id)
            elif not isinstance(message, HumanMessage):
                messages[index] = RemoveMessage(id=message.id)
            else:
                break
        # logger.debug("After memory manager: %s", messages)
        return state

    if memory_manager is None:
        memory_manager = default_memory_manager

    # Define the function that calls the model
    def call_model(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])

        # Log message state before token limiting
        msg_count = len(state["messages"])
        token_count = _count_tokens(state["messages"])
        logger.debug(
            f"Before token limiting - Messages: {msg_count}, Tokens: {token_count}"
        )

        # Limit tokens before calling model
        state["messages"] = _limit_tokens(state["messages"], input_token_limit)

        # Log state after token limiting
        msg_count = len(state["messages"])
        token_count = _count_tokens(state["messages"])
        logger.debug(
            f"After token limiting - Messages: {msg_count}, Tokens: {token_count}"
        )

        try:
            logger.debug("Starting model invocation...")
            response = model_runnable.invoke(state, config)
            logger.debug(f"Model invocation completed. Response type: {type(response)}")

            # Log response details
            if isinstance(response, AIMessage):
                has_tool_calls = bool(response.tool_calls)
                logger.debug(f"Response is AIMessage. Has tool calls: {has_tool_calls}")
                if has_tool_calls:
                    logger.debug(f"Number of tool calls: {len(response.tool_calls)}")
            else:
                logger.debug(f"Response is not AIMessage: {type(response)}")

        except Exception as e:
            logger.error(f"Error in call model: {e}", exc_info=True)
            # Clean message history on error
            state["messages"] = _clean_history_on_error(state["messages"])
            raise e

        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
        if (
            (
                "remaining_steps" not in state
                and state["is_last_step"]
                and has_tool_calls
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 1
                and all_tools_return_direct
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 2
                and has_tool_calls
            )
        ):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    async def acall_model(state: AgentState, config: RunnableConfig) -> AgentState:
        _validate_chat_history(state["messages"])
        # Limit tokens before calling model
        state["messages"] = _limit_tokens(state["messages"], input_token_limit)
        try:
            response = await model_runnable.ainvoke(state, config)
        except Exception as e:
            logger.error(f"Error in async call model: {e}")
            # Clean message history on error
            state["messages"] = _clean_history_on_error(state["messages"])
            raise e
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
        if (
            (
                "remaining_steps" not in state
                and state["is_last_step"]
                and has_tool_calls
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 1
                and all_tools_return_direct
            )
            or (
                "remaining_steps" in state
                and state["remaining_steps"] < 2
                and has_tool_calls
            )
        ):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    if not tool_calling_enabled:
        # Define a new graph
        workflow = StateGraph(state_schema or AgentState)
        workflow.add_node("agent", RunnableCallable(call_model, acall_model))
        workflow.set_entry_point("agent")
        workflow.add_node("memory_manager", memory_manager)
        workflow.add_edge("agent", "memory_manager")
        workflow.add_edge("memory_manager", END)
        return workflow.compile(
            checkpointer=checkpointer,
            store=store,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
            debug=debug,
        )

    # Define the function that determines whether to continue or not
    def should_continue(state: AgentState) -> Literal["tools", "memory_manager"]:
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return "memory_manager"
        # Otherwise if there is, we continue
        else:
            return "tools"

    # Define a new graph
    workflow = StateGraph(state_schema or AgentState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", RunnableCallable(call_model, acall_model))
    workflow.add_node("tools", tool_node)
    workflow.add_node("memory_manager", memory_manager)

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        # First, we define the start node. We use `agent`.
        # This means these are the edges taken after the `agent` node is called.
        "agent",
        # Next, we pass in the function that will determine which node is called next.
        should_continue,
    )
    workflow.add_edge("memory_manager", END)

    # If any of the tools are configured to return_directly after running,
    # our graph needs to check if these were called
    should_return_direct = {t.name for t in tool_classes if t.return_direct}

    def route_tool_responses(state: AgentState) -> Literal["agent", "memory_manager"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in should_return_direct:
                return "memory_manager"
        return "agent"

    if should_return_direct:
        workflow.add_conditional_edges("tools", route_tool_responses)
    else:
        workflow.add_edge("tools", "agent")

    # Finally, we compile it!
    # This compiles it into a LangChain Runnable,
    # meaning you can use it as you would any other runnable
    return workflow.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before,
        interrupt_after=interrupt_after,
        debug=debug,
    )
