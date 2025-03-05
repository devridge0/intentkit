"""Twitter skills."""

from abstracts.skill import SkillStoreABC
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


class Config(SkillConfig):
    """Configuration for Twitter skills."""


def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[TwitterBaseTool]:
    """Get all Twitter skills."""
    # always return public skills
    resp = [get_twitter_skill(name, store) for name in config["public_skills"]]
    # return private skills only if is_private
    if is_private and "private_skills" in config:
        resp.extend(
            [
                get_twitter_skill(name, store)
                for name in config["private_skills"]
                # remove duplicates
                if name not in config["public_skills"]
            ]
        )
    return resp


def get_twitter_skill(
    name: str,
    store: SkillStoreABC,
) -> TwitterBaseTool:
    """Get a Twitter skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested Twitter skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "get_mentions":
        return TwitterGetMentions(
            skill_store=store,
        )
    elif name == "post_tweet":
        return TwitterPostTweet(
            skill_store=store,
        )
    elif name == "reply_tweet":
        return TwitterReplyTweet(
            skill_store=store,
        )
    elif name == "get_timeline":
        return TwitterGetTimeline(
            skill_store=store,
        )
    elif name == "follow_user":
        return TwitterFollowUser(
            skill_store=store,
        )
    elif name == "like_tweet":
        return TwitterLikeTweet(
            skill_store=store,
        )
    elif name == "retweet":
        return TwitterRetweet(
            skill_store=store,
        )
    elif name == "search_tweets":
        return TwitterSearchTweets(
            skill_store=store,
        )
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
