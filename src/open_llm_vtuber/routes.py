import json
import asyncio
import numpy as np
from uuid import uuid4
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from .conversation import conversation_chain, group_conversation_chain
from .service_context import ServiceContext
from .config_manager.utils import (
    scan_config_alts_directory,
    scan_bg_directory,
)
from .chat_history_manager import (
    create_new_history,
    store_message,
    modify_latest_message,
    get_history,
    delete_history,
    get_history_list,
)
from .chat_group import ChatGroupManager
from .message_handler import message_handler
from .utils.stream_audio import prepare_audio_payload


def create_routes(default_context_cache: ServiceContext):
    router = APIRouter()
    client_connections: Dict[str, WebSocket] = {}
    client_contexts: Dict[str, ServiceContext] = {}
    chat_group_manager = ChatGroupManager()
    # Track active group conversations
    active_group_conversations: Dict[str, asyncio.Task] = {}  # group_id -> conversation task

    async def broadcast_to_group(
        group_members: List[str], 
        message: Dict, 
        exclude_uid: str = None
    ):
        """Broadcast message to all members in a group except the sender"""
        for member_uid in group_members:
            if member_uid != exclude_uid and member_uid in client_connections:
                try:
                    await client_connections[member_uid].send_text(
                        json.dumps(message)
                    )
                except Exception as e:
                    logger.error(f"Failed to broadcast to {member_uid}: {e}")

    async def send_group_update(websocket: WebSocket, client_uid: str):
        """Send group information to client"""
        group = chat_group_manager.get_client_group(client_uid)
        if group:
            await websocket.send_text(
                json.dumps({
                    "type": "group-update",
                    "members": list(group.members),
                    "is_owner": group.owner_uid == client_uid
                })
            )

    async def cleanup_group_conversation(group_members: List[str]):
        """Clean up group conversation and notify all members"""
        await broadcast_to_group(
            group_members,
            {
                "type": "control",
                "text": "conversation-chain-end",
            }
        )
        await broadcast_to_group(
            group_members,
            {
                "type": "full-text",
                "text": "Conversation ended",
            }
        )

    async def handle_group_interrupt(group_id: str, heard_response: str = ""):
        """
        Handle interruption for a group conversation
        
        Args:
            group_id: The group ID
            heard_response: The partial response heard before interruption
        """
        if group_id in active_group_conversations:
            task = active_group_conversations[group_id]
            if not task.done():
                task.cancel()
                try:
                    await task  
                except asyncio.CancelledError:
                    logger.info(f"🛑 Group conversation {group_id} cancelled successfully.")
            active_group_conversations.pop(group_id, None)
            
            group = chat_group_manager.get_group_by_id(group_id)
            if group:
                for member_uid in group.members:
                    if member_uid in client_contexts:
                        try:
                            context = client_contexts[member_uid]
                            context.agent_engine.handle_interrupt(heard_response)
                            
                            if context.history_uid:
                                if not modify_latest_message(
                                    conf_uid=context.character_config.conf_uid,
                                    history_uid=context.history_uid,
                                    role="ai",
                                    new_content=heard_response,
                                ):
                                    logger.warning(f"Failed to modify message for member {member_uid}")

                                store_message(
                                    conf_uid=context.character_config.conf_uid,
                                    history_uid=context.history_uid,
                                    role="system",
                                    content="[Interrupted by user]",
                                )
                        except Exception as e:
                            logger.error(f"Error handling interrupt for member {member_uid}: {e}")
                
                await broadcast_to_group(
                    list(group.members),
                    {
                        "type": "interrupt-signal",
                        "text": "conversation-interrupted",
                    }
                )
        

    async def handle_interrupt(
        client_uid: str,
        heard_response: str,
        current_conversation_task: Optional[asyncio.Task],
        session_service_context: ServiceContext,
        chat_group_manager: ChatGroupManager,
    ) -> None:
        """
        Handle interrupt signal for both group and normal conversations
        
        Args:
            client_uid: Client identifier
            heard_response: Partial response heard before interruption
            current_conversation_task: Current conversation task (if any)
            session_service_context: Client's service context
            chat_group_manager: Chat group manager instance
        """
        # Get client's group
        group = chat_group_manager.get_client_group(client_uid)
        if group and len(group.members) > 1:
            # Handle group conversation interrupt
            await handle_group_interrupt(group.group_id, heard_response)
        else:
            # Handle normal conversation interrupt
            if current_conversation_task and not current_conversation_task.done():
                if not current_conversation_task.cancel():
                    logger.warning("❌ Conversation task was NOT cancelled")
                else:
                    logger.info("🛑 Conversation task was successfully interrupted")

            try:
                session_service_context.agent_engine.handle_interrupt(heard_response)
            except Exception as e:
                logger.error(f"Error handling interrupt: {e}")

            # Update chat history for interrupted conversation
            if session_service_context.history_uid:
                if not modify_latest_message(
                    conf_uid=session_service_context.character_config.conf_uid,
                    history_uid=session_service_context.history_uid,
                    role="ai",
                    new_content=heard_response,
                ):
                    logger.warning("Failed to modify message")

                store_message(
                    conf_uid=session_service_context.character_config.conf_uid,
                    history_uid=session_service_context.history_uid,
                    role="system",
                    content="[Interrupted by user]",
                )

    @router.websocket("/client-ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        client_uid = str(uuid4())

        # Initialize service context for this session
        session_service_context: ServiceContext = ServiceContext()
        session_service_context.load_cache(
            config=default_context_cache.config,
            system_config=default_context_cache.system_config,
            character_config=default_context_cache.character_config,
            live2d_model=default_context_cache.live2d_model,
            asr_engine=default_context_cache.asr_engine,
            tts_engine=default_context_cache.tts_engine,
            agent_engine=default_context_cache.agent_engine,
            translate_engine=default_context_cache.translate_engine,
        )

        # Store client connection and context
        client_connections[client_uid] = websocket
        client_contexts[client_uid] = session_service_context

        # Initialize client's group status (empty string means not in any group)
        chat_group_manager.client_group_map[client_uid] = ""
        await send_group_update(websocket, client_uid)

        await websocket.send_text(
            json.dumps({"type": "full-text", "text": "Connection established"})
        )

        logger.info(f"Connection established for client {client_uid}")

        await websocket.send_text(
            json.dumps(
                {
                    "type": "set-model-and-conf",
                    "model_info": session_service_context.live2d_model.model_info,
                    "conf_name": session_service_context.character_config.conf_name,
                    "conf_uid": session_service_context.character_config.conf_uid,
                    "client_uid": client_uid,
                }
            )
        )
        received_data_buffer = np.array([])
        # start mic
        await websocket.send_text(json.dumps({"type": "control", "text": "start-mic"}))

        current_conversation_task: asyncio.Task | None = None

        try:
            while True:
                data = await websocket.receive_json()
                message_handler.handle_message(client_uid, data)

                if data.get("type") == "add-client-to-group":
                    invitee_uid = data.get("invitee_uid")
                    if invitee_uid:
                        success, message = chat_group_manager.add_client_to_group(
                            inviter_uid=client_uid,
                            invitee_uid=invitee_uid
                        )
                        await websocket.send_text(
                            json.dumps({
                                "type": "group-operation-result",
                                "success": success,
                                "message": message
                            })
                        )
                        if success:
                            # Send updates to all affected clients
                            for member_uid in chat_group_manager.get_group_members(client_uid):
                                if member_uid in client_connections:
                                    await send_group_update(
                                        client_connections[member_uid], 
                                        member_uid
                                    )

                elif data.get("type") == "remove-client-from-group":
                    target_uid = data.get("target_uid")
                    if target_uid:
                        old_group_members = chat_group_manager.get_group_members(client_uid)
                        success, message = chat_group_manager.remove_client_from_group(
                            remover_uid=client_uid,
                            target_uid=target_uid
                        )
                        await websocket.send_text(
                            json.dumps({
                                "type": "group-operation-result",
                                "success": success,
                                "message": message
                            })
                        )
                        if success:
                            # Send updates to all affected clients
                            for member_uid in old_group_members:
                                if member_uid in client_connections:
                                    await send_group_update(
                                        client_connections[member_uid], 
                                        member_uid
                                    )

                elif data.get("type") == "request-group-info":
                    await send_group_update(websocket, client_uid)

                # ==== chat history related ====

                if data.get("type") == "fetch-history-list":
                    histories = get_history_list(
                        session_service_context.character_config.conf_uid
                    )
                    await websocket.send_text(
                        json.dumps({"type": "history-list", "histories": histories})
                    )

                elif data.get("type") == "fetch-and-set-history":
                    history_uid = data.get("history_uid")
                    if history_uid:
                        # Update history_uid in service context
                        session_service_context.history_uid = history_uid
                        session_service_context.agent_engine.set_memory_from_history(
                            conf_uid=session_service_context.character_config.conf_uid,
                            history_uid=history_uid,
                        )
                        messages = [
                            msg
                            for msg in get_history(
                                session_service_context.character_config.conf_uid,
                                history_uid,
                            )
                            if msg["role"] != "system"
                        ]
                        await websocket.send_text(
                            json.dumps({"type": "history-data", "messages": messages})
                        )

                elif data.get("type") == "create-new-history":
                    history_uid = create_new_history(session_service_context.character_config.conf_uid)
                    if history_uid:
                        # Update history_uid in service context
                        session_service_context.history_uid = history_uid
                        session_service_context.agent_engine.set_memory_from_history(
                            conf_uid=session_service_context.character_config.conf_uid,
                            history_uid=history_uid,
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "new-history-created",
                                    "history_uid": history_uid,
                                }
                            )
                        )

                elif data.get("type") == "delete-history":
                    history_uid = data.get("history_uid")
                    if history_uid:
                        success = delete_history(
                            session_service_context.character_config.conf_uid,
                            history_uid,
                        )
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "history-deleted",
                                    "success": success,
                                    "history_uid": history_uid,
                                }
                            )
                        )
                        if history_uid == session_service_context.history_uid:
                            session_service_context.history_uid = None

                # ==== conversation related ====

                elif data.get("type") == "interrupt-signal":
                    await handle_interrupt(
                        client_uid,
                        data.get("text", ""),
                        current_conversation_task,
                        session_service_context,
                        chat_group_manager,
                    )

                # Default sampleRate = 16000, frameSamples = 512, buffer window = 32ms
                elif data.get("type") == "mic-audio-data":
                    received_data_buffer = np.append(
                        received_data_buffer,
                        np.array(data.get("audio"), dtype=np.float32),
                    )

                elif data.get("type") in [
                    "mic-audio-end",
                    "text-input",
                    "ai-speak-signal",
                ]:
                    if data.get("type") == "ai-speak-signal":
                        user_input = ""
                        await websocket.send_text(
                            json.dumps({
                                "type": "full-text",
                                "text": "AI wants to speak something...",
                            })
                        )
                    elif data.get("type") == "text-input":
                        # Text input requires special handling since it arrives simultaneously with an interruption.
                        # Unlike audio input where there's sufficient delay between interrupt-signal and mic-audio-end,
                        # we must explicitly interrupt the current conversation before starting a new one
                        await handle_interrupt(
                            client_uid,
                            data.get("text", ""),
                            current_conversation_task,
                            session_service_context,
                            chat_group_manager,
                        )
                        user_input = data.get("text")
                    else:
                        user_input = received_data_buffer

                    received_data_buffer = np.array([])

                    # Get images if present
                    images = data.get("images")

                    logger.debug(f"data: {data}")
                    group = chat_group_manager.get_client_group(client_uid)
                    if group and len(group.members) > 1:
                        # Handle group conversation
                        if group.group_id not in active_group_conversations or \
                           active_group_conversations[group.group_id].done():
                            logger.info(f"Starting new group conversation for {group.group_id}")
                            # Start new group conversation only if none is active
                            active_group_conversations[group.group_id] = (
                                asyncio.create_task(
                                    group_conversation_chain(
                                        user_input=user_input,
                                        initiator_client_uid=client_uid,
                                        client_contexts=client_contexts,
                                        client_connections=client_connections,
                                        asr_engine=session_service_context.asr_engine,
                                        tts_engine=session_service_context.tts_engine,
                                        websocket_send=websocket.send_text,
                                        broadcast_func=broadcast_to_group,
                                        group_members=group.members,
                                        images=images,
                                    )
                                )
                            )
                    else:
                        # Handle normal conversation
                        current_conversation_task = asyncio.create_task(
                            conversation_chain(
                                client_uid=client_uid,
                                user_input=user_input,
                                asr_engine=session_service_context.asr_engine,
                                tts_engine=session_service_context.tts_engine,
                                agent_engine=session_service_context.agent_engine,
                                live2d_model=session_service_context.live2d_model,
                                websocket_send=websocket.send_text,
                                conf_uid=session_service_context.character_config.conf_uid,
                                history_uid=session_service_context.history_uid,
                                images=images,
                                character_name=session_service_context.character_config.conf_name,
                            )
                        )

                elif data.get("type") == "fetch-configs":
                    config_files = scan_config_alts_directory(
                        session_service_context.system_config.config_alts_dir
                    )
                    # logger.info("Sending config files +++++")
                    # logger.debug({"type": "config-files", "configs": config_files})
                    await websocket.send_text(
                        json.dumps({"type": "config-files", "configs": config_files})
                    )
                elif data.get("type") == "switch-config":
                    config_file_name: str = data.get("file")
                    if config_file_name:
                        await session_service_context.handle_config_switch(
                            websocket, config_file_name
                        )
                elif data.get("type") == "fetch-backgrounds":
                    bg_files = scan_bg_directory()
                    await websocket.send_text(
                        json.dumps({"type": "background-files", "files": bg_files})
                    )
                elif data.get("type") == "audio-play-start":
                    # Broadcast silent display to group members when speaker starts playing audio
                    group_members = chat_group_manager.get_group_members(client_uid)
                    if len(group_members) > 1:
                        display_text = data.get("display_text")
                        if display_text:
                            silent_payload = prepare_audio_payload(
                                audio_path=None,
                                display_text=display_text,
                                actions=None,
                                forwarded=True,
                            )
                            await broadcast_to_group(
                                group_members,
                                silent_payload,
                                exclude_uid=client_uid
                            )
                else:
                    logger.info("Unknown data type received.")

        except WebSocketDisconnect:
            # Clean up group conversation if client was in one
            group = chat_group_manager.get_client_group(client_uid)
            if group:
                await handle_group_interrupt(group.group_id)
            # Get group members before cleanup
            old_group_members = chat_group_manager.get_group_members(client_uid)

            # Cancel any ongoing conversation
            if current_conversation_task:
                current_conversation_task.cancel()

            await cleanup_group_conversation(old_group_members)

            # Clean up client data
            chat_group_manager.remove_client(client_uid)
            if client_uid in client_connections:
                del client_connections[client_uid]
            if client_uid in client_contexts:
                del client_contexts[client_uid]

            # Send updates to remaining group members
            for member_uid in old_group_members:
                if member_uid != client_uid and member_uid in client_connections:
                    await send_group_update(client_connections[member_uid], member_uid)
                    # Notify about member disconnection
                    await client_connections[member_uid].send_text(
                        json.dumps({
                            "type": "group-operation-result",
                            "success": True,
                            "message": f"Member {client_uid} disconnected"
                        })
                    )

            logger.info(f"Client {client_uid} disconnected")
            message_handler.cleanup_client(client_uid)

    return router
