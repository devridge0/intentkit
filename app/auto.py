import sys
import time

from langchain_core.messages import HumanMessage


def run_autonomous_mode(agent_executor, config, interval=180):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Get account mentions for the currently authenticated Twitter (X) user context."
                "If there is no mention, post a new tweet on Twitter,"
                "saying you are waiting for mentions, every 3 minutes you will reply one person."
                "If you have a mention, pickup the first one, reply to the mention."
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)
