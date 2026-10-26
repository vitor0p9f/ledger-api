import strawberry
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
from typing import List, Optional

from src.database import SessionLocal
from src.models.account import Account as AccountModel


@strawberry.type
class Account:
    id: int
    name: str
    balance: float
    created_at: datetime
    updated_at: datetime


@strawberry.input
class AccountCreate:
    name: str
    balance: float

    def __post_init__(self):
        if self.balance < 0:
            raise ValueError("Balance must be greater than or equal to 0")


@strawberry.input
class AccountUpdate:
    name: str
    

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_account(self, input: AccountCreate) -> Optional[Account]:
        database = SessionLocal()

        new_account = AccountModel(name=input.name, balance=input.balance)
        database.add(new_account)
        database.commit()
        database.refresh(new_account)

        return new_account

    @strawberry.mutation
    def update_account(self, account_id: int, input: AccountUpdate) -> Optional[Account]:
        database = SessionLocal()
        account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

        if not account:
            return None

        account.name = input.name
        database.commit()
        database.refresh(account)

        return account

    @strawberry.mutation
    def delete_account(self, account_id: int) -> bool:
        database = SessionLocal()
        account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

        if not account:
            return False

        database.delete(account)
        database.commit()

        return True

@strawberry.type
class Query:
    @strawberry.field
    def accounts(self) -> List[Account]:
        database = SessionLocal()
        
        try:
            return database.query(AccountModel).all()
        finally:
            database.close()

    @strawberry.field
    def account(self, account_id: int) -> Optional[Account]:
        database = SessionLocal()

        try:
            return database.query(AccountModel).filter(AccountModel.id == account_id).first()
        finally:
            database.close()


account_schema = strawberry.Schema(Query, Mutation)
graphql_account_router = GraphQLRouter(account_schema)