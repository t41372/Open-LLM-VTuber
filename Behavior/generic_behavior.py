import random
from abc import abstractmethod

import numpy as np
from typing import Any, Dict


class GenericBehavior():

    @abstractmethod
    def fetch_new_action(self, rewards: Dict[str, float], biases: Dict[str, float]) -> Any:
        pass

    @abstractmethod
    def generate_reward(self, action: Any, emotion: str) -> float:
        pass

    @abstractmethod
    def update_biases(self, rewards: Dict[str, float], biases: Dict[str, float], emotions_map: Dict[str, float]) -> Dict[str, float]:
        pass

    @abstractmethod
    def update_initiatives(self, emotions_map: Dict[str, float]) -> Dict[str, float]:
        """
        Updates initiatives for emotions like anger and happiness based on Monte Carlo simulation.
        Uses a probability distribution to assign initiatives dynamically.
        :param emotions_map: A dictionary mapping emotions to their initial initiatives.
        :return: Updated initiatives for each emotion.
        """
        pass