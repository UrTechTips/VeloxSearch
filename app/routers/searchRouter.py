import time
import uuid
from fastapi import APIRouter, Response, Response, Depends
from app.utils.api_utils import get_dataset_id_from_apikey
from app.services.search_service import SearchService
from app.db import service as database_service
from app.utils.dependencies_utils import get_apikey
from app.utils.api_utils import apihash

router = APIRouter(
    prefix="/search",
    tags=["search"],
    # dependencies=[Depends(get_apikey)]
)

@router.get("/")
def read_search(apikey: str = Depends(get_apikey)):
    return {"message": "Welcome to the search route!"}

@router.post("/query")
def execute_search(query: str, apikey: str = Depends(get_apikey)):
    start_time = time.perf_counter()
    dataset_id: str = get_dataset_id_from_apikey(apikey)
    search = SearchService(dataset_id)
    end_time = time.perf_counter()
    latency = end_time - start_time
    usage_id = uuid.uuid4().hex
    database_service.insert_usage(usage_id, apihash(apikey), "/search/query", latency, query_hash=uuid.uuid5(uuid.NAMESPACE_X500, query).hex)
    if not search.is_indexed():
        return {"message": "Dataset not indexed!"}, 400
    result = search.search(query)
    return {"message": f"Search results for query: {query}!", "results": result}, 200