# How to create an agent

## Your First Agent

Use the following bash script to create your first agent:

```bash
curl -X POST http://127.0.0.1:8000/agents \
     -H "Content-Type: application/json" \
     -d '{
         "id": "admin",
         "name": "Admin",
         "prompt": "You are an autonomous AI agent. Respond to user queries."
     }'
```

## Advanced Agent Creation Script

There are many fields that can control an agent's behavior.
We have provided a [helper shell](create_agent.sh) for your convenience.
To use it, modify the config fields in the script as necessary, then run:

```bash
./create_agent.sh
```

## The Prompt
In agent config, there are 3 fields about prompt, they are `prompt`, `prompt_append` and `autonomous_prompt`.  
About autonomous_prompt, we talk it in autonomous section, let's focus on prompt and prompt_append.

### LLM Interaction
The models cannot remember anything, so every time we interact with it, we have to provide all the 
background information and interaction context (that is, additional knowledge and memory).  
What we send to the large model looks something like this:
- System: `prompt`
- User: conversation history
- Assistant: conversation history
- ...
- User: conversation history
- Assistant: conversation history
- User: currently being said 
- System: `prompt_append` (Optional)

The content of the system role is to inform the AI that it is being addressed by an administrator, 
so it should not treat you like an user. However, your permissions are not necessarily always higher 
than those of regular users; you simply have the advantage of being the first to set various rules 
for the AI to follow according to your logic.  
For example, you can tell it that the system role has the highest authority, and if the user role 
requests an action that violates the rules set by the system role, you should deny it.

### Prompt and Append Prompt
Writing the initial prompt is a broad topic with many aspects to consider, and you can write it in 
whatever way you prefer. Here, I will only address the prompt_append.  
We’ve found that if you emphasize the most important rules again at the end, it significantly increases 
the likelihood of the AI following your rules. You can declare or repeat your core rules in this section.  
One last tip: the AI will perceive this information as having been inserted just before it responds to the user, 
so avoid saying anything like “later” in this instruction, as that “later” will never happen for the AI.
