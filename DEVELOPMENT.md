# Development

## Quick Start

### Docker (Recommended)
0. Install [Docker](https://docs.docker.com/get-started/get-docker/).

1. Create a new directory and navigate into it:
```bash
mkdir intentkit && cd intentkit
```

2. Download the required files:
```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/crestalnetwork/intentkit/main/docker-compose.yml

# Download example environment file
curl -O https://raw.githubusercontent.com/crestalnetwork/intentkit/main/example.env
```

3. Set up environment:
```bash
# Rename example.env to .env
mv example.env .env

# Edit .env file and add your configuration
# Make sure to set OPENAI_API_KEY
```

4. Start the services:
```bash
docker compose up
```

5. To create your first agent, check out the [agent creation guide](docs/create_agent.md) for development.

6. Try it out:
```bash
curl "http://127.0.0.1:8000/admin/chat?q=Hello"
```
In terminal, curl cannot auto escape special characters, so you can use browser to test. Just copy the URL to your browser, replace "Hello" with your words.

### Local Development
0. Python 3.11-3.12 are supported versions, and it's recommended to use [3.12](https://www.python.org/downloads/).

1. Clone the repository:
```bash
git clone https://github.com/crestalnetwork/intentkit.git
cd intentkit
```

2. Set up your environment:

If you haven't installed [poetry](https://python-poetry.org/), please [install](https://python-poetry.org/docs/#installation) it first.
We recommend manually creating a venv; otherwise, the venv created automatically by Poetry may not meet your needs.
```bash
python3.12 -m venv .venv
source .venv/bin/activate
poetry install --with dev
```

3. Configure your environment:

Read [Configuration](docs/configuration.md) for detailed settings. Then create your local .env file.
```bash
cp example.env .env
# Edit .env with your configuration
```

4. Run the application:
```bash
# Run the API server in development mode
uvicorn app.api:app --reload

# Run the autonomous agent scheduler
python -m app.autonomous
```

Refer to "To create your first agent" and "Try it out" in the Docker section.
