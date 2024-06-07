
# Original code by David Ng in [GlaDOS](https://github.com/dnhkng/GlaDOS), licensed under the MIT License
# https://opensource.org/licenses/MIT# 
# Modifications by Yi-Ting Chiu as part of OpenLLM-VTuber, licensed under the MIT License
# https://opensource.org/licenses/MIT
# 
#


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
print(f"\nDIRRRR\n{current_dir}")

import asr, vad

# Using pathlib for OS-independent paths
ASR_MODEL_NAME = "distil-medium.en"
VAD_MODEL_PATH = Path(current_dir + "/models/silero_vad.onnx")
print(f"\nVAD_MODEL_PATH\n{VAD_MODEL_PATH}")
SAMPLE_RATE = 16000  # Sample rate for input stream
VAD_SIZE = 50  # Milliseconds of sample for Voice Activity Detection (VAD)
VAD_THRESHOLD = 0.7  # Threshold for VAD detection
BUFFER_SIZE = 600  # Milliseconds of buffer before VAD detection
PAUSE_LIMIT = 1300  # Milliseconds of pause allowed before processing
WAKE_WORD = "computer"  # Wake word for activation
SIMILARITY_THRESHOLD = 2  # Threshold for wake word similarity

# Rest of the class remains unchanged
ASR_MODEL_NAME = "distil-medium.en"
VAD_MODEL_PATH = Path(current_dir + "/models/silero_vad.onnx")
SAMPLE_RATE = 16000  # Sample rate for input stream
VAD_SIZE = 50  # Milliseconds of sample for Voice Activity Detection (VAD)
VAD_THRESHOLD = 0.7  # Threshold for VAD detection
BUFFER_SIZE = 600  # Milliseconds of buffer before VAD detection
PAUSE_LIMIT = 1300  # Milliseconds of pause allowed before processing
WAKE_WORD = "computer"  # Wake word for activation
SIMILARITY_THRESHOLD = 2  # Threshold for wake word similarity


class VoiceRecognition:
    def __init__(
        self, wake_word: str | None = None, function: Callable = print
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
            wake_word (str, optional): The wake word to use for activation. Defaults to None.
            func (Callable, optional): The function to call when the wake word is detected. Defaults to print.
        """

        self._setup_audio_stream()
        self._setup_vad_model()
        self._setup_asr_model()

        # Initialize sample queues and state flags
        self.samples = []
        self.sample_queue = queue.Queue()
        self.buffer = queue.Queue(maxsize=BUFFER_SIZE // VAD_SIZE)
        self.recording_started = False
        self.gap_counter = 0
        self.wake_word = wake_word
        self.func = function

    def _setup_audio_stream(self):
        """
        Sets up the audio input stream with sounddevice.
        """
        self.input_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=self.audio_callback,
            blocksize=int(SAMPLE_RATE * VAD_SIZE / 1000),
        )

    def _setup_vad_model(self):
        """
        Loads the Voice Activity Detection (VAD) model.
        """
        self.vad_model = vad.VAD(model_path=VAD_MODEL_PATH)

    def _setup_asr_model(self):
        self.asr_model = asr.ASR(model=ASR_MODEL_NAME)

    def audio_callback(self, indata, frames, time, status):
        """
        Callback function for the audio stream, processing incoming data.
        """
        data = indata.copy()
        data = data.squeeze()  # Reduce to single channel if necessary
        vad_confidence = self.vad_model.process_chunk(data) > VAD_THRESHOLD
        self.sample_queue.put((data, vad_confidence))

    def start(self):
        """
        Starts the Glados voice assistant, continuously listening for input and responding.
        """
        logger.info("Starting Listening...")
        self.input_stream.start()
        logger.info("Listening Running")
        return self._listen_and_respond()
    
    def transcribe_once(self):
        """
        Start listening for audio input and responds appropriately when active voice is detected.
        This function will return the transcribed text once a pause is detected.
        
        Returns:
            str: The transcribed text
        """
        self.input_stream.start()
        logger.info("Starting Listening...")
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
                self.reset()
                if returnText:
                    return result
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
            if self.gap_counter >= PAUSE_LIMIT // VAD_SIZE:
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

            # if self.wake_word is not None:
            #     if self._wakeword_detected(detected_text):
            #         logger.info("Wake word detected!")
            #         self.func(detected_text)
            #     else:
            #         logger.info("No wake word detected. Ignoring...")
            # else:
            #     self.func(detected_text)

        # these two lines will never be reached because I made the function return the detected text
        # so the reset function will be called in the _listen_and_respond function instead
        self.reset()
        self.input_stream.start()

    def asr(self, samples: List[np.ndarray]) -> str:
        """
        Performs automatic speech recognition on the collected samples.
        """
        audio = np.concatenate(samples)

        detected_text = self.asr_model.transcribe(audio)
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




if __name__ == "__main__":
    demo = VoiceRecognition()
    demo.start()
    # text = demo.transcribe_once()
    # print(text)