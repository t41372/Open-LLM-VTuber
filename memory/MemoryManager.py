from threading import Lock

from letta.schemas.agent import AgentState

from utils.StateInfo import StateInfo


class MemoryManager:
    """
    A thread-safe singleton class to manage core and archival memory fetches.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(MemoryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.core_memory = {}
            self.archival_memory = {}
            self._initialized = True

    def core_memory_fetch(self, agent_state: "AgentState", label: str):
        """
        Replace the contents of core memory. To delete memories, use an empty string for new_content.

        Args:
            agent_state: The AgentState object.ie, The Agent itself
            label (str): Section of the memory to be edited (persona or human).
        Returns:
            Optional[str]: None is always returned as this function does not produce a response.But it updates the agent's memory blocks.
        """
        memory_blocks=[]

        for speakers in StateInfo().get_active_speakers():
            break


    def archival_memory_fetch(self, key):
        """
        Fetch data from archival memory.

        Args:
            key (str): The key to fetch data for.

        Returns:
            The data associated with the key, or None if not found.
        """
        return self.archival_memory.get(key)