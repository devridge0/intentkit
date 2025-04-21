# LLMs

## Supported Models
For now, we support all models from [OpenAI](https://openai.com/), [DeepSeek](https://www.deepseek.com/), and [Reigent](https://reisearch.box).  
We will support more models in the future.

## Reigent Integration

The Reigent integration allows you to use Reigent's AI models within IntentKit. The integration uses the same ChatOpenAI implementation that powers our OpenAI integration, but with a different base URL.

### Configuration

To use Reigent models:

1. Set this environment variable:
   - `REIGENT_API_KEY`: Your REI Secret Token for authentication

2. Configure your agent to use a model name starting with "reigent" 

### API Reference

Reigent models use the standard OpenAI-compatible endpoint:
```
https://api.reisearch.box/rei/agents/chat-completion
```

Authentication is handled using a REI Secret Token in the Authorization header, similar to how OpenAI API keys are used.
