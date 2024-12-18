from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List, Optional

engine = None


def init_db(
        host: str,
        username: str,
        password: str,
        dbname: str,
        port: str = '5432'
) -> None:
    global engine
    if engine is None:
        engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{dbname}')
    SQLModel.metadata.create_all(engine)


def get_db() -> Session:
    with Session(engine) as session:
        yield session


class Agent(SQLModel, table=True):
    __tablename__ = 'agents'

    id: str = Field(primary_key=True)
    # AI part
    name: Optional[str] = Field(default=None)
    model: str = Field(default='gpt-4o-mini')
    prompt: Optional[str]
    # auto thought mode
    thought_enabled: bool
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
    # skills not require config
    common_skills: Optional[List[str]] = Field(sa_column=Column(ARRAY(String)))

    def create_or_update(self, db: Session) -> None:
        """Create the agent if not exists, otherwise update it."""
        existing_agent = db.exec(select(Agent).where(Agent.id == self.id)).first()
        if existing_agent:
            # Update existing agent
            for field in self.model_fields:
                if field != 'id':  # Skip the primary key
                    setattr(existing_agent, field, getattr(self, field))
            db.add(existing_agent)
        else:
            # Create new agent
            db.add(self)
        db.commit()
