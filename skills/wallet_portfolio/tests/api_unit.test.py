import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta

from skills.wallet_portfolio.api import (
    fetch_moralis_data,
    fetch_wallet_balances,
    fetch_nft_data,
    fetch_transaction_history,
    fetch_token_approvals,
    fetch_defi_positions,
    fetch_net_worth,
    resolve_ens_address,
    CHAIN_MAPPING
)
from skills.wallet_portfolio.base import WalletPortfolioBaseTool
from skills.wallet_portfolio.fetch_wallet_portfolio import FetchWalletPortfolio
from skills.wallet_portfolio.fetch_chain_portfolio import FetchChainPortfolio
from skills.wallet_portfolio.fetch_nft_portfolio import FetchNftPortfolio
from skills.wallet_portfolio.fetch_transaction_history import FetchTransactionHistory
from skills.wallet_portfolio.fetch_asset_portfolio import FetchAssetPortfolio
from skills.wallet_portfolio.solana import (
    FetchSolanaPortfolio,
    fetch_solana_api,
    get_solana_portfolio,
    get_solana_balance,
    get_solana_spl_tokens,
    get_solana_nfts,
    get_token_price
)
from skills.wallet_portfolio import get_skills, get_wallet_portfolio_skill
from utils.chain_helpers import setup_chain_provider


class DummyResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
        self.text = json.dumps(json_data) if json_data else ""

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


