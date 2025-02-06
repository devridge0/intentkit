# Agent's Memory Cleanup

Agent memory can be cleared using a request that requires an admin JWT token for authentication. This functionality allows for granular control:

- **Clear all agent memory**: Reset the entire memory state of the agent.
- **Clear thread memory**: Clear memory specifically associated with a particular thread within the agent.

> The `thread_id` parameter is used to specify the target thread for memory clearing.

```bash
curl --location '{base_url}/agents/clean-memory' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer {jwt_token}' \
--data '{
    "agent_id": "local",
    "thread_id": "chat1",
    "clean_agent_memory": true,
    "clean_skills_memory": true
}'
```
