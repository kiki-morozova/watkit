from colorama import Fore, Style
import re

def escape_js_string(s: str) -> str:
    """Escape a string for use in JavaScript."""
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')

def generate_js_runner(output_path: str, main_module_path: str, imports: list[dict[str, str]], module_paths: dict[str, str]) -> None:
    """
    Generate a JS runner that loads a WASM module and calls an exported function.
    Args:
        output_path: str - path to the output JS file
        main_module_path: str - path to the main WAT file
        imports: list[dict[str, str]] - list of imports from the main WAT file
        module_paths: dict[str, str] - mapping of module names to their WASM file paths (includes bundled deps)
    """
    # Build a map of module names to their exported functions
    modules = {}
    for imp in imports:
        mod = imp["module"]
        modules.setdefault(mod, set()).add(imp["name"])

    with open(output_path, "w") as f:
        f.write("import fs from 'node:fs/promises';\n\n")

        # Load all modules in module_paths (including bundled dependencies)
        for mod_name, mod_path in module_paths.items():
            # Create a valid JS identifier for the variable name
            var_name = re.sub(r'[^a-zA-Z0-9_]', '_', mod_name)
            f.write(f"const {var_name}Wasm = await fs.readFile('{mod_path}');\n")
            f.write(f"const {var_name} = await WebAssembly.instantiate({var_name}Wasm);\n\n")

        f.write(f"const mainWasm = await fs.readFile('{main_module_path}');\n")
        f.write("const main = await WebAssembly.instantiate(mainWasm, {\n")
        
        # Build import object with all modules that have exports
        import_entries = []
        for mod_name, funcs in modules.items():
            if mod_name in module_paths:  # Only include modules that were loaded
                var_name = re.sub(r'[^a-zA-Z0-9_]', '_', mod_name)
                exports = ", ".join([f"{fn}: {var_name}.instance.exports.{fn}" for fn in funcs])
                import_entries.append(f"  [{repr(mod_name)}]: {{ {exports} }}")
        
        f.write(",\n".join(import_entries) + "\n")
        f.write("});\n")
        f.write("// main.instance.exports.<your_function>()\n")

    print(f"{Fore.GREEN}✓ JS runner written to {output_path}{Style.RESET_ALL}")