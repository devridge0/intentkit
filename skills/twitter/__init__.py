"""Twitter skills."""

from tweepy import Client

from abstracts.skill import SkillStoreABC
from skills.twitter.base import TwitterBaseTool
from skills.twitter.get_mentions import TwitterGetMentions
from skills.twitter.get_timeline import TwitterGetTimeline
from skills.twitter.post_tweet import TwitterPostTweet
from skills.twitter.reply_tweet import TwitterReplyTweet


def get_twitter_skill(
    name: str, client: Client, store: SkillStoreABC, agent_id: str
) -> TwitterBaseTool:
    if name == "get_mentions":
        return TwitterGetMentions(client=client, store=store, agent_id=agent_id)
    elif name == "post_tweet":
        return TwitterPostTweet(client=client, store=store, agent_id=agent_id)
    elif name == "reply_tweet":
        return TwitterReplyTweet(client=client, store=store, agent_id=agent_id)
    elif name == "get_timeline":
        return TwitterGetTimeline(client=client, store=store, agent_id=agent_id)
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
