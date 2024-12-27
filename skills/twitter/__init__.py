"""Twitter skills."""

from tweepy import Client

from skills.twitter.base import TwitterBaseTool
from skills.twitter.get_mentions import TwitterGetMentions
from skills.twitter.post_tweet import TwitterPostTweet
from skills.twitter.reply_tweet import TwitterReplyTweet


def get_twitter_skill(name: str, client: Client) -> TwitterBaseTool:
    if name == "get_mentions":
        return TwitterGetMentions(client=client)
    elif name == "post_tweet":
        return TwitterPostTweet(client=client)
    elif name == "reply_tweet":
        return TwitterReplyTweet(client=client)
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
