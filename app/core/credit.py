import logging
from typing import List, Optional, Tuple

from epyxid import XID
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.credit import (
    DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
    DEFAULT_PLATFORM_ACCOUNT_RECHARGE,
    DEFAULT_PLATFORM_ACCOUNT_REWARD,
    CreditAccount,
    CreditAccountTable,
    CreditDebit,
    CreditEvent,
    CreditEventTable,
    CreditTransactionTable,
    CreditType,
    Direction,
    EventType,
    OwnerType,
    TransactionType,
    UpstreamType,
)

logger = logging.getLogger(__name__)


async def recharge(
    session: AsyncSession,
    user_id: str,
    amount: float,
    upstream_tx_id: str,
    note: Optional[str] = None,
) -> CreditAccount:
    """
    Recharge credits to a user account.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to recharge
        amount: Amount of credits to recharge
        upstream_tx_id: ID of the upstream transaction
        note: Optional note for the transaction

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount <= 0:
        raise ValueError("Recharge amount must be positive")

    # 1. Update user account - add credits
    user_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount=amount,
        credit_type=CreditType.PERMANENT,  # Recharge adds to permanent credits
    )

    # 2. Update platform recharge account - deduct credits
    platform_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_RECHARGE,
        credit_type=CreditType.PERMANENT,
        amount=amount,
    )

    # 3. Create credit event record
    event_id = str(XID())
    event = CreditEventTable(
        id=event_id,
        event_type=EventType.RECHARGE,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.INCOME,
        account_id=user_account.id,
        total_amount=amount,
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=amount,
        base_original_amount=amount,
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (credit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECHARGE,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount,
    )
    session.add(user_tx)

    # 4.2 Platform recharge account transaction (debit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.RECHARGE,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    return user_account


async def reward(
    session: AsyncSession,
    user_id: str,
    amount: float,
    upstream_tx_id: str,
    note: Optional[str] = None,
) -> CreditAccount:
    """
    Reward a user account with reward credits.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to reward
        amount: Amount of reward credits to add
        upstream_tx_id: ID of the upstream transaction
        note: Optional note for the transaction

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount <= 0:
        raise ValueError("Reward amount must be positive")

    # 1. Update user account - add reward credits
    user_account = await CreditAccount.income_in_session(
        session=session,
        owner_type=OwnerType.USER,
        owner_id=user_id,
        amount=amount,
        credit_type=CreditType.REWARD,  # Reward adds to reward credits
    )

    # 2. Update platform reward account - deduct credits
    platform_account = await CreditAccount.deduction_in_session(
        session=session,
        owner_type=OwnerType.PLATFORM,
        owner_id=DEFAULT_PLATFORM_ACCOUNT_REWARD,
        credit_type=CreditType.PERMANENT,
        amount=amount,
    )

    # 3. Create credit event record
    event_id = str(XID())
    event = CreditEventTable(
        id=event_id,
        event_type=EventType.REWARD,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=Direction.INCOME,
        account_id=user_account.id,
        total_amount=amount,
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=amount,
        base_original_amount=amount,
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction (credit)
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.REWARD,
        credit_debit=CreditDebit.CREDIT,
        change_amount=amount,
    )
    session.add(user_tx)

    # 4.2 Platform reward account transaction (debit)
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.REWARD,
        credit_debit=CreditDebit.DEBIT,
        change_amount=amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    return user_account


async def adjustment(
    session: AsyncSession,
    user_id: str,
    credit_type: CreditType,
    amount: float,
    upstream_tx_id: str,
    note: str,
) -> CreditAccount:
    """
    Adjust a user account's credits (can be positive or negative).

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to adjust
        credit_type: Type of credit to adjust (FREE, REWARD, or PERMANENT)
        amount: Amount to adjust (positive for increase, negative for decrease)
        upstream_tx_id: ID of the upstream transaction
        note: Required explanation for the adjustment

    Returns:
        Updated user credit account
    """
    # Check for idempotency - prevent duplicate transactions
    await CreditEvent.check_upstream_tx_id_exists(
        session, UpstreamType.API, upstream_tx_id
    )

    if amount == 0:
        raise ValueError("Adjustment amount cannot be zero")

    if not note:
        raise ValueError("Adjustment requires a note explaining the reason")

    # Determine direction based on amount sign
    is_income = amount > 0
    abs_amount = abs(amount)
    direction = Direction.INCOME if is_income else Direction.EXPENSE
    credit_debit_user = CreditDebit.CREDIT if is_income else CreditDebit.DEBIT
    credit_debit_platform = CreditDebit.DEBIT if is_income else CreditDebit.CREDIT

    # 1. Update user account
    if is_income:
        user_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.USER,
            owner_id=user_id,
            amount=abs_amount,
            credit_type=credit_type,
        )
    else:
        # Deduct the credits using deduction_in_session
        # For adjustment, we don't check if the user has enough credits
        # It can be positive or negative
        user_account = await CreditAccount.deduction_in_session(
            session=session,
            owner_type=OwnerType.USER,
            owner_id=user_id,
            credit_type=credit_type,
            amount=abs_amount,
        )

    # 2. Update platform adjustment account
    if is_income:
        platform_account = await CreditAccount.deduction_in_session(
            session=session,
            owner_type=OwnerType.PLATFORM,
            owner_id=DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
            credit_type=CreditType.PERMANENT,
            amount=abs_amount,
        )
    else:
        platform_account = await CreditAccount.income_in_session(
            session=session,
            owner_type=OwnerType.PLATFORM,
            owner_id=DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT,
            amount=abs_amount,
            credit_type=CreditType.PERMANENT,
        )

    # 3. Create credit event record
    event_id = str(XID())
    event = CreditEventTable(
        id=event_id,
        event_type=EventType.ADJUSTMENT,
        upstream_type=UpstreamType.API,
        upstream_tx_id=upstream_tx_id,
        direction=direction,
        account_id=user_account.id,
        total_amount=abs_amount,
        balance_after=user_account.credits
        + user_account.free_credits
        + user_account.reward_credits,
        base_amount=abs_amount,
        base_original_amount=abs_amount,
        note=note,
    )
    session.add(event)
    await session.flush()

    # 4. Create credit transaction records
    # 4.1 User account transaction
    user_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=user_account.id,
        event_id=event_id,
        tx_type=TransactionType.ADJUSTMENT,
        credit_debit=credit_debit_user,
        change_amount=abs_amount,
    )
    session.add(user_tx)

    # 4.2 Platform adjustment account transaction
    platform_tx = CreditTransactionTable(
        id=str(XID()),
        account_id=platform_account.id,
        event_id=event_id,
        tx_type=TransactionType.ADJUSTMENT,
        credit_debit=credit_debit_platform,
        change_amount=abs_amount,
    )
    session.add(platform_tx)

    # Commit all changes
    await session.commit()

    return user_account


