from fastapi import APIRouter, UploadFile, File, Response, Form
from app.services.dataset import Dataset
import json

router = APIRouter(
    prefix="/dataset",
    tags=["dataset"]
)

@router.get("/")
def read_dataset():
    return {"message": "Welcome to the dataset route!"}

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
        return Response(content=json.dumps({"message": "Failed to upload dataset!"}), media_type="application/json", status_code=400)
    
@router.post("/config")
def upload_config(id: str = Form(...), file: UploadFile = File()):
    try:
        data = json.load(file.file)
        dataset = Dataset(id)
        dataset.save_config(data)
        print(f"Config for dataset {id} uploaded successfully!")
        return Response(content=json.dumps({"message": "Config uploaded successfully!"}), media_type="application/json", status_code=200)
    except Exception as e:
        print(f"Error uploading config: {e}")
        return Response(content=json.dumps({"message": "Failed to upload config!"}), media_type="application/json", status_code=400)
    
@router.get("/parse/{id}")
def parse_dataset(id: str):
    return Response(content=json.dumps({"message": f"Parsing dataset {id}!"}), media_type="application/json", status_code=200)