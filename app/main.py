import redis
import uvicorn
import firebase_admin
from contextlib import asynccontextmanager
from app.core import REDIS_HOST, REDIS_PORT
from app.utils.indexQueue import index_dataset
from fastapi import FastAPI, Request, Response
from app.services.redisQueue import IndexQueue
from app.services.token_bucket import TokenBucket
from fastapi.middleware.cors import CORSMiddleware
from app.services.vector_search import VectorSearch
from firebase_admin import credentials, initialize_app
from .routers import indexRouter, datasetRouter, apikeyRouter, searchRouter, userRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        VectorSearch.preload_model()
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        token_bucket = TokenBucket(redis_client, 100, 1, 1)
        index_queue = IndexQueue(index_dataset, "index_queue")
        print("Connected to Redis")
        app.state.redis_client = redis_client
        app.state.index_queue = index_queue
        app.state.token_bucket = token_bucket
        yield
        redis_client.close()
    except Exception as e:
        print(f"Error during lifespan: {e}")

app = FastAPI(lifespan=lifespan)
cred = credentials.Certificate("firebaseCred.json")
firebase_admin.initialize_app(cred)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_origin_regex = "http://localhost:[0-9]+",
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
)

@app.middleware("http")
async def server_wide_ratelimit(request: Request, call_next):
    bucket = request.app.state.token_bucket
    
    allowed, remaining = bucket.allow("global")
    if not allowed:
        return Response(status_code=429, content="Rate limit exceeded. Please try again later.")
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(indexRouter)
app.include_router(datasetRouter)
app.include_router(apikeyRouter)
app.include_router(searchRouter)
app.include_router(userRouter)

if __name__ == "__main__":
    uvicorn.run("app.main", host="localhost", port=8080, reload=True)