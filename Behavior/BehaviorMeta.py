
from utils.SingletonMeta import SingletonMeta


class BehaviorMeta(SingletonMeta):
    """
    Combines Singleton behavior with required methods for Listener classes.
    """
    def __new__(cls, name, bases, class_dict):
        return super().__new__(cls, name, bases, class_dict)