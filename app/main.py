import redis
import uvicorn
from fastapi import FastAPI, Request
from .routers import indexRouter, datasetRouter, apikeyRouter, searchRouter
from contextlib import asynccontextmanager
from app.core import REDIS_HOST, REDIS_PORT
from app.services.redisQueue import IndexQueue
from app.utils.indexQueue import index_dataset
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        index_queue = IndexQueue(index_dataset, "index_queue")
        print("Connected to Redis")
        app.state.redis_client = redis_client
        app.state.index_queue = index_queue
        yield
        redis_client.close()
    except Exception as e:
        print(f"Error during lifespan: {e}")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_origin_regex = "http://localhost:[0-9]+",
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(indexRouter)
app.include_router(datasetRouter)
app.include_router(apikeyRouter)
app.include_router(searchRouter)

if __name__ == "__main__":
    uvicorn.run("app.main", host="localhost", port=8000, reload=True)