from fastapi import FastAPI
from src.server.routers.health import health_router
from src.server.routers.account import account_router
from src.server.graphql.account import graphql_account_router
from src.server.graphql.health import graphql_health_router

app = FastAPI(title="Ledger API")
app.include_router(health_router)
app.include_router(account_router)
app.include_router(graphql_account_router, prefix="/graphql/account")
app.include_router(graphql_health_router, prefix="/graphql")