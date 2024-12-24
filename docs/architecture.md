# IntentKit Architecture

## Overview

IntentKit is built with a modular architecture that separates concerns into distinct components:


## Components

### 1. FastAPI REST API (`app/main.py`)
- Handles HTTP requests for agent interactions
- Manages agent creation and configuration
- Implements quota management
- Provides health check endpoints

### 2. Agent Engine (`app/ai.py`)
- Initializes and manages AI agents
- Integrates with LangChain for agent execution
- Handles tool integration and management
- Manages agent state and memory

### 3. Autonomous Scheduler (`app/autonomous.py`)
- Schedules and executes autonomous agent tasks
- Manages periodic execution of agent actions
- Handles graceful shutdown and error recovery

### 4. Skills System
- Individual skills (`skill/`)
- Predefined skill sets (`skill_set/`)
- Tool integrations (CDP, Twitter, etc.)

### 5. Database Layer (`app/db.py`)
- Manages agent persistence
- Handles quota tracking
- Stores agent configurations and state

## Data Flow

1. **API Request Flow**
   ```
   Client Request → FastAPI → Agent Engine → Skills/Tools → Response
   ```

2. **Autonomous Execution Flow**
   ```
   Scheduler → Agent Engine → Skills/Tools → Database Update
   ```

3. **Agent Initialization Flow**
   ```
   Request → Load Config → Initialize LLM → Load Tools → Create Agent
   ```

## Key Design Decisions

1. **Agent Caching**
   - Agents are cached in memory for performance
   - Cache is invalidated on configuration changes

2. **Tool Management**
   - Tools are loaded dynamically based on agent configuration
   - Each tool is isolated and independently maintainable

3. **Error Handling**
   - Graceful degradation on tool failures
   - Comprehensive logging for debugging
   - Quota management to prevent abuse

4. **State Management**
   - PostgreSQL for persistent storage
   - In-memory caching for performance
   - Transaction management for data consistency
