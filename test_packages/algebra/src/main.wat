(module
  ;; import from math_utils
  (import "math_utils" "abs_i32" (func $abs_i32 (param i32) (result i32)))

  (func (export "safe_distance") (param $a i32) (param $b i32) (result i32)
    (call $abs_i32
      (i32.sub (local.get $a) (local.get $b))
    )
  )

)
