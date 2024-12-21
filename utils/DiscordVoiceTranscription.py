import asyncio
import io
import os
import threading
import time

import discord
import dotenv
import numpy as np
import torch
import torchaudio
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink
from discord.opus import Decoder as OpusDecoder
from loguru import logger

from asr.asr_with_vad import PAUSE_LIMIT, VAD_THRESHOLD
from asr.vad import SAMPLE_RATE
from utils.DiscordInputList import DiscordInputList
from utils.OutputQueue import OutputQueue


# model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
# (get_speech_ts, save_audio, read_audio, VADIterator, collect_chunks) = utils


class VoiceActivityBot(discord.Client):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:  # Check if instance already exists
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super(VoiceActivityBot, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, intents=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        dotenv.load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")
        super().__init__(intents=intents)
        self.voice_client = None
        self.message_channel = 1212177824803328004
        self.voice_channel = None
        self.audio_buffer = {}  # Store audio per speaker {username: [audio_frames]}
        # Standard sample rate for PCM audio
        self.recording_task = None
        self.thread = threading.Thread(target=self.run_bot, daemon=True, args=[self.bot_token])
        self.thread.start()

    def run_bot(self, bot_token):
        # Run the bot
        asyncio.run(self.start(bot_token))

    async def on_ready(self):
        logger.critical(f"Bot is ready and logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!join"):
            if message.author.voice and message.author.voice.channel:
                await self.join_voice_channel(message.author.voice.channel, message.channel)
            else:
                await message.channel.send("You need to join a voice channel first.")

        elif message.content.startswith("!leave"):
            await self.leave_voice_channel(message.channel)

        elif message.content.startswith("!capture"):
            await self.start_capture(message.channel)

    async def _send_text_message(self, text):
        channel = self.get_channel(self.message_channel)
        await channel.send(text)

    def send_message(self, text):
        asyncio.run_coroutine_threadsafe(self._send_text_message(text), asyncio.get_event_loop()).result()

    async def join_voice_channel(self, channel, text_channel):
        try:
            self.voice_client = channel
            self.voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
            await text_channel.send(f"Connected to voice channel: {channel.name}")
            await self.start_capture(text_channel)
        except Exception as e:
            await text_channel.send(f"Failed to join voice channel: {e}")

    async def leave_voice_channel(self, text_channel):
        if self.voice_client is not None:
            await self.voice_client.disconnect()
            self.voice_client = None
            await text_channel.send("Disconnected from the voice channel.")
        else:
            await text_channel.send("I'm not connected to any voice channel.")

    # async def consumer(self, channel: discord.TextChannel):
    #     """"Fetch chunks from the queue and send them as messages to a Discord channel."""
    #     while True:
    #         text_chunk = OutputQueue().get_output()
    #         if text_chunk is None:
    #             return
    #         await channel.send(text_chunk)
    #        # Send the text chunk to Discord

    async def start_capture(self, text_channel):
        if not self.voice_client or not self.voice_client.is_connected():
            await text_channel.send("I'm not connected to a voice channel.")
            return

        await text_channel.send("Started capturing audio.")
        sink = StreamedNumPySink()
        self.voice_client.listen(sink)

        # Start the consumer once and let it run forever
        ##  asyncio.create_task(self.consumer(text_channel))

        try:
            while True:
                text_chunk = OutputQueue().get_output()
                if text_chunk is None:
                    return
                await text_channel.send(text_chunk)
                if not self.voice_client or not self.voice_client.is_connected():
                    self.voice_client = await self.voice_channel.connect(cls=voice_recv.VoiceRecvClient)
                    self.voice_client.listen(sink)
                logger.success("Listening to new message")
                # asyncio.create_task(self.consumer(text_channel))
            ## await asyncio.sleep(0.1)  # keep this loop alive
        except Exception as e:
            await text_channel.send(f"Error: {str(e)}")


class StreamedNumPySink(AudioSink):
    def wants_opus(self) -> bool:
        return False

    def __init__(self):
        super().__init__()
        self.vad_sample_rate = SAMPLE_RATE
        self.sample_rate = OpusDecoder.SAMPLING_RATE
        self.channels = OpusDecoder.CHANNELS
        self.sample_width = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
        self.pause_limit = PAUSE_LIMIT / 1000
        self.min_duration = 1  # minimum length of speech
        self.ttfb_start_time = 0

        self.vad_threshold = VAD_THRESHOLD  # Confidence threshold for VAD
        self.active_streams = {}  # {speaker_name: BytesIO stream}
        self.last_active_times = {}  # {speaker_name: last active timestamp}
        self.finalized_sessions = []  # List of finalized sessions
        self.last_global_activity = time.time()  # Last activity time
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self.keep_time, daemon=True)
        self.thread.start()

    def write(self, user, data):
        """
        Write PCM data for a user into their respective stream.
        """
        if user is None or not hasattr(user, 'display_name'):
            return

        user_id = user.display_name
        current_time = time.time()

        # Update global activity time
        self.last_global_activity = current_time

        # Initialize or update the active stream for the user
        if user_id not in self.active_streams:
            self.active_streams[user_id] = io.BytesIO()
            self.last_active_times[user_id] = current_time

        # Append PCM data to the stream
        self.active_streams[user_id].write(data.pcm)
        self.last_active_times[user_id] = current_time

    def process_conversation_end(self):
        """
        Finalize all remaining streams and process the conversation data.
        """
        for speaker_name in list(self.active_streams.keys()):
            self.finalize_stream(speaker_name)

        # Process the finalized data with VAD
        start_time = time.time()
        # Reset for the next conversation
        if len(self.finalized_sessions) > 0:
            ##  self.apply_vad_to_finalized_audio() ## disabling as VAD is a part of the ASR with faster-whisper
            DiscordInputList().add_input({'type': 'audio', 'data': self.finalized_sessions})
        self.reset_state()

    def finalize_stream(self, speaker_name):
        """
        Finalize a single speaker's stream.
        """
        if speaker_name not in self.active_streams:
            return

        # Retrieve audio from the stream
        stream = self.active_streams[speaker_name]
        stream.seek(0)
        raw_data = stream.read()
        stream.close()

        # Convert PCM data to NumPy array
        audio_array = np.frombuffer(raw_data, dtype=np.int16)
        audio_array = self.resample_pcm_with_torchaudio(pcm_data=audio_array, orig_sample_rate=self.sample_rate,
                                                        target_sample_rate=self.vad_sample_rate)

        # Append the finalized session
        self.finalized_sessions.append({"name": speaker_name, "data": audio_array})

        # Remove the stream
        del self.active_streams[speaker_name]
        del self.last_active_times[speaker_name]

    # def apply_vad_to_finalized_audio(self):
    #     """
    #     Apply Silero VAD to all finalized speaker audio.
    #     """
    #     for session in self.finalized_sessions:
    #         audio_array = session["data"]
    #
    #         # Resample to 16 kHz (required for Silero VAD)
    #         if self.sample_rate != self.vad_sample_rate:
    #             audio_array = self.resample_pcm_with_torchaudio(audio_array, self.sample_rate, self.vad_sample_rate)
    #
    #         # Convert NumPy array to PyTorch tensor
    #         audio_tensor = self.convert_to_tensor(audio_array)
    #
    #         # Run VAD on the audio
    #         speech_timestamps = get_speech_ts(audio_tensor, model, sampling_rate=self.vad_sample_rate)
    #
    #         # Extract speech chunks based on VAD results
    #         if not speech_timestamps:
    #             continue
    #         speech_data_tensor = collect_chunks(speech_timestamps, audio_tensor)
    #
    #         # Convert the resulting PyTorch tensor back to NumPy array
    #         speech_data = self.convert_to_array(speech_data_tensor)
    #         # Replace session data with VAD-processed audio
    #         session["data"] = speech_data

    def keep_time(self):
        """
        Periodically check for global inactivity and finalize speakers.
        """
        while not self._stop_event.is_set():
            current_time = time.time()

            # Check for global inactivity
            if current_time - self.last_global_activity > self.pause_limit:
                self.process_conversation_end()

            time.sleep(0.1)

    def reset_state(self):
        """
        Reset state for the next conversation.
        """
        self.active_streams.clear()
        self.last_active_times.clear()
        self.finalized_sessions.clear()
        self.last_global_activity = time.time()

    def cleanup(self):
        """
        Clean up all resources.
        """
        self._stop_event.set()
        self.thread.join()
        self.process_conversation_end()

    def resample_pcm_with_torchaudio(self, pcm_data, orig_sample_rate, target_sample_rate):
        """
        Resample PCM data from the original sample rate to the target sample rate using TorchAudio.

        Args:
            pcm_data (numpy.ndarray): PCM data as a NumPy array (int16 format).
            orig_sample_rate (int): Original sample rate (e.g., 48000 Hz).
            target_sample_rate (int): Target sample rate (e.g., 16000 Hz).

        Returns:
            numpy.ndarray: Resampled PCM data as a NumPy array.

        """
        if self.channels == 2:
            pcm_data = pcm_data.reshape(-1, 2)  # Shape: (num_samples, 2)
            # Convert stereo to mono by averaging channels
            pcm_data = pcm_data.mean(axis=1).astype(np.int16)
        audio_tensor = self.convert_to_tensor(pcm_data)
        resampled_audio = torchaudio.functional.resample(
            audio_tensor, orig_freq=orig_sample_rate, new_freq=target_sample_rate
        )
        resampled_audio = self.convert_to_array(resampled_audio)
        return resampled_audio

    def convert_to_tensor(self, audio_array):
        if not isinstance(audio_array, np.ndarray):
            raise ValueError("Input must be a NumPy array.")

        # Convert to float32 and normalize to [-1.0, 1.0]
        return torch.tensor(audio_array, dtype=torch.float32) / 32768.0

    def convert_to_array(self, audio_tensor):
        if not isinstance(audio_tensor, torch.Tensor):
            raise ValueError("Input must be a PyTorch tensor.")

        # Scale back to int16 and clamp to valid range
        return (audio_tensor * 32768.0).clamp(-32768, 32767).short().numpy()
