from typing import Dict, Optional, Callable, Awaitable
import asyncio
from fastapi import WebSocket
from loguru import logger
from collections import defaultdict

class MessageHandler:
    def __init__(self):
        self._response_events: Dict[str, Dict[str, asyncio.Event]] = defaultdict(dict)
        self._response_data: Dict[str, Dict[str, dict]] = defaultdict(dict)
        
    async def wait_for_response(self, client_uid: str, response_type: str, timeout: float | None = None) -> Optional[dict]:
        """
        Wait for a response of specific type from a client.
        
        Args:
            client_uid: Client identifier
            response_type: Type of response to wait for
            timeout: Optional timeout in seconds. If None, wait indefinitely
        
        Returns:
            Optional[dict]: Response data if received, None if timeout
        """
        event = asyncio.Event()
        self._response_events[client_uid][response_type] = event
        
        try:
            if timeout is not None:
                # Wait with timeout
                await asyncio.wait_for(event.wait(), timeout)
            else:
                # Wait indefinitely
                await event.wait()
            
            return self._response_data[client_uid].pop(response_type, None)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for {response_type} from {client_uid}")
            return None
        finally:
            self._response_events[client_uid].pop(response_type, None)
            
    def handle_message(self, client_uid: str, message: dict) -> None:
        """
        Process an incoming message with a response event waiting.
        
        Args:
            client_uid: Client identifier
            message: Message data dictionary
        """
        msg_type = message.get("type")
        if not msg_type:
            return
            
        if client_uid in self._response_events and msg_type in self._response_events[client_uid]:
            self._response_data[client_uid][msg_type] = message
            self._response_events[client_uid][msg_type].set()
            
    def cleanup_client(self, client_uid: str) -> None:
        """
        Cleanup all events and cached data for a given client.
        
        Args:
            client_uid: Client identifier
        """
        if client_uid in self._response_events:
            for event in self._response_events[client_uid].values():
                event.set()
            self._response_events.pop(client_uid)
            self._response_data.pop(client_uid, None)

message_handler = MessageHandler() 