(module
    (import "pkg/math_utilsv0.1.0" "abs_i32" (func $abs_i32 (param i32) (result i32)))
    
    (func (export "abs_add") (param $a i32) (param $b i32) (result i32)
        (call $abs_i32
            (i32.add (local.get $a) (local.get $b))
        )
    )
)
