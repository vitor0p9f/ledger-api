from src.server.routes import router
from fastapi import FastAPI
from src.server.graphql.schema import graphQL_router

app = FastAPI(title="Ledger API")
app.include_router(router)
app.include_router(graphQL_router, prefix="/graphql")