from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Column, DateTime, String, func, select
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base


class AppSettingTable(Base):
    """App settings database table model."""

    __tablename__ = "app_settings"

    key = Column(
        String,
        primary_key=True,
    )
    value = Column(
        JSONB,
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


class PaymentSettings(BaseModel):
    """Payment settings model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "credit_per_doller": 200,
                "fee_platform_percentage": 0.2,
                "fee_dev_percentage": 0.1,
                "agent_whitelist_enabled": False,
                "agent_whitelist": [],
            }
        }
    )

    credit_per_doller: Annotated[
        Decimal,
        Field(default=Decimal("200"), description="Number of credits per dollar"),
    ]
    fee_platform_percentage: Annotated[
        Decimal,
        Field(default=Decimal("0.2"), description="Platform fee percentage"),
    ]
    fee_dev_percentage: Annotated[
        Decimal,
        Field(default=Decimal("0.1"), description="Developer fee percentage"),
    ]
    agent_whitelist_enabled: Annotated[
        bool,
        Field(default=False, description="Whether agent whitelist is enabled"),
    ]
    agent_whitelist: Annotated[
        List[str],
        Field(default_factory=list, description="List of whitelisted agent IDs"),
    ]

    @field_validator(
        "credit_per_doller", "fee_platform_percentage", "fee_dev_percentage"
    )
    @classmethod
    def round_decimal(cls, v: Any) -> Decimal:
        """Round decimal values to 4 decimal places."""
        if isinstance(v, Decimal):
            return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        elif isinstance(v, (int, float)):
            return Decimal(str(v)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return v


class AppSetting(BaseModel):
    """App setting model with all fields."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat(timespec="milliseconds"),
        },
    )

    key: Annotated[str, Field(description="Setting key")]
    value: Annotated[Any, Field(description="Setting value as JSON")]
    created_at: Annotated[
        datetime, Field(description="Timestamp when this setting was created")
    ]
    updated_at: Annotated[
        datetime, Field(description="Timestamp when this setting was last updated")
    ]

    @staticmethod
    async def payment(session) -> PaymentSettings:
        """Get payment settings from the database.

        Args:
            session: Database session

        Returns:
            PaymentSettings: Payment settings
        """

        # Query the database for the payment settings
        stmt = select(AppSettingTable).where(AppSettingTable.key == "payment")
        setting = await session.scalar(stmt)

        # If settings don't exist, return default settings
        if not setting:
            return PaymentSettings()

        # Convert the JSON value to PaymentSettings
        return PaymentSettings(**setting.value)
