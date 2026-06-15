from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from app.utils.api_utils import generate_key, deactivate_key, list_keys
from app.utils.dependencies_utils import get_current_user

router = APIRouter(
    prefix="/apikey",
    tags=["apikey"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/generate") 
def generate_apikey(name: str, dataset_id: str, user_id: str = Depends(get_current_user)):
    print("Generating API key for user_id:", user_id, "dataset_id:", dataset_id, "name:", name)
    api_key = generate_key(user_id, dataset_id, name)
    return JSONResponse(content={"message": "API key generated successfully!", "api_key": api_key, "success": True}, media_type="text/plain", status_code=201)

@router.post("/deactivate")
def deactivate_apikey(api_key: str, user_id: str = Depends(get_current_user)):
    success = deactivate_key(api_key, user_id)
    if success:
        return JSONResponse(content={"message": "API key deactivated successfully!", "success": True}, media_type="text/plain", status_code=200)
    else:
        return JSONResponse(content={"message": "Failed to deactivate API key!", "success": False}, media_type="text/plain", status_code=400)

@router.get("/list")
def list_apikeys(dataset_id: str, user_id: str = Depends(get_current_user)):
    try:
        keys = list_keys(dataset_id, user_id)
        return JSONResponse(content={"api_keys": keys, "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": f"Failed to list API keys: {str(e)}", "success": False}, media_type="application/json", status_code=400)