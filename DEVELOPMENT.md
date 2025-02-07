# Development

## Quick Start

### Docker (Recommended)
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

5. Create your first Agent:
```bash
curl -X POST http://127.0.0.1:8000/agents \
     -H "Content-Type: application/json" \
     -d '{
         "id": "admin",
         "name": "Admin",
         "prompt": "You are an autonomous AI agent. Respond to user queries."
     }'
```
There are many fields that can control the agent's behavior, we have provided a [helper shell](docs/create_agent.sh) for you.

6. Try it out:
```bash
curl "http://127.0.0.1:8000/admin/chat?q=Hello"
```
In terminal, curl cannot auto escape special characters, so you can use browser to test. Just copy the URL to your browser, replace "Hello" with your words.

### Local Development
1. Clone the repository:
```bash
git clone https://github.com/crestalnetwork/intentkit.git
cd intentkit
```

2. Set up your environment:
Python 3.10-3.12 are supported versions, and it's recommended to use 3.12.
If you haven't installed `poetry`, please install it first.
We recommend manually creating a venv; otherwise, the venv created automatically by Poetry may not meet your needs.
```bash
python3.12 -m venv .venv
source .venv/bin/activate
poetry install --with dev
```

3. Configure your environment:
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

"Create Agent" and "Try it out" refer to the Docker section.
