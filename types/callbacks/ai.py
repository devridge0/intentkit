from typing import Callable, List

# Define a type hint for the callback that takes three strings and returns a list of strings
AgentExecutionCallback = Callable[[str, str, str], List[str]]
"""Callback function type for agent execution.

Args:
    aid (str): The agent ID that uniquely identifies the AI agent
    prompt (str): The input prompt/query provided to the agent
    thread_id (str): The thread ID for tracking the execution context

Returns:
    List[str]: A list of formatted response lines from the agent execution
"""
