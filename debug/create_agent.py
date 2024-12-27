import logging

from app.config.config import config
from app.models.agent import Agent
from app.models.db import get_db, init_db

if config.env == "local":
    # Set up logging configuration
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

init_db(**config.db)
db = next(get_db())
agent = Agent(
    id="local",
    name="IntentKit",
    model="gpt-4o-mini",  # This repetition could be omitted if default is intended
    prompt="",  # Confirm if an empty prompt is acceptable
    autonomous_enabled=False,  # This field must be provided
    autonomous_content="",  # Optional, provide if needed
    autonomous_minutes=None,  # Optional, provide if needed
    cdp_enabled=True,
    cdp_skills=[],  # Confirm if loading all skills when empty is the desired behavior
    cdp_wallet_data="",  # Assuming wallet_data was meant to be cdp_wallet_data
    cdp_network_id="base-sepolia",
    twitter_enabled=False,
    twitter_config={},  # Ensure this dict structure aligns with expected config format
    twitter_skills=[],  # Confirm if no specific Twitter skills are to be enabled
    common_skills=[],  # Confirm if no common skills are to be added initially
)

agent.create_or_update(db)
