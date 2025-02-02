from datetime import datetime
import uuid
import json
import asyncio
from typing import AsyncIterator, List, Dict, Union, Any, Callable, Optional
import numpy as np
from loguru import logger
from fastapi import WebSocket
import random
import itertools
import base64
from dataclasses import dataclass

from .live2d_model import Live2dModel
from .asr.asr_interface import ASRInterface
from .agent.agents.agent_interface import AgentInterface
from .agent.output_types import BaseOutput, SentenceOutput, AudioOutput, Actions, DisplayText
from .agent.input_types import BatchInput, TextData, ImageData, TextSource, ImageSource
from .tts.tts_interface import TTSInterface

from .utils.stream_audio import prepare_audio_payload
from .chat_history_manager import store_message
from .service_context import ServiceContext
from .message_handler import message_handler


@dataclass
class BroadcastContext:
    """Context for broadcasting messages in group chat"""
    broadcast_func: Optional[Callable] = None
    group_members: Optional[List[str]] = None
    current_client_uid: Optional[str] = None


class TTSTaskManager:
    """Manages TTS tasks and their sequential execution"""

    def __init__(self):
        self.task_list = []
        self._lock = asyncio.Lock()

    async def speak(
        self,
        tts_text: str,
        display_text: DisplayText,
        actions: Actions | None,
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocket.send,
        broadcast_ctx: BroadcastContext = None,
    ) -> None:
        """Generate and send audio for a sentence."""
        if not tts_text or not tts_text.strip():
            logger.debug("Empty TTS text, sending silent display payload")
            audio_payload = prepare_audio_payload(
                audio_path=None,
                display_text=display_text,
                actions=actions,
            )
            await websocket_send(json.dumps(audio_payload))
            return

        logger.debug(f"🏃Generating audio for '''{tts_text}''' (by {display_text.name})")

        async with self._lock:
            task = asyncio.create_task(
                self._process_tts(
                    tts_text,
                    display_text,
                    actions,
                    live2d_model,
                    tts_engine,
                    websocket_send,
                )
            )
            self.task_list.append(task)

    def clear(self):
        self.task_list = []

    async def _process_tts(
        self,
        tts_text: str,
        display_text: DisplayText,
        actions: Actions | None,
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocket.send,
    ) -> None:
        """Process TTS generation and send audio to the frontend."""
        audio_file_path = None
        try:
            logger.debug(f"🏃Generating audio for '''{tts_text}'''...")

            audio_file_path = await tts_engine.async_generate_audio(
                text=tts_text,
                file_name_no_ext=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}",
            )

            # Prepare audio payload
            audio_payload = prepare_audio_payload(
                audio_path=audio_file_path,
                display_text=display_text,
                actions=actions,
            )

            # Send to current client
            logger.debug("Sending Audio payload.")
            await websocket_send(json.dumps(audio_payload))

        except Exception as e:
            logger.error(f"Error preparing audio payload: {e}")
            # Send a silent payload to maintain conversation flow
            error_payload = prepare_audio_payload(
                audio_path=None,
                display_text=display_text,
                actions=actions,
            )
            await websocket_send(json.dumps(error_payload))
        finally:
            if audio_file_path:
                tts_engine.remove_file(audio_file_path)
                logger.debug("Audio cache file cleaned.")

async def _process_agent_output(
    output: BaseOutput,
    tts_manager: TTSTaskManager,
    live2d_model: Live2dModel,
    tts_engine: TTSInterface,
    websocket_send: WebSocket.send,
    broadcast_ctx: BroadcastContext = None,
) -> str:
    """Process a single agent output and return the response text"""
    full_response = ""

    if isinstance(output, SentenceOutput):
        async for display_text, tts_text, actions in output:
            full_response += display_text.text
            await tts_manager.speak(
                tts_text=tts_text,
                display_text=display_text,
                actions=actions,
                live2d_model=live2d_model,
                tts_engine=tts_engine,
                websocket_send=websocket_send,
                broadcast_ctx=broadcast_ctx,
            )
    elif isinstance(output, AudioOutput):
        async for audio_path, display_text, transcript, actions in output:
            full_response += display_text.text
            audio_payload = prepare_audio_payload(
                audio_path=audio_path,
                display_text=display_text,
                actions=actions
            )
            await websocket_send(json.dumps(audio_payload))

    return full_response


