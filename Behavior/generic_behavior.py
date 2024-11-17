from typing import List

import numpy as np
import torch
from numpy import random
from torch import nn, optim

from Behavior.BehaviorMeta import BehaviorMeta
from Emotion.EmotionHandler import EmotionHandler
from actions import ActionInterface
from loguru import logger


class BehaviorActor(nn.Module):
    def __init__(self, input_size, action_size):
        super(BehaviorActor, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)

        # Actor (policy network)
        self.actor_fc = nn.Linear(128, action_size)
        self.softmax = nn.Softmax(dim=-1)

        # Critic (value network)
        self.critic_fc = nn.Linear(128, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))

        policy_logits = self.softmax(self.actor_fc(x))
        value = self.critic_fc(x)

        return policy_logits, value


class GenericBehavior(metaclass=BehaviorMeta):

    def __init__(self, actions: List[str], learning_rate=0.001, dominant_prob=0.7, actions_map=None):
        self.actions = actions
        self.actor_critic = BehaviorActor(14, 3)
        self.optimizer = optim.Adam(self.actor_critic.parameters(), lr=learning_rate)
        self.gamma = 0.99  # Discount factor
        self.dominant_prob = dominant_prob  # Probability of choosing the dominant action
        self.repeated_action_penalty = 0.1  # Penalty for repeating the same action
        self.last_action = None
        self.actions_map = actions_map  # Track the last action to apply the penalty

    def select_action(self, state: np.array) -> ActionInterface:
        """
        Selects an action using a probability distribution.
        The dominant action is chosen with ~70% probability, with room for other actions.
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        policy_logits, _ = self.actor_critic(state_tensor)

        # Get action probabilities
        probs = policy_logits.detach().numpy().flatten()

        # Select dominant action based on probabilities (~70% for highest, remaining for others)
        dominant_action_idx = np.argmax(probs)
        remaining_prob = 1 - self.dominant_prob
        action_probs = np.full(len(probs), remaining_prob / (len(probs) - 1))
        action_probs[dominant_action_idx] = self.dominant_prob
        # Sample action based on the new probabilities
        action_idx = np.random.choice(3, p=action_probs)
        action = self.actions[0]

        # Track the last action to introduce a penalty if repeated
        if self.last_action is None:
            self.last_action = action
        # Select an action based on current state
        logger.info(f"Selected action: {action}")
        previous_state=EmotionHandler().get_previous_state()
        current_state = EmotionHandler().get_current_state()
        # Simulated reward feedback
        reward = random.uniform(-1, 1)
        done = True  # Set to True if episode ends
        EmotionHandler().remember(previous_state, action, reward, current_state, done)
        # Update the model with feedback
        if previous_state is not None:
            self.update(EmotionHandler().get_previous_state(), action, reward, current_state)
        return self.actions_map[self.actions[0]]

    def update(self, state, action, reward, next_state):
        """
        Update the Actor-Critic model based on the feedback and critic value.
        Apply a penalty if the action is repeated.

        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)

        policy_logits, value = self.actor_critic(state_tensor)
        _, next_value = self.actor_critic(next_state_tensor)

        action_idx = torch.tensor([self.actions.index(action)])
        distribution = torch.distributions.Categorical(policy_logits)
        log_prob = distribution.log_prob(action_idx)

        # Apply penalty for repeated action
        if action == self.last_action:
            reward -= self.repeated_action_penalty
        target_value = reward
        self.last_action = action
        advantage = target_value - value.item()

        # Actor loss (policy loss)
        actor_loss = -log_prob * advantage

        # Critic loss (value loss)
        critic_loss = nn.MSELoss()(value, torch.tensor([target_value]))

        # Total loss
        loss = actor_loss + critic_loss

        # Perform optimization step
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
