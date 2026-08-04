//! Shared deterministic and mutation-based robustness entrypoints.

use std::{ptr, str};

use chess_book::IndexedBook;
use chess_core::{Game, Position, UciMove};
use chess_ffi::c_abi::{
    chess_engine_buffer_free, chess_engine_create, chess_engine_destroy, chess_engine_get_fen,
    chess_engine_play_move, chess_engine_set_position, ChessEngineBuffer, ChessEngineConfig,
    ChessEngineResultCode, CHESS_ENGINE_NULL_HANDLE,
};
use chess_tune::NamedWeightArtifact;

const MAX_SEQUENCE_PLIES: usize = 128;

fn read_u32(data: &[u8], offset: usize) -> u32 {
    let mut bytes = [0_u8; 4];
    for (index, output) in bytes.iter_mut().enumerate() {
        *output = data.get(offset + index).copied().unwrap_or_default();
    }
    u32::from_le_bytes(bytes)
}

fn assert_position(position: &Position, context: &str) {
    position
        .validate_invariants()
        .unwrap_or_else(|error| panic!("{context}: invariant failure: {error}"));
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "{context}: incremental hash differs from full recomputation"
    );
}

/// Exercises strict FEN parsing and canonical round trips.
pub fn fuzz_fen_parser(data: &[u8]) {
    let Ok(text) = str::from_utf8(data) else {
        return;
    };
    let Ok(position) = Position::from_fen(text) else {
        return;
    };
    assert_position(&position, "accepted FEN");
    let canonical = position.to_fen();
    let reparsed = Position::from_fen(&canonical)
        .unwrap_or_else(|error| panic!("canonical FEN failed to parse: {canonical}: {error}"));
    assert_eq!(reparsed, position, "canonical FEN changed the position");
    assert_eq!(reparsed.to_fen(), canonical, "canonical FEN was unstable");
}

/// Exercises UCI coordinate-move syntax parsing and formatting.
pub fn fuzz_uci_move_parser(data: &[u8]) {
    let Ok(text) = str::from_utf8(data) else {
        return;
    };
    let Ok(parsed) = text.parse::<UciMove>() else {
        return;
    };
    let canonical = parsed.to_string();
    let reparsed = canonical
        .parse::<UciMove>()
        .unwrap_or_else(|error| panic!("formatted UCI move failed to parse: {canonical}: {error}"));
    assert_eq!(reparsed, parsed, "UCI move round trip changed identity");
}

/// Selects a bounded legal sequence from bytes and reverses it exactly.
pub fn fuzz_legal_sequence(data: &[u8]) {
    let mut position = Position::starting();
    let root = position.clone();
    let mut undos = Vec::new();

    for (ply, selector) in data.iter().copied().take(MAX_SEQUENCE_PLIES).enumerate() {
        let moves = position
            .legal_moves()
            .unwrap_or_else(|error| panic!("ply {ply}: legal generation failed: {error}"));
        if moves.is_empty() {
            break;
        }
        let index = usize::from(selector) % moves.len();
        let current = moves.get(index).expect("bounded legal move index exists");
        assert!(
            position
                .is_legal_move(current)
                .unwrap_or_else(|error| panic!("ply {ply}: legality query failed: {error}")),
            "ply {ply}: generated move {} was rejected",
            current.to_uci()
        );
        let moving_side = position.side_to_move();
        let undo = position.make_move(current).unwrap_or_else(|error| {
            panic!(
                "ply {ply}: generated move {} failed: {error}",
                current.to_uci()
            )
        });
        assert!(
            !position.is_in_check(moving_side),
            "ply {ply}: legal move {} left its king in check",
            current.to_uci()
        );
        assert_position(&position, &format!("ply {ply}"));
        undos.push(undo);
    }

    while let Some(undo) = undos.pop() {
        position
            .unmake_move(undo)
            .unwrap_or_else(|error| panic!("reverse unmake failed: {error}"));
        assert_position(&position, "reverse unmake");
    }
    assert_eq!(position, root, "legal sequence did not restore its root");
}

