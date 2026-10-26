# Ledger API

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white)
![GraphQL](https://img.shields.io/badge/GraphQL-Strawberry-E10098?logo=graphql&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)

A small accounts and transactions API, built as a **study project**.

The main goal was to practice building the same features twice — once with a
REST API and once with GraphQL — on top of the same database, and to see how
both approaches compare in day-to-day code.

## What it does

- Create, read, update and delete accounts
- Register income and outcome transactions
- Keep the account balance in sync with each transaction
- Reject outcome transactions when the balance is not enough
- Expose everything through both REST and GraphQL

## Tech stack

- **Python** + **FastAPI** for the HTTP layer
- **Strawberry** for GraphQL
- **SQLAlchemy** as the ORM
- **PostgreSQL** as the database
- **Docker Compose** to run the API and the database
- **pytest** for tests

## Getting started

### With Docker

Create a `.env` file with the database settings:

```env
POSTGRES_USER=ledger
POSTGRES_PASSWORD=ledger_secret
POSTGRES_DB=ledger_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://ledger:ledger_secret@localhost:5432/ledger_db
```

Then start everything:

```bash
docker compose up --build
```

The API runs at `http://localhost:8000` and the interactive docs are at
`http://localhost:8000/docs`.

### Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.server.server:app --reload
```

You still need a PostgreSQL instance running and a `DATABASE_URL` pointing to it.

## Endpoints

### REST

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health/` | Health check |
| `GET` | `/accounts/` | List accounts |
| `POST` | `/accounts/` | Create an account |
| `GET` | `/accounts/{account_id}` | Get one account |
| `PATCH` | `/accounts/{account_id}` | Update the account name |
| `DELETE` | `/accounts/{account_id}` | Delete an account |
| `GET` | `/transactions/` | List transactions |
| `POST` | `/transactions/` | Create a transaction |
| `GET` | `/transactions/{transaction_id}` | Get one transaction |
| `GET` | `/transactions/account/{account_id}` | List an account's transactions |

### GraphQL

| Path | Exposes |
| --- | --- |
| `/graphql` | `health` |
| `/graphql/account` | `accounts`, `account`, `createAccount`, `updateAccount`, `deleteAccount` |
| `/graphql/transaction` | `transactions`, `transaction`, `transactionsByAccount`, `createTransaction` |

Both GraphQL endpoints accept `POST` with a JSON body containing `query` and
`variables`.

## Tests

```bash
pytest
```

The tests use the same `DATABASE_URL` configured for the app, so point it to a
database you don't mind writing to.

## Project layout

```
src/
├── models/      database models
├── schemas/     request/response schemas
├── server/
│   ├── routers/ REST endpoints
│   └── graphql/ GraphQL endpoints
└── tests/       REST and GraphQL tests
```

## Notes

This is a learning project, not production software. There is no
authentication, no migrations and no pagination — the focus was on the API
design and on keeping the REST and GraphQL sides consistent.

## Tags

`python` `fastapi` `graphql` `strawberry` `sqlalchemy` `postgresql` `docker` `pytest` `study-project` `rest-api`
