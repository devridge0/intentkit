# Web Search Skill

This skill enables agents to search the web for up-to-date information using the [Tavily](https://tavily.com/) search API.

## Overview

The Web Search skill allows agents to:
- Search the internet for current information
- Retrieve relevant search results with snippets and URLs
- Find answers to questions that may not be in the agent's training data
- Access real-time information and news

## Configuration

To enable this skill, add the following to your agent configuration:

```yaml
skills:
  web_search:
    enabled: true
    api_key: "your-tavily-api-key"
    states:
      web_search: public  # or "private" or "disabled"
```

### Configuration Options

- `enabled`: Whether the skill is enabled (true/false)
- `api_key`: Your Tavily API key
- `states.web_search`: The state of the web search skill
  - `public`: Available to agent owner and all users
  - `private`: Available only to the agent owner
  - `disabled`: Not available to anyone

## Usage

The agent will automatically use web search when:
- A user asks for current information or news
- The agent needs to verify facts or find up-to-date information
- A query seeks information that may not be in the agent's training data

## Example Interaction

**User**: "What's the current price of Bitcoin?"

**Agent**: *Uses web search to find current cryptocurrency prices*

## API Requirements

This skill requires a valid Tavily API key. You can sign up for one at [tavily.com](https://tavily.com/).

## Limitations

- Search results are limited to a maximum of 10 items per query
- The quality of results depends on the Tavily search API
- Rate limits may apply based on your Tavily API plan 