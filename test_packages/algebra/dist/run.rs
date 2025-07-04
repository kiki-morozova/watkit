use wasmtime::*;
        use std::fs;

        fn main() -> anyhow::Result<()> {
            let engine = Engine::default();
            let mut store = Store::new(&engine, ());
            let mut linker = Linker::new(&engine);

            // Load and instantiate pkg/math_utilsv0.1.0
                let pkg_math_utilsv0_1_0_module = Module::from_file(&engine, "pkg/math_utilsv0.1.0/dist/main.wasm")?;
                let pkg_math_utilsv0_1_0_instance = Instance::new(&mut store, &pkg_math_utilsv0_1_0_module, &[])?;
                // Load and instantiate add1
                let add1_module = Module::from_file(&engine, "dist/add1.wasm")?;
                let add1_instance = Instance::new(&mut store, &add1_module, &[])?;
                let pkg_math_utilsv0_1_0_abs_i32 = pkg_math_utilsv0_1_0_instance
                        .get_func(&mut store, "abs_i32")
                        .ok_or("missing function abs_i32")?;
                    linker.define("pkg/math_utilsv0.1.0", "abs_i32", Extern::Func(pkg_math_utilsv0_1_0_abs_i32))?;
                    let add1_add = add1_instance
                        .get_func(&mut store, "add")
                        .ok_or("missing function add")?;
                    linker.define("add1", "add", Extern::Func(add1_add))?;
                
            // Load and instantiate main module
            let main_module = Module::from_file(&engine, "dist/main.wasm")?;
            let main_instance = linker.instantiate(&mut store, &main_module)?;

            println!("✓ wasm module loaded and linked successfully.");
            // example: call main_instance.get_func(...) here

            Ok(())
        }
        