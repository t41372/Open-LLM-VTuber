import asyncio
import copy
import threading
from typing import Any

from loguru import logger


class DiscordInputList:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(DiscordInputList, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.list = []
            self.loop = asyncio.new_event_loop()  # Create a dedicated event loop for the queue
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            self.condition = threading.Condition()
            logger.success(f"CREATING Discord INPUT List THREAD : {id(self)}, thread id {threading.get_ident()}")

    def _run_event_loop(self):
        """Runs the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_input(self, input: Any):
        """Thread-safe method to add a prompt to the queue."""
        with self.condition:
            self.list.append(copy.deepcopy(input))
            logger.info(f"current input size: {len(self.list)}")
            self.condition.notify_all()  # Notify all waiting threads

    def get_input(self, message_type) -> Any:
        """Blocks until a prompt is available in the queue."""
        with self.condition:
            while len(self.list) == 0:
                logger.info("Message list is empty. Waiting for input...")
                self.condition.wait()  # Block until notified

            # Once notified, fetch the prompt
            future = asyncio.run_coroutine_threadsafe(self.get(message_type), self.loop)

            try:
                result = future.result()  # This blocks until an item is available
                return result
            except Exception as e:
                logger.error(f"Error while retrieving prompt: {e}")
                return None

    async def get(self, message_type) -> Any:
        for index, message in enumerate(self.list):
            if message["type"] == message_type:
                # Remove the message in place
                return self.list.pop(index)


