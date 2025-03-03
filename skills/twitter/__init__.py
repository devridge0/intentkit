"""Twitter skills."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from abstracts.twitter import TwitterABC
from clients import TwitterClient, TwitterClientConfig
from models.skill import SkillConfig
from skills.twitter.base import TwitterBaseTool
from skills.twitter.follow_user import TwitterFollowUser
from skills.twitter.get_mentions import TwitterGetMentions
from skills.twitter.get_timeline import TwitterGetTimeline
from skills.twitter.like_tweet import TwitterLikeTweet
from skills.twitter.post_tweet import TwitterPostTweet
from skills.twitter.reply_tweet import TwitterReplyTweet
from skills.twitter.retweet import TwitterRetweet
from skills.twitter.search_tweets import TwitterSearchTweets


class Config(SkillConfig, TwitterClientConfig):
    """Configuration for Twitter skills."""


def get_skills(
    config: "Config",
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    **_,
) -> list[TwitterBaseTool]:
    """Get all Twitter skills."""
    # always return public skills
    twitter = TwitterClient(agent_id, agent_store, config)
    resp = [
        get_twitter_skill(name, twitter, store, agent_id, agent_store)
        for name in config["public_skills"]
    ]
    # return private skills only if is_private
    if is_private and "private_skills" in config:
        resp.extend(
            [
                get_twitter_skill(name, twitter, store, agent_id, agent_store)
                for name in config["private_skills"]
                # remove duplicates
                if name not in config["public_skills"]
            ]
        )
    return resp


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
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "post_tweet":
        return TwitterPostTweet(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "reply_tweet":
        return TwitterReplyTweet(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "get_timeline":
        return TwitterGetTimeline(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "follow_user":
        return TwitterFollowUser(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "like_tweet":
        return TwitterLikeTweet(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "retweet":
        return TwitterRetweet(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "search_tweets":
        return TwitterSearchTweets(
            twitter=twitter,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
