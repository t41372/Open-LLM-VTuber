from datetime import datetime
import uuid
import json
import asyncio
from typing import (
    List,
    Dict,
    Union,
    Any,
    Callable,
    Optional,
    TypedDict,
    Awaitable,
)
import numpy as np
from loguru import logger
from fastapi import WebSocket
from pydantic import BaseModel
from dataclasses import dataclass

from .live2d_model import Live2dModel
from .asr.asr_interface import ASRInterface
from .agent.agents.agent_interface import AgentInterface
from .agent.output_types import (
    BaseOutput,
    SentenceOutput,
    AudioOutput,
    Actions,
    DisplayText,
)
from .agent.input_types import BatchInput, TextData, ImageData, TextSource, ImageSource
from .tts.tts_interface import TTSInterface
from .utils.stream_audio import prepare_audio_payload
from .chat_history_manager import store_message
from .service_context import ServiceContext
from .message_handler import message_handler

# Type definitions
WebSocketSend = Callable[[str], Awaitable[None]]
BroadcastFunc = Callable[[List[str], dict, Optional[str]], Awaitable[None]]


class AudioPayload(TypedDict):
    """Type definition for audio payload"""

    type: str
    audio: Optional[str]
    volumes: Optional[List[float]]
    slice_length: Optional[int]
    display_text: Optional[DisplayText]
    actions: Optional[Actions]
    forwarded: Optional[bool]


@dataclass
class BroadcastContext:
    """Context for broadcasting messages in group chat"""

    broadcast_func: Optional[BroadcastFunc] = None
    group_members: Optional[List[str]] = None
    current_client_uid: Optional[str] = None


class ConversationConfig(BaseModel):
    """Configuration for conversation chain"""

    conf_uid: str = ""
    history_uid: str = ""
    client_uid: str = ""
    character_name: str = "AI"


class GroupConversationState(BaseModel):
    """State for group conversation"""

    conversation_history: List[str] = []
    memory_index: Dict[str, int] = {}
    group_queue: List[str] = []
    session_emoji: str = ""


class TTSTaskManager:
    """Manages TTS tasks and their sequential execution"""

    def __init__(self) -> None:
        self.task_list: List[asyncio.Task] = []
        self._lock = asyncio.Lock()

    async def speak(
        self,
        tts_text: str,
        display_text: DisplayText,
        actions: Optional[Actions],
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
        broadcast_ctx: Optional[BroadcastContext] = None,
    ) -> None:
        """
        Generate and send audio for a sentence.

        Args:
            tts_text: Text to synthesize
            display_text: Text to display
            actions: Live2D model actions
            live2d_model: Live2D model instance
            tts_engine: TTS engine instance
            websocket_send: WebSocket send function
            broadcast_ctx: Optional broadcast context for group chat
        """
        if not tts_text or not tts_text.strip():
            logger.debug("Empty TTS text, sending silent display payload")
            await self._send_silent_payload(display_text, actions, websocket_send)
            return

        logger.debug(
            f"🏃Generating audio for '''{tts_text}''' (by {display_text.name})"
        )

        async with self._lock:
            task = asyncio.create_task(
                self._process_tts(
                    tts_text=tts_text,
                    display_text=display_text,
                    actions=actions,
                    live2d_model=live2d_model,
                    tts_engine=tts_engine,
                    websocket_send=websocket_send,
                )
            )
            self.task_list.append(task)

    async def _send_silent_payload(
        self,
        display_text: DisplayText,
        actions: Optional[Actions],
        websocket_send: WebSocketSend,
    ) -> None:
        """Send a silent audio payload"""
        audio_payload = prepare_audio_payload(
            audio_path=None,
            display_text=display_text,
            actions=actions,
        )
        await websocket_send(json.dumps(audio_payload))

    async def _process_tts(
        self,
        tts_text: str,
        display_text: DisplayText,
        actions: Optional[Actions],
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
    ) -> None:
        """Process TTS generation and send audio to the frontend"""
        audio_file_path = None
        try:
            audio_file_path = await self._generate_audio(tts_engine, tts_text)
            await self._send_audio_payload(
                audio_file_path, display_text, actions, websocket_send
            )
        except Exception as e:
            logger.error(f"Error preparing audio payload: {e}")
            await self._send_silent_payload(display_text, actions, websocket_send)
        finally:
            if audio_file_path:
                tts_engine.remove_file(audio_file_path)
                logger.debug("Audio cache file cleaned.")

    async def _generate_audio(self, tts_engine: TTSInterface, text: str) -> str:
        """Generate audio file from text"""
        logger.debug(f"🏃Generating audio for '''{text}'''...")
        return await tts_engine.async_generate_audio(
            text=text,
            file_name_no_ext=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}",
        )

    async def _send_audio_payload(
        self,
        audio_path: str,
        display_text: DisplayText,
        actions: Optional[Actions],
        websocket_send: WebSocketSend,
    ) -> None:
        """Send audio payload to client"""
        audio_payload = prepare_audio_payload(
            audio_path=audio_path,
            display_text=display_text,
            actions=actions,
        )
        logger.debug("Sending Audio payload.")
        await websocket_send(json.dumps(audio_payload))

    def clear(self) -> None:
        """Clear all pending tasks"""
        self.task_list.clear()


