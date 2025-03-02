import json
import logging
import re
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional

import yaml
from epyxid import XID
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, constr, field_validator, model_validator
from pydantic import Field as PydanticField
from pydantic.json_schema import SkipJsonSchema
from sqlalchemy import BigInteger, Column, DateTime, Identity, String, func, select
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base

from models.db import get_session
from models.skill import SkillConfig

logger = logging.getLogger(__name__)

Base = declarative_base()


class AgentAutonomous(BaseModel):
    """Autonomous agent configuration."""

    id: Annotated[
        str,
        PydanticField(description="Unique identifier for the autonomous configuration"),
    ]
    name: Annotated[
        Optional[str],
        PydanticField(
            default=None, description="Display name of the autonomous configuration"
        ),
    ]
    description: Annotated[
        Optional[str],
        PydanticField(
            default=None, description="Description of the autonomous configuration"
        ),
    ]
    minutes: Annotated[
        Optional[int],
        PydanticField(
            default=None,
            description="Interval in minutes between operations, mutually exclusive with cron",
        ),
    ]
    cron: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Cron expression for scheduling operations, mutually exclusive with minutes",
        ),
    ]
    prompt: Annotated[
        str,
        PydanticField(description="Special prompt used during autonomous operation"),
    ]
    enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=True, description="Whether the autonomous configuration is enabled"
        ),
    ]

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v:
            raise ValueError("id cannot be empty")
        if len(v.encode()) > 20:
            raise ValueError("id must be at most 20 bytes")
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "id must contain only lowercase letters, numbers, and dashes"
            )
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.encode()) > 50:
            raise ValueError("name must be at most 50 bytes")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.encode()) > 200:
            raise ValueError("description must be at most 200 bytes")
        return v

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.encode()) > 2000:
            raise ValueError("prompt must be at most 2000 bytes")
        return v

    @model_validator(mode="after")
    def validate_schedule(self) -> "AgentAutonomous":
        if self.minutes is None and self.cron is None:
            raise ValueError("either minutes or cron must have a value")
        return self


