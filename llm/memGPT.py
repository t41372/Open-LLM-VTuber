import os
import requests
import json
import concurrent.futures
import pysbd
from rich.console import Console

console = Console()


import yaml

# load configurations
def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, "memgpt_config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


config = load_config()


def get_config(key, default=None):
    return config.get(key, default)


class LLM:

    def __init__(
        self,
        base_url=get_config("BASE_URL"),
        server_admin_token=get_config("ADMIN_TOKEN"),
        agent_id=get_config("AGENT_ID"),
        verbose=get_config("VERBOSE", False),
    ) -> None:

        self.base_url = base_url
        self.token = server_admin_token
        self.agent_id = agent_id

        if not self.base_url:
            raise ValueError("BASE_URL is required in the configuration file.")
        if not self.token:
            raise ValueError("ADMIN_TOKEN is required in the configuration file.")

        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {self.token}",
        }
        self.verbose = verbose



    def chat_stream_audio(
        self, prompt, generate_audio_file=None, stream_audio_file=None
    ):
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
        
        full_response = self._send_message_to_agent(prompt, callback_function=None)

        sentences = self.__split_into_sentences(full_response)


        index = 0

        # Initialize ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            last_stream_future = None
            for sentence in sentences:
                print(f">> {sentence}")
                
                if callable(generate_audio_file):
                    print("\n")
                    file_path = generate_audio_file(sentence, file_name_no_ext=f"temp-{index}")
                    
                    # wait for the audio to finish playing
                    if last_stream_future:
                        last_stream_future.result()
                    # stream the audio file to the frontend
                    last_stream_future = executor.submit(stream_audio_file, sentence, filename=file_path)
                    index += 1
                
            # wait for the last audio to finish playing
            if last_stream_future:
                last_stream_future.result()

        print("\n ===== LLM response received ===== \n")

        return full_response






    def __split_into_sentences(self, text):
        """
        Splits the text into a list of sentences using the pysbd library.

        Parameters:
        - text (str): The text to split into sentences.

        Returns:
        - list: A list of sentences.
        """

        return pysbd.Segmenter(language="en", clean=False).segment(text)


    def _send_message_to_agent(self, message, callback_function=print):
        """
        Sends a message to the specified agent, invokes the callback with the assistant's full message if given, and return the assistant's full response. The response will NOT be streamed back word by word.

        Utilizes Server-Sent Events (SSE) for streaming assistant_messages back to the client. If verbose mode is enabled, messages of other types will be printed out. The callback is exclusively for assistant messages.

        This function uses REST API endpoint to avoid installing the memGPT python package, because it currently has a dependency conflict with fastapi.

        Parameters:
        - message (str): The message to send to the agent.
        - callback_function (function): The function to call with the assistant's message. Defaults to print.

        Returns:
        - str: The assistant's full response.
        """

        url = f"{self.base_url}/api/agents/{self.agent_id}/messages"

        data = {
            "agent_id": self.agent_id,
            "message": message,
            "stream": True,
            "role": "user",
        }
        response = requests.post(
            url, headers=self.headers, data=json.dumps(data), stream=True
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to send message: {response.text}")

        result = ""

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8").strip()
                if decoded_line.startswith("data:"):
                    decoded_line = decoded_line[len("data:") :].strip()
                if decoded_line:
                    try:
                        json_line = json.loads(decoded_line)
                        if self.verbose:
                            console.print(json_line)
                        if "assistant_message" in json_line:
                            result += json_line["assistant_message"]
                            if callable(callback_function):
                                callback_function(json_line["assistant_message"])

                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e} for line: {decoded_line}")
                else:
                    print("Received an empty line or non-JSON data.")

        return result




if __name__ == "__main__":



    llm = LLM(
        verbose=True,
    )

    print(llm.__split_into_sentences("Hello, Mr. Smith. How are you? I am fine. Thank you."))
    print(llm.__split_into_sentences("Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer. He also worked at craigslist.org as a business analyst... but he is now retired and living in the U.K.!"))
    # while True:
        # llm.send_message_to_agent(message=input(">> "))
        # print(llm.split_sentences(input(">> ")))
