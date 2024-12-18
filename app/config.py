# app/config.py
import json
import os

import botocore.session
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

def load_from_aws(name):
    client = botocore.session.get_session().create_client('secretsmanager')
    cache_config = SecretCacheConfig()
    cache = SecretCache(config=cache_config, client=client)
    secret = cache.get_secret_string(name)
    return json.loads(secret)

class Config:
    def __init__(self):
        # this part can only be load from env
        self.env = os.getenv("ENV", "local")
        self.release = os.getenv("RELEASE", "local")
        # load secret map from aws secrets manager
        secret_name = 'intentkit/' + self.env
        if self.env == "testnet-dev":
            self.secrets = load_from_aws(secret_name)
            self.db = load_from_aws('rds/crestal-chat-test/rw')
        elif self.env == "testnet-prod":
            self.secrets = load_from_aws(secret_name)
            self.db = load_from_aws('rds/crestal-chat/rw')
        else:
            self.secrets = {}
            self.db = {
                "username": os.getenv("DB_USERNAME"),
                "password": os.getenv("DB_PASSWORD"),
                "host": os.getenv("DB_HOST"),
                "port": os.getenv("DB_PORT"),
                "dbname": os.getenv("DB_NAME"),
            }
        # format the db config
        self.db['port'] = str(self.db['port'])
        if "host" not in self.db:
            raise ValueError("db config is not set")
        self.db = {k: v for k, v in self.db.items() if k in ["username", "password", "host", "dbname", "port"]}
        # this part can be load from env or aws secrets manager
        self.cdp_api_key_name = self.load("CDP_API_KEY_NAME")
        self.cdp_api_key_private_key = self.load("CDP_API_KEY_PRIVATE_KEY")
        self.openai_api_key = self.load("OPENAI_API_KEY")
    def load(self, key):
        """Load a secret from the secrets map or env"""
        return self.secrets.get(key, os.getenv(key))

config = Config()
