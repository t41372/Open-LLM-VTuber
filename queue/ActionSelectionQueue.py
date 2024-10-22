import threading
import time

from torch.multiprocessing import queue

from Behavior.generic_behavior import GenericBehavior
from actions import ActionInterface


class ActionSelectionQueue:

    def __init__(self, default_behavior: GenericBehavior):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.stop_event = threading.Event()
        self.default_behavior = default_behavior  # Default action to be executed if the queue is empty
        self.rewards = {'action1': 1.0, 'action2': 2.0}
        self.biases = {'action1': 0.5, 'action2': 1.0}

    def start(self):
        """Starts the queue processing thread."""
        print("Starting ActionHandlerQueue thread...")
        self.thread.start()

    def stop(self):
        """Stops the thread gracefully."""
        self.stop_event.set()
        self.thread.join()
        print("ActionHandlerQueue thread stopped.")

    def add_action(self, action: ActionInterface):
        """Adds a new action to the queue."""
        self.queue.put(action)
        print(f"Action {action.__class__.__name__} added to the queue.")

    def run(self):
        """Run the queue processor in a separate thread."""
        while not self.stop_event.is_set():
            try:
                # If the queue is empty, use the default action
                if self.queue.empty():
                    print("Queue is empty. Executing default action.")
                    result = self.default_behavior.fetch_new_action(self.rewards, self.biases)
                    print(f"Default action result: {result}")
                else:
                    # Fetch the next action from the queue
                    action = self.queue.get()  # Wait for 1 second
                    print(f"Processing action: {action.__class__.__name__}")
                    result = action.fetch_new_action(self.rewards, self.biases)
                    print(f"Action result: {result}")
            except queue.Empty:
                # If no action is in the queue, just pass and continue
                pass

            # Simulate some delay between actions
            time.sleep(0.5)
