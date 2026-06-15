import json
import time
import uuid
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.utils.api_utils import get_dataset_id_from_apikey
from app.services.search_service import SearchService
from app.db import service as database_service
from app.utils.dependencies_utils import get_apikey
from app.utils.hash_utils import queryHash, apihash
from typing import Tuple

router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_apikey)]
)

@router.get("/")
def read_search():
    return {"message": "Welcome to the search route!"}

@router.post("/query")
def execute_search(query: str, limit=10, sort=None, dependency: Tuple[str, str] = Depends(get_apikey), query_hash: str = Depends(queryHash), request: Request = None):
    """Search for relevant information in the dataset based on the query and return the results.

    Args:
        query (str): The search query provided by the user.
        limit (int, optional): The maximum number of results to return. Defaults to 10.
        sort (_type_, optional): The sorting criteria for the search results. Defaults to None.
        dependency (Tuple[str, str], optional): The API key and dataset ID tuple. Defaults to Depends(get_apikey).
        query_hash (str, optional): The hash of the query for caching purposes. Defaults to Depends(queryHash).
        request (Request, optional): The FastAPI request object. Defaults to None.

    Raises:
        HTTPException: If the dataset is not indexed yet, a 409 Conflict error is raised with a message indicating that the dataset is not ready for searching.

    Returns:
        JSONResponse: The search results wrapped in a JSONResponse object.
    """
    apikey, dataset_id = dependency
    redis_client = request.app.state.redis_client
    print(f"Received search query: {query} for dataset_id: {dataset_id} with query_hash: {query_hash}")
    if redis_client.exists(f"search:{dataset_id}:{query_hash}"):
        start_time = time.perf_counter()
        cached_result = redis_client.get(f"search:{dataset_id}:{query_hash}")
        end_time = time.perf_counter()
        latency = end_time - start_time
        database_service.insert_usage(apihash(apikey), "/search/query", latency, query_hash=uuid.uuid5(uuid.NAMESPACE_X500, query).hex)
        return JSONResponse(content={"message": f"Search results for query: {query} (cached)!", "results": eval(cached_result), "success": True}, media_type="application/json", status_code=200)

    start_time = time.perf_counter()
    search = SearchService(dataset_id)
    
    if not search.is_indexed():
        # return {"message": "Dataset is not indexed yet. Please try again later.", "results": []}
        raise HTTPException(status_code=409, detail={"message": "Dataset is not indexed yet. Please try again later.", "success": False})
    search = search.load()
    result = search.search(query, top_k=int(limit))

    end_time = time.perf_counter()
    latency = end_time - start_time
    database_service.insert_usage(apihash(apikey), "/search/query", latency, query_hash=uuid.uuid5(uuid.NAMESPACE_X500, query).hex)

    redis_client.setex(f"search:{dataset_id}:{query_hash}", 3600, str(result))
    
    return JSONResponse(content={"message": f"Search results for query: {query}!", "results": result, "success": True}, media_type="application/json", status_code=200)