import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Type

import httpx
from pydantic import BaseModel, Field

from abstracts.exception import RateLimitExceeded
from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill


class TwitterBaseTool(IntentKitSkill):
    """Base class for Twitter tools."""

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )

    @property
    def category(self) -> str:
        return "twitter"

    async def check_rate_limit(
        self, agent_id: str, max_requests: int = 1, interval: int = 15
    ) -> None:
        """Check if the rate limit has been exceeded.

        Args:
            agent_id: The ID of the agent.
            max_requests: Maximum number of requests allowed within the rate limit window.
            interval: Time interval in minutes for the rate limit window.

        Raises:
            RateLimitExceeded: If the rate limit has been exceeded.
        """
        rate_limit = await self.skill_store.get_agent_skill_data(
            agent_id, self.name, "rate_limit"
        )

        current_time = datetime.now(tz=timezone.utc)

        if (
            rate_limit
            and rate_limit.get("reset_time")
            and rate_limit["count"] is not None
            and datetime.fromisoformat(rate_limit["reset_time"]) > current_time
        ):
            if rate_limit["count"] >= max_requests:
                raise RateLimitExceeded("Rate limit exceeded")

            rate_limit["count"] += 1
            await self.skill_store.save_agent_skill_data(
                agent_id, self.name, "rate_limit", rate_limit
            )

            return

        # If no rate limit exists or it has expired, create a new one
        new_rate_limit = {
            "count": 1,
            "reset_time": (current_time + timedelta(minutes=interval)).isoformat(),
        }
        await self.skill_store.save_agent_skill_data(
            agent_id, self.name, "rate_limit", new_rate_limit
        )
        return

    async def upload_media(self, agent_id: str, image_url: str) -> List[str]:
        """Upload media to Twitter and return the media IDs.

        Args:
            agent_id: The ID of the agent.
            image_url: The URL of the image to upload.

        Returns:
            List[str]: A list of media IDs for the uploaded media.

        Raises:
            ValueError: If there's an error uploading the media.
        """
        # Get agent data to access the token
        agent_data = await self.skill_store.get_agent_data(agent_id)
        if not agent_data or not agent_data.twitter_access_token:
            raise ValueError("Twitter access token not found in agent data")

        media_ids = []
        # Download the image
        async with httpx.AsyncClient() as session:
            response = await session.get(image_url)
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
                    content_type = response.headers.get("content-type", "image/jpeg")

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
                    f"Failed to download image from URL: {image_url}. Status code: {response.status_code}"
                )

        return media_ids

    def process_tweets_response(self, response: Dict[str, Any]) -> List["Tweet"]:
        """Process Twitter API response and convert it to a list of Tweet objects.

        Args:
            response: Raw Twitter API response containing tweets data and includes.

        Returns:
            List[Tweet]: List of processed Tweet objects.
        """
        result = []
        if not response.get("data"):
            return result

        # Create lookup dictionaries from includes
        users_dict = {}
        if response.get("includes") and "users" in response.get("includes"):
            users_dict = {
                user["id"]: TwitterUser(
                    id=str(user["id"]),
                    name=user["name"],
                    username=user["username"],
                    description=user["description"],
                    public_metrics=user["public_metrics"],
                    is_following="following" in user.get("connection_status", []),
                    is_follower="followed_by" in user.get("connection_status", []),
                )
                for user in response.get("includes", {}).get("users", [])
            }

        media_dict = {}
        if response.get("includes") and "media" in response.get("includes"):
            media_dict = {
                media["media_key"]: TwitterMedia(
                    media_key=media["media_key"],
                    type=media["type"],
                    url=media.get("url"),
                )
                for media in response.get("includes", {}).get("media", [])
            }

        tweets_dict = {}
        if response.get("includes") and "tweets" in response.get("includes"):
            tweets_dict = {
                tweet["id"]: Tweet(
                    id=str(tweet["id"]),
                    text=tweet["text"],
                    author_id=str(tweet["author_id"]),
                    created_at=datetime.fromisoformat(
                        tweet["created_at"].replace("Z", "+00:00")
                    ),
                    author=users_dict.get(tweet["author_id"]),
                    referenced_tweets=None,  # Will be populated in second pass
                    attachments=None,
                )
                for tweet in response.get("includes", {}).get("tweets", [])
            }

        # Create main tweet objects
        for tweet_data in response.get("data", []):
            try:
                # Create list of media attachments if present
                media_list = []
                if (
                    "attachments" in tweet_data
                    and "media_keys" in tweet_data["attachments"]
                ):
                    media_list = [
                        media_dict[media_key]
                        for media_key in tweet_data["attachments"]["media_keys"]
                        if media_key in media_dict
                    ]

                # Create list of referenced tweets if present
                ref_tweets = []
                if "referenced_tweets" in tweet_data:
                    ref_tweets = [
                        tweets_dict[ref_tweet["id"]]
                        for ref_tweet in tweet_data["referenced_tweets"]
                        if ref_tweet["id"] in tweets_dict
                    ]

                tweet_obj = Tweet(
                    id=str(tweet_data["id"]),
                    text=tweet_data["text"],
                    author_id=str(tweet_data["author_id"]),
                    author=users_dict.get(tweet_data["author_id"]),
                    created_at=datetime.fromisoformat(
                        tweet_data["created_at"].replace("Z", "+00:00")
                    ),
                    referenced_tweets=ref_tweets if ref_tweets else None,
                    attachments=media_list if media_list else None,
                )
                result.append(tweet_obj)
            except Exception as e:
                raise Exception(f"Error processing tweet {tweet_data}: {str(e)}")

        return result


class TwitterMedia(BaseModel):
    """Model representing Twitter media from the API response."""

    media_key: str
    type: str
    url: str | None = None


class TwitterUser(BaseModel):
    """Model representing a Twitter user from the API response."""

    id: str
    name: str
    username: str
    description: str
    public_metrics: dict = Field(
        description="User metrics including followers_count, following_count, tweet_count, listed_count, like_count, and media_count"
    )
    is_following: bool = Field(
        description="Whether the authenticated user is following this user",
        default=False,
    )
    is_follower: bool = Field(
        description="Whether this user is following the authenticated user",
        default=False,
    )


class Tweet(BaseModel):
    """Model representing a Twitter tweet."""

    id: str
    text: str
    author_id: str
    author: TwitterUser | None = None
    created_at: datetime
    referenced_tweets: List["Tweet"] | None = None
    attachments: List[TwitterMedia] | None = None
