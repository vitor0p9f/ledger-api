from datetime import datetime
from decimal import Decimal

import strawberry
from strawberry.fastapi import GraphQLRouter

from src.database import SessionLocal
from src.models.account import Account as AccountModel


@strawberry.type
class Account:
    id: int
    name: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, account: AccountModel) -> "Account":
        return cls(
            id=account.id,
            name=account.name,
            balance=account.balance,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )


@strawberry.input
class AccountCreate:
    name: str
    balance: Decimal

    def __post_init__(self):
        if self.balance < Decimal(0):
            raise ValueError("Balance must be greater than or equal to 0")


@strawberry.input
class AccountUpdate:
    name: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_account(self, input: AccountCreate) -> Account:
        database = SessionLocal()

        try:
            new_account = AccountModel(name=input.name, balance=input.balance)
            database.add(new_account)
            database.commit()
            database.refresh(new_account)

            return Account.from_model(new_account)
        except Exception as _:
            database.rollback()
            raise
        finally:
            database.close()

    @strawberry.mutation
    def update_account(self, account_id: int, input: AccountUpdate) -> Account | None:
        database = SessionLocal()

        try:
            account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

            if not account:
                return None

            account.name = input.name
            database.commit()
            database.refresh(account)

            return Account.from_model(account)
        except Exception as _:
            database.rollback()
            raise
        finally:
            database.close()

    @strawberry.mutation
    def delete_account(self, account_id: int) -> bool:
        database = SessionLocal()

        try:
            account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

            if not account:
                return False

            if account.transactions:
                raise ValueError("Account has transactions!")

            database.delete(account)
            database.commit()

            return True
        except Exception as _:
            database.rollback()
            raise
        finally:
            database.close()

@strawberry.type
class Query:
    @strawberry.field
    def accounts(self) -> list[Account]:
        database = SessionLocal()

        try:
            return [Account.from_model(account) for account in database.query(AccountModel).all()]
        finally:
            database.close()

    @strawberry.field
    def account(self, account_id: int) -> Account | None:
        database = SessionLocal()

        try:
            account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

            if not account:
                return None

            return Account.from_model(account)
        finally:
            database.close()


account_schema = strawberry.Schema(Query, Mutation)
graphql_account_router = GraphQLRouter(account_schema)