class TestWalletPortfolioBaseClass(unittest.IsolatedAsyncioTestCase):
    """Test the base wallet portfolio tool class"""
    
    async def test_base_class_init(self):
        """Test base class initialization"""
        mock_skill_store = MagicMock()
        mock_agent_store = MagicMock()
        mock_chain_provider = MagicMock()
        
        # Create a concrete subclass for testing
        class TestTool(WalletPortfolioBaseTool):
            async def _arun(self, *args, **kwargs):
                return "test"
        
        tool = TestTool(
            api_key="test_key",
            skill_store=mock_skill_store,
            agent_id="test_agent",
            agent_store=mock_agent_store,
            chain_provider=mock_chain_provider
        )
        
        self.assertEqual(tool.api_key, "test_key")
        self.assertEqual(tool.agent_id, "test_agent")
        self.assertEqual(tool.skill_store, mock_skill_store)
        self.assertEqual(tool.agent_store, mock_agent_store)
        self.assertEqual(tool.chain_provider, mock_chain_provider)
    
    async def test_check_rate_limit(self):
        """Test rate limiting functionality"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        class TestTool(WalletPortfolioBaseTool):
            async def _arun(self, *args, **kwargs):
                return "test"
        
        tool = TestTool(
            api_key="test_key",
            skill_store=mock_skill_store,
            agent_id="test_agent",
            agent_store=MagicMock(),
            chain_provider=MagicMock()
        )
        
        # First call should not be rate limited
        is_limited, msg = await tool.check_rate_limit()
        self.assertFalse(is_limited)
        self.assertIsNone(msg)
        
        # Set up rate limit data for testing
        now = datetime.now()
        future = (now + timedelta(minutes=5)).isoformat()
        
        # Test under limit
        mock_skill_store.get_agent_skill_data = AsyncMock(
            return_value={"count": 5, "reset_time": future}
        )
        is_limited, msg = await tool.check_rate_limit(max_requests=10)
        self.assertFalse(is_limited)
        
        # Test at limit
        mock_skill_store.get_agent_skill_data = AsyncMock(
            return_value={"count": 10, "reset_time": future}
        )
        is_limited, msg = await tool.check_rate_limit(max_requests=10)
        self.assertTrue(is_limited)
        self.assertEqual(msg, "Rate limit exceeded")
        
    async def test_get_chain_name(self):
        """Test chain name conversion"""
        class TestTool(WalletPortfolioBaseTool):
            async def _arun(self, *args, **kwargs):
                return "test"
        
        tool = TestTool(
            api_key="test_key",
            skill_store=MagicMock(),
            agent_id="test_agent",
            agent_store=MagicMock(),
            chain_provider=MagicMock()
        )
        
        # Test with known chain ID
        self.assertEqual(tool._get_chain_name(1), "eth")
        self.assertEqual(tool._get_chain_name(56), "bsc")
        
        # Test with unknown chain ID
        self.assertEqual(tool._get_chain_name(999999), "eth")


class TestAPIFunctions(unittest.IsolatedAsyncioTestCase):
    """Test the API interaction functions"""
    
    async def test_fetch_moralis_data(self):
        """Test the base Moralis API function"""
        with patch("app.config.config.config.moralis_api_key", "test_api_key"):
            with patch("httpx.AsyncClient") as MockClient:
                client_instance = AsyncMock()
                client_instance.get.return_value = DummyResponse(
                    200, {"success": True, "data": "test_data"}
                )
                MockClient.return_value.__aenter__.return_value = client_instance
                
                result = await fetch_moralis_data(
                    "test_api_key", "test_endpoint", "0xAddress", 1
                )
                
                self.assertEqual(result, {"success": True, "data": "test_data"})
                
                # Test error handling
                client_instance.get.return_value = DummyResponse(404, None)
                client_instance.get.return_value.raise_for_status = AsyncMock(
                    side_effect=Exception("HTTP error 404")
                )
                
                result = await fetch_moralis_data(
                    "test_api_key", "test_endpoint", "0xAddress", 1
                )
                self.assertIn("error", result)
    
    async def test_fetch_wallet_balances(self):
        """Test fetching wallet balances"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": [{"token_address": "0x123", "symbol": "TEST", "balance": "1000000", "usd_value": 100}]
            }
            
            result = await fetch_wallet_balances("test_api_key", "0xAddress", 1)
            
            self.assertEqual(result["result"][0]["symbol"], "TEST")
            mock_fetch.assert_called_once_with(
                "test_api_key", "wallets/{address}/tokens", "0xAddress", 1, None
            )
    
    async def test_fetch_nft_data(self):
        """Test fetching NFT data"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": [
                    {
                        "token_address": "0x123",
                        "token_id": "1",
                        "name": "Test NFT",
                        "symbol": "TNFT",
                        "metadata": json.dumps({"name": "Test NFT", "image": "image.png"}),
                        "contract_type": "ERC721"
                    }
                ]
            }
            
            result = await fetch_nft_data("test_api_key", "0xAddress", 1)
            
            self.assertEqual(result["result"][0]["name"], "Test NFT")
            mock_fetch.assert_called_once_with(
                "test_api_key", "{address}/nft", "0xAddress", 1, {"normalizeMetadata": True}
            )
    
    async def test_fetch_transaction_history(self):
        """Test fetching transaction history"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": [
                    {
                        "hash": "0xabc",
                        "from_address": "0xAddress",
                        "to_address": "0xDest",
                        "value": "1000000000000000000",
                        "block_timestamp": "1622480000",
                        "gas_price": "20000000000",
                        "gas_used": "21000"
                    }
                ]
            }
            
            result = await fetch_transaction_history("test_api_key", "0xAddress", 1)
            
            self.assertEqual(result["result"][0]["hash"], "0xabc")
            mock_fetch.assert_called_once_with(
                "test_api_key", "wallets/{address}/history", "0xAddress", 1, {"limit": 100}
            )
    
    async def test_fetch_token_approvals(self):
        """Test fetching token approvals"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": [
                    {
                        "token_address": "0x123",
                        "spender": "0xDest",
                        "allowance": "1000000000000000000",
                        "token_symbol": "TEST"
                    }
                ]
            }
            
            result = await fetch_token_approvals("test_api_key", "0xAddress", 1)
            
            self.assertEqual(result["result"][0]["token_symbol"], "TEST")
            mock_fetch.assert_called_once_with(
                "test_api_key", "wallets/{address}/approvals", "0xAddress", 1, None
            )
    
    async def test_fetch_defi_positions(self):
        """Test fetching DeFi positions"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": [
                    {
                        "protocol": "aave",
                        "chain": "eth",
                        "position_type": "supply",
                        "token_address": "0x123",
                        "balance": "1000000000000000000",
                        "balance_usd": 100
                    }
                ]
            }
            
            result = await fetch_defi_positions("test_api_key", "0xAddress")
            
            self.assertEqual(result["result"][0]["protocol"], "aave")
            mock_fetch.assert_called_once_with(
                "test_api_key", "wallets/{address}/defi/positions", "0xAddress", None, None
            )
    
    async def test_fetch_net_worth(self):
        """Test fetching net worth"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": {
                    "total_networth_usd": 1000,
                    "wallet_balances": 800,
                    "nft_value": 200
                }
            }
            
            result = await fetch_net_worth("test_api_key", "0xAddress")
            
            self.assertEqual(result["result"]["total_networth_usd"], 1000)
            mock_fetch.assert_called_once_with(
                "test_api_key", "wallets/{address}/net-worth", "0xAddress", None, None
            )
    
    async def test_resolve_ens_address(self):
        """Test resolving ENS address"""
        with patch("skills.wallet_portfolio.api.fetch_moralis_data") as mock_fetch:
            mock_fetch.return_value = {
                "result": "vitalik.eth"
            }
            
            result = await resolve_ens_address("test_api_key", "0xAddress")
            
            self.assertEqual(result["result"], "vitalik.eth")
            mock_fetch.assert_called_once_with(
                "test_api_key", "resolve/{address}/reverse", "0xAddress", None, None
            )
    
    async def test_no_api_key(self):
        """Test behavior when no API key is configured"""
        with patch("app.config.config.config.moralis_api_key", None):
            result = await fetch_wallet_balances(None, "0xAddress", 1)
            self.assertIn("error", result)
            self.assertEqual(result["error"], "Moralis API key not configured")


class TestSolanaAPI(unittest.IsolatedAsyncioTestCase):
    """Test Solana-specific API functions"""
    
    async def test_fetch_solana_api(self):
        """Test the base Solana API function"""
        with patch("httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get.return_value = DummyResponse(
                200, {"success": True, "data": "test_data"}
            )
            MockClient.return_value.__aenter__.return_value = client_instance
            
            result = await fetch_solana_api(
                "test_api_key", "/test_endpoint"
            )
            
            self.assertEqual(result, {"success": True, "data": "test_data"})
            
            # Test error handling
            client_instance.get.return_value = DummyResponse(404, None)
            client_instance.get.return_value.raise_for_status = AsyncMock(
                side_effect=Exception("HTTP error 404")
            )
            
            result = await fetch_solana_api(
                "test_api_key", "/test_endpoint"
            )
            self.assertIn("error", result)
    
    async def test_get_solana_portfolio(self):
        """Test getting Solana portfolio"""
        with patch("skills.wallet_portfolio.solana.fetch_solana_api") as mock_fetch:
            mock_fetch.return_value = {
                "nativeBalance": {"solana": 1.5, "lamports": 1500000000},
                "tokens": [
                    {
                        "symbol": "TEST",
                        "name": "Test Token",
                        "mint": "TokenMintAddress",
                        "associatedTokenAddress": "AssocTokenAddress",
                        "amount": 10,
                        "decimals": 9,
                        "amountRaw": "10000000000"
                    }
                ]
            }
            
            result = await get_solana_portfolio("test_api_key", "SolAddress", "mainnet")
            
            mock_fetch.assert_called_once_with(
                "test_api_key", f"/account/mainnet/SolAddress/portfolio"
            )
            self.assertEqual(result["nativeBalance"]["solana"], 1.5)
            self.assertEqual(len(result["tokens"]), 1)
            self.assertEqual(result["tokens"][0]["symbol"], "TEST")
    
    async def test_get_solana_balance(self):
        """Test getting Solana balance"""
        with patch("skills.wallet_portfolio.solana.fetch_solana_api") as mock_fetch:
            mock_fetch.return_value = {
                "solana": 1.5,
                "lamports": 1500000000
            }
            
            result = await get_solana_balance("test_api_key", "SolAddress", "mainnet")
            
            mock_fetch.assert_called_once_with(
                "test_api_key", f"/account/mainnet/SolAddress/balance"
            )
            self.assertEqual(result["solana"], 1.5)
            self.assertEqual(result["lamports"], 1500000000)
    
    async def test_get_solana_spl_tokens(self):
        """Test getting Solana SPL tokens"""
        with patch("skills.wallet_portfolio.solana.fetch_solana_api") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "symbol": "TEST",
                    "name": "Test Token",
                    "mint": "TokenMintAddress",
                    "associatedTokenAddress": "AssocTokenAddress",
                    "amount": 10,
                    "decimals": 9,
                    "amountRaw": "10000000000"
                }
            ]
            
            result = await get_solana_spl_tokens("test_api_key", "SolAddress", "mainnet")
            
            mock_fetch.assert_called_once_with(
                "test_api_key", f"/account/mainnet/SolAddress/tokens"
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["symbol"], "TEST")
    
    async def test_get_solana_nfts(self):
        """Test getting Solana NFTs"""
        with patch("skills.wallet_portfolio.solana.fetch_solana_api") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "mint": "NFTMintAddress",
                    "name": "Test NFT",
                    "symbol": "TNFT",
                    "associatedTokenAddress": "AssocTokenAddress",
                    "metadata": {"name": "Test NFT", "image": "image.png"}
                }
            ]
            
            result = await get_solana_nfts("test_api_key", "SolAddress", "mainnet")
            
            mock_fetch.assert_called_once_with(
                "test_api_key", f"/account/mainnet/SolAddress/nft"
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "Test NFT")
    
    async def test_get_token_price(self):
        """Test getting token price"""
        with patch("skills.wallet_portfolio.solana.fetch_solana_api") as mock_fetch:
            mock_fetch.return_value = {
                "usdPrice": 1.5,
                "timestamp": 1622480000
            }
            
            result = await get_token_price("test_api_key", "TokenMintAddress", "mainnet")
            
            mock_fetch.assert_called_once_with(
                "test_api_key", f"/token/mainnet/TokenMintAddress/price"
            )
            self.assertEqual(result["usdPrice"], 1.5)


class TestFetchWalletPortfolio(unittest.IsolatedAsyncioTestCase):
    """Test the FetchWalletPortfolio skill"""
    
    async def test_wallet_portfolio_success(self):
        """Test successful wallet portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        mock_chain_provider = MagicMock()
        mock_chain_provider.chain_configs = {
            "ethereum": MagicMock(chain_id=1),
            "bsc": MagicMock(chain_id=56)
        }
        
        with patch("skills.wallet_portfolio.fetch_wallet_portfolio.fetch_wallet_balances") as mock_balances, \
             patch("skills.wallet_portfolio.fetch_wallet_portfolio.fetch_net_worth") as mock_net_worth:
            
            # Mock successful responses
            mock_balances.return_value = {
                "result": [
                    {
                        "token_address": "0x123",
                        "symbol": "TEST",
                        "name": "Test Token",
                        "logo": "logo.png",
                        "decimals": 18,
                        "balance": "1000000000000000000",
                        "balance_formatted": "1.0",
                        "usd_value": 100
                    }
                ]
            }
            mock_net_worth.return_value = {
                "result": {"total_networth_usd": 1000}
            }
            
            tool = FetchWalletPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock(),
                chain_provider=mock_chain_provider
            )
            
            result = await tool._arun(address="0xAddress")
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.total_net_worth, 1000)
            self.assertEqual(len(result.tokens), 1)
            self.assertEqual(result.tokens[0].symbol, "TEST")
    
    async def test_wallet_portfolio_error(self):
        """Test error handling in wallet portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        mock_chain_provider = MagicMock()
        mock_chain_provider.chain_configs = {
            "ethereum": MagicMock(chain_id=1)
        }
        
        with patch("skills.wallet_portfolio.fetch_wallet_portfolio.fetch_wallet_balances") as mock_balances:
            mock_balances.return_value = {"error": "API error"}
            
            tool = FetchWalletPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock(),
                chain_provider=mock_chain_provider
            )
            
            result = await tool._arun(address="0xAddress")
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.total_net_worth, 0)
            self.assertEqual(len(result.tokens), 0)
            self.assertEqual(result.error, "API error")
    
    async def test_wallet_portfolio_rate_limit(self):
        """Test rate limiting in wallet portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(
            return_value={
                "count": 10, 
                "reset_time": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
        )
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        tool = FetchWalletPortfolio(
            api_key="test_key",
            skill_store=mock_skill_store,
            agent_id="test_agent",
            agent_store=MagicMock(),
            chain_provider=MagicMock()
        )
        
        result = await tool._arun(address="0xAddress")
        
        self.assertEqual(result.address, "0xAddress")
        self.assertEqual(result.error, "Rate limit exceeded")


class TestFetchChainPortfolio(unittest.IsolatedAsyncioTestCase):
    """Test the FetchChainPortfolio skill"""
    
    async def test_chain_portfolio_success(self):
        """Test successful chain portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_chain_portfolio.fetch_wallet_balances") as mock_balances, \
             patch("skills.wallet_portfolio.fetch_chain_portfolio.fetch_token_approvals") as mock_approvals:
            
            # Mock successful responses
            mock_balances.return_value = {
                "result": [
                    {
                        "token_address": "0x123",
                        "symbol": "TEST",
                        "name": "Test Token",
                        "logo": "logo.png",
                        "decimals": 18,
                        "balance": "1000000000000000000",
                        "balance_formatted": "1.0",
                        "usd_value": 100,
                        "native_token": True
                    },
                    {
                        "token_address": "0x456",
                        "symbol": "TOK2",
                        "name": "Second Token",
                        "logo": "logo2.png",
                        "decimals": 18,
                        "balance": "2000000000000000000",
                        "balance_formatted": "2.0",
                        "usd_value": 200,
                        "native_token": False
                    }
                ]
            }
            mock_approvals.return_value = {
                "result": [
                    {
                        "token_address": "0x123",
                        "spender": "0xSpender",
                        "allowance": "1000000000000000000"
                    }
                ]
            }
            
            tool = FetchChainPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.chain_name, "eth")
            self.assertEqual(result.total_usd_value, 300)
            self.assertEqual(len(result.tokens), 1)  # Regular tokens, not native
            self.assertIsNotNone(result.native_token)
            self.assertEqual(result.native_token.symbol, "TEST")
            self.assertEqual(result.tokens[0].symbol, "TOK2")
            self.assertIsNotNone(result.token_approvals)
            self.assertEqual(len(result.token_approvals), 1)
    
    async def test_chain_portfolio_error(self):
        """Test error handling in chain portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_chain_portfolio.fetch_wallet_balances") as mock_balances:
            mock_balances.return_value = {"error": "API error"}
            
            tool = FetchChainPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.chain_name, "eth")
            self.assertEqual(result.error, "API error")


