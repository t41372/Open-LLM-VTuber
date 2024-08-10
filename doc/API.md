API

`/client-ws`



~~~mermaid

sequenceDiagram
    participant l2d as 瀏覽器
    participant server as Server
    participant py as Python後端

    
    l2d ->> server: 瀏覽器啟動, ws 建立 (/client-ws, init)
    server ->> py: 如果沒有後端, 啟動後端
    activate py
    %% Note right of py: conversation loop
    py ->> l2d: 傳遞模型信息

    
    Note left of l2d: conversation loop, 等待用戶輸入
    Note left of l2d: 用戶輸入
    activate l2d
    l2d ->> server: ws, user_input
    activate server
    server --> py: 繼續conversation_chain, LLM -> speak
    Note left of py: 如果
    Note left of server: stream_audio可以放到server來做 
    Note right of server: 理想狀況下server提供一個ws.send對象, 傳入audio_play來串流
    
    server ->> l2d: ws, res_seg

    Note left of l2d: 用戶打斷, 播放終止
    
    l2d ->> server: ws, interrupt
    deactivate l2d
    activate l2d
    Note right of server: 打斷, break出迴圈, 收集已有的信息當作history
    l2d ->> server: ws, user_input... 下一個cycle




    deactivate py
    %% l2d->>+server: Hello server, how are you?
    %% l2d->>+server: server, can you hear me?
    %% server-->>-l2d: Hi l2d, I can hear you!
    %% server-->>-l2d: I feel great!
    %% 如果不用GUI, 就只開server 就行, live2D on/off 應該被deprecated, 不過server.py 還會用到這個選項

~~~







## Client to Server

### text input

~~~json
{
	"type": "text_input",
	"text": "some text"
}
~~~

- text input from the user to the LLM



### audio input

~~~json
...
~~~

- text input from the user to the LLM





## Server to Client





### Set Model

~~~json
{
	"type": "set-model",
	"text": {}
}
~~~

- `text`: The configuration JSON of the Live2D model from `model-dict.json`.



### Audio

~~~json
{
  "type": "audio",
  "audio": "data...base64 audio",
  "volumes": ["array of volumes"],
  "slice_length": 20,
  "text": "text to display",
  "expressions": [1, 2, 1, 3, 4],
}
~~~

- `audio` is the audio to be played in base64 format.
- `volume` is a list of audio volume information. Each element in the list represents the average volume of `slice_length` time. It is used to control the mouth movement (lip sync).
- The `slice_length` is the duration of each element in the `volume`, measured in milliseconds (ms). Since `volume` represents the average audio volume over a certain period, such as 20ms, `slice_length` indicates the length of this short time segment, which is 20ms.
- `text` is the text to be displayed as a subtitle.
- `expressions` is a list of expression index (numbers) to control the facial expression.





### Send Full text to be displayed as a subtitle

~~~json
{
	"type": "full-text",
	"text": "some message"
}
~~~

- `text` will be displayed as the subtitle on the screen



### Set Expression

~~~json
{
	"type": "expression",
	"text": ""
}
~~~

- `text`: the expression index of the facial expression you want it to do.



### Control Signals

~~~json
{
	"type": "control",
	"text": ""
}
~~~

Type: `control`

- Type `start-mic`
  - Start microphone indefinitely
  - 
- Type `speaking-start`: 
  - Start speaking (start moving mouth like an idiot)
- Type `speaking-stop`:
  - Stop speaking (stop moving mouth like an idiot)
