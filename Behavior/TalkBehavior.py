import random

from Behavior.generic_behavior import GenericBehavior
from actions.TalkAction import TalkAction


class TalkBehavior(GenericBehavior):

    def __init__(self, learning_rate=0.001, dominant_prob=0.7):
        actions_map = {
            'talk': TalkAction()
        }
        actions = ['talk']
        super().__init__(actions, learning_rate, dominant_prob, actions_map)

