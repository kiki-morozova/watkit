use wasmtime::*;
        use std::fs;

        fn main() -> anyhow::Result<()> {
            let engine = Engine::default();
            let mut store = Store::new(&engine, ());
            let mut linker = Linker::new(&engine);

            // Load and instantiate math_utils
                let math_utils_module = Module::from_file(&engine, "watkit_modules/math_utils/dist/main.wasm")?;
                let math_utils_instance = Instance::new(&mut store, &math_utils_module, &[])?;
                let math_utils_abs_i32 = math_utils_instance
                        .get_func(&mut store, "abs_i32")
                        .ok_or("missing function abs_i32")?;
                    linker.define("math_utils", "abs_i32", Extern::Func(math_utils_abs_i32))?;
                
            // Load and instantiate main module
            let main_module = Module::from_file(&engine, "dist/main.wasm")?;
            let main_instance = linker.instantiate(&mut store, &main_module)?;

            println!("✓ wasm module loaded and linked successfully.");
            // example: call main_instance.get_func(...) here

            Ok(())
        }
        