class AgentTable(Base):
    """Agent table db model."""

    __tablename__ = "agents"

    id = Column(
        String,
        primary_key=True,
        comment="Unique identifier for the agent. Must be URL-safe, containing only lowercase letters, numbers, and hyphens",
    )
    number = Column(
        BigInteger,
        Identity(start=1, increment=1),
        nullable=False,
        comment="Auto-incrementing number assigned by the system for easy reference",
    )
    name = Column(
        String,
        nullable=True,
        comment="Display name of the agent",
    )
    slug = Column(
        String,
        nullable=True,
        comment="Slug of the agent, used for URL generation",
    )
    ticker = Column(
        String,
        nullable=True,
        comment="Ticker symbol of the agent",
    )
    token_address = Column(
        String,
        nullable=True,
        comment="Token address of the agent",
    )
    purpose = Column(
        String,
        nullable=True,
        comment="Purpose or role of the agent",
    )
    personality = Column(
        String,
        nullable=True,
        comment="Personality traits of the agent",
    )
    principles = Column(
        String,
        nullable=True,
        comment="Principles or values of the agent",
    )
    owner = Column(
        String,
        nullable=True,
        comment="Owner identifier of the agent, used for access control",
    )
    upstream_id = Column(
        String,
        nullable=True,
        comment="External reference ID for idempotent operations",
    )
    # AI part
    model = Column(
        String,
        nullable=True,
        default="gpt-4o-mini",
        comment="AI model identifier to be used by this agent for processing requests. Available models: gpt-4o, gpt-4o-mini, chatgpt-4o-latest, deepseek-chat, deepseek-reasoner, grok-2",
    )
    prompt = Column(
        String,
        nullable=True,
        comment="Base system prompt that defines the agent's behavior and capabilities",
    )
    prompt_append = Column(
        String,
        nullable=True,
        comment="Additional system prompt that has higher priority than the base prompt",
    )
    temperature = Column(
        JSONB,
        nullable=True,
        default=0.7,
        comment="AI model temperature parameter controlling response randomness (0.0~1.0)",
    )
    frequency_penalty = Column(
        JSONB,
        nullable=True,
        default=0.0,
        comment="Frequency penalty for the AI model, a higher value penalizes new tokens based on their existing frequency in the chat history (-2.0~2.0)",
    )
    presence_penalty = Column(
        JSONB,
        nullable=True,
        default=0.0,
        comment="Presence penalty for the AI model, a higher value penalizes new tokens based on whether they appear in the chat history (-2.0~2.0)",
    )
    # autonomous mode
    autonomous = Column(
        JSONB,
        nullable=True,
        comment="Autonomous agent configurations",
    )
    autonomous_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether the agent can operate autonomously without user input",
    )
    autonomous_minutes = Column(
        JSONB,
        nullable=True,
        default=240,
        comment="Interval in minutes between autonomous operations when enabled",
    )
    autonomous_prompt = Column(
        String,
        nullable=True,
        comment="Special prompt used during autonomous operation mode",
    )
    # skills
    skills = Column(
        JSONB,
        nullable=True,
        comment="Dict of skills and their corresponding configurations",
    )
    # if cdp_enabled, agent will have a cdp wallet
    cdp_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether CDP (Crestal Development Platform) integration is enabled",
    )
    cdp_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of CDP skills available to this agent",
    )
    cdp_network_id = Column(
        String,
        nullable=True,
        default="base-mainnet",
        comment="Network identifier for CDP integration",
    )
    # if goat_enabled, will load goat skills
    crossmint_config = Column(
        JSONB,
        nullable=True,
        comment="Dict of Crossmint wallet configurations",
    )
    goat_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether GOAT integration is enabled",
    )
    goat_skills = Column(
        JSONB,
        nullable=True,
        comment="Dict of GOAT skills and their corresponding configurations",
    )
    # if twitter_enabled, the twitter_entrypoint will be enabled, twitter_config will be checked
    twitter_entrypoint_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether the agent can receive events from Twitter",
    )
    twitter_config = Column(
        JSONB,
        nullable=True,
        comment="This configuration will be used for entrypoint only",
    )
    # twitter skills require config, but not require twitter_enabled flag.
    # As long as twitter_skills is not empty, the corresponding skills will be loaded.
    twitter_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Twitter-specific skills available to this agent",
    )
    # if telegram_entrypoint_enabled, the telegram_entrypoint_enabled will be enabled, telegram_config will be checked
    telegram_entrypoint_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether the agent can receive events from Telegram",
    )
    telegram_config = Column(
        JSONB,
        nullable=True,
        comment="Telegram integration configuration settings",
    )
    # telegram skills not used for now
    telegram_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Telegram-specific skills available to this agent",
    )
    # skills have no category
    common_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of general-purpose skills available to this agent",
    )
    # if enso_enabled, the enso skillset will be enabled, enso_config will be checked
    enso_enabled = Column(
        JSONB,
        nullable=True,
        default=False,
        comment="Whether Enso integration is enabled",
    )
    # enso skills
    enso_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Enso-specific skills available to this agent",
    )
    enso_config = Column(
        JSONB,
        nullable=True,
        comment="Enso integration configuration settings",
    )
    # Acolyt skills
    acolyt_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Acolyt-specific skills available to this agent",
    )
    acolyt_config = Column(
        JSONB,
        nullable=True,
        comment="Acolyt integration configuration settings",
    )
    # Allora skills
    allora_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Allora-specific skills available to this agent",
    )
    allora_config = Column(
        JSONB,
        nullable=True,
        comment="Allora integration configuration settings",
    )
    # ELFA skills
    elfa_skills = Column(
        ARRAY(String),
        nullable=True,
        comment="List of Elfa-specific skills available to this agent",
    )
    elfa_config = Column(
        JSONB,
        nullable=True,
        comment="Elfa integration configuration settings",
    )
    # auto timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the agent was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Timestamp when the agent was last updated",
    )


