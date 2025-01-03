from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, func, Identity, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, Session, SQLModel, select

from utils.slack_alert import send_slack_message


class Agent(SQLModel, table=True):
    """Agent model."""

    __tablename__ = "agents"

    id: str = Field(primary_key=True)
    number: int = Field(
        sa_column=Column(BigInteger, Identity(start=1, increment=1), nullable=False)
    )
    # AI part
    name: Optional[str] = Field(default=None)
    model: str = Field(default="gpt-4o-mini")
    prompt: Optional[str]
    # autonomous mode
    autonomous_enabled: bool = Field(default=False)
    autonomous_minutes: Optional[int]
    autonomous_prompt: Optional[str]
    # if cdp_enabled, will load cdp skills
    # if the cdp_skills is empty, will load all
    cdp_enabled: bool = Field(default=False)
    cdp_skills: Optional[List[str]] = Field(sa_column=Column(JSONB, nullable=True))
    cdp_wallet_data: Optional[str]
    cdp_network_id: Optional[str]
    # if twitter_enabled, the twitter_entrypoint will be enabled, twitter_config will be checked
    twitter_enabled: bool = Field(default=False)
    twitter_config: Optional[dict] = Field(sa_column=Column(JSONB, nullable=True))
    # twitter skills require config, but not require twitter_enabled flag.
    # As long as twitter_skills is not empty, the corresponding skills will be loaded.
    twitter_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    telegram_enabled: bool = Field(default=False)
    telegram_config: Optional[dict] = Field(sa_column=Column(JSONB, nullable=True))
    # twitter skills require config, but not require twitter_enabled flag.
    # As long as twitter_skills is not empty, the corresponding skills will be loaded.
    telegram_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # crestal skills
    crestal_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # skills not require config
    common_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # skill set
    skill_sets: Optional[Dict[str, Dict[str, Any]]] = Field(
        sa_column=Column(JSONB, nullable=True)
    )
    # auto timestamp
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc),
        },
        nullable=False,
    )

    def create_or_update(self, db: Session) -> None:
        """Create the agent if not exists, otherwise update it."""
        existing_agent = db.exec(select(Agent).where(Agent.id == self.id)).first()
        if existing_agent:
            # Update existing agent
            for field in self.model_fields:
                if field != "id" and field != "cdp_wallet_data":  # Skip the primary key
                    if getattr(self, field) is not None:
                        setattr(existing_agent, field, getattr(self, field))
            db.add(existing_agent)
        else:
            # Create new agent
            db.add(self)
            # Count the total agents
            total_agents = db.exec(select(func.count()).select_from(Agent)).one()
            # Send a message to Slack
            send_slack_message(
                f"New agent created: {self.id}",
                attachments=[
                    {"text": f"Total agents: {total_agents}", "color": "good"}
                ],
            )
        db.commit()


