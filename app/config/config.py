# app/config.py
import json
import logging
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import botocore.session
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

from utils.logging import setup_logging

logger = logging.getLogger(__name__)


def load_from_aws(name):
    client = botocore.session.get_session().create_client("secretsmanager")
    cache_config = SecretCacheConfig()
    cache = SecretCache(config=cache_config, client=client)
    secret = cache.get_secret_string(name)
    return json.loads(secret)


class Config:
    def __init__(self):
        # this part can only be load from env
        self.env = os.getenv("ENV", "local")
        self.release = os.getenv("RELEASE", "local")
        secret_name = os.getenv("AWS_SECRET_NAME")
        db_secret_name = os.getenv("AWS_DB_SECRET_NAME")
        # load from aws secrets manager
        if secret_name:
            self.secrets = load_from_aws(secret_name)
        else:
            self.secrets = {}
        if db_secret_name:
            self.db = load_from_aws(db_secret_name)
            # format the db config
            self.db["port"] = str(self.db["port"])
            # only keep the necessary fields
            self.db = {
                k: v
                for k, v in self.db.items()
                if k in ["username", "password", "host", "dbname", "port"]
            }
        else:
            self.db = {
                "username": os.getenv("DB_USERNAME"),
                "password": os.getenv("DB_PASSWORD"),
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "dbname": os.getenv("DB_NAME"),
            }
        # validate the db config
        if "host" not in self.db:
            raise ValueError("db config is not set")
        # this part can be load from env or aws secrets manager
        self.db["auto_migrate"] = self.load("DB_AUTO_MIGRATE", "true") == "true"
        self.debug = self.load("DEBUG") == "true"
        self.debug_resp = (
            self.load("DEBUG_RESP", "false") == "true"
        )  # Agent response with thought steps and time cost
        self.cdp_api_key_name = self.load("CDP_API_KEY_NAME")
        self.cdp_api_key_private_key = self.load("CDP_API_KEY_PRIVATE_KEY")
        self.openai_api_key = self.load("OPENAI_API_KEY")
        self.slack_token = self.load("SLACK_TOKEN")  # For alert purposes only
        self.slack_channel = self.load("SLACK_CHANNEL")
        # Now we know the env, set up logging
        setup_logging(self.env, self.debug)
        logger.info("config loaded")

    def load(self, key, default=None):
        """Load a secret from the secrets map or env"""
        return self.secrets.get(key, os.getenv(key, default))


config: Config = Config()
