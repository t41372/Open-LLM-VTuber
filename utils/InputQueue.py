import asyncio
import threading
from typing import Any

from loguru import logger

from Emotion.EmotionHandler import EmotionHandler


class InputQueue:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(InputQueue, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.queue = asyncio.Queue()
            self.loop = asyncio.new_event_loop()  # Create a dedicated event loop for the queue
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            logger.success(f"CREATING INPUT QUEUE THREAD : {id(self)}, thread id {threading.get_ident()}")

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

    async def async_add_input(self, input: Any):
        """
        Asynchronously adds an input to the queue.
        If the input is a string, it classifies the emotion and appends it.
        """
        result = []

        for dialogue in input:
            if dialogue['type'] == 'text':
                classified_emotions = await EmotionHandler().classify_emotion(dialogue['content'])
            else:
                classified_emotions = await EmotionHandler().classify_audio_emotion(dialogue['audio_data'])
            ## del dialogue['wav2vec_samples']
            dialogue['emotions'] = classified_emotions
            del dialogue['audio_data']
            result.append(dialogue)
        await self.queue.put(result)

    async def async_get_input(self):
        """
        Asynchronously retrieves inputs from the queue.
        :param number_inputs: Number of inputs to retrieve from the queue.
        :return: A list of inputs.
        """
        inputs_list = await self.queue.get()
        ##logger.info(f"Inputs retrieved from the queue: {inputs_list}")
        return inputs_list
