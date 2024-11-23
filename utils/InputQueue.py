import asyncio
import threading

import os
from loguru import logger
import numpy as np
from Emotion.EmotionHandler import EmotionHandler


class InputQueue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Ensure only one instance of InputQueue is created
        if cls._instance is None:
            cls._instance = super(InputQueue, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.queue = asyncio.Queue()
        self.loop = asyncio.new_event_loop()  # Create a dedicated event loop for the queue
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def add_input(self, input):
        """Thread-safe method to add input to the queue."""
        asyncio.run_coroutine_threadsafe(self.async_add_input(input), self.loop)

    def get_input(self):
        """Thread-safe method to get input from the queue."""
        future = asyncio.run_coroutine_threadsafe(self.async_get_input(), self.loop)
        return future.result()

    async def async_add_input(self, input: str | np.ndarray):
        """
        Asynchronously adds an input to the queue.
        If the input is a string, it classifies the emotion and appends it.
        """
        if isinstance(input, str):
            emotion_handler = EmotionHandler()
            classified_emotions = await emotion_handler.classify_emotion(input)
            input += "\n" + 'user emotions:' + str(classified_emotions) + '\n'
        await self.queue.put(input)

    async def async_get_input(self, number_inputs=1):
        """
        Asynchronously retrieves inputs from the queue.
        :param number_inputs: Number of inputs to retrieve from the queue.
        :return: A list of inputs.
        """
        inputs_list = await self.queue.get()
        logger.info(f"Inputs retrieved from the queue: {inputs_list}")
        return inputs_list
