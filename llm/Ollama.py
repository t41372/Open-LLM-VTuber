
# This file is responsible for the communicating with the Ollama Server
import json
import requests

class Ollama:
    '''
    This class is responsible for communicating with the Ollama Server.
    '''

    def __init__(self, base_url, model, system, verbose=False):
        self.base_url = base_url # base url of the ollama server
        self.verbose = verbose
        self.model = model # model name
        self.system = system # system prompt



    def generate(self, prompt: str, context=[]):
        '''
        Send the request to the ollama server and return the response.
        The response is streamed one token at a time onto the console.

        Parameters
        ----------
        prompt  :   str
            the prompt to send to the ollama server

        context :   list of number
            The context of the chat to send to the ollama server. 
            Basically the chat history in vector returned from Ollama server last time. 
            Size of the context is the token length of the chat history.
            Check [Ollama API](https://github.com/jmorganca/ollama/blob/main/docs/api.md) for more details.
            Also the article [Ollama context at generate API output](https://stephencowchau.medium.com/ollama-context-at-generate-api-output-what-are-those-numbers-b8cbff140d95)

        Returns
        -------
        A tuple of the following:
        complete_response : str
            the complete response from the ollama server
        context : list of vectors
            the context of the chat returned from the ollama server.
            Pass this to the next generate call to continue the chat with short-term memory.
        
        '''
        req = requests.post(self.base_url + '/api/generate',
                        json={
                            'model': self.model,
                            'system': self.system,
                            'prompt': prompt,
                            'context': context,
                        },
                        stream=True)
        req.raise_for_status()
        complete_response = ''

        for line in req.iter_lines():
            body = json.loads(line)
            if body.get('done', False):
                return complete_response, body['context']
            response_part = body.get('response', '')
            complete_response += response_part
            # the response streams one token at a time, print that as we receive it
            print(response_part, end='', flush=True)

            if 'error' in body:
                raise Exception(body['error'])




