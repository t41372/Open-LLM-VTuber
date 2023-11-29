
# This file is responsible for the communicating with the Ollama Server
from datetime import datetime
import json
import requests
from vectordb import VectorDB

class Ollama:
    '''
    This class is responsible for communicating with the Ollama Server.
    The conversation memory is stored inside this class.
    '''


    def __init__(self, base_url: str, model: str, system: str, vector_db_path="", verbose=True):
        '''
        Initialize the Ollama class.
        Parameters
        ----------
        base_url    :   str
            the base url of the ollama server
        model       :   str
            the model name
        system      :   str 
            the system prompt.
        vector_db_path  :   str
            the path to the vector database. default to "".
        verbose     :   bool
            whether to print the debug information. default to False. I'm sorry but its currently useless.🥲
        '''
        self.base_url = base_url # base url of the ollama server
        self.verbose = verbose
        self.model = model # model name
        self.system = system # system prompt
        if vector_db_path != "":
            self.vector_db = VectorDB(vector_db_path) # vector database to search for relavant information for long term memory
        
        self.context = [] # context of the conversation. (list of vectors)
        '''
        context :   list of number
        The context of the chat to send to the ollama server. 
        Basically the chat history in vector returned from Ollama server last time. 
        Size of the context is the token length of the chat history.
        Check [Ollama API](https://github.com/jmorganca/ollama/blob/main/docs/api.md) for more details.
        Also the article [Ollama context at generate API output](https://stephencowchau.medium.com/ollama-context-at-generate-api-output-what-are-those-numbers-b8cbff140d95)
        '''
        
    def generateWithLongTermMemory(self, prompt: str, currentContext=None, vector_db=None, system=None, LLMAssist=False):
        '''
        Generate response with both short term memory (currentContext) and long term memory (vector_db).
        Search the vector database for relavant information, plug it into the prompt, and 
        call generateWithMemory() with the context from the long term memory.
        Parameters
        ----------
        prompt  :   str
            the prompt to send to the ollama server
        currentContext :   list of number. Default: None
            Check the docs of generateWithMemory() for more details.
        vector_db   :   VectorDB,     default: None
            the vector database to search for relavant information. Stored in this class if not provided.
        system  :   str. Default: None
            the system prompt. 
            By default, unless a value was passed in, this function will use the value stored in this class.
        Returns
        -------
        complete_response : str
            the complete response from the ollama server        
        '''
        relevantInfo = self.getRelevantInfoFromVectorDB(prompt, vector_db, LLMAssist)
        relevantInfo = "\nYour memory reminds you: \n{" + relevantInfo + "}\n"
        if self.verbose: 
            print(relevantInfo)
        
        if system is None:
            system = self.system
        
        return self.generateWithMemory(prompt, currentContext, system + relevantInfo)
    
    def getRelevantInfoFromVectorDB(self, prompt: str, vector_db: VectorDB, LLMassist=False):
        '''
        Search the vector database for relavant information and have the llm review, summerize, and return it.
        
        Parameters
        ----------
        prompt  :   str
            user's prompt
        vector_db   :   VectorDB or None
            the vector database to search for relavant information. The function will use the one stored in this class if not provided.
        Returns
        -------
        summerized_prompt : str
            the summerized prompt from the llm
        '''
        if type(vector_db) is not VectorDB:
            if self.vector_db is None:
                raise Exception("No vector database provided.")
            vector_db = self.vector_db

        # Search the vector database for relavant information
        relavantMessages = ""
        if vector_db is not None:
            if self.verbose:
                print("\n >>> Some Unknown Voice inside LLM's Head <<<\n")
            
            results = vector_db.queryMessage(prompt)
            documents = results["documents"]
            metadatas = results["metadatas"]

            # Plug the query result into the prompt
            for document, metadata in zip(documents, metadatas):
                relavantMessages += metadata["Speaker"] + " ({}) ".format(metadata["Date"]) + "said: " + document + "\n"

        relevantInfo = "\nRelevant Information from your memory: \n{" + relavantMessages + "}\n"
        if self.verbose: print(relevantInfo)

        if not LLMassist:
            return relevantInfo

        # Have the llm review, summerize, and return it.
        system_prompt = "Serve as a digital reminder with no personality delivering pertinent information based on the provided data. Communicate in the third person, summarizing only relevant details for answering questions. Omit non-relevant information, and in the absence of pertinent details, refrain from responding. Current Time: {{{}}}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        prompt = "Remind me of the relevant information to assist in answering the user's question. Make sure that I can consider the provided context while formulating my response. If none of the provided information is related to the question or if you think you don't have enough information, add the phrase [don't know] at the beginning of your response, and just say you don't know, be short. Don't ask for more information, just say you don't know. The user's question is: {{{}}}. The relevant information is provided here:\n {{{}}}\n.".format(relevantInfo, prompt)
        summerized_prompt = self.generateWithMemory(prompt=prompt, currentContext=[], system=system_prompt, displayStreamText=False)

        if summerized_prompt.startswith("[Don't know]") or summerized_prompt.startswith("Don't know"):
            if self.verbose:
                print(summerized_prompt)
                print(">> LLM doesn't know the answer. Returning empty string.")
            summerized_prompt = ""

        if self.verbose:
            print(summerized_prompt)

        return summerized_prompt



    def generateWithMemory(self, prompt: str, currentContext=None, system=None, displayStreamText=True):
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

        system  :   str. Default: None
            the system prompt. 
            By default, unless a value was passed in, this function will use the value stored in this class.
        
        displayStreamText   :   bool. Default: True
            whether to print the response from the ollama server as it streams in.
            Set this to False if you want to supress the output.
            The response is streamed one token at a time onto the console.

        Returns
        -------
        complete_response : str
            the complete response from the ollama server        
        '''
        req = requests.post(self.base_url + '/api/generate',
                        json={
                            'model': self.model,
                            'system': system if system is not None else self.system,
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
            if displayStreamText:
                print(response_part, end='', flush=True)

            if 'error' in body:
                raise Exception(body['error'])




