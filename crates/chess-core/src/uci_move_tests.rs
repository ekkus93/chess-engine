use std::panic::{catch_unwind, AssertUnwindSafe};

use crate::{Move, MoveKind, PieceKind, Square};

use super::{MoveParseError, UciMove};

fn square(value: &str) -> Square {
    value.parse().expect("test square is valid")
}

#[test]
fn normal_and_promotion_syntax_round_trip() {
    for value in ["e2e4", "g1f3", "e7e8n", "e7e8b", "e7e8r", "e7e8q"] {
        let parsed: UciMove = value.parse().expect("valid UCI syntax");
        assert_eq!(parsed.to_string(), value);
    }
}

#[test]
fn invalid_syntax_is_rejected_by_category() {
    assert_eq!(
        "".parse::<UciMove>(),
        Err(MoveParseError::InvalidLength { found: 0 })
    );
    assert_eq!(
        "e2e".parse::<UciMove>(),
        Err(MoveParseError::InvalidLength { found: 3 })
    );
    assert_eq!("é2e4".parse::<UciMove>(), Err(MoveParseError::NonAscii));
    assert_eq!(
        "i2e4".parse::<UciMove>(),
        Err(MoveParseError::InvalidSource {
            value: "i2".to_owned(),
        })
    );
    assert_eq!(
        "e2e9".parse::<UciMove>(),
        Err(MoveParseError::InvalidDestination {
            value: "e9".to_owned(),
        })
    );
    assert_eq!(
        "e7e8k".parse::<UciMove>(),
        Err(MoveParseError::InvalidPromotion { value: 'k' })
    );
    assert_eq!(
        "e7e8Q".parse::<UciMove>(),
        Err(MoveParseError::InvalidPromotion { value: 'Q' })
    );
}

#[test]
fn every_internal_move_kind_formats_canonically() {
    let source = square("a7");
    let destination = square("b8");
    for kind in MoveKind::ALL {
        let current = Move::new(source, destination, kind);
        let expected_suffix = match kind.promotion() {
            Some(piece) => piece.fen_char().to_string(),
            None => String::new(),
        };
        assert_eq!(current.to_uci(), format!("a7b8{expected_suffix}"));
    }
}

#[test]
fn parsed_syntax_matches_only_the_same_move_identity() {
    let syntax: UciMove = "a7b8n".parse().expect("promotion syntax");
    assert_eq!(syntax.source(), square("a7"));
    assert_eq!(syntax.destination(), square("b8"));
    assert_eq!(syntax.promotion(), Some(PieceKind::Knight));
    assert!(syntax.matches(Move::new(
        square("a7"),
        square("b8"),
        MoveKind::KnightPromotionCapture,
    )));
    assert!(!syntax.matches(Move::new(
        square("a7"),
        square("b8"),
        MoveKind::QueenPromotionCapture,
    )));
    assert!(!syntax.matches(Move::new(
        square("a7"),
        square("b8"),
        MoveKind::Capture,
    )));
}

#[test]
fn arbitrary_utf8_input_never_panics() {
    let mut state = 0xbb67_ae85_84ca_a73b_u64;
    for length in 0..16 {
        for _ in 0..128 {
            let mut value = String::new();
            for _ in 0..length {
                state = state
                    .wrapping_mul(2_862_933_555_777_941_757)
                    .wrapping_add(3_037_000_493);
                let scalar = u32::try_from((state >> 32) % 0x11_0000)
                    .expect("bounded scalar fits u32");
                value.push(char::from_u32(scalar).unwrap_or('\u{fffd}'));
            }
            assert!(
                catch_unwind(AssertUnwindSafe(|| value.parse::<UciMove>())).is_ok(),
                "parser panicked for {value:?}"
            );
        }
    }
}
