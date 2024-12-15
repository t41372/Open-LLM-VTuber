import json
import asyncio
import numpy as np
import os
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from .config.config_manager import (
    load_config_with_env,
    load_config_file_with_guess_encoding,
    scan_config_alts_directory,
    load_new_config,
    scan_bg_directory
)


def create_routes(service_context):

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

        service_context.set_audio_output_func(
            lambda s, f: audio_playback_func(websocket, service_context, s, f)
        )

        await websocket.send_text(
            json.dumps({"type": "set-model", "text": service_context.live2d_model.model_info})
        )
        received_data_buffer = np.array([])
        # start mic
        await websocket.send_text(
            json.dumps({"type": "control", "text": "start-mic"})
        )

        conversation_task = None

        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("type") == "interrupt-signal":
                    if conversation_task is not None:
                        service_context.open_llm_vtuber.interrupt(data.get("text"))

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

                    async def _run_conversation():
                        try:
                            await websocket.send_text(
                                json.dumps({"type": "control", "text": "conversation-chain-start"})
                            )
                            await asyncio.to_thread(
                                service_context.open_llm_vtuber.conversation_chain,
                                user_input=user_input,
                            )
                            await websocket.send_text(
                                json.dumps({"type": "control", "text": "conversation-chain-end"})
                            )
                            logger.info("One Conversation Loop Completed")
                        except asyncio.CancelledError:
                            logger.info("Conversation task was cancelled.")
                        except InterruptedError as e:
                            logger.info(f"Conversation was interrupted: {e}")

                    conversation_task = asyncio.create_task(_run_conversation())

                elif data.get("type") == "fetch-configs":
                    config_files = scan_config_alts_directory(service_context.config)
                    await websocket.send_text(
                        json.dumps({"type": "config-files", "files": config_files})
                    )
                elif data.get("type") == "switch-config":
                    config_file = data.get("file")
                    if config_file:
                        result = await handle_config_switch(websocket, service_context, config_file)
                        if result:
                            l2d, open_llm_vtuber = result
                elif data.get("type") == "fetch-backgrounds":
                    bg_files = scan_bg_directory()
                    await websocket.send_text(
                        json.dumps({"type": "background-files", "files": bg_files})
                    )
                else:
                    logger.info("Unknown data type received.")

        except WebSocketDisconnect:
            connected_clients.remove(websocket)


    async def handle_config_switch(websocket: WebSocket, service_context, config_file: str):
        new_config = load_new_config(service_context.config, config_file)
        if new_config:
            try:
                l2d, open_llm_vtuber = service_context.switch_config(new_config)
                await websocket.send_text(
                    json.dumps(
                        {"type": "config-switched", "message": f"Switched to config: {config_file}"}
                    )
                )
                await websocket.send_text(
                    json.dumps({"type": "set-model", "text": l2d.model_info})
                )
                logger.info(f"Configuration switched to {config_file}")

                return l2d, open_llm_vtuber
            except Exception as e:
                logger.error(f"Error switching configuration: {e}")
                await websocket.send_text(
                    json.dumps(
                        {"type": "error", "message": f"Error switching configuration: {str(e)}"}
                    )
                )
        return None

    def audio_playback_func(websocket: WebSocket, service_context, sentence: str | None, filepath: str | None):
        if filepath is None:
            logger.info("No audio to be streamed. Response is empty.")
            return

        if sentence is None:
            sentence = ""

        logger.info(f"Playing {filepath}...")
        payload, duration = service_context.audio_preparer.prepare_audio_payload(
            audio_path=filepath,
            display_text=sentence,
            expression_list=service_context.live2d_model.extract_emotion(sentence),
        )
        logger.info("Payload prepared")

        async def _send_audio():
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(duration)

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(_send_audio())
        new_loop.close()

        logger.info("Audio played")

    return router
