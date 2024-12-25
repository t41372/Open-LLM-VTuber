from datetime import datetime
import uuid
import json
import asyncio
from typing import AsyncIterator, List
import numpy as np
from loguru import logger
from fastapi import WebSocket

from .live2d_model import Live2dModel
from .asr.asr_interface import ASRInterface
from .llm.llm_interface import LLMInterface
from .tts.tts_interface import TTSInterface
from .translate.translate_interface import TranslateInterface
from .translate.translate_factory import TranslateFactory

from .utils.audio_preprocessor import audio_filter
from .utils.sentence_divider import is_complete_sentence
from .utils.stream_audio import prepare_audio_payload
from .chat_history_manager import store_message


class TTSTaskManager:
    def __init__(self):
        self.task_list: List[asyncio.Task] = []
        self.next_index_to_play: int = 0

    def clear(self):
        self.task_list.clear()
        self.next_index_to_play = 0

    async def speak(
        self,
        sentence_buffer: str,
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocket.send,
    ) -> None:
        if not sentence_buffer or not sentence_buffer.strip():
            logger.error(
                f'TTS receives "{sentence_buffer}", which is empty. So nothing to be spoken.'
            )
            return

        logger.debug(f"🏃Generating audio for '''{sentence_buffer}'''...")
        emotion = live2d_model.extract_emotion(str_to_check=sentence_buffer)
        logger.debug(f"emotion: {emotion}, content: {sentence_buffer}")

        current_task_index = len(self.task_list)
        tts_task = asyncio.create_task(
            tts_engine.async_generate_audio(
                text=sentence_buffer,
                file_name_no_ext=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}",
            )
        )
        self.task_list.append(tts_task)

        try:
            while current_task_index != self.next_index_to_play:
                await asyncio.sleep(0.01)

            audio_file_path = await tts_task

            try:
                audio_payload = prepare_audio_payload(
                    audio_path=audio_file_path,
                    display_text=sentence_buffer,
                    expression_list=[emotion],
                )
            except asyncio.CancelledError as e:
                logger.debug("TTS task cancelled.")
                raise e
            except Exception as e:
                logger.error(f"Error preparing audio payload: {e}")
                return

            logger.debug("Sending Audio payload.")
            await websocket_send(json.dumps(audio_payload))

            tts_engine.remove_file(audio_file_path)
            logger.debug("Payload sent. Audio cache file cleaned.")

            self.next_index_to_play += 1

            if current_task_index == len(self.task_list) - 1:
                self.clear()

        except Exception as e:
            logger.error(f"Error in speak function: {e}")
            self.next_index_to_play += 1


async def conversation_chain(
    user_input: str | np.ndarray,
    asr_engine: ASRInterface,
    llm_engine: LLMInterface,
    tts_engine: TTSInterface,
    live2d_model: Live2dModel,
    websocket_send: WebSocket.send,
    conf_uid: str = "",
    history_uid: str = "",
) -> str:
    """
    One iteration of the main conversation.
    1. Transcribe the user input (or use the input if it's already a string)
    2. Call the LLM with the user input
    3. Text to speech
    4. Send the audio via the websocket

    Parameters:
    - user_input (str, numpy array): The user input to be used in the conversation. If it's string, it will be considered as user input. If it's a numpy array, it will be transcribed. If it's None, we'll request input from the user.

    Returns:
    - str: The full response from the LLM
    """
    try:
        session_emoji = np.random.choice(EMOJI_LIST)

        await websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-start",
                }
            )
        )

        # Apply the color to the console output
        logger.info(f"New Conversation Chain {session_emoji} started!")

        # if user_input is not string, make it string
        if user_input is None:
            logger.warning("❓User input is None. Aborting conversation.")
            return ""
        elif isinstance(user_input, np.ndarray):
            print("transcribing...")
            user_input: str = await asr_engine.async_transcribe_np(user_input)

        store_message(conf_uid, history_uid, "human", user_input)
        await websocket_send(
            json.dumps({"type": "user-input-transcription", "text": user_input})
        )

        print(f"User input: {user_input}")

        tts_manager = TTSTaskManager()

        full_response: str = ""
        sentence_buffer: str = ""

        chat_completion: AsyncIterator[str] = llm_engine.async_chat_iter(user_input)

        async for token in chat_completion:
            sentence_buffer += token
            full_response += token
            if is_complete_sentence(sentence_buffer) and sentence_buffer.strip():
                await tts_manager.speak(
                    sentence_buffer=sentence_buffer,
                    live2d_model=live2d_model,
                    tts_engine=tts_engine,
                    websocket_send=websocket_send,
                )
                sentence_buffer = ""

        if sentence_buffer:
            await tts_manager.speak(
                sentence_buffer=sentence_buffer,
                live2d_model=live2d_model,
                tts_engine=tts_engine,
                websocket_send=websocket_send,
            )

        # Wait for all TTS tasks to complete
        if tts_manager.task_list:
            await asyncio.gather(*tts_manager.task_list)

        # store the full response in the case we are not interrupted
        if full_response:
            store_message(conf_uid, history_uid, "ai", full_response)
            logger.info(f"💾 Stored AI message: '''{full_response}'''")

    except asyncio.CancelledError:
        logger.info(f"🤡👍 Conversation {session_emoji} cancelled because interrupted.")
        # We need to store the partial response outside this function (because it's
        # a part of the interruption-signal from the frontend and we don't
        # have access to it here)

    finally:
        logger.debug(f"🧹 Clearing up conversation {session_emoji}.")
        tts_manager.clear()

        await websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-end",
                }
            )
        )
        logger.info(f"😎👍✅ Conversation Chain {session_emoji} completed!")
        return full_response


EMOJI_LIST = [
    "🐶",
    "🐱",
    "🐭",
    "🐹",
    "🐰",
    "🦊",
    "🐻",
    "🐼",
    "🐨",
    "🐯",
    "🦁",
    "🐮",
    "🐷",
    "🐸",
    "🐵",
    "🐔",
    "🐧",
    "🐦",
    "🐤",
    "🐣",
    "🐥",
    "🦆",
    "🦅",
    "🦉",
    "🦇",
    "🐺",
    "🐗",
    "🐴",
    "🦄",
    "🐝",
    "🌵",
    "🎄",
    "🌲",
    "🌳",
    "🌴",
    "🌱",
    "🌿",
    "☘️",
    "🍀",
    "🍂",
    "🍁",
    "🍄",
    "🌾",
    "💐",
    "🌹",
    "🌸",
    "🌛",
    "🌍",
    "⭐️",
    "🔥",
    "🌈",
    "🌩",
    "⛄️",
    "🎃",
    "🎄",
    "🎉",
    "🎏",
    "🎗",
    "🀄️",
    "🎭",
    "🎨",
    "🧵",
    "🪡",
    "🧶",
    "🥽",
    "🥼",
    "🦺",
    "👔",
    "👕",
    "👜",
    "👑",
]
