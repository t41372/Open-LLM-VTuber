from utils.SingletonMeta import SingletonMeta


class ActionsMeta(SingletonMeta):
    """
    This is a thread-safe implementation of Singletons for the action classes.
    """

    """
    Combines Singleton behavior with required methods for Listener classes.
    """
    def __new__(cls, name, bases, class_dict):
        required_methods = ['start_action']
        if bases:
            for method in required_methods:
                if method not in class_dict or not callable(class_dict[method]):
                    raise TypeError(f"Class '{name}' must implement method '{method}'")
        return super().__new__(cls, name, bases, class_dict)