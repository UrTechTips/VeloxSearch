import uuid
import json
from typing import Dict, List
from pydantic import BaseModel
from jsonschema import validate
from app.services.dataset import Dataset
from app.db import service as database_service
from app.utils.dependencies_utils import get_current_user
from fastapi import APIRouter, HTTPException, UploadFile, File, Response, Form, Depends

class DatasetCreateRequest(BaseModel):
    database_name: str
    description: str = None

class ConfigUploadRequest(BaseModel):
    id: str
    config: str # JSON STRING

config_schema = {
    "type": "object",
    "properties": {
        "searchable_fields": { "type": "array", "items": {"type": "string"} },
        "vector_terms": { "type": "array", "items": {"type": "string"} },
        "length": { "type": "integer" },
        "id_field": { "type": "string" }
    },
    "required": ["searchable_fields", "vector_terms", "length", "id_field"]
}

router = APIRouter(
    prefix="/dataset",
    tags=["dataset"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def read_dataset_get():
    return {"message": "Welcome to datasets route"}

@router.get("/list")
def read_dataset(user_id: str = Depends(get_current_user)):
    try:
        datasets = database_service.list_datasets(user_id)
        return {"datasets": datasets, "success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to list datasets! Error: {e}", "success": False})

@router.post("/create")
def create_dataset(request: DatasetCreateRequest, user_id: str = Depends(get_current_user)):
    if request.description == "":
        request.description = "No description provided."

    dataset_id = uuid.uuid5(uuid.NAMESPACE_X500, f"{user_id}_{request.database_name}").hex
    result = database_service.insert_dataset(dataset_id, user_id, request.database_name, request.description)
    if (result):
        return Response(content=json.dumps({"message": "Dataset created successfully!", "dataset_id": dataset_id}), media_type="application/json", status_code=200)
    else:
        raise HTTPException(status_code=400, detail={"message": "Failed to create dataset!"})

@router.post("/upload")
def upload_dataset(id: str = Form(...), file: UploadFile = File(), user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to upload to this dataset!"})
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_dataset(data)
        return Response(content=json.dumps({"message": "Dataset uploaded successfully!"}), media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to upload dataset! Error: {e}"})

@router.post("/config")
def upload_config(request: ConfigUploadRequest, user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(request.id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to upload config for this dataset!"})
        data = json.loads(request.config)
        validate(data, config_schema)
        dataset = Dataset(request.id)
        dataset.save_config(data)
        return Response(content=json.dumps({"message": "Config uploaded successfully!"}), media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to upload config! Error: {e}"})

@router.get("/parse/{id}")
def parse_dataset(id: str, user_id: str = Depends(get_current_user)):
    if database_service.validate_dataset_id(id, user_id) is False:
        raise HTTPException(status_code=403, detail={"message": "You do not have permission to parse this dataset!"})
    return Response(content=json.dumps({"message": f"Parsing dataset {id}!"}), media_type="application/json", status_code=200)