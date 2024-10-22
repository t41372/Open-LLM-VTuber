import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque


# Define the Deep Q-Network (DQN) architecture
class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)


class EmotionHandlerDQN:
    def __init__(self, emotions, state_size, action_size, gamma=0.95, epsilon=1.0, epsilon_min=0.01,
                 epsilon_decay=0.995, learning_rate=0.001):
        self.emotions = emotions
        self.emotion_reward_map = {emotion: 1 for emotion in emotions}
        self.initiative_map = {emotion: 1 for emotion in emotions}
        self.repeated_tone_count = 0
        self.random_factor = 0.3  # Starting at 30% for randomness
        self.high_initiative_threshold = 1.5  # Threshold for high initiatives

        # Q-learning parameters
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate

        # Replay buffer
        self.memory = deque(maxlen=2000)

        # Initialize Q-networks
        self.model = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = nn.MSELoss()

    def classify_emotion(self, input_text):
        """Stub for emotion classifier."""
        classified_emotion = random.choice(self.emotions)
        print(f"Classified emotion: {classified_emotion}")
        return classified_emotion

    def choose_emotions_based_on_initiative(self):
        """
        Determines the emotions to respond with based on the initiative map.
        Q-learning will be used to determine whether to respond with a single strong emotion or a combination of emotions.
        :return: A list of emotions based on initiative.
        """
        state = self.get_current_state()
        action = self.act(state)  # Use DQN to choose an action
        return self.map_action_to_emotions(action)

    def get_current_state(self):
        """
        Get the current state based on the emotion reward map and initiative map.
        Example state: [anger_reward, disgust_reward, ..., anger_initiative, disgust_initiative, ...]
        """
        state = list(self.emotion_reward_map.values()) + list(self.initiative_map.values())
        return state

    def map_action_to_emotions(self, action):
        """
        Maps a chosen action (from Q-learning) to a list of emotions.
        Example action mapping:
        - 0: Return a single strong emotion (highest initiative).
        - 1: Return two emotions (high-medium initiatives).
        - 2: Return three emotions (lower-medium initiatives).
        """
        sorted_emotions = sorted(self.initiative_map.items(), key=lambda item: item[1], reverse=True)

        if action == 0:
            # Respond with a single strong emotion
            return [sorted_emotions[0][0]]
        elif action == 1:
            # Respond with two emotions
            return [sorted_emotions[0][0], sorted_emotions[1][0]]
        else:
            # Respond with three emotions
            return [sorted_emotions[0][0], sorted_emotions[1][0], sorted_emotions[2][0]]

    def act(self, state):
        """Choose an action using epsilon-greedy policy (explore or exploit)."""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)  # Explore: random action
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        act_values = self.model(state_tensor)
        return torch.argmax(act_values[0]).item()  # Exploit: action with highest Q-value

    def replay(self, batch_size):
        """Replay experiences and learn from them."""
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)
                target = reward + self.gamma * torch.max(self.model(next_state_tensor)[0]).item()
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            target_f = self.model(state_tensor)
            target_f[0][action] = target
            # Train the model
            self.optimizer.zero_grad()
            loss = self.loss_fn(target_f, self.model(state_tensor))
            loss.backward()
            self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def remember(self, state, action, reward, next_state, done):
        """Store experiences in memory."""
        self.memory.append((state, action, reward, next_state, done))

    def get_llm_response_emotion(self, user_prompt_emotion: str) -> str:
        """
        Simulates generating an LLM response based on the chosen emotions.
        """
        # Choose emotions based on the Q-learning model
        emotions_to_use = self.choose_emotions_based_on_initiative()

        # Simulate response
        response = f"LLM responds with emotions: {', '.join(emotions_to_use)}"
        print(response)
        return response

    def update_emotion_and_initiative(self, user_prompt_emotion: str, feedback: float):
        """
        Update the reward and initiative maps based on user emotion and feedback (reward).
        :param user_prompt_emotion: The emotion detected from the user's prompt.
        :param feedback: The reward or penalty for the response.
        """
        self.emotion_reward_map[user_prompt_emotion] += feedback  # Update rewards
        self.initiative_map[user_prompt_emotion] += 0.1  # Increase initiative for that emotion


# Example usage
if __name__ == "__main__":
    emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    state_size = len(emotions) * 2  # Both emotion rewards and initiatives as part of the state
    action_size = 3  # 0 = single strong emotion, 1 = two emotions, 2 = three emotions

    handler = EmotionHandlerDQN(emotions, state_size, action_size)

    # Simulate some interactions
    for episode in range(10):
        user_emotion = handler.classify_emotion("User prompt")  # Classify user's emotion
        handler.get_llm_response_emotion(user_emotion)  # Generate LLM response

        # Simulate feedback (reward), and update the emotion maps
        feedback = random.uniform(-1, 1)  # Reward could be based on external feedback or satisfaction
        handler.update_emotion_and_initiative(user_emotion, feedback)

        # Store state, action, and reward for replay
        state = handler.get_current_state()
        action = handler.act(state)
        next_state = handler.get_current_state()
        handler.remember(state, action, feedback, next_state, done=False)

        # Perform replay to learn from the experiences
        handler.replay(batch_size=32)
