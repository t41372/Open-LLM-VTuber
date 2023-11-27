
# This file is responsible for the communicating with the Ollama Server
import json
import requests

class Ollama:
    '''
    This class is responsible for communicating with the Ollama Server.
    The conversation memory is stored inside this class.
    '''


    def __init__(self, base_url, model, system, verbose=False):
        self.base_url = base_url # base url of the ollama server
        self.verbose = verbose
        self.model = model # model name
        self.system = system # system prompt
        self.context = [] # context of the conversation. (list of vectors)
        '''
        context :   list of number
            The context of the chat to send to the ollama server. 
            Basically the chat history in vector returned from Ollama server last time. 
            Size of the context is the token length of the chat history.
            Check [Ollama API](https://github.com/jmorganca/ollama/blob/main/docs/api.md) for more details.
            Also the article [Ollama context at generate API output](https://stephencowchau.medium.com/ollama-context-at-generate-api-output-what-are-those-numbers-b8cbff140d95)

        '''



    def generateWithMemory(self, prompt: str, currentContext=None):
        '''
        Send the request to the ollama server and return the response.
        The response is streamed one token at a time onto the console.
        The context of the conversation is stored in this class.
        Set the context to an empty list if you want a stateless conversation.

        Parameters
        ----------
        prompt  :   str
            the prompt to send to the ollama server

        currentContext :   list of number. Default: None
            The context of the chat to send to the ollama server. 
            Only pass this if you want to change the context of the conversation.
            By default, unless a value was passed in, this function will use the value stored in this class.
            Check [Ollama API](https://github.com/jmorganca/ollama/blob/main/docs/api.md) for more details.
            Also the article [Ollama context at generate API output](https://stephencowchau.medium.com/ollama-context-at-generate-api-output-what-are-those-numbers-b8cbff140d95)

        Returns
        -------
        complete_response : str
            the complete response from the ollama server        
        '''
        req = requests.post(self.base_url + '/api/generate',
                        json={
                            'model': self.model,
                            'system': self.system,
                            'prompt': prompt,
                            'context': currentContext if currentContext is not None else self.context,
                        },
                        stream=True)
        req.raise_for_status()
        complete_response = ''

        for line in req.iter_lines():
            body = json.loads(line)
            if body.get('done', False):
                # print(" THE CONTEXT IS: {}".format(body["context"]))
                self.context = body.get("context", [])
                return complete_response
            response_part = body.get('response', '')
            complete_response += response_part
            # the response streams one token at a time, print that as we receive it
            print(response_part, end='', flush=True)

            if 'error' in body:
                raise Exception(body['error'])




