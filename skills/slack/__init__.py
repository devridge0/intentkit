"""Slack skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.slack.base import SlackBaseTool
from skills.slack.get_channel import SlackGetChannel
from skills.slack.get_message import SlackGetMessage
from skills.slack.schedule_message import SlackScheduleMessage
from skills.slack.send_message import SlackSendMessage

# we cache skills in system level, because they are stateless
_cache: dict[str, SlackBaseTool] = {}


class SkillStates(TypedDict):
    get_channel: SkillState
    get_message: SkillState
    schedule_message: SkillState
    send_message: SkillState


class Config(SkillConfig):
    """Configuration for Slack skills."""

    slack_bot_token: str
    skill_states: SkillStates


def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[SlackBaseTool]:
    """Get all Slack skills."""
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["skill_states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [
        get_slack_skill(name, store, config.slack_bot_token)
        for name in available_skills
    ]


def get_slack_skill(
    name: str,
    store: SkillStoreABC,
    slack_bot_token: str,
) -> SlackBaseTool:
    """Get a Slack skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data
        slack_bot_token: The Slack bot token for API access

    Returns:
        The requested Slack skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "get_channel":
        if name not in _cache:
            _cache[name] = SlackGetChannel(
                skill_store=store,
                slack_bot_token=slack_bot_token,
            )
        return _cache[name]
    elif name == "get_message":
        if name not in _cache:
            _cache[name] = SlackGetMessage(
                skill_store=store,
                slack_bot_token=slack_bot_token,
            )
        return _cache[name]
    elif name == "schedule_message":
        if name not in _cache:
            _cache[name] = SlackScheduleMessage(
                skill_store=store,
                slack_bot_token=slack_bot_token,
            )
        return _cache[name]
    elif name == "send_message":
        if name not in _cache:
            _cache[name] = SlackSendMessage(
                skill_store=store,
                slack_bot_token=slack_bot_token,
            )
        return _cache[name]
    else:
        raise ValueError(f"Unknown Slack skill: {name}")
