import time
import json
import asyncio
import traceback
from fastapi import APIRouter, Depends, WebSocket, status, HTTPException
from app.services.redisQueue import IndexQueue
from app.utils.indexQueue import index_dataset
from app.utils.dependencies_utils import get_current_user
from app.db import service as database_service

router = APIRouter(
    prefix="/index",
    tags=["index"],
)

@router.get("/")
def read_index():
    return {"message": "Welcome to the index route!"}

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None):
    await websocket.accept()

    try:
        if token is None:
            raise HTTPException(status_code=403, detail="Token is required for authentication")
        user_id = get_current_user(f"Bearer {token}")
    except Exception as e:
        await websocket.send_text(json.dumps({"message": f"Authentication error: {e}"}))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    redis = websocket.app.state.redis_client
    redis_queue = websocket.app.state.index_queue

    try:
        data = await websocket.receive_text()
        data = json.loads(data)
        dataset_id = data.get("id")
    except Exception:
        await websocket.send_text(json.dumps({"message": "Invalid initial message format"}))
        await websocket.close()
        return

    if not dataset_id:
        await websocket.send_text(json.dumps({"message": "Invalid dataset ID!"}))
        await websocket.close()
        return
    
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
    database_service.update_dataset(dataset_id, user_id, index_status="queued")

    pubsub = redis.pubsub()
    pubsub.subscribe(f"status:{dataset_id}")
    redis_queue.offer(dataset_id)

    while True:
        try:
            redis_message = pubsub.get_message(ignore_subscribe_messages=True)
            if redis_message and redis_message['type'] == 'message':
                msg_payload = redis_message['data'].decode('utf-8')
                await websocket.send_text(msg_payload)

                if json.loads(msg_payload).get("progress") == 100:
                    await websocket.send_text(json.dumps({"message": "Indexing complete!"}))
                    database_service.update_dataset(dataset_id, user_id, index_status="indexed")
                    break

            await asyncio.sleep(0.1)
        except Exception as e:
            await websocket.send_text(json.dumps({"message": f"WebSocket error: {e}"}))
            traceback.print_exc()
            break
    await websocket.close()