"""Fetching transaction history for a wallet with enhanced capabilities."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from skills.moralis.api import (
    fetch_transaction_history,
    get_decoded_transaction_by_hash,
)
from skills.moralis.base import WalletBaseTool

logger = logging.getLogger(__name__)


class FetchTransactionHistoryInput(BaseModel):
    """Input for FetchTransactionHistory tool."""

    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(
        None, description="Chain ID (if not specified, fetches from Ethereum mainnet)"
    )
    limit: Optional[int] = Field(
        100, description="Maximum number of transactions to return"
    )
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    from_date: Optional[str] = Field(
        None, description="Start date (YYYY-MM-DD) to fetch transactions from"
    )
    to_date: Optional[str] = Field(
        None, description="End date (YYYY-MM-DD) to fetch transactions until"
    )
    from_block: Optional[int] = Field(
        None, description="Start block number to fetch transactions from"
    )
    to_block: Optional[int] = Field(
        None, description="End block number to fetch transactions until"
    )
    include_internal: bool = Field(
        False, description="Whether to include internal transactions"
    )
    enhance_transaction: bool = Field(
        False,
        description="Whether to enhance transaction data with decoded information",
    )


class TokenTransfer(BaseModel):
    """Model for a token transfer within a transaction."""

    token_address: str = Field(..., description="Token contract address")
    token_name: Optional[str] = Field(None, description="Token name")
    token_symbol: Optional[str] = Field(None, description="Token symbol")
    token_decimals: Optional[int] = Field(None, description="Token decimals")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    value: str = Field(..., description="Raw transfer value")
    value_decimal: Optional[float] = Field(None, description="Formatted decimal value")
    value_usd: Optional[float] = Field(None, description="USD value of transfer")


class DecodedParam(BaseModel):
    """Model for decoded parameter."""

    name: str = Field(..., description="Parameter name")
    value: str = Field(..., description="Parameter value")
    type: str = Field(..., description="Parameter type")


class DecodedFunction(BaseModel):
    """Model for decoded function call."""

    signature: str = Field(..., description="Function signature")
    label: str = Field(..., description="Function label")
    type: str = Field(..., description="Function type")
    params: Optional[List[DecodedParam]] = Field(
        None, description="Function parameters"
    )


class Transaction(BaseModel):
    """Model for a transaction."""

    hash: str = Field(..., description="Transaction hash")
    block_number: int = Field(..., description="Block number")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    from_address: str = Field(..., description="Sender address")
    from_address_label: Optional[str] = Field(None, description="Sender address label")
    to_address: Optional[str] = Field(
        None, description="Recipient address (None for contract creations)"
    )
    to_address_label: Optional[str] = Field(None, description="Recipient address label")
    value: str = Field(..., description="Raw native token value")
    value_decimal: float = Field(..., description="Formatted decimal value")
    value_usd: Optional[float] = Field(None, description="USD value of transaction")
    gas_price: str = Field(..., description="Gas price")
    gas_used: Optional[str] = Field(None, description="Gas used")
    fee: Optional[float] = Field(None, description="Transaction fee in native token")
    fee_usd: Optional[float] = Field(None, description="Transaction fee in USD")
    method: Optional[str] = Field(None, description="Contract method name if available")
    token_transfers: List[TokenTransfer] = Field(
        default_factory=list, description="Token transfers in this transaction"
    )
    transaction_type: Optional[str] = Field(
        None, description="Transaction type (transfer, swap, approval, etc.)"
    )
    chain: str = Field("eth", description="Blockchain network")
    decoded_function: Optional[DecodedFunction] = Field(
        None, description="Decoded function call if available"
    )
    summary: Optional[str] = Field(
        None, description="Human-readable transaction summary"
    )


class TransactionHistoryOutput(BaseModel):
    """Output for FetchTransactionHistory tool."""

    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(None, description="Chain ID if specified")
    chain_name: Optional[str] = Field(None, description="Chain name if specified")
    transactions: List[Transaction] = Field(
        default_factory=list, description="List of transactions"
    )
    total_count: Optional[int] = Field(None, description="Total count of transactions")
    page_size: int = Field(0, description="Page size")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    error: Optional[str] = Field(None, description="Error message if any")
    statistics: Optional[Dict[str, Any]] = Field(
        None, description="Transaction statistics"
    )


class FetchTransactionHistory(WalletBaseTool):
    """Tool for fetching transaction history for a wallet with enhanced capabilities.

    This tool retrieves detailed transaction data for a wallet address,
    including token transfers, gas costs, USD values, and optionally enhances
    transactions with decoded function calls and human-readable summaries.
    """

    name: str = "moralis_fetch_transaction_history"
    description: str = (
        "This tool fetches transaction history for a wallet address with enhanced analysis capabilities.\n"
        "Provide a wallet address and optionally a chain ID to get detailed transaction data.\n"
        "Returns:\n"
        "- Transaction details (hash, timestamp, value, etc.)\n"
        "- Transaction type (transfer, swap, approval, etc.)\n"
        "- Token movements (from, to, amount)\n"
        "- Gas costs and USD values\n"
        "- Decoded function calls and human-readable summaries (when enhanced mode is enabled)\n"
        "- Transaction statistics\n"
        "Use this tool whenever a user wants to analyze their transaction history."
    )
    args_schema: Type[BaseModel] = FetchTransactionHistoryInput

    async def _arun(
        self,
        address: str,
        chain_id: Optional[int] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        include_internal: bool = False,
        enhance_transaction: bool = False,
        **kwargs,
    ) -> TransactionHistoryOutput:
        """Fetch transaction history for a wallet with enhanced capabilities.

        Args:
            address: Wallet address to fetch transactions for
            chain_id: Chain ID to fetch transactions for (if None, fetches from Ethereum mainnet)
            limit: Maximum number of transactions to return
            cursor: Cursor for pagination
            from_date: Start date to fetch transactions from
            to_date: End date to fetch transactions until
            from_block: Start block number to fetch transactions from
            to_block: End block number to fetch transactions until
            include_internal: Whether to include internal transactions
            enhance_transaction: Whether to enhance transaction data with decoded information

        Returns:
            TransactionHistoryOutput containing transaction history data
        """
        try:
            # Default to Ethereum mainnet if chain_id is not specified
            if chain_id is None:
                chain_id = 1  # Ethereum mainnet

            # Prepare parameters
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date
            if from_block:
                params["from_block"] = from_block
            if to_block:
                params["to_block"] = to_block
            if include_internal:
                params["include"] = "internal_transactions"

            # Fetch transaction history
            tx_data = await fetch_transaction_history(
                self.api_key, address, chain_id, cursor, limit
            )

            if "error" in tx_data:
                return TransactionHistoryOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=tx_data["error"],
                )

            # Process the data
            chain_name = self._get_chain_name(chain_id)
            result = {
                "address": address,
                "chain_id": chain_id,
                "chain_name": chain_name,
                "transactions": [],
                "total_count": tx_data.get("total"),
                "page_size": tx_data.get("page_size", limit),
                "cursor": tx_data.get("cursor"),
            }

            # Process transactions
            for tx in tx_data.get("result", []):
                transaction = await self._process_transaction(
                    tx, chain_name, enhance_transaction
                )
                result["transactions"].append(transaction)

            # Generate statistics
            result["statistics"] = self._generate_statistics(result["transactions"])

            return TransactionHistoryOutput(**result)

        except Exception as e:
            logger.error(f"Error fetching transaction history: {str(e)}")
            return TransactionHistoryOutput(
                address=address,
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id) if chain_id else None,
                error=str(e),
            )

    async def _process_transaction(
        self, tx: Dict[str, Any], chain_name: str, enhance: bool
    ) -> Transaction:
        """Process a transaction from the API response.

        Args:
            tx: Transaction data from API
            chain_name: Chain name
            enhance: Whether to enhance transaction data with decoded information

        Returns:
            Processed Transaction object
        """
        # Process token transfers
        token_transfers = []
        if "token_transfers" in tx:
            for transfer in tx["token_transfers"]:
                token_transfer = TokenTransfer(
                    token_address=transfer.get("token_address", ""),
                    token_name=transfer.get("token_name"),
                    token_symbol=transfer.get("token_symbol"),
                    token_decimals=transfer.get("token_decimals"),
                    from_address=transfer.get(
                        "from_address", tx.get("from_address", "")
                    ),
                    to_address=transfer.get("to_address", ""),
                    value=transfer.get("value", "0"),
                    value_decimal=transfer.get("value_decimal"),
                    value_usd=transfer.get("value_usd"),
                )
                token_transfers.append(token_transfer)

        # Determine transaction type based on method name or token transfers
        tx_type = None
        if "method" in tx:
            method = tx["method"].lower() if tx["method"] else ""
            if "transfer" in method:
                tx_type = "transfer"
            elif "swap" in method:
                tx_type = "swap"
            elif "approve" in method:
                tx_type = "approval"
            elif "withdraw" in method:
                tx_type = "withdrawal"
            elif "deposit" in method:
                tx_type = "deposit"
            elif "mint" in method:
                tx_type = "mint"
            elif "burn" in method:
                tx_type = "burn"

        # If no method-based type, derive from token transfers
        if not tx_type and token_transfers:
            tx_type = "token_transfer"

        # Create transaction
        transaction_data = {
            "hash": tx.get("hash", ""),
            "block_number": int(tx.get("block_number", 0)),
            "timestamp": datetime.fromtimestamp(int(tx.get("block_timestamp", 0)))
            if tx.get("block_timestamp")
            else datetime.now(),
            "from_address": tx.get("from_address", ""),
            "from_address_label": tx.get("from_address_label"),
            "to_address": tx.get("to_address"),
            "to_address_label": tx.get("to_address_label"),
            "value": tx.get("value", "0"),
            "value_decimal": float(tx.get("value_decimal", 0)),
            "value_usd": tx.get("value_usd"),
            "gas_price": tx.get("gas_price", "0"),
            "gas_used": tx.get("gas_used"),
            "fee": tx.get("fee"),
            "fee_usd": tx.get("fee_usd"),
            "method": tx.get("method"),
            "token_transfers": token_transfers,
            "transaction_type": tx_type,
            "chain": chain_name,
        }

        # Enhance transaction with decoded data if requested
        if enhance and tx.get("hash"):
            try:
                decoded_tx = await get_decoded_transaction_by_hash(
                    self.api_key, tx["hash"], self._get_chain_id(chain_name)
                )
                if "error" not in decoded_tx and "decoded_call" in decoded_tx:
                    decoded_call = decoded_tx["decoded_call"]
                    transaction_data["decoded_function"] = DecodedFunction(
                        signature=decoded_call.get("signature", ""),
                        label=decoded_call.get("label", ""),
                        type=decoded_call.get("type", ""),
                        params=decoded_call.get("params", []),
                    )
                    transaction_data["summary"] = self._generate_transaction_summary(
                        transaction_data, decoded_call
                    )
            except Exception as e:
                logger.warning(
                    f"Error enhancing transaction {tx.get('hash')}: {str(e)}"
                )

        return Transaction(**transaction_data)

    def _generate_transaction_summary(
        self, tx_data: Dict[str, Any], decoded_call: Dict[str, Any]
    ) -> str:
        """Generate a human-readable summary of the transaction.

        Args:
            tx_data: Transaction data
            decoded_call: Decoded function call data

        Returns:
            Human-readable summary
        """
        # Format addresses with labels if available
        from_address = tx_data["from_address"]
        if tx_data.get("from_address_label"):
            from_address += f" ({tx_data['from_address_label']})"

        to_address = tx_data.get("to_address", "Contract Creation")
        if tx_data.get("to_address_label"):
            to_address += f" ({tx_data['to_address_label']})"

        # Format value in Ether if it's in wei
        try:
            value_eth = float(tx_data["value"]) / 10**18
            value_formatted = f"{value_eth:.6f} ETH"
        except (ValueError, TypeError):
            value_formatted = tx_data.get("value", "0")

        # Get timestamp
        timestamp = tx_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        # Get transaction type
        tx_type = tx_data.get("transaction_type", "Unknown")
        if decoded_call and decoded_call.get("label"):
            tx_type = decoded_call["label"]

        # Build summary
        summary = f"Transaction {tx_data['hash']}\n"
        summary += f"Type: {tx_type}\n"
        summary += f"From: {from_address}\n"
        summary += f"To: {to_address}\n"
        summary += f"Value: {value_formatted}\n"
        summary += f"Timestamp: {timestamp}\n"

        # Add decoded call details
        if decoded_call and decoded_call.get("signature"):
            summary += f"\nFunction: {decoded_call['signature']}\n"
            if decoded_call.get("params"):
                summary += "Parameters:\n"
                for param in decoded_call["params"]:
                    summary += f"- {param.get('name')}: {param.get('value')} ({param.get('type')})\n"

        # Add token transfers if available
        if tx_data.get("token_transfers"):
            summary += "\nToken Transfers:\n"
            for transfer in tx_data["token_transfers"]:
                token_symbol = transfer.get("token_symbol", "Unknown")
                token_value = transfer.get("value_decimal", "Unknown")
                summary += f"- {token_value} {token_symbol} from {transfer.get('from_address')} to {transfer.get('to_address')}\n"

        return summary

    def _generate_statistics(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Generate statistics from transaction history.

        Args:
            transactions: List of transactions

        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_transactions": len(transactions),
            "transaction_types": {},
            "token_movements": {},
            "total_value_sent": 0,
            "total_value_received": 0,
            "total_fees_paid": 0,
            "activity_by_month": {},
        }

        # Process transactions for statistics
        for tx in transactions:
            # Count transaction types
            tx_type = tx.transaction_type or "unknown"
            stats["transaction_types"][tx_type] = (
                stats["transaction_types"].get(tx_type, 0) + 1
            )

            # Count token movements
            for transfer in tx.token_transfers:
                token = transfer.token_symbol or "unknown"
                stats["token_movements"][token] = (
                    stats["token_movements"].get(token, 0) + 1
                )

            # Track value sent/received
            if tx.value_decimal:
                if tx.from_address == tx.to_address:
                    pass  # Self-transfer
                else:
                    stats["total_value_sent"] += tx.value_decimal

            # Track fees paid
            if tx.fee:
                stats["total_fees_paid"] += tx.fee

            # Activity by month
            month_key = tx.timestamp.strftime("%Y-%m")
            stats["activity_by_month"][month_key] = (
                stats["activity_by_month"].get(month_key, 0) + 1
            )

        return stats

    def _get_chain_id(self, chain_name: str) -> int:
        """Convert chain name to chain ID.

        Args:
            chain_name: Chain name

        Returns:
            Chain ID
        """
        chain_mapping = {
            "eth": 1,
            "bsc": 56,
            "polygon": 137,
            "avalanche": 43114,
            "fantom": 250,
            "arbitrum": 42161,
            "optimism": 10,
            "base": 8453,
        }
        return chain_mapping.get(chain_name, 1)
