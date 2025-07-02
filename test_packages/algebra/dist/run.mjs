import fs from 'node:fs/promises';

const math_utilsWasm = await fs.readFile('watkit_modules/math_utils/dist/main.wasm');
const math_utils = await WebAssembly.instantiate(math_utilsWasm);

const mainWasm = await fs.readFile('dist/main.wasm');
const main = await WebAssembly.instantiate(mainWasm, {
  math_utils: { abs_i32: math_utils.instance.exports.abs_i32 }
});
// main.instance.exports.<your_function>()
