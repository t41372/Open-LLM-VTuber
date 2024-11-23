import atexit
import threading

import torch
import yaml
from transformers import pipeline

from Behavior.TalkBehavior import TalkBehavior
from OpenLLMVtuber import OpenLLMVTuberMain
from server import WebSocketServer
from utils.ActionSelectionQueue import ActionSelectionQueue
from utils.InferenceQueue import InferenceQueue
from utils.InputQueue import InputQueue
from utils.VoiceListener import VoiceListener
from loguru import logger

## Main Thread for program, also works as "main-loop" for inference, uses data from the StateInfo class

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)

    server = WebSocketServer(open_llm_vtuber_config=config)
    server.start()
    vtuber_main = OpenLLMVTuberMain(config)
    listener = VoiceListener(config)
    input_queue = InputQueue()
    default_behavior = TalkBehavior()
    inference_queue = InferenceQueue()
    action_selection_queue = ActionSelectionQueue(default_behavior=default_behavior)
    config["LIVE2D"] = True
    # make sure the live2d is enabled
    # Initialize and run the WebSocket server

    atexit.register(WebSocketServer.clean_cache)
    atexit.register(vtuber_main.clean_cache)


    def _run_conversation_chain():
        try:
            action_selection_queue.start()
        except InterruptedError as e:
            logger.error(f"😢Conversation was interrupted. {e}")
            listener.stop()
    while True:
        logger.critical("tts on: ", vtuber_main.config.get("TTS_ON", False))
        if not vtuber_main.config.get("TTS_ON", False):
            logger.error("its indeed off")
        else:
            listener.start()
            threading.Thread(name='Main LLM Thread', target=_run_conversation_chain).start()
            if input(">>> say i and press enter to interrupt: ") == "i":
                logger.error("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
                vtuber_main.interrupt()
