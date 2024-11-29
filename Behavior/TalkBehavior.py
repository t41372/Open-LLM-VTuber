import random

from Behavior.generic_behavior import GenericBehavior
from actions.TalkAction import TalkAction
from utils.PromptLoader import PromptLoader


class TalkBehavior(GenericBehavior):

    def __init__(self, learning_rate=0.001, dominant_prob=0.7):
        self.action_context_prompt_file = r"C:\Users\Administrator\Desktop\AIVtuber\Open-LLM-VTuber\prompts\behavior\TalkBehavior"
        self.actions_map = {
            'talk': TalkAction()
        }
        self.actions = ['talk']

        super(TalkBehavior, self).__init__(self.actions, learning_rate, dominant_prob, self.actions_map)







