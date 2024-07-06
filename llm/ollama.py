# Description: This file contains the implementation of the `ollama` class.
# This class is responsible for handling the interaction with the OpenAI API for language generation.
# And it is compatible with all of the OpenAI Compatible endpoints, including Ollama, OpenAI, and more.

from openai import OpenAI
import concurrent.futures

from .llm_interface import LLMInterface

class LLM(LLMInterface):

    def __init__(self, base_url, model, system, callback=print, organization_id="z", project_id="z", llm_api_key="z", verbose=False):
        """
        Initializes an instance of the `ollama` class.

        Parameters:
        - base_url (str): The base URL for the OpenAI API.
        - model (str): The model to be used for language generation.
        - system (str): The system to be used for language generation.
        - callback (function, optional): The callback function to be called after each API call. Defaults to `print`.
        - organization_id (str, optional): The organization ID for the OpenAI API. Defaults to an empty string.
        - project_id (str, optional): The project ID for the OpenAI API. Defaults to an empty string.
        - llm_api_key (str, optional): The API key for the OpenAI API. Defaults to an empty string.
        - verbose (bool, optional): Whether to enable verbose mode. Defaults to `False`.
        """

        self.base_url = base_url
        self.model = model
        self.system = system
        self.callback = callback
        self.memory = []
        self.verbose = verbose
        self.client = OpenAI(
            base_url=base_url,
            organization=organization_id,
            project=project_id,
            api_key=llm_api_key,
        )

        self.__set_system(system)

        if self.verbose:
            self.__printDebugInfo()

    
    def __set_system(self, system):
        '''
        Set the system prompt
        system: str
            the system prompt
        '''
        self.system = system
        self.memory.append(
            {
                "role": "system",
                "content": system,
            }
        )

    def __printMemory(self):
        '''
        Print the memory
        '''
        print("Memory:\n========\n")
        # for message in self.memory:
        print(self.memory)
        print("\n========\n")

    def __printDebugInfo(self):
        print(" -- Base URL: " + self.base_url)
        print(" -- Model: " + self.model)
        print(" -- System: " + self.system)
    
    def __is_complete_sentence(self, text):
        """
        Check if the text is a complete sentence.
        text: str
            the text to check
        """

        white_list = ["...", "Dr.", "Mr.", "Ms.", "Mrs.", "Jr.", "Sr.", "St.", "Ave.", "Rd.", "Blvd.", "Dept.", "Univ.", "Prof.", "Ph.D.", "M.D.", "U.S.", "U.K.", "U.N.", "E.U.", "U.S.A.", "U.K.", "U.S.S.R.", "U.A.E."]

        for item in white_list:
            if text.strip().endswith(item):
                return False

        punctuation_blacklist = [".", "?", "!", "。", "；", "？", "！", "…", "〰", "〜", "～", "！", ]
        return any(text.strip().endswith(punct) for punct in punctuation_blacklist)
    
    def chat(self, prompt):

        self.memory.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        if self.verbose:
            self.__printMemory()
            print(" -- Base URL: " + self.base_url)
            print(" -- Model: " + self.model)
            print(" -- System: " + self.system)
            print(" -- Prompt: " + prompt + "\n\n")

        chat_completion = []
        try:
            chat_completion = self.client.chat.completions.create(
                messages=self.memory,
                model=self.model,
                stream=True,
            )
        except Exception as e:
            print("Error calling the chat endpoint: " + str(e))
            self.__printDebugInfo()
            return "Error calling the chat endpoint: " + str(e)

        full_response = ""
        for chunk in chat_completion:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content or "", end="")
                full_response += chunk.choices[0].delta.content

        print("\n ===== LLM response received ===== \n")

        self.callback(full_response)

        self.memory.append(
            {
                "role": "assistant",
                "content": full_response,
            }
        )

        return full_response
    
    
    
    def chat_stream_audio(self, prompt, generate_audio_file=None, stream_audio_file=None):
        """
        Call the llm with text, print the result, and stream the audio to the frontend if the generate_audio_file and stream_audio_file functions are provided.
        prompt: str
            the text to send to the llm
        generate_audio_file: function
            the function to generate audio file from text. The function should take the text as input and return the path to the generated audio file. Defaults to None.
        stream_audio_file: function
            the function to stream the audio file to the frontend. The function should take the path to the audio file as input. Defaults to None.

        Returns:
        str: the full response from the llm
        """

        self.memory.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        if self.verbose:
            self.__printMemory()
            print(" -- Base URL: " + self.base_url)
            print(" -- Model: " + self.model)
            print(" -- System: " + self.system)
            print(" -- Prompt: " + prompt + "\n\n")

        chat_completion = []
        try:
            chat_completion = self.client.chat.completions.create(
                messages=self.memory,
                model=self.model,
                stream=True,
            )
        except Exception as e:
            print("Error calling the chat endpoint: " + str(e))
            self.__printDebugInfo()
            return "Error calling the chat endpoint: " + str(e)

        
        
        index = 0
        sentence_buffer = ""
        full_response = ""
        

        # Initialize ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            last_stream_future = None
            for chunk in chat_completion:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content or "", end="")
                    sentence_buffer += chunk.choices[0].delta.content
                    full_response += chunk.choices[0].delta.content
                    if self.__is_complete_sentence(sentence_buffer):
                        if callable(generate_audio_file):
                            print("\n")
                            file_path = generate_audio_file(sentence_buffer, file_name_no_ext=f"temp-{index}")
                            
                            # wait for the audio to finish playing
                            if last_stream_future:
                                last_stream_future.result()
                            # stream the audio file to the frontend
                            last_stream_future = executor.submit(stream_audio_file, sentence_buffer, filename=file_path)
                            index += 1
                        sentence_buffer = ""
            if sentence_buffer: # if there is any remaining text, generate and stream the audio
                if callable(generate_audio_file):
                    print("\n")
                    file_path = generate_audio_file(sentence_buffer, file_name_no_ext=f"temp-{index}")
                    # wait for the audio to finish playing
                    if last_stream_future:
                        last_stream_future.result()
                    # stream the audio file to the frontend
                    last_stream_future = executor.submit(stream_audio_file, sentence_buffer, filename=file_path)
                    index += 1
            # wait for the last audio to finish playing
            if last_stream_future:
                last_stream_future.result()

        print("\n ===== LLM response received ===== \n")

        self.callback(full_response)

        self.memory.append(
            {
                "role": "assistant",
                "content": full_response,
            }
        )

        return full_response
    

if __name__ == "__main__":
    llm = LLM(
        base_url="http://localhost:11434/v1",
        model="llama3:latest",
        callback=print,
        system="You are a sarcastic AI chatbot who loves to the jokes \"Get out and touch some grass\"",
        organization_id="organization_id",
        project_id="project_id",
        llm_api_key="llm_api_key",
        verbose=True,
    )
    while True:
        print("\n>> (Press Ctrl+C to exit.)")
        llm.chat_stream_audio(input(">> "))
        