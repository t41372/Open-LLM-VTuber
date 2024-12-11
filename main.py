import asyncio
import atexit
import threading

import discord
import yaml
from letta import create_client
from letta.schemas.embedding_config import EmbeddingConfig
from letta.schemas.llm_config import LLMConfig
from loguru import logger

from Behavior.TalkBehavior import TalkBehavior
from OpenLLMVtuber import OpenLLMVTuberMain
from server import WebSocketServer
from utils.ActionSelectionQueue import ActionSelectionQueue
from utils.DiscordVoiceTranscription import VoiceAudioBot
from utils.InferenceQueue import InferenceQueue
from utils.InputQueue import InputQueue
from utils.OutputQueue import OutputQueue
from utils.VoiceListener import VoiceListener

import dotenv

## Main Thread for program, also works as "main-loop" for inference, uses data from the StateInfo class

if __name__ == "__main__":
    with open("conf.yaml", "rb") as f:
        config = yaml.safe_load(f)
    dotenv.load_dotenv()
    server = WebSocketServer(open_llm_vtuber_config=config)
    server.start()
    vtuber_main = OpenLLMVTuberMain(config)
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
    client = VoiceAudioBot(intents=intents)
    client.run(BOT_TOKEN)

    action_selection_queue = ActionSelectionQueue(default_behavior=default_behavior)
    config["LIVE2D"] = True
  ##  main_loop = asyncio.new_event_loop()
    # make sure the live2d is enabled
    # Initialize and run the WebSocket server

    atexit.register(WebSocketServer.clean_cache)
    atexit.register(vtuber_main.clean_cache)


    def _run_conversation_chain():
      ##  asyncio.set_event_loop(main_loop)
      ##  main_loop.run_forever()
        try:
            action_selection_queue.start()
            prompt = inference_queue.get_prompt()
            inference_result = vtuber_main.conversation_chain(prompt)
            OutputQueue().add_output(inference_result)
        except Exception as e:
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
