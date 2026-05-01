from fastapi import APIRouter, Depends, Response
from app.utils.api_utils import generate_key, deactivate_key
from app.utils.dependencies_utils import get_current_user

router = APIRouter(
    prefix="/apikey",
    tags=["apikey"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/generate")
def generate_apikey(dataset_id: str, user_id: str = Depends(get_current_user)):
    api_key = generate_key(user_id, dataset_id)
    return Response(content=api_key, media_type="text/plain", status_code=201)

@router.post("/deactivate")
def deactivate_apikey(api_key: str, user_id: str = Depends(get_current_user)):
    success = deactivate_key(api_key)
    if success:
        return Response(content="API key deactivated successfully!", media_type="text/plain", status_code=200)
    else:
        return Response(content="Failed to deactivate API key!", media_type="text/plain", status_code=400)