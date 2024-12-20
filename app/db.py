import logging
import psycopg
from sqlalchemy import Column, String, func, Table, MetaData, text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List, Optional
from urllib.parse import quote_plus
import os

from app.db_mig import safe_migrate
from app.slack import send_slack_message

conn_str = None
conn = None
engine = None


def init_db(
        host: str,
        username: str,
        password: str,
        dbname: str,
        port: str = '5432'
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
        conn_str = f'postgresql://{username}:{quote_plus(password)}@{host}:{port}/{dbname}'
    
    # Initialize SQLAlchemy engine
    global engine
    if engine is None:
        engine = create_engine(conn_str)
        safe_migrate(engine)
    
    # Initialize psycopg connection
    global conn
    if conn is None:
        conn = psycopg.connect(conn_str,autocommit=True)
    
def get_db() -> Session:
    with Session(engine) as session:
        yield session

def get_coon_str():
    return conn_str

def get_coon():
    return conn

class Agent(SQLModel, table=True):
    """Agent model."""
    __tablename__ = 'agents'

    id: str = Field(primary_key=True)
    # AI part
    name: Optional[str] = Field(default=None)
    model: str = Field(default='gpt-4o-mini')
    prompt: Optional[str]
    # auto thought mode
    thought_enabled: bool = Field(default=False)
    thought_content: Optional[str]
    thought_minutes: Optional[int]
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

    def create_or_update(self, db: Session) -> None:
        """Create the agent if not exists, otherwise update it."""
        existing_agent = db.exec(select(Agent).where(Agent.id == self.id)).first()
        if existing_agent:
            # Update existing agent
            for field in self.model_fields:
                if field != 'id' and field != 'cdp_wallet_data':  # Skip the primary key
                    setattr(existing_agent, field, getattr(self, field))
            db.add(existing_agent)
        else:
            # Create new agent
            db.add(self)
            # Count the total agents
            total_agents = db.exec(select(func.count()).select_from(Agent)).one()
            # Send a message to Slack
            send_slack_message(f"New agent created: {self.id}",attachments=[{
                "text": f"Total agents: {total_agents}",
                "color": "good"
            }])
        db.commit()
