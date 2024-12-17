import asyncio
import threading
from typing import Any

from loguru import logger


class InferenceQueue:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(InferenceQueue, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.queue = asyncio.Queue()
            self.loop = asyncio.new_event_loop()  # Dedicated event loop for the queue
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            self.condition = threading.Condition()  # Used for synchronization
            logger.success(f"CREATING INFERENCE QUEUE THREAD object : {id(self)}, thread id {threading.get_ident()}")

    def _run_event_loop(self):
        """Runs the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_prompt(self, input: Any):
        """Thread-safe method to add a prompt to the queue."""
        with self.condition:
            asyncio.run_coroutine_threadsafe(self.queue.put(input), self.loop)

            logger.info(f"current queue size: {self.queue.qsize()}")
            self.condition.notify_all()  # Notify all waiting threads

    def get_prompt(self) -> Any:
        """Blocks until a prompt is available in the queue."""
        with self.condition:
            while self.queue.empty():
                logger.info("Queue is empty. Waiting for prompts...")
                self.condition.wait()  # Block until notified

            # Once notified, fetch the prompt
            future = asyncio.run_coroutine_threadsafe(self.queue.get(), self.loop)
            try:
                result = future.result()  # This blocks until an item is available
                logger.info(f"Prompt retrieved from queue: {result}")
                return result
            except Exception as e:
                logger.error(f"Error while retrieving prompt: {e}")
                return None
