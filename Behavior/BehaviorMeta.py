
from utils.SingletonMeta import SingletonMeta


class BehaviorMeta(SingletonMeta):
    """
    Combines Singleton behavior with required methods for Listener classes.
    """
    def __new__(cls, name, bases, class_dict):
        required_methods = ['select_action', 'update']
        if bases:
            for method in required_methods:
                if method not in class_dict or not callable(class_dict[method]):
                    raise TypeError(f"Class '{name}' must implement method '{method}'")
        return super().__new__(cls, name, bases, class_dict)