from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from decimal import Decimal


class AccountCreate(BaseModel):
    name: str
    balance: Decimal = Field(
        default=Decimal("0.0"),
        decimal_places=2
    )

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("Balance must be greater than or equal to 0")
        
        return value


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime


class AccountUpdate(BaseModel):
    name: str | None = None