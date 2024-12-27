import random
from collections import deque
from typing import Any, List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from loguru import logger
from transformers import AutoModelForAudioClassification, pipeline, AutoFeatureExtractor

emotions = ["anger", "calm", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
state_size = len(emotions) * 2  # Both emotion rewards and initiatives as part of the state
action_size = 3



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


class EmotionHandler:
    _instance = None  # Class variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        # Ensure only one instance of EmotionHandler is created
        if cls._instance is None:
            cls._instance = super(EmotionHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self, emotions=emotions, state_size=state_size, action_size=action_size, gamma=0.95, epsilon=1.0,
                 epsilon_min=0.01, epsilon_decay=0.995, learning_rate=0.001):
        if hasattr(self, '_initialized') and self._initialized:
            return  # Skip reinitialization if already initialized
        self._initialized = True  # Mark as initialized

        # Initialize class attributes
        self.emotions = emotions
        self.emotion_reward_map = {emotion: 1 for emotion in emotions}
        self.initiative_map = {emotion: 1 for emotion in emotions}
        self.repeated_tone_count = 0
        self.random_factor = 0.3  # Starting at 30% for randomness
        self.high_initiative_threshold = 1.3  # Threshold for high initiatives

        self.classifier = pipeline("sentiment-analysis", model="michellejieli/emotion_text_classifier", device="cuda") ## for text data

        self.audio_classifier = AutoModelForAudioClassification.from_pretrained("firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3") ## for audio data
        self.feature_extractor = AutoFeatureExtractor.from_pretrained("firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3", do_normalize=False)
        self.id2label = self.audio_classifier.config.id2label
        # Q-learning parameters
        self.current_user_emotion = 'neutral'
        self.current_llm_emotion = ['neutral']

        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.learning_rate = learning_rate
        self.previous_state = None

        # Replay buffer
        self.memory = deque(maxlen=4000)

        # Initialize Q-networks
        self.model = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = nn.MSELoss()
        logger.success(f"CREATING EMOTION HANDLER THREAD : {id(self)}")
    async def classify_emotion(self, input_text):
        """Traditional text based emotion classifier"""

        if input_text is None:
            return None

        try:
            result = self.classifier(input_text)
            classified_emotions = dict(zip(self.emotions, list(round(float(i), 2) for i in result[0])))
            return classified_emotions
        except Exception as e:
            logger.error(e)
        return None

    async def classify_audio_emotion(self, input_audio):
        """Classifies emotions based on audio input, more expensive and can introduce significant latency, do it only if you have a good GPU"""
        max_duration=30.0
        max_length = int(self.feature_extractor.sampling_rate * max_duration)
        if len(input_audio) > max_length:
            audio_array = input_audio[:max_length]
        else:
            audio_array = np.pad(input_audio, (0, max_length - len(input_audio)))

        inputs = self.feature_extractor(
            audio_array,
            sampling_rate=self.feature_extractor.sampling_rate,
            max_length=max_length,
            truncation=True,
            return_tensors="pt",
        )
        if input_audio is None:
            return None
        try:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = self.audio_classifier.to(device)
            inputs = {key: value.to(device) for key, value in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            logits = outputs.logits
            predicted_id = torch.argmax(logits, dim=-1).item()
            classified_emotions = self.id2label[predicted_id]

            return classified_emotions

        except Exception as e:
            logger.error(e)
        return None

    def choose_emotions_based_on_initiative(self):
        """
        Determines the emotions to respond with based on the initiative map.
        Q-learning will be used to determine whether to respond with a single strong emotion or a combination of emotions.
        :return: A list of emotions based on initiative.
        """
        state = self.get_current_state()
        action = self.act(state)  # Use DQN to choose an action
        return self.map_action_to_emotions(action)

    def get_current_state(self) -> List[Any]:
        """
        Get the current state based on the emotion reward map and initiative map.
        Example state: [anger_reward, disgust_reward, ..., anger_initiative, disgust_initiative, ...]
        """
        state = list(self.emotion_reward_map.values()) + list(self.initiative_map.values())
        return state

    def get_previous_state(self) -> List[Any]:
        """
        Get the current state based on the emotion reward map and initiative map.
        Example state: [anger_reward, disgust_reward, ..., anger_initiative, disgust_initiative, ...]
        """
        return self.previous_state

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

    def remember(self, previous_state, action, reward, current_state, done):
        """Store experiences in memory."""
        self.memory.append((previous_state, action, reward, current_state, done))

    def get_llm_response_emotion(self) -> list[Any]:
        """
        Simulates generating an LLM response based on the chosen emotions.
        """
        # Choose emotions based on the Q-learning model
        emotions_to_use = self.choose_emotions_based_on_initiative()
        self.learn_from_inference()
        return emotions_to_use

    def update_emotion_and_initiative(self, user_prompt_emotion: str, feedback: float):
        """
        Update the reward and initiative maps based on user emotion and feedback (reward).
        :param user_prompt_emotion: The emotion detected from the user's prompt.
        :param feedback: The reward or penalty for the response.
        """
        self.previous_state = self.get_current_state()
        self.emotion_reward_map[user_prompt_emotion] += feedback  # Update rewards
        self.initiative_map[user_prompt_emotion] += 0.1  # Increase initiative for that emotion

    def learn_from_inference(self):
        # 0 = single strong emotion, 1 = two emotions, 2 = three emotions
        user_emotion = self.current_user_emotion  # Classify user's emotion
        # Simulate feedback (reward), and update the emotion maps
        feedback = random.uniform(-1, 1)  # Reward could be based on external feedback or satisfaction
        self.update_emotion_and_initiative(user_emotion, feedback)
        # Store state, action, and reward for replay
        current_state = self.get_current_state()
        action = self.act(current_state)
        self.remember(current_state, action, feedback, self.previous_state, done=False)
        # Perform replay to learn from the experiences
