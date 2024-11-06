import abc
import os
from playsound3 import playsound


class TTSInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def generate_audio(self, text: str, file_name_no_ext=None) -> str:
        """
        Generate speech audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext (optional and deprecated): str
            name of the file without file extension

        Returns:
        str: the path to the generated audio file

        """
        raise NotImplementedError

    def remove_file(self, filepath: str, verbose: bool = True) -> None:
        """
        Remove a file from the file system.

        This is a separate method instead of a part of the `play_audio_file_local()` because `play_audio_file_local()` is not the only way to play audio files. This method will be used to remove the audio file after it has been played.

        Parameters:
            filepath (str): The path to the file to remove.
            verbose (bool): If True, print messages to the console.
        """
        if not os.path.exists(filepath):
            print(f"File {filepath} does not exist")
            return
        try:
            print(f"Removing file {filepath}") if verbose else None
            os.remove(filepath)
        except Exception as e:
            print(f"Failed to remove file {filepath}: {e}")

    def play_audio_file_local(self, audio_file_path: str) -> None:
        """
        Play the audio file locally on this device (not stream to some kind of live2d front end).

        audio_file_path: str
            the path to the audio file
        """
        playsound(audio_file_path)
        

    def generate_cache_file_name(self, file_name_no_ext=None, file_extension="wav"):
        """
        Generate a cross-platform cache file name.

        file_name_no_ext: str
            name of the file without extension
        file_extension: str
            file extension

        Returns:
        str: the path to the generated cache file
        """
        cache_dir = "./cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if file_name_no_ext is None:
            file_name_no_ext = "temp"

        file_name = f"{file_name_no_ext}.{file_extension}"
        return os.path.join(cache_dir, file_name)
