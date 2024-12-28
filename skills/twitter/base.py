from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel
from tweepy import Client


class TwitterBaseTool(BaseTool):
    """Base class for Twitter tools."""

    client: Client
    name: str
    description: str
    args_schema: Type[BaseModel]
