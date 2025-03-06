"""Twitter skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from clients.twitter import TwitterClientConfig
from skills.base import SkillConfig, SkillState
from skills.twitter.base import TwitterBaseTool
from skills.twitter.follow_user import TwitterFollowUser
from skills.twitter.get_mentions import TwitterGetMentions
from skills.twitter.get_timeline import TwitterGetTimeline
from skills.twitter.like_tweet import TwitterLikeTweet
from skills.twitter.post_tweet import TwitterPostTweet
from skills.twitter.reply_tweet import TwitterReplyTweet
from skills.twitter.retweet import TwitterRetweet
from skills.twitter.search_tweets import TwitterSearchTweets

# we cache skills in system level, because they are stateless
_cache: dict[str, TwitterBaseTool] = {}


class SkillStates(TypedDict):
    get_mentions: SkillState
    post_tweet: SkillState
    reply_tweet: SkillState
    get_timeline: SkillState
    follow_user: SkillState
    like_tweet: SkillState
    retweet: SkillState
    search_tweets: SkillState


class Config(SkillConfig, TwitterClientConfig):
    """Configuration for Twitter skills."""

    skill_states: SkillStates


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
        if name not in _cache:
            _cache[name] = TwitterGetMentions(
                skill_store=store,
            )
        return _cache[name]
    elif name == "post_tweet":
        if name not in _cache:
            _cache[name] = TwitterPostTweet(
                skill_store=store,
            )
        return _cache[name]
    elif name == "reply_tweet":
        if name not in _cache:
            _cache[name] = TwitterReplyTweet(
                skill_store=store,
            )
        return _cache[name]
    elif name == "get_timeline":
        if name not in _cache:
            _cache[name] = TwitterGetTimeline(
                skill_store=store,
            )
        return _cache[name]
    elif name == "follow_user":
        if name not in _cache:
            _cache[name] = TwitterFollowUser(
                skill_store=store,
            )
        return _cache[name]
    elif name == "like_tweet":
        if name not in _cache:
            _cache[name] = TwitterLikeTweet(
                skill_store=store,
            )
        return _cache[name]
    elif name == "retweet":
        if name not in _cache:
            _cache[name] = TwitterRetweet(
                skill_store=store,
            )
        return _cache[name]
    elif name == "search_tweets":
        if name not in _cache:
            _cache[name] = TwitterSearchTweets(
                skill_store=store,
            )
        return _cache[name]
    else:
        raise ValueError(f"Unknown Twitter skill: {name}")