async def _process_agent_output(
    output: BaseOutput,
    tts_manager: TTSTaskManager,
    live2d_model: Live2dModel,
    tts_engine: TTSInterface,
    websocket_send: WebSocketSend,
    broadcast_ctx: Optional[BroadcastContext] = None,
) -> str:
    """
    Process a single agent output and return the response text.

    Args:
        output: Agent output to process
        tts_manager: TTS task manager instance
        live2d_model: Live2D model instance
        tts_engine: TTS engine instance
        websocket_send: WebSocket send function
        broadcast_ctx: Optional broadcast context for group chat

    Returns:
        str: Accumulated response text
    """
    full_response = ""

    try:
        if isinstance(output, SentenceOutput):
            full_response = await _handle_sentence_output(
                output,
                tts_manager,
                live2d_model,
                tts_engine,
                websocket_send,
                broadcast_ctx,
            )
        elif isinstance(output, AudioOutput):
            full_response = await _handle_audio_output(output, websocket_send)
        else:
            logger.warning(f"Unknown output type: {type(output)}")
    except Exception as e:
        logger.error(f"Error processing agent output: {e}")
        # Send error message to client
        await websocket_send(
            json.dumps(
                {"type": "error", "message": f"Error processing response: {str(e)}"}
            )
        )

    return full_response


async def _handle_sentence_output(
    output: SentenceOutput,
    tts_manager: TTSTaskManager,
    live2d_model: Live2dModel,
    tts_engine: TTSInterface,
    websocket_send: WebSocketSend,
    broadcast_ctx: Optional[BroadcastContext],
) -> str:
    """Handle sentence output type"""
    full_response = ""
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
    return full_response


async def _handle_audio_output(
    output: AudioOutput,
    websocket_send: WebSocketSend,
) -> str:
    """Handle audio output type"""
    full_response = ""
    async for audio_path, display_text, transcript, actions in output:
        full_response += display_text.text
        audio_payload = prepare_audio_payload(
            audio_path=audio_path, display_text=display_text, actions=actions
        )
        await websocket_send(json.dumps(audio_payload))
    return full_response


