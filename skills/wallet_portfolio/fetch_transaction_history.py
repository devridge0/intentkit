"""Tool for fetching transaction history for a wallet."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .base import WalletPortfolioBaseTool
from .api import fetch_transaction_history

FETCH_TRANSACTION_HISTORY_PROMPT = """
This tool fetches transaction history for a wallet address.
Provide a wallet address and optionally a chain ID to get detailed transaction data.
Returns:
- Transaction details (hash, timestamp, value, etc.)
- Transaction type (transfer, swap, approval, etc.)
- Token movements (from, to, amount)
- Gas costs
"""

class FetchTransactionHistoryInput(BaseModel):
    """Input schema for fetching transaction history."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(None, description="Chain ID (if not specified, fetches from all supported chains)")
    limit: Optional[int] = Field(100, description="Maximum number of transactions to return")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")


class TokenTransfer(BaseModel):
    """Model representing a token transfer within a transaction."""
    
    token_address: str = Field(..., description="Token contract address")
    token_name: Optional[str] = Field(None, description="Token name")
    token_symbol: Optional[str] = Field(None, description="Token symbol")
    token_decimals: Optional[int] = Field(None, description="Token decimals")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    value: str = Field(..., description="Raw transfer value")
    value_decimal: Optional[float] = Field(None, description="Formatted decimal value")
    value_usd: Optional[float] = Field(None, description="USD value of transfer")


class Transaction(BaseModel):
    """Model representing a transaction."""
    
    hash: str = Field(..., description="Transaction hash")
    block_number: int = Field(..., description="Block number")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    from_address: str = Field(..., description="Sender address")
    to_address: Optional[str] = Field(None, description="Recipient address (None for contract creations)")
    value: str = Field(..., description="Raw native token value")
    value_decimal: float = Field(..., description="Formatted decimal value")
    value_usd: Optional[float] = Field(None, description="USD value of transaction")
    gas_price: str = Field(..., description="Gas price")
    gas_used: Optional[str] = Field(None, description="Gas used")
    fee: Optional[float] = Field(None, description="Transaction fee in native token")
    fee_usd: Optional[float] = Field(None, description="Transaction fee in USD")
    method: Optional[str] = Field(None, description="Contract method name if available")
    token_transfers: List[TokenTransfer] = Field(default_factory=list, description="Token transfers in this transaction")
    transaction_type: Optional[str] = Field(None, description="Transaction type (transfer, swap, approval, etc.)")


class TransactionHistoryOutput(BaseModel):
    """Response schema for transaction history."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(None, description="Chain ID if specified")
    chain_name: Optional[str] = Field(None, description="Chain name if specified")
    transactions: List[Transaction] = Field(default_factory=list, description="List of transactions")
    total_count: Optional[int] = Field(None, description="Total count of transactions")
    page_size: int = Field(0, description="Page size")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    error: Optional[str] = Field(None, description="Error message if any")


class FetchTransactionHistory(WalletPortfolioBaseTool):
    """Tool for fetching transaction history for a wallet.
    
    This tool retrieves detailed transaction data for a wallet address,
    including token transfers, gas costs, and USD values when available.
    """
    
    name: str = "fetch_transaction_history"
    description: str = FETCH_TRANSACTION_HISTORY_PROMPT
    args_schema = FetchTransactionHistoryInput
    
    def _run(
        self, 
        address: str, 
        chain_id: Optional[int] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> TransactionHistoryOutput:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(
        self, 
        address: str, 
        chain_id: Optional[int] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> TransactionHistoryOutput:
        """Fetch transaction history for a wallet.
        
        Args:
            address: Wallet address to fetch transactions for
            chain_id: Chain ID to fetch transactions for (if None, fetches from all supported chains)
            limit: Maximum number of transactions to return
            cursor: Cursor for pagination
            
        Returns:
            TransactionHistoryOutput containing transaction history data
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return TransactionHistoryOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id) if chain_id else None,
                    error=error_msg
                )
            
            # Fetch transaction history
            tx_data = await fetch_transaction_history(
                self.api_key, 
                address, 
                chain_id, 
                cursor, 
                limit
            )
            
            if "error" in tx_data:
                return TransactionHistoryOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id) if chain_id else None,
                    error=tx_data["error"]
                )
            
            # Process the data
            result = {
                "address": address,
                "chain_id": chain_id,
                "chain_name": self._get_chain_name(chain_id) if chain_id else None,
                "transactions": [],
                "total_count": tx_data.get("total"),
                "page_size": tx_data.get("page_size", limit),
                "cursor": tx_data.get("cursor")
            }
            
            for tx in tx_data.get("result", []):
                # Process token transfers
                token_transfers = []
                if "token_transfers" in tx:
                    for transfer in tx["token_transfers"]:
                        token_transfer = TokenTransfer(
                            token_address=transfer.get("token_address", ""),
                            token_name=transfer.get("token_name"),
                            token_symbol=transfer.get("token_symbol"),
                            token_decimals=transfer.get("token_decimals"),
                            from_address=transfer.get("from_address", tx.get("from_address", "")),
                            to_address=transfer.get("to_address", ""),
                            value=transfer.get("value", "0"),
                            value_decimal=transfer.get("value_decimal"),
                            value_usd=transfer.get("value_usd")
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
                transaction = Transaction(
                    hash=tx.get("hash", ""),
                    block_number=int(tx.get("block_number", 0)),
                    timestamp=datetime.fromtimestamp(int(tx.get("block_timestamp", 0))),
                    from_address=tx.get("from_address", ""),
                    to_address=tx.get("to_address"),
                    value=tx.get("value", "0"),
                    value_decimal=float(tx.get("value_decimal", 0)),
                    value_usd=tx.get("value_usd"),
                    gas_price=tx.get("gas_price", "0"),
                    gas_used=tx.get("gas_used"),
                    fee=tx.get("fee"),
                    fee_usd=tx.get("fee_usd"),
                    method=tx.get("method"),
                    token_transfers=token_transfers,
                    transaction_type=tx_type
                )
                
                result["transactions"].append(transaction)
            
            return TransactionHistoryOutput(**result)
            
        except Exception as e:
            return TransactionHistoryOutput(
                address=address,
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id) if chain_id else None,
                error=str(e)
            )