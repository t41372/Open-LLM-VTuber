from utils.SingletonMeta import SingletonMeta


class ActionsMeta(SingletonMeta):
    """
    This is a thread-safe implementation of Singletons for the action classes.
    """

    """
    Combines Singleton behavior with required methods for Listener classes.
    """
    def __new__(cls, name, bases, class_dict):
        required_methods = ['start_action','finish_action','block_llm_generation']
        required_attributes = ['is_blocking_action']
        if bases:
            for method in required_methods:
                if method not in class_dict or not callable(class_dict[method]):
                    raise TypeError(f"Class '{name}' must implement method '{method}'")
            for attribute in required_attributes:
                if attribute not in class_dict or not callable(class_dict[attribute]):
                    raise TypeError(f"Class '{name}' must implement attribute '{attribute}'")
        return super().__new__(cls, name, bases, class_dict)