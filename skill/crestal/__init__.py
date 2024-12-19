from langchain_core.tools import BaseTool

from skill.crestal.search_web3_services import search_web3_services

def get_crestal_skill(name: str) -> BaseTool:
    if name == "search_web3_services":
        return search_web3_services
