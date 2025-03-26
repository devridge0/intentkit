import logging

from epyxid import XID

from app.core.engine import execute_agent
from models.agent import AgentQuota
from models.chat import AuthorType, ChatMessageCreate

logger = logging.getLogger(__name__)


async def run_autonomous_task(
    agent_id: str, agent_owner: str, task_id: str, prompt: str
):
    """
    Run a specific autonomous task for an agent.

    Args:
        agent_id: The ID of the agent
        task_id: The ID of the autonomous task
        prompt: The autonomous prompt to execute
    """
    logger.info(f"Running autonomous task {task_id} for agent {agent_id}")

    try:
        # Get agent quota
        quota = await AgentQuota.get(agent_id)

        # Check if agent has quota
        if not quota.has_autonomous_quota():
            logger.warning(
                f"Agent {agent_id} has no autonomous quota for task {task_id}. "
                f"Monthly: {quota.autonomous_count_monthly}/{quota.autonomous_limit_monthly}, "
                f"Total: {quota.autonomous_count_total}/{quota.autonomous_limit_total}"
            )
            return

        # Run the autonomous action
        chat_id = f"autonomous-{task_id}"
        message = ChatMessageCreate(
            id=str(XID()),
            agent_id=agent_id,
            chat_id=chat_id,
            user_id=agent_owner,
            author_id="autonomous",
            author_type=AuthorType.TRIGGER,
            thread_type=AuthorType.TRIGGER,
            message=prompt,
        )

        # Execute agent and get response
        resp = await execute_agent(message)

        # Update quota after successful run
        await quota.add_autonomous()

        # Log the response
        logger.info(
            f"Task {task_id} completed: " + "\n".join(str(m) for m in resp),
            extra={"aid": agent_id},
        )
    except Exception as e:
        logger.error(
            f"Error in autonomous task {task_id} for agent {agent_id}: {str(e)}"
        )
