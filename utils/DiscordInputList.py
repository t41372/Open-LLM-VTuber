import asyncio
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
            logger.success(f"CREATING Discord INPUT QUEUE THREAD : {id(self)}, thread id {threading.get_ident()}")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_input(self, input):
        """Thread-safe method to add input to the list."""
        asyncio.run_coroutine_threadsafe(self.async_add_input(input), self.loop)

    def get_input(self, message_type):
        """Thread-safe method to get input from the list."""
        future = asyncio.run_coroutine_threadsafe(self.async_get_input(message_type), self.loop)
        return future.result()

    async def async_add_input(self, input: Any):
        """
        Asynchronously adds an input to the list.
        If the input is a string, it classifies the emotion and appends it.
        """
        logger.info(f"Inputs added to the queue: {input}")
        self.list.append(input)

    async def async_get_input(self, message_type="text"):
        """
        Asynchronously retrieves inputs from the queue.
        :param message_type: The type of message to retrieve ie. text or audio etc..
        :return: A list of inputs.
        """
        for message in self.list:
            if message['type'] == message_type:
                result = message
                logger.info(f"Inputs retrieved from the queue: {result}")
                self.list.append(result)
                self.list.remove(message)
                return result
