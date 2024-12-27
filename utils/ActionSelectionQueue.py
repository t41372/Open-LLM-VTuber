import queue
import threading

from loguru import logger

from Behavior.generic_behavior import GenericBehavior
from OpenLLMVtuber import OpenLLMVTuberMain
from actions import ActionInterface
from utils.ActionPriority import ActionPriority
from utils.InferenceQueue import InferenceQueue
from utils.InputQueue import InputQueue
from utils.PromptFormatter import PromptFormatter


class ActionSelectionQueue:
    _instance = None
    _lock = threading.Lock()  # Lock object to ensure thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(ActionSelectionQueue, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, default_behavior: GenericBehavior):
        if not self._initialized:
            self._initialized = True
            self.queue = queue.PriorityQueue()
            self.thread = threading.Thread(target=self.run)
            self.stop_event = threading.Event()
            self.pause_event = threading.Event()
            self.default_behavior = default_behavior  # Default behavior to be executed if the queue is empty
            logger.success(f"CREATING ACTION SELECTION QUEUE THREAD : {id(self)}, thread id {threading.get_ident()}")

    def start(self):
        """Starts the queue processing thread."""
        logger.info("Starting ActionHandlerQueue thread...")
        self.thread.start()

    def stop(self):
        """Stops the thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        print("ActionHandlerQueue thread stopped.")

    def add_action(self, action: (ActionPriority, ActionInterface)):
        """Adds a new action to the queue."""
        self.queue.put(action)
        logger.info(f"Action {action.__class__.__name__} added to the queue.")

    def get_action(self):
        action = self.queue.get()[1]
        logger.info(f"Action {action.__class__.__name__} fetched from the queue.")
        return action

    def pause_action(self):
        self.pause_event.set()

    def resume_action(self):
        self.pause_event.clear()

    def run(self):
        """Run the queue processor in a separate thread."""
        while not self.stop_event.is_set():
            if self.pause_event.is_set():  # Handle pause
                logger.info("Action selection paused.")
                self.thread.join()
                continue

            ## disabling these because I moved to a model where the Listener decides the behavior not the queue

            # If the queue is empty, use the default action
            # if self.queue.empty():
            #     logger.info("Queue is empty. Executing default action.")
            #
            #
            #     ##selected_action = self.default_behavior.select_action(state=EmotionHandler().get_current_state())
            #     ##self.add_action(selected_action)

            else:
                # Fetch the next action from the queue
                action = self.get_action()
                if action.requires_input:
                    try:
                        # Directly run the async method and retrieve its result
                        current_input = InputQueue().get_input()

                    except Exception as e:
                        logger.error(f"Error fetching input: {e}")
                        continue

                    if action.not_is_blocking_action:
                        OpenLLMVTuberMain().not_is_blocking_event.set()
                else:
                    current_input = None
                result = PromptFormatter().format_for_gpt(action.start_action(),
                                                          self.default_behavior.choose_behavior(),
                                                          current_input)
                logger.info(f"Processing action: {action.__class__.__name__}")
                inference_queue = InferenceQueue()
                inference_queue.add_prompt(result)