class AgentUpdate(BaseModel):
    """Agent update model."""

    name: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Display name of the agent",
        ),
    ]
    slug: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Slug of the agent, used for URL generation",
        ),
    ]
    ticker: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Ticker symbol of the agent",
        ),
    ]
    token_address: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Token address of the agent",
        ),
    ]
    purpose: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Purpose or role of the agent",
        ),
    ]
    personality: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Personality traits of the agent",
        ),
    ]
    principles: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Principles or values of the agent",
        ),
    ]
    owner: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Owner identifier of the agent, used for access control",
        ),
    ]
    upstream_id: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            index=True,
            description="External reference ID for idempotent operations",
        ),
    ]
    # AI part
    model: Annotated[
        Optional[str],
        PydanticField(
            default="gpt-4o-mini",
            description="AI model identifier to be used by this agent for processing requests. Available models: gpt-4o, gpt-4o-mini, chatgpt-4o-latest, deepseek-chat, deepseek-reasoner, grok-2",
        ),
    ]
    prompt: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Base system prompt that defines the agent's behavior and capabilities",
        ),
    ]
    prompt_append: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Additional system prompt that has higher priority than the base prompt",
        ),
    ]
    temperature: Annotated[
        Optional[float],
        PydanticField(
            default=0.7,
            description="AI model temperature parameter controlling response randomness (0.0~1.0)",
        ),
    ]
    frequency_penalty: Annotated[
        Optional[float],
        PydanticField(
            default=0.0,
            description="Frequency penalty for the AI model, a higher value penalizes new tokens based on their existing frequency in the chat history (-2.0~2.0)",
        ),
    ]
    presence_penalty: Annotated[
        Optional[float],
        PydanticField(
            default=0.0,
            description="Presence penalty for the AI model, a higher value penalizes new tokens based on whether they appear in the chat history (-2.0~2.0)",
        ),
    ]
    # autonomous mode
    autonomous: Annotated[
        Optional[List[AgentAutonomous]],
        PydanticField(
            default=None,
            description="Autonomous agent configurations",
        ),
    ]
    autonomous_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            deprecated="Please use autonomous instead",
            description="Whether the agent can operate autonomously without user input",
        ),
    ]
    autonomous_minutes: Annotated[
        Optional[int],
        PydanticField(
            default=240,
            deprecated=True,
            description="Interval in minutes between autonomous operations when enabled",
        ),
    ]
    autonomous_prompt: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            deprecated=True,
            description="Special prompt used during autonomous operation mode",
        ),
    ]
    # skills
    skills: Annotated[
        Optional[Dict[str, SkillConfig]],
        PydanticField(
            default=None,
            description="Dict of skills and their corresponding configurations",
        ),
    ]
    # if cdp_enabled, agent will have a cdp wallet
    cdp_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            description="Whether CDP (Crestal Development Platform) integration is enabled",
        ),
    ]
    cdp_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of CDP skills available to this agent",
        ),
    ]
    cdp_network_id: Annotated[
        Optional[str],
        PydanticField(
            default="base-mainnet",
            description="Network identifier for CDP integration",
        ),
    ]
    # if goat_enabled, will load goat skills
    crossmint_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            description="Dict of Crossmint wallet configurations",
        ),
    ]
    goat_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            description="Whether GOAT integration is enabled",
        ),
    ]
    goat_skills: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            description="Dict of GOAT skills and their corresponding configurations",
        ),
    ]
    # if twitter_enabled, the twitter_entrypoint will be enabled, twitter_config will be checked
    twitter_entrypoint_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            description="Whether the agent can receive events from Twitter",
        ),
    ]
    twitter_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            description="This configuration will be used for entrypoint only",
        ),
    ]
    # twitter skills require config, but not require twitter_enabled flag.
    # As long as twitter_skills is not empty, the corresponding skills will be loaded.
    twitter_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Twitter-specific skills available to this agent",
        ),
    ]
    # if telegram_entrypoint_enabled, the telegram_entrypoint_enabled will be enabled, telegram_config will be checked
    telegram_entrypoint_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            description="Whether the agent can receive events from Telegram",
        ),
    ]
    telegram_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            description="Telegram integration configuration settings",
        ),
    ]
    # telegram skills not used for now
    telegram_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Telegram-specific skills available to this agent",
        ),
    ]
    # skills have no category
    common_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            description="List of general-purpose skills available to this agent",
        ),
    ]
    # if enso_enabled, the enso skillset will be enabled, enso_config will be checked
    enso_enabled: Annotated[
        Optional[bool],
        PydanticField(
            default=False,
            description="Whether Enso integration is enabled",
        ),
    ]
    # enso skills
    enso_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Enso-specific skills available to this agent",
        ),
    ]
    enso_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            deprecated=True,
            description="Enso integration configuration settings",
        ),
    ]
    # Acolyt skills
    acolyt_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Acolyt-specific skills available to this agent",
        ),
    ]
    acolyt_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            deprecated=True,
            description="Acolyt integration configuration settings",
        ),
    ]
    # Allora skills
    allora_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Allora-specific skills available to this agent",
        ),
    ]
    allora_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            deprecated=True,
            description="Allora integration configuration settings",
        ),
    ]
    # ELFA skills
    elfa_skills: Annotated[
        Optional[List[str]],
        PydanticField(
            default=None,
            deprecated=True,
            description="List of Elfa-specific skills available to this agent",
        ),
    ]
    elfa_config: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            deprecated=True,
            description="Elfa integration configuration settings",
        ),
    ]

    def check_prompt(self):
        # Check for markdown headers in text fields
        fields_to_check = [
            "purpose",
            "personality",
            "principles",
            "prompt",
            "prompt_append",
        ]
        for field in fields_to_check:
            value = getattr(self, field)
            if value and isinstance(value, str):
                for line_num, line in enumerate(value.split("\n"), 1):
                    line = line.strip()
                    if line.startswith("# ") or line.startswith("## "):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field}' contains markdown level 1/2 header at line {line_num}. You can use level 3 (### ) instead.",
                        )

    async def update(self, id: str) -> "Agent":
        self.check_prompt()
        async with get_session() as db:
            db_agent = (
                await db.exec(select(AgentTable).where(AgentTable.id == id))
            ).first()
            if not db_agent:
                raise HTTPException(
                    status_code=404,
                    detail="Agent not found",
                )
            # check onwer
            if self.owner and db_agent.owner != self.owner:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to update this agent",
                )
            # update
            for key, value in self.model_dump(exclude_unset=True).items():
                setattr(db_agent, key, value)
            await db.commit()
            await db.refresh(db_agent)
            return Agent.model_validate(db_agent)