async def _finalize_conversation_turn(
    tts_manager: TTSTaskManager,
    websocket_send: WebSocketSend,
    client_uid: str,
    character_name: str = "",
    broadcast_ctx: Optional[BroadcastContext] = None,
    session_emoji: str = "",
) -> bool:
    """
    Finalize a conversation turn by handling TTS tasks and sending completion signals.

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

    try:
        await asyncio.gather(*tts_manager.task_list)
        await _send_completion_signals(
            websocket_send, client_uid, character_name, broadcast_ctx, session_emoji
        )
        return True
    except Exception as e:
        logger.error(f"Error finalizing conversation turn: {e}")
        return False


async def _send_completion_signals(
    websocket_send: WebSocketSend,
    client_uid: str,
    character_name: str,
    broadcast_ctx: Optional[BroadcastContext],
    session_emoji: str,
) -> None:
    """Send completion signals to client and group members"""
    # Send backend-synth-complete
    await websocket_send(json.dumps({"type": "backend-synth-complete"}))

    # Wait for frontend playback completion
    response = await message_handler.wait_for_response(
        client_uid, "frontend-playback-complete"
    )

    if not response:
        logger.warning(f"No playback completion response from {client_uid}")
        return

    # Send force-new-message
    force_new_msg = {"type": "force-new-message"}
    await websocket_send(json.dumps(force_new_msg))

    # Broadcast to group if in group chat
    if broadcast_ctx and broadcast_ctx.broadcast_func and broadcast_ctx.group_members:
        await broadcast_ctx.broadcast_func(
            broadcast_ctx.group_members,
            force_new_msg,
            broadcast_ctx.current_client_uid,
        )

    logger.info(
        f"Frontend playback complete for {client_uid}"
        f"{f', {character_name}' if character_name else ''}"
    )

    # Send conversation-chain-end
    await _send_chain_end_signal(websocket_send, broadcast_ctx, session_emoji)


async def _send_chain_end_signal(
    websocket_send: WebSocketSend,
    broadcast_ctx: Optional[BroadcastContext],
    session_emoji: str,
) -> None:
    """Send conversation chain end signal"""
    chain_end_msg = {
        "type": "control",
        "text": "conversation-chain-end",
    }

    await websocket_send(json.dumps(chain_end_msg))

    if broadcast_ctx and broadcast_ctx.broadcast_func and broadcast_ctx.group_members:
        await broadcast_ctx.broadcast_func(
            broadcast_ctx.group_members,
            chain_end_msg,
        )

    logger.info(f"😎👍✅ Conversation Chain {session_emoji} completed!")


def _create_batch_input(
    input_text: str,
    images: Optional[List[Dict[str, Any]]],
    character_name: str,
) -> BatchInput:
    """Create batch input for agent processing"""
    return BatchInput(
        texts=[
            TextData(
                source=TextSource.INPUT, content=input_text, from_name=character_name
            )
        ],
        images=(
            [
                ImageData(
                    source=ImageSource(img["source"]),
                    data=img["data"],
                    mime_type=img["mime_type"],
                )
                for img in (images or [])
            ]
            if images
            else None
        ),
    )


class SingleConversation:
    """Handles single-user conversation"""

    def __init__(
        self,
        agent_engine: AgentInterface,
        live2d_model: Live2dModel,
        asr_engine: ASRInterface,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
        conf_uid: str = "",
        history_uid: str = "",
        client_uid: str = "",
        character_name: str = "AI",
    ) -> None:
        self.agent_engine = agent_engine
        self.live2d_model = live2d_model
        self.asr_engine = asr_engine
        self.tts_engine = tts_engine
        self.websocket_send = websocket_send
        self.conf_uid = conf_uid
        self.history_uid = history_uid
        self.client_uid = client_uid
        self.character_name = character_name
        self.session_emoji = np.random.choice(EMOJI_LIST)
        self.tts_manager = TTSTaskManager()

    async def _process_user_input(
        self,
        user_input: Union[str, np.ndarray],
    ) -> str:
        """Process user input, converting audio to text if needed"""
        if isinstance(user_input, np.ndarray):
            logger.info("Transcribing audio input...")
            input_text = await self.asr_engine.async_transcribe_np(user_input)
            await self.websocket_send(
                json.dumps({"type": "user-input-transcription", "text": input_text})
            )
            return input_text
        return user_input

    async def _send_conversation_start_signals(self) -> None:
        """Send initial conversation signals"""
        await self.websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-start",
                }
            )
        )
        await self.websocket_send(
            json.dumps({"type": "full-text", "text": "Thinking..."})
        )

    def cleanup(self) -> None:
        """Clean up resources"""
        self.tts_manager.clear()
        logger.debug(f"🧹 Clearing up conversation {self.session_emoji}.")

    async def process_conversation(
        self,
        user_input: Union[str, np.ndarray],
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Process one conversation turn"""
        try:
            await self._send_conversation_start_signals()
            logger.info(f"New Conversation Chain {self.session_emoji} started!")

            # Process user input
            input_text = await self._process_user_input(user_input)

            # Create batch input
            batch_input = _create_batch_input(input_text, images, self.character_name)

            # Store user message
            store_message(self.conf_uid, self.history_uid, "human", input_text)
            logger.info(f"User input: {input_text}")
            if images:
                logger.info(f"With {len(images)} images")

            # Process agent response
            full_response = await self._process_agent_response(batch_input)

            # Store AI response
            if full_response:
                store_message(self.conf_uid, self.history_uid, "ai", full_response)
                logger.info(f"AI response: {full_response}")

            # Finalize conversation
            await _finalize_conversation_turn(
                tts_manager=self.tts_manager,
                websocket_send=self.websocket_send,
                client_uid=self.client_uid,
                character_name=self.character_name,
                session_emoji=self.session_emoji,
            )

            return full_response

        except asyncio.CancelledError:
            logger.info(
                f"🤡👍 Conversation {self.session_emoji} "
                "cancelled because interrupted."
            )
            raise
        except Exception as e:
            logger.error(f"Error in conversation chain: {e}")
            await self.websocket_send(
                json.dumps(
                    {"type": "error", "message": f"Conversation error: {str(e)}"}
                )
            )
            raise
        finally:
            self.cleanup()

    async def _process_agent_response(
        self,
        batch_input: BatchInput,
    ) -> str:
        """Process agent response and generate output"""
        full_response = ""
        try:
            agent_output = self.agent_engine.chat(batch_input)
            async for output in agent_output:
                full_response += await _process_agent_output(
                    output=output,
                    tts_manager=self.tts_manager,
                    live2d_model=self.live2d_model,
                    tts_engine=self.tts_engine,
                    websocket_send=self.websocket_send,
                )
        except Exception as e:
            logger.error(f"Error processing agent response: {e}")
            raise

        return full_response


