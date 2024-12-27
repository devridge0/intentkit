from tweepy import Client

from skills.twitter.base import TwitterBaseTool
from skills.twitter.get_mentions import TwitterGetMentions


def get_twitter_skill(name: str, client: Client) -> TwitterBaseTool:
    if name == "get_mentions":
        return TwitterGetMentions(client=client)
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
