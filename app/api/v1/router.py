from fastapi import APIRouter

api_router = APIRouter()

from app.api.v1 import auth, pairings

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(pairings.router, prefix="/pairings", tags=["pairings"])

@api_router.get("/")
def root():
    return {"message": "Hello World"}
