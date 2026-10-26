from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.enums import TransactionType

if TYPE_CHECKING:
    from src.models.account import Account


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(
            TransactionType,
            values_callable=lambda enum: [member.value for member in enum],
            name="transaction_type",
            create_constraint=True,
        ),
        nullable=False,
    )
    account: Mapped["Account"] = relationship(back_populates="transactions")
