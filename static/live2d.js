var app, model2;
var modelInfo, emoMap;
var pointerInteractionEnabled = true;

const live2dModule = (function () {
  const live2d = PIXI.live2d;

  async function init() {
    app = new PIXI.Application({
      view: document.getElementById("canvas"),
      autoStart: true,
      resizeTo: window,
      transparent: true,
      backgroundAlpha: 0,
    });
  }

  async function loadModel(modelInfo) {
    emoMap = modelInfo["emotionMap"];

    if (model2) {
      app.stage.removeChild(model2); // Remove old model
    }

    const models = await Promise.all([
      live2d.Live2DModel.from(modelInfo.url, {
        autoInteract: window.pointerInteractionEnabled
      }),
    ]);

    models.forEach((model) => {
      app.stage.addChild(model);

      const scaleX = (innerWidth * modelInfo.kScale);
      const scaleY = (innerHeight * modelInfo.kScale);

      model.scale.set(Math.min(scaleX, scaleY));
      model.y = innerHeight * 0.01;
      draggable(model);
    });

    model2 = models[0];

    if (!modelInfo.initialXshift) modelInfo.initialXshift = 0;
    if (!modelInfo.initialYshift) modelInfo.initialYshift = 0;

    model2.x = app.view.width / 2 - model2.width / 2 + modelInfo["initialXshift"];
    model2.y = app.view.height / 2 - model2.height / 2 + modelInfo["initialYshift"];

    // model2.on("hit", (hitAreas) => {
    //   if (hitAreas.includes("body")) {
    //     model2.motion("tap_body");
    //   }

    //   if (hitAreas.includes("head")) {
    //     model2.expression();
    //   }
    // });
  }

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

  function changeBackgroundImage(imageUrl) {
    document.body.style.backgroundImage = `url('${imageUrl}')`;
  }

  return {
    init,
    loadModel,
    changeBackgroundImage
  };
})();

document.addEventListener('DOMContentLoaded', function () {
  const pointerInteractionBtn = document.getElementById('pointerInteractionBtn');

  pointerInteractionBtn.addEventListener('click', function () {
    window.pointerInteractionEnabled = !window.pointerInteractionEnabled;
    pointerInteractionBtn.textContent = window.pointerInteractionEnabled ? "👀 Pointer Interactive On" : "❌ Pointer Interactive Off";
    model2.interactive = window.pointerInteractionEnabled;
    if (!window.pointerInteractionEnabled) {
      // attempt to reset the pointer interaction
      model2.internalModel.focusController.targetX = 0;
      model2.internalModel.focusController.targetY = 0;
    }
  });
});
