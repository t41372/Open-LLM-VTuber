import random

from Behavior.generic_behavior import GenericBehavior
from Emotion import EmotionHandler
from actions import TalkAction


class TalkBehavior(GenericBehavior):

    def __init__(self, learning_rate=0.001, dominant_prob=0.7):
        actions_map = {
            'talk': TalkAction()
        }
        actions = ['talk']
        super().__init__(actions, learning_rate, dominant_prob, actions_map)


# Example usage
if __name__ == "__main__":
    state_size = 1  # Example state size (emotions and initiatives)
    # Initialize A2C agent with dominant action probability of 70%
    a2c_agent = TalkBehavior()
    state = EmotionHandler().get_current_state()
    # Select an action based on current state
    action = a2c_agent.select_action(state)
    print(f"Selected action: {action}")
    next_state = EmotionHandler().get_current_state()
    # Simulated reward feedback
    reward = random.uniform(-1, 1)
    done = True  # Set to True if episode ends
    # Update the model with feedback
    a2c_agent.update(state, action, reward, next_state)
