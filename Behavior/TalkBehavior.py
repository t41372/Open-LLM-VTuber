import random

from Behavior.generic_behavior import GenericBehavior
from actions.TalkAction import TalkAction


class TalkBehavior(GenericBehavior):

    def __init__(self, learning_rate=0.001, dominant_prob=0.7):
        self.actions_map = {
            'talk': TalkAction()
        }
        self.actions = ['talk']
        super(TalkBehavior, self).__init__(self.actions, learning_rate, dominant_prob,self.actions_map)
