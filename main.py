import atexit
import threading

import yaml

from Behavior.TalkBehavior import TalkBehavior
from OpenLLMVtuber import OpenLLMVTuberMain
from utils.ActionSelectionQueue import ActionSelectionQueue
from utils.InputQueue import InputQueue
from utils.VoiceListener import VoiceListener

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)

    vtuber_main = OpenLLMVTuberMain(config)
    listener = VoiceListener(config)
    input_queue = InputQueue()
    input_queue.start()
    listener.start()
    atexit.register(vtuber_main.clean_cache)
    main_queue = ActionSelectionQueue(default_behavior=TalkBehavior())


    def _run_conversation_chain():
        try:
            vtuber_main.conversation_chain()
        except InterruptedError as e:
            print(f"😢Conversation was interrupted. {e}")
            listener.stop()
            listener.join()  # Ensure the thread has fully stopped
    while True:
        print("tts on: ", vtuber_main.config.get("TTS_ON", False))
        if not vtuber_main.config.get("TTS_ON", False):
            print("its indeed off")
            vtuber_main.conversation_chain()
        else:
            listener.start()
            threading.Thread(name='Main LLM Thread', target=_run_conversation_chain).start()
            if input(">>> say i and press enter to interrupt: ") == "i":
                print("\n\n!!!!!!!!!! interrupt !!!!!!!!!!!!...\n")
                vtuber_main.interrupt()
