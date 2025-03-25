"""Fetching blockchain transaction data using Moralis Blockchain API."""

import logging
from typing import List, Optional, Type, Union

from pydantic import BaseModel, Field

from skills.moralis.api import (
    get_decoded_transaction_by_hash,
    get_transaction_by_hash,
)
from skills.moralis.base import WalletBaseTool

logger = logging.getLogger(__name__)


class FetchTransactionByHashInput(BaseModel):
    """Input for FetchTransactionByHash tool."""

    transaction_hash: str = Field(..., description="Transaction hash")
    chain_id: int = Field(1, description="Chain ID (default: Ethereum mainnet)")
    include_internal: bool = Field(
        False, description="Whether to include internal transactions"
    )
    decode: bool = Field(True, description="Whether to decode the transaction data")


class DecodedParam(BaseModel):
    """Model for decoded parameter."""

    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Parameter value")
    type: str = Field(..., description="Parameter type")


class DecodedEvent(BaseModel):
    """Model for decoded event."""

    signature: str = Field(..., description="Event signature")
    label: str = Field(..., description="Event label")
    type: str = Field(..., description="Event type")
    params: List[DecodedParam] = Field(..., description="Event parameters")


class DecodedCall(BaseModel):
    """Model for decoded call."""

    signature: str = Field(..., description="Function signature")
    label: str = Field(..., description="Function label")
    type: str = Field(..., description="Function type")
    params: List[DecodedParam] = Field(..., description="Function parameters")


class TransactionLog(BaseModel):
    """Model for transaction log."""

    log_index: str = Field(..., description="Log index")
    transaction_hash: str = Field(..., description="Transaction hash")
    transaction_index: str = Field(..., description="Transaction index")
    address: str = Field(..., description="Contract address")
    data: str = Field(..., description="Log data")
    topic0: Optional[str] = Field(None, description="Topic 0")
    topic1: Optional[str] = Field(None, description="Topic 1")
    topic2: Optional[str] = Field(None, description="Topic 2")
    topic3: Optional[str] = Field(None, description="Topic 3")
    block_timestamp: str = Field(..., description="Block timestamp")
    block_number: str = Field(..., description="Block number")
    block_hash: str = Field(..., description="Block hash")
    decoded_event: Optional[DecodedEvent] = Field(None, description="Decoded event")


class InternalTransaction(BaseModel):
    """Model for internal transaction."""

    transaction_hash: str = Field(..., description="Transaction hash")
    block_number: Union[int, str] = Field(..., description="Block number")
    block_hash: str = Field(..., description="Block hash")
    type: str = Field(..., description="Transaction type (CALL, CREATE, etc.)")
    from_address: str = Field(..., description="From address")
    to_address: str = Field(..., description="To address")
    value: str = Field(..., description="Value in wei")
    gas: str = Field(..., description="Gas limit")
    gas_used: str = Field(..., description="Gas used")
    input: str = Field(..., description="Input data")
    output: str = Field(..., description="Output data")


class Transaction(BaseModel):
    """Model for transaction data."""

    hash: str = Field(..., description="Transaction hash")
    nonce: str = Field(..., description="Nonce")
    transaction_index: str = Field(..., description="Transaction index")
    from_address: str = Field(..., description="From address")
    from_address_label: Optional[str] = Field(None, description="From address label")
    from_address_entity: Optional[str] = Field(None, description="From address entity")
    from_address_entity_logo: Optional[str] = Field(
        None, description="From address entity logo"
    )
    to_address: str = Field(..., description="To address")
    to_address_label: Optional[str] = Field(None, description="To address label")
    to_address_entity: Optional[str] = Field(None, description="To address entity")
    to_address_entity_logo: Optional[str] = Field(
        None, description="To address entity logo"
    )
    value: str = Field(..., description="Value in wei")
    gas: str = Field(..., description="Gas limit")
    gas_price: str = Field(..., description="Gas price")
    input: str = Field(..., description="Input data")
    receipt_cumulative_gas_used: str = Field(..., description="Cumulative gas used")
    receipt_gas_used: str = Field(..., description="Gas used")
    receipt_contract_address: Optional[str] = Field(
        None, description="Contract address"
    )
    receipt_root: Optional[str] = Field(None, description="Receipt root")
    receipt_status: str = Field(..., description="Receipt status")
    block_timestamp: str = Field(..., description="Block timestamp")
    block_number: str = Field(..., description="Block number")
    block_hash: str = Field(..., description="Block hash")
    logs: Optional[Union[List[TransactionLog], TransactionLog]] = Field(
        None, description="Transaction logs"
    )
    internal_transactions: Optional[
        Union[List[InternalTransaction], InternalTransaction]
    ] = Field(None, description="Internal transactions")
    decoded_call: Optional[DecodedCall] = Field(None, description="Decoded call data")


