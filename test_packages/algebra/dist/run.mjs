import fs from 'node:fs/promises';

const pkg_math_utilsv0_1_0Wasm = await fs.readFile('pkg/math_utilsv0.1.0/dist/main.wasm');
const pkg_math_utilsv0_1_0 = await WebAssembly.instantiate(pkg_math_utilsv0_1_0Wasm);

const add1Wasm = await fs.readFile('dist/add1.wasm');
const add1 = await WebAssembly.instantiate(add1Wasm);

const mainWasm = await fs.readFile('dist/main.wasm');
const main = await WebAssembly.instantiate(mainWasm, {
  ['pkg/math_utilsv0.1.0']: { abs_i32: pkg_math_utilsv0_1_0.instance.exports.abs_i32 },
  ['add1']: { add: add1.instance.exports.add }
});
// main.instance.exports.<your_function>()
