(module 
    (memory (export "memory") 1)

    (func (export "reverse_mem_block_bytes_copy") ;; NOT AN IN PLACE OPERATION
        (param $mem_blk_ptr i32)
        (param $mem_blk_len i32) ;; in bytes
        (param $write_ptr i32)

        (local $unaligned_tail_len i32)
        (local $curr_read_ptr i32)
        (local $curr_write_ptr i32)
        (local $remainder_after_simd i32)
        (local $num_simd_blocks i32)
        (local $simd_block_counter i32)
        
        (local $shuffling_vector v128)

        (local.set $curr_read_ptr (i32.add (local.get $mem_blk_ptr) (i32.sub (local.get $mem_blk_len) (i32.const 1))))
        (local.set $curr_write_ptr (local.get $write_ptr))
        ;; check alignment of end of mem block
        (local.set $unaligned_tail_len
            (i32.rem_u (local.get $curr_read_ptr) (i32.const 16))
        )
        ;; compute the number of SIMD blocks 
        (local.set $num_simd_blocks
            (i32.div_u (i32.sub (local.get $mem_blk_len) (local.get $unaligned_tail_len)) (i32.const 16))
        )
        ;; compute remainder (how much to loop) after simd blocks
        (local.set $remainder_after_simd
            (i32.rem_u (i32.sub (local.get $mem_blk_len) (local.get $unaligned_tail_len)) (i32.const 16))
        )
        
        (block $handle_pre_aligned_chunk
            (loop $unaligned_bytes
                (br_if $handle_pre_aligned_chunk (i32.eqz (local.get $unaligned_tail_len)))
                (i32.store8
                    (local.get $curr_write_ptr)
                    (i32.load8_u(local.get $curr_read_ptr))
                )
                ;; num unaligned bytes left--
                (local.set $unaligned_tail_len (i32.sub (local.get $unaligned_tail_len) (i32.const 1)))
                ;; read ptr -- 
                (local.set $curr_read_ptr (i32.sub (local.get $curr_read_ptr) (i32.const 1)))
                ;; write ptr ++
                (local.set $curr_write_ptr (i32.add (local.get $curr_write_ptr) (i32.const 1)))
                (br $unaligned_bytes)
            )
        )
        (local.set $curr_read_ptr (i32.add (local.get $curr_read_ptr) (i32.const 1)))

        (local.set $simd_block_counter (i32.const 0))
        (block $reverse_with_simd
            (loop $simd_batch
                (br_if $reverse_with_simd (i32.ge_u (local.get $simd_block_counter) (local.get $num_simd_blocks)))
                ;; read ptr - 16
                (local.set $curr_read_ptr (i32.sub (local.get $curr_read_ptr) (i32.const 16)))

                (local.set $shuffling_vector
                    (v128.load
                        (local.get $curr_read_ptr)
                    )
                )

                (v128.store
                    (local.get $curr_write_ptr)
                    (i8x16.shuffle 
                        15 14 13 12 11 10 9 8 7 6 5 4 3 2 1 0
                        (local.get $shuffling_vector)
                        (local.get $shuffling_vector)
                    )
                )
                ;; write pointer + 16 only after store
                (local.set $curr_write_ptr (i32.add (local.get $curr_write_ptr) (i32.const 16)))

                ;; simd_block_counter++
                (local.set $simd_block_counter (i32.add (local.get $simd_block_counter) (i32.const 1)))
                (br $simd_batch)
            )
        )

        (local.set $curr_read_ptr (i32.sub (local.get $curr_read_ptr) (i32.const 1)))

        ;; after simd, do remainder
        (block $handle_post_aligned_chunk
            (loop $post_unaligned_bytes
                (br_if $handle_post_aligned_chunk (i32.eqz (local.get $remainder_after_simd)))
                (i32.store8
                    (local.get $curr_write_ptr)
                    (i32.load8_u(local.get $curr_read_ptr))
                )
                ;; num unaligned bytes left--
                (local.set $remainder_after_simd (i32.sub (local.get $remainder_after_simd) (i32.const 1)))
                ;; read ptr -- 
                (local.set $curr_read_ptr (i32.sub (local.get $curr_read_ptr) (i32.const 1)))
                ;; write ptr ++
                (local.set $curr_write_ptr (i32.add (local.get $curr_write_ptr) (i32.const 1)))
                (br $post_unaligned_bytes)
            )
        )
    )
)