class TransactionOutput(BaseModel):
    """Output for FetchTransactionByHash tool."""

    transaction: Optional[Transaction] = Field(None, description="Transaction data")
    chain_id: int = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    error: Optional[str] = Field(None, description="Error message if any")
    human_readable_summary: Optional[str] = Field(
        None, description="Human-readable summary of the transaction"
    )


class FetchTransactionByHash(WalletBaseTool):
    """Tool for fetching transaction data by hash.

    This tool retrieves detailed information about a transaction by its hash,
    including sender/receiver, value, gas, timestamps, and optionally decoded data.
    """

    name: str = "moralis_fetch_transaction_by_hash"
    description: str = (
        "This tool fetches transaction data by hash.\n"
        "Provide a transaction hash and optionally a chain ID to get detailed transaction data.\n"
        "Returns:\n"
        "- Transaction details (hash, timestamp, value, etc.)\n"
        "- Sender and receiver information, including labels if available\n"
        "- Gas costs and receipt status\n"
        "- Decoded call data and events when available\n"
        "- Internal transactions if requested\n"
        "Use this tool when a user wants to explore the details of a specific transaction."
    )
    args_schema: Type[BaseModel] = FetchTransactionByHashInput

    async def _arun(
        self,
        transaction_hash: str,
        chain_id: int = 1,
        include_internal: bool = False,
        decode: bool = True,
        **kwargs,
    ) -> TransactionOutput:
        """Fetch transaction data by hash.

        Args:
            transaction_hash: Transaction hash to fetch
            chain_id: Chain ID (default: Ethereum mainnet)
            include_internal: Whether to include internal transactions
            decode: Whether to decode the transaction data

        Returns:
            TransactionOutput containing transaction data
        """
        try:
            # Fetch transaction data
            if decode:
                tx_data = await get_decoded_transaction_by_hash(
                    self.api_key, transaction_hash, chain_id, include_internal
                )
            else:
                tx_data = await get_transaction_by_hash(
                    self.api_key, transaction_hash, chain_id, include_internal
                )

            if "error" in tx_data:
                return TransactionOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=tx_data["error"],
                )

            # Handle different response structures
            if isinstance(tx_data, dict) and "result" in tx_data:
                tx_data = tx_data["result"]

            # Process the data
            try:
                transaction = Transaction(**tx_data)
            except Exception as e:
                logger.error(f"Error parsing transaction data: {str(e)}")
                # If parsing fails, return the raw data
                return TransactionOutput(
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=f"Error parsing transaction data: {str(e)}",
                )

            # Generate human-readable summary
            summary = self._generate_transaction_summary(transaction)

            return TransactionOutput(
                transaction=transaction,
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                human_readable_summary=summary,
            )

        except Exception as e:
            logger.error(f"Error fetching transaction by hash: {str(e)}")
            return TransactionOutput(
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                error=str(e),
            )

    def _generate_transaction_summary(self, transaction: Transaction) -> str:
        """Generate a human-readable summary of the transaction.

        Args:
            transaction: Transaction data

        Returns:
            Human-readable summary
        """
        # Format addresses with labels if available
        from_address = transaction.from_address
        if transaction.from_address_label:
            from_address += f" ({transaction.from_address_label})"
        elif transaction.from_address_entity:
            from_address += f" ({transaction.from_address_entity})"

        to_address = transaction.to_address
        if transaction.to_address_label:
            to_address += f" ({transaction.to_address_label})"
        elif transaction.to_address_entity:
            to_address += f" ({transaction.to_address_entity})"

        # Format value in Ether if it's in wei
        try:
            value_eth = float(transaction.value) / 10**18
            value_formatted = f"{value_eth:.6f} ETH"
        except ValueError:
            value_formatted = transaction.value

        # Get timestamp
        timestamp = transaction.block_timestamp

        # Get transaction status
        status = "Success" if transaction.receipt_status == "1" else "Failed"

        # Get transaction type based on decoded call if available
        tx_type = "Transfer"
        if transaction.decoded_call:
            tx_type = transaction.decoded_call.label

        # Build summary
        summary = f"Transaction {transaction.hash}\n"
        summary += f"Status: {status}\n"
        summary += f"Type: {tx_type}\n"
        summary += f"From: {from_address}\n"
        summary += f"To: {to_address}\n"
        summary += f"Value: {value_formatted}\n"
        summary += f"Block: {transaction.block_number}\n"
        summary += f"Timestamp: {timestamp}\n"

        # Add decoded call details if available
        if transaction.decoded_call:
            summary += f"\nFunction: {transaction.decoded_call.signature}\n"
            if transaction.decoded_call.params:
                summary += "Parameters:\n"
                for param in transaction.decoded_call.params:
                    summary += f"- {param.name}: {param.value} ({param.type})\n"

        return summary
