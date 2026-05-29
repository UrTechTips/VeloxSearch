from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import service as database_service
from app.utils.dependencies_utils import validate_jwt

class RegisteredUserRequest(BaseModel):
    uid: str

class RegisterUserRequest(BaseModel):
    uid: str
    email: str
    name: str

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(validate_jwt)]
)

@router.post("/register")
def register_user(request: RegisterUserRequest):
    uid = request.uid
    email = request.email
    name = request.name
    try:
        database_service.insert_user(uid, name, email)
        return JSONResponse(content={"message": "User registered successfully", "success": True}, media_type="application/json", status_code=201)
    except Exception as e:
        return JSONResponse(content={"message": f"Error registering user: {str(e)}", "success": False}, media_type="application/json", status_code=500)

@router.post("/registered")
def registered_user(request: RegisteredUserRequest):
    uid = request.uid
    user_metadata = database_service.get_user_metadata(uid)
    if user_metadata:
        return JSONResponse(content={"message": "User is registered", "registered": True}, media_type="application/json")
    else:
        return JSONResponse(content={"message": "User not registered", "registered": False}, media_type="application/json")