async def _finalize_conversation_turn(
    tts_manager: TTSTaskManager,
    websocket_send: WebSocket.send,
    client_uid: str,
    character_name: str = "",
    broadcast_ctx: BroadcastContext = None,
    session_emoji: str = "",
) -> bool:
    """
    Finalize a conversation turn by:
    1. Waiting for TTS tasks to complete
    2. Sending backend-synth-complete signal
    3. Waiting for frontend playback to complete
    4. Sending force-new-message and conversation-chain-end signals
    5. Broadcasting signals to group members if in group chat

    Args:
        tts_manager: TTS task manager instance
        websocket_send: WebSocket send function
        client_uid: Client identifier
        character_name: Optional character name for logging
        broadcast_ctx: Optional broadcast context for group chat
        session_emoji: Optional emoji for logging

    Returns:
        bool: True if the turn was successfully finalized
    """
    if not tts_manager.task_list:
        logger.warning(
            f"No TTS tasks found{f' for {character_name}' if character_name else ''}"
        )
        return False

    await asyncio.gather(*tts_manager.task_list)

    # Send backend-synth-complete to current client
    synth_complete_msg = {"type": "backend-synth-complete"}
    await websocket_send(json.dumps(synth_complete_msg))

    response = await message_handler.wait_for_response(
        client_uid, "frontend-playback-complete"
    )

    if response:
        # Send force-new-message to current client and group
        force_new_msg = {"type": "force-new-message"}
        await websocket_send(json.dumps(force_new_msg))
        if broadcast_ctx and broadcast_ctx.broadcast_func and broadcast_ctx.group_members:
            await broadcast_ctx.broadcast_func(
                broadcast_ctx.group_members,
                force_new_msg,
                broadcast_ctx.current_client_uid,
            )

        logger.info(
            f"Frontend playback complete for {client_uid}{f', {character_name}' if character_name else ''}"
        )

        await websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-end",
                }
            )
        )
        
        if broadcast_ctx and broadcast_ctx.broadcast_func and broadcast_ctx.group_members:
            await broadcast_ctx.broadcast_func(
                broadcast_ctx.group_members,
                {
                    "type": "control",
                    "text": "conversation-chain-end",
                }
            )

        logger.info(f"😎👍✅ Conversation Chain {session_emoji} completed!")
        
        return True

    logger.warning(f"No playback completion response from {client_uid}")
    return False


