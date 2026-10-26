from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.account import Account as AccountModel
from src.models.enums import TransactionType
from src.models.transaction import Transaction as TransactionModel
from src.schemas.transaction import Transaction as TransactionResponse
from src.schemas.transaction import TransactionCreate

transaction_router = APIRouter(prefix="/transactions", tags=["Transactions"])

@transaction_router.get("/", response_model=list[TransactionResponse])
def list_transactions(database: Annotated[Session, Depends(get_db)]):
    return database.query(TransactionModel).all()

@transaction_router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, database: Annotated[Session, Depends(get_db)]):
    transaction = database.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found!")

    return transaction

@transaction_router.get("/account/{account_id}", response_model=list[TransactionResponse])
def list_account_transactions(account_id: int, database: Annotated[Session, Depends(get_db)]):
    account = database.query(AccountModel).filter(AccountModel.id == account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found!")

    return database.query(TransactionModel).filter(TransactionModel.account_id == account_id).all()

@transaction_router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(transaction_data: TransactionCreate, database: Annotated[Session, Depends(get_db)]):
    account = database.query(AccountModel).filter(AccountModel.id == transaction_data.account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found!")

    if transaction_data.transaction_type == TransactionType.INCOME:
        database.execute(
            update(AccountModel)
            .where(AccountModel.id == account.id)
            .values(balance=AccountModel.balance + transaction_data.amount)
        )
    else:
        result = cast(
            "CursorResult[Any]",
            database.execute(
                update(AccountModel)
                .where(
                    AccountModel.id == account.id,
                    AccountModel.balance >= transaction_data.amount,
                )
                .values(balance=AccountModel.balance - transaction_data.amount)
            ),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient funds!")

    new_transaction = TransactionModel(**transaction_data.model_dump())

    database.add(new_transaction)
    database.commit()
    database.refresh(new_transaction)

    return new_transaction
