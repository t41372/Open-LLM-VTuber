import asyncio
from typing import Optional, Union, Any, List, Dict
import numpy as np
import json
from loguru import logger

from ..message_handler import message_handler
from .types import WebSocketSend, BroadcastContext
from .tts_manager import TTSTaskManager
from ..agent.output_types import SentenceOutput, AudioOutput
from ..agent.input_types import BatchInput, TextData, ImageData, TextSource, ImageSource
from ..asr.asr_interface import ASRInterface
from ..live2d_model import Live2dModel
from ..tts.tts_interface import TTSInterface

# Constants
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


class BaseConversation:
    """Base class for conversation handling"""

    def __init__(
        self,
        tts_manager: Optional[TTSTaskManager] = None,
    ) -> None:
        """Initialize base conversation

        Args:
            tts_manager: Optional TTSTaskManager instance
        """
        self.tts_manager = tts_manager or TTSTaskManager()
        self.session_emoji = np.random.choice(EMOJI_LIST)

    @staticmethod
    def _create_batch_input(
        input_text: str,
        images: Optional[List[Dict[str, Any]]],
        from_name: str,
    ) -> BatchInput:
        """Create batch input for agent processing

        Args:
            input_text: Text input
            images: Optional list of image data
            from_name: Name of the sender

        Returns:
            BatchInput: Formatted input for agent
        """
        return BatchInput(
            texts=[
                TextData(
                    source=TextSource.INPUT, content=input_text, from_name=from_name
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

    async def _process_agent_output(
        self,
        output: Union[AudioOutput, SentenceOutput],
        character_config: Any,
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
    ) -> str:
        """Process agent output with character information"""
        # Update display_text with character info
        output.display_text.name = character_config.conf_name
        output.display_text.avatar = character_config.avatar

        full_response = ""
        try:
            if isinstance(output, SentenceOutput):
                full_response = await self._handle_sentence_output(
                    output, live2d_model, tts_engine, websocket_send
                )
            elif isinstance(output, AudioOutput):
                full_response = await self._handle_audio_output(output, websocket_send)
            else:
                logger.warning(f"Unknown output type: {type(output)}")
        except Exception as e:
            logger.error(f"Error processing agent output: {e}")
            await websocket_send(
                json.dumps(
                    {"type": "error", "message": f"Error processing response: {str(e)}"}
                )
            )

        return full_response

    async def _handle_sentence_output(
        self,
        output: SentenceOutput,
        live2d_model: Live2dModel,
        tts_engine: TTSInterface,
        websocket_send: WebSocketSend,
    ) -> str:
        """Handle sentence output type"""
        full_response = ""
        async for display_text, tts_text, actions in output:
            full_response += display_text.text
            await self.tts_manager.speak(
                tts_text=tts_text,
                display_text=display_text,
                actions=actions,
                live2d_model=live2d_model,
                tts_engine=tts_engine,
                websocket_send=websocket_send,
            )
        return full_response

    async def _handle_audio_output(
        self,
        output: AudioOutput,
        websocket_send: WebSocketSend,
    ) -> str:
        """Handle audio output type"""
        full_response = ""
        async for audio_path, display_text, transcript, actions in output:
            full_response += transcript
            audio_payload = {
                "type": "audio",
                "audio": audio_path,
                "display_text": display_text.to_dict() if display_text else None,
                "actions": actions.to_dict() if actions else None,
            }
            await websocket_send(json.dumps(audio_payload))
        return full_response

    async def _send_conversation_start_signals(
        self, websocket_send: WebSocketSend
    ) -> None:
        """Send initial conversation signals

        Args:
            websocket_send: WebSocket send function
        """
        await websocket_send(
            json.dumps(
                {
                    "type": "control",
                    "text": "conversation-chain-start",
                }
            )
        )
        await websocket_send(json.dumps({"type": "full-text", "text": "Thinking..."}))

    async def _process_user_input(
        self,
        user_input: Union[str, np.ndarray],
        asr_engine: ASRInterface,
        websocket_send: WebSocketSend,
    ) -> str:
        """Process user input, converting audio to text if needed

        Args:
            user_input: Text or audio input
            asr_engine: ASR engine instance
            websocket_send: WebSocket send function

        Returns:
            str: Processed text input
        """
        if isinstance(user_input, np.ndarray):
            logger.info("Transcribing audio input...")
            input_text = await asr_engine.async_transcribe_np(user_input)
            await websocket_send(
                json.dumps({"type": "user-input-transcription", "text": input_text})
            )
            return input_text
        return user_input

    async def _finalize_conversation_turn(
        self,
        tts_manager: TTSTaskManager,
        websocket_send: WebSocketSend,
        client_uid: str,
        broadcast_ctx: Optional[BroadcastContext] = None,
    ) -> None:
        """Finalize a conversation turn"""
        if tts_manager.task_list:
            await asyncio.gather(*tts_manager.task_list)
            await websocket_send(json.dumps({"type": "backend-synth-complete"}))

            response = await message_handler.wait_for_response(
                client_uid, "frontend-playback-complete"
            )

            if not response:
                logger.warning(f"No playback completion response from {client_uid}")
                return

        # Send force-new-message signal
        await websocket_send(json.dumps({"type": "force-new-message"}))

        # For group chat, broadcast force-new-message to all members
        if broadcast_ctx and broadcast_ctx.broadcast_func:
            await broadcast_ctx.broadcast_func(
                broadcast_ctx.group_members,
                {"type": "force-new-message"},
                broadcast_ctx.current_client_uid,
            )

        await self._send_conversation_end_signal(websocket_send, broadcast_ctx)

    async def _send_conversation_end_signal(
        self,
        websocket_send: WebSocketSend,
        broadcast_ctx: Optional[BroadcastContext],
    ) -> None:
        """Send conversation chain end signal"""
        chain_end_msg = {
            "type": "control",
            "text": "conversation-chain-end",
        }

        await websocket_send(json.dumps(chain_end_msg))

        if (
            broadcast_ctx
            and broadcast_ctx.broadcast_func
            and broadcast_ctx.group_members
        ):
            await broadcast_ctx.broadcast_func(
                broadcast_ctx.group_members,
                chain_end_msg,
            )

        logger.info(f"😎👍✅ Conversation Chain {self.session_emoji} completed!")

    def cleanup(self) -> None:
        """Clean up resources"""
        self.tts_manager.clear()
        logger.debug(f"🧹 Clearing up conversation {self.session_emoji}.")
