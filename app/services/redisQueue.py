from typing import Any, Callable, Optional
from rq import Queue as RQQueue
from rq.job import Job
from redis import Redis
from app.utils.redis_utils import publish_status

class IndexQueue:
    def __init__(self, func: Callable, queue_name: str = "default", host: str = "localhost", port: int = 6379) -> None:
        """Initializes a persistent indexing queue using Redis.

        Args:
            func (Callable): The function to be executed for each dataset ID enqueued. This function should accept a single argument, which is the dataset ID.
            queue_name (str, optional): The name of the Redis queue. Defaults to "default".
            host (str, optional): The hostname of the Redis server. Defaults to "localhost".
            port (int, optional): The port of the Redis server. Defaults to 6379.
        """
        self.redis_conn = Redis(host=host, port=port, decode_responses=False)
        self.function = func
        # is_async = True => jobs will be executed in background
        self.queue = RQQueue(name=queue_name, connection=self.redis_conn, is_async=True)

    def offer(self, *args: Any, **kwargs: Any) -> None:
        """Enqueues a dataset ID for processing. The provided function will be executed with the dataset ID as its argument.

        Returns:
            str: The ID of the enqueued job.
        """
        job = self.queue.enqueue(self.function, *args, **kwargs)
        publish_status(dataset_id=args[0], message="Dataset is queued for indexing.", progress=0)
        return job.id
    
    def get_status(self, job_id: str) -> Optional[str]:
        """Retrieves the status of a job in the queue.

        Args:
            job_id (str): The ID of the job to check.

        Returns:
            Optional[str]: The status of the job (e.g., "queued", "started", "finished", "failed"), or None if the job does not exist.
        """
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            return {
                "id": job.id,
                "status": job.get_status(),
                "progress": job.meta.get('progress', 0),
                "result": job.result if job.is_finished else None,
                "error": str(job.exc_info) if job.is_failed else None
            }
        except Exception as e:
            return {"error": "Job not found: " + str(e)}
    
    def clear(self) -> None:
        """Clears all jobs from the queue.
        """
        self.queue.empty()

    def __len__(self):
        """Returns the number of jobs currently in the queue.

        Returns:
            int: The number of jobs in the queue.
        """
        return len(self.queue)
    
    def __del__(self):
        try:
            self.queue.empty()
            self.redis_conn.close()
        except Exception as e:
            print(f"Error closing Redis connection: {e}")
