import json
import asyncio
import numpy as np
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from .conversation import conversation_chain
from .service_context import ServiceContext
from .utils.config_loader import (
    scan_config_alts_directory,
    scan_bg_directory,
)
from .chat_history_manager import (
    create_new_history,
    store_message,
    get_history,
    delete_history,
    get_history_list,
)


def create_routes(default_context_cache: ServiceContext):
    """Creates the FastAPI routes for the application."""

    router = APIRouter()
    connected_clients = {}

    async def handle_websocket_message(
        websocket: WebSocket,
        session_service_context: ServiceContext,
        data: dict,
        current_conversation_task: asyncio.Task | None,
        ai_message_buffer: str,
        current_history_uid: str | None,
    ):
        """
        Handles individual websocket messages, potentially spawning long-running tasks.

        Parameters:
        - websocket (WebSocket): The websocket connection.
        - session_service_context (ServiceContext): The service context for the session.
        - data (dict): The data received from the client.
        - current_conversation_task (asyncio.Task | None): The current conversation task.
        - ai_message_buffer (str): The current AI message buffer.
        - current_history_uid (str | None): The current history UID.
        """

        conf_uid = session_service_context.system_config.get("CONF_UID", "")

        if data.get("type") == "fetch-conf-info":
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "config-info",
                        "conf_name": session_service_context.system_config.get(
                            "CONF_NAME"
                        ),
                        "conf_uid": session_service_context.system_config.get(
                            "CONF_UID"
                        ),
                    }
                )
            )

        elif data.get("type") == "fetch-history-list":
            histories = get_history_list(conf_uid)
            await websocket.send_text(
                json.dumps({"type": "history-list", "histories": histories})
            )

        elif data.get("type") == "fetch-and-set-history":
            history_uid = data.get("history_uid")
            if history_uid:
                messages = get_history(conf_uid, history_uid)
                current_history_uid = history_uid
                session_service_context.llm_engine.set_memory_from_history(messages)
                await websocket.send_text(
                    json.dumps({"type": "history-data", "messages": messages})
                )

        elif data.get("type") == "create-new-history":
            current_history_uid = create_new_history(conf_uid)
            session_service_context.llm_engine.clear_memory()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "new-history-created",
                        "history_uid": current_history_uid,
                    }
                )
            )

        elif data.get("type") == "delete-history":
            history_uid = data.get("history_uid")
            if history_uid:
                success = delete_history(conf_uid, history_uid)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "history-deleted",
                            "success": success,
                            "history_uid": history_uid,
                        }
                    )
                )
                if history_uid == current_history_uid:
                    current_history_uid = None

        elif data.get("type") == "interrupt-signal":
            logger.info(
                "⌛️ Interruption Signal Received: Attempting to interrupt conversation task..."
            )
            if current_conversation_task is not None:
                if not current_conversation_task.cancel():
                    logger.info(
                        "Conversation task was NOT cancelled. Likely because there is no running task."
                    )
                else:
                    logger.info("✅ Conversation task was successfully cancelled.")
                    interrupted_ai_msg = data.get("text") or ""
                    if interrupted_ai_msg:
                        ai_message_buffer = interrupted_ai_msg
                    logger.info(
                        "Conversation was interrupted. Using partial AI msg: "
                        + ai_message_buffer
                    )
            else:
                logger.info("🤨 No running conversation task to interrupt.")

        elif data.get("type") == "mic-audio-data":
            # Append received audio data to the buffer
            connected_clients[websocket]["received_data_buffer"] = np.append(
                connected_clients[websocket]["received_data_buffer"],
                np.array(data.get("audio"), dtype=np.float32),
            )

        elif data.get("type") in ["mic-audio-end", "text-input"]:
            await websocket.send_text(
                json.dumps({"type": "full-text", "text": "Thinking..."})
            )
            if data.get("type") == "text-input":
                user_input = data.get("text")
            else:
                user_input: np.ndarray | str = connected_clients[websocket][
                    "received_data_buffer"
                ]

            # Reset the buffer
            connected_clients[websocket]["received_data_buffer"] = np.array([])

            async def conversation_task_wrapper():
                try:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "control",
                                "text": "conversation-chain-start",
                            }
                        )
                    )
                    current_conversation_task: asyncio.Task = asyncio.create_task(
                        conversation_chain(
                            user_input=user_input,
                            asr_engine=session_service_context.asr_engine,
                            tts_engine=session_service_context.tts_engine,
                            llm_engine=session_service_context.llm_engine,
                            live2d_model=session_service_context.live2d_model,
                            websocket_send=websocket.send_text,
                            conf_uid=conf_uid,
                            history_uid=current_history_uid,
                        )
                    )

                    ai_message_buffer = await current_conversation_task
                    connected_clients[websocket]["current_conversation_task"] = None

                    if ai_message_buffer:
                        store_message(
                            conf_uid, current_history_uid, "ai", ai_message_buffer
                        )
                        logger.info(f"Stored AI message: {ai_message_buffer[:50]}...")

                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "control",
                                "text": "conversation-chain-end",
                            }
                        )
                    )
                    logger.info("One Conversation Loop Completed")

                    return ai_message_buffer
                except asyncio.CancelledError:
                    logger.info("Conversation task was cancelled.")
                    if ai_message_buffer:
                        store_message(
                            conf_uid, current_history_uid, "ai", ai_message_buffer
                        )
                        logger.info(
                            f"Stored interrupted AI message: {ai_message_buffer[:50]}..."
                        )
                    return ai_message_buffer
                except InterruptedError as e:
                    logger.info(f"Conversation was interrupted: {e}")
                    return ""

            # Start the potentially long-running conversation task
            current_conversation_task = asyncio.create_task(conversation_task_wrapper())
            connected_clients[websocket]["current_conversation_task"] = (
                current_conversation_task
            )
            # Update ai_message_buffer concurrently if needed
            if current_conversation_task is not None:
                asyncio.create_task(
                    update_ai_message_buffer(websocket, current_conversation_task)
                )

        elif data.get("type") == "fetch-configs":
            config_files = scan_config_alts_directory(
                session_service_context.system_config.get(
                    "CONFIG_ALTS_DIR", "config_alts"
                )
            )
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
        else:
            logger.info("Unknown data type received.")

        return current_conversation_task, ai_message_buffer, current_history_uid

    async def update_ai_message_buffer(
        websocket: WebSocket, current_conversation_task: asyncio.Task
    ):
        """Updates the ai_message_buffer with the result of the conversation task."""
        try:
            ai_message_buffer = await current_conversation_task
            if ai_message_buffer:
                connected_clients[websocket]["ai_message_buffer"] = ai_message_buffer

        except asyncio.CancelledError:
            logger.info("update_ai_message_buffer task was cancelled.")

    async def websocket_manager(websocket: WebSocket):
        """Manages the lifecycle of a single websocket connection."""
        await websocket.accept()

        session_service_context: ServiceContext = ServiceContext()
        session_service_context.load_cache(
            system_config=default_context_cache.system_config,
            live2d_model=default_context_cache.live2d_model,
            asr_engine=default_context_cache.asr_engine,
            tts_engine=default_context_cache.tts_engine,
            llm_engine=default_context_cache.llm_engine,
        )

        await websocket.send_text(
            json.dumps({"type": "full-text", "text": "Connection established"})
        )

        connected_clients[websocket] = {
            "service_context": session_service_context,
            "received_data_buffer": np.array([]),
            "current_conversation_task": None,
            "ai_message_buffer": "",
            "current_history_uid": None,
        }

        logger.info(f"Connection established with client: {websocket.client}")

        await websocket.send_text(
            json.dumps(
                {
                    "type": "set-model",
                    "model_info": session_service_context.live2d_model.model_info,
                }
            )
        )

        # start mic
        await websocket.send_text(json.dumps({"type": "control", "text": "start-mic"}))

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                current_conversation_task = connected_clients[websocket][
                    "current_conversation_task"
                ]
                ai_message_buffer = connected_clients[websocket]["ai_message_buffer"]
                current_history_uid = connected_clients[websocket][
                    "current_history_uid"
                ]

                # Create a task to handle the message
                asyncio.create_task(
                    handle_websocket_message(
                        websocket,
                        session_service_context,
                        data,
                        current_conversation_task,
                        ai_message_buffer,
                        current_history_uid,
                    )
                )

        except WebSocketDisconnect:
            logger.info(f"Connection closed with client: {websocket.client}")
            ai_message_buffer = connected_clients[websocket]["ai_message_buffer"]
            current_history_uid = connected_clients[websocket]["current_history_uid"]
            conf_uid = session_service_context.system_config.get("CONF_UID", "")
            if ai_message_buffer:
                store_message(conf_uid, current_history_uid, "ai", ai_message_buffer)
            del connected_clients[websocket]

    @router.websocket("/client-ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket_manager(websocket)

    return router
