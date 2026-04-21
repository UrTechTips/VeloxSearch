from fastapi import APIRouter, Response
from app.utils.api_utils import generate_key, deactivate_key

router = APIRouter(
    prefix="/apikey",
    tags=["apikey"]
)

@router.post("/generate")
def generate_apikey(owner_id: str, dataset_id: str):
    api_key = generate_key(owner_id, dataset_id)
    return Response(content=api_key, media_type="text/plain", status_code=201)

@router.post("/deactivate")
def deactivate_apikey(api_key: str):
    success = deactivate_key(api_key)
    if success:
        return Response(content="API key deactivated successfully!", media_type="text/plain", status_code=200)
    else:
        return Response(content="Failed to deactivate API key!", media_type="text/plain", status_code=400)