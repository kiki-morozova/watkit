from colorama import Fore, Style

def generate_js_runner(output_path: str, main_module_path: str, imports: list[dict[str, str]], MODULES_DIR: str) -> None:
    """
    Generate a JS runner that loads a WASM module and calls an exported function.
    Args:
        output_path: str - path to the output JS file
        main_module_path: str - path to the main WAT file
        imports: list[dict[str, str]] - list of imports from the main WAT file
        MODULES_DIR: str - path to the modules directory
    """
    modules = {}
    for imp in imports:
        mod = imp["module"]
        modules.setdefault(mod, set()).add(imp["name"])

    with open(output_path, "w") as f:
        f.write("import fs from 'node:fs/promises';\n\n")

        for mod in modules:
            f.write(f"const {mod}Wasm = await fs.readFile('{MODULES_DIR}/{mod}/dist/main.wasm');\n")
            f.write(f"const {mod} = await WebAssembly.instantiate({mod}Wasm);\n\n")

        f.write(f"const mainWasm = await fs.readFile('{main_module_path}');\n")
        f.write("const main = await WebAssembly.instantiate(mainWasm, {\n")
        for i, (mod, funcs) in enumerate(modules.items()):
            exports = ", ".join([f"{fn}: {mod}.instance.exports.{fn}" for fn in funcs])
            comma = "," if i < len(modules) - 1 else ""
            f.write(f"  {mod}: {{ {exports} }}{comma}\n")
        f.write("});\n")
        f.write("// main.instance.exports.<your_function>()\n")

    print(f"{Fore.GREEN}✓ JS runner written to {output_path}{Style.RESET_ALL}")