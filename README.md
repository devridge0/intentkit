# IntentKit

IntentKit is an autonomous agent framework that enables the creation and management of AI agents with various capabilities including blockchain interactions, social media management, and custom skill integration.

## Alpha Warning

This project is currently in alpha stage and is not recommended for production use.

## Features

- 🤖 Multiple Agent Support
- 🔄 Autonomous Agent Management
- 🔗 Blockchain Integration (EVM chains first)
- 🐦 Social Media Integration (Twitter, Telegram, and more)
- 🛠️ Extensible Skill System
- 🔌 Extensible Plugin System (WIP)

## Architecture

```
                                                                                                       
                                 Entrypoints                                                           
                       │                             │                                                 
                       │   Twitter/Telegram & more   │                                                 
                       └──────────────┬──────────────┘                                                 
                                      │                                                                
  Storage:  ────┐                     │                      ┌──── Skills:                             
                │                     │                      │                                         
  Agent Config  │     ┌───────────────▼────────────────┐     │  Chain Integration
                │     │                                │     │                                         
  Credentials   │     │                                │     │  Wallet Management                      
                │     │           The  Agent           │     │                                         
  Personality   │     │                                │     │  On-Chain Actions                       
                │     │                                │     │                                         
  Memory        │     │      Powered by LangGraph      │     │  Internet Search                        
                │     │                                │     │                                         
  Skill State   │     └────────────────────────────────┘     │  Image Processing                       
            ────┘                                            └────                                     
                                                                                                       
                                                                More and More...                       
                         ┌──────────────────────────┐                                                  
                         │                          │                                                  
                         │  Agent Config & Memory   │                                                  
                         │                          │                                                  
                         └──────────────────────────┘                                                  
                                                                                                       
```

The architecture is a simplified view, and more details can be found in the [Architecture](docs/architecture.md) section.

## Development

Read [Development Guide](DEVELOPMENT.md) to setup different development environments.

## The Model
For now, we only support any model from OpenAI and DeepSeek.  
We will support more models in the future.

## Integrations

### Twitter
[Twitter Integration](docs/twitter.md)

### Coinbase
[Coinbase Integration](docs/skills/cdp.md)

## Configuration

The application can be configured using environment variables or AWS Secrets Manager. Key configuration options:

- `ENV`: Environment (local or others)
- `DB_*`: PostgreSQL Database configuration (Required)
- `OPENAI_API_KEY`: OpenAI API key for agent interactions (Required)
- `CDP_*`: Coinbase Developer Platform configuration (Optional)

See `example.env` for all available options.

## Project Structure

- `abstracts/`: Abstract classes and interfaces
- `app/`: Core application code
  - `core/`: Core modules
  - `services/`: Services
  - `entrypoints/`: Entrypoints means the way to interact with the agent
  - `admin/`: Admin logic
  - `config/`: Configurations
  - `api.py`: REST API server
  - `autonomous.py`: Autonomous agent scheduler
  - `twitter.py`: Twitter listener
  - `telegram.py`: Telegram listener
- `models/`: Database models
- `skills/`: Skill implementations
- `skill_sets/`: Predefined skill set collections
- `plugins/`: Reserved for Plugin implementations
- `utils/`: Utility functions

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

### Contribute Skills

If you want to add a skill collection, follow these steps:

1. Create a new skill collection in the `skills/` directory
2. Implement the skill interface
3. Register the skill in `skills/YOUR_SKILL_COLLECTION/__init__.py`

If you want to add a simple skill, follow these steps:

1. Create a new skill in the `skills/common/` directory
2. Register the skill in `skills/common/__init__.py`

See the [Skill Development Guide](docs/contributing/skills.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
