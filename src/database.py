import os
from dotenv import load_dotenv
from src.models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ledger:ledger_secret@localhost:5432/ledger_db",
)

connect_args = {"check_same_thread": False} if str(DATABASE_URL).startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
