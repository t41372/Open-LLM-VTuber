from typing import Iterator
import json
import requests
from rich.console import Console
from .agents.agent_interface import AgentInterface

console = Console()


class LLM(AgentInterface):

    def __init__(
        self,
        base_url: str,
        server_admin_token: str,
        agent_id: str,
        verbose: str = False,
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

    def chat_iter(self, prompt) -> Iterator[str]:
        full_response = self._send_message_to_agent(prompt, callback_function=print)
        # memGPT will handle the memory, so no need to deal with it here
        return full_response

    def handle_interrupt(self, heard_response: str) -> None:
        print(
            "\n>> (MemGPT doesn't know you interrupted it for now. I don't know how to tell it about the interruption.) \n"
        )

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
            url, headers=self.headers, data=json.dumps(data), stream=True, timeout=30
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
