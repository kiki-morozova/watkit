(module 
    (memory (export "memory") 1)

    (func (export "reverse_mem_block_bytes") ;; NOT AN IN PLACE OPERATION
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

  (func (export "xor_mem_blocks") ;; NOT AN IN PLACE OPERATION
    (param $a_ptr i32) ;; a and b must be the same length (obv?)
    (param $b_ptr i32)
    (param $len i32)
    (param $write_ptr i32)

    (local $unaligned_head_len i32)
    (local $unaligned_tail_len i32)
    (local $aligned_len i32)
    (local $offset i32)
    (local $simd_block_counter i32)
    (local $a_vec v128)
    (local $b_vec v128)
    (local $a_curr i32)
    (local $b_curr i32)
    (local $w_curr i32)

    (local.set $a_curr (local.get $a_ptr))
    (local.set $b_curr (local.get $b_ptr))
    (local.set $w_curr (local.get $write_ptr))

    ;; calc unaligned head length
    (local.set $unaligned_head_len
      (i32.rem_u (local.get $a_curr) (i32.const 16))
    )

    ;; process head bytes
    (block $aligned
      (loop $unaligned_head_loop
        (br_if $aligned (i32.eqz (local.get $unaligned_head_len)))
        ;; store a[i] ^ b[i] to w[i]
        (i32.store8
          (local.get $w_curr)
          (i32.xor
            (i32.load8_u (local.get $a_curr))
            (i32.load8_u (local.get $b_curr))
          )
        )
        ;; a++, b++, w++
        (local.set $a_curr (i32.add (local.get $a_curr) (i32.const 1)))
        (local.set $b_curr (i32.add (local.get $b_curr) (i32.const 1)))
        (local.set $w_curr (i32.add (local.get $w_curr) (i32.const 1)))

        ;; unaligned head len--
        (local.set $unaligned_head_len (i32.sub (local.get $unaligned_head_len) (i32.const 1)))
        (br $unaligned_head_loop)
      )
    )

    ;; how many full, aligned 16-byte blocks can we simd over? aligned = speedup which is why we handle the head and tail separately
    (local.set $aligned_len
      (i32.and (local.get $len) (i32.const -16))
    )

    (local.set $simd_block_counter (i32.const 0))

    ;; simd xor
    (block $done_simd
      (loop $simd_loop
        (br_if $done_simd
          (i32.ge_u
            (local.get $simd_block_counter)
            (i32.div_u (local.get $aligned_len) (i32.const 16))
          )
        )

        (local.set $a_vec (v128.load (local.get $a_curr)))
        (local.set $b_vec (v128.load (local.get $b_curr)))

        ;; xor the 16 bytes we just loaded
        (v128.store
          (local.get $w_curr)
          (v128.xor (local.get $a_vec) (local.get $b_vec))
        )

        ;; move forward
        (local.set $a_curr (i32.add (local.get $a_curr) (i32.const 16)))
        (local.set $b_curr (i32.add (local.get $b_curr) (i32.const 16)))
        (local.set $w_curr (i32.add (local.get $w_curr) (i32.const 16)))
        (local.set $simd_block_counter (i32.add (local.get $simd_block_counter) (i32.const 1)))

        (br $simd_loop)
      )
    )

    ;; tail: any bytes not covered by simd (bc the length was not a multiple of 16 and the head was made aligned)
    (local.set $unaligned_tail_len
      (i32.sub (local.get $len)
               (i32.add
                 (i32.sub (local.get $a_curr) (local.get $a_ptr))
                 (i32.const 0)
               )
      )
    )

    ;; handle tail like head
    (block $done_tail
      (loop $tail_loop
        (br_if $done_tail (i32.eqz (local.get $unaligned_tail_len)))

        (i32.store8
          (local.get $w_curr)
          (i32.xor
            (i32.load8_u (local.get $a_curr))
            (i32.load8_u (local.get $b_curr))
          )
        )
        (local.set $a_curr (i32.add (local.get $a_curr) (i32.const 1)))
        (local.set $b_curr (i32.add (local.get $b_curr) (i32.const 1)))
        (local.set $w_curr (i32.add (local.get $w_curr) (i32.const 1)))
        (local.set $unaligned_tail_len (i32.sub (local.get $unaligned_tail_len) (i32.const 1)))
        (br $tail_loop)
      )
    )
  )
)