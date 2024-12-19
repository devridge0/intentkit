import requests
from typing import Annotated
from langchain_core.tools import tool
from pydantic import Field


@tool
def search_web3_services(
    keyword: Annotated[str, Field(description="The keyword of the web3 service to search, e.g. `rpc`")]
    ) -> str:
    """This tool will search for web3 services from crestal.network .
    It takes the keyword of the web3 service as input.
    Return a message containing the web3 service search results.
    """
    try:
        response = requests.get(
            f"https://api.service.crestal.network/v1/services?keyword={keyword}"
        )
        services = response.json()
        data = ""
        for service in services:
            data += f"{service['display_name']}:\n{service['summary']}\nhttps://app.crestal.network/lab/service/{service['id']}\n\n"
    except Exception as e:
        return f"Error searching for web3 services {e!s}"
    return data
