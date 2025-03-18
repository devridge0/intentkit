"""Tool for fetching NFT portfolio for a wallet."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .base import WalletPortfolioBaseTool
from .api import fetch_nft_data

FETCH_NFT_PORTFOLIO_PROMPT = """
This tool fetches NFT holdings for a wallet address.
Provide a wallet address and optionally a chain ID to get detailed information about NFTs.
Returns:
- NFT collection data
- NFT metadata and attributes
- Media URLs if available
- Floor prices if available
"""

class FetchNftPortfolioInput(BaseModel):
    """Input schema for fetching NFT portfolio."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(None, description="Chain ID (if not specified, fetches from all supported chains)")
    limit: Optional[int] = Field(100, description="Maximum number of NFTs to return")
    normalize_metadata: bool = Field(True, description="Whether to normalize metadata across different standards")


class NftMetadata(BaseModel):
    """Model representing NFT metadata."""
    
    name: Optional[str] = Field(None, description="NFT name")
    description: Optional[str] = Field(None, description="NFT description")
    image: Optional[str] = Field(None, description="NFT image URL")
    animation_url: Optional[str] = Field(None, description="NFT animation URL")
    attributes: Optional[List[Dict]] = Field(None, description="NFT attributes/traits")
    external_url: Optional[str] = Field(None, description="External URL")


class NftItem(BaseModel):
    """Model representing an NFT item."""
    
    token_id: str = Field(..., description="NFT token ID")
    token_address: str = Field(..., description="NFT contract address")
    contract_type: Optional[str] = Field(None, description="NFT contract type (ERC721, ERC1155, etc.)")
    name: Optional[str] = Field(None, description="NFT name")
    symbol: Optional[str] = Field(None, description="NFT symbol")
    owner_of: str = Field(..., description="Owner address")
    metadata: Optional[NftMetadata] = Field(None, description="NFT metadata")
    floor_price: Optional[float] = Field(None, description="Floor price in ETH if available")


class NftPortfolioOutput(BaseModel):
    """Response schema for NFT portfolio."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: Optional[int] = Field(None, description="Chain ID if specified")
    chain_name: Optional[str] = Field(None, description="Chain name if specified")
    nfts: List[NftItem] = Field(default_factory=list, description="List of NFT items")
    total_count: int = Field(0, description="Total count of NFTs")
    page_size: int = Field(0, description="Page size")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    error: Optional[str] = Field(None, description="Error message if any")


class FetchNftPortfolio(WalletPortfolioBaseTool):
    """Tool for fetching NFT portfolio for a wallet.
    
    This tool retrieves detailed information about NFTs owned by a wallet address,
    including metadata, media URLs, and floor prices when available.
    """
    
    name: str = "fetch_nft_portfolio"
    description: str = FETCH_NFT_PORTFOLIO_PROMPT
    args_schema = FetchNftPortfolioInput
    
    def _run(
        self, 
        address: str, 
        chain_id: Optional[int] = None,
        limit: int = 100,
        normalize_metadata: bool = True
    ) -> NftPortfolioOutput:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(
        self, 
        address: str, 
        chain_id: Optional[int] = None,
        limit: int = 100,
        normalize_metadata: bool = True
    ) -> NftPortfolioOutput:
        """Fetch NFT portfolio for a wallet.
        
        Args:
            address: Wallet address to fetch NFTs for
            chain_id: Chain ID to fetch NFTs for (if None, fetches from all supported chains)
            limit: Maximum number of NFTs to return
            normalize_metadata: Whether to normalize metadata across different standards
            
        Returns:
            NftPortfolioOutput containing NFT portfolio data
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return NftPortfolioOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id) if chain_id else None,
                    error=error_msg
                )
            
            # Fetch NFT data
            params = {
                "limit": limit,
                "normalizeMetadata": normalize_metadata
            }
            
            nft_data = await fetch_nft_data(self.api_key, address, chain_id, params)
            
            if "error" in nft_data:
                return NftPortfolioOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id) if chain_id else None,
                    error=nft_data["error"]
                )
            
            # Process the data
            result = {
                "address": address,
                "chain_id": chain_id,
                "chain_name": self._get_chain_name(chain_id) if chain_id else None,
                "nfts": [],
                "total_count": nft_data.get("total", 0),
                "page_size": nft_data.get("page_size", limit),
                "cursor": nft_data.get("cursor")
            }
            
            for nft in nft_data.get("result", []):
                # Extract metadata
                metadata = None
                if "metadata" in nft and nft["metadata"]:
                    try:
                        if isinstance(nft["metadata"], str):
                            import json
                            metadata_dict = json.loads(nft["metadata"])
                        else:
                            metadata_dict = nft["metadata"]
                            
                        metadata = NftMetadata(
                            name=metadata_dict.get("name"),
                            description=metadata_dict.get("description"),
                            image=metadata_dict.get("image"),
                            animation_url=metadata_dict.get("animation_url"),
                            attributes=metadata_dict.get("attributes"),
                            external_url=metadata_dict.get("external_url")
                        )
                    except:
                        # If metadata parsing fails, continue without it
                        pass
                
                # Create NFT item
                nft_item = NftItem(
                    token_id=nft.get("token_id", ""),
                    token_address=nft.get("token_address", ""),
                    contract_type=nft.get("contract_type"),
                    name=nft.get("name"),
                    symbol=nft.get("symbol"),
                    owner_of=nft.get("owner_of", address),
                    metadata=metadata,
                    floor_price=nft.get("floor_price")
                )
                
                result["nfts"].append(nft_item)
            
            return NftPortfolioOutput(**result)
            
        except Exception as e:
            return NftPortfolioOutput(
                address=address,
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id) if chain_id else None,
                error=str(e)
            )