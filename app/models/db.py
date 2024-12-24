import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import psycopg
from sqlalchemy import Column, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, Session, SQLModel, create_engine, select

from app.db_mig import safe_migrate
from app.slack import send_slack_message

conn_str = None
conn = None
engine = None


def init_db(
    host: str, username: str, password: str, dbname: str, port: str = "5432"
) -> None:
    """Initialize the database and handle schema updates.

    Args:
        host: Database host
        username: Database username
        password: Database password
        dbname: Database name
        port: Database port (default: 5432)
    """
    global conn_str
    if conn_str is None:
        conn_str = (
            f"postgresql://{username}:{quote_plus(password)}@{host}:{port}/{dbname}"
        )

    # Initialize SQLAlchemy engine
    global engine
    if engine is None:
        engine = create_engine(conn_str)
        # safe_migrate(engine)

    # Initialize psycopg connection
    global conn
    if conn is None:
        conn = psycopg.connect(conn_str, autocommit=True)


def get_db() -> Session:
    with Session(engine) as session:
        yield session


def get_coon_str():
    return conn_str


def get_coon():
    return conn


class Agent(SQLModel, table=True):
    """Agent model."""

    __tablename__ = "agents"

    id: str = Field(primary_key=True)
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
    # if twitter_enabled, twitter_config will be checked
    twitter_enabled: bool = Field(default=False)
    twitter_config: Optional[dict] = Field(sa_column=Column(JSONB, nullable=True))
    twitter_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # crestal skills
    crestal_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # skills not require config
    common_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))
    # skill set
    skill_sets: Optional[Dict[str, Dict[str, Any]]] = Field(
        sa_column=Column(JSONB, nullable=True)
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
    plan: str = Field(default="free")
    message_count_total: int = Field(default=0)
    message_limit_total: int = Field(default=1000)
    message_count_monthly: int = Field(default=0)
    message_limit_monthly: int = Field(default=100)
    message_count_daily: int = Field(default=0)
    message_limit_daily: int = Field(default=10)
    last_message_time: Optional[datetime] = Field(default=None)
    autonomous_count_total: int = Field(default=0)
    autonomous_limit_total: int = Field(default=100)
    autonomous_count_monthly: int = Field(default=0)
    autonomous_limit_monthly: int = Field(default=100)
    last_autonomous_time: Optional[datetime] = Field(default=None)

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
