"""Fetching blockchain data using Moralis Blockchain API."""

import logging
from typing import List, Optional, Type, Union

from pydantic import BaseModel, Field

from skills.moralis.api import (
    get_block_by_date,
    get_block_by_hash_or_number,
    get_latest_block_number,
)
from skills.moralis.base import WalletBaseTool

logger = logging.getLogger(__name__)


class FetchLatestBlockInput(BaseModel):
    """Input for FetchLatestBlock tool."""

    chain_id: int = Field(1, description="Chain ID (default: Ethereum mainnet)")


class FetchBlockByHashOrNumberInput(BaseModel):
    """Input for FetchBlockByHashOrNumber tool."""

    block_identifier: str = Field(..., description="Block hash or number")
    chain_id: int = Field(1, description="Chain ID (default: Ethereum mainnet)")


class FetchBlockByDateInput(BaseModel):
    """Input for FetchBlockByDate tool."""

    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    chain_id: int = Field(1, description="Chain ID (default: Ethereum mainnet)")


class Transaction(BaseModel):
    """Model for transaction in block."""

    hash: str = Field(..., description="Transaction hash")
    nonce: str = Field(..., description="Nonce")
    from_address: str = Field(..., description="From address")
    to_address: Optional[str] = Field(None, description="To address")
    value: str = Field(..., description="Value in wei")
    gas: str = Field(..., description="Gas limit")
    gas_price: str = Field(..., description="Gas price")
    transaction_index: str = Field(..., description="Transaction index")


class Block(BaseModel):
    """Model for block data."""

    hash: str = Field(..., description="Block hash")
    number: str = Field(..., description="Block number")
    timestamp: str = Field(..., description="Block timestamp")
    parent_hash: str = Field(..., description="Parent hash")
    nonce: str = Field(..., description="Nonce")
    sha3_uncles: str = Field(..., description="SHA3 uncles")
    logs_bloom: str = Field(..., description="Logs bloom")
    transactions_root: str = Field(..., description="Transactions root")
    state_root: str = Field(..., description="State root")
    receipts_root: str = Field(..., description="Receipts root")
    miner: str = Field(..., description="Miner address")
    difficulty: str = Field(..., description="Difficulty")
    total_difficulty: str = Field(..., description="Total difficulty")
    size: str = Field(..., description="Block size")
    gas_limit: str = Field(..., description="Gas limit")
    gas_used: str = Field(..., description="Gas used")
    transactions: Optional[List[Union[str, Transaction]]] = Field(
        None, description="Transactions"
    )
    uncles: Optional[List[str]] = Field(None, description="Uncles")
    extra_data: Optional[str] = Field(None, description="Extra data")


class BlockchainDataOutput(BaseModel):
    """Output for blockchain data tools."""

    chain_id: int = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    block_number: Optional[str] = Field(None, description="Block number")
    block: Optional[Block] = Field(None, description="Block data")
    error: Optional[str] = Field(None, description="Error message if any")


class FetchLatestBlock(WalletBaseTool):
    """Tool for fetching the latest block number.

    This tool retrieves the latest block number from a blockchain network.
    """

    name: str = "moralis_fetch_latest_block"
    description: str = (
        "This tool fetches the latest block number from a blockchain network.\n"
        "Provide a chain ID to get the latest block number.\n"
        "Returns the block number of the most recently mined block on the specified chain.\n"
        "Use this tool when a user wants to know the current state of a blockchain."
    )
    args_schema: Type[BaseModel] = FetchLatestBlockInput

    async def _arun(
        self,
        chain_id: int = 1,
        **kwargs,
    ) -> BlockchainDataOutput:
        """Fetch the latest block number.

        Args:
            chain_id: Chain ID (default: Ethereum mainnet)

        Returns:
            BlockchainDataOutput containing the latest block number
        """
        try:
            # Fetch the latest block number
            block_data = await get_latest_block_number(self.api_key, chain_id)

            if "error" in block_data:
                return BlockchainDataOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=block_data["error"],
                )

            # Process the data
            block_number = block_data.get("result", {}).get("number", "")

            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                block_number=block_number,
            )

        except Exception as e:
            logger.error(f"Error fetching latest block number: {str(e)}")
            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                error=str(e),
            )


class FetchBlockByHashOrNumber(WalletBaseTool):
    """Tool for fetching block data by hash or number.

    This tool retrieves detailed information about a block by its hash or number.
    """

    name: str = "moralis_fetch_block_by_hash_or_number"
    description: str = (
        "This tool fetches block data by hash or number.\n"
        "Provide a block hash or number and optionally a chain ID to get detailed block data.\n"
        "Returns detailed information about the specified block, including transactions, timestamp, gas used, etc.\n"
        "Use this tool when a user wants to analyze a specific block on a blockchain."
    )
    args_schema: Type[BaseModel] = FetchBlockByHashOrNumberInput

    async def _arun(
        self,
        block_identifier: str,
        chain_id: int = 1,
        **kwargs,
    ) -> BlockchainDataOutput:
        """Fetch block data by hash or number.

        Args:
            block_identifier: Block hash or number
            chain_id: Chain ID (default: Ethereum mainnet)

        Returns:
            BlockchainDataOutput containing block data
        """
        try:
            # Fetch block data
            block_data = await get_block_by_hash_or_number(
                self.api_key, block_identifier, chain_id
            )

            if "error" in block_data:
                return BlockchainDataOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=block_data["error"],
                )

            # Process the data
            if "result" in block_data:
                block_data = block_data["result"]

            # Create Block model
            block = Block(**block_data)

            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                block_number=block.number,
                block=block,
            )

        except Exception as e:
            logger.error(f"Error fetching block data: {str(e)}")
            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                error=str(e),
            )


class FetchBlockByDate(WalletBaseTool):
    """Tool for fetching block data by date.

    This tool retrieves block information based on a specific date.
    """

    name: str = "moralis_fetch_block_by_date"
    description: str = (
        "This tool fetches block data by date.\n"
        "Provide a date in ISO format (YYYY-MM-DD) and optionally a chain ID to get block data.\n"
        "Returns information about the block that was mined closest to the specified date.\n"
        "Use this tool when a user wants to find out what was happening on a blockchain at a particular date."
    )
    args_schema: Type[BaseModel] = FetchBlockByDateInput

    async def _arun(
        self,
        date: str,
        chain_id: int = 1,
        **kwargs,
    ) -> BlockchainDataOutput:
        """Fetch block data by date.

        Args:
            date: Date in ISO format (YYYY-MM-DD)
            chain_id: Chain ID (default: Ethereum mainnet)

        Returns:
            BlockchainDataOutput containing block data
        """
        try:
            # Fetch block data by date
            block_data = await get_block_by_date(self.api_key, date, chain_id)

            if "error" in block_data:
                return BlockchainDataOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=block_data["error"],
                )

            # Get block number from the date query
            block_number = block_data.get("result", {}).get("block", "")

            if not block_number:
                return BlockchainDataOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error="No block found for the specified date",
                )

            # Fetch block data by number
            block_details = await get_block_by_hash_or_number(
                self.api_key, block_number, chain_id
            )

            if "error" in block_details:
                return BlockchainDataOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    block_number=block_number,
                    error=block_details["error"],
                )

            # Process the data
            if "result" in block_details:
                block_details = block_details["result"]

            # Create Block model
            block = Block(**block_details)

            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                block_number=block_number,
                block=block,
            )

        except Exception as e:
            logger.error(f"Error fetching block by date: {str(e)}")
            return BlockchainDataOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                error=str(e),
            )
