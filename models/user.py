from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Index, Integer, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base
from models.db import get_session


class UserTable(Base):
    """User database table model."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_x_username", "x_username"),
        Index("ix_users_telegram_username", "telegram_username"),
    )

    id = Column(
        String,
        primary_key=True,
    )
    nft_count = Column(
        Integer,
        default=0,
        nullable=False,
    )
    email = Column(
        String,
        nullable=True,
    )
    x_username = Column(
        String,
        nullable=True,
    )
    github_username = Column(
        String,
        nullable=True,
    )
    telegram_username = Column(
        String,
        nullable=True,
    )
    extra = Column(
        JSONB,
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


class UserUpdate(BaseModel):
    """User update model without id and timestamps."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(timespec="milliseconds"),
        },
    )

    nft_count: Annotated[
        int, Field(default=0, description="Number of NFTs owned by the user")
    ]
    email: Annotated[Optional[str], Field(None, description="User's email address")]
    x_username: Annotated[
        Optional[str], Field(None, description="User's X (Twitter) username")
    ]
    github_username: Annotated[
        Optional[str], Field(None, description="User's GitHub username")
    ]
    telegram_username: Annotated[
        Optional[str], Field(None, description="User's Telegram username")
    ]
    extra: Annotated[
        Optional[dict], Field(None, description="Additional user information")
    ]

    async def patch(self, id: str) -> "User":
        """Update only the provided fields of a user in the database.
        If the user doesn't exist, create a new one with the provided ID and fields.

        Args:
            id: ID of the user to update or create

        Returns:
            Updated or newly created User model
        """
        async with get_session() as db:
            db_user = await db.get(UserTable, id)
            if not db_user:
                # Create new user if it doesn't exist
                db_user = UserTable(id=id)
                db.add(db_user)

            # Update only the fields that were provided
            for key, value in self.model_dump(exclude_unset=True).items():
                setattr(db_user, key, value)

            await db.commit()
            await db.refresh(db_user)
            return User.model_validate(db_user)

    async def put(self, id: str) -> "User":
        """Replace all fields of a user in the database with the provided values.
        If the user doesn't exist, create a new one with the provided ID and fields.

        Args:
            id: ID of the user to update or create

        Returns:
            Updated or newly created User model
        """
        async with get_session() as db:
            db_user = await db.get(UserTable, id)
            if not db_user:
                # Create new user if it doesn't exist
                db_user = UserTable(id=id)
                db.add(db_user)

            # Replace all fields with the provided values
            for key, value in self.model_dump().items():
                setattr(db_user, key, value)

            await db.commit()
            await db.refresh(db_user)
            return User.model_validate(db_user)


class User(UserUpdate):
    """User model with all fields including id and timestamps."""

    id: Annotated[
        str,
        Field(description="Unique identifier for the user"),
    ]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this user was created")
    ]
    updated_at: Annotated[
        datetime, Field(description="Timestamp when this user was last updated")
    ]

    @classmethod
    async def get(cls, user_id: str) -> Optional["User"]:
        """Get a user by ID.

        Args:
            user_id: ID of the user to get

        Returns:
            User model or None if not found
        """
        async with get_session() as session:
            return await cls.get_in_session(session, user_id)

    @classmethod
    async def get_in_session(
        cls, session: AsyncSession, user_id: str
    ) -> Optional["User"]:
        """Get a user by ID using the provided session.

        Args:
            session: Database session
            user_id: ID of the user to get

        Returns:
            User model or None if not found
        """
        result = await session.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if user is None:
            return None
        return cls.model_validate(user)
