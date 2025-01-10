# Building Skills for IntentKit

This guide will help you create new skills for IntentKit. Skills are the building blocks that give agents their capabilities.

## Overview

A skill in IntentKit is a specialized tool that inherits from `IntentKitSkill` (which extends LangChain's `BaseTool`). Each skill provides specific functionality that agents can use to interact with external services or perform specific tasks.

## Basic Structure

Every skill consists of at least two components:

1. A skill class that inherits from `IntentKitSkill`
2. Input/Output models using Pydantic

### Example Structure
```python
from pydantic import BaseModel
from abstracts.skill import IntentKitSkill

class MySkillInput(BaseModel):
    """Input parameters for your skill"""
    param1: str
    param2: int = 10  # with default value

class MySkillOutput(BaseModel):
    """Output format for your skill"""
    result: str
    error: str | None = None

class MySkill(IntentKitSkill):
    name: str = "my_skill_name"
    description: str = "Description of what your skill does"
    args_schema: Type[BaseModel] = MySkillInput

    def _run(self, param1: str, param2: int = 10) -> MySkillOutput:
        try:
            # Your skill implementation here
            result = f"Processed {param1} {param2} times"
            return MySkillOutput(result=result)
        except Exception as e:
            return MySkillOutput(result="", error=str(e))

    async def _arun(self, param1: str, param2: int = 10) -> MySkillOutput:
        """Async implementation if needed"""
        return await self._run(param1, param2)
```

## Key Components

### 1. Input/Output Models

- Use Pydantic models to define input parameters and output structure
- Input model will be used as `args_schema` in your skill
- Output model ensures consistent return format

### 2. Skill Class

Required attributes:
- `name`: Unique identifier for your skill
- `description`: Clear description of what the skill does
- `args_schema`: Pydantic model for input validation

Required methods:
- `_run`: Synchronous implementation of your skill
- `_arun`: Asynchronous implementation (if needed)

### 3. State Management

Skills have access to persistent storage through `self.store`, which implements `SkillStoreABC`:

```python
# Store agent-specific data
self.store.save_agent_skill_data(
    self.agent_id,  # automatically provided
    self.name,      # your skill name
    "key_name",     # custom key for your data
    {"data": "value"}  # any JSON-serializable data
)

# Retrieve agent-specific data
data = self.store.get_agent_skill_data(
    self.agent_id,
    self.name,
    "key_name"
)

# Store thread-specific data
self.store.save_thread_skill_data(
    thread_id,      # provided in context
    self.agent_id,
    self.name,
    "key_name",
    {"data": "value"}
)

# Retrieve thread-specific data
data = self.store.get_thread_skill_data(
    thread_id,
    self.name,
    "key_name"
)
```

## Best Practices

1. **Error Handling**
   - Always wrap your main logic in try-except blocks
   - Return errors through your output model rather than raising exceptions
   - Provide meaningful error messages

2. **Documentation**
   - Add detailed docstrings to your skill class and methods
   - Document input parameters and return values
   - Include usage examples in docstrings

3. **Input Validation**
   - Use Pydantic models to validate inputs
   - Set appropriate field types and constraints
   - Provide default values when sensible

4. **State Management**
   - Use `self.store` for persistent data storage
   - Keep agent-specific data separate from thread-specific data
   - Use meaningful keys for stored data

5. **Async Support**
   - Implement `_arun` for skills that perform I/O operations
   - Use async libraries when available
   - Maintain consistent behavior between sync and async implementations

## Example: Twitter Timeline Skill

Here's a real-world example of a skill that fetches tweets from a user's timeline:

```python
class TwitterGetTimelineInput(BaseModel):
    """Empty input model as no parameters needed"""
    pass

class Tweet(BaseModel):
    """Model representing a Twitter tweet"""
    id: str
    text: str
    author_id: str
    created_at: datetime
    referenced_tweets: list[dict] | None = None
    attachments: dict | None = None

class TwitterGetTimelineOutput(BaseModel):
    tweets: list[Tweet]
    error: str | None = None

class TwitterGetTimeline(TwitterBaseTool):
    name: str = "twitter_get_timeline"
    description: str = "Get tweets from the authenticated user's timeline"
    args_schema: Type[BaseModel] = TwitterGetTimelineInput

    def _run(self) -> TwitterGetTimelineOutput:
        try:
            # Get last processed tweet ID from storage
            last = self.store.get_agent_skill_data(self.agent_id, self.name, "last")
            since_id = last.get("since_id") if last else None

            # Fetch timeline
            timeline = self.client.get_home_timeline(...)

            # Process and return results
            result = [Tweet(...) for tweet in timeline.data]
            
            # Update storage with newest tweet ID
            if timeline.meta:
                self.store.save_agent_skill_data(
                    self.agent_id,
                    self.name,
                    "last",
                    {"since_id": timeline.meta["newest_id"]}
                )

            return TwitterGetTimelineOutput(tweets=result)
        except Exception as e:
            return TwitterGetTimelineOutput(tweets=[], error=str(e))
```

## Testing Your Skill

1. Create unit tests in the `tests/skills` directory
2. Test both success and error cases
3. Mock external services and dependencies
4. Verify state management behavior
5. Test both sync and async implementations

## Contributing

1. Create your skill in the `skills/` directory
2. Follow the structure of existing skills
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

For more examples, check the existing skills in the `skills/` directory.
