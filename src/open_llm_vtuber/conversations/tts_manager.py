import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional
from loguru import logger

from ..agent.output_types import DisplayText, Actions
from ..live2d_model import Live2dModel
from ..tts.tts_interface import TTSInterface
from ..utils.stream_audio import prepare_audio_payload
from .types import BroadcastContext, WebSocketSend


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
