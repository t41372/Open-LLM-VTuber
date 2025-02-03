from typing import Union, List, Dict, Any, Optional
import asyncio
import json
from loguru import logger
import numpy as np

from .base import BaseConversation
from .types import WebSocketSend
from ..chat_history_manager import store_message
from ..service_context import ServiceContext
from ..agent.input_types import BatchInput


class SingleConversation(BaseConversation):
    """Handles single-user conversation"""

    def __init__(
        self,
        context: ServiceContext,
        websocket_send: WebSocketSend,
        client_uid: str = "",
    ) -> None:
        """Initialize conversation handler

        Args:
            context: Service context containing all configurations and engines
            websocket_send: WebSocket send function
            client_uid: Client unique identifier
        """
        super().__init__()
        self.context = context
        self.agent_engine = context.agent_engine
        self.live2d_model = context.live2d_model
        self.asr_engine = context.asr_engine
        self.tts_engine = context.tts_engine
        self.websocket_send = websocket_send
        self.client_uid = client_uid

    async def process_conversation(
        self,
        user_input: Union[str, np.ndarray],
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Process a conversation turn

        Args:
            user_input: Text or audio input from user
            images: Optional list of image data

        Returns:
            str: Complete response text
        """
        try:
            # Send initial signals
            await self._send_conversation_start_signals(self.websocket_send)
            logger.info(f"New Conversation Chain {self.session_emoji} started!")

            # Process user input
            input_text = await self._process_user_input(
                user_input, self.asr_engine, self.websocket_send
            )

            # Create batch input
            batch_input = self._create_batch_input(
                input_text=input_text,
                images=images,
                from_name=self.context.character_config.human_name,
            )

            # Store user message
            if self.context.history_uid:
                store_message(
                    conf_uid=self.context.character_config.conf_uid,
                    history_uid=self.context.history_uid,
                    role="human",
                    content=input_text,
                    name=self.context.character_config.human_name,
                )
            logger.info(f"User input: {input_text}")
            if images:
                logger.info(f"With {len(images)} images")

            # Process agent response
            full_response = await self._process_agent_response(batch_input)

            # Store AI response
            if self.context.history_uid and full_response:
                store_message(
                    conf_uid=self.context.character_config.conf_uid,
                    history_uid=self.context.history_uid,
                    role="ai",
                    content=full_response,
                    name=self.context.character_config.conf_name,
                    avatar=self.context.character_config.avatar,
                )
                logger.info(f"AI response: {full_response}")

            # Finalize conversation
            if self.tts_manager.task_list:
                await asyncio.gather(*self.tts_manager.task_list)
                await self.websocket_send(
                    json.dumps({"type": "backend-synth-complete"})
                )

            await self._finalize_conversation_turn(
                tts_manager=self.tts_manager,
                websocket_send=self.websocket_send,
                client_uid=self.client_uid,
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
        """Process agent response and generate output

        Args:
            batch_input: Input data for the agent

        Returns:
            str: The complete response text
        """
        full_response = ""
        try:
            agent_output = self.agent_engine.chat(batch_input)
            async for output in agent_output:
                response_part = await self._process_agent_output(
                    output=output,
                    character_config=self.context.character_config,
                    live2d_model=self.live2d_model,
                    tts_engine=self.tts_engine,
                    websocket_send=self.websocket_send,
                )
                full_response += response_part

        except Exception as e:
            logger.error(f"Error processing agent response: {e}")
            raise

        return full_response
