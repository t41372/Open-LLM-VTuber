import time
import json
import requests
import TaskQueue


ModelDictPath = "model_dict.json"



class Live2dController:

    def __init__(self, live2d_model_name: str, base_url: str = "http://127.0.0.1:8000"):

        self.base_url = base_url
        self.live2d_model_name = live2d_model_name

        self.model_info = self.setModel(live2d_model_name)

        self.emoMap = self.model_info["emotionMap"]

        self.task_queue = TaskQueue.TaskQueue()



    def getEmoMapKeyAsString(self):
        '''
        Returns a string of the keys in the emoMap dictionary.
        
        Parameters:
            None
            
            Returns:
            str: A string of the keys in the emoMap dictionary. The keys are enclosed in square brackets.
                example: `"[fear], [anger], [disgust], [sadness], [joy], [neutral], [surprise]"`
            
            Raises:
            None
        '''
        return " ".join([f"[{key}]," for key in self.emoMap.keys()])



    def setModel(self, model_name: str):
        '''
        Sets the live2d model name and returns the matched model dictionary.

        Parameters:
            model_name (str): The name of the live2d model.

        Returns:
            dict: The matched model dictionary.

        Raises:
            None

        '''
        self.live2d_model_name = model_name

        with open(ModelDictPath, 'r') as file:
            model_dict = json.load(file)

        # Find the model in the model_dict
        matched_model = next((model for model in model_dict if model["name"] == model_name), None)

        if matched_model is None:
            print(f"No model found for {model_name}. Exiting.")
            exit()

        self.send_message_to_broadcast({"type": "set-model", "text": matched_model})
        return matched_model


    def setExpression(self, expression: str):
        """
        Sets the expression of the Live2D model.

        This method sends a message to the broadcast route with the expression to be set immediately.
        The expression is mapped to the corresponding text in the `emoMap` dictionary.

        Parameters:
        - expression (str): The expression to be set.

        Prints:
        - The expression being set to the console.
        """

        print(f">>>>>> setExpression ({self.emoMap[expression]}): {expression}")
        self.send_message_to_broadcast({"type": "expression", "text": self.emoMap[expression]})

    def startSpeaking(self):
        """
        Sends a signal to the live2D front-end: start speaking.

        Parameters:
            None

        Returns:
            None
        """
        self.send_message_to_broadcast({"type": "control", "text": "speaking-start"})

    def stopSpeaking(self):
        """
        Sends a signal to the live2D front-end: stop speaking.

        Parameters:
            None

        Returns:
            None
        """
        self.send_message_to_broadcast({"type": "control", "text": "speaking-stop"})

    def send_text(self, text):
        """
        Sends a text message to the live2D front-end.

        Parameters:
            text (str): The text message to send.

        Returns:
            None
        """
        self.send_message_to_broadcast({"type": "full-text", "text": text})


    def check_string_for_expression(self, str):
        """
        Checks if the given string contains any expressions defined in the emoMap dictionary,
        and send the corresponding expressions one-by-one every 3 sec to the Live2D model.
        
        Parameters:
            str (str): The string to check for expressions.
            
        Returns:
            None
            
        Raises:
            None
        """
        for key, value in self.emoMap.items():
            if f"[{key}]" in str.lower():
                # print(f">> [ ] <- add to exec queue: {key}, {value}")
                def new_task(num):
                    self.setExpression(num)
                    time.sleep(3)
                self.task_queue.add_task(new_task(key))



    def send_message_to_broadcast(self, message):
        """
        Sends a message to the broadcast route.

        This method constructs a URL by appending "/broadcast" to the base URL stored in `self.base_url`.
        It then serializes the `message` parameter into a JSON string using `json.dumps` and sends this
        payload as a JSON object within a POST request to the constructed URL. The response from the
        server is checked for success (response.ok), and a message is printed to the console indicating
        the status of the operation.

        Parameters:
        - message (dict): A dictionary containing the message to be sent. This dictionary is serialized
                        into a JSON string before being sent.

        Prints:
        - The status code of the response to the console.
        - A success message if the message was successfully sent to the broadcast route.
        """
        url = self.base_url + "/broadcast"
        
        payload = json.dumps(message)

        response = requests.post(url, json={"message": payload})
        # print(f"Response Status Code: {response.status_code}")
        # if response.ok:
        #     print("Message successfully sent to the broadcast route.")
        # else:
        #     print("Failed to send message to the broadcast route.")




if __name__ == "__main__":
    
    live2d = Live2dController("shizuku")

    print(live2d.getEmoMapKeyAsString())


    # live2d.startSpeaking()
    # live2d.check_string_for_expression("Welrkvs rsv, [fear] [anger], [disgust],[sadness], , [joy], [neutral]  [surprise],")

    input()


