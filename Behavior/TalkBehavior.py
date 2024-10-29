import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from typing import List, Dict, Any

from Behavior.generic_behavior import GenericBehavior
from actions.ActionInterface import ActionInterface
from actions.TalkAction import TalkAction


class TalkBehaviorActor(nn.Module):
    def __init__(self, input_size, action_size):
        super(TalkBehaviorActor, self).__init__()
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


class TalkBehavior(GenericBehavior):

    def __init__(self, actions: List[str], state_size: int, learning_rate=0.001, dominant_prob=0.7):
        self.actions = actions
        self.actor_critic = TalkBehaviorActor(state_size, len(actions))
        self.optimizer = optim.Adam(self.actor_critic.parameters(), lr=learning_rate)
        self.gamma = 0.99  # Discount factor
        self.dominant_prob = dominant_prob  # Probability of choosing the dominant action
        self.repeated_action_penalty = 0.1  # Penalty for repeating the same action
        self.last_action = None  # Track the last action to apply the penalty

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
        action_idx = np.random.choice(len(self.actions), p=action_probs)
        action = self.actions[action_idx]

        # Track the last action to introduce a penalty if repeated
        if self.last_action is None:
            self.last_action = action
        return actions_map[actions[action_idx]]

    def update(self, state, action, reward, next_state, done):
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

        # Calculate target value
        if done:
            target_value = reward
            self.last_action = action
        else:
            target_value = reward + self.gamma * next_value.item()

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


# Example usage
if __name__ == "__main__":
    actions_map ={
        'talk': TalkAction()
    }
    actions = ['talk']
    state_size = 1  # Example state size (emotions and initiatives)

    # Initialize A2C agent with dominant action probability of 70%
    a2c_agent = TalkBehavior(actions, state_size, dominant_prob=0.7)

    emotions_map = {'anger': 0.8, 'happiness': 0.6, 'fear': 0.4, 'sadness': 0.3}
    initiatives_map = {'anger': 0.7, 'happiness': 0.9, 'fear': 0.3, 'sadness': 0.4}

    state = EmotionHandler
    next_state = np.array(
        list(emotions_map.values()) + list(initiatives_map.values()))  # In practice, this would change

    # Select an action based on current state
    action = a2c_agent.select_action(state)
    print(f"Selected action: {action}")

    # Simulated reward feedback
    reward = random.uniform(-1, 1)
    done = True  # Set to True if episode ends

    # Update the model with feedback
    a2c_agent.update(state, action, reward, next_state, done)