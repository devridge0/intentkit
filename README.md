# IntentKit

IntentKit is an autonomous agent framework that enables the creation and management of AI agents with various capabilities including blockchain interactions, social media management, and custom skill integration.

## Features

- 🤖 Autonomous Agent Management
- 🔄 Scheduled Task Execution
- 💼 Quota Management System
- 🔗 Blockchain Integration via CDP (Coinbase Developer Platform)
- 🐦 Twitter Integration
- 🛠️ Extensible Skill System
- 🔌 RESTful API Interface

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/crestal/intentkit.git
cd intentkit
```

2. Set up your environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp example.env .env
# Edit .env with your configuration
```

4. Run the application:
```bash
# Run the API server
python -m app.main

# Run the autonomous agent scheduler
python -m app.autonomous
```

## Configuration

The application can be configured using environment variables or AWS Secrets Manager. Key configuration options:

- `ENV`: Environment (local, testnet-dev, testnet-prod)
- `DB_*`: Database configuration
- `CDP_*`: Coinbase Developer Platform configuration
- `OPENAI_API_KEY`: OpenAI API key for agent interactions

See `example.env` for all available options.

## Project Structure

- `app/`: Core application code
  - `ai.py`: Agent initialization and execution
  - `autonomous.py`: Autonomous agent scheduler
  - `main.py`: FastAPI application
  - `db.py`: Database models and connection
- `skill/`: Custom skill implementations
- `skill_set/`: Predefined skill set collections
- `utils/`: Utility functions
- `manifests/`: Kubernetes deployment manifests

## Development

### Adding New Skills

1. Create a new skill in the `skill/` directory
2. Implement the skill interface
3. Register the skill in `skill/__init__.py`

### Running Tests

```bash
# TODO: Add testing instructions
```

## Deployment

The project includes Kubernetes manifests for deployment:

```bash
kubectl apply -f manifests/testnet-dev/
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.