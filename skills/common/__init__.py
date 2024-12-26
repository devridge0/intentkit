from langchain_core.tools import BaseTool

# this is forward compatibility
from skills.crestal.search_web3_services import search_web3_services


def get_common_skill(name: str) -> BaseTool:
    if name == "search_web3_services":
        return search_web3_services
