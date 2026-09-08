export default {
  multipass: true,
  floatPrecision: 2,
  plugins: [
    { name: 'preset-default', params: { overrides: {
      cleanupIds: false,          // the border's <use href="#abN"> and mask ids must survive
      removeViewBox: false,
      convertShapeToPath: false,
      mergePaths: false,
      removeUnknownsAndDefaults: { keepDataAttrs: false },
    } } },
  ],
};
