import json
import asyncio
import traceback
from fastapi import APIRouter, WebSocket, status, WebSocketDisconnect
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
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection initiated", flush=True)
    await websocket.accept()

    try:
        raw_data = await websocket.receive_text()
        data = json.loads(raw_data)
        token = data.get("token")
        dataset_id = data.get("id")
    except WebSocketDisconnect:
        print("Client disconnected before sending payload", flush=True)
        return
    except Exception as e:
        print(f"Invalid message format: {e}", flush=True)
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid format")
        return

    # 1. Validate Token
    if not token:
        print("Token missing during authentication", flush=True)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return

    try:
        user_id = get_current_user(f"Bearer {token}")
        print(f"User {user_id} authenticated successfully", flush=True)
    except Exception as e:
        print(f"Authentication error: {e}", flush=True)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        return

    # 3. Validate Dataset ID & Permissions
    if not dataset_id:
        print("Dataset ID missing", flush=True)
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Missing dataset ID")
        return

    try:
        database_service.validate_dataset_id(dataset_id, user_id)
    except Exception as e:
        print(f"Error validating dataset ID: {e}", flush=True)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Permission denied")
        return

    # 4. Queue Job & Subscribe to Redis
    database_service.update_dataset(dataset_id, user_id, index_status="queued")

    redis = websocket.app.state.redis_client
    redis_queue = websocket.app.state.index_queue

    pubsub = redis.pubsub()
    pubsub.subscribe(f"status:{dataset_id}")
    redis_queue.offer(dataset_id)

    # 5. Message Loop
    try:
        while True:
            # Note: If using redis.asyncio, replace with: redis_message = await pubsub.get_message(...)
            redis_message = pubsub.get_message(ignore_subscribe_messages=True)
            
            if redis_message and redis_message.get('type') == 'message':
                msg_payload = redis_message['data']
                if isinstance(msg_payload, bytes):
                    msg_payload = msg_payload.decode('utf-8')

                await websocket.send_text(msg_payload)

                try:
                    payload_data = json.loads(msg_payload)
                    if payload_data.get("progress") == 100:
                        await websocket.send_text(json.dumps({"message": "Indexing complete!"}))
                        database_service.update_dataset(dataset_id, user_id, index_status="indexed")
                        break
                except json.JSONDecodeError:
                    pass

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"Client disconnected during indexing (Dataset: {dataset_id})", flush=True)
    except Exception as e:
        print(f"WebSocket execution error: {e}", flush=True)
        traceback.print_exc()
    finally:
        # Guarantee pubsub unsubscription and clean disconnect
        try:
            pubsub.unsubscribe(f"status:{dataset_id}")
            pubsub.close()
        except Exception:
            pass
            
        try:
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        except RuntimeError:
            # Connection was already closed by client
            pass    