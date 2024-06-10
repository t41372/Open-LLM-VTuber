
var model2;


const cubism2Model =
  "https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/shizuku/shizuku.model.json";
const cubism4Model =
  "https://cdn.jsdelivr.net/gh/Eikanya/Live2d-model/VenusScramble/playerunits/player_unit_00003/live2d/model.json";

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
    live2d.Live2DModel.from(cubism2Model),
    live2d.Live2DModel.from(cubism4Model)
  ]);

  models.forEach((model) => {
    app.stage.addChild(model);

    const scaleX = (innerWidth * 0.4) / model.width;
    const scaleY = (innerHeight * 0.8) / model.height;

    // fit the window
    model.scale.set(Math.min(scaleX, scaleY));

    model.y = innerHeight * 0.1;

    draggable(model);
    // addFrame(model);
    // addHitAreaFrames(model);
  });

  model2 = models[0];
  const model4 = models[1];

  model2.x = (innerWidth - model2.width - model4.width) / 2;
  model4.x = model2.x + model2.width;



  // handle tapping

  model2.on("hit", (hitAreas) => {
    if (hitAreas.includes("body")) {
      model2.motion("tap_body");
    }

    if (hitAreas.includes("head")) {
      model2.expression();
    }
  });

  model4.on("hit", (hitAreas) => {
    if (hitAreas.includes("Body")) {
      model4.motion("Tap");
    }

    if (hitAreas.includes("Head")) {
      model4.expression();
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

// function addFrame(model) {
//   const foreground = PIXI.Sprite.from(PIXI.Texture.WHITE);
//   foreground.width = model.internalModel.width;
//   foreground.height = model.internalModel.height;
//   foreground.alpha = 0.2;

//   model.addChild(foreground);

//   checkbox("Model Frames", (checked) => (foreground.visible = checked));
// }

// function addHitAreaFrames(model) {
//   const hitAreaFrames = new live2d.HitAreaFrames();

//   model.addChild(hitAreaFrames);

//   checkbox("Hit Area Frames", (checked) => (hitAreaFrames.visible = checked));
// }

