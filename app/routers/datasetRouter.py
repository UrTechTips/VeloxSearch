import uuid
import json
from typing import Dict
from pydantic import BaseModel
from app.services.dataset import Dataset
from app.db import service as database_service
from fastapi import APIRouter, UploadFile, File, Response, Form

class DatasetCreateRequest(BaseModel):
    user_id: str
    database_name: str
    description: str = None

class ConfigUploadRequest(BaseModel):
    id: str
    config: Dict

router = APIRouter(
    prefix="/dataset",
    tags=["dataset"]
)

@router.get("/")
def read_dataset():
    return {"message": "Welcome to the dataset route!"}

@router.post("/create")
def create_dataset(request: DatasetCreateRequest):
    if request.description == "":
        request.description = "No description provided."

    dataset_id = uuid.uuid5(uuid.NIL, f"{request.user_id}_{request.database_name}").hex
    result = database_service.insert_dataset(dataset_id, request.user_id, request.database_name, request.description)
    if (result):
        return Response(content=json.dumps({"message": "Dataset created successfully!", "dataset_id": dataset_id}), media_type="application/json", status_code=200)
    else:
        return Response(content=json.dumps({"message": "Failed to create dataset!"}), media_type="application/json", status_code=400)

@router.post("/")
def upload_dataset(id: str = Form(...), file: UploadFile = File()):
    try:
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_dataset(data)
        print(f"Dataset {id} uploaded successfully!")
        return Response(content=json.dumps({"message": "Dataset uploaded successfully!"}), media_type="application/json", status_code=200)
    except Exception as e:
        print(f"Error uploading dataset: {e}")
        return Response(content=json.dumps({"message": f"Failed to upload dataset! Error: {e}"}), media_type="application/json", status_code=400)

@router.post("/config")
def upload_config(request: ConfigUploadRequest):
    try:
        data = json.load(request.config)
        dataset = Dataset(request.id)
        dataset.save_config(data)
        print(f"Config for dataset {request.id} uploaded successfully!")
        return Response(content=json.dumps({"message": "Config uploaded successfully!"}), media_type="application/json", status_code=200)
    except Exception as e:
        print(f"Error uploading config: {e}")
        return Response(content=json.dumps({"message": f"Failed to upload config! Error: {e}"}), media_type="application/json", status_code=400)

@router.get("/parse/{id}")
def parse_dataset(id: str):
    return Response(content=json.dumps({"message": f"Parsing dataset {id}!"}), media_type="application/json", status_code=200)