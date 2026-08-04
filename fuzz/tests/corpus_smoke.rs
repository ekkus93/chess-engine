use std::{fs, path::Path};

use chess_engine_fuzz::{
    fuzz_c_abi_buffers_and_handles, fuzz_fen_parser, fuzz_game_history, fuzz_legal_sequence,
    fuzz_opening_book_parser, fuzz_uci_move_parser, fuzz_weight_parser,
};

type Target = fn(&[u8]);

#[test]
fn committed_seed_corpus_is_nonempty_and_replayable() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("corpus");
    let targets: [(&str, Target); 7] = [
        ("fen_parser", fuzz_fen_parser),
        ("uci_move_parser", fuzz_uci_move_parser),
        ("legal_sequence", fuzz_legal_sequence),
        ("game_history", fuzz_game_history),
        ("weight_parser", fuzz_weight_parser),
        ("opening_book_parser", fuzz_opening_book_parser),
        ("c_abi_buffers_handles", fuzz_c_abi_buffers_and_handles),
    ];

    for (name, target) in targets {
        let directory = root.join(name);
        let mut paths = fs::read_dir(&directory)
            .unwrap_or_else(|error| panic!("failed to read {}: {error}", directory.display()))
            .map(|entry| entry.expect("corpus directory entry is readable").path())
            .filter(|path| path.is_file())
            .collect::<Vec<_>>();
        paths.sort();
        assert!(!paths.is_empty(), "{name} corpus is empty");
        for path in paths {
            let bytes = fs::read(&path)
                .unwrap_or_else(|error| panic!("failed to read {}: {error}", path.display()));
            target(&bytes);
        }
    }
}
