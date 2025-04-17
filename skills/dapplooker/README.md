# DappLooker Skill

This skill provides access to the DappLooker API for retrieving comprehensive crypto market data and analytics.

## Features

The DappLooker skill allows your agent to:

- Retrieve detailed token market data using token tickers or contract addresses
- Get real-time price information, market cap, and volume
- Access technical indicators like support/resistance levels and RSI
- View smart money insights including holder metrics and liquidity data
- Check supply information and token fundamentals

## Configuration

To use this skill, you'll need to:

1. Enable the skill in your agent configuration
2. Obtain a DappLooker API key from [DappLooker](https://docs.dapplooker.com/dapplooker-ai/ai-apis)
3. Configure the skill in your agent settings

### Agent Configuration

```yaml
skills:
  dapplooker:
    enabled: true
    api_key: "your_dapplooker_api_key"  # Optional if using environment variable
    states:
      dapplooker_token_data: public  # or "private" for agent owner only
```

### Environment Variable

You can also set the DappLooker API key as an environment variable:

```
DAPPLOOKER_API_KEY=your_dapplooker_api_key
```

The skill will first check the agent configuration for the API key, and if not found, it will use the environment variable.

## Usage

Your agent can now access crypto token data by using the `dapplooker_token_data` skill:

- Query by token ticker (e.g., "aixbt,vader") 
- Query by contract address (e.g., "0x4F9Fd6Be4a90f2620860d680c0d4d5Fb53d1A825")
- Specify blockchain network (default is "base")

## Example

A user might ask:
"What's the current price and market metrics for AIXBT token on Base?"

The agent would use the DappLooker skill to retrieve and present this information in a structured format. 