class TestFetchNftPortfolio(unittest.IsolatedAsyncioTestCase):
    """Test the FetchNftPortfolio skill"""
    
    async def test_nft_portfolio_success(self):
        """Test successful NFT portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_nft_portfolio.fetch_nft_data") as mock_nft_data:
            
            # Mock successful responses
            mock_nft_data.return_value = {
                "result": [
                    {
                        "token_id": "1",
                        "token_address": "0x123",
                        "contract_type": "ERC721",
                        "name": "Test NFT",
                        "symbol": "TNFT",
                        "owner_of": "0xAddress",
                        "metadata": json.dumps({
                            "name": "Test NFT #1",
                            "description": "A test NFT",
                            "image": "image.png",
                            "attributes": [
                                {"trait_type": "Color", "value": "Blue"}
                            ]
                        }),
                        "floor_price": 1.5
                    }
                ],
                "total": 1,
                "page_size": 100,
                "cursor": "next_cursor"
            }
            
            tool = FetchNftPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.chain_name, "eth")
            self.assertEqual(len(result.nfts), 1)
            self.assertEqual(result.nfts[0].token_id, "1")
            self.assertEqual(result.nfts[0].name, "Test NFT")
            self.assertEqual(result.nfts[0].metadata.name, "Test NFT #1")
            self.assertEqual(result.total_count, 1)
            self.assertEqual(result.cursor, "next_cursor")
    
    async def test_nft_portfolio_error(self):
        """Test error handling in NFT portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_nft_portfolio.fetch_nft_data") as mock_nft_data:
            mock_nft_data.return_value = {"error": "API error"}
            
            tool = FetchNftPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.error, "API error")


