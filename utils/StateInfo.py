import threading
import time
from loguru import logger


class StateInfo(threading.Thread):
    def __init__(self):
        super(StateInfo, self).__init__()
        self.daemon = True  # Optional: Makes the thread exit when the main program exits

        # State variables
        self._current_action = None
        self._requires_input = False
        self._is_interrupted = False
        self._is_running = False
        self._voice_interface = None

        # Thread control
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def run(self):
        """Main loop that monitors state variables."""
        while not self._stop_event.is_set():
            with self._lock:
                # Log the current state for debugging
                logger.info(f"Action: {self._current_action}, "
                            f"Requires Input: {self._requires_input}, "
                            f"Interrupted: {self._is_interrupted}, "
                            f"Running: {self._is_running}")
            time.sleep(1)  # Adjust the frequency of state checks as needed

    # Setters
    def set_current_action(self, action):
        with self._lock:
            self._current_action = action
            logger.info(f"Current action set to: {self._current_action}")

    def set_requires_input(self, requires_input):
        with self._lock:
            self._requires_input = requires_input
            logger.info(f"Requires input set to: {self._requires_input}")

    def set_is_interrupted(self, is_interrupted):
        with self._lock:
            self._is_interrupted = is_interrupted
            logger.info(f"Is interrupted set to: {self._is_interrupted}")

    def set_is_running(self, is_running):
        with self._lock:
            self._is_running = is_running
            logger.info(f"Is running set to: {self._is_running}")

    # Getters
    def get_current_action(self):
        with self._lock:
            return self._current_action

    def get_requires_input(self):
        with self._lock:
            return self._requires_input

    def get_is_interrupted(self):
        with self._lock:
            return self._is_interrupted

    def get_is_running(self):
        with self._lock:
            return self._is_running

    def get_voice_interface(self):
        with self._lock:
            return self._voice_interface

    def set_voice_interface(self, voice_interface):
        with self._lock:
            self._voice_interface = voice_interface

    def stop(self):
        """Signals the thread to stop."""
        self._stop_event.set()
