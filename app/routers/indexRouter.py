import time
import json
import asyncio
import traceback
from fastapi import APIRouter, Depends, WebSocket
from app.services.redisQueue import IndexQueue
from app.utils.indexQueue import index_dataset
from app.utils.dependencies_utils import get_current_user
from app.db import service as database_service

router = APIRouter(
    prefix="/index",
    tags=["index"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
def read_index():
    return {"message": "Welcome to the index route!"}

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, user_id: str = Depends(get_current_user)):
    await websocket.accept()
    redis = websocket.app.state.redis_client
    redis_queue = websocket.app.state.index_queue

    data = await websocket.receive_text()
    data = json.loads(data)
    print(f"Received message: {data['message']}")
    dataset_id = data.get("id")
    
    try:
        # Will be True if no errors but I dont care about the result here, just want to validate permissions
        database_service.validate_dataset_id(dataset_id, user_id)
    except Exception as e:
        await websocket.send_text(json.dumps({"message": f"Error validating dataset ID: {e}"}))
        await websocket.close()
        return

    if dataset_id is None or dataset_id == "":
        await websocket.send_text(json.dumps({"message": "Invalid dataset ID!"}))
        await websocket.close()
        return

    pubsub = redis.pubsub()
    pubsub.subscribe(f"status:{dataset_id}")
    redis_queue.offer(dataset_id)

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