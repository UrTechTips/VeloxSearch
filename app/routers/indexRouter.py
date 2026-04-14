import time
import json
import asyncio
import traceback
from fastapi import APIRouter, WebSocket
from app.services.redisQueue import IndexQueue
from app.utils.indexQueue import index_dataset

router = APIRouter(
    prefix="/index",
    tags=["index"]
)

@router.get("/")
def read_index():
    return {"message": "Welcome to the index route!"}

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    redis = websocket.app.state.redis_client

    data = await websocket.receive_text()
    data = json.loads(data)
    print(f"Received message: {data['message']}")

    pubsub = redis.pubsub()
    pubsub.subscribe(f"status:{data['id']}")
    redis_queue = IndexQueue(index_dataset)
    redis_queue.offer(data['id'])

    while True:
        try:
            redis_message = pubsub.get_message(ignore_subscribe_messages=True)
            if redis_message and redis_message['type'] == 'message':
                msg_payload = redis_message['data'].decode('utf-8')
                await websocket.send_text(f"Update: {msg_payload}")

                if json.loads(msg_payload).get("progress") == 100:
                    break

            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"WebSocket error: {e}")
            traceback.print_exc()
            break
    await websocket.close()