async def conversation_chain(
    user_input: Union[str, np.ndarray],
    asr_engine: ASRInterface,
    agent_engine: AgentInterface,
    tts_engine: TTSInterface,
    live2d_model: Live2dModel,
    websocket_send: WebSocket.send,
    conf_uid: str = "",
    history_uid: str = "",
    images: List[Dict[str, Any]] = None,
    client_uid: str = "",
    character_name: str = "AI",
) -> str:
    """
    One iteration of the main conversation chain.

    Args:
        user_input: User input (string or audio array)
        asr_engine: ASR engine instance
        agent_engine: Agent instance
        tts_engine: TTS engine instance
        live2d_model: Live2D model instance
        websocket_send: WebSocket send function
        conf_uid: Configuration ID
        history_uid: History ID
        images: Optional list of image data from frontend
        client_uid: Client ID
    Returns:
        str: Complete response from the agent
    """
    tts_manager = TTSTaskManager()
    full_response: str = ""

    try:
        session_emoji = np.random.choice(EMOJI_LIST)

        await websocket_send(
            json.dumps({
                "type": "control",
                "text": "conversation-chain-start",
            })
        )

        await websocket_send(
            json.dumps({"type": "full-text", "text": "Thinking..."})
        )

        logger.info(f"New Conversation Chain {session_emoji} started!")

        # Handle audio input
        input_text = user_input
        if isinstance(user_input, np.ndarray):
            logger.info("Transcribing audio input...")
            input_text = await asr_engine.async_transcribe_np(user_input)
            await websocket_send(
                json.dumps({"type": "user-input-transcription", "text": input_text})
            )

        # Prepare BatchInput
        batch_input = BatchInput(
            texts=[TextData(source=TextSource.INPUT, content=input_text, from_name=character_name)],
            images=(
                [ImageData(source=ImageSource(img["source"]), data=img["data"], mime_type=img["mime_type"]) 
                 for img in (images or [])]
                if images else None
            ),
        )

        store_message(conf_uid, history_uid, "human", input_text)
        logger.info(f"User input: {input_text}")
        if images:
            logger.info(f"With {len(images)} images")

        try:
            # Process agent output
            agent_output: AsyncIterator[BaseOutput] = agent_engine.chat(batch_input)
            async for output in agent_output:
                try:
                    full_response += await _process_agent_output(
                        output,
                        tts_manager,
                        live2d_model,
                        tts_engine,
                        websocket_send,
                        None,
                    )
                except Exception as e:
                    logger.error(f"Error processing output: {e}")
                    raise
        except Exception as e:
            logger.error(f"Error in agent chat: {e}")
            raise

        # After all TTS tasks complete
        if tts_manager.task_list:
            await _finalize_conversation_turn(
                tts_manager,
                websocket_send,
                client_uid,
                session_emoji=session_emoji
            )
        else:
            logger.warning("No TTS tasks found")

        if full_response:
            store_message(conf_uid, history_uid, "ai", full_response)
            logger.info(f"💾 Stored AI message: '''{full_response}'''")

        return full_response

    except asyncio.CancelledError:
        logger.info(f"🤡👍 Conversation {session_emoji} cancelled because interrupted.")
    except Exception as e:
        logger.error(f"Error in conversation chain: {e}")
        raise
    finally:
        logger.debug(f"🧹 Clearing up conversation {session_emoji}.")
        tts_manager.clear()


