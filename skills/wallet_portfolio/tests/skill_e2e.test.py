import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from skills.wallet_portfolio import get_skills, get_wallet_portfolio_skill
from skills.wallet_portfolio.fetch_wallet_portfolio import FetchWalletPortfolio
from skills.wallet_portfolio.fetch_chain_portfolio import FetchChainPortfolio
from skills.wallet_portfolio.fetch_nft_portfolio import FetchNftPortfolio
from skills.wallet_portfolio.fetch_transaction_history import FetchTransactionHistory
from skills.wallet_portfolio.solana import FetchSolanaPortfolio


class TestSkillInitialization(unittest.TestCase):
    """Test skill initialization and configuration"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.mock_skill_store = MagicMock()
        self.mock_agent_store = MagicMock()
        self.mock_chain_provider = MagicMock()
    
    def tearDown(self):
        self.loop.close()
    
    def test_get_wallet_portfolio_skill(self):
        """Test getting individual skills by name"""
        skill_names = [
            "fetch_wallet_portfolio",
            "fetch_chain_portfolio", 
            "fetch_nft_portfolio",
            "fetch_transaction_history",
            "fetch_solana_portfolio"
        ]
        
        for name in skill_names:
            skill = get_wallet_portfolio_skill(
                name,
                "test_api_key",
                self.mock_skill_store,
                "test_agent",
                self.mock_agent_store,
                self.mock_chain_provider,
                {"evm": True, "solana": True}
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
                self.mock_skill_store,
                "test_agent",
                self.mock_agent_store
            )
    
    def test_get_skills(self):
        """Test getting multiple skills from config"""
        config = {
            "api_key": "test_api_key",
            "public_skills": ["fetch_wallet_portfolio", "fetch_chain_portfolio"],
            "private_skills": ["fetch_nft_portfolio"],
            "supported_chains": {"evm": True, "solana": True}
        }
        
        # Test public skills
        public_skills = get_skills(
            config,
            False,  # is_private=False
            self.mock_skill_store,
            "test_agent",
            self.mock_agent_store,
            self.mock_chain_provider
        )
        
        self.assertEqual(len(public_skills), 2)
        self.assertIsInstance(public_skills[0], FetchWalletPortfolio)
        self.assertIsInstance(public_skills[1], FetchChainPortfolio)
        
        
        all_skills = get_skills(
            config,
            True,  # is_private=True
            self.mock_skill_store,
            "test_agent",
            self.mock_agent_store,
            self.mock_chain_provider
        )
        
        self.assertEqual(len(all_skills), 3)