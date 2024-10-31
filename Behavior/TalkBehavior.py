import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from typing import List, Dict, Any

from Behavior.generic_behavior import GenericBehavior
from Emotion.EmotionHandler import EmotionHandler

from actions.ActionInterface import ActionInterface
from actions.TalkAction import TalkAction




class TalkBehavior(GenericBehavior):

    def __init__(self, actions: List[str], state_size: int, learning_rate=0.001, dominant_prob=0.7):
        self.actions = actions
        self.actor_critic = TalkBehaviorActor(state_size, len(actions))
        self.optimizer = optim.Adam(self.actor_critic.parameters(), lr=learning_rate)
        self.gamma = 0.99  # Discount factor
        self.dominant_prob = dominant_prob  # Probability of choosing the dominant action
        self.repeated_action_penalty = 0.1  # Penalty for repeating the same action
        self.last_action = None  # Track the last action to apply the penalty




# Example usage
if __name__ == "__main__":
    actions_map ={
        'talk': TalkAction()
    }
    actions = ['talk']
    state_size = 1  # Example state size (emotions and initiatives)

    # Initialize A2C agent with dominant action probability of 70%
    a2c_agent = TalkBehavior(actions, state_size, dominant_prob=0.7)

    state = EmotionHandler()
    # Select an action based on current state
    action = a2c_agent.select_action(state)
    print(f"Selected action: {action}")

    # Simulated reward feedback
    reward = random.uniform(-1, 1)
    done = True  # Set to True if episode ends

    # Update the model with feedback
    a2c_agent.update(state, action, reward, next_state, done)