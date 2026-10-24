from fastapi import status, APIRouter

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"message": "API is healthy and running!"}