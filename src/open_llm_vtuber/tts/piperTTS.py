import os
import threading
import subprocess
import platform
from .tts_interface import TTSInterface


class TTSEngine(TTSInterface):

    file_extension: str = "wav"
    new_audio_dir: str = "cache"
    # process: subprocess.Popen = None

    # Voice path (the path of the .onnx file (the .onnx.json file needs to be present as well) for the voice model)
    voice_model_path: str = None

    def __init__(self, voice_path, verbose=False):
        """Initialize the Piper TTS client."""
        self.verbose = verbose
        self.voice_model_path = voice_path

        if not self.voice_model_path or not os.path.exists(self.voice_model_path):
            print(
                f'Error: Piper TTS voice model not found at path "{self.voice_model_path}"'
            )
            print("Downloading the default voice model...")
            import scripts.install_piper_tts

            scripts.install_piper_tts.download_default_model()
            print("Using the default voice model for PiperTTS.")
            self.voice_model_path = os.path.join(
                "models", "piper_voice", "en_US-amy-medium.onnx"
            )

        self.piper_binary_path: str = (
            os.path.join("models", "piper_tts", "piper.exe")
            if platform.system() == "Windows"
            else os.path.join("models", "piper_tts", "piper")
        )

        if not os.path.exists(self.piper_binary_path):
            print(f"Piper TTS binary not found at {self.piper_binary_path}")
            print("Installing Piper TTS...")
            import scripts.install_piper_tts

            scripts.install_piper_tts.setup_piper_tts()

        # self.initialize_piper_cli()
        # can't initialize and keep the process open because of racing conditions

    def initialize_piper_cli(self) -> subprocess.Popen:
        try:
            # Construct and execute the Piper TTS command
            command = [
                self.piper_binary_path,
                "-m",
                self.voice_model_path,
                "-d",
                self.new_audio_dir,
            ]
            return subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            print(f"Error initializing Piper TTS: {e}")
            raise e

    def generate_audio(self, text: str, file_name_no_ext=None):
        def run_piper_tts():
            with self.initialize_piper_cli() as process:
                try:
                    stdout, stderr = process.communicate(input=text)

                    if process.returncode != 0:
                        if self.verbose:
                            print(f"Error running Piper TTS command: {stderr}")
                        return None

                    output = stdout.strip()

                    if not output.endswith(".wav"):
                        if self.verbose:
                            print(f"Error running Piper TTS command:")
                            print(f"Unexpected output: {output}")
                        return None

                    print(f'\n\nGenerated audio file: ""{output}""\n\n')
                    return output

                except subprocess.CalledProcessError as e:
                    if self.verbose:
                        print(f"Error running Piper TTS command: {e}")
                    return None
                finally:
                    process.kill()
                    process.wait()

        thread = threading.Thread(target=run_piper_tts)
        thread.start()
        thread.join()
