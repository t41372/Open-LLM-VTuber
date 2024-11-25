import queue
import threading

import numpy as np
from loguru import logger


class InferenceQueue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InferenceQueue, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.queue = queue.Queue()
        self.stop_event = threading.Event()

    def add_prompt(self, input: str | np.ndarray):
        self.queue.put(input)
        logger.info("Input added to the inference queue.")

    def get_prompt(self, number_inputs=1):
        """Gets a new input action from the Inference queue"""
        inputs_list = []
        for input_idx in range(number_inputs):
            inputs_list.append(self.queue.get())
        return inputs_list

