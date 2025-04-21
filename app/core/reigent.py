"""
Custom ChatOpenAI implementation for Reigent API.
This implementation removes the model parameter from the request,
as the Reigent API doesn't support it.
"""
import json
from typing import Any, Dict, List, Mapping, Optional

import requests
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult


class ReigentChatModel(BaseChatModel):
    """Custom ChatOpenAI implementation for Reigent API."""
    
    base_url: str = "https://api.reisearch.box/v1"
    api_key: str
    temperature: float = 0.7
    timeout: float = 120
    model_name: str = "reigent"  # Just for identification
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "reigent-chat"
    
    def _convert_message_to_dict(self, message: BaseMessage) -> dict:
        """Convert a LangChain message to a dict."""
        message_dict = {"role": "user", "content": ""}
        
        if isinstance(message, SystemMessage):
            message_dict["role"] = "system"
            message_dict["content"] = message.content
        elif isinstance(message, AIMessage):
            message_dict["role"] = "assistant"
            message_dict["content"] = message.content
        elif isinstance(message, HumanMessage):
            message_dict["role"] = "user"
            message_dict["content"] = message.content
        elif isinstance(message, ChatMessage):
            message_dict["role"] = message.role
            message_dict["content"] = message.content
        else:
            raise ValueError(f"Message type {type(message)} not supported")
            
        return message_dict
    
    def _create_message_dicts(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Create a list of message dicts from a list of LangChain messages."""
        return [self._convert_message_to_dict(message) for message in messages]
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat response."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Only include the messages parameter
        payload = {
            "messages": self._create_message_dicts(messages),
        }
        
        # Send the request
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            
            # Check for errors
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                raise ValueError(error_msg)
                
            # Parse the response
            response_json = response.json()
            
            # Extract the assistant message
            if "choices" in response_json and len(response_json["choices"]) > 0:
                message = response_json["choices"][0]["message"]
                content = message.get("content", "")
                
                # Create a ChatGeneration with the response
                generation = ChatGeneration(
                    message=AIMessage(content=content),
                )
                
                # Return the ChatResult
                return ChatResult(generations=[generation])
            else:
                raise ValueError("Invalid response from Reigent API")
        except Exception as e:
            raise ValueError(f"Error calling Reigent API: {str(e)}")
            
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs) 