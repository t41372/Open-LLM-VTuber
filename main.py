import atexit
import threading
import time

import discord
import dotenv
import yaml
from loguru import logger

from Behavior.TalkBehavior import TalkBehavior
from Emotion.EmotionHandler import EmotionHandler
from OpenLLMVtuber import OpenLLMVTuberMain
from server import WebSocketServer
from utils.ActionSelectionQueue import ActionSelectionQueue
from utils.DiscordVoiceTranscription import VoiceActivityBot
from utils.InferenceQueue import InferenceQueue
from utils.InputQueue import InputQueue
from utils.OutputQueue import OutputQueue
from utils.StateInfo import StateInfo
from utils.VoiceListener import VoiceListener

## Main Thread for program, also works as "main-loop" for inference, uses data from the StateInfo class

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)
    dotenv.load_dotenv()

    vtuber_main = OpenLLMVTuberMain(config)
    voice_interface = "discord"
    state_info = StateInfo()
    state_info.set_voice_interface(voice_interface)
    listener = VoiceListener(config)
    input_queue = InputQueue()
    default_behavior = TalkBehavior()
    inference_queue = InferenceQueue()

    ## discord bot spec

    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    intents.voice_states = True
    intents.message_content = True
    discord_client = VoiceActivityBot(intents=intents)
    emotion_handler = EmotionHandler()

    ## live2d model
    action_selection_queue = ActionSelectionQueue(default_behavior=default_behavior)
    config["LIVE2D"] = True

    atexit.register(vtuber_main.clean_cache)


    def _run_conversation_chain():
        try:
            listener.start()
            action_selection_queue.start()
            while True:  # Loop to keep running the conversation chain
                prompt = inference_queue.get_prompt()
                vtuber_main.conversation_chain(prompt)
        except Exception as e:
            logger.error(f"😢Conversation was interrupted. {e}")
        finally:
            listener.stop()
            action_selection_queue.stop()
            logger.info("Listener and action selection queue stopped.")


    while True:
        logger.critical("tts on: ", vtuber_main.config.get("TTS_ON", False))
        if not vtuber_main.config.get("TTS_ON", False):
            logger.error("its indeed off")
        else:
            threading.Thread(name='Main LLM Thread', target=_run_conversation_chain).start()
            if input(">>> say i and press enter to interrupt: ") == "i":
                logger.error("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
                vtuber_main.interrupt()
