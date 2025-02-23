import json

from app.config.config import config
from models.agent import Agent, AgentData


def agent_prompt(agent: Agent, agent_data: AgentData) -> str:
    prompt = "# SYSTEM PROMPT\n\n"
    if config.system_prompt:
        prompt += config.system_prompt + "\n\n"
    prompt += "You are an autonomous AI agent in an opensource platform 'IntentKit'.\n"
    prompt += "Your tools are called 'skills'.\n"
    if agent.name:
        prompt += f"Your name is {agent.name}.\n"
    if agent.ticker:
        prompt += f"Your ticker symbol is {agent.ticker}.\n"
    if agent_data and agent.cdp_enabled:
        if agent_data.cdp_wallet_data:
            wallet_data = json.loads(agent_data.cdp_wallet_data)
            prompt += f"Your CDP wallet address in {agent.cdp_network_id} is {wallet_data['default_address_id']} .\n"
            if agent.cdp_network_id == "base-mainnet":
                prompt += "The USDC contract address in base-mainnet is 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\n"
                prompt += "When you get balance from tools, or pass amount to tools, don't forget they have decimals.\n"
                prompt += "USDC and USDT has 6 decimals, you must divide the amount you get by 10^6, multiply 10^6 when passing to tools.\n"
                prompt += "Other currencies include native ETH usually has 18 decimals, you need divide or multiply 10^18.\n"
        if agent_data.twitter_id:
            prompt += f"Your twitter id is {agent_data.twitter_id}, never reply or retweet yourself.\n"
        if agent_data.twitter_username:
            prompt += f"Your twitter username is {agent_data.twitter_username}.\n"
        if agent_data.twitter_name:
            prompt += f"Your twitter name is {agent_data.twitter_name}.\n"
        if agent_data.telegram_id:
            prompt += f"Your telegram bot id is {agent_data.telegram_id}.\n"
        if agent_data.telegram_username:
            prompt += f"Your telegram bot username is {agent_data.telegram_username}.\n"
        if agent_data.telegram_name:
            prompt += f"Your telegram bot name is {agent_data.telegram_name}.\n"
    prompt += "\n"
    if agent.purpose:
        prompt += f"## Purpose\n\n{agent.purpose}\n\n"
    if agent.personality:
        prompt += f"## Personality\n\n{agent.personality}\n\n"
    if agent.principles:
        prompt += f"## Principles\n\n{agent.principles}\n\n"
    if agent.prompt:
        prompt += f"## Initial Rules\n\n{agent.prompt}\n\n"
    elif agent.cdp_enabled:
        prompt += (
            "## Coinbase AgentKit Skills Guide\n\n"
            "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
            "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
            "them from the faucet if you are on network ID 'base-mainnet'. If not, you can provide your wallet "
            "details and request funds from the user. Before executing your first action, get the wallet details "
            "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
            "again later. If someone asks you to do something you can't do with your currently available tools, "
            "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
            "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
            "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
            "\n\nWallet addresses are public information. If someone asks for your default wallet, current wallet, "
            "personal wallet, crypto wallet, or wallet public address, don't use any address in message history, "
            "you must use the 'get_wallet_details' tool to retrieve your wallet address every time."
        )
    if agent.enso_enabled:
        prompt += """## ENSO Skills Guide\n\nYou are integrated with the Enso API. You can use enso_get_tokens to retrieve token information,
        including APY, Protocol Slug, Symbol, Address, Decimals, and underlying tokens. When interacting with token amounts,
        ensure to multiply input amounts by the token's decimal places and divide output amounts by the token's decimals. 
        Utilize enso_route_shortcut to find the best swap or deposit route. Set broadcast_request to True only when the 
        user explicitly requests a transaction broadcast. Insufficient funds or insufficient spending approval can cause 
        Route Shortcut broadcasts to fail. To avoid this, use the enso_broadcast_wallet_approve tool that requires explicit 
        user confirmation before broadcasting any approval transactions for security reasons.\n\n"""
    if agent.goat_enabled:
        prompt += """## GOAT Skills Guide\n\nYou're using the Great Onchain Agent Toolkit (GOAT) SDK, which provides tools for DeFi, minting, betting, and analytics.
        GOAT supports EVM blockchains and various wallets, including keypairs, smart wallets, LIT, and MPC.\n\n"""
    return prompt