class TestFetchTransactionHistory(unittest.IsolatedAsyncioTestCase):
    """Test the FetchTransactionHistory skill"""
    
    async def test_transaction_history_success(self):
        """Test successful transaction history fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_transaction_history.fetch_transaction_history") as mock_tx_history:
            
            # Mock successful responses
            mock_tx_history.return_value = {
                "result": [
                    {
                        "hash": "0xabc",
                        "block_number": "12345678",
                        "block_timestamp": "1622480000",
                        "from_address": "0xAddress",
                        "to_address": "0xDest",
                        "value": "1000000000000000000",
                        "value_decimal": 1.0,
                        "value_usd": 100,
                        "gas_price": "20000000000",
                        "gas_used": "21000",
                        "fee": 0.00042,
                        "fee_usd": 0.042,
                        "method": "transfer",
                        "token_transfers": [
                            {
                                "token_address": "0x123",
                                "token_name": "Test Token",
                                "token_symbol": "TEST",
                                "token_decimals": 18,
                                "from_address": "0xAddress",
                                "to_address": "0xDest",
                                "value": "1000000000000000000",
                                "value_decimal": 1.0,
                                "value_usd": 100
                            }
                        ]
                    }
                ],
                "total": 1,
                "page_size": 100,
                "cursor": "next_cursor"
            }
            
            tool = FetchTransactionHistory(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.chain_name, "eth")
            self.assertEqual(len(result.transactions), 1)
            self.assertEqual(result.transactions[0].hash, "0xabc")
            self.assertEqual(result.transactions[0].from_address, "0xAddress")
            self.assertEqual(result.transactions[0].to_address, "0xDest")
            self.assertEqual(result.transactions[0].value_decimal, 1.0)
            self.assertEqual(len(result.transactions[0].token_transfers), 1)
            self.assertEqual(result.transactions[0].token_transfers[0].token_symbol, "TEST")
            self.assertEqual(result.total_count, 1)
            self.assertEqual(result.cursor, "next_cursor")
    
    async def test_transaction_history_error(self):
        """Test error handling in transaction history fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.fetch_transaction_history.fetch_transaction_history") as mock_tx_history:
            mock_tx_history.return_value = {"error": "API error"}
            
            tool = FetchTransactionHistory(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="0xAddress", chain_id=1)
            
            self.assertEqual(result.address, "0xAddress")
            self.assertEqual(result.chain_id, 1)
            self.assertEqual(result.error, "API error")


