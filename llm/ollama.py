# Description: This file contains the implementation of the `ollama` class.
# This class is responsible for handling the interaction with the OpenAI API for language generation.
# And it is compatible with all of the OpenAI Compatible endpoints, including Ollama, OpenAI, and more.


from openai import OpenAI
# import rich as print

class LLM:

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

        self.setSystem(system)
            
    def setSystem(self, system):
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
    
    def chat(self, prompt):
        """
        Call the llm with text and print the result.
        text: str
            the text that is recognized
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

        

        response = ""
        for chunk in chat_completion:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content or "", end="")
                response += chunk.choices[0].delta.content

        print("\n ===== LLM response received ===== \n")

        self.callback(response)

        self.memory.append(
            {
                "role": "assistant",
                "content": response,
            }
        )

        return response
    

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
        llm.chat(input(">> "))
        