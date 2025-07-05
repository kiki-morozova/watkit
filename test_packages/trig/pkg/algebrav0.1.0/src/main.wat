(module
  ;; import from math_utils
  (import "pkg/math_utilsv0.1.0" "abs_i32" (func $abs_i32 (param i32) (result i32)))
  (import "add1" "add" (func $add (param i32) (param i32) (result i32)))

  (func (export "safe_distance") (param $a i32) (param $b i32) (result i32)
    (call $add
    (call $abs_i32
      (i32.sub (local.get $a) (local.get $b))
    )
    (i32.const 1)
    )
    
  )

)
