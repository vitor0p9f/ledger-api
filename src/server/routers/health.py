from fastapi import APIRouter, status

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("/", status_code=status.HTTP_200_OK)
async def health():
    return {"message": "API is healthy and running!"}
