from datetime import datetime
from typing import Type

from pydantic import BaseModel, Field

from abstracts.agent import AgentStoreABC
from abstracts.skill import IntentKitSkill, SkillStoreABC
from abstracts.twitter import TwitterABC


class Tweet(BaseModel):
    """Model representing a Twitter tweet."""

    id: str
    text: str
    author_id: str
    created_at: datetime
    referenced_tweets: list[dict] | None = None
    attachments: dict | None = None


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
