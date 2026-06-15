import json
import redis
from rq import get_current_job

from typing import Any, List, Optional
from app.services.search_service import SearchService
from app.utils.redis_utils import publish_status


def index_dataset(dataset_id: str):
    """Placeholder function to simulate dataset indexing. Replace with actual indexing logic.

    Args:
        dataset_id (str): The ID of the dataset to be indexed.
    """
    print("Index is called with dataset_id:", dataset_id) #TODO: Remove before production
    job = get_current_job()
    
    publish_status(dataset_id=dataset_id, message="Starting indexing process...", progress=0)
    try:
        path = f"data/{dataset_id}"
        search = SearchService(dataset_id=dataset_id, path=path)
        search.index()
    except Exception as e:
        publish_status(dataset_id=dataset_id, message=f"Indexing failed: {str(e)}", progress=0)
        raise e

    if job:
        job.meta['progress'] = 100
        job.save_meta()