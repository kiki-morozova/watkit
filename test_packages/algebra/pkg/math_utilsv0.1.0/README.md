# math_utils
includes simple math functions for wasm, that are especially useful for low-level development, but aren't built into WAT.  
>**n ote:** this package will be updated with more useful functions as they are needed (feel free to send recommendations to the author!).

## functions

### clamp
implements a clamp functions for i32 and i64 in WAT. 
params: 
- `x`: the value to clamp (i32 or i64, depending on the function)
- `min`: the minimum value (i32 or i64, depending on the function)
- `max`: the maximum value (i32 or i64, depending on the function)

returns:
- `x` if `x` is between `min` and `max`
- `min` if `x` is less than `min`
- `max` if `x` is greater than `max`

### abs
implements an abs function for i32 and i64 in WAT. 
params: 
- `x`: the value to get the absolute value of (i32 or i64, depending on the function)

returns:
- `x` if `x` is greater than 0
- `-x` if `x` is less than 0

### next_power_of_two
finds the next power of two greater than or equal to the given value using the clz instruction (it's really cool, check it out!).
params: 
- `x`: the value to find the next power of two for (i32 or i64, depending on the function)

returns:
- the next power of two greater than or equal to `x`

### prev_power_of_two
finds the previous power of two less than or equal to the given value using the clz instruction.
params: 
- `x`: the value to find the previous power of two for (i32 or i64, depending on the function)

returns:
- the previous power of two less than or equal to `x`


### min/max i32/i64
implements min and max functions for i32 and i64 in WAT.
params: 
- `a`: the first value to compare (i32 or i64, depending on the function)
- `b`: the second value to compare (i32 or i64, depending on the function)

returns:
- the minimum of `a` and `b`
- the maximum of `a` and `b`



