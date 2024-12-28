# Twitter Integration

IntentKit provides two ways to integrate with Twitter: using it as an entrypoint for your agent, or incorporating Twitter-specific skills into your agent's capabilities.

## Twitter as an Entrypoint

Entrypoint is a type of conversational interface.

The Twitter entrypoint allows your agent to automatically respond to Twitter mentions. When enabled, the agent will monitor mentions every 15 minutes and respond to them all.

### Configuration

1. Enable Twitter for your agent:
```python
agent.twitter_enabled = True
```

2. Configure Twitter credentials in your agent's config:
```python
agent.twitter_config = {
    "bearer_token": "your_bearer_token",
    "consumer_key": "your_consumer_key",
    "consumer_secret": "your_consumer_secret",
    "access_token": "your_access_token",
    "access_token_secret": "your_access_token_secret"
}
```

3. Run the Twitter entrypoint:
```bash
python -m app.entrypoints.twitter
```

### How it Works

The Twitter entrypoint:
- Polls for new mentions every 15 minutes
- Uses both `since_id` and `start_time` for reliable mention tracking
- Maintains the last processed tweet ID in the agent's plugin data
- Automatically manages API rate limits and quotas
- Responds to mentions as threaded replies

## Twitter Skills

IntentKit provides a set of Twitter-specific skills that can be added to your agent's toolkit. All skills are built on top of the `TwitterBaseTool` base class which handles authentication and client initialization.

### Available Skills

1. `TwitterGetMentions`
   - Retrieves mentions of the authenticated user
   - Uses both `since_id` and `start_time` for reliable mention tracking
   - Always looks back 24 hours for safety
   - No additional parameters required

2. `TwitterGetTimeline`
   - Retrieves tweets from the authenticated user's timeline
   - Tracks the last retrieved tweet using timestamp
   - Returns formatted timeline data
   - No additional parameters required

3. `TwitterPostTweet`
   - Posts new tweets to Twitter
   - Parameters:
     - `text`: Tweet content (max 280 characters)

4. `TwitterReplyTweet`
   - Posts reply tweets to existing tweets
   - Parameters:
     - `tweet_id`: ID of the tweet to reply to
     - `text`: Reply content (max 280 characters)

### Using Twitter Skills

Add Twitter skills to your agent:

```python
from skills.twitter import get_twitter_skill
from tweepy import Client

# Create Twitter client
client = Client(
    bearer_token="your_bearer_token",
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    access_token="your_access_token",
    access_token_secret="your_access_token_secret"
)

# Add skills to your agent
agent.add_tool(get_twitter_skill("get_mentions", client))
agent.add_tool(get_twitter_skill("post_tweet", client))
agent.add_tool(get_twitter_skill("reply_tweet", client))
agent.add_tool(get_twitter_skill("get_timeline", client))
```

## Rate Limits and Quotas

IntentKit implements quota management for Twitter interactions:

- Daily limits: Configurable maximum tweets per day
- Total limits: Overall maximum tweets
- Quota tracking: Automatically tracks and enforces limits
- Reset periods: Daily quotas reset at UTC midnight

## Best Practices

1. Error Handling
   - Always handle Twitter API errors gracefully
   - Implement exponential backoff for rate limits
   - Log failed interactions for debugging

2. Content Guidelines
   - Keep responses within Twitter's character limit
   - Handle thread creation for longer responses
   - Consider Twitter's content policies

3. Security
   - Store Twitter credentials securely
   - Use environment variables for sensitive data
   - Regularly rotate access tokens

## Example Use Cases

1. Social Media Manager Bot
   ```python
   from app.models.agent import Agent
   
   # Create an agent with Twitter skills
   agent = Agent(
       name="Social Media Manager",
       twitter_enabled=True,
       twitter_skills=["get_mentions", "post_tweet", "reply_tweet"],
       twitter_config={
           "bearer_token": "your_bearer_token",
           "consumer_key": "your_consumer_key",
           "consumer_secret": "your_consumer_secret",
           "access_token": "your_access_token",
           "access_token_secret": "your_access_token_secret"
       },
       prompt="You are a helpful social media manager. Monitor mentions and engage with users professionally."
   )
   ```

2. Content Aggregator with Timeline Analysis
   ```python
   # Create an agent that analyzes timeline content
   agent = Agent(
       name="Content Analyzer",
       twitter_enabled=True,
       twitter_skills=["get_timeline", "post_tweet"],
       twitter_config={...},  # Twitter credentials
       prompt="""You are a content analyzer. Monitor the timeline for trending topics and provide insights.
       When you find interesting patterns, share them as tweets."""
   )
   ```

3. Interactive Support Assistant
   ```python
   # Create a support agent that handles user queries
   agent = Agent(
       name="Support Assistant",
       twitter_enabled=True,
       twitter_skills=["get_mentions", "reply_tweet"],
       twitter_config={...},  # Twitter credentials
       prompt="""You are a support assistant. Monitor mentions for support queries.
       Respond helpfully and professionally to user questions.
       If you can't help, politely explain why and suggest alternatives."""
   )
   ```

Each example demonstrates:
- Proper agent configuration with Twitter credentials
- Specific skill selection for the use case
- Custom prompts to guide agent behavior
- Integration with IntentKit's agent system

## Troubleshooting

Common issues and solutions:

1. Rate Limit Exceeded
   - Check your quota settings
   - Implement proper waiting periods
   - Use the built-in quota management

2. Authentication Errors
   - Verify credential configuration
   - Check token expiration
   - Ensure proper permission scopes

3. Missing Mentions
   - Verify `since_id` tracking
   - Check `start_time` configuration
   - Monitor the Twitter entrypoint logs