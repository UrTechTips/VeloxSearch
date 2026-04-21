from fastapi import APIRouter, UploadFile, File, Response, Form
from app.services.dataset import Dataset
from app.db import service as database_service
import json

router = APIRouter(
    prefix="/dataset",
    tags=["dataset"]
)

@router.get("/")
def read_dataset():
    return {"message": "Welcome to the dataset route!"}

@router.get("/create")
def create_dataset(user_id: str, dataset_id: str, database_name: str, description: str):
    if description == "":
        description = "No description provided."
    result = database_service.insert_dataset(dataset_id, user_id, database_name, description)
    if (result):
        return {"message": f"Created dataset {dataset_id}!"}, 201
    else:
        return {"message": "Failed to create dataset!"}, 400

@router.post("/")
def upload_dataset(id: str = Form(...), file: UploadFile = File()):
    try:
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_dataset(data)
        print(f"Dataset {id} uploaded successfully!")
        return {"message": "Dataset uploaded successfully!"}, 200
    except Exception as e:
        print(f"Error uploading dataset: {e}")
        return {"message": f"Failed to upload dataset! Error: {e}"}, 400

@router.post("/config")
def upload_config(id: str = Form(...), file: UploadFile = File()):
    try:
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_config(data)
        print(f"Config for dataset {id} uploaded successfully!")
        return {"message": "Config uploaded successfully!"}, 200
    except Exception as e:
        print(f"Error uploading config: {e}")
        return {"message": f"Failed to upload config! Error: {e}"}, 400
    
@router.get("/parse/{id}")
def parse_dataset(id: str):
    return {"message": f"Parsing dataset {id}!"}, 200