from typing import Type

import httpx
from langchain.tools.base import ToolException
from pydantic import BaseModel, Field
from typing_extensions import Literal

from skills.acolyt.base import AcolytBaseTool

from .base import base_url


class AcolytAskGptInput(BaseModel):
    question: str


class InputMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool", "function"] = Field(
        "user", description="The role of the message sender."
    )
    content: str


class AcolytAskGptRequest(BaseModel):
    messages: list[InputMessage]
    model: str | None = Field("gpt-4o", description="The AI model to be used.")
    stream: bool | None = Field(
        False, description="To request for response of type stream."
    )
    temperature: float | None = Field(
        0.7,
        le=2,
        ge=0,
        description="Controls the degree of randomness in the generated text.",
    )


class OutputMessage(BaseModel):
    content: str | None = Field(
        None,
        description="The output content of the question response from acolyt API call.",
    )


class OutputChoices(BaseModel):
    finish_reason: Literal[
        "stop", "length", "tool_calls", "content_filter", "function_call"
    ] = Field(description="The reason of GPT method stop.")
    message: OutputMessage


class AcolytAskGptOutput(BaseModel):
    choices: list[OutputChoices]


class AcolytAskGpt(AcolytBaseTool):
    """
    This tool allows users to ask questions which are then sent to the Acolyt API. this should be run if the user requests to
    ask Acolyt explicitly.
    The API response is processed and summarized before being returned to the user.


    Attributes:
        name (str): Name of the tool, specifically "acolyt_ask_gpt".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    name: str = "acolyt_ask_gpt"
    description: str = (
        """
        This tool allows users to ask questions which are then sent to the Acolyt API. this should be run if the user requests to
        ask Acolyt explicitly.
        The API response is processed and summarized before being returned to the user.
        """
    )
    args_schema: Type[BaseModel] = AcolytAskGptInput

    def _run(self, question: str) -> AcolytAskGptOutput:
        """Run the tool to get the tokens and APYs from the API.

        Returns:
             AcolytAskOutput: A structured output containing output of Acolyt chat completion API.

        Raises:
            Exception: If there's an error accessing the Acolyt API.
        """
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, question: str) -> AcolytAskGptOutput:
        """Run the tool to get answer from Acolyt GPT.
        Args:
            question (str): The question body from user.
        Returns:
            AcolytAskOutput: A structured output containing output of Acolyt chat completion API.

        Raises:
            Exception: If there's an error accessing the Acolyt API.
        """
        url = f"{base_url}/api/chat/completions"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = AcolytAskGptRequest(
            messages=[InputMessage(content=question)],
        ).model_dump(exclude_none=True)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, headers=headers, timeout=30, json=body
                )
                response.raise_for_status()
                json_dict = response.json()

                res = AcolytAskGptOutput(**json_dict)

                return res
            except httpx.RequestError as req_err:
                raise ToolException(
                    f"request error from Acolyt API: {req_err}"
                ) from req_err
            except httpx.HTTPStatusError as http_err:
                raise ToolException(
                    f"http error from Acolyt API: {http_err}"
                ) from http_err
            except Exception as e:
                raise ToolException(f"error from Acolyt API: {e}") from e
