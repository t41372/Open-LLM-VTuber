from typing import AsyncIterator, Tuple, Optional, Union
import asyncio
import sys
import numpy as np
from loguru import logger
import base64
import json
import requests
import websockets
from .agent_interface import AgentInterface, AgentOutputType
import os
from dotenv import load_dotenv
from pathlib import Path


class HumeAIAgent(AgentInterface):
    """Hume AI Agent that handles text input and audio output"""

    def __init__(
        self,
        api_key: str,
        host: str = "api.hume.ai",
        config_id: Optional[str] = None,
        config_version: Optional[int] = None,
        verbose_transcription: bool = False
    ):
        self.api_key = api_key
        self.host = host
        self.config_id = config_id
        self.config_version = config_version
        self.verbose_transcription = verbose_transcription
        self._ws = None
        self._current_text = None
        self._current_id = None
        self._connected = False
        self._heartbeat_task = None

        # Create cache directory if it doesn't exist
        self.cache_dir = Path("./cache")
        self.cache_dir.mkdir(exist_ok=True)

    async def _heartbeat(self):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                if self._ws and not self._ws.closed:
                    await self._ws.send(json.dumps({"type": "ping"}))
                await asyncio.sleep(60)  # Send heartbeat every 60 seconds
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")

    async def connect(self):
        """Establish initial WebSocket connection"""
        if not self._connected:
            # Build URL with query parameters according to documentation
            socket_url = f"wss://{self.host}/v0/evi/chat?api_key={self.api_key}"

            if self.config_id:
                socket_url += f"&config_id={self.config_id}"
                if self.config_version:
                    socket_url += f"&config_version={self.config_version}"

            if self.verbose_transcription:
                socket_url += "&verbose_transcription=true"

            logger.info(f"Connecting to EVI with config_id: {self.config_id}")
            self._ws = await websockets.connect(socket_url)
            self._connected = True

            # Start heartbeat
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def _ensure_connection(self):
        """Ensure connection is alive, reconnect if needed"""
        if not self._connected or not self._ws or self._ws.closed:
            await self.connect()

    @property
    def output_type(self) -> AgentOutputType:
        return AgentOutputType.AUDIO_TEXT

    async def chat(self, prompt: str) -> AsyncIterator[Tuple[str, str]]:
        """Chat with Hume AI and get audio response"""
        try:
            await self._ensure_connection()

            message = {
                "type": "user_input",
                "text": prompt,
            }
            await self._ws.send(json.dumps(message))

            async for message in self._ws:
                try:
                    response_data = json.loads(message)
                    msg_type = response_data.get("type")
                    msg_id = response_data.get("id")

                    if msg_type == "assistant_message":
                        self._current_text = response_data["message"]["content"]
                        self._current_id = msg_id

                    elif msg_type == "audio_output":
                        if msg_id == self._current_id and self._current_text:
                            audio_data = base64.b64decode(response_data["data"])

                            # Create temp file in cache directory
                            cache_file = self.cache_dir / f"evi_audio_{msg_id}.wav"
                            with open(cache_file, "wb") as f:
                                f.write(audio_data)
                                logger.debug(f"Saved audio to cache file: {cache_file}")
                                
                            # Add a small delay to ensure file is fully written
                            yield str(cache_file), self._current_text

                            self._current_text = None
                            self._current_id = None
                        else:
                            logger.warning("Received audio output without matching text")

                    elif msg_type == "assistant_end":
                        break

                    elif msg_type == "tool_error_message":
                        logger.error(f"Tool error: {response_data.get('error')}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response JSON: {e}")
                    continue

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"Connection closed: {e}, attempting to reconnect...")
            self._connected = False
            await self._ensure_connection()
            # Retry the chat after reconnection
            async for result in self.chat(prompt):
                yield result

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise

    def handle_interrupt(self, heard_response: str) -> None:
        pass

    def set_memory_from_history(self, messages: list) -> None:
        pass

    async def clear_memory(self) -> None:
        """Clear memory by resetting the WebSocket connection"""
        try:
            # Cancel heartbeat task if exists
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
            
            # Close existing WebSocket connection
            if self._ws:
                await self._ws.close()
                self._ws = None
            
            # Reset connection state
            self._connected = False
            self._current_text = None
            self._current_id = None
            
            # Reconnect to establish fresh connection
            await self.connect()
            
            logger.info("Successfully cleared memory by resetting WebSocket connection")
            
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            raise

    async def __del__(self):
        """Cleanup WebSocket connection and cache files"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._ws:
            await self._ws.close()

        # Clean up cache files
        try:
            for file in self.cache_dir.glob("evi_audio_*.wav"):
                file.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up cache files: {e}")
