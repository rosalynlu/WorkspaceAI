from fastapi import APIRouter

router = APIRouter()

@router.get("/login")
def login():
    return {"message": "OAuth login not implemented yet"}