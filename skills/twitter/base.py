from datetime import datetime, timedelta, timezone
from typing import Type

from pydantic import BaseModel, Field

from abstracts.agent import AgentStoreABC
from abstracts.skill import IntentKitSkill, SkillStoreABC
from abstracts.twitter import TwitterABC


class TwitterBaseTool(IntentKitSkill):
    """Base class for Twitter tools."""

    twitter: TwitterABC = Field(description="The Twitter client abstraction")
    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    agent_id: str = Field(description="The ID of the agent")
    agent_store: AgentStoreABC = Field(
        description="The agent store for persisting data"
    )
    store: SkillStoreABC = Field(description="The skill store for persisting data")

    def check_rate_limit(
        self, max_requests: int = 1, interval: int = 15
    ) -> tuple[bool, str | None]:
        """Check if the rate limit has been exceeded.

        Args:
            max_requests: Maximum number of requests allowed within the rate limit window.
            interval: Time interval in minutes for the rate limit window.

        Returns:
            tuple[bool, str | None]: (is_rate_limited, error_message)
        """
        rate_limit = self.store.get_agent_skill_data(
            self.agent_id, self.name, "rate_limit"
        )
        
        current_time = datetime.now(tz=timezone.utc)
        
        if (
            rate_limit
            and rate_limit.get("reset_time")
            and rate_limit["count"] is not None
            and datetime.fromisoformat(rate_limit["reset_time"]) > current_time
        ):
            if rate_limit["count"] >= max_requests:
                return True, "Rate limit exceeded"
            else:
                rate_limit["count"] += 1
                self.store.save_agent_skill_data(
                    self.agent_id, self.name, "rate_limit", rate_limit
                )
                return False, None

        # If no rate limit exists or it has expired, create a new one
        new_rate_limit = {
            "count": 1,
            "reset_time": (current_time + timedelta(minutes=interval)).isoformat(),
        }
        self.store.save_agent_skill_data(
            self.agent_id, self.name, "rate_limit", new_rate_limit
        )
        return False, None


class Tweet(BaseModel):
    """Model representing a Twitter tweet."""

    id: str
    text: str
    author_id: str
    created_at: datetime
    referenced_tweets: list[dict] | None = None
    attachments: dict | None = None
