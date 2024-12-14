import asyncio
import os
import threading
import time
from collections import defaultdict

import discord
import dotenv
import numpy as np
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink, VoiceData
from discord.opus import Decoder as OpusDecoder
from loguru import logger

from utils.DiscordInputList import DiscordInputList


class VoiceActivityBot(discord.Client):
    def __init__(self, intents=None):
        dotenv.load_dotenv()
        self.bot_token = os.getenv("BOT_TOKEN")
        super().__init__(intents=intents)
        self.voice_client = None
        self.audio_buffer = {}  # Store audio per speaker {username: [audio_frames]}
        self.sample_rate = 16000  # Standard sample rate for PCM audio
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

    async def start_capture(self, text_channel):
        try:
            if not self.voice_client or not self.voice_client.is_connected():
                await text_channel.send("I'm not connected to a voice channel.")
                return
            await text_channel.send("Started capturing audio.")
            sink = NumPySink()
            self.voice_client.listen(sink)
        except Exception as e:
            logger.critical(f"Failed to start capture: {e}")


class NumPySink(AudioSink):
    """Endpoint AudioSink that generates a wav file.
    Best used in conjunction with a silence generating sink. (TBD)
    """
    CHANNELS = OpusDecoder.CHANNELS
    SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
    SAMPLING_RATE = OpusDecoder.SAMPLING_RATE
    PAUSE_LIMIT = 1300

    def __init__(self):
        super().__init__()
        self.user_buffers = defaultdict(list)  # Buffers for each user's data
        self.last_active_time = {}  # Last activity time for each user
        self.transcription_delay = 1.3  # 1300ms delay to stop transcribing
        self.min_duration = 0.05  # Minimum duration in seconds (50ms)
        self.sample_rate = 16000  # Sample rate (16 kHz)
        self.input_queue = DiscordInputList()

    def wants_opus(self) -> bool:
        return False

    def write(self, user, data):
        """
        Capture PCM data from a Discord user, buffer it, and return transcriptions
        when the user stops speaking.

        Args:
            user (discord.User): The Discord user speaking.
            data (VoiceData): The PCM audio data received.

        Returns:
            list: A list of dicts with {name, timestamp, data} fields for transcriptions.
        """
        if user is None or not hasattr(user, 'name'):
            return

        current_time = time.time()
        user_id = user.id

        # Initialize user's buffer and last active time if not present
        if user_id not in self.user_buffers:
            self.user_buffers[user_id] = []
            self.last_active_time[user_id] = current_time

        # Append PCM data to the user's buffer with a timestamp
        self.user_buffers[user_id].append({
            'timestamp': current_time,
            'data': np.frombuffer(data.pcm, dtype=np.int16)
        })
        self.last_active_time[user_id] = current_time

        # Check for users who have stopped speaking
        to_transcribe = []
        for user_id, last_time in list(self.last_active_time.items()):
            if current_time - last_time > self.transcription_delay:
                # Combine the user's audio data into a single numpy array
                combined_data = []
                start_time = None

                for entry in self.user_buffers[user_id]:
                    duration = len(entry['data']) / self.sample_rate
                    if duration >= self.min_duration:
                        combined_data.append(entry['data'])
                        if start_time is None:
                            start_time = entry['timestamp']

                if combined_data:
                    # Concatenate all data into a single array
                    full_data = np.concatenate(combined_data)

                    # Append transcription data
                    to_transcribe.append({
                        'name': user.name,
                        'timestamp': start_time,
                        'data': full_data,
                        'type': 'audio'
                    })

                # Clear the user's buffer and remove their last active time
                del self.user_buffers[user_id]
                del self.last_active_time[user_id]

        # Return the transcriptions sorted by timestamp
        result = sorted(to_transcribe, key=lambda x: x['timestamp'])
        self.input_queue.add_input(result)

    def cleanup(self) -> None:
        try:
            self.user_buffers.clear()
            self.last_active_time.clear()
        except Exception as e:
            logger.warning("NumPySink got error closing file on cleanup", exc_info=True)
