import time
import uuid
from fastapi import APIRouter, Request, Response, Depends, HTTPException
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
def read_search(apikey: str = Depends(get_apikey)):
    return {"message": "Welcome to the search route!"}

@router.post("/query")
def execute_search(query: str, dependency: Tuple[str, str] = Depends(get_apikey), query_hash: str = Depends(queryHash), request: Request = None):
    redis_client = request.app.state.redis_client
    if redis_client.exists(f"search:{dependency[1]}:{query_hash}"):
        cached_result = redis_client.get(f"search:{dependency[1]}:{query_hash}")
        return Response(content={"message": f"Search results for query: {query} (cached)!", "results": eval(cached_result)}, media_type="application/json", status_code=200)

    apikey, dataset_id = dependency
    start_time = time.perf_counter()
    search = SearchService(dataset_id)
    
    if not search.is_indexed():
        return {"message": "Dataset is not indexed yet. Please try again later.", "results": []}
        # raise HTTPException(status_code=409, detail={"message": "Dataset is not indexed yet. Please try again later."})
    result = search.search(query)

    end_time = time.perf_counter()
    latency = end_time - start_time
    database_service.insert_usage(apihash(apikey), "/search/query", latency, query_hash=uuid.uuid5(uuid.NAMESPACE_X500, query).hex)

    redis_client.setex(f"search:{dataset_id}:{query_hash}", 3600, str(result))
    
    return Response(content={"message": f"Search results for query: {query}!", "results": result}, media_type="application/json", status_code=200)