/// Exercises game-owned move, repetition, draw, and reverse-history state.
pub fn fuzz_game_history(data: &[u8]) {
    let mut game = Game::starting();
    let root = game.clone();
    let mut undos = Vec::new();

    for (ply, selector) in data.iter().copied().take(MAX_SEQUENCE_PLIES).enumerate() {
        let status = game
            .status()
            .unwrap_or_else(|error| panic!("ply {ply}: status failed: {error}"));
        if status.is_terminal() {
            break;
        }
        let moves = game
            .legal_moves()
            .unwrap_or_else(|error| panic!("ply {ply}: game move generation failed: {error}"));
        if moves.is_empty() {
            break;
        }
        let current = moves
            .get(usize::from(selector) % moves.len())
            .expect("bounded game move index exists");
        let undo = game.make_move(current).unwrap_or_else(|error| {
            panic!("ply {ply}: game move {} failed: {error}", current.to_uci())
        });
        assert_position(game.position(), &format!("game ply {ply}"));
        assert_eq!(game.position_hashes().len(), game.moves().len() + 1);
        assert_eq!(
            game.position_hashes().last().copied(),
            Some(game.position().zobrist())
        );
        assert!(game.repetition_count() >= 1);
        let _ = game.draw_claims();
        let _ = game
            .status()
            .unwrap_or_else(|error| panic!("ply {ply}: post-move status failed: {error}"));
        undos.push(undo);
    }

    while let Some(undo) = undos.pop() {
        game.unmake_move(undo)
            .unwrap_or_else(|error| panic!("game reverse unmake failed: {error}"));
        assert_position(game.position(), "game reverse unmake");
        assert_eq!(game.position_hashes().len(), game.moves().len() + 1);
    }
    assert_eq!(game, root, "game history did not restore its root");
}

/// Exercises the complete named evaluation-weight artifact parser.
pub fn fuzz_weight_parser(data: &[u8]) {
    let Ok(text) = str::from_utf8(data) else {
        return;
    };
    let Ok(artifact) = NamedWeightArtifact::deserialize(text) else {
        return;
    };
    let canonical = artifact
        .serialize()
        .unwrap_or_else(|error| panic!("accepted weight artifact failed to serialize: {error}"));
    let reparsed = NamedWeightArtifact::deserialize(&canonical)
        .unwrap_or_else(|error| panic!("canonical weight artifact failed to parse: {error}"));
    assert_eq!(
        reparsed, artifact,
        "weight artifact round trip changed identity"
    );
}

/// Exercises the checksummed indexed opening-book parser.
pub fn fuzz_opening_book_parser(data: &[u8]) {
    let Ok(book) = IndexedBook::from_bytes(data) else {
        return;
    };
    let canonical = book.to_bytes();
    let reparsed = IndexedBook::from_bytes(&canonical)
        .unwrap_or_else(|error| panic!("canonical opening book failed to parse: {error}"));
    assert_eq!(reparsed, book, "opening-book round trip changed identity");
}

