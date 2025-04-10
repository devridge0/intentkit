from typing import Optional

from epyxid import XID
from sqlalchemy.ext.asyncio import AsyncSession

from models.credit import (
    DEFAULT_PLATFORM_ACCOUNT_RECHARGE,
    CreditAccount,
    CreditDebit,
    CreditEventTable,
    CreditTransactionTable,
    CreditType,
    Direction,
    EventType,
    OwnerType,
    TransactionType,
    UpstreamType,
)


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
