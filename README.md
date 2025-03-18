# IntentKit

<div align="center">
  <img src="docs/images/intentkit_banner.png" alt="IntentKit by Crestal" width="100%" />
</div>
<br>

IntentKit is an autonomous agent framework that enables the creation and management of AI agents with various capabilities including blockchain interaction, social media management, and custom skill integration.

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
                │     │           The Agent            │     │                      
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

Read [Development Guide](DEVELOPMENT.md) to get started with your setup.

## Documentation

Check out [Documentation](docs/) before you start.

## Project Structure

- [abstracts/](abstracts/): Abstract classes and interfaces
- [app/](app/): Core application code
  - [core/](app/core/): Core modules
  - [services/](app/services/): Services
  - [entrypoints/](app/entrypoints/): Entrypoints means the way to interact with the agent
  - [admin/](app/admin/): Admin logic
  - [config/](app/config/): Configurations
  - [api.py](app/api.py): REST API server
  - [autonomous.py](app/autonomous.py): Autonomous agent scheduler
  - [singleton.py](app/singleton.py): Singleton agent scheduler
  - [scheduler.py](app/scheduler.py): Scheduler for periodic tasks
  - [readonly.py](app/readonly.py): Readonly entrypoint
  - [twitter.py](app/twitter.py): Twitter listener
  - [telegram.py](app/telegram.py): Telegram listener
- [clients/](clients/): Clients for external services
- [docs/](docs/): Documentation
- [models/](models/): Database models
- [scripts/](scripts/): Scripts for agent management
- [skills/](skills/): Skill implementations
- [plugins/](plugins/): Reserved for Plugin implementations
- [utils/](utils/): Utility functions

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

### Contribute Skills

First check [Wishlist](docs/contributing/wishlist.md) for active requests.

Once you are ready to start, see [Skill Development Guide](docs/contributing/skills.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
