# CryptoCompare Skills

A collection of skills for interacting with the CryptoCompare API to fetch cryptocurrency data and news.

## Skills

### 1. Fetch News
Fetches cryptocurrency news articles for a specific token.

```python
from skills.cryptocompare import get_cryptocompare_skill

news_skill = get_cryptocompare_skill(
    name="fetch_news",
    api_key="your_api_key",
    store=skill_store,
    agent_id="agent_123",
    agent_store=agent_store
)

# Fetch news for Bitcoin
result = await news_skill._arun(token="BTC")
```

### 2. Fetch Price (TODO)
### 3. Fetch Trading Signals (TODO)
### 4. Fetch Top Market Cap (TODO)
### 5. Fetch Top Exchanges (TODO)
### 6. Fetch Top Volume (TODO)

## Configuration

All skills require a CryptoCompare API key. You can get one by signing up at [CryptoCompare](https://min-api.cryptocompare.com/).

## Rate Limiting

All skills include built-in rate limiting to prevent API abuse. The default limit is:
- 1 request per 15 minutes per agent

## Error Handling

All skills return structured output with proper error handling:
```python
class SkillOutput(BaseModel):
    result: Any  # Skill-specific result type
    error: str | None = None
```

## Testing

Run tests with pytest:
```bash
pytest tests/skills/cryptocompare/
```
