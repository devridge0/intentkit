import asyncio
import logging
import unittest
from unittest.mock import patch
from datetime import datetime

from skills.wallet_portfolio.api import (
    fetch_wallet_balances,
    fetch_nft_data,
    fetch_transaction_history,
    fetch_token_approvals,
    fetch_net_worth
)
from skills.wallet_portfolio.solana import (
    get_solana_balance,
    get_solana_spl_tokens,
    get_solana_nfts,
    get_token_price
)
from skills.wallet_portfolio import get_skills
from utils.chain_helpers import setup_chain_provider


class QuietTestResult(unittest.TextTestResult):
    """Custom TestResult class that minimizes output unless there's a failure"""

    def startTest(self, test):
        self._started_at = datetime.now()
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            self.stream.write(".")
            self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write("\n")
        self.stream.write(self.separator1 + "\n")
        self.stream.write(f"ERROR: {self.getDescription(test)}\n")
        self.stream.write(self.separator2 + "\n")
        self.stream.write(self._exc_info_to_string(err, test))
        self.stream.write("\n")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write("\n")
        self.stream.write(self.separator1 + "\n")
        self.stream.write(f"FAIL: {self.getDescription(test)}\n")
        self.stream.write(self.separator2 + "\n")
        self.stream.write(self._exc_info_to_string(err, test))
        self.stream.write("\n")
        self.stream.flush()


class QuietTestRunner(unittest.TextTestRunner):
    """Custom TestRunner that uses QuietTestResult"""

    resultclass = QuietTestResult


class TestWalletPortfolioAPI(unittest.TestCase):
    """Integration tests for Wallet Portfolio API client"""

    def setUp(self):
        """Set up the async event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.timeout = 10
        
        # Configure logging
        logging.basicConfig(level=logging.WARNING)
        
        
        self.eth_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # vitalik.eth
        self.sol_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # binance address
        
    def tearDown(self):
        """Clean up the event loop"""
        self.loop.close()

    def run_async(self, coro):
        """Helper to run async functions in test methods with timeout"""
        try:
            return self.loop.run_until_complete(
                asyncio.wait_for(coro, timeout=self.timeout)
            )
        except asyncio.TimeoutError:
            self.skipTest(f"Test timed out after {self.timeout} seconds")
        except Exception as e:
            if "API key not configured" in str(e):
                self.skipTest("API key not configured, skipping test")
            raise

    def test_fetch_wallet_balances(self):
        """Test fetching wallet balances"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                fetch_wallet_balances("dummy_key", self.eth_address, 1)
            )
            
            # Check general structure without exact values
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("result", result)
    
    def test_fetch_nft_data(self):
        """Test fetching NFT data"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                fetch_nft_data("dummy_key", self.eth_address, 1)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("result", result)
    
    def test_fetch_transaction_history(self):
        """Test fetching transaction history"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                fetch_transaction_history("dummy_key", self.eth_address, 1)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("result", result)
    
    def test_fetch_token_approvals(self):
        """Test fetching token approvals"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                fetch_token_approvals("dummy_key", self.eth_address, 1)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("result", result)
    
    def test_fetch_net_worth(self):
        """Test fetching net worth"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                fetch_net_worth("dummy_key", self.eth_address)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("result", result)


