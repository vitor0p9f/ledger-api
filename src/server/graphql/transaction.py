from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import strawberry
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from strawberry.fastapi import GraphQLRouter

from src.database import SessionLocal
from src.models.account import Account as AccountModel
from src.models.enums import TransactionType
from src.models.transaction import Transaction as TransactionModel


@strawberry.type
class Transaction:
    id: int
    date: datetime
    description: str
    amount: Decimal
    account_id: int
    transaction_type: TransactionType

    @classmethod
    def from_model(cls, transaction: TransactionModel) -> "Transaction":
        return cls(
            id=transaction.id,
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            account_id=transaction.account_id,
            transaction_type=transaction.transaction_type,
        )


@strawberry.input
class TransactionCreate:
    date: datetime
    description: str
    amount: Decimal
    account_id: int
    transaction_type: TransactionType

    def __post_init__(self):
        if self.amount <= Decimal(0):
            raise ValueError("Amount must be greater than 0")


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_transaction(self, input: TransactionCreate) -> Transaction | None:
        database = SessionLocal()

        try:

            new_transaction = TransactionModel(
                date=input.date,
                description=input.description,
                amount=input.amount,
                account_id=input.account_id,
                transaction_type=input.transaction_type.value,
            )

            account = database.query(AccountModel).filter(AccountModel.id == input.account_id).first()

            if account is None:
                raise ValueError("Account not found!")

            if input.transaction_type == TransactionType.INCOME:
                result = cast(
                    "CursorResult[Any]",
                    database.execute(
                        update(AccountModel)
                        .where(AccountModel.id == input.account_id)
                        .values(balance=AccountModel.balance + input.amount)
                    ),
                )
            else:
                result = cast(
                    "CursorResult[Any]",
                    database.execute(
                        update(AccountModel)
                        .where(
                            AccountModel.id == input.account_id,
                            AccountModel.balance >= input.amount,
                        )
                        .values(balance=AccountModel.balance - input.amount)
                    ),
                )

                if result.rowcount == 0:
                    raise ValueError("Insufficient funds!")

            database.add(new_transaction)
            database.commit()
            database.refresh(new_transaction)
            database.refresh(account)

            return Transaction.from_model(new_transaction)
        except Exception as _:
            database.rollback()
            raise
        finally:
            database.close()

@strawberry.type
class Query:
    @strawberry.field
    def transactions(self) -> list[Transaction]:
        database = SessionLocal()

        try:
            return [Transaction.from_model(transaction) for transaction in database.query(TransactionModel).all()]
        finally:
            database.close()

    @strawberry.field
    def transaction(self, id: int) -> Transaction | None:
        database = SessionLocal()

        try:
            transaction = database.query(TransactionModel).filter(TransactionModel.id == id).first()

            if not transaction:
                return None

            return Transaction.from_model(transaction)
        finally:
            database.close()

    @strawberry.field
    def transactions_by_account(self, account_id: int) -> list[Transaction]:
        database = SessionLocal()

        try:
            account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

            if not account:
                raise ValueError("Account not found!")

            transactions = (
                database.query(TransactionModel)
                .filter(TransactionModel.account_id == account_id)
                .all()
            )

            return [Transaction.from_model(transaction) for transaction in transactions]
        finally:
            database.close()

transaction_schema = strawberry.Schema(Query, Mutation)
graphql_transaction_router = GraphQLRouter(transaction_schema)
