
var model2;
var modelIndex = 0; // the index of the model to load
// the model will be loaded from modelDict.js
var modelInfo = modelDict[modelIndex];
var emoMap = modelInfo["emotionMap"];

// const cubism2Model =
//   "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json";
// const cubism4Model =
//   "https://cdn.jsdelivr.net/gh/Eikanya/Live2d-model/VenusScramble/playerunits/player_unit_00003/live2d/model.json";

const live2d = PIXI.live2d;

(async function main() {
  const app = new PIXI.Application({
    view: document.getElementById("canvas"),
    autoStart: true,
    resizeTo: window,
    backgroundColor: 0x000000,
    transparent: true
  });

  const models = await Promise.all([
    // live2d.Live2DModel.from(cubism2Model),
    // live2d.Live2DModel.from(cubism4Model)
    live2d.Live2DModel.from(modelInfo.url),
  ]);

  models.forEach((model) => {
    app.stage.addChild(model);

    const scaleX = (innerWidth * modelInfo.kScale);
    const scaleY = (innerHeight * modelInfo.kScale);

    // fit the window
    model.scale.set(Math.min(scaleX, scaleY));

    model.y = innerHeight * 0.01;

    draggable(model);
    // addFrame(model);
    // addHitAreaFrames(model);
  });

  model2 = models[0];

  model2.x = app.view.width / 2 - model2.width / 2;



  // handle tapping

  model2.on("hit", (hitAreas) => {
    if (hitAreas.includes("body")) {
      model2.motion("tap_body");
    }

    if (hitAreas.includes("head")) {
      model2.expression();
    }
  });

  
})();

/**
 * Makes a PIXI model draggable.
 * @param {PIXI.Container} model - The model to make draggable.
 */
function draggable(model) {
  model.buttonMode = true;
  model.on("pointerdown", (e) => {
    model.dragging = true;
    model._pointerX = e.data.global.x - model.x;
    model._pointerY = e.data.global.y - model.y;
  });
  model.on("pointermove", (e) => {
    if (model.dragging) {
      model.position.x = e.data.global.x - model._pointerX;
      model.position.y = e.data.global.y - model._pointerY;
    }
  });
  model.on("pointerupoutside", () => (model.dragging = false));
  model.on("pointerup", () => (model.dragging = false));
}