class TestFetchSolanaPortfolio(unittest.IsolatedAsyncioTestCase):
    """Test the FetchSolanaPortfolio skill"""
    
    async def test_solana_portfolio_success(self):
        """Test successful Solana portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.solana.get_solana_portfolio") as mock_portfolio, \
             patch("skills.wallet_portfolio.solana.get_solana_balance") as mock_balance, \
             patch("skills.wallet_portfolio.solana.get_solana_spl_tokens") as mock_tokens, \
             patch("skills.wallet_portfolio.solana.get_token_price") as mock_price, \
             patch("skills.wallet_portfolio.solana.get_solana_nfts") as mock_nfts:
            
            # Mock successful responses
            mock_portfolio.return_value = {
                "nativeBalance": {"solana": 1.5, "lamports": 1500000000},
                "tokens": [
                    {
                        "symbol": "TEST",
                        "name": "Test Token",
                        "mint": "TokenMintAddress",
                        "associatedTokenAddress": "AssocTokenAddress",
                        "amount": 10,
                        "decimals": 9,
                        "amountRaw": "10000000000"
                    }
                ]
            }
            
            mock_balance.return_value = {
                "solana": 1.5,
                "lamports": 1500000000
            }
            
            mock_tokens.return_value = [
                {
                    "symbol": "TEST",
                    "name": "Test Token",
                    "mint": "TokenMintAddress",
                    "associatedTokenAddress": "AssocTokenAddress",
                    "amount": 10,
                    "decimals": 9,
                    "amountRaw": "10000000000"
                }
            ]
            
            mock_price.return_value = {
                "usdPrice": 100,
                "timestamp": 1622480000
            }
            
            mock_nfts.return_value = [
                {
                    "mint": "NFTMintAddress",
                    "name": "Test NFT",
                    "symbol": "TNFT",
                    "associatedTokenAddress": "AssocTokenAddress",
                    "metadata": {"name": "Test NFT", "image": "image.png"}
                }
            ]
            
            tool = FetchSolanaPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(
                address="SolAddress",
                include_nfts=True,
                include_price=True
            )
            
            self.assertEqual(result.address, "SolAddress")
            self.assertEqual(result.sol_balance, 1.5)
            self.assertEqual(result.sol_balance_lamports, 1500000000)
            self.assertEqual(len(result.tokens), 1)
            self.assertEqual(result.tokens[0].token_info.symbol, "TEST")
            self.assertEqual(len(result.nfts), 1)
            self.assertEqual(result.nfts[0].name, "Test NFT")
            self.assertEqual(result.sol_price_usd, 100)
            self.assertEqual(result.sol_value_usd, 150)  # 1.5 SOL * $100
    
    async def test_solana_portfolio_error(self):
        """Test error handling in Solana portfolio fetch"""
        mock_skill_store = MagicMock()
        mock_skill_store.get_agent_skill_data = AsyncMock(return_value=None)
        mock_skill_store.save_agent_skill_data = AsyncMock()
        
        with patch("skills.wallet_portfolio.solana.get_solana_portfolio") as mock_portfolio, \
             patch("skills.wallet_portfolio.solana.get_solana_balance") as mock_balance:
            
            mock_portfolio.return_value = {"error": "API error"}
            mock_balance.return_value = {"error": "API error"}
            
            tool = FetchSolanaPortfolio(
                api_key="test_key",
                skill_store=mock_skill_store,
                agent_id="test_agent",
                agent_store=MagicMock()
            )
            
            result = await tool._arun(address="SolAddress")
            
            self.assertEqual(result.address, "SolAddress")
            self.assertEqual(result.sol_balance, 0)
            self.assertEqual(result.sol_balance_lamports, 0)
            self.assertEqual(result.error, "API error")


class TestChainHelpers(unittest.TestCase):
    """Test chain helper functions"""
    
    def test_setup_chain_provider_evm_only(self):
        """Test setup chain provider with EVM only"""
        mock_agent = MagicMock()
        mock_agent.wallet_portfolio_config = {
            "supported_chains": {"evm": True, "solana": False}
        }
        
        with patch("utils.chain_helpers.ChainProvider") as MockChainProvider:
            chain_provider_instance = MagicMock()
            MockChainProvider.return_value = chain_provider_instance
            
            result = setup_chain_provider(mock_agent)
            
            self.assertEqual(result, chain_provider_instance)
            # Should not have solana_networks set
            self.assertFalse(hasattr(chain_provider_instance, "solana_networks"))
    
    def test_setup_chain_provider_solana_enabled(self):
        """Test setup chain provider with Solana enabled"""
        mock_agent = MagicMock()
        mock_agent.wallet_portfolio_config = {
            "supported_chains": {"evm": True, "solana": True}
        }
        
        with patch("utils.chain_helpers.ChainProvider") as MockChainProvider:
            chain_provider_instance = MagicMock()
            MockChainProvider.return_value = chain_provider_instance
            
            result = setup_chain_provider(mock_agent)
            
            self.assertEqual(result, chain_provider_instance)
            # Should have solana_networks set
            self.assertTrue(hasattr(chain_provider_instance, "solana_networks"))
            self.assertEqual(chain_provider_instance.solana_networks, ["mainnet", "devnet"])
    
    def test_setup_chain_provider_no_config(self):
        """Test setup chain provider with no config"""
        mock_agent = MagicMock()
        mock_agent.wallet_portfolio_config = None
        
        result = setup_chain_provider(mock_agent)
        
        self.assertIsNone(result)


class TestSkillInitialization(unittest.TestCase):
    """Test skill initialization and configuration"""
    
    def test_get_wallet_portfolio_skill(self):
        """Test getting individual skills by name"""
        skill_names = [
            "fetch_wallet_portfolio",
            "fetch_chain_portfolio", 
            "fetch_nft_portfolio",
            "fetch_transaction_history",
            "fetch_solana_portfolio"
        ]
        
        mock_skill_store = MagicMock()
        mock_agent_store = MagicMock()
        mock_chain_provider = MagicMock()
        
        for name in skill_names:
            skill = get_wallet_portfolio_skill(
                name,
                "test_api_key",
                mock_skill_store,
                "test_agent",
                mock_agent_store,
                mock_chain_provider
            )
            
            self.assertIsNotNone(skill)
            self.assertEqual(skill.api_key, "test_api_key")
            
            # Check the correct class is instantiated
            if name == "fetch_wallet_portfolio":
                self.assertIsInstance(skill, FetchWalletPortfolio)
            elif name == "fetch_chain_portfolio":
                self.assertIsInstance(skill, FetchChainPortfolio)
            elif name == "fetch_nft_portfolio":
                self.assertIsInstance(skill, FetchNftPortfolio)
            elif name == "fetch_transaction_history":
                self.assertIsInstance(skill, FetchTransactionHistory)
            elif name == "fetch_solana_portfolio":
                self.assertIsInstance(skill, FetchSolanaPortfolio)
    
    def test_invalid_skill_name(self):
        """Test error handling for invalid skill names"""
        with self.assertRaises(ValueError):
            get_wallet_portfolio_skill(
                "invalid_skill",
                "test_api_key",
                MagicMock(),
                "test_agent",
                MagicMock()
            )
    
    def test_get_skills_public_only(self):
        """Test getting public skills from config"""
        config = {
            "api_key": "test_api_key",
            "public_skills": ["fetch_wallet_portfolio", "fetch_chain_portfolio"],
            "private_skills": ["fetch_nft_portfolio"],
            "supported_chains": {"evm": True, "solana": True}
        }
        
        mock_skill_store = MagicMock()
        mock_agent_store = MagicMock()
        mock_chain_provider = MagicMock()
        
        with patch("skills.wallet_portfolio.get_wallet_portfolio_skill") as mock_get_skill:
            mock_get_skill.side_effect = lambda name, *args, **kwargs: name
            
            skills = get_skills(
                config,
                False,  # is_private=False
                mock_skill_store,
                "test_agent",
                mock_agent_store,
                mock_chain_provider
            )
            
            self.assertEqual(len(skills), 2)
            self.assertEqual(skills[0], "fetch_wallet_portfolio")
            self.assertEqual(skills[1], "fetch_chain_portfolio")
    
    def test_get_skills_public_and_private(self):
        """Test getting both public and private skills"""
        config = {
            "api_key": "test_api_key",
            "public_skills": ["fetch_wallet_portfolio"],
            "private_skills": ["fetch_nft_portfolio", "fetch_chain_portfolio"],
            "supported_chains": {"evm": True, "solana": True}
        }
        
        mock_skill_store = MagicMock()
        mock_agent_store = MagicMock()
        mock_chain_provider = MagicMock()
        
        with patch("skills.wallet_portfolio.get_wallet_portfolio_skill") as mock_get_skill:
            mock_get_skill.side_effect = lambda name, *args, **kwargs: name
            
            skills = get_skills(
                config,
                True,  # is_private=True
                mock_skill_store,
                "test_agent",
                mock_agent_store,
                mock_chain_provider
            )
            
            self.assertEqual(len(skills), 3)
            self.assertIn("fetch_wallet_portfolio", skills)
            self.assertIn("fetch_nft_portfolio", skills)
            self.assertIn("fetch_chain_portfolio", skills)


if __name__ == "__main__":
    unittest.main()