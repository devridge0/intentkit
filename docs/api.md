# API Documentation

## REST API Endpoints

### Agent Management

#### GET `/{aid}/chat`
Chat with an agent.

**Parameters:**
- `aid` (path): Agent ID
- `q` (query): Input message

**Response:**
```text
[ You: ]

your message

-------------------
[ Agent: ]

agent response

-------------------
agent cost: 0.123 seconds
```

**Error Responses:**
- `404`: Agent not found
- `429`: Quota exceeded
- `500`: Internal server error

#### POST `/agents`
Create or update an agent.

**Request Body:**
```json
{
  "id": "my-agent",
  "name": "My Agent",
  "model": "gpt-4",
  "prompt": "You are a helpful assistant",
  "autonomous_enabled": false,
  "autonomous_minutes": null,
  "autonomous_prompt": null,
  "cdp_enabled": false,
  "twitter_enabled": false,
  "crestal_skills": ["skill1", "skill2"],
  "common_skills": ["skill3"]
  }
}
```

**Response:**
```json
{
  "id": "my-agent",
  "name": "My Agent",
  ...
}
```

### Health Check

#### GET `/health`
Check API health status.

**Response:**
```json
{
  "status": "healthy"
}
```

## Autonomous Agent Configuration

Autonomous agents can be configured with the following parameters:

- `autonomous_enabled`: Enable autonomous execution
- `autonomous_minutes`: Interval between executions
- `autonomous_prompt`: Prompt for autonomous actions

Example configuration:
```json
{
  "id": "auto-agent",
  "autonomous_enabled": true,
  "autonomous_minutes": 60,
  "autonomous_prompt": "Check for new updates and summarize them"
}
```

## Quota Management

Each agent has quota limits for:
- Total messages
- Monthly messages
- Daily messages
- Total autonomous executions
- Monthly autonomous executions

Quota errors include detailed information about current usage and limits.