class AgentCreate(AgentUpdate):
    """Agent create model."""

    id: Annotated[
        str,
        PydanticField(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the agent. Must be URL-safe, containing only lowercase letters, numbers, and hyphens",
        ),
        constr(pattern=r"^[a-z][a-z0-9-]*$"),
    ]

    async def check_upstream_id(self) -> None:
        if self.upstream_id:
            async with get_session() as db:
                ok = await db.exec(
                    select(AgentTable).where(AgentTable.upstream_id == self.upstream_id)
                ).first()
                if ok:
                    raise HTTPException(
                        status_code=400,
                        detail="Upstream id already in use",
                    )

    async def create(self) -> "Agent":
        self.check_prompt()
        await self.check_upstream_id()
        async with get_session() as db:
            db_agent = AgentTable(**self.model_dump())
            db.add(db_agent)
            await db.commit()
            await db.refresh(db_agent)
            return Agent.model_validate(db_agent)

    async def create_or_update(self) -> ("Agent", bool):
        self.check_prompt()
        is_new = False
        async with get_session() as db:
            db_agent = (
                await db.exec(select(AgentTable).where(AgentTable.id == self.id))
            ).first()
            if not db_agent:
                upstream = await db.exec(
                    select(AgentTable).where(AgentTable.upstream_id == self.upstream_id)
                ).first()
                if upstream:
                    raise HTTPException(
                        status_code=400,
                        detail="Upstream id already in use",
                    )
                db_agent = AgentTable(**self.model_dump())
                db.add(db_agent)
                is_new = True
            else:
                # check onwer
                if self.owner and db_agent.owner != self.owner:
                    raise HTTPException(
                        status_code=403,
                        detail="You do not have permission to update this agent",
                    )
                for key, value in self.model_dump(exclude_unset=True).items():
                    setattr(db_agent, key, value)
            await db.commit()
            await db.refresh(db_agent)
            return (Agent.model_validate(db_agent), is_new)


class Agent(AgentCreate):
    """Agent model."""

    model_config = ConfigDict(from_attributes=True)

    # auto increment number by db
    number: Annotated[
        int,
        PydanticField(
            description="Auto-incrementing number assigned by the system for easy reference",
        ),
    ]
    # auto timestamp
    created_at: Annotated[
        datetime,
        PydanticField(
            description="Timestamp when the agent was created, will ignore when importing"
        ),
    ]
    updated_at: Annotated[
        datetime,
        PydanticField(
            description="Timestamp when the agent was last updated, will ignore when importing"
        ),
    ]

    def to_yaml(self) -> str:
        """
        Dump the agent model to YAML format with field descriptions as comments.
        The comments are extracted from the field descriptions in the model.
        Fields annotated with SkipJsonSchema will be excluded from the output.

        Returns:
            str: YAML representation of the agent with field descriptions as comments
        """
        data = {}
        yaml_lines = []

        for field_name, field in self.model_fields.items():
            logger.debug(f"Processing field {field_name} with type {field.metadata}")
            # Skip fields with SkipJsonSchema annotation
            if any(isinstance(item, SkipJsonSchema) for item in field.metadata):
                continue

            value = getattr(self, field_name)
            data[field_name] = value
            # Add comment from field description if available
            description = field.description
            if description:
                if len(yaml_lines) > 0:  # Add blank line between fields
                    yaml_lines.append("")
                # Split description into multiple lines if too long
                desc_lines = [f"# {line}" for line in description.split("\n")]
                yaml_lines.extend(desc_lines)

            # Format the value based on its type
            if value is None:
                yaml_lines.append(f"{field_name}: null")
            elif isinstance(value, str):
                if "\n" in value or len(value) > 60:
                    # Use block literal style (|) for multiline strings
                    # Remove any existing escaped newlines and use actual line breaks
                    value = value.replace("\\n", "\n")
                    yaml_value = f"{field_name}: |-\n"
                    # Indent each line with 2 spaces
                    yaml_value += "\n".join(f"  {line}" for line in value.split("\n"))
                    yaml_lines.append(yaml_value)
                else:
                    # Use flow style for short strings
                    yaml_value = yaml.dump(
                        {field_name: value},
                        default_flow_style=False,
                        allow_unicode=True,  # This ensures emojis are preserved
                    )
                    yaml_lines.append(yaml_value.rstrip())
            else:
                # Handle non-string values
                yaml_value = yaml.dump(
                    {field_name: value},
                    default_flow_style=False,
                    allow_unicode=True,
                )
                yaml_lines.append(yaml_value.rstrip())

        return "\n".join(yaml_lines) + "\n"

    @staticmethod
    @classmethod
    async def count() -> int:
        async with get_session() as db:
            return (await db.exec(select(func.count(AgentTable.id)))).one()

    @classmethod
    async def get(cls, agent_id: str) -> Optional["Agent"]:
        async with get_session() as db:
            res = (
                await db.exec(select(AgentTable).where(AgentTable.id == agent_id))
            ).first()
            return cls.model_validate(res)


