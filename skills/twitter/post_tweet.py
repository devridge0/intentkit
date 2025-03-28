import os
import tempfile
from typing import Optional, Type

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import get_twitter_client
from skills.twitter.base import TwitterBaseTool


class TwitterPostTweetInput(BaseModel):
    """Input for TwitterPostTweet tool."""

    text: str = Field(
        description="The text content of the tweet to post", max_length=280
    )
    image: Optional[str] = Field(
        default=None, description="Optional URL of an image to attach to the tweet"
    )


class TwitterPostTweet(TwitterBaseTool):
    """Tool for posting tweets to Twitter.

    This tool uses the Twitter API v2 to post new tweets to Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_post_tweet"
    description: str = "Post a new tweet to Twitter"
    args_schema: Type[BaseModel] = TwitterPostTweetInput

    async def _arun(
        self,
        text: str,
        image: Optional[str] = None,
        config: RunnableConfig = None,
        **kwargs,
    ) -> str:
        """Async implementation of the tool to post a tweet.

        Args:
            text (str): The text content of the tweet to post.
            image (Optional[str]): Optional URL of an image to attach to the tweet.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            str: The ID of the posted tweet.

        Raises:
            Exception: If there's an error posting to the Twitter API.
        """
        try:
            context = self.context_from_config(config)
            twitter = get_twitter_client(
                agent_id=context.agent.id,
                skill_store=self.skill_store,
                config=context.config,
            )

            # Check rate limit only when not using OAuth
            if not twitter.use_key:
                await self.check_rate_limit(
                    context.agent.id, max_requests=24, interval=1440
                )

            client = await twitter.get_client()
            media_ids = []

            # Handle image upload if provided
            if image:
                if twitter.use_key:
                    raise ValueError(
                        "Image upload is not supported when using API key authentication"
                    )
                # Get agent data to access the token
                agent_data = await self.skill_store.get_agent_data(context.agent.id)
                if not agent_data or not agent_data.twitter_access_token:
                    raise ValueError("Twitter access token not found in agent data")

                # Download the image
                async with httpx.AsyncClient() as session:
                    response = await session.get(image)
                    if response.status_code == 200:
                        # Create a temporary file to store the image
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                            tmp_file.write(response.content)
                            tmp_file_path = tmp_file.name

                        # tweepy is outdated, we need to use httpx call new API
                        try:
                            # Upload the image directly to Twitter using the Media Upload API
                            headers = {
                                "Authorization": f"Bearer {agent_data.twitter_access_token}"
                            }

                            # Upload to Twitter's media/upload endpoint using multipart/form-data
                            upload_url = "https://api.twitter.com/2/media/upload"

                            # Get the content type from the response headers or default to image/jpeg
                            content_type = response.headers.get(
                                "content-type", "image/jpeg"
                            )

                            # Create a multipart form with the image file using the correct content type
                            files = {
                                "media": (
                                    "image",
                                    open(tmp_file_path, "rb"),
                                    content_type,
                                )
                            }

                            upload_response = await session.post(
                                upload_url, headers=headers, files=files
                            )

                            if upload_response.status_code == 200:
                                media_data = upload_response.json()
                                if "id" in media_data:
                                    media_ids.append(media_data["id"])
                                else:
                                    raise ValueError(
                                        f"Unexpected response format from Twitter media upload: {media_data}"
                                    )
                            else:
                                raise ValueError(
                                    f"Failed to upload image to Twitter. Status code: {upload_response.status_code}, Response: {upload_response.text}"
                                )
                        finally:
                            # Clean up the temporary file
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                    else:
                        raise ValueError(
                            f"Failed to download image from URL: {image}. Status code: {response.status_code}"
                        )

            # Post tweet using tweepy client
            tweet_params = {"text": text, "user_auth": twitter.use_key}
            if media_ids:
                tweet_params["media_ids"] = media_ids

            response = await client.create_tweet(**tweet_params)
            if "data" in response and "id" in response["data"]:
                tweet_id = response["data"]["id"]
                return tweet_id
            else:
                raise ValueError("Failed to post tweet.")

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
