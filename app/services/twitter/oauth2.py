import tweepy
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from app.config.config import config

router = APIRouter(prefix="/callback/auth", tags=["twitter"])

# Initialize Twitter OAuth2 client
oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=config.twitter_oauth2_client_id,
    client_secret=config.twitter_oauth2_client_secret,
    redirect_uri=config.twitter_oauth2_redirect_uri,
    scope=["tweet.read", "tweet.write", "users.read"],
)

print(oauth2_user_handler.get_authorization_url())


@router.get("/twitter")
async def twitter_oauth_callback(state: str, code: str):
    try:
        # TODO: Parse and validate state
        if not state or not code:
            raise HTTPException(
                status_code=400, detail="Missing state or code parameter"
            )

        # Get access token
        access_token = oauth2_user_handler.fetch_token(code)

        # Print tokens for debugging
        print("Access Token:", access_token)

        return JSONResponse(
            content={"message": "Authentication successful"}, status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
