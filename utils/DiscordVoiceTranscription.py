import discord
import asyncio
import numpy as np

from utils.InputQueue import InputQueue

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN"


class VoiceActivityBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.voice_client = None
        self.audio_buffer = {}  # Store audio per speaker {username: [audio_frames]}
        self.speaking_users = set()  # Track active speakers
        self.sample_rate = 16000  # Standard sample rate for PCM audio
        self.recording_task = None
        self.input_queue = InputQueue()

    async def on_ready(self):
        print(f"Bot is ready and logged in as {self.user}")

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
            self.voice_client = await channel.connect()
            self.voice_client.listen(self)  # Register this class to listen for audio
            await text_channel.send(f"Connected to voice channel: {channel.name}")
        except Exception as e:
            await text_channel.send(f"Failed to join voice channel: {e}")

    async def leave_voice_channel(self, text_channel):
        if self.voice_client is not None:
            if self.recording_task and not self.recording_task.done():
                self.recording_task.cancel()
            await self.voice_client.disconnect()
            self.voice_client = None
            await text_channel.send("Disconnected from the voice channel.")
        else:
            await text_channel.send("I'm not connected to any voice channel.")

    async def start_capture(self, text_channel):
        if not self.voice_client or not self.voice_client.is_connected():
            await text_channel.send("I'm not connected to a voice channel.")
            return

        if self.recording_task and not self.recording_task.done():
            await text_channel.send("Already capturing audio.")
            return

        await text_channel.send("Started automatic audio capture.")
        self.audio_buffer.clear()  # Reset the audio buffer
        self.speaking_users.clear()  # Clear active speakers
        self.recording_task = asyncio.create_task(self.capture_audio())

    async def capture_audio(self):
        """Automatically start and stop capturing based on speaking events."""
        try:
            while self.voice_client and self.voice_client.is_connected():
                if not self.speaking_users:
                    await asyncio.sleep(0.1)  # Wait until someone starts speaking
                    continue

                # Capture audio for active speakers
                pcm_frame = await self.voice_client.recv_audio()
                pcm_data = np.frombuffer(pcm_frame.data, dtype=np.int16)
                user_id = pcm_frame.ssrc

                # Map user ID to username
                username = self.get_username(user_id)
                if username:
                    if username not in self.audio_buffer:
                        self.audio_buffer[username] = []
                    self.audio_buffer[username].append(pcm_data)
                for username, frames in self.audio_buffer.items():
                    combined_audio = np.concatenate(frames)
                    self.input_queue.add_input({username: combined_audio})
                self.audio_buffer.clear()  # Clear buffer after processing

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error capturing audio: {e}")

    def on_speaking(self, user_id, speaking):
        """Track speaking users and manage automatic capture."""
        username = self.get_username(user_id)

        if speaking:
            if username:
                self.speaking_users.add(username)
        else:
            if username in self.speaking_users:
                self.speaking_users.remove(username)

    def get_username(self, user_id):
        """Resolve SSRC to Discord username."""
        for member in self.voice_client.channel.members:
            if member.id == user_id:
                return member.name
        return "Unknown"

