import queue
import threading

import numpy as np
from loguru import logger

from Emotion.EmotionHandler import EmotionHandler


class InputQueue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Ensure only one instance of EmotionHandler is created
        if cls._instance is None:
            cls._instance = super(InputQueue, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.stop_event = threading.Event()

    # Default action to be executed if the queue is empty

    def start(self):
        """Starts the queue processing thread."""
        logger.info("Starting InputQueue thread...")
        self.thread.start()

    def stop(self):
        """Stops the thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        logger.info("InputQueue thread stopped.")

    def add_input(self, input: str | np.ndarray):
        if type(input) == str:
            classified_emotions = EmotionHandler().classify_emotion(input)
            input += '\n' + 'user emotions:' + str(classified_emotions) + '\n'
        self.queue.put(input)
        print(f"Input {input} added to the queue.")

    def get_input(self, number_inputs=1):
        """Gets a new input action from the queue"""
        inputs_list = []
        for input_idx in range(number_inputs):
            inputs_list.append(self.queue.get())
        return inputs_list

    def run(self):
        """Run the queue processor in a separate thread."""
        while not self.stop_event.is_set():
            pass
        return
