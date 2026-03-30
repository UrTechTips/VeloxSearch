import redis
import json

def publish_status(dataset_id: str, message: str, progress: int = 0) -> None:
    """Publishes a status update to a Redis channel for a specific dataset.

    Args:
        dataset_id (str): The ID of the dataset for which the status update is being published.
        message (str): The status message to be published.
        progress (int, optional): The progress percentage (0-100) to be included in the status update. Defaults to 0.
    """
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    channel = f"status:{dataset_id}"
    r.publish(channel, json.dumps({"message": message, "progress": progress}))