class AgentResponse(Agent):
    """Response model for Agent API."""

    # data part
    cdp_wallet_address: Annotated[
        Optional[str], PydanticField(description="CDP wallet address for the agent")
    ]
    has_twitter_linked: Annotated[
        bool,
        PydanticField(description="Whether the agent has linked their Twitter account"),
    ]
    linked_twitter_username: Annotated[
        Optional[str],
        PydanticField(description="The username of the linked Twitter account"),
    ]
    linked_twitter_name: Annotated[
        Optional[str],
        PydanticField(description="The name of the linked Twitter account"),
    ]
    has_twitter_self_key: Annotated[
        bool,
        PydanticField(
            description="Whether the agent has self-keyed their Twitter account"
        ),
    ]
    has_telegram_self_key: Annotated[
        bool,
        PydanticField(
            description="Whether the agent has self-keyed their Telegram account"
        ),
    ]
    linked_telegram_username: Annotated[
        Optional[str],
        PydanticField(description="The username of the linked Telegram account"),
    ]
    linked_telegram_name: Annotated[
        Optional[str],
        PydanticField(description="The name of the linked Telegram account"),
    ]

    @classmethod
    def from_agent(
        cls, agent: Agent, agent_data: Optional["AgentData"] = None
    ) -> "AgentResponse":
        """Create an AgentResponse from an Agent instance.

        Args:
            agent: Agent instance
            agent_data: Optional AgentData instance

        Returns:
            AgentResponse: Response model with additional processed data
        """
        # Get base data from agent
        data = agent.model_dump()

        # Process CDP wallet address
        cdp_wallet_address = None
        if agent_data and agent_data.cdp_wallet_data:
            try:
                wallet_data = json.loads(agent_data.cdp_wallet_data)
                cdp_wallet_address = wallet_data.get("default_address_id")
            except (json.JSONDecodeError, AttributeError):
                pass

        # Process Twitter linked status
        has_twitter_linked = False
        linked_twitter_username = None
        linked_twitter_name = None
        if agent_data and agent_data.twitter_access_token:
            linked_twitter_username = agent_data.twitter_username
            linked_twitter_name = agent_data.twitter_name
            if agent_data.twitter_access_token_expires_at:
                has_twitter_linked = (
                    agent_data.twitter_access_token_expires_at
                    > datetime.now(timezone.utc)
                )
            else:
                has_twitter_linked = True

        # Process Twitter self-key status and remove sensitive fields
        has_twitter_self_key = False
        twitter_config = data.get("twitter_config", {})
        if twitter_config:
            required_keys = {
                "access_token",
                "bearer_token",
                "consumer_key",
                "consumer_secret",
                "access_token_secret",
            }
            has_twitter_self_key = all(
                key in twitter_config and twitter_config[key] for key in required_keys
            )

        # Process Telegram self-key status and remove token
        linked_telegram_username = None
        linked_telegram_name = None
        telegram_config = data.get("telegram_config", {})
        has_telegram_self_key = bool(
            telegram_config and "token" in telegram_config and telegram_config["token"]
        )
        if telegram_config and "token" in telegram_config:
            if agent_data:
                linked_telegram_username = agent_data.telegram_username
                linked_telegram_name = agent_data.telegram_name

        # Add processed fields to response
        data.update(
            {
                "cdp_wallet_address": cdp_wallet_address,
                "has_twitter_linked": has_twitter_linked,
                "linked_twitter_username": linked_twitter_username,
                "linked_twitter_name": linked_twitter_name,
                "has_twitter_self_key": has_twitter_self_key,
                "has_telegram_self_key": has_telegram_self_key,
                "linked_telegram_username": linked_telegram_username,
                "linked_telegram_name": linked_telegram_name,
            }
        )

        return cls.model_validate(**data)


