"""
Fork of langchain_community/agent_toolkits/slack/toolkit.py.
We need to pass the Slack client to the tools.
"""
import logging

from typing import List

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit
from pydantic import ConfigDict

from langchain_community.tools.slack.get_channel import SlackGetChannel
from langchain_community.tools.slack.get_message import SlackGetMessage
from langchain_community.tools.slack.schedule_message import SlackScheduleMessage
from langchain_community.tools.slack.send_message import SlackSendMessage

from slack_sdk import WebClient

logger = logging.getLogger(__name__)


class CrestalSlackGetChannel(SlackGetChannel):
    client: WebClient
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

class CrestalSlackGetMessage(SlackGetMessage):
    client: WebClient
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

class CrestalSlackScheduleMessage(SlackScheduleMessage):
    client: WebClient
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

class CrestalSlackSendMessage(SlackSendMessage):
    client: WebClient
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, client: WebClient) -> None:
        super().__init__(client=client)

class SlackSkillSet(BaseToolkit):
    """Toolkit for interacting with Slack.

    Parameters:
        client: The Slack client.

    Setup:
        Install ``slack_sdk`` and set environment variable ``SLACK_USER_TOKEN``.

        .. code-block:: bash

            pip install -U slack_sdk
            export SLACK_USER_TOKEN="your-user-token"

    Key init args:
        client: slack_sdk.WebClient
            The Slack client.

    Instantiate:
        .. code-block:: python

            from langchain_community.agent_toolkits import SlackToolkit

            toolkit = SlackToolkit()

    Tools:
        .. code-block:: python

            tools = toolkit.get_tools()
            tools

    Use within an agent:
        .. code-block:: python

            from langchain_openai import ChatOpenAI
            from langgraph.prebuilt import create_react_agent

            llm = ChatOpenAI(model="gpt-4o-mini")
            agent_executor = create_react_agent(llm, tools)

            example_query = "When was the #general channel created?"

            events = agent_executor.stream(
                {"messages": [("user", example_query)]},
                stream_mode="values",
            )
            for event in events:
                message = event["messages"][-1]
                if message.type != "tool":  # mask sensitive information
                    event["messages"][-1].pretty_print()

        .. code-block:: none

             ================================[1m Human Message [0m=================================

            When was the #general channel created?
            ==================================[1m Ai Message [0m==================================
            Tool Calls:
            get_channelid_name_dict (call_NXDkALjoOx97uF1v0CoZTqtJ)
            Call ID: call_NXDkALjoOx97uF1v0CoZTqtJ
            Args:
            ==================================[1m Ai Message [0m==================================

            The #general channel was created on timestamp 1671043305.
    """  # noqa: E501

    client: WebClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        logger.info(self.client)
        return [
            CrestalSlackGetChannel(client=self.client),
            CrestalSlackGetMessage(client=self.client),
            CrestalSlackScheduleMessage(client=self.client),
            CrestalSlackSendMessage(client=self.client),
        ]
