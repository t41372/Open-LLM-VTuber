API

`/client-ws`





### Audio

~~~json
{
  type: "audio",
  audio: "data...base64 audio",
  volumes: array of volumes,
  slice_length: 20,
  text: "text to display",
  expressions: [1, 2, 1, 3, 4],
}
~~~

- `audio` is the audio to be played in base64 format.
- `volume` is a list of audio volume information. Each element in the list represents the average volume of `slice_length` time. It is used to control the mouth movement (lip sync).
- The `slice_length` is the duration of each element in the `volume`, measured in milliseconds (ms). Since `volume` represents the average audio volume over a certain period, such as 20ms, `slice_length` indicates the length of this short time segment, which is 20ms.
- `text` is the text to be displayed as a subtitle.
- `expressions` is a list of expression index (numbers) to control the facial expression.



### Set Model

~~~json
{
	type: "set-model",
	text: {}
}
~~~

- `text`: The configuration JSON of the Live2D model from `model-dict.json`.



### Send Full text to be displayed as a subtitle

~~~json
{
	type: "full-text",
	text: "some message"
}
~~~

- `text` will be displayed as the subtitle on the screen



### Set Expression

~~~json
{
	type: "expression",
	text: ""
}
~~~

- `text`: the expression index of the facial expression you want it to do.



### Control Signals

~~~json
{
	type: "control",
	text: ""
}
~~~

Type: `control`

- message `speaking-start`: 
  - Start speaking (start moving mouth like an idiot)
- message `speaking-stop`:
  - Stop speaking (stop moving mouth like an idiot)
