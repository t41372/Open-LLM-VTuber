
> :warning:
> Some live2d model (quite a lot it turns out) downloaded from the internet don't work well with this project. Problems include but not limited to:
> - Mouth don't open
> - Can't show facial expression correctly
> - Model keep doing some action iteratively


## Load your own Live2D models
Steps to load your own live2D model:
1. Find some live2d models
2. Add the configuration in `model_dict.json`
3. Load the model

### Find some live2d models
- You can find some live2d models here `https://guansss.github.io/live2d-viewer-web/`
- Some (many, it turns out) live2d models don't work well with the project. Most notibly, their mouth won't move. I don't know why. The error message says that the `model2.internalModel.coreModel.setParamFloat` is not a function. Not sure if it is because these models are made for Cubism 5, and our live2d driver `guansss/pixi-live2d-display` only supports Cubism 4 (and lower).

### Add live2d model configuration

Add the configuration of the model into `model_dict.json`.

`model_dict.json` is a list of configs for live2d models.

A configuration may look like this:

~~~json
{
    "name": "shizuku-local",
    "description": "Orange-Haired Girl, locally available. no internet required.",
    "url": "/live2d-models/shizuku/shizuku.model.json",
    "kScale": 0.000625,
    "kXOffset": 1150,
    "idleMotionGroupName": "Idle",
    "emotionMap": {
        "neutral": 0,
        "anger": 2,
        "disgust": 2,
        "fear": 1,
        "joy": 3,
        "smirk": 3,
        "sadness": 1,
        "surprise": 3
    }
},
~~~

Something you want to change
- `name`: Name of the model
- `description`: Description for this model. Just write anything.
- `url`: Link to the model json file like `shizuku.model.json`.
  - If the model files are hosted somewhere, you can just paste the url. The url should starts with `http://` or `https://`.
  - If the model you are trying to load is on your computer, put the model folder into the `live2d-models` directory and enter the relative path for the `url`. Like this `/live2d-models/UG/ugofficial.model3.json`. Keep the `/live2d-models` intact and don't change it nor add dots before it like `./live2d-models`.
- `KScale`: How big the model should be. Make it smaller if the model is too big. Vice versa.
- `emotionMap`: a dictionary of facial expressions available.
  - The key (text left to the semicolon) is the name of the emotion. You can put any words into it, and the LLM will use these keywords to control the expression of the live2d model.
  - The value (text right to the semicolon) is the emotion index. This is the index that specify the emotion of the live2d model. After loading the model in the server, you can try running the function `setExpression(index)` in the console of the browser. Put some numbers into the function, see what the live2d model would do, and edit the emotion map according to the behavior and the index.



### Load the model
Load the model by changing the `LIVE2D_MODEL` config to the name of your new model. Remember to restart the `server.py` and refresh the website.





