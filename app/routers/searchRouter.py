from fastapi import APIRouter
from app.utils.api_utils import get_dataset_id_from_apikey
from app.services.search_service import SearchService

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

@router.get("/")
def read_search():
    return {"message": "Welcome to the search route!"}

@router.post("/query")
def execute_search(apikey: str, query: str):
    dataset_id: str = get_dataset_id_from_apikey(apikey)
    search = SearchService(dataset_id)
    if not search.is_indexed():
        return {"message": "Dataset not indexed!"}, 400
    result = search.search(query)
    return {"message": f"Search results for query: {query}!", "results": result}, 200