class AgentDataTable(Base):
    """Agent data model for database storage of additional data related to the agent."""

    __tablename__ = "agent_data"

    id = Column(String, primary_key=True, comment="Same as Agent.id")
    cdp_wallet_data = Column(String, nullable=True, comment="CDP wallet data")
    crossmint_wallet_data = Column(
        JSONB, nullable=True, comment="Crossmint wallet information"
    )
    twitter_id = Column(String, nullable=True, comment="Twitter user ID")
    twitter_username = Column(String, nullable=True, comment="Twitter username")
    twitter_name = Column(String, nullable=True, comment="Twitter display name")
    twitter_access_token = Column(String, nullable=True, comment="Twitter access token")
    twitter_access_token_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Twitter access token expiration time",
    )
    twitter_refresh_token = Column(
        String, nullable=True, comment="Twitter refresh token"
    )
    telegram_id = Column(String, nullable=True, comment="Telegram user ID")
    telegram_username = Column(String, nullable=True, comment="Telegram username")
    telegram_name = Column(String, nullable=True, comment="Telegram display name")
    error_message = Column(String, nullable=True, comment="Last error message")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when the agent data was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=func.now(),
        comment="Timestamp when the agent data was last updated",
    )


class AgentData(BaseModel):
    """Agent data model for storing additional data related to the agent."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[
        str,
        PydanticField(
            description="Same as Agent.id",
        ),
    ]
    cdp_wallet_data: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="CDP wallet data",
        ),
    ]
    crossmint_wallet_data: Annotated[
        Optional[dict],
        PydanticField(
            default=None,
            description="Crossmint wallet information",
        ),
    ]
    twitter_id: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Twitter user ID",
        ),
    ]
    twitter_username: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Twitter username",
        ),
    ]
    twitter_name: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Twitter display name",
        ),
    ]
    twitter_access_token: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Twitter access token",
        ),
    ]
    twitter_access_token_expires_at: Annotated[
        Optional[datetime],
        PydanticField(
            default=None,
            description="Twitter access token expiration time",
        ),
    ]
    twitter_refresh_token: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Twitter refresh token",
        ),
    ]
    telegram_id: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Telegram user ID",
        ),
    ]
    telegram_username: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Telegram username",
        ),
    ]
    telegram_name: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Telegram display name",
        ),
    ]
    error_message: Annotated[
        Optional[str],
        PydanticField(
            default=None,
            description="Last error message",
        ),
    ]
    created_at: Annotated[
        datetime,
        PydanticField(
            description="Timestamp when the agent data was created",
        ),
    ]
    updated_at: Annotated[
        datetime,
        PydanticField(
            description="Timestamp when the agent data was last updated",
        ),
    ]

    @classmethod
    async def get(cls, agent_id: str) -> Optional["AgentData"]:
        """Get agent data by ID.

        Args:
            agent_id: Agent ID

        Returns:
            AgentData if found, None otherwise

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                result = (
                    await db.exec(
                        select(AgentDataTable).where(AgentDataTable.id == agent_id)
                    )
                ).first()
                if result:
                    return cls.model_validate(result)
                return None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent data: {str(e)}",
            ) from e

    async def save(self) -> None:
        """Save or update agent data.

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                existing = (
                    await db.exec(
                        select(AgentDataTable).where(AgentDataTable.id == self.id)
                    )
                ).first()

                if existing:
                    # Update existing record
                    for field, value in self.model_dump(exclude_unset=True).items():
                        setattr(existing, field, value)
                    db.add(existing)
                else:
                    # Create new record
                    db_agent_data = AgentDataTable(**self.model_dump())
                    db.add(db_agent_data)

                await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save agent data: {str(e)}",
            ) from e


class AgentPluginDataTable(Base):
    """Database model for storing plugin-specific data for agents.

    This model uses a composite primary key of (agent_id, plugin, key) to store
    plugin-specific data for agents in a flexible way.

    Attributes:
        agent_id: ID of the agent this data belongs to
        plugin: Name of the plugin this data is for
        key: Key for this specific piece of data
        data: JSON data stored for this key
    """

    __tablename__ = "agent_plugin_data"

    agent_id = Column(String, primary_key=True)
    plugin = Column(String, primary_key=True)
    key = Column(String, primary_key=True)
    data = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AgentPluginData(BaseModel):
    """Model for storing plugin-specific data for agents.

    This model uses a composite primary key of (agent_id, plugin, key) to store
    plugin-specific data for agents in a flexible way.

    Attributes:
        agent_id: ID of the agent this data belongs to
        plugin: Name of the plugin this data is for
        key: Key for this specific piece of data
        data: JSON data stored for this key
    """

    model_config = ConfigDict(from_attributes=True)

    agent_id: str
    plugin: str
    key: str
    data: Dict[str, Any] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def get(
        cls, agent_id: str, plugin: str, key: str
    ) -> Optional["AgentPluginData"]:
        """Get plugin data for an agent.

        Args:
            agent_id: ID of the agent
            plugin: Name of the plugin
            key: Data key

        Returns:
            AgentPluginData if found, None otherwise

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                result = (
                    await db.exec(
                        select(AgentPluginDataTable).where(
                            AgentPluginDataTable.agent_id == agent_id,
                            AgentPluginDataTable.plugin == plugin,
                            AgentPluginDataTable.key == key,
                        )
                    )
                ).first()
                if result:
                    return cls.model_validate(result)
                return None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get plugin data: {str(e)}",
            ) from e

    async def save(self) -> None:
        """Save or update plugin data.

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                existing = (
                    await db.exec(
                        select(AgentPluginDataTable).where(
                            AgentPluginDataTable.agent_id == self.agent_id,
                            AgentPluginDataTable.plugin == self.plugin,
                            AgentPluginDataTable.key == self.key,
                        )
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.data = self.data
                    existing.updated_at = datetime.now(timezone.utc)
                    db.add(existing)
                else:
                    # Create new record
                    now = datetime.now(timezone.utc)
                    new_record = AgentPluginDataTable(
                        agent_id=self.agent_id,
                        plugin=self.plugin,
                        key=self.key,
                        data=self.data,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(new_record)

                await db.commit()

                # Refresh the model with updated data
                if existing:
                    await db.refresh(existing)
                    self.data = existing.data
                    self.created_at = existing.created_at
                    self.updated_at = existing.updated_at
                else:
                    # Get the newly created record to update this instance
                    new_record = (
                        await db.exec(
                            select(AgentPluginDataTable).where(
                                AgentPluginDataTable.agent_id == self.agent_id,
                                AgentPluginDataTable.plugin == self.plugin,
                                AgentPluginDataTable.key == self.key,
                            )
                        )
                    ).first()
                    if new_record:
                        self.created_at = new_record.created_at
                        self.updated_at = new_record.updated_at

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save plugin data: {str(e)}",
            ) from e


class AgentQuotaTable(Base):
    """AgentQuota database table model."""

    __tablename__ = "agent_quotas"

    id = Column(String, primary_key=True)
    plan = Column(String, default="self-hosted")
    message_count_total = Column(BigInteger, default=0)
    message_limit_total = Column(BigInteger, default=99999999)
    message_count_monthly = Column(BigInteger, default=0)
    message_limit_monthly = Column(BigInteger, default=99999999)
    message_count_daily = Column(BigInteger, default=0)
    message_limit_daily = Column(BigInteger, default=99999999)
    last_message_time = Column(DateTime(timezone=True), default=None, nullable=True)
    autonomous_count_total = Column(BigInteger, default=0)
    autonomous_limit_total = Column(BigInteger, default=99999999)
    autonomous_count_monthly = Column(BigInteger, default=0)
    autonomous_limit_monthly = Column(BigInteger, default=99999999)
    last_autonomous_time = Column(DateTime(timezone=True), default=None, nullable=True)
    twitter_count_total = Column(BigInteger, default=0)
    twitter_limit_total = Column(BigInteger, default=99999999)
    twitter_count_daily = Column(BigInteger, default=0)
    twitter_limit_daily = Column(BigInteger, default=99999999)
    last_twitter_time = Column(DateTime(timezone=True), default=None, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AgentQuota(BaseModel):
    """AgentQuota model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    plan: str = "self-hosted"
    message_count_total: int = 0
    message_limit_total: int = 99999999
    message_count_monthly: int = 0
    message_limit_monthly: int = 99999999
    message_count_daily: int = 0
    message_limit_daily: int = 99999999
    last_message_time: Optional[datetime] = None
    autonomous_count_total: int = 0
    autonomous_limit_total: int = 99999999
    autonomous_count_monthly: int = 0
    autonomous_limit_monthly: int = 99999999
    last_autonomous_time: Optional[datetime] = None
    twitter_count_total: int = 0
    twitter_limit_total: int = 99999999
    twitter_count_daily: int = 0
    twitter_limit_daily: int = 99999999
    last_twitter_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    async def get(cls, agent_id: str) -> "AgentQuota":
        """Get agent quota by id, if not exists, create a new one.

        Args:
            agent_id: Agent ID

        Returns:
            AgentQuota: The agent's quota object

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                quota_record = (
                    await db.exec(
                        select(AgentQuotaTable).where(AgentQuotaTable.id == agent_id)
                    )
                ).first()

                if not quota_record:
                    # Create new record
                    now = datetime.now(timezone.utc)
                    quota_record = AgentQuotaTable(
                        id=agent_id,
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(quota_record)
                    await db.commit()
                    await db.refresh(quota_record)

                return cls.model_validate(quota_record)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent quota: {str(e)}",
            ) from e

    def has_message_quota(self) -> bool:
        """Check if the agent has message quota.

        Returns:
            bool: True if the agent has quota, False otherwise
        """
        # Check total limit
        if self.message_count_total >= self.message_limit_total:
            return False
        # Check monthly limit
        if self.message_count_monthly >= self.message_limit_monthly:
            return False
        # Check daily limit
        if self.message_count_daily >= self.message_limit_daily:
            return False
        return True

    def has_autonomous_quota(self) -> bool:
        """Check if the agent has autonomous quota.

        Returns:
            bool: True if the agent has quota, False otherwise
        """
        # Check total limit
        if self.autonomous_count_total >= self.autonomous_limit_total:
            return False
        # Check monthly limit
        if self.autonomous_count_monthly >= self.autonomous_limit_monthly:
            return False
        return True

    def has_twitter_quota(self) -> bool:
        """Check if the agent has twitter quota.

        Returns:
            bool: True if the agent has quota, False otherwise
        """
        # Check total limit
        if self.twitter_count_total >= self.twitter_limit_total:
            return False
        # Check daily limit
        if self.twitter_count_daily >= self.twitter_limit_daily:
            return False
        return True

    async def add_message(self) -> None:
        """Add a message to the agent's message count.

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                quota_record = (
                    await db.exec(
                        select(AgentQuotaTable).where(AgentQuotaTable.id == self.id)
                    )
                ).first()

                if quota_record:
                    # Update record
                    quota_record.message_count_total += 1
                    quota_record.message_count_monthly += 1
                    quota_record.message_count_daily += 1
                    quota_record.last_message_time = datetime.now(timezone.utc)
                    db.add(quota_record)
                    await db.commit()

                    # Update this instance
                    await db.refresh(quota_record)
                    self.message_count_total = quota_record.message_count_total
                    self.message_count_monthly = quota_record.message_count_monthly
                    self.message_count_daily = quota_record.message_count_daily
                    self.last_message_time = quota_record.last_message_time
                    self.updated_at = quota_record.updated_at
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add message: {str(e)}",
            ) from e

    async def add_autonomous(self) -> None:
        """Add an autonomous operation to the agent's autonomous count.

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                quota_record = (
                    await db.exec(
                        select(AgentQuotaTable).where(AgentQuotaTable.id == self.id)
                    )
                ).first()

                if quota_record:
                    # Update record
                    quota_record.autonomous_count_total += 1
                    quota_record.autonomous_count_monthly += 1
                    quota_record.last_autonomous_time = datetime.now(timezone.utc)
                    db.add(quota_record)
                    await db.commit()

                    # Update this instance
                    await db.refresh(quota_record)
                    self.autonomous_count_total = quota_record.autonomous_count_total
                    self.autonomous_count_monthly = (
                        quota_record.autonomous_count_monthly
                    )
                    self.last_autonomous_time = quota_record.last_autonomous_time
                    self.updated_at = quota_record.updated_at
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add autonomous operation: {str(e)}",
            ) from e

    async def add_twitter_message(self) -> None:
        """Add a twitter message to the agent's twitter count.

        Raises:
            HTTPException: If there are database errors
        """
        try:
            async with get_session() as db:
                quota_record = (
                    await db.exec(
                        select(AgentQuotaTable).where(AgentQuotaTable.id == self.id)
                    )
                ).first()

                if quota_record:
                    # Update record
                    quota_record.twitter_count_total += 1
                    quota_record.twitter_count_daily += 1
                    quota_record.last_twitter_time = datetime.now(timezone.utc)
                    db.add(quota_record)
                    await db.commit()

                    # Update this instance
                    await db.refresh(quota_record)
                    self.twitter_count_total = quota_record.twitter_count_total
                    self.twitter_count_daily = quota_record.twitter_count_daily
                    self.last_twitter_time = quota_record.last_twitter_time
                    self.updated_at = quota_record.updated_at
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add twitter message: {str(e)}",
            ) from e
