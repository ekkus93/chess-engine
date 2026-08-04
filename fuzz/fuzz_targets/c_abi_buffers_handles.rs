#![no_main]

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| chess_engine_fuzz::fuzz_c_abi_buffers_handles(data));
