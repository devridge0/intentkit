import logging
from typing import ClassVar, List, Type

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


from .base import NationBaseTool

logger = logging.getLogger(__name__)


class NftCheckInput(BaseModel):
    nation_wallet_address: str = Field(default="nation wallet address")

class NftCheck(NationBaseTool):
    """Implementation of the NFT Check tool.

    Args:
        nation_wallet_address: The wallet address of the nation.

    Returns:
        str: Formatted NFT check results based on the nation wallet address.
    """

    name: str = "nft_check"
    description: str = "Check user nation pass NFTs stats in nation, including usage status and linked agents."
    args_schema: Type[BaseModel] = NftCheckInput

    async def _arun(self, nation_wallet_address: str, config: RunnableConfig = None) -> str:
        """Implementation of the NFT Check tool.

        Args:
            nation_wallet_address: The wallet address of the nation.

        Returns:
            str: Formatted NFT check results based on the nation wallet address.
        """

        context = self.context_from_config(config)
        logger.debug(f"nft_check.py: Running NFT check with context {context}")

        url = f"{self.get_base_url()}/v1/users/{nation_wallet_address}"

        api_key = self.get_api_key()

        if not api_key:
            raise ValueError("Backend API key not found")

        headers = {
            "Accept": "application/json",
            "x-api-key": api_key
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code != 200:
                    logger.error(
                        f"nft_check.py: Error from API: {response.status_code} - {response.text}"
                    )
                    return f"Error fetching NFT data: {response.status_code} - {response.text}"

                data = response.json()
                nfts = data.get("nfts", [])

                if not nfts:
                    return f"No NFTs found for wallet address: {nation_wallet_address}"

                # Format the NFT data
                formatted_results = f"NFTs for wallet address '{nation_wallet_address}':\n\n"

                for i, nft in enumerate(nfts, 1):
                    token_id = nft.get("token_id", "Unknown")
                    used_by = nft.get("used_by", None)
                    linked_agent_id = nft.get("linked_agent_id", "None")

                    formatted_results += f"{i}. Token ID: {token_id}\n"
                    if used_by:
                        formatted_results += f"   Status: Used by Agent ID {linked_agent_id}\n"
                    else:
                        formatted_results += "   Status: Available\n"
                    formatted_results += "\n"

                return formatted_results.strip()

        except httpx.TimeoutException:
            logger.error("nft_check.py: Request timed out")
            return "The request to the NFT API timed out. Please try again later."
        except Exception as e:
            logger.error(f"nft_check.py: Error fetching NFT data: {e}", exc_info=True)
            return "An error occurred while fetching NFT data. Please try again later."
