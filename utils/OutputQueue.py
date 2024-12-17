import asyncio
import threading

import numpy as np
from loguru import logger

from Emotion.EmotionHandler import EmotionHandler


class OutputQueue:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(OutputQueue, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.queue = asyncio.Queue()
            self.loop = asyncio.new_event_loop()  # Create a dedicated event loop for the queue
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            logger.success(f"CREATING OUTPUT QUEUE THREAD : {id(self)}, thread id {threading.get_ident()}")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_output(self, input):
        """Thread-safe method to add inference results to the queue."""
        asyncio.run_coroutine_threadsafe(self.async_add_output(input), self.loop)

    def get_output(self):
        """Thread-safe method to get inference results from the queue."""
        future = asyncio.run_coroutine_threadsafe(self.async_get_output(), self.loop)
        return future.result()

    async def async_add_output(self, input: str | np.ndarray):
        """
        Asynchronously adds an messages to the queue.
        If the input is a string, it classifies the emotion and appends it.
        """
        await self.queue.put(input)

    async def async_get_output(self, number_inputs=1):
        """
        Asynchronously retrieves messages from the queue.
        :param number_inputs: Number of inputs to retrieve from the queue.
        :return: A list of inputs.
        """
        inputs_list = await self.queue.get()
        return inputs_list
