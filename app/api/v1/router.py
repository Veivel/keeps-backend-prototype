from fastapi import APIRouter

api_router = APIRouter()

# Import and include other routers here, e.g.:
# from app.api.v1.endpoints import users, login
# api_router.include_router(login.router, tags=["login"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])

@api_router.get("/")
def root():
    return {"message": "Hello World"}
