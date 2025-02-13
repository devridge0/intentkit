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
    The Acolyt Data Fetcher is a versatile LangChain tool designed to interact with the Acolyt chat API to retrieve insightful data
    across various categories, including Twitter Metrics, Onchain Analysis, DEX & Trading, and Overall Metrics. This tool seamlessly
    processes user queries, fetches relevant data from the Acolyt API, and returns concise, summarized responses for easy consumption.

    Features:
    - Twitter Metrics: Retrieve engagement metrics for specific Twitter accounts, Identify which AI agents have the highest count of smart followers, Display the best tweets from specified accounts, Compare the mindshare between different AI agents, Determine which agents have the highest impressions-to-followers ratio.
    - Onchain Analysis: Fetch the current market capitalization for tokens, Show the distribution of top holders for tokens, Identify tokens with the highest whale concentration, Compare holder retention rates between tokens, Calculate the Herfindahl index for tokens, List tokens with large amount of holders.
    - DEX & Trading: Get the 24-hour trading volume for tokens, Identify which DEX has the highest liquidity for tokens, Obtain the buy/sell ratio for tokens over specific time periods. Compare price changes across different timeframes for tokens. List trading pairs with over a value in liquidity for tokens.
    - Overall Metrics: Identify projects with the highest smart engagement relative to their market cap, Determine which agents have the best mindshare relative to their market cap. Compare the percentage of smart followers across the top n AI agents by market cap


    Attributes:
        name (str): Name of the tool, specifically "acolyt_ask_gpt".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    name: str = "acolyt_ask_gpt"
    description: str = """
        The Acolyt Data Fetcher is a LangChain tool accessing the Acolyt chat API for data across Twitter Metrics, Onchain Analysis, DEX & Trading, and Overall Metrics.  It processes queries, fetches data, and returns summarized responses. Features include:

        Twitter: Engagement metrics, top smart follower counts, best tweets, mindshare comparison, impressions/follower ratio.
        Onchain: Market cap, holder distribution, whale concentration, holder retention, Herfindahl index, high holder count tokens.
        DEX & Trading: 24h volume, top DEX liquidity, buy/sell ratio, price change comparison, high liquidity pairs.
        Overall: Smart engagement/market cap ratio, mindshare/market cap ratio, smart follower percentage comparison across top AI agents.
        """
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
