from colorama import Fore, Style
from typing import List, Dict
import os
import re

def escape_rust_string(s: str) -> str:
    """Escape a string for use in Rust."""
    return s.replace('\\', '\\\\').replace('"', '\\"')

def generate_rust_stub(
    output_path: str,
    wasm_path: str,
    imports: List[Dict[str, str]],
    module_paths: Dict[str, str]
) -> None:
    """
    Generate a Rust stub that loads the main WASM module and links imported modules.
    Args:
        output_path: str - path to the output Rust file
        wasm_path: str - path to the main WASM file
        imports: List of dicts with 'module' and 'name' keys
        module_paths: Dict mapping module names to their WASM file paths (includes bundled deps)
    """
    # Build a map of module names to their exported functions
    grouped_imports = {}
    for imp in imports:
        grouped_imports.setdefault(imp["module"], set()).add(imp["name"])

    with open(output_path, "w") as f:
        f.write(
        """use wasmtime::*;
        use std::fs;

        fn main() -> anyhow::Result<()> {
            let engine = Engine::default();
            let mut store = Store::new(&engine, ());
            let mut linker = Linker::new(&engine);

        """)

        # Load all modules in module_paths (including bundled dependencies)
        for mod_name, mod_path in module_paths.items():
            # Create a valid Rust identifier for the variable name
            var_name = re.sub(r'[^a-zA-Z0-9_]', '_', mod_name)
            instance_var = f"{var_name}_instance"
            f.write(f"""    // Load and instantiate {mod_name}
                let {var_name}_module = Module::from_file(&engine, "{mod_path}")?;
                let {instance_var} = Instance::new(&mut store, &{var_name}_module, &[])?;
            """)

        # Link functions for modules that have exports
        for mod_name, funcs in grouped_imports.items():
            if mod_name in module_paths:  # Only link modules that were loaded
                var_name = re.sub(r'[^a-zA-Z0-9_]', '_', mod_name)
                instance_var = f"{var_name}_instance"
                for func in funcs:
                    f.write(f"""    let {var_name}_{func} = {instance_var}
                        .get_func(&mut store, "{func}")
                        .ok_or("missing function {func}")?;
                    linker.define("{escape_rust_string(mod_name)}", "{func}", Extern::Func({var_name}_{func}))?;
                """)

        f.write(f"""
            // Load and instantiate main module
            let main_module = Module::from_file(&engine, "{wasm_path}")?;
            let main_instance = linker.instantiate(&mut store, &main_module)?;

            println!("✓ wasm module loaded and linked successfully.");
            // example: call main_instance.get_func(...) here

            Ok(())
        }}
        """)

    print(f"{Fore.GREEN}✓ Rust stub written to {output_path}{Style.RESET_ALL}")