class GroupConversation:
    """Handles group conversation"""

    def __init__(
        self,
        client_contexts: Dict[str, ServiceContext],
        client_connections: Dict[str, WebSocket],
        asr_engine: ASRInterface,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
        broadcast_func: BroadcastFunc,
        group_members: List[str],
        initiator_client_uid: str,
    ) -> None:
        self.client_contexts = client_contexts
        self.client_connections = client_connections
        self.asr_engine = asr_engine
        self.tts_engine = tts_engine
        self.websocket_send = websocket_send
        self.broadcast_func = broadcast_func
        self.group_members = group_members
        self.initiator_client_uid = initiator_client_uid
        self.session_emoji = np.random.choice(EMOJI_LIST)
        self.tts_manager = TTSTaskManager()
        self.state = GroupConversationState(
            conversation_history=[],
            memory_index={uid: 0 for uid in group_members},
            group_queue=list(group_members),
            session_emoji=self.session_emoji,
        )

        # Initialize group conversation context for each AI
        self._init_group_conversation()

    def _init_group_conversation(self) -> None:
        """Initialize group conversation context for each AI participant"""
        # Get all AI character names
        ai_names = [
            ctx.character_config.conf_name for ctx in self.client_contexts.values()
        ]

        for context in self.client_contexts.values():
            agent = context.agent_engine
            if hasattr(agent, "start_group_conversation"):
                agent.start_group_conversation(
                    human_name="Human",
                    ai_participants=[
                        name
                        for name in ai_names
                        if name != context.character_config.conf_name
                    ],
                )
                logger.debug(
                    f"Initialized group conversation context for "
                    f"{context.character_config.conf_name}"
                )

    async def process_conversation(
        self,
        user_input: Union[str, np.ndarray],
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Process group conversation"""
        self.state.conversation_history = [f"Human: {user_input}"]

        try:
            logger.info(f"Group Conversation Chain {self.session_emoji} started!")

            # Process initial input
            input_text = await self._process_group_input(user_input)
            self.state.conversation_history[0] = f"Human: {input_text}"

            # Main conversation loop
            while self.state.group_queue:
                try:
                    await self._handle_group_member_turn(
                        current_member_uid=self.state.group_queue.pop(0),
                        images=images,
                    )

                except Exception as e:
                    logger.error(f"Error in group member turn: {e}")
                    await self._handle_member_error(f"Error in conversation: {str(e)}")

        except asyncio.CancelledError:
            logger.info(
                f"🤡👍 Group Conversation {self.session_emoji} "
                "cancelled because interrupted."
            )
            raise
        except Exception as e:
            logger.error(f"Error in group conversation chain: {e}")
            await self._handle_member_error(f"Fatal error in conversation: {str(e)}")
            raise
        finally:
            self.cleanup()

    async def _process_group_input(
        self,
        user_input: Union[str, np.ndarray],
    ) -> str:
        """Process and broadcast user input to group"""
        input_text = await self._process_user_input(user_input)
        await self._broadcast_transcription(input_text)
        return input_text

    async def _broadcast_transcription(
        self,
        text: str,
        exclude_uid: Optional[str] = None,
    ) -> None:
        """Broadcast transcription to group members"""
        await self.broadcast_func(
            self.group_members,
            {
                "type": "user-input-transcription",
                "text": text,
            },
            exclude_uid or self.initiator_client_uid,
        )

    async def _handle_group_member_turn(
        self,
        current_member_uid: str,
        images: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Handle a single group member's conversation turn"""
        await self._broadcast_thinking_state()

        context = self.client_contexts[current_member_uid]
        current_ws_send = self.client_connections[current_member_uid].send_text

        # Get new messages for this AI
        new_messages = self.state.conversation_history[
            self.state.memory_index[current_member_uid] :
        ]
        new_context = "\n".join(new_messages) if new_messages else ""

        # Create batch input
        batch_input = _create_batch_input(
            new_context, images, context.character_config.conf_name
        )

        logger.info(
            f"AI {context.character_config.conf_name} "
            f"(client {current_member_uid}) receiving context:\n{new_context}"
        )

        # Process response
        full_response = await self._process_member_response(
            context=context,
            batch_input=batch_input,
            current_ws_send=current_ws_send,
            current_member_uid=current_member_uid,
        )

        # Update conversation state
        if full_response:
            ai_message = f"{context.character_config.conf_name}: {full_response}"
            self.state.conversation_history.append(ai_message)
            logger.info(f"Appended complete response: {ai_message}")

        # Update memory index and queue
        self.state.memory_index[current_member_uid] = len(
            self.state.conversation_history
        )
        self.state.group_queue.append(current_member_uid)

    async def _broadcast_thinking_state(self) -> None:
        """Broadcast thinking state to group"""
        await self.broadcast_func(
            self.group_members,
            {"type": "control", "text": "conversation-chain-start"},
        )
        await self.broadcast_func(
            self.group_members,
            {"type": "full-text", "text": "Thinking..."},
        )

    async def _handle_member_error(self, error_message: str) -> None:
        """Handle and broadcast member error"""
        await self.broadcast_func(
            self.group_members,
            {
                "type": "error",
                "message": error_message,
            },
        )

    async def _process_member_response(
        self,
        context: ServiceContext,
        batch_input: BatchInput,
        current_ws_send: WebSocketSend,
        current_member_uid: str,
    ) -> str:
        """Process group member's response"""
        full_response = ""

        try:
            agent_output = context.agent_engine.chat(batch_input)
            broadcast_ctx = BroadcastContext(
                broadcast_func=self.broadcast_func,
                group_members=self.group_members,
                current_client_uid=current_member_uid,
            )

            async for output in agent_output:
                full_response += await _process_agent_output(
                    output=output,
                    tts_manager=self.tts_manager,
                    live2d_model=context.live2d_model,
                    tts_engine=context.tts_engine,
                    websocket_send=current_ws_send,
                    broadcast_ctx=broadcast_ctx,
                )

            if self.tts_manager.task_list:
                await asyncio.gather(*self.tts_manager.task_list)
                await current_ws_send(json.dumps({"type": "backend-synth-complete"}))

                await _finalize_conversation_turn(
                    tts_manager=self.tts_manager,
                    websocket_send=current_ws_send,
                    client_uid=current_member_uid,
                    character_name=context.character_config.conf_name,
                    broadcast_ctx=broadcast_ctx,
                    session_emoji=self.session_emoji,
                )

        except Exception as e:
            logger.error(f"Error processing member response: {e}")
            raise
        finally:
            self.tts_manager.clear()

        return full_response

    async def _process_user_input(
        self,
        user_input: Union[str, np.ndarray],
    ) -> str:
        """Process user input, converting audio to text if needed"""
        if isinstance(user_input, np.ndarray):
            logger.info("Transcribing audio input...")
            input_text = await self.asr_engine.async_transcribe_np(user_input)
            await self.websocket_send(
                json.dumps({"type": "user-input-transcription", "text": input_text})
            )
            return input_text
        return user_input

    async def _send_conversation_start_signals(self) -> None:
        """Send initial conversation signals"""
        await self.websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-start",
                }
            )
        )
        await self.websocket_send(
            json.dumps({"type": "full-text", "text": "Thinking..."})
        )

    def cleanup(self) -> None:
        """Clean up resources"""
        self.tts_manager.clear()
        logger.debug(f"🧹 Clearing up conversation {self.session_emoji}.")


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
