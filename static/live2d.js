// index.js
var app, model2;
var modelInfo, emoMap;

const live2dModule = (function() {
  const live2d = PIXI.live2d;

  async function init() {
    app = new PIXI.Application({
      view: document.getElementById("canvas"),
      autoStart: true,
      resizeTo: window,
      backgroundColor: 0x000000,
      transparent: true
    });
  }

  async function loadModel(modelInfo) {
    emoMap = modelInfo["emotionMap"];

    if (model2) {
      app.stage.removeChild(model2); // Remove old model
    }

    const models = await Promise.all([
      live2d.Live2DModel.from(modelInfo.url),
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
    model2.x = app.view.width / 2 - model2.width / 2;

    model2.on("hit", (hitAreas) => {
      if (hitAreas.includes("body")) {
        model2.motion("tap_body");
      }

      if (hitAreas.includes("head")) {
        model2.expression();
      }
    });
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

  return {
    init,
    loadModel
  };
})();

