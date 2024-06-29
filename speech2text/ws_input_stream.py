import json
import numpy as np
import websocket
import threading


class InputStream:

    def __init__(
        self, ws_url: str, samplerate: int, channels: int, callback, buffersize: int
    ):
        """
        Initializes the InputStream object with the specified parameters.

        Parameters:
            ws_url (str): The URL of the WebSocket server. Like `ws://localhost:8000/server-ws`.
            samplerate (int): The sample rate of the audio stream.
            channels (int): The number of audio channels.
            callback (callable): The callback function to process incoming audio data.
            blocksize (int): The block size of the audio stream.

        """
        self.ws_url = ws_url
        self.samplerate = samplerate
        self.channels = channels
        self.buffersize = buffersize
        self.callback = callback

        self.ws = self.init_ws()

    def start(self):
        """
        Start listening for audio data from the websocket connection.
        Non-blocking.

        Parameters:
            None

        Returns:
            None
        """
        thread = threading.Thread(target=self.ws.run_forever)
        thread.start()

    def stop(self):
        """
        Stop listening for audio data from the websocket connection.

        Parameters:
            None

        Returns:
            None
        """
        # once the ws is closed, the server will send 'close-mic' message to the front end, so no need to send it here.
        self.ws.close()

    def init_ws(self) -> websocket.WebSocketApp:
        """
        Initializes the WebSocket connection.

        Parameters:
            None

        Returns:
            websocket.WebSocketApp: The WebSocketApp object.
        """

        def on_message(ws, message):
            data = json.loads(message)
            if data.get("type") == "audio-stream":
                received_data = np.array(data["audio"], dtype=np.float32)
                self.callback(received_data.reshape(-1, 1))

        def on_error(ws, error):
            print("Error:", error)

        def on_close(ws, close_status_code, close_msg):
            pass

            print("### closed ###")

        def on_open(ws):
            print("Start waiting for audio data from front end...")
            print("attempt to send initialization message to front end...")
            payload = {
                "type": "init-audio",
                "params": {
                    "samplerate": self.samplerate,
                    "channels": self.channels,
                    "buffersize": self.buffersize,
                },
            }
            ws.send(json.dumps(payload))
            print("Sent initialization message to front end.")

        return websocket.WebSocketApp(
            url=self.ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

import sounddevice as sd
if __name__ == "__main__":
    buffer = []

    def callback(data):
        buffer.append(data.copy())
    
    def audio_callback(self, indata, frames=None, time=None, status=None):
        buffer.append(indata)
        # buffer.append(indata.copy())

    ws_url = "ws://localhost:8000/server-ws"
    samplerate = 16000
    channels = 1
    blocksize = 1024

    # input_stream = InputStream(ws_url, samplerate, channels, callback, blocksize)
    # input_stream.start()
    # input("started. Press enter to stop.")
    # input_stream.stop()
    # input("Stopped listening for audio data.")
    # print(buffer)

    input("NEXT Press Enter to continue...")
    buffer = []
    gogo = sd.InputStream(
        samplerate=samplerate,
        channels=1,
        callback=audio_callback,
        blocksize=800,
    )
    input("start? ")
    gogo.start()
    input("end? ")
    gogo.stop()
    print(buffer)
