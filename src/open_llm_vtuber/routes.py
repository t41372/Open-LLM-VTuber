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
from .chat_history_manager import create_new_history, store_message, get_history, delete_history, get_history_list


def create_routes(default_context_cache: ServiceContext):
    router = APIRouter()
    connected_clients = []

    @router.websocket("/client-ws")
    async def websocket_endpoint(websocket: WebSocket):
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
            json.dumps(
                {
                    "type": "config-info",
                    "conf_name": session_service_context.system_config.get("CONF_NAME"),
                    "conf_uid": session_service_context.system_config.get("CONF_UID"),
                }
            )
        )

        await websocket.send_text(
            json.dumps({"type": "full-text", "text": "Connection established"})
        )

        connected_clients.append(websocket)
        logger.info("Connection established")

        await websocket.send_text(
            json.dumps(
                {
                    "type": "set-model",
                    "model_info": session_service_context.live2d_model.model_info,
                }
            )
        )
        received_data_buffer = np.array([])
        # start mic
        await websocket.send_text(json.dumps({"type": "control", "text": "start-mic"}))

        conf_uid = session_service_context.system_config.get("CONF_UID", "")
        
        current_history_uid = create_new_history(conf_uid)  # Create new history for this session
        session_service_context.llm_engine.clear_memory()

        histories = get_history_list(conf_uid)
        await websocket.send_text(
            json.dumps({
                "type": "history-list",
                "histories": histories
            })
        )

        await websocket.send_text(
            json.dumps({
                "type": "new-history-created",
                "history_uid": current_history_uid
            })
        )

        current_conversation_task: asyncio.Task | None = None
        ai_message_buffer: str = ""

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "fetch-history-list":
                    histories = get_history_list(conf_uid)
                    await websocket.send_text(
                        json.dumps({
                            "type": "history-list",
                            "histories": histories
                        })
                    )
                    continue

                if data.get("type") == "fetch-and-set-history":
                    history_uid = data.get("history_uid")
                    if history_uid:
                        messages = get_history(conf_uid, history_uid)
                        current_history_uid = history_uid
                        session_service_context.llm_engine.set_memory_from_history(messages)
                        await websocket.send_text(
                            json.dumps({
                                "type": "history-data",
                                "messages": messages
                            })
                        )
                    continue

                if data.get("type") == "interrupt-signal":
                    if current_conversation_task is not None:
                        # session_service_context.open_llm_vtuber.interrupt(data.get("text"))
                        if not current_conversation_task.cancel():
                            logger.info(
                                "Conversation task was NOT cancelled. Likely because there is no running task."
                            )
                    interrupted_ai_msg = data.get("text") or ""
                    if interrupted_ai_msg:
                        ai_message_buffer = interrupted_ai_msg
                    logger.info(
                        "Conversation was interrupted. Using partial AI msg: "
                        + ai_message_buffer
                    )

                elif data.get("type") == "mic-audio-data":
                    received_data_buffer = np.append(
                        received_data_buffer,
                        np.array(list(data.get("audio").values()), dtype=np.float32),
                    )

                elif data.get("type") in ["mic-audio-end", "text-input"]:
                    await websocket.send_text(
                        json.dumps({"type": "full-text", "text": "Thinking..."})
                    )
                    if data.get("type") == "text-input":
                        user_input = data.get("text")
                    else:
                        user_input: np.ndarray | str = received_data_buffer

                    received_data_buffer = np.array([])

                    try:
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "control",
                                    "text": "conversation-chain-start",
                                }
                            )
                        )
                        # await asyncio.to_thread(
                        #     service_context.open_llm_vtuber.conversation_chain,
                        #     user_input=user_input,
                        # )

                        #! TODO
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
                        current_conversation_task = None
                        if ai_message_buffer:
                            store_message(conf_uid, current_history_uid, "ai", ai_message_buffer)
                            logger.info(
                                f"Stored AI message: {ai_message_buffer[:50]}..."
                            )

                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "control",
                                    "text": "conversation-chain-end",
                                }
                            )
                        )
                        logger.info("One Conversation Loop Completed")
                    except asyncio.CancelledError:
                        #! TODO: Handle interruption memory and clean up
                        logger.info("Conversation task was cancelled.")
                        if ai_message_buffer:
                            store_message(conf_uid, current_history_uid, "ai", ai_message_buffer)
                            logger.info(
                                f"Stored interrupted AI message: {ai_message_buffer[:50]}..."
                            )
                    except InterruptedError as e:
                        logger.info(f"Conversation was interrupted: {e}")

                elif data.get("type") == "fetch-configs":
                    config_files = scan_config_alts_directory(
                        session_service_context.system_config.get(
                            "CONFIG_ALTS_DIR", "config_alts"
                        )
                    )
                    await websocket.send_text(
                        json.dumps({"type": "config-files", "files": config_files})
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
                elif data.get("type") == "create-new-history":
                    current_history_uid = create_new_history(conf_uid)
                    session_service_context.llm_engine.clear_memory()
                    await websocket.send_text(
                        json.dumps({
                            "type": "new-history-created",
                            "history_uid": current_history_uid
                        })
                    )
                    continue
                elif data.get("type") == "delete-history":
                    history_uid = data.get("history_uid")
                    if history_uid:
                        success = delete_history(conf_uid, history_uid)
                        await websocket.send_text(
                            json.dumps({
                                "type": "history-deleted",
                                "success": success,
                                "history_uid": history_uid
                            })
                        ) 
                        if history_uid == current_history_uid:
                            current_history_uid = None
                        continue
                else:
                    logger.info("Unknown data type received.")

        except WebSocketDisconnect:
            connected_clients.remove(websocket)

        if ai_message_buffer:
            store_message(conf_uid, current_history_uid, "ai", ai_message_buffer)

    

    return router
