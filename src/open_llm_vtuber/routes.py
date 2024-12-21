import os
import json
import asyncio
import numpy as np
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from .conversation import conversation_chain
from .service_context import ServiceContext
from .utils.config_loader import (
    load_config,
    scan_config_alts_directory,
    scan_bg_directory,
)


def create_routes(default_context_cache: ServiceContext):
    router = APIRouter()
    connected_clients = []

    @router.websocket("/client-ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        await websocket.send_text(
            json.dumps({"type": "full-text", "text": "Connection established"})
        )

        connected_clients.append(websocket)
        logger.info("Connection established")

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
                    "type": "set-model",
                    "model_info": session_service_context.live2d_model.model_info,
                }
            )
        )
        received_data_buffer = np.array([])
        # start mic
        await websocket.send_text(json.dumps({"type": "control", "text": "start-mic"}))

        current_conversation_task: asyncio.Task | None = None

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "interrupt-signal":
                    if current_conversation_task is not None:
                        # session_service_context.open_llm_vtuber.interrupt(data.get("text"))
                        if not current_conversation_task.cancel():
                            logger.info(
                                "Conversation task was NOT cancelled. Likely because there is no running task."
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
                            )
                        )

                        await current_conversation_task
                        current_conversation_task = None

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
                        await handle_config_switch(
                            websocket, session_service_context, config_file_name
                        )
                elif data.get("type") == "fetch-backgrounds":
                    bg_files = scan_bg_directory()
                    await websocket.send_text(
                        json.dumps({"type": "background-files", "files": bg_files})
                    )
                else:
                    logger.info("Unknown data type received.")

        except WebSocketDisconnect:
            connected_clients.remove(websocket)

    async def handle_config_switch(
        websocket: WebSocket, service_context: ServiceContext, config_file_name: str
    ) -> None:
        """
        Handle the configuration switch request.
        Change the configuration to a new config and notify the client.

        Parameters:
        - websocket (WebSocket): The WebSocket connection.
        - service_context (ServiceContext): The ServiceContext instance.
            New configuration will be loaded into this instance.
        - config_file_name (str): The name of the configuration file.
        """
        try:
            new_config = None

            if config_file_name == "conf.yaml":
                new_config = load_config("conf.yaml")

            config_alts_dir = service_context.system_config.get(
                "CONFIG_ALTS_DIR", "config_alts"
            )
            file_path = os.path.join(config_alts_dir, config_file_name)
            new_config = load_config(file_path)

            if new_config:
                service_context.load_from_config(new_config)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "config-switched",
                            "message": f"Switched to config: {config_file_name}",
                        }
                    )
                )
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "set-model",
                            "model_info": service_context.live2d_model.model_info,
                        }
                    )
                )
                logger.info(f"Configuration switched to {config_file_name}")

        except Exception as e:
            logger.error(f"Error switching configuration: {e}")
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Error switching configuration: {str(e)}",
                    }
                )
            )

    return router
