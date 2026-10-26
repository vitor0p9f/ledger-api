from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.account import Account
from src.schemas.account import AccountCreate, AccountResponse, AccountUpdate

account_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@account_router.get("/", response_model=list[AccountResponse])
async def list_accounts(database: Annotated[Session, Depends(get_db)]):
    return database.query(Account).all()

@account_router.get("/{account_id}", response_model=AccountResponse)
async def get_account_by_id(account_id: int, database: Annotated[Session, Depends(get_db)]):
    account = database.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found!")

    return account

@account_router.post("/", response_model=AccountResponse)
async def create_account(account: AccountCreate, database: Annotated[Session, Depends(get_db)]):
    new_account = Account(**account.model_dump())

    database.add(new_account)
    database.commit()
    database.refresh(new_account)

    return new_account

@account_router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account_data: AccountUpdate, database: Annotated[Session, Depends(get_db)]):
    account = database.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found!")

    data = account_data.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(account, field, value)

    database.commit()
    database.refresh(account)

    return account

@account_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, database: Annotated[Session, Depends(get_db)]):
    account = database.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found!")

    database.delete(account)
    database.commit()