class AgentQuota(SQLModel, table=True):
    """AgentQuota model."""

    __tablename__ = "agent_quotas"

    id: str = Field(primary_key=True)
    plan: str = Field(default="self-hosted")
    message_count_total: int = Field(default=0)
    message_limit_total: int = Field(default=9999)
    message_count_monthly: int = Field(default=0)
    message_limit_monthly: int = Field(default=9999)
    message_count_daily: int = Field(default=0)
    message_limit_daily: int = Field(default=9999)
    last_message_time: Optional[datetime] = Field(default=None)
    autonomous_count_total: int = Field(default=0)
    autonomous_limit_total: int = Field(default=9999)
    autonomous_count_monthly: int = Field(default=0)
    autonomous_limit_monthly: int = Field(default=9999)
    last_autonomous_time: Optional[datetime] = Field(default=None)
    twitter_count_total: int = Field(default=0)
    twitter_limit_total: int = Field(default=9999)
    twitter_count_daily: int = Field(default=0)
    twitter_limit_daily: int = Field(default=9999)
    last_twitter_time: Optional[datetime] = Field(default=None)
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc),
        },
        nullable=False,
    )

    @staticmethod
    def get(id: str, db: Session) -> "AgentQuota":
        """Get agent quota by id, if not exists, create a new one."""
        aq = db.exec(select(AgentQuota).where(AgentQuota.id == id)).one_or_none()
        if aq is None:
            aq = AgentQuota(id=id)
            db.add(aq)
            db.commit()
        return aq

    def has_message_quota(self, db: Session) -> bool:
        """Check if the agent has message quota."""
        return (
            self.message_count_monthly < self.message_limit_monthly
            and self.message_count_daily < self.message_limit_daily
            and self.message_count_total < self.message_limit_total
        )

    def has_autonomous_quota(self, db: Session) -> bool:
        """Check if the agent has autonomous quota."""
        if not self.has_message_quota(db):
            return False
        return (
            self.autonomous_count_monthly < self.autonomous_limit_monthly
            and self.autonomous_count_total < self.autonomous_limit_total
        )

    def has_twitter_quota(self, db: Session) -> bool:
        """Check if the agent has twitter quota."""
        if not self.has_message_quota(db):
            return False
        return (
            self.twitter_count_daily < self.twitter_limit_daily
            and self.twitter_count_total < self.twitter_limit_total
        )

    def add_message(self, db: Session) -> None:
        """Add a message to the agent's message count."""
        self.message_count_monthly += 1
        self.message_count_daily += 1
        self.message_count_total += 1
        self.last_message_time = datetime.now()
        db.add(self)
        db.commit()

    def add_autonomous(self, db: Session) -> None:
        """Add an autonomous message to the agent's autonomous count."""
        self.message_count_daily += 1
        self.message_count_monthly += 1
        self.message_count_total += 1
        self.autonomous_count_monthly += 1
        self.autonomous_count_total += 1
        self.last_autonomous_time = datetime.now()
        self.last_message_time = datetime.now()
        db.add(self)
        db.commit()

    def add_twitter(self, db: Session) -> None:
        """Add a twitter message to the agent's twitter count."""
        self.message_count_daily += 1
        self.message_count_monthly += 1
        self.message_count_total += 1
        self.twitter_count_daily += 1
        self.twitter_count_total += 1
        self.last_twitter_time = datetime.now()
        self.last_message_time = datetime.now()
        db.add(self)
        db.commit()


class AgentPluginData(SQLModel, table=True):
    """Model for storing plugin-specific data for agents.

    This model uses a composite primary key of (agent_id, plugin, key) to store
    plugin-specific data for agents in a flexible way.

    Attributes:
        agent_id: ID of the agent this data belongs to
        plugin: Name of the plugin this data is for
        key: Key for this specific piece of data
        data: JSON data stored for this key
    """

    __tablename__ = "agent_plugin_data"

    agent_id: str = Field(primary_key=True)
    plugin: str = Field(primary_key=True)
    key: str = Field(primary_key=True)
    data: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=True))
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc),
        },
        nullable=False,
    )

    @classmethod
    def get(
        cls, agent_id: str, plugin: str, key: str, db: Session
    ) -> Optional["AgentPluginData"]:
        """Get plugin data for an agent.

        Args:
            agent_id: ID of the agent
            plugin: Name of the plugin
            key: Data key
            db: Database session

        Returns:
            AgentPluginData if found, None otherwise
        """
        return db.exec(
            select(cls).where(
                cls.agent_id == agent_id,
                cls.plugin == plugin,
                cls.key == key,
            )
        ).first()

    def save(self, db: Session) -> None:
        """Save or update plugin data.

        Args:
            db: Database session
        """
        existing = db.exec(
            select(AgentPluginData).where(
                AgentPluginData.agent_id == self.agent_id,
                AgentPluginData.plugin == self.plugin,
                AgentPluginData.key == self.key,
            )
        ).first()

        if existing:
            # Update existing record
            for field in self.model_fields:
                if getattr(self, field) is not None:
                    setattr(existing, field, getattr(self, field))
            db.add(existing)
        else:
            # Create new record
            db.add(self)

        db.commit()
