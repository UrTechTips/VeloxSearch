import redis
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core import REDIS_HOST, REDIS_PORT
from .routers import index

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        print("Connected to Redis")
        app.state.redis_client = redis_client
        yield
        redis_client.close()
    except Exception as e:
        print(f"Error during lifespan: {e}")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(index.router)

if __name__ == "__main__":
    uvicorn.run("app.main", host="localhost", port=8000, reload=True)