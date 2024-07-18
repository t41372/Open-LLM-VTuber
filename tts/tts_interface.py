import abc
import os

class TTSInterface(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def speak_local(self, text, on_speak_start_callback=None, on_speak_end_callback=None):
        '''
        Speak the text locally on this device (not stream to some kind of live2d front end).

        text: str
            the text to speak
        on_speak_start_callback: function
            the callback function to call when synthesis starts
        on_speak_end_callback: function
            the callback function to call when synthesis ends
        '''
        pass

    @abc.abstractmethod
    def generate_audio(self, text, file_name_no_ext=None):
        '''
        Generate speech audio file using TTS.
        text: str
            the text to speak
        file_name_no_ext (optional and deprecated): str
            name of the file without extension

        
        Returns:
        str: the path to the generated audio file
        
        '''
        pass
    
    @staticmethod
    def remove_file(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Failed to remove file {filepath}: {e}")
