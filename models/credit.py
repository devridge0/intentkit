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
    """Credit type is used in db column names, do not change it."""

    DAILY = "daily_credits"
    REWARD = "reward_credits"
    PERMANENT = "credits"


class OwnerType(str, Enum):
    """Type of credit account owner."""

    USER = "user"
    AGENT = "agent"
    PLATFORM = "platform"


# Platform virtual account ids, they are used for transaction balance tracing
DEFAULT_PLATFORM_ACCOUNT_RECHARGE = "platform_recharge"
DEFAULT_PLATFORM_ACCOUNT_DAILY_RESET = "platform_daily_reset"
DEFAULT_PLATFORM_ACCOUNT_ADJUSTMENT = "platform_adjustment"
DEFAULT_PLATFORM_ACCOUNT_REWARD = "platform_reward"
DEFAULT_PLATFORM_ACCOUNT_REFUND = "platform_refund"
DEFAULT_PLATFORM_ACCOUNT_FEE = "platform_fee"
DEFAULT_PLATFORM_ACCOUNT_DEV = "platform_dev"


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
        if owner_type != OwnerType.USER:
            # only users have daily quota
            daily_quota = 0.0
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


class EventType(str, Enum):
    """Type of credit event."""

    MESSAGE = "message"
    SKILL_CALL = "skill_call"
    RECHARGE = "recharge"
    REWARD = "reward"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    DAILY_RESET = "daily_reset"


class UpstreamType(str, Enum):
    """Type of upstream transaction."""

    API = "api"
    SCHEDULER = "scheduler"
    EXECUTOR = "executor"


class Direction(str, Enum):
    """Direction of credit flow."""

    INCOME = "income"
    EXPENSE = "expense"


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
    upstream_type = Column(
        String,
        nullable=False,
    )
    upstream_tx_id = Column(
        String,
        nullable=False,
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
    base_llm_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    base_skill_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    fee_platform_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    fee_dev_account = Column(
        String,
        nullable=True,
    )
    fee_dev_amount = Column(
        Float,
        default=0.0,
        nullable=True,
    )
    fee_agent_account = Column(
        String,
        nullable=True,
    )
    fee_agent_amount = Column(
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
    event_type: Annotated[EventType, Field(description="Type of the event")]
    upstream_type: Annotated[
        UpstreamType, Field(description="Type of upstream transaction")
    ]
    upstream_tx_id: Annotated[str, Field(description="Upstream transaction ID if any")]
    start_message_id: Annotated[
        Optional[str],
        Field(None, description="ID of the starting message if applicable"),
    ]
    message_id: Annotated[
        Optional[str], Field(None, description="ID of the message if applicable")
    ]
    skill_call_id: Annotated[
        Optional[str], Field(None, description="ID of the skill call if applicable")
    ]
    direction: Annotated[Direction, Field(description="Direction of the credit flow")]
    from_account: Annotated[
        Optional[str], Field(None, description="Account ID from which credits flow")
    ]
    total_amount: Annotated[
        float, Field(default=0.0, description="Total amount of credits involved")
    ]
    base_llm_amount: Annotated[
        Optional[float], Field(default=0.0, description="Base LLM cost amount")
    ]
    base_skill_amount: Annotated[
        Optional[float], Field(default=0.0, description="Base skill cost amount")
    ]
    fee_platform_amount: Annotated[
        Optional[float], Field(default=0.0, description="Platform fee amount")
    ]
    fee_dev_account: Annotated[
        Optional[str], Field(None, description="Developer account ID receiving fee")
    ]
    fee_dev_amount: Annotated[
        Optional[float], Field(default=0.0, description="Developer fee amount")
    ]
    fee_agent_account: Annotated[
        Optional[str], Field(None, description="Agent account ID receiving fee")
    ]
    fee_agent_amount: Annotated[
        Optional[float], Field(default=0.0, description="Agent fee amount")
    ]
    note: Annotated[Optional[str], Field(None, description="Additional notes")]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this event was created")
    ]


class TransactionType(str, Enum):
    """Type of credit transaction."""

    PAY = "pay"
    RECEIVE_BASE_LLM = "receive_base_llm"
    RECEIVE_BASE_SKILL = "receive_base_skill"
    RECEIVE_FEE_DEV = "receive_fee_dev"
    RECEIVE_FEE_AGENT = "receive_fee_agent"
    RECEIVE_FEE_PLATFORM = "receive_fee_platform"
    RECHARGE = "recharge"
    REWARD = "reward"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    DAILY_RESET = "daily_reset"


class CreditDebit(str, Enum):
    """Credit or debit transaction."""

    CREDIT = "credit"
    DEBIT = "debit"


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


class PriceType(str, Enum):
    """Type of credit price."""

    SKILL_CALL = "skill_call"


DEFAULT_SKILL_CALL_PRICE = 10.0
DEFAULT_SKILL_CALL_SELF_KEY_PRICE = 5.0


class CreditPriceTable(Base):
    """Credit price database table model.

    Stores price information for different types of services.
    """

    __tablename__ = "credit_prices"

    id = Column(
        String,
        primary_key=True,
    )
    price_type = Column(
        String,
        nullable=False,
    )
    price_name = Column(
        String,
        nullable=False,
    )
    price = Column(
        Float,
        default=0.0,
        nullable=False,
    )
    self_key_price = Column(
        Float,
        default=0.0,
        nullable=False,
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


class CreditPrice(BaseModel):
    """Credit price model with all fields."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat(timespec="milliseconds")},
    )

    id: Annotated[
        str,
        Field(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the credit price",
        ),
    ]
    price_type: Annotated[
        PriceType, Field(description="Type of the price (agent or skill_call)")
    ]
    price_name: Annotated[str, Field(description="Name of the price")]
    price: Annotated[float, Field(default=0.0, description="Standard price")]
    self_key_price: Annotated[
        float, Field(default=0.0, description="Price for self-key usage")
    ]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this price was created")
    ]
    updated_at: Annotated[
        datetime, Field(description="Timestamp when this price was last updated")
    ]


class CreditPriceLogTable(Base):
    """Credit price log database table model.

    Records history of price changes.
    """

    __tablename__ = "credit_price_logs"

    id = Column(
        String,
        primary_key=True,
    )
    price_id = Column(
        String,
        nullable=False,
    )
    old_price = Column(
        Float,
        nullable=False,
    )
    old_self_key_price = Column(
        Float,
        nullable=False,
    )
    new_price = Column(
        Float,
        nullable=False,
    )
    new_self_key_price = Column(
        Float,
        nullable=False,
    )
    modified_by = Column(
        String,
        nullable=False,
    )
    modified_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CreditPriceLog(BaseModel):
    """Credit price log model with all fields."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat(timespec="milliseconds")},
    )

    id: Annotated[
        str,
        Field(
            default_factory=lambda: str(XID()),
            description="Unique identifier for the log entry",
        ),
    ]
    price_id: Annotated[str, Field(description="ID of the price that was modified")]
    old_price: Annotated[float, Field(description="Previous standard price")]
    old_self_key_price: Annotated[float, Field(description="Previous self-key price")]
    new_price: Annotated[float, Field(description="New standard price")]
    new_self_key_price: Annotated[float, Field(description="New self-key price")]
    modified_by: Annotated[
        str, Field(description="ID of the user who made the modification")
    ]
    modified_at: Annotated[
        datetime, Field(description="Timestamp when the modification was made")
    ]
