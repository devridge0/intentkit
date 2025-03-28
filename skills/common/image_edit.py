import io
import logging
from typing import Type

import aiohttp
import openai
from langchain_core.runnables import RunnableConfig
from PIL import Image
from pydantic import BaseModel, Field

from skills.common.base import CommonBaseTool

logger = logging.getLogger(__name__)


class ImageEditInput(BaseModel):
    """Input for ImageEdit tool."""

    prompt: str = Field(
        description="A text description of the desired image. The maximum length is 1000 characters.",
    )
    image: str = Field(
        description="URL of the image to edit.",
    )


class ImageEdit(CommonBaseTool):
    """Tool for editing images using OpenAI's image editing capabilities.

    This tool takes an image URL and a prompt, resizes the image to 1024x1024,
    and then sends it to OpenAI's image editing API.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "dalle_image_edit"
    description: str = (
        "Edit an existing image based on a text prompt.\n"
        "The image will be resized to a 1024x1024 square before processing.\n"
        "Provide a URL to the image and a descriptive prompt for the edit."
    )
    args_schema: Type[BaseModel] = ImageEditInput

    async def _arun(
        self, prompt: str, image: str, config: RunnableConfig, **kwargs
    ) -> str:
        """Implementation of the tool to edit images.

        Args:
            prompt (str): The text prompt describing the desired edit.
            image (str): URL of the image to edit.

        Returns:
            str: URL of the edited image.
        """
        context = self.context_from_config(config)
        logger.debug(f"context: {context}")

        # Get the OpenAI client from the skill store
        api_key = self.skill_store.get_system_config("openai_api_key")
        client = openai.AsyncOpenAI(api_key=api_key)

        try:
            # Download the image from the URL
            async with aiohttp.ClientSession() as session:
                async with session.get(image) as response:
                    if response.status != 200:
                        return f"Error: Failed to download image from URL: {response.status}"
                    image_data = await response.read()

            # Process the image to 1024x1024
            img = Image.open(io.BytesIO(image_data))

            # Determine the crop dimensions to make it square
            width, height = img.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size

            # Crop to square and resize to 1024x1024
            img = img.crop((left, top, right, bottom))
            img = img.resize((1024, 1024), Image.Resampling.LANCZOS)

            # Convert to RGBA format which is required by OpenAI API
            img = img.convert("RGBA")

            # Convert to bytes for the API
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Use OpenAI API to edit the image
            response = await client.images.edit(
                image=buffer,
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            logger.debug(f"Response: {response}")

            # Return the URL of the edited image
            return response.data[0].url

        except Exception as e:
            logger.error(f"Error editing image: {e}")
            return f"Error editing image: {str(e)}"
