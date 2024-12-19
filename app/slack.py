"""
Slack notification module for sending messages to Slack channels.
"""
from math import log
from typing import Optional, Union, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import logging
from app.config import config

logger = logging.getLogger(__name__)

def send_slack_message(
    message: str,
    blocks: Optional[list] = None,
    attachments: Optional[list] = None,
    thread_ts: Optional[str] = None,
):
    """
    Send a message to a Slack channel using config values.
    
    Args:
        message: The message text to send
        blocks: Optional blocks for rich message formatting (see Slack Block Kit)
        attachments: Optional attachments for the message
        thread_ts: Optional thread timestamp to reply to a thread
    
    Raises:
        ValueError: If slack token or channel is not found in config
        SlackApiError: If the message fails to send
    """
    # Get token from config
    if not config.slack_token:
        # Write the input message to the log and return
        logger.info("Slack token not found in config")
        logger.info(message)
        if blocks:
            logger.info(blocks)
        if attachments:
            logger.info(attachments)
        return


    # Get channel from config
    if not config.slack_channel:
        raise ValueError("Slack channel not found in config")

    try:
        client = WebClient(token=config.slack_token)
        
        # Prepare the message payload
        msg_payload = {
            'channel': config.slack_channel,
            'text': message,
        }
        
        if blocks:
            msg_payload['blocks'] = blocks
        if attachments:
            msg_payload['attachments'] = attachments
        if thread_ts:
            msg_payload['thread_ts'] = thread_ts

        # Send the message
        client.chat_postMessage(**msg_payload)
        
        logger.info(f"Message sent successfully to channel {config.slack_channel}")
        return
        
    except SlackApiError as e:
        error_msg = f"Failed to send Slack message: {str(e)}"
        logger.error(error_msg)
        raise SlackApiError(message=error_msg, response=e.response)
