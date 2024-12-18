import logging

from anyio.lowlevel import checkpoint
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import create_react_agent
from twitter_langchain import TwitterApiWrapper, TwitterToolkit

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from fastapi import HTTPException

from app.config import config
from app.db import Agent, get_db, get_coon

def initialize_agent(aid):
    """Initialize the agent with CDP Agentkit."""
    db = next(get_db())
    # get the agent from the database
    try:
        agent : Agent = db.query(Agent).filter(Agent.id == aid).one()
    except NoResultFound:
        # Handle the case where the user is not found
        raise HTTPException(status_code=404, detail="Agent not found")
    except SQLAlchemyError as e:
        # Handle other SQLAlchemy-related errors
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))
    # Initialize LLM.
    llm = ChatOpenAI(model_name=agent.model,openai_api_key=config.openai_api_key)

    # Load tools
    tools: list[BaseTool] = []

    # Configure CDP Agentkit Langchain Extension.
    if agent.cdp_enabled:
        values = {
            "cdp_api_key_name": config.cdp_api_key_name,
            "cdp_api_key_private_key": config.cdp_api_key_private_key,
            "network_id": getattr(agent,"cdp_network_id","base-sepolia"),
        }
        if agent.cdp_wallet_data:
            # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
            values = {"cdp_wallet_data": agent.cdp_wallet_data}

        agentkit = CdpAgentkitWrapper(**values)

        # save the wallet after first create
        if not agent.cdp_wallet_data:
            agent.cdp_wallet_data = agentkit.export_wallet()
            db.add(agent)
            db.commit()


        # Initialize CDP Agentkit Toolkit and get tools.
        cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
        tools.extend(cdp_toolkit.get_tools())

    # Initialize CDP Agentkit Twitter Langchain
    try:
        wrapper = TwitterApiWrapper(**values)
        toolkit = TwitterToolkit.from_twitter_api_wrapper(wrapper)
        tools.extend(toolkit.get_tools())
    except Exception:
        pass

    # Store buffered conversation history in memory.
    memory = PostgresSaver(get_coon())
    memory.setup()

    prompt = ""
    if agent.name:
        prompt = f"Your name is {agent.name}. "


    if agent.prompt:
        prompt += agent.prompt
    elif agent.cdp_enabled:
        prompt += (
            "You are a helpful agent that can interact onchain using the Coinbase Developer Platform AgentKit. "
            "You are empowered to interact onchain using your tools. If you ever need funds, you can request "
            "them from the faucet if you are on network ID 'base-sepolia'. If not, you can provide your wallet "
            "details and request funds from the user. Before executing your first action, get the wallet details "
            "to see what network you're on. If there is a 5XX (internal) HTTP error code, ask the user to try "
            "again later. If someone asks you to do something you can't do with your currently available tools, "
            "you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, "
            "recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with your "
            "responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
        )

    # Create ReAct Agent using the LLM and CDP Agentkit tools.
    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=prompt,
    )
