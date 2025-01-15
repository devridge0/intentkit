"""Twitter skills."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from abstracts.twitter import TwitterABC
from skills.twitter.base import TwitterBaseTool
from skills.twitter.get_mentions import TwitterGetMentions
from skills.twitter.get_timeline import TwitterGetTimeline
from skills.twitter.post_tweet import TwitterPostTweet
from skills.twitter.reply_tweet import TwitterReplyTweet


def get_twitter_skill(
    name: str,
    twitter: TwitterABC,
    store: SkillStoreABC,
    agent_id: str,
    agent_store: AgentStoreABC,
) -> TwitterBaseTool:
    """Get a Twitter skill by name.

    Args:
        name: The name of the skill to get
        twitter: The Twitter client abstraction
        store: The skill store for persisting data
        agent_id: The ID of the agent
        agent_store: The agent store for persisting data

    Returns:
        The requested Twitter skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "get_mentions":
        return TwitterGetMentions(
            twitter=twitter, store=store, agent_id=agent_id, agent_store=agent_store
        )
    elif name == "post_tweet":
        return TwitterPostTweet(
            twitter=twitter, store=store, agent_id=agent_id, agent_store=agent_store
        )
    elif name == "reply_tweet":
        return TwitterReplyTweet(
            twitter=twitter, store=store, agent_id=agent_id, agent_store=agent_store
        )
    elif name == "get_timeline":
        return TwitterGetTimeline(
            twitter=twitter, store=store, agent_id=agent_id, agent_store=agent_store
        )
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
