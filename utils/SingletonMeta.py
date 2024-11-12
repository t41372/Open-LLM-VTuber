import threading


class SingletonMeta(type):
    """
    A thread-safe Singleton metaclass that enforces single instance creation.
    """
    _instances = {}  # Dictionary to hold a single instance of each class
    _lock = threading.Lock()  # Lock for thread-safe instance creation

    def __call__(cls, *args, **kwargs):
        with cls._lock:  # Ensure only one thread can create an instance at a time
            if cls not in cls._instances:
                # Create a new instance if it doesn't exist
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
