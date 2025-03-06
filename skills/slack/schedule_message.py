from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.slack.base import SlackBaseTool


class SlackScheduleMessageSchema(BaseModel):
    """Input schema for SlackScheduleMessage."""

    channel_id: str = Field(
        description="The ID of the channel to send the scheduled message to",
    )
    text: str = Field(
        description="The text content of the message to schedule",
    )
    post_at: str = Field(
        description="The time to send the message in ISO format (e.g., '2023-12-25T10:00:00Z')",
    )
    thread_ts: Optional[str] = Field(
        None,
        description="The timestamp of the thread to reply to, if sending a thread reply",
    )


class SlackScheduleMessage(SlackBaseTool):
    """Tool for scheduling messages to be sent to a Slack channel or thread."""

    name = "schedule_message"
    description = (
        "Schedule a message to be sent to a Slack channel or thread at a specific time"
    )
    args_schema = SlackScheduleMessageSchema
    slack_bot_token: str
    skill_store: SkillStoreABC

    def __init__(self, skill_store: SkillStoreABC, slack_bot_token: str) -> None:
        super().__init__(skill_store=skill_store)
        self.slack_bot_token = slack_bot_token

    async def _run(
        self,
        channel_id: str,
        text: str,
        post_at: str,
        thread_ts: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run the tool to schedule a Slack message.

        Args:
            channel_id: The ID of the channel to send the message to
            text: The text content of the message to schedule
            post_at: The time to send the message in ISO format
            thread_ts: The timestamp of the thread to reply to, if sending a thread reply

        Returns:
            Information about the scheduled message

        Raises:
            Exception: If an error occurs scheduling the message
        """
        client = self.get_client(self.slack_bot_token)

        try:
            # Convert ISO datetime string to Unix timestamp
            post_datetime = datetime.fromisoformat(post_at.replace("Z", "+00:00"))
            post_time_unix = int(post_datetime.timestamp())

            # Prepare message parameters
            message_params = {
                "channel": channel_id,
                "text": text,
                "post_at": post_time_unix,
            }

            # Add thread_ts if replying to a thread
            if thread_ts:
                message_params["thread_ts"] = thread_ts

            # Schedule the message
            response = client.chat_scheduleMessage(**message_params)

            if response["ok"]:
                return {
                    "channel": channel_id,
                    "scheduled_message_id": response["scheduled_message_id"],
                    "post_at": post_at,
                    "text": text,
                    "thread_ts": thread_ts,
                }
            else:
                raise Exception(f"Error scheduling message: {response.get('error')}")

        except Exception as e:
            raise Exception(f"Error scheduling message: {str(e)}")
