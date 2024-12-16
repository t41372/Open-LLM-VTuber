import datetime
import uuid
import json
from typing import AsyncIterator

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


async def conversation_chain(
    self,
    user_input: str | np.ndarray,
    asr_engine: ASRInterface,
    llm_engine: LLMInterface,
    tts_engine: TTSInterface,
    live2d_model: Live2dModel,
    websocket_send: WebSocket.send,
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
    random_emoji = np.random.choice([
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🌵", "🎄", "🌲", "🌳", "🌴", "🌱", "🌿", "☘️", "🍀", 
        "🍂", "🍁", "🍄", "🌾", "💐", "🌹","🌸", 
        "🌛", "🌍", "⭐️", "🔥","🌈","🌩", "⛄️", "🎃", "🎄", "🎉", "🎏", "🎗", "🀄️", 
        "🎭", "🎨", "🧵", "🪡", "🧶", "🥽", "🥼", "🦺", "👔", "👕", 
        "👜", "👑", ])
    
    # Apply the color to the console output
    logger.info(f"New Conversation Chain {random_emoji} started!")

    # if user_input is not string, make it string
    if user_input is None:
        logger.warning("❓User input is None. Aborting conversation.")
    elif isinstance(user_input, np.ndarray):
        print("transcribing...")
        user_input: str = await asr_engine.async_transcribe_np(user_input)

    print(f"User input: {user_input}")

    chat_completion: AsyncIterator[str] = await llm_engine.async_chat_iter(user_input)

    full_response: str = ""
    sentence_buffer: str = ""
    async for token in chat_completion:
        sentence_buffer += token
        full_response += token
        if is_complete_sentence(sentence_buffer) and sentence_buffer.strip():
            await speak(
                sentence_buffer=sentence_buffer,
                live2d_model=live2d_model,
                tts_engine=tts_engine,
                websocket_send=websocket_send,
            )
            sentence_buffer = ""

    # If there's still something in the buffer, speak it
    if sentence_buffer:
        await speak(
            sentence_buffer=sentence_buffer,
            live2d_model=live2d_model,
            tts_engine=tts_engine,
            websocket_send=websocket_send,
        )
        
    logger.info(f"Conversation Chain {random_emoji} completed!")
    
    return full_response


async def speak(
    sentence_buffer: str,
    live2d_model: Live2dModel,
    tts_engine: TTSInterface,
    websocket_send: WebSocket.send,
) -> None:
    """
    Generate and stream the audio to the frontend
    
    Parameters:
    - sentence_buffer (str): The sentence to be spoken
    - live2d_model (Live2dModel): The Live2D model to use
    - tts_engine (TTSInterface): The TTS engine to use
    - websocket_send (WebSocket.send): The function to send the audio to the frontend
    """
    if not sentence_buffer or not sentence_buffer.strip():
        logger.error(
            f'TTS receives "{sentence_buffer}", which is empty. So nothing to be spoken.'
        )
        return
    logger.debug(f"🏃Generating audio for '''{sentence_buffer}'''...")

    emotion, sentence_buffer = live2d_model.extract_emotion(text=sentence_buffer)

    logger.debug(f"emotion: {emotion}, content: {sentence_buffer}")

    try:
        audio_file_path = await tts_engine.async_generate_audio(
            text=sentence_buffer, file_name_no_ext=f"{datetime.now().strftime("%Y%m%d_%H%M%S")}_{str(uuid.uuid4())[:8]}"
        )
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return
    
    try:
        audio_payload = prepare_audio_payload(
            audio_path=audio_file_path,
            display_text=sentence_buffer,
            expression_list=[emotion],
        )
    except Exception as e:
        logger.error(f"Error preparing audio payload: {e}")
        return
    logger.debug("Sending Audio payload.")
    await websocket_send(json.dumps(audio_payload))
    # clean up
    sentence_buffer = ""
    tts_engine.remove_file(audio_file_path)
    logger.debug("Payload sent. Audio cache file cleaned.")
