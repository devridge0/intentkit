"""
S3 utility module for storing and retrieving images from AWS S3.
"""

import logging
from typing import Optional

import boto3
import httpx
from botocore.exceptions import ClientError
from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)

# Global variables for S3 configuration
_bucket: Optional[str] = None
_client: Optional[S3Client] = None
_prefix: Optional[str] = None
_cdn_url: Optional[str] = None


def init_s3(bucket: str, cdn_url: str, env: str) -> None:
    """
    Initialize S3 configuration.

    Args:
        bucket: S3 bucket name
        cdn_url: CDN URL for the S3 bucket
        env: Environment name for the prefix

    Raises:
        ValueError: If bucket or cdn_url is empty
    """
    global _bucket, _client, _prefix, _cdn_url

    if not bucket:
        raise ValueError("S3 bucket name cannot be empty")
    if not cdn_url:
        raise ValueError("S3 CDN URL cannot be empty")

    _bucket = bucket
    _cdn_url = cdn_url
    _prefix = f"{env}/intentkit/"
    _client = boto3.client("s3")

    logger.info(f"S3 initialized with bucket: {bucket}, prefix: {_prefix}")


async def store_image(url: str, key: str) -> str:
    """
    Store an image from a URL to S3 asynchronously.

    Args:
        url: Source URL of the image
        key: Key to store the image under (without prefix)

    Returns:
        str: The CDN URL of the stored image, or the original URL if S3 is not initialized

    Raises:
        ClientError: If the upload fails
        httpx.HTTPError: If the download fails
    """
    if not _client or not _bucket or not _prefix or not _cdn_url:
        # If S3 is not initialized, log and return the original URL
        logger.info("S3 not initialized. Returning original URL.")
        return url

    try:
        # Download the image from the URL asynchronously
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Prepare the S3 key with prefix
            prefixed_key = f"{_prefix}{key}"

            # Upload to S3
            _client.upload_fileobj(
                httpx.ByteStream(response.content),
                _bucket,
                prefixed_key,
                ExtraArgs={
                    "ContentType": response.headers.get("Content-Type", "image/jpeg")
                },
            )

            # Return the CDN URL
            cdn_url = f"{_cdn_url}{prefixed_key}"
            logger.info(f"Image uploaded successfully to {cdn_url}")
            return cdn_url

    except httpx.HTTPError as e:
        logger.error(f"Failed to download image from URL {url}: {str(e)}")
        raise
    except ClientError as e:
        logger.error(f"Failed to upload image to S3: {str(e)}")
        raise
