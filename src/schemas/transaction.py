
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.enums import TransactionType


class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    description: str
    amount: Decimal
    account_id: int
    transaction_type: TransactionType

    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be positive!")
        return value

class TransactionCreate(BaseModel):
    date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    description: str = Field(default="")
    amount: Decimal
    account_id: int
    transaction_type: TransactionType

    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("Amount must be positive!")
        return value
