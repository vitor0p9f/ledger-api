from enum import Enum


class TransactionType(str, Enum):
    INCOME = "Income"
    OUTCOME = "Outcome"
