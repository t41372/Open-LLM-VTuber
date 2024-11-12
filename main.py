import atexit
import threading

import yaml

from Behavior.TalkBehavior import TalkBehavior
from OpenLLMVtuber import OpenLLMVTuberMain
from server import WebSocketServer
from utils.ActionSelectionQueue import ActionSelectionQueue
from utils.InputQueue import InputQueue
from utils.VoiceListener import VoiceListener

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)

    vtuber_main = OpenLLMVTuberMain(config)
    listener = VoiceListener(config)
    input_queue = InputQueue()
    default_behavior = TalkBehavior()
    action_selection_queue = ActionSelectionQueue(default_behavior=default_behavior)
    config["LIVE2D"] = True  # make sure the live2d is enabled
    # Initialize and run the WebSocket server
    server = WebSocketServer(open_llm_vtuber_config=config)
    server.start()
    atexit.register(WebSocketServer.clean_cache)
    atexit.register(vtuber_main.clean_cache)

    def _run_conversation_chain():
        try:

            action_selection_queue.start()
        except InterruptedError as e:
            print(f"😢Conversation was interrupted. {e}")
            listener.stop()
    while True:
        print("tts on: ", vtuber_main.config.get("TTS_ON", False))
        if not vtuber_main.config.get("TTS_ON", False):
            print("its indeed off")
        else:
            input_queue.start()
            listener.start()
            threading.Thread(name='Main LLM Thread', target=_run_conversation_chain).start()
            if input(">>> say i and press enter to interrupt: ") == "i":
                print("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
                vtuber_main.interrupt()
