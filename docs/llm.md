# LLMs

## Supported Models
For now, we support all models from [OpenAI](https://openai.com/), [DeepSeek](https://www.deepseek.com/), and [Reigent](https://reisearch.box).  
We will support more models in the future.

## Reigent Integration

The Reigent API is OpenAI-compatible but has some limitations. It doesn't accept additional parameters like `model`, `temperature`, etc. 

To work around this, we've created a custom implementation:

```python
from models.llm_reigent import ReigentChatModel

llm = ReigentChatModel(
   api_key=config.reigent_api_key,
)
```

To use Reigent with your agent:

1. Add your Reigent API key to the `.env` file as `REIGENT_API_KEY`
2. Set the agent model name to start with "reigent" (this is only used for identification in our system)

### Configuration

To use Reigent models:

1. Set this environment variable:
   - `REIGENT_API_KEY`: Your REI Secret Token for authentication

2. Configure your agent to use a model name starting with "reigent" 

### API Reference

Reigent models use the v1 OpenAI-compatible endpoint:
```
https://api.reisearch.box/v1/chat/completions
```

Authentication is handled using a REI Secret Token in the Authorization header, similar to how OpenAI API keys are used.