async def group_conversation_chain(
    user_input: Union[str, np.ndarray],
    initiator_client_uid: str,
    client_contexts: Dict[str, ServiceContext],
    client_connections: Dict[str, WebSocket],
    asr_engine: ASRInterface,
    tts_engine: TTSInterface,
    websocket_send: WebSocket.send,
    broadcast_func: Callable,
    group_members: List[str],
    images: List[Dict[str, Any]] = None,
) -> None:
    """
    Group conversation chain where multiple AI characters take turns to speak.
    Updated to use a queue and per-AI memory to pass only "new" conversation history.
    """
    session_emoji = np.random.choice(EMOJI_LIST)
    # Global conversation history, starting with human input
    conversation_history = [f"Human: {user_input}"]
    # Memory index for each AI: indicates the index of conversation_history that the AI has already seen
    memory_index = {uid: 0 for uid in group_members}
    # Initialize speaking queue with the group_members order
    group_queue = list(group_members)

    try:
        logger.info(f"Group Conversation Chain {session_emoji} started!")

        # Handle audio input: if audio, transcribe and send transcription to all members.
        input_text = user_input
        if isinstance(user_input, np.ndarray):
            logger.info("Transcribing audio input...")
            input_text = await asr_engine.async_transcribe_np(user_input)
            # Broadcast transcription to all members
            await broadcast_func(
                group_members,
                {
                    "type": "user-input-transcription",
                    "text": input_text,
                }
            )

        else:
            await broadcast_func(
                group_members,
                {
                    "type": "user-input-transcription",
                    "text": input_text,
                },
                initiator_client_uid,
            )
        # Update the human input in conversation history (optional, if transcription differs)
        conversation_history[0] = f"Human: {input_text}"

        while group_queue:
            try:
                await broadcast_func(
                    group_members,
                    {
                        "type": "control",
                        "text": "conversation-chain-start",
                    }
                )

                await broadcast_func(
                    group_members,
                    {
                        "type": "full-text",
                        "text": "Thinking...",
                    }
                )
                current_client_uid = group_queue.pop(0)
                context = client_contexts[current_client_uid]
                current_ws_send = client_connections[current_client_uid].send_text

                # Get new messages for this AI
                new_messages_list = conversation_history[memory_index[current_client_uid]:]
                new_context = "\n".join(new_messages_list) if new_messages_list else ""

                batch_input = BatchInput(
                    texts=[TextData(
                        source=TextSource.INPUT, 
                        content=new_context,
                        from_name=context.character_config.conf_name
                    )],
                    images=(
                        [ImageData(source=ImageSource(img["source"]), data=img["data"], mime_type=img["mime_type"]) 
                         for img in (images or [])]
                        if images else None
                    ),
                )

                logger.info(f"AI {context.character_config.conf_name} (client {current_client_uid}) "
                           f"receiving context:\n{new_context}")

                tts_manager = TTSTaskManager()
                # Store full response for current AI turn
                full_response = ""

                try:
                    # Process agent output using only the new context for the current AI
                    agent_output: AsyncIterator[BaseOutput] = context.agent_engine.chat(batch_input)

                    broadcast_ctx = BroadcastContext(
                        broadcast_func=broadcast_func,
                        group_members=group_members,
                        current_client_uid=current_client_uid,
                    )

                    async for output in agent_output:
                        full_response += await _process_agent_output(
                            output,
                            tts_manager,
                            context.live2d_model,
                            context.tts_engine,
                            current_ws_send,
                            broadcast_ctx,
                        )

                    # After processing all outputs, append the complete response to conversation history
                    if full_response:
                        ai_message = f"{context.character_config.conf_name}: {full_response}"
                        conversation_history.append(ai_message)
                        logger.info(f"Appended complete response: {ai_message}")

                    if tts_manager.task_list:
                        await asyncio.gather(*tts_manager.task_list)
                        await current_ws_send(json.dumps({
                            "type": "backend-synth-complete"
                        }))

                        await _finalize_conversation_turn(
                            tts_manager,
                            current_ws_send,
                            current_client_uid,
                            context.character_config.conf_name,
                            broadcast_ctx,
                            session_emoji,
                        )
                    else:
                        logger.warning(f"No TTS tasks found for {context.character_config.conf_name}")

                    # Update the memory pointer for the current AI
                    memory_index[current_client_uid] = len(conversation_history)

                except asyncio.CancelledError:
                    logger.info(f"🛑 AI {context.character_config.conf_name}'s turn was interrupted")
                    # Clean up the current turn
                    tts_manager.clear()
                    # Re-raise to handle at outer level
                    raise
                except Exception as e:
                    logger.error(f"Error during AI {context.character_config.conf_name} response: {e}")
                    conversation_history.append(f"[System: {context.character_config.conf_name} encountered an error: {str(e)}]")
                finally:
                    tts_manager.clear()

                # After current AI's turn, push it back to the end of the queue
                group_queue.append(current_client_uid)

            except asyncio.CancelledError:
                logger.info(f"🛑 AI {context.character_config.conf_name}'s turn was interrupted")
                # Clean up the current turn
                tts_manager.clear()
                # Re-raise to handle at outer level
                raise
            except Exception as e:
                logger.error(f"Error during AI {context.character_config.conf_name} response: {e}")
                conversation_history.append(f"[System: {context.character_config.conf_name} encountered an error: {str(e)}]")
            finally:
                tts_manager.clear()

    except asyncio.CancelledError:
        logger.info(
            f"🤡👍 Group Conversation {session_emoji} cancelled because interrupted."
        )
        # Send conversation-chain-end to all members
        await broadcast_func(
            group_members,
            {
                "type": "control",
                "text": "conversation-chain-end",
            }
        )
    finally:
        logger.debug(f"🧹 Clearing up group conversation {session_emoji}.")
        logger.info(f"😎👍✅ Group Conversation Chain {session_emoji} completed!")


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
