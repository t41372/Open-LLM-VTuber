from typing import Any, Dict, List, Optional, Union
import asyncio
import json
from loguru import logger
from fastapi import WebSocket
import numpy as np

from .base import BaseConversation
from .types import (
    BroadcastFunc,
    GroupConversationState,
    BroadcastContext,
    WebSocketSend,
)
from ..service_context import ServiceContext
from ..chat_history_manager import store_message
from ..agent.input_types import BatchInput


class GroupConversation(BaseConversation):
    """Handles group conversation"""

    def __init__(
        self,
        client_contexts: Dict[str, ServiceContext],
        client_connections: Dict[str, WebSocket],
        broadcast_func: BroadcastFunc,
        group_members: List[str],
        initiator_client_uid: str,
    ) -> None:
        """Initialize group conversation

        Args:
            client_contexts: Dictionary of client contexts
            client_connections: Dictionary of client WebSocket connections
            broadcast_func: Function to broadcast messages to group
            group_members: List of group member UIDs
            initiator_client_uid: UID of conversation initiator
        """
        super().__init__()
        self.client_contexts = client_contexts
        self.client_connections = client_connections
        self.broadcast_func = broadcast_func
        self.group_members = group_members
        self.initiator_client_uid = initiator_client_uid

        # Initialize group state
        self.state = GroupConversationState(
            conversation_history=[],
            memory_index={uid: 0 for uid in group_members},
            group_queue=list(group_members),
            session_emoji=self.session_emoji,
        )

        # Initialize group conversation context for each AI
        self._init_group_conversation()

        initiator_context = client_contexts.get(initiator_client_uid)
        self.human_name = (
            initiator_context.character_config.human_name
            if initiator_context
            else "Human"
        )

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
        try:
            logger.info(f"Group Conversation Chain {self.session_emoji} started!")

            # Process initial input
            input_text = await self._process_group_input(user_input)

            # Store user message
            initiator_context = self.client_contexts[self.initiator_client_uid]
            if initiator_context.history_uid:
                store_message(
                    conf_uid=initiator_context.character_config.conf_uid,
                    history_uid=initiator_context.history_uid,
                    role="human",
                    content=input_text,
                    name=self.human_name,
                )

            self.state.conversation_history = [f"{self.human_name}: {input_text}"]

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
        context = self.client_contexts[self.initiator_client_uid]
        current_ws_send = self.client_connections[self.initiator_client_uid].send_text

        input_text = await self._process_user_input(
            user_input, context.asr_engine, current_ws_send
        )
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

        new_messages = self.state.conversation_history[
            self.state.memory_index[current_member_uid] :
        ]
        new_context = "\n".join(new_messages) if new_messages else ""

        batch_input = self._create_batch_input(
            input_text=new_context, images=images, from_name=self.human_name
        )

        logger.info(
            f"AI {context.character_config.conf_name} "
            f"(client {current_member_uid}) receiving context:\n{new_context}"
        )

        full_response = await self._process_member_response(
            context=context,
            batch_input=batch_input,
            current_ws_send=current_ws_send,
            current_member_uid=current_member_uid,
        )

        if full_response:
            ai_message = f"{context.character_config.conf_name}: {full_response}"
            self.state.conversation_history.append(ai_message)
            logger.info(f"Appended complete response: {ai_message}")

            if context.history_uid:
                store_message(
                    conf_uid=context.character_config.conf_uid,
                    history_uid=context.history_uid,
                    role="ai",
                    content=full_response,
                    name=context.character_config.conf_name,
                    avatar=context.character_config.avatar,
                )

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
                response_part = await self._process_agent_output(
                    output=output,
                    character_config=context.character_config,
                    live2d_model=context.live2d_model,
                    tts_engine=context.tts_engine,
                    websocket_send=current_ws_send,
                )
                full_response += response_part

                # Store forwarded message for each group member
                for member_uid in self.group_members:
                    if member_uid != current_member_uid:
                        await self._store_forwarded_message(
                            member_uid=member_uid,
                            content=response_part,
                            name=context.character_config.conf_name,
                            avatar=context.character_config.avatar,
                        )

            if self.tts_manager.task_list:
                await asyncio.gather(*self.tts_manager.task_list)
                await current_ws_send(json.dumps({"type": "backend-synth-complete"}))

                await self._finalize_conversation_turn(
                    tts_manager=self.tts_manager,
                    websocket_send=current_ws_send,
                    client_uid=current_member_uid,
                    broadcast_ctx=broadcast_ctx,
                )

        except Exception as e:
            logger.error(f"Error processing member response: {e}")
            raise
        finally:
            self.tts_manager.clear()

        return full_response

    async def _store_forwarded_message(
        self,
        member_uid: str,
        content: str,
        name: str,
        avatar: str,
    ) -> None:
        """Store forwarded message for a group member"""
        context = self.client_contexts.get(member_uid)
        if not context or not context.history_uid:
            return

        try:
            store_message(
                conf_uid=context.character_config.conf_uid,
                history_uid=context.history_uid,
                role="ai",
                content=content,
                name=name,
                avatar=avatar,
            )
            logger.debug(
                f"Stored forwarded message for member {member_uid}: {content[:50]}..."
            )
        except Exception as e:
            logger.error(f"Failed to store forwarded message: {e}")
