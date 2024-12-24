"All skill set definitions"
from typing import Dict, List, Optional, Union

from langchain_core.tools import BaseTool

from skill_set.base import SkillSetOptions
from skill_set.slack import SlackSkillSet, SlackSkillSetOptions


def get_skill_set(
    name: str, config: Optional[Union[Dict, SkillSetOptions]] = None
) -> List[BaseTool]:
    if name == "slack":
        if not config:
            raise ValueError("Slack skill set requires config")
        return SlackSkillSet(
            options=SlackSkillSetOptions.model_validate(config)
        ).get_tools()
    else:
        raise ValueError(f"Unknown skill set: {name}")
