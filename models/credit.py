from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional

from epyxid import XID
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    String,
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base
from models.db import get_session


class CreditType(str, Enum):
    DAILY = "daily_credits"
    REWARD = "reward_credits"
    PERMANENT = "credits"


class OwnerType(str, Enum):
    """Type of credit account owner."""

    USER = "user"
    AGENT = "agent"
    SKILL = "skill"


class EventType(str, Enum):
    """Type of credit event."""

    MESSAGE = "message"
    SKILL_CALL = "skill_call"
    TOPUP = "topup"
    REWARD = "reward"
    REFUND = "refund"


class Direction(str, Enum):
    """Direction of credit flow."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    """Type of credit transaction."""

    MESSAGE = "message"
    SKILL_CALL = "skill_call"
    TOPUP = "topup"
    REWARD = "reward"
    REFUND = "refund"
    DAILY_RESET = "daily_reset"


class CreditDebit(str, Enum):
    """Credit or debit transaction."""

    CREDIT = "credit"
    DEBIT = "debit"


class CreditAccountTable(Base):
    """Credit account database table model."""

    __tablename__ = "credit_accounts"
    __table_args__ = (Index("ix_credit_accounts_owner", "owner_type", "owner_id"),)

    id = Column(
        String,
        primary_key=True,
    )
    owner_type = Column(
        String,
        nullable=False,
    )
    owner_id = Column(
        String,
        nullable=False,
    )
    daily_quota = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    daily_credits = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    reward_credits = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    credits = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    income_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    expense_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CreditEventTable(Base):
    """Credit events database table model.

    Records business events like message processing, skill calls, etc.
    """

    __tablename__ = "credit_events"

    id = Column(
        String,
        primary_key=True,
    )
    event_type = Column(
        String,
        nullable=False,
    )
    upstream_tx_id = Column(
        String,
        nullable=True,
    )
    start_message_id = Column(
        String,
        nullable=True,
    )
    message_id = Column(
        String,
        nullable=True,
    )
    skill_call_id = Column(
        String,
        nullable=True,
    )
    direction = Column(
        String,
        nullable=False,
    )
    from_account = Column(
        String,
        nullable=True,
    )
    total_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    to_account = Column(
        String,
        nullable=True,
    )
    to_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    agent_account = Column(
        String,
        nullable=True,
    )
    agent_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    owner_account = Column(
        String,
        nullable=True,
    )
    owner_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    note = Column(
        String,
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CreditTransactionTable(Base):
    """Credit transactions database table model.

    Records the flow of credits in and out of accounts.
    """

    __tablename__ = "credit_transactions"
    __table_args__ = (Index("ix_credit_transactions_account", "account_id"),)

    id = Column(
        String,
        primary_key=True,
    )
    account_id = Column(
        String,
        nullable=False,
    )
    event_id = Column(
        String,
        nullable=False,
    )
    tx_type = Column(
        String,
        nullable=False,
    )
    credit_debit = Column(
        String,
        nullable=False,
    )
    change_amount = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CreditAccount(BaseModel):
    """Credit account model with all fields."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat(timespec="milliseconds")},
    )

    id: Annotated[
        str,
        Field(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the credit account",
        ),
    ]
    owner_type: Annotated[OwnerType, Field(description="Type of the account owner")]
    owner_id: Annotated[str, Field(description="ID of the account owner")]
    daily_quota: Annotated[
        float, Field(default=0.0, description="Daily credit quota that resets each day")
    ]
    daily_credits: Annotated[
        float, Field(default=0.0, description="Current available daily credits")
    ]
    reward_credits: Annotated[
        float, Field(default=0.0, description="Reward credits earned through rewards")
    ]
    credits: Annotated[
        float, Field(default=0.0, description="Credits added through top-ups")
    ]
    income_at: Annotated[
        Optional[datetime],
        Field(None, description="Timestamp of the last income transaction"),
    ]
    expense_at: Annotated[
        Optional[datetime],
        Field(None, description="Timestamp of the last expense transaction"),
    ]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this account was created")
    ]
    updated_at: Annotated[
        datetime, Field(description="Timestamp when this account was last updated")
    ]

    @classmethod
    async def get_in_session(
        cls, session: AsyncSession, owner_type: OwnerType, owner_id: str
    ) -> "CreditAccount":
        """Get a credit account by owner type and ID.

        Args:
            session: Async session to use for database queries
            owner_type: Type of the owner
            owner_id: ID of the owner

        Returns:
            CreditAccount if found, None otherwise
        """
        stmt = select(CreditAccountTable).where(
            CreditAccountTable.owner_type == owner_type,
            CreditAccountTable.owner_id == owner_id,
        )
        result = await session.scalar(stmt)
        if not result:
            account = await cls.create_in_session(session, owner_type, owner_id)
        else:
            account = cls.model_validate(result)

        return account

    @classmethod
    async def get(cls, owner_type: OwnerType, owner_id: str) -> "CreditAccount":
        """Get a credit account by owner type and ID.

        Args:
            owner_type: Type of the owner
            owner_id: ID of the owner

        Returns:
            CreditAccount if found, None otherwise
        """
        async with get_session() as session:
            return await cls.get_in_session(session, owner_type, owner_id)

    @classmethod
    async def get_by_user(cls, user_id: str) -> "CreditAccount":
        return await cls.get(OwnerType.USER, user_id)

    @classmethod
    async def expense_in_session(
        cls, session: AsyncSession, owner_type: OwnerType, owner_id: str, amount: float
    ) -> None:
        # check first
        account = await cls.get_in_session(session, owner_type, owner_id)
        if (
            amount > account.daily_credits
            and amount > account.reward_credits
            and amount > account.credits
        ):
            raise HTTPException(status_code=400, detail="Not enough credits")

        # expense
        field = "credits"
        if amount <= account.daily_credits:
            field = "daily_credits"
        elif amount <= account.reward_credits:
            field = "reward_credits"

        stmt = (
            update(CreditAccountTable)
            .where(
                CreditAccountTable.owner_type == owner_type,
                CreditAccountTable.owner_id == owner_id,
            )
            .values({field: CreditAccountTable.c[field] - amount})
        )
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def expense(cls, owner_type: OwnerType, owner_id: str, amount: float) -> None:
        async with get_session() as session:
            await cls.expense_in_session(session, owner_type, owner_id, amount)

    @classmethod
    async def expense_by_user(cls, user_id: str, amount: float) -> None:
        await cls.expense(OwnerType.USER, user_id, amount)

    @classmethod
    async def income_in_session(
        cls,
        session: AsyncSession,
        owner_type: OwnerType,
        owner_id: str,
        amount: float,
        credit_type: CreditType,
    ) -> None:
        # income
        stmt = (
            update(CreditAccountTable)
            .where(
                CreditAccountTable.owner_type == owner_type,
                CreditAccountTable.owner_id == owner_id,
            )
            .values(
                {credit_type.value: CreditAccountTable.c[credit_type.value] + amount}
            )
        )
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def create_in_session(
        cls,
        session: AsyncSession,
        owner_type: OwnerType,
        owner_id: str,
        daily_quota: float = 100.0,
    ) -> "CreditAccount":
        """Get an existing credit account or create a new one if it doesn't exist.

        This is useful for silent creation of accounts when they're first accessed.

        Args:
            session: Async session to use for database queries
            owner_type: Type of the owner
            owner_id: ID of the owner
            daily_quota: Daily quota for a new account if created

        Returns:
            CreditAccount: The existing or newly created credit account
        """
        record = CreditAccountTable(
            id=str(XID()),
            owner_type=owner_type,
            owner_id=owner_id,
            daily_quota=daily_quota,
            daily_credits=daily_quota,
            reward_credits=0.0,
            credits=0.0,
            income_at=None,
            expense_at=None,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return cls.model_validate(record)


class CreditEvent(BaseModel):
    """Credit event model with all fields."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat(timespec="milliseconds")},
    )

    id: Annotated[
        str,
        Field(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the credit event",
        ),
    ]
    event_type: Annotated[EventType, Field(description="Type of the credit event")]
    upstream_tx_id: Annotated[
        Optional[str], Field(None, description="ID of the upstream transaction")
    ]
    start_message_id: Annotated[
        Optional[str], Field(None, description="ID of the starting message")
    ]
    message_id: Annotated[
        Optional[str], Field(None, description="ID of the associated message")
    ]
    skill_call_id: Annotated[
        Optional[str], Field(None, description="ID of the associated skill call")
    ]
    direction: Annotated[Direction, Field(description="Direction of credit flow")]
    from_account: Annotated[Optional[str], Field(None, description="Source account ID")]
    total_amount: Annotated[
        float, Field(default=0.0, description="Total amount of credits involved")
    ]
    to_account: Annotated[
        Optional[str], Field(None, description="Destination account ID")
    ]
    to_amount: Annotated[
        Optional[float], Field(None, description="Amount sent to destination account")
    ]
    agent_account: Annotated[
        Optional[str], Field(None, description="Agent's account ID")
    ]
    agent_amount: Annotated[
        Optional[float], Field(None, description="Amount sent to agent's account")
    ]
    owner_account: Annotated[
        Optional[str], Field(None, description="Owner's account ID")
    ]
    owner_amount: Annotated[
        Optional[float], Field(None, description="Amount sent to owner's account")
    ]
    note: Annotated[
        Optional[str], Field(None, description="Additional notes about the event")
    ]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this event was created")
    ]


class CreditTransaction(BaseModel):
    """Credit transaction model with all fields."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat(timespec="milliseconds")},
    )

    id: Annotated[
        str,
        Field(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the credit transaction",
        ),
    ]
    account_id: Annotated[
        str, Field(description="ID of the account this transaction belongs to")
    ]
    event_id: Annotated[
        str, Field(description="ID of the event that triggered this transaction")
    ]
    tx_type: Annotated[TransactionType, Field(description="Type of the transaction")]
    credit_debit: Annotated[
        CreditDebit, Field(description="Whether this is a credit or debit transaction")
    ]
    change_amount: Annotated[
        float, Field(default=0.0, description="Amount of credits changed")
    ]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this transaction was created")
    ]
