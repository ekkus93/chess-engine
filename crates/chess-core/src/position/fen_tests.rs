use std::panic::{catch_unwind, AssertUnwindSafe};

use crate::{Color, Position, PositionBuildError};

use super::FenError;

const START: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const CURATED: &str = "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b qKkQ e3 17 42";

#[test]
fn starting_position_serializes_canonically() {
    let position = Position::from_fen(START).expect("starting FEN is valid");
    assert_eq!(position, Position::starting());
    assert_eq!(position.to_fen(), START);
}

#[test]
fn curated_position_round_trips_with_canonical_castling_order() {
    let position = Position::from_fen(CURATED).expect("curated FEN is valid");
    let canonical = "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b KQkq e3 17 42";
    assert_eq!(position.to_fen(), canonical);
    assert_eq!(
        Position::from_fen(&position.to_fen()).expect("serialized FEN parses"),
        position
    );
}

#[test]
fn malformed_fen_categories_are_fail_loud() {
    let cases = [
        ("", FenError::FieldCount { found: 0 }),
        ("8/8/8/8/8/8/8 w - - 0 1", FenError::RankCount { found: 7 }),
        (
            "8/8/8/8/8/8/8/7 w - - 0 1",
            FenError::RankWidth { rank: 1, files: 7 },
        ),
        (
            "8/8/8/8/8/8/8/7x w - - 0 1",
            FenError::InvalidPlacementCharacter {
                rank: 1,
                file: 8,
                value: 'x',
            },
        ),
        (
            "4k3/8/8/8/8/8/8/P3K3 w - - 0 1",
            FenError::PawnOnPromotionRank {
                square: "a1".parse().expect("square"),
                color: Color::White,
            },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 x - - 0 1",
            FenError::InvalidActiveColor {
                value: "x".to_owned(),
            },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 w KK - 0 1",
            FenError::DuplicateCastlingRight { value: 'K' },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 w A - 0 1",
            FenError::InvalidCastlingField {
                value: "A".to_owned(),
            },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 w - e3 0 1",
            FenError::InvalidEnPassantRank {
                side_to_move: Color::White,
                square: "e3".parse().expect("square"),
            },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 w - - -1 1",
            FenError::InvalidHalfmoveClock {
                value: "-1".to_owned(),
            },
        ),
        (
            "4k3/8/8/8/8/8/8/4K3 w - - 0 0",
            FenError::InvalidFullmoveNumber {
                value: "0".to_owned(),
            },
        ),
    ];

    for (value, expected) in cases {
        assert_eq!(Position::from_fen(value), Err(expected), "{value}");
    }
}

#[test]
fn playable_parser_requires_both_kings_and_does_not_mutate_existing_state() {
    let existing = Position::starting();
    let snapshot = existing.clone();
    assert_eq!(
        Position::from_fen("8/8/8/8/8/8/8/4K3 w - - 0 1"),
        Err(FenError::Position(PositionBuildError::MissingKing {
            color: Color::Black,
        }))
    );
    assert_eq!(existing, snapshot);
}

#[test]
fn parse_serialize_parse_is_stable_for_curated_corpus() {
    for fen in [
        START,
        "4k3/8/8/8/8/8/8/4K3 w - - 99 65535",
        "r3k2r/8/8/8/8/8/8/R3K2R b Kq - 4 23",
        "4k3/8/8/8/8/8/8/4K3 b - a3 0 1",
        "4k3/8/8/8/8/8/8/4K3 w - h6 0 1",
    ] {
        let first = Position::from_fen(fen).expect("corpus FEN is valid");
        let encoded = first.to_fen();
        let second = Position::from_fen(&encoded).expect("canonical FEN is valid");
        assert_eq!(second, first, "{fen}");
        assert_eq!(second.to_fen(), encoded, "{fen}");
    }
}

#[test]
fn arbitrary_utf8_input_never_panics() {
    let mut state = 0x6a09_e667_f3bc_c909_u64;
    for length in 0..96 {
        for _ in 0..64 {
            let mut value = String::new();
            for _ in 0..length {
                state = state
                    .wrapping_mul(6_364_136_223_846_793_005)
                    .wrapping_add(1_442_695_040_888_963_407);
                let scalar =
                    u32::try_from((state >> 32) % 0x11_0000).expect("bounded scalar fits u32");
                value.push(char::from_u32(scalar).unwrap_or('\u{fffd}'));
            }
            assert!(
                catch_unwind(AssertUnwindSafe(|| Position::from_fen(&value))).is_ok(),
                "parser panicked for {value:?}"
            );
        }
    }
}

#[test]
fn analysis_position_policy_is_explicit_and_safe() {
    let accepted = [
        "4k3/8/8/8/8/8/8/4K3 w K - 0 1",
        "4k3/8/8/8/8/8/8/3K4 w K - 0 1",
        "4k3/8/8/3p4/8/8/8/4K3 w - d6 0 1",
        "8/8/8/8/8/8/4k3/4K3 w - - 0 1",
        "4k3/4R3/8/8/8/8/4r3/4K3 w - - 0 1",
        "4r1k1/8/8/8/8/8/8/4K3 w - - 0 1",
        "4k3/8/8/8/8/8/4R3/4K3 w - - 0 1",
        "4k3/QQQQQQQQ/8/8/8/8/8/4K3 w - - 0 1",
    ];

    for fen in accepted {
        let mut position = Position::from_fen(fen).expect("analysis FEN is accepted");
        position
            .validate_invariants()
            .expect("analysis FEN satisfies structural invariants");
        assert_eq!(position.to_fen(), fen);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        let _moves = position
            .legal_moves()
            .expect("analysis legal generation is safe");
        assert_eq!(position.perft(0).expect("depth-zero perft succeeds"), 1);
        assert_eq!(
            Position::from_fen(&position.to_fen()).expect("canonical analysis FEN parses"),
            position
        );
    }
}
