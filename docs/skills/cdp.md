## CDP AgentKit

All CDP Skills are supported by [AgentKit](https://github.com/coinbase/cdp-agentkit/).

AgentKit supports the following tools:

- `get_wallet_details` - Get details about the MPC Wallet
- `get_balance` - Get balance for specific assets
- `request_faucet_funds` - Request test tokens from the [Base Sepolia faucet](https://portal.cdp.coinbase.com/products/faucet)
- `transfer` - Transfer assets between addresses
- `trade` - Trade assets (mainnets only)
- `deploy_token` - Deploy [ERC-20](https://www.coinbase.com/learn/crypto-glossary/what-is-erc-20) token contracts
- `mint_nft` - Mint NFTs from existing contracts
- `deploy_nft` - Deploy new NFT contracts
- `register_basename` - Register a [Basename](https://www.base.org/names) for the wallet
- `wow_create_token` - Deploy a token using [Zora's Wow Launcher](https://wow.xyz/mechanics) (Bonding Curve) (Base only)
- `wow_buy_token` - Buy [Zora Wow](https://wow.xyz/) ERC-20 memecoin with ETH (Base only)
- `wow_sell_token` - Sell [Zora Wow](https://wow.xyz/) ERC-20 memecoin for ETH (Base only)

Any action not supported by default by AgentKit can be added by [adding agent capabilities](https://docs.cdp.coinbase.com/agentkit/docs/add-agent-capabilities).

AgentKit supports every network that the [CDP SDK supports](https://docs.cdp.coinbase.com/cdp-apis/docs/networks).

