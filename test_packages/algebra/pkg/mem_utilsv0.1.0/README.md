# mem_utils
a module for memory manipulation with simd, currently implements xor and reverse.  
in browser testing, xor_mem_blocks shows consistent 30x speedups over a standard js implementations and reverse_mem_block_bytes shows 19x speedups over a standard js implementation (on sequences 4096 bytes in length, begins showing speedups at 64 bytes).  

>**note:** this package is in active development and will be updated with more useful functions as they are needed (feel free to send recommendations to the author!).

## functions
### reverse_mem_block_bytes
> ** warning: not in place! **  

reverses a memory block.
params: 
- `mem_blk_ptr`: pointer to the memory block to reverse
- `mem_blk_len`: length of the memory block
- `write_ptr`: pointer to the memory block to write the result to

returns: none!

### xor_mem_blocks
> ** warning: not in place! **  

xors two memory blocks of equal length. 
params: 
- `a_ptr`: pointer to the first memory block
- `b_ptr`: pointer to the second memory block
- `len`: length of the memory blocks
- `write_ptr`: pointer to the memory block to write the result to

returns: none!
