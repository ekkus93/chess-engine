use chess_engine_fuzz::fuzz_c_abi_buffers_and_handles;

#[test]
fn forged_buffer_with_wrong_token_type_is_rejected_as_invalid_buffer() {
    fuzz_c_abi_buffers_and_handles(include_bytes!(
        "../regressions/c_abi_buffers_handles/forged-buffer-wrong-token-type.bin"
    ));
}
