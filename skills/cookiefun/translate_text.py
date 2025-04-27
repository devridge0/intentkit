import logging
from typing import Optional, Type

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.cookiefun.base import CookieFunBaseTool

logger = logging.getLogger(__name__)


class TranslateTextInput(BaseModel):
    """Input for TranslateText tool."""
    
    text: str = Field(
        description="The text that should be translated"
    )
    language: str = Field(
        description="The language the text should be translated to"
    )
    source_language: Optional[str] = Field(
        default=None,
        description="Source language of the text (optional, for more accurate translations)"
    )


class TranslateText(CookieFunBaseTool):
    """Tool for translating text using Cookie.fun's translation API."""

    name: str = "translate_text"
    description: str = (
        "Translate text to different languages using Cookie.fun's translation system.\n"
        "Use this when you need to translate text to another language."
    )
    args_schema: Type[BaseModel] = TranslateTextInput

    async def _arun(
        self,
        text: str,
        language: str,
        source_language: Optional[str] = None,
        config: RunnableConfig = None,
        **kwargs
    ) -> str:
        """Translate text using Cookie.fun API."""
        context = self.context_from_config(config)
        api_key = context.config.get("cookiefun_api_key")
        if not api_key:
            return "Error: Cookie.fun API key not configured"

        try:
            params = {
                "text": text,
                "language": language
            }
            if source_language:
                params["source_language"] = source_language

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cookie-api.com/api/translate",
                    params=params,
                    headers={"Authorization": api_key},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("success"):
                    return data.get("response", "No translation received")
                else:
                    return f"Error: {data.get('error', 'Unknown error')}"

        except httpx.HTTPError as e:
            logger.error(f"HTTP error when translating text: {str(e)}")
            return f"Error translating text: {str(e)}"
        except Exception as e:
            logger.error(f"Error in translation: {str(e)}")
            return f"Unexpected error: {str(e)}" 