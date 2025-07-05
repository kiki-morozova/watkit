(module
  ;; import from math_utils
  (import "add1" "abs_add" (func $abs_add (param i32) (param i32) (result i32)))

  (func (export "safe_distance") (param $a i32) (param $b i32) (result i32)
    (call $abs_add
      (i32.sub (local.get $a) (local.get $b))
      (i32.const 1)
    )
  )

)