/// Exercises valid-pointer C ABI inputs, opaque handles, and owned buffers.
pub fn fuzz_c_abi_buffers_and_handles(data: &[u8]) {
    let selector = data.first().copied().unwrap_or_default();
    let mut config = ChessEngineConfig::new();
    config.transposition_table_mebibytes = u64::from(selector % 4 + 1);
    if selector & 1 != 0 {
        config.struct_size = read_u32(data, 1);
    }
    if selector & 2 != 0 {
        config.abi_version = read_u32(data, 5);
    }

    let mut handle = CHESS_ENGINE_NULL_HANDLE;
    // SAFETY: Both pointers reference initialized records for the duration of the call.
    let create_code = unsafe { chess_engine_create(&config, &mut handle) };
    if create_code != ChessEngineResultCode::Ok {
        assert_eq!(handle, CHESS_ENGINE_NULL_HANDLE);
        return;
    }
    assert_ne!(handle, CHESS_ENGINE_NULL_HANDLE);

    let payload = data.get(9..).unwrap_or_default();
    let (input_pointer, input_length) = if selector & 4 != 0 {
        (ptr::null(), payload.len().max(1))
    } else {
        (payload.as_ptr(), payload.len())
    };
    // SAFETY: The non-null branch supplies the exact readable payload length; the null
    // branch intentionally tests the ABI's null validation before any dereference.
    let _ = unsafe { chess_engine_set_position(handle, input_pointer, input_length) };

    let move_bytes = payload.get(..payload.len().min(5)).unwrap_or_default();
    // SAFETY: `move_bytes` is readable for exactly the supplied length.
    let _ = unsafe { chess_engine_play_move(handle, move_bytes.as_ptr(), move_bytes.len()) };

    let mut output = ChessEngineBuffer::empty();
    // SAFETY: `output` is writable for one complete buffer record.
    assert_eq!(
        unsafe { chess_engine_get_fen(handle, &mut output) },
        ChessEngineResultCode::Ok
    );
    let mut stale = output;
    if selector & 8 != 0 {
        let mut forged = output;
        forged.allocation ^= 1;
        // SAFETY: The record is intentionally fabricated; validation must reject it
        // without dereferencing or releasing the live allocation.
        assert_eq!(
            unsafe { chess_engine_buffer_free(&mut forged) },
            ChessEngineResultCode::InvalidBuffer
        );
    }
    // SAFETY: `output` is the unchanged live record returned by the ABI.
    assert_eq!(
        unsafe { chess_engine_buffer_free(&mut output) },
        ChessEngineResultCode::Ok
    );
    // SAFETY: `stale` repeats a released allocation token and must fail closed.
    assert_eq!(
        unsafe { chess_engine_buffer_free(&mut stale) },
        ChessEngineResultCode::InvalidBuffer
    );

    assert_eq!(chess_engine_destroy(handle), ChessEngineResultCode::Ok);
    assert_eq!(
        chess_engine_destroy(handle),
        ChessEngineResultCode::InvalidHandle
    );
    let mut stale_output = ChessEngineBuffer::empty();
    // SAFETY: The output record is writable; the handle is intentionally stale.
    assert_eq!(
        unsafe { chess_engine_get_fen(handle, &mut stale_output) },
        ChessEngineResultCode::InvalidHandle
    );
    assert_eq!(stale_output, ChessEngineBuffer::empty());
}

#[cfg(test)]
mod tests {
    use chess_book::IndexedBook;
    use chess_search::EvaluationWeights;
    use chess_tune::{
        NamedWeightArtifact, TrainingDatasetProvenance, TrainingMetadata, TrainingRunProvenance,
    };

    use super::{
        fuzz_c_abi_buffers_and_handles, fuzz_fen_parser, fuzz_game_history, fuzz_legal_sequence,
        fuzz_opening_book_parser, fuzz_uci_move_parser, fuzz_weight_parser,
    };

    const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    #[test]
    fn valid_images_reach_every_success_path() {
        fuzz_fen_parser(STARTING_FEN.as_bytes());
        fuzz_uci_move_parser(b"e2e4");
        fuzz_legal_sequence(&[0, 1, 2, 3, 5, 8, 13, 21, 34, 55]);
        fuzz_game_history(&[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]);

        let book = IndexedBook::from_records(Vec::new()).expect("empty book is valid");
        fuzz_opening_book_parser(&book.to_bytes());

        let metadata = TrainingMetadata::new(
            TrainingRunProvenance::new(1, [1; 20], 2, 3, 4),
            TrainingDatasetProvenance::new(1, 5, 6, 7),
        );
        let artifact = NamedWeightArtifact::new(8, metadata, EvaluationWeights::DEFAULT)
            .expect("baseline artifact is valid");
        let serialized = artifact.serialize().expect("artifact serializes");
        fuzz_weight_parser(serialized.as_bytes());

        let mut abi_input = vec![0_u8; 9];
        abi_input.extend_from_slice(STARTING_FEN.as_bytes());
        fuzz_c_abi_buffers_and_handles(&abi_input);
    }

    #[test]
    fn malformed_inputs_are_rejected_without_panics() {
        fuzz_fen_parser(&[0xff, 0xfe]);
        fuzz_uci_move_parser(b"e2e9");
        fuzz_weight_parser(b"not an artifact");
        fuzz_opening_book_parser(b"CHBKIDX");
        fuzz_c_abi_buffers_and_handles(&[7, 0, 0, 0, 0, 0, 0, 0, 0]);
    }
}
