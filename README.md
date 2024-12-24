# IntentKit

IntentKit is an autonomous agent framework that enables the creation and management of AI agents with various capabilities including blockchain interactions, social media management, and custom skill integration.

## Alpha Warning

This project is currently in alpha stage and is not recommended for production use.

## Features

- 🤖 Multiple Agent Support
- 🔄 Autonomous Agent Management
- 🔗 Blockchain Integration (CDP for now, will add more)
- 🐦 Socail Media Integration (Twitter,Telegram for now, will add more)
- 🛠️ Extensible Skill System
- 🔌 Extensible Plugin System

## Quick Start

### Docker (Recommended)
WIP

### Local Development
1. Clone the repository:
```bash
git clone https://github.com/crestal/intentkit.git
cd intentkit
```

2. Set up your environment:
Python 3.10-3.12 are supported versions, and it's recommended to use 3.12.
You can create a virtual environment with a specified version of Python.
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp example.env .env
# Edit .env with your configuration
```

3. Add your first Agent:
```bash
python -m debug.create_agent
```

4. Run the application:
```bash
# Run the API server in development mode
uvicorn app.entrypoints.api:app --reload

# Run the autonomous agent scheduler
python -m app.entrypoints.autonomous
```

## Configuration

The application can be configured using environment variables or AWS Secrets Manager. Key configuration options:

- `ENV`: Environment (local, or others)
- `DB_*`: PostgreSQL Database configuration (Required)
- `OPENAI_API_KEY`: OpenAI API key for agent interactions (Required)
- `CDP_*`: Coinbase Developer Platform configuration (Optional)

See `example.env` for all available options.

## Project Structure

- `app/`: Core application code
  - `ai.py`: Agent initialization and execution
  - `autonomous.py`: Autonomous agent scheduler
  - `main.py`: API entrypoint
  - `db.py`: Database models and connection
- `skill/`: Skill implementations
- `skill_set/`: Predefined skill set collections
- `utils/`: Utility functions

## Development

### Adding New Skills

1. Create a new skill in the `skill/` directory
2. Implement the skill interface
3. Register the skill in `skill/__init__.py`


## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.