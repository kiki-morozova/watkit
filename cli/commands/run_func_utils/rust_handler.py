from colorama import Fore, Style
from typing import List, Dict
import os

def generate_rust_stub(
    output_path: str,
    wasm_path: str,
    imports: List[Dict[str, str]],
    module_dir: str  
) -> None:
    """
    Generate a Rust stub that loads the main WASM module and links imported modules.
    Args:
        output_path: str - path to the output Rust file
        wasm_path: str - path to the main WASM file
        imports: List of dicts with 'module' and 'name' keys
        module_dir: base directory containing installed modules (e.g., "watkit_modules")
    """
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

        for mod_name, funcs in grouped_imports.items():
            mod_path = os.path.join(module_dir, mod_name, "dist", "main.wasm").replace("\\", "/")
            instance_var = f"{mod_name}_instance"
            f.write(f"""    // Load and instantiate {mod_name}
                let {mod_name}_module = Module::from_file(&engine, "{mod_path}")?;
                let {instance_var} = Instance::new(&mut store, &{mod_name}_module, &[])?;
            """)
            for func in funcs:
                f.write(f"""    let {mod_name}_{func} = {instance_var}
                        .get_func(&mut store, "{func}")
                        .ok_or("missing function {func}")?;
                    linker.define("{mod_name}", "{func}", Extern::Func({mod_name}_{func}))?;
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
