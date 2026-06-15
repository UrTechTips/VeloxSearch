import uuid
import json
from typing import Dict, List
from fastapi.responses import JSONResponse
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

class DatasetDeleteRequest(BaseModel):
    id: str

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

@router.get("/get/{id}")
def get_dataset_metadata(id: str, user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to access this dataset!"})
        metadata = database_service.get_dataset_metadata(id)['metadata']
        usage_quota = database_service.get_dataset_usagequota(id)
        usage_rate = database_service.get_dataset_useagerate(id)
        metadata["usage_quota"] = usage_quota
        metadata["usage_rate"] = usage_rate
        return JSONResponse(content={"message": f"Metadata for dataset {id}!", "metadata": metadata, "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to get dataset metadata! Error: {e}", "success": False})

@router.get("/list")
def list_datasets(user_id: str = Depends(get_current_user)):
    try:
        datasets = database_service.list_datasets(user_id)
        return JSONResponse(content={"datasets": datasets, "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to list datasets! Error: {e}", "success": False})

@router.post("/create")
def create_dataset(request: DatasetCreateRequest, user_id: str = Depends(get_current_user)):
    if request.description == "":
        request.description = "No description provided."

    name = request.database_name
    id_hash = uuid.uuid5(uuid.NAMESPACE_X500, f"{user_id}_{request.database_name}").hex
    random_string = id_hash[:8]
    dataset_id = f"{name}-{random_string}"
    result = database_service.insert_dataset(dataset_id, user_id, request.database_name, request.description, index_status="created")
    if (result):
        return JSONResponse(content={"message": "Dataset created successfully!", "dataset_id": dataset_id, "success": True}, media_type="application/json", status_code=200)
    else:
        raise HTTPException(status_code=400, detail={"message": "Failed to create dataset!", "success": False})

@router.post("/upload")
def upload_dataset(id: str = Form(...), file: UploadFile = File(), user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to upload to this dataset!"})
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_dataset(data)
        database_service.update_dataset(id, user_id, index_status="uploaded", length=len(data))
        return JSONResponse(content={"message": "Dataset uploaded successfully!", "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to upload dataset! Error: {e}", "success": False})

@router.post("/config")
def upload_config(request: ConfigUploadRequest, user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(request.id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to upload config for this dataset!", "success": False})
        data = json.loads(request.config)
        validate(data, config_schema)
        dataset = Dataset(request.id)
        dataset.save_config(data)
        return JSONResponse(content={"message": "Config uploaded successfully!", "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to upload config! Error: {e}", "success": False})

@router.get("/parse/{id}")
def parse_dataset(id: str, user_id: str = Depends(get_current_user)):
    try:
        if database_service.validate_dataset_id(id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to parse this dataset!"})
        dataset = Dataset(id)
        parsed_documents = dataset.parse_dataset()
        return JSONResponse(content={"message": f"Parsing dataset {id}!", "schema": parsed_documents, "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to parse dataset! Error: {e}", "success": False})

@router.post("/delete/{id}")
def delete_dataset(request: DatasetDeleteRequest, user_id: str = Depends(get_current_user)):
    try:
        id = request.id
        if not id:
            raise HTTPException(status_code=400, detail={"message": "Dataset ID is required!", "success": False})
        if database_service.validate_dataset_id(id, user_id) is False:
            raise HTTPException(status_code=403, detail={"message": "You do not have permission to delete this dataset!", "success": False})
        dataset = Dataset(id)
        dataset.delete_dataset()
        database_service.delete_dataset(id, user_id)
        return JSONResponse(content={"message": f"Deleted dataset {id}!", "success": True}, media_type="application/json", status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"message": f"Failed to delete dataset! Error: {e}", "success": False})