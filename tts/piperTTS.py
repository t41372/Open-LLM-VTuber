import os
import subprocess
import platform
from .tts_interface import TTSInterface


class TTSEngine(TTSInterface):

    file_extension: str = "wav"
    new_audio_dir: str = "./cache"

    # Voice path (the path of the .onnx file (the .onnx.json file needs to be present as well) for the voice model)
    voice_model_path: str = None

    def __init__(self, voice_path, verbose=False):
        """Initialize the Piper TTS client."""
        self.verbose = verbose
        self.voice_model_path = voice_path

        print("Initializing TTSEngine...")  # Log de início de inicialização

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

        print(f"Piper binary path: {self.piper_binary_path}")  # Log caminho do binário

        if not os.path.exists(self.piper_binary_path):
            print(f"Piper TTS binary not found at {self.piper_binary_path}")
            print("Installing Piper TTS...")
            import scripts.install_piper_tts
            scripts.install_piper_tts.setup_piper_tts()
        else:
            print("Piper TTS binary found.")  # Log para confirmar que o binário foi encontrado

    def generate_audio(self, text: str, file_name_no_ext=None):
        if file_name_no_ext:
            print(
                "Piper TTS does not support custom file names. Ignoring the provided file name."
            )

        try:
            # Verifica se o caminho do modelo e o binário estão corretos
            if not os.path.exists(self.voice_model_path):
                raise FileNotFoundError(f"Voice model not found at {self.voice_model_path}")
            if not os.path.exists(self.piper_binary_path):
                raise FileNotFoundError(f"Piper binary not found at {self.piper_binary_path}")

            print(f"Generating audio for text: {text[:50]}...")  # Log para texto a ser convertido (mostrando apenas os primeiros 50 caracteres)

            # Construct and execute the Piper TTS command
            command = [
                self.piper_binary_path,
                "-m", self.voice_model_path,
                "-d", self.new_audio_dir,
            ]

            print(f"Running command: {' '.join(command)}")  # Log do comando que será executado

            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Enviar texto para o processo e obter saída
            stdout, stderr = process.communicate(input=text)

            print("Command executed, processing output...")  # Log após execução do comando

            if process.returncode != 0:
                print(f"Error: Piper TTS process returned a non-zero exit code: {process.returncode}")
                if self.verbose:
                    print(f"Standard Error Output: {stderr}")
                return None

            output = stdout.strip()

            if self.verbose:
                print(f"Command stdout: {stdout}")
                print(f"Command stderr: {stderr}")

            if not output.endswith(".wav"):
                print(f"Unexpected output format: {output}")
                if self.verbose:
                    print(f"Full command output: {stdout}")
                return None

            print(f"Generated audio file: {output}")
            return output

        except subprocess.CalledProcessError as e:
            print(f"Subprocess error occurred: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