async def update_daily_quota(
    session: AsyncSession,
    user_id: str,
    free_quota: Optional[float] = None,
    refill_amount: Optional[float] = None,
    upstream_tx_id: str = "",
    note: str = "",
) -> CreditAccount:
    """
    Update the daily quota and refill amount of a user's credit account.

    Args:
        session: Async session to use for database operations
        user_id: ID of the user to update
        free_quota: Optional new daily quota value
        refill_amount: Optional amount to refill hourly, not exceeding free_quota
        upstream_tx_id: ID of the upstream transaction (for logging purposes)
        note: Explanation for changing the daily quota

    Returns:
        Updated user credit account
    """
    # Log the upstream_tx_id for record keeping
    logger.info(
        f"Updating quota settings for user {user_id} with upstream_tx_id: {upstream_tx_id}"
    )

    # Check that at least one parameter is provided
    if free_quota is None and refill_amount is None:
        raise ValueError("At least one of free_quota or refill_amount must be provided")

    # Get current account to check existing values and validate
    user_account = await CreditAccount.get_or_create_in_session(
        session, OwnerType.USER, user_id, for_update=True
    )

    # Use existing values if not provided
    if free_quota is None:
        free_quota = user_account.free_quota
    elif free_quota <= 0:
        raise ValueError("Daily quota must be positive")

    if refill_amount is None:
        refill_amount = user_account.refill_amount
    elif refill_amount < 0:
        raise ValueError("Refill amount cannot be negative")

    # Ensure refill_amount doesn't exceed free_quota
    if refill_amount > free_quota:
        raise ValueError("Refill amount cannot exceed daily quota")

    if not note:
        raise ValueError("Quota update requires a note explaining the reason")

    # Already got the user account above, no need to get it again

    # Update the free_quota field
    stmt = (
        update(CreditAccountTable)
        .where(
            CreditAccountTable.owner_type == OwnerType.USER,
            CreditAccountTable.owner_id == user_id,
        )
        .values(free_quota=free_quota, refill_amount=refill_amount)
        .returning(CreditAccountTable)
    )
    result = await session.scalar(stmt)
    if not result:
        raise ValueError("Failed to update user account")

    user_account = CreditAccount.model_validate(result)

    # No credit event needed for updating account settings

    # Commit all changes
    await session.commit()

    return user_account


async def list_credit_events_by_owner(
    session: AsyncSession,
    owner_type: OwnerType,
    owner_id: str,
    direction: Direction,
    cursor: Optional[str] = None,
    limit: int = 20,
    event_type: Optional[EventType] = None,
) -> Tuple[List[CreditEvent], Optional[str], bool]:
    """
    List credit events for a specific owner (user or agent) with cursor pagination.

    Args:
        session: Async database session.
        owner_type: The type of the owner (USER or AGENT).
        owner_id: The ID of the owner.
        direction: The direction of the events (INCOME or EXPENSE).
        cursor: The ID of the last event from the previous page.
        limit: Maximum number of events to return per page.
        event_type: Optional filter for specific event type.

    Returns:
        A tuple containing:
        - A list of CreditEvent models.
        - The cursor for the next page (ID of the last event in the list).
        - A boolean indicating if there are more events available.
    """
    # 1. Find the account for the owner
    account = await CreditAccount.get_in_session(session, owner_type, owner_id)
    if not account:
        # Decide if returning empty or raising error is better. Empty list seems reasonable.
        # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{owner_type.value.capitalize()} account not found")
        return [], None, False

    # 2. Build the query
    stmt = (
        select(CreditEventTable)
        .where(CreditEventTable.account_id == account.id)
        .where(CreditEventTable.direction == direction.value)
        .order_by(desc(CreditEventTable.id))
        .limit(limit + 1) # Fetch one extra to check if there are more
    )

    # 3. Apply event type filter if provided
    if event_type:
        stmt = stmt.where(CreditEventTable.event_type == event_type.value)

    # 4. Apply cursor filter if provided
    if cursor:
        stmt = stmt.where(CreditEventTable.id < cursor)

    # 5. Execute query
    result = await session.execute(stmt)
    events_data = result.scalars().all()

    # 6. Determine pagination details
    has_more = len(events_data) > limit
    events_to_return = events_data[:limit] # Slice to the requested limit

    next_cursor = events_to_return[-1].id if events_to_return else None

    # 7. Convert to Pydantic models
    events_models = [CreditEvent.model_validate(event) for event in events_to_return]

    return events_models, next_cursor, has_more
