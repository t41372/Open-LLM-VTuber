
from typing import Dict

from numpy.random import random

from Behavior.generic_behavior import GenericBehavior


class TalkBehavior(GenericBehavior):

    def __init__(self, emotion_factors: Dict[str, float], initiative_factors: Dict[str, float]):
        """
        Initializes the ActionHandler with emotion factors and initiative factors.
        :param emotion_factors: A dictionary mapping emotions to their corresponding factors.
        :param initiative_factors: A dictionary mapping emotions to their initial initiatives.
        """
        self.emotion_factors = emotion_factors
        self.initiative_factors = initiative_factors

    def fetch_new_action(self, rewards: Dict[str, float], biases: Dict[str, float]) -> str:
        """
        Selects a new action based on a simple weighted sum of rewards and biases.
        """
        action_scores = {}
        for action, reward in rewards.items():
            bias = biases.get(action, 0)
            action_scores[action] = reward + bias

        # Pick the action with the highest score
        selected_action = max(action_scores, key=action_scores.get)
        return selected_action

    def generate_reward(self, action: str, emotion: str) -> float:
        """
        Generates a reward based on the action and an emotional factor.
        Uses emotion factors passed during class initialization.
        """
        base_reward = random.uniform(1, 10)
        emotion_multiplier = self.emotion_factors.get(emotion, 1.0)
        reward = base_reward * emotion_multiplier
        print(f"Generated reward for action '{action}' with emotion '{emotion}': {reward:.2f}")
        return reward

    def update_biases(self, rewards: Dict[str, float], biases: Dict[str, float], emotions_map: Dict[str, float]) -> \
    Dict[str, float]:
        """
        Updates biases based on the current emotions map, where each emotion is weighted by the "initiative".
        """
        for emotion, initiative in emotions_map.items():
            for action in rewards.keys():
                if emotion in biases:
                    biases[action] += initiative * rewards[action]
                else:
                    biases[action] = initiative * rewards[action]
        print(f"Updated biases: {biases}")
        return biases

    def update_initiatives(self, emotions_map: Dict[str, float]) -> Dict[str, float]:
        """
        Updates the initiatives based on the emotion and other factors.
        Emotions like 'anger' and 'happiness' have higher initiatives, and the method considers various factors.
        """
        for emotion in emotions_map:
            if emotion in ['anger', 'happiness']:
                # Increase initiative for these emotions based on specific factors
                factor = self.initiative_factors.get(emotion, 1.0)
                emotions_map[emotion] += factor
            else:
                # For other emotions, update based on their respective factors
                factor = self.initiative_factors.get(emotion, 0.5)
                emotions_map[emotion] += factor

        print(f"Updated initiatives: {emotions_map}")
        return emotions_map

# Example usage
if __name__ == "__main__":
    rewards = {
        'talk': 5.0,
    }

    biases = {
        'talk': 1.0,
    }

    # Emotion factors defined outside the methods
    emotion_factors = {
        'happy': 1.5,
        'sad': 0.5,
        'neutral': 1.0,
        'angry': 0.8
    }

    emotions_map = {
        'happy': 1.2,
        'sad': -0.8
    }

    # Initialize the ActionHandler with the emotion factors
