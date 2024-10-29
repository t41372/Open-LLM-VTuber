import random
from abc import abstractmethod

import numpy as np
from typing import Any, Dict

from Behavior.BehaviorMeta import BehaviorMeta


class GenericBehavior(metaclass=BehaviorMeta):

    @abstractmethod
    def select_action(self, state) -> Any:
        pass

    @abstractmethod
    def update(self, action: Any, emotion: str) -> float:
        pass

