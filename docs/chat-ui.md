# IntentKit Sandbox UI

The IntentKit Sandbox UI is a Next.js application specifically designed for testing and interacting with IntentKit agents.

<div align="center">
  <video src="https://github.com/user-attachments/assets/dbedb56b-4bb6-4dcf-97cd-b82913b99461" width="600" autoplay loop muted playsinline></video>
</div>

## Overview

The Sandbox UI allows you to:

- Chat with your IntentKit agents directly through a user-friendly interface
- View and manage agent configurations
- Test agent skills (token, portfolio, etc.)
- View JSON responses with syntax highlighting
- Configure server connection settings

## Setup

### Prerequisites

- Node.js 14.x or higher
- npm or yarn
- Running IntentKit server (see [Development Guide](../DEVELOPMENT.md))

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/bluntbrain/intentkit-sandbox-ui.git
   cd intentkit-sandbox-ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Access the UI:
   Open your browser and navigate to [http://localhost:3000](http://localhost:3000)

## Using the Chat UI

### Connecting to IntentKit Server

By default, the UI connects to an IntentKit server running on `http://127.0.0.1:8000`. You can change this by clicking the gear icon (⚙️) in the UI and entering a different server URL.

### Agent Selection

The sidebar displays a list of all available agents from your connected IntentKit server. Click on an agent to select it and start interacting.

### Chat Interface

The main interface allows you to:

1. Send messages to the selected agent
2. View agent responses in a conversational format
3. Toggle between chat and agent configuration views
4. View detailed JSON responses for examining skill execution results

### Testing Skills

The Chat UI is especially useful for testing skills:

1. Create messages that would trigger specific skills
2. Observe how the agent decides which skills to use
3. View the results of skill execution
4. Test the agent's ability to use multiple skills in sequence

### Viewing Agent Configuration

Click the "View Details" button to switch from chat view to configuration view. This allows you to examine the agent's:

- Basic information
- Enabled skills and their settings
- Prompt configuration
- Other agent-specific settings

## Troubleshooting

- **Can't connect to the server?** Make sure the IntentKit server is running at the configured URL
- **No agents showing up?** You need to create at least one agent using the IntentKit CLI or API
- **Authentication errors?** Click the gear icon to enter your credentials if your server requires authentication

## Development

If you want to contribute to the Sandbox UI or customize it for your needs, the codebase is built with:

- Next.js for the framework
- React for components
- Tailwind CSS for styling

## Additional Resources

- [IntentKit GitHub Repository](https://github.com/crestalnetwork/intentkit)
- [IntentKit Sandbox UI Repository](https://github.com/bluntbrain/intentkit-sandbox-ui)
- [Building Skills for IntentKit](contributing/skills.md) 