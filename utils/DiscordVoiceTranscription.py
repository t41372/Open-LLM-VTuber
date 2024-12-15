import asyncio
import io
import os
import threading
import time

import discord
import dotenv
import numpy as np
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink
from discord.opus import Decoder as OpusDecoder
from loguru import logger

from asr.asr_with_vad import PAUSE_LIMIT


class VoiceActivityBot(discord.Client):
    def __init__(self, intents=None):
        dotenv.load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")
        super().__init__(intents=intents)
        self.voice_client = None
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

    async def join_voice_channel(self, channel, text_channel):
        try:
            self.voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
            await text_channel.send(f"Connected to voice channel: {channel.name}")
        except Exception as e:
            await text_channel.send(f"Failed to join voice channel: {e}")

    async def leave_voice_channel(self, text_channel):
        if self.voice_client is not None:
            await self.voice_client.disconnect()
            self.voice_client = None
            await text_channel.send("Disconnected from the voice channel.")
        else:
            await text_channel.send("I'm not connected to any voice channel.")

    def cb_func(self, member, vdata):
        print(f"got data for{member},{vdata}")

    async def start_capture(self, text_channel):
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                await text_channel.send("I'm not connected to a voice channel.")
                return
            await text_channel.send("Started capturing audio.")
            ##sink = BasicSink(self.cb_func)
            sink = StreamedNumPySink()
            self.voice_client.listen(sink)
            logger.info("Listening...")

        except Exception as e:
            logger.critical(f"Failed to start capture: {e}")


class StreamedNumPySink(AudioSink):
    def wants_opus(self) -> bool:
        return False

    def __init__(self):
        super().__init__()
        self.sample_rate = OpusDecoder.SAMPLING_RATE
        self.channels = OpusDecoder.CHANNELS
        self.sample_width = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
        self.pause_limit = PAUSE_LIMIT / 1000
        self.min_duration = 1 # minimum length of speech
        self.chunk_size = 1200  # Size of each chunk in bytes
        self.active_streams = {}  # {speaker_name: BytesIO stream}
        self.min_samples = int(self.sample_rate * self.min_duration)
        self.last_active_times = {}  # {speaker_name: last active timestamp}
        self.last_global_activity = time.time()  # Last time any speaker wrote data
        self.finalized_sessions = []  # List of finalized speaker sessions
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

    def finalize_stream(self, speaker_name):
        """
        Finalize a single speaker's stream and store it in the finalized sessions if it meets the minimum duration.
        """
        if speaker_name not in self.active_streams:
            return

        # Retrieve the stream and convert to NumPy array
        stream = self.active_streams[speaker_name]
        stream.seek(0)
        raw_data = stream.read()

        audio_array = np.frombuffer(raw_data, dtype=np.int16)
        if self.channels == 2:
            audio_array = audio_array.reshape(-1, 2)

        # Check if the audio meets the minimum duration threshold
        if len(audio_array) >= self.min_samples:
            # Append the finalized session
            self.finalized_sessions.append({"name": speaker_name, "data": audio_array})
        else:
            print(f"Ignored small chunk for {speaker_name}: {len(audio_array)} samples")

        # Clean up the stream
        stream.close()
        del self.active_streams[speaker_name]
        del self.last_active_times[speaker_name]

    def keep_time(self):
        """
        Periodically check for global inactivity and finalize the conversation if needed.
        """
        while not self._stop_event.is_set():
            current_time = time.time()

            # Finalize streams for speakers who have been inactive beyond the pause limit
            for speaker_name, last_active_time in list(self.last_active_times.items()):
                if current_time - last_active_time > self.pause_limit:
                    self.finalize_stream(speaker_name)

            # Finalize the conversation if no activity globally
            if current_time - self.last_global_activity > self.pause_limit:
                self.process_conversation_end()

            time.sleep(0.1)  # Small delay to reduce CPU usage

    def process_conversation_end(self):
        """
        Finalize all remaining streams and process the conversation data.
        """
        print("Conversation ended. Finalizing all streams...")

        # Finalize all remaining streams
        for speaker_name in list(self.active_streams.keys()):
            self.finalize_stream(speaker_name)

        # Process the finalized data
        self.process_finalized_sessions()

        # Reset state for the next conversation
        self.reset_state()

    def process_finalized_sessions(self):
        """
        Process all finalized speaker sessions.
        """
        for session in self.finalized_sessions:
            print(f"Speaker: {session['name']}, Data Shape: {session['data'].shape}")


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
        Clean up all resources and stop the background thread.
        """
        self._stop_event.set()
        self.thread.join()
        # Finalize any remaining streams
        for speaker_name in list(self.active_streams.keys()):
            self.finalize_stream(speaker_name)