
# Original code by David Ng in [GlaDOS](https://github.com/dnhkng/GlaDOS), licensed under the MIT License
# https://opensource.org/licenses/MIT# 
# Modifications by Yi-Ting Chiu as part of Open-LLM-VTuber, licensed under the MIT License
# https://opensource.org/licenses/MIT
# 
#

import threading
import queue
from pathlib import Path
from typing import Callable, List

import numpy as np
import sounddevice as sd
from loguru import logger

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import vad
import ws_input_stream




class VoiceRecognitionVAD:
    def __init__(
        self, 
        asr_transcribe_func: Callable, 
        ws_url: str = None,
        wake_word: str | None = None, 
        
    ) -> None:
        """
        Initializes the VoiceRecognition class, setting up necessary models, streams, and queues.

        This class is not thread-safe, so you should only use it from one thread. It works like this:
        1. The audio stream is continuously listening for input.
        2. The audio is buffered until voice activity is detected. This is to make sure that the
            entire sentence is captured, including before voice activity is detected.
        2. While voice activity is detected, the audio is stored, together with the buffered audio.
        3. When voice activity is not detected after a short time (the PAUSE_LIMIT), the audio is
            transcribed. If voice is detected again during this time, the timer is reset and the
            recording continues.
        4. After the voice stops, the listening stops, and the audio is transcribed.
        5. If a wake word is set, the transcribed text is checked for similarity to the wake word.
        6. The function is called with the transcribed text as the argument.
        7. The audio stream is reset (buffers cleared), and listening continues.

        Args:
            asr_transcribe_func (Callable): The function to use for automatic speech recognition.
            ws_url (str, optional): The WebSocket URL to use for audio input. Defaults to None. If provided, the audio input stream will use WebSockets instead of sounddevice. For example: `ws://localhost:8000/server-ws`.
            wake_word (str, optional): The wake word to use for activation. Defaults to None.
            
        """

        # Set up some constants
        # Using pathlib for OS-independent paths
        self.VAD_MODEL_PATH = Path(current_dir + "/models/silero_vad.onnx")
        self.SAMPLE_RATE = 16000  # Sample rate for input stream
        self.VAD_SIZE = 50  # Milliseconds of sample for Voice Activity Detection (VAD)
        self.VAD_SIZE = 32  # Milliseconds of sample for Voice Activity Detection (VAD)
        self.VAD_THRESHOLD = 0.7  # Threshold for VAD detection
        self.BUFFER_SIZE = 600  # Milliseconds of buffer before VAD detection
        self.PAUSE_LIMIT = 1300  # Milliseconds of pause allowed before processing
        self.WAKE_WORD = "computer"  # Wake word for activation
        self.SIMILARITY_THRESHOLD = 2  # Threshold for wake word similarity


        # Set up the audio input stream
        if isinstance(ws_url, str):
            self.input_stream = self._setup_ws_audio_stream(ws_url)
        else:
            self.input_stream = self._setup_sd_audio_stream()

        # self.input_stream = self._setup_sd_audio_stream()

        self._setup_vad_model()
        self.transcribe = asr_transcribe_func

        # Initialize sample queues and state flags
        self.samples = []
        self.sample_queue = queue.Queue()
        self.buffer = queue.Queue(maxsize=self.BUFFER_SIZE // self.VAD_SIZE)
        self.recording_started = False
        self.gap_counter = 0
        self.wake_word = wake_word

    def _setup_sd_audio_stream(self):
        """
        Sets up the audio input stream with sounddevice.
        """
        return sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(self.SAMPLE_RATE * self.VAD_SIZE / 1000),
        ) # samplerate * VAD_SIZE / 1000
          # 16000 * 50 / 1000 = 800
          # 512 = 16000 * 32 / 1000
    
    def _setup_ws_audio_stream(self, ws_url: str):
        """
        Sets up the audio input stream with websockets.
        """
        return ws_input_stream.InputStream(
            ws_url=ws_url,
            samplerate=self.SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            buffersize=int(self.SAMPLE_RATE * self.VAD_SIZE / 1000),
        )

    def _setup_vad_model(self):
        """
        Loads the Voice Activity Detection (VAD) model.
        """
        self.vad_model = vad.VAD(model_path=self.VAD_MODEL_PATH)
        

    def audio_callback(self, indata, frames=None, time=None, status=None):
        """
        Callback function for the audio stream, processing incoming data.

        Args:
            indata (np.ndarray): The incoming audio data.
            frames (int): The number of frames in the audio data.
            time (sounddevice.CallbackTimeInfo): Timestamps for the audio data.
            status (sounddevice.CallbackFlags): Flags for the audio data.
        """
        print("audio callback" + str(indata))
        # input("audio callback")
        data = indata.copy()
        data = data.squeeze()  # Reduce to single channel if necessary
        vad_confidence = self.vad_model.process_chunk(data) > self.VAD_THRESHOLD
        self.sample_queue.put((data, vad_confidence))

    # def start(self):
    #     """
    #     [DEPRECATED] Starts the Glados voice assistant, continuously listening for input and responding.
    #     """
    #     logger.info("Starting Listening...")
    #     self.input_stream.start()
    #     logger.info("Listening Running")
    #     return self._listen_and_respond()
    
    def start_listening(self) -> str:
        """
        Start listening for audio input and responds appropriately when active voice is detected.
        This function will return the transcribed text once a pause is detected.
        It uses the `transcribe` function provided in the constructor to transcribe the audio.
        
        Returns:
            str: The transcribed text
        """
        logger.info("Starting Listening...")
        self.input_stream.start()
        logger.info("Listening Running")
        return self._listen_and_respond(returnText=True)

    def _listen_and_respond(self, returnText=False):
        """
        Listens for audio input and responds appropriately when the wake word is detected.
        """
        logger.info("Listening...")
        while True:  # Loop forever, but is 'paused' when new samples are not available
            sample, vad_confidence = self.sample_queue.get()
            result = self._handle_audio_sample(sample, vad_confidence)

            if result:
                if returnText:
                    # if we return the text and are not starting the listening again, we can reset the recorder without blocking
                    threading.Thread(target=self.reset).start()
                    # self.reset()
                    return result
                self.reset()
                self.input_stream.start()

    def _handle_audio_sample(self, sample, vad_confidence):
        """
        Handles the processing of each audio sample.
        """
        if not self.recording_started:
            self._manage_pre_activation_buffer(sample, vad_confidence)
        else:
            return self._process_activated_audio(sample, vad_confidence)

    def _manage_pre_activation_buffer(self, sample, vad_confidence):
        """
        Manages the buffer of audio samples before activation (i.e., before the voice is detected).
        """
        if self.buffer.full():
            self.buffer.get()  # Discard the oldest sample to make room for new ones
        self.buffer.put(sample)

        if vad_confidence:  # Voice activity detected
            self.samples = list(self.buffer.queue)
            self.recording_started = True

    def _process_activated_audio(self, sample: np.ndarray, vad_confidence: bool):
        """
        Processes audio samples after activation (i.e., after the wake word is detected).

        Uses a pause limit to determine when to process the detected audio. This is to
        ensure that the entire sentence is captured before processing, including slight gaps.
        """

        self.samples.append(sample)

        if not vad_confidence:
            self.gap_counter += 1
            if self.gap_counter >= self.PAUSE_LIMIT // self.VAD_SIZE:
                return self._process_detected_audio()
        else:
            self.gap_counter = 0

    # def _wakeword_detected(self, text: str) -> bool:
    #     """
    #     Calculates the nearest Levenshtein distance from the detected text to the wake word.

    #     This is used as 'Glados' is not a common word, and Whisper can sometimes mishear it.
    #     """
    #     words = text.split()
    #     closest_distance = min(
    #         [distance(word.lower(), self.wake_word) for word in words]
    #     )
    #     return closest_distance < SIMILARITY_THRESHOLD

    def _process_detected_audio(self):
        """
        Processes the detected audio and generates a response.
        """
        logger.info("Detected pause after speech. Processing...")

        logger.info("Stopping listening...")
        self.input_stream.stop()
        

        detected_text = self.asr(self.samples)

        if detected_text:
            logger.info(f"Detected: '{detected_text}'")
            return detected_text

        # these two lines will never be reached because I made the function return the detected text
        # so the reset function will be called in the _listen_and_respond function instead
        # self.reset()
        # self.input_stream.start()

    def asr(self, samples: List[np.ndarray]) -> str:
        """
        Performs automatic speech recognition on the collected samples.
        """
        audio = np.concatenate(samples)

        detected_text = self.transcribe(audio)
        return detected_text

    def reset(self):
        """
        Resets the recording state and clears buffers.
        """
        logger.info("Resetting recorder...")
        self.recording_started = False
        self.samples.clear()
        self.gap_counter = 0
        with self.buffer.mutex:
            self.buffer.queue.clear()




# if __name__ == "__main__":
    # demo = VoiceRecognition()
    # demo.start()
    # text = demo.transcribe_once()
    # print(text)