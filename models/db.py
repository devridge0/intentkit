from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote_plus

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from models.db_mig import safe_migrate

conn_str = None
conn = None
engine = None


def init_db(
    host: str,
    username: str,
    password: str,
    dbname: str,
    port: str = "5432",
    auto_migrate: bool = True,
) -> None:
    """Initialize the database and handle schema updates.

    Args:
        host: Database host
        username: Database username
        password: Database password
        dbname: Database name
        port: Database port (default: 5432)
        auto_migrate: Whether to run migrations automatically (default: True)
    """
    global conn_str
    if conn_str is None:
        conn_str = (
            f"postgresql://{username}:{quote_plus(password)}@{host}:{port}/{dbname}"
        )

    # Initialize SQLAlchemy engine with pool settings
    global engine
    if engine is None:
        engine = create_engine(
            conn_str,
            pool_size=20,  # Increase pool size
            max_overflow=30,  # Increase max overflow
            pool_timeout=60,  # Increase timeout
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        if auto_migrate:
            safe_migrate(engine)

    # Initialize psycopg connection
    global conn
    if conn is None:
        conn = ConnectionPool(conn_str, open=True, max_idle=20, max_waiting=30)
        if auto_migrate:
            # Check and create PostgresSaver tables
            one_time_coon = conn.getconn()
            one_time_coon.autocommit = True
            memory = PostgresSaver(one_time_coon)
            memory.setup()
            conn.putconn(one_time_coon)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def get_session() -> Session:
    """Get a database session using a context manager.

    This function is designed to be used with the 'with' statement,
    ensuring proper session cleanup.

    Returns:
        Session: A SQLModel session that will be automatically closed

    Example:
        ```python
        with get_session() as session:
            # use session here
            session.query(...)
        # session is automatically closed
        ```
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_coon_str() -> str:
    return conn_str


def get_coon() -> ConnectionPool:
    return conn


def get_engine() -> Engine:
    return engine
