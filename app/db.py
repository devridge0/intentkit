from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import sessionmaker, declarative_base, Session

SessionLocal = None

def init_db(
    host: str,
    username: str,
    password: str,
    dbname: str,
    port: str = '5432'):
    global SessionLocal
    if SessionLocal is not None:
        return
    engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{dbname}')
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the base model
class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(String, primary_key=True)
    name = Column(String)
    model = Column(String, default='gpt-4o-mini')
    prompt = Column(String)
    wallet_data = Column(String)
    tools = Column(JSON)
