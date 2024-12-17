import logging

from app.db import init_db, get_db, Agent
from app.config import config

if config.env == "local":
    # Set up logging configuration
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

init_db(**config.db)
db = next(get_db())
agent = Agent(
    id="local",
    name="IntentKit",
    model="gpt-4o-mini",
    prompt="",
    wallet_data="",
    cdp_enabled=False,
    cdp_skills=[],
    twitter_enabled=False,
    twitter_config={},
    twitter_skills=[],
    common_skills=[],
)

agent.create_or_update(db)
