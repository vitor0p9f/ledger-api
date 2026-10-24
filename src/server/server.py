from src.server.routes import router
from fastapi import FastAPI

app = FastAPI(title="Ledger API")
app.include_router(router)