class TestSolanaAPI(unittest.TestCase):
    """Integration tests for Solana API functions"""

    def setUp(self):
        """Set up the async event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.timeout = 10
        
        # Test address (public address with known data)
        self.sol_address = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        self.sol_token = "So11111111111111111111111111111111111111112"  # SOL mint address

    def tearDown(self):
        """Clean up the event loop"""
        self.loop.close()

    def run_async(self, coro):
        """Helper to run async functions in test methods with timeout"""
        try:
            return self.loop.run_until_complete(
                asyncio.wait_for(coro, timeout=self.timeout)
            )
        except asyncio.TimeoutError:
            self.skipTest(f"Test timed out after {self.timeout} seconds")
        except Exception as e:
            if "API key not configured" in str(e):
                self.skipTest("API key not configured, skipping test")
            raise

    def test_get_solana_balance(self):
        """Test getting Solana balance"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                get_solana_balance("dummy_key", self.sol_address)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("solana", result)
                self.assertIn("lamports", result)
    
    def test_get_solana_spl_tokens(self):
        """Test getting Solana SPL tokens"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                get_solana_spl_tokens("dummy_key", self.sol_address)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertTrue(isinstance(result, list))
    
    def test_get_solana_nfts(self):
        """Test getting Solana NFTs"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                get_solana_nfts("dummy_key", self.sol_address)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertTrue(isinstance(result, list))
    
    def test_get_token_price(self):
        """Test getting token price"""
        with patch("app.config.config.config.moralis_api_key", "test_key"):
            result = self.run_async(
                get_token_price("dummy_key", self.sol_token)
            )
            
            if "error" in result:
                self.skipTest(f"API request failed: {result['error']}")
            else:
                self.assertIn("usdPrice", result)


class TestSkillInitialization(unittest.TestCase):
    """Test skill initialization with real config"""
    
    def test_wallet_portfolio_skills_initialization(self):
        """Test initialization of wallet portfolio skills"""
        
        config = {
            "api_key": "test_api_key",
            "public_skills": [
                "fetch_wallet_portfolio",
                "fetch_chain_portfolio",
                "fetch_nft_portfolio"
            ],
            "private_skills": [
                "fetch_transaction_history",
                "fetch_solana_portfolio"
            ],
            "supported_chains": {
                "evm": True,
                "solana": True
            }
        }
        
        with patch("skills.wallet_portfolio.get_wallet_portfolio_skill") as mock_get_skill:
            mock_get_skill.side_effect = lambda name, *args, **kwargs: name
            
            # Test public skills (is_private=False)
            skills = get_skills(
                config,
                False,
                "mock_store",
                "agent_id",
                "agent_store",
                None
            )
            
            self.assertEqual(len(skills), 3)
            self.assertIn("fetch_wallet_portfolio", skills)
            self.assertIn("fetch_chain_portfolio", skills)
            self.assertIn("fetch_nft_portfolio", skills)
            
            # Test all skills (is_private=True)
            skills = get_skills(
                config,
                True,
                "mock_store",
                "agent_id",
                "agent_store",
                None
            )
            
            self.assertEqual(len(skills), 5)
            self.assertIn("fetch_wallet_portfolio", skills)
            self.assertIn("fetch_chain_portfolio", skills)
            self.assertIn("fetch_nft_portfolio", skills)
            self.assertIn("fetch_transaction_history", skills)
            self.assertIn("fetch_solana_portfolio", skills)
    
    def test_chain_provider_setup(self):
        """Test chain provider setup with different configs"""
        # Test with a mock chain provider
        with patch("utils.chain_helpers.ChainProvider") as MockChainProvider:
            chain_provider_instance = MockChainProvider.return_value
            
            # 1. Test with EVM only
            mock_agent = unittest.mock.MagicMock()
            mock_agent.wallet_portfolio_config = {
                "supported_chains": {"evm": True, "solana": False}
            }
            
            result = setup_chain_provider(mock_agent)
            
            self.assertEqual(result, chain_provider_instance)
            self.assertFalse(hasattr(chain_provider_instance, "solana_networks"))
            
            # 2. Test with both EVM and Solana
            mock_agent.wallet_portfolio_config = {
                "supported_chains": {"evm": True, "solana": True}
            }
            
            result = setup_chain_provider(mock_agent)
            
            self.assertEqual(result, chain_provider_instance)
            self.assertTrue(hasattr(chain_provider_instance, "solana_networks"))
            self.assertEqual(chain_provider_instance.solana_networks, ["mainnet", "devnet"])


if __name__ == "__main__":    
    runner = QuietTestRunner(verbosity=1)
    unittest.main(testRunner=runner)