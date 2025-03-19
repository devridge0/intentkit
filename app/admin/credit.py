import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.config.config import config
from models.credit import (
    CreditAccount,
    CreditEvent,
    CreditType,
    OwnerType,
)
from utils.middleware import create_jwt_middleware

logger = logging.getLogger(__name__)
verify_jwt = create_jwt_middleware(config.admin_auth_enabled, config.admin_jwt_secret)

credit_router = APIRouter(prefix="/credit", tags=["Credit"])
credit_router_readonly = APIRouter(prefix="/credit", tags=["Credit"])


# ===== Input models =====
class RechargeRequest(BaseModel):
    """Request model for recharging a user account."""

    upstream_tx_id: Annotated[
        str, Field(str, description="Upstream transaction ID, idempotence Check")
    ]
    user_id: Annotated[str, Field(description="ID of the user to recharge")]
    amount: Annotated[float, Field(gt=0, description="Amount to recharge")]
    note: Annotated[
        Optional[str], Field(None, description="Optional note for the recharge")
    ]


class RewardRequest(BaseModel):
    """Request model for rewarding a user account."""

    upstream_tx_id: Annotated[
        str, Field(str, description="Upstream transaction ID, idempotence Check")
    ]
    user_id: Annotated[str, Field(description="ID of the user to reward")]
    amount: Annotated[float, Field(gt=0, description="Amount to reward")]
    note: Annotated[
        Optional[str], Field(None, description="Optional note for the reward")
    ]


class AdjustmentRequest(BaseModel):
    """Request model for adjusting a user account."""

    upstream_tx_id: Annotated[
        str, Field(str, description="Upstream transaction ID, idempotence Check")
    ]
    user_id: Annotated[str, Field(description="ID of the user to adjust")]
    credit_type: Annotated[CreditType, Field(description="Type of credit to adjust")]
    amount: Annotated[
        float, Field(description="Amount to adjust (positive or negative)")
    ]
    note: Annotated[str, Field(description="Required explanation for the adjustment")]


class UpdateDailyQuotaRequest(BaseModel):
    """Request model for updating account daily quota."""

    upstream_tx_id: Annotated[
        str, Field(str, description="Upstream transaction ID, idempotence Check")
    ]
    daily_quota: Annotated[
        float, Field(gt=0, description="New daily quota value for the account")
    ]
    note: Annotated[str, Field(description="Explanation for changing the daily quota")]


# ===== Output models =====
class CreditEventResponse(BaseModel):
    """Response model for credit events."""

    events: List[CreditEvent]
    total: int


# ===== API Endpoints =====
@credit_router.get("/accounts/{owner_type}/{owner_id}", response_model=CreditAccount)
async def get_account(owner_type: OwnerType, owner_id: str):
    """Get a credit account by owner type and ID.

    Args:
        owner_type: Type of the owner (user, agent, company)
        owner_id: ID of the owner

    Returns:
        The credit account
    """
    # Implementation will be added later
    pass


@credit_router.post(
    "/recharge", response_model=CreditAccount, status_code=status.HTTP_200_OK
)
async def recharge_user_account(request: RechargeRequest):
    """Recharge a user account with credits.

    Args:
        request: Recharge request details

    Returns:
        The updated credit account
    """
    # Implementation will be added later
    pass


@credit_router.post(
    "/reward", response_model=CreditAccount, status_code=status.HTTP_200_OK
)
async def reward_user_account(request: RewardRequest):
    """Reward a user account with credits.

    Args:
        request: Reward request details

    Returns:
        The updated credit account
    """
    # Implementation will be added later
    pass


@credit_router.post(
    "/adjust", response_model=CreditAccount, status_code=status.HTTP_200_OK
)
async def adjust_user_account(request: AdjustmentRequest):
    """Adjust a user account's credits.

    Args:
        request: Adjustment request details

    Returns:
        The updated credit account
    """
    # Implementation will be added later
    pass


@credit_router.put(
    "/accounts/users/{user_id}/daily-quota",
    response_model=CreditAccount,
    status_code=status.HTTP_200_OK,
)
async def update_account_daily_quota(
    user_id: str, request: UpdateDailyQuotaRequest
) -> CreditAccount:
    """Update the daily quota of a credit account.

    Args:
        user_id: ID of the user
        request: Update request details including new daily_quota and explanation note

    Returns:
        The updated credit account
    """
    # Implementation will be added later
    pass


@credit_router_readonly.get(
    "/event/users/{user_id}/expense", response_model=List[CreditEvent]
)
async def list_user_expense_events(
    user_id: str,
    cursor: Annotated[Optional[str], Query(description="Cursor for pagination")] = None,
) -> List[CreditEvent]:
    """List all expense events for a user account.

    Args:
        user_id: ID of the user
        cursor: Cursor for pagination

    Returns:
        List of expense events
    """
    # Implementation will be added later
    pass


@credit_router_readonly.get(
    "/event/users/{user_id}/income", response_model=List[CreditEvent]
)
async def list_user_income_events(
    user_id: str,
    cursor: Annotated[Optional[str], Query(description="Cursor for pagination")] = None,
) -> List[CreditEvent]:
    """List all income events for a user account.

    Args:
        user_id: ID of the user
        cursor: Cursor for pagination

    Returns:
        List of income events
    """
    # Implementation will be added later
    pass


@credit_router_readonly.get(
    "/event/agents/{agent_id}/income", response_model=List[CreditEvent]
)
async def list_agent_income_events(
    agent_id: str,
    cursor: Annotated[Optional[str], Query(description="Cursor for pagination")] = None,
) -> List[CreditEvent]:
    """List all income events for an agent account.

    Args:
        agent_id: ID of the agent
        cursor: Cursor for pagination

    Returns:
        List of income events
    """
    # Implementation will be added later
    pass
