use crate::{Game, GameError, GameStatus, LegalMoveError, Move, MoveKind, PieceKind};

/// Formats one exact legal move in Standard Algebraic Notation without mutating `game`.
///
/// SAN is chess-rule notation and therefore belongs in `chess-core`, not in a
/// presentation adapter. The caller supplies the exact packed move identity so
/// promotion, castling, and en-passant semantics cannot be guessed from text.
pub fn move_to_san(game: &Game, current: Move) -> Result<String, GameError> {
    let mut source = game.clone();
    let legal_moves = source.legal_moves()?;
    if !legal_moves.iter().any(|candidate| candidate == current) {
        return Err(GameError::Rules(LegalMoveError::IllegalMove { current }));
    }

    let moving_piece = source
        .position()
        .piece_at(current.source())
        .expect("an exact legal move always has a source piece");

    let mut san = match current.kind() {
        MoveKind::KingCastle => "O-O".to_owned(),
        MoveKind::QueenCastle => "O-O-O".to_owned(),
        _ => {
            let mut value = String::new();
            if moving_piece.kind == PieceKind::Pawn {
                if current.kind().is_capture() {
                    value.push(current.source().file_char());
                }
            } else {
                value.push(piece_letter(moving_piece.kind));
                append_disambiguation(
                    &mut value,
                    &source,
                    &legal_moves,
                    current,
                    moving_piece.kind,
                );
            }

            if current.kind().is_capture() {
                value.push('x');
            }
            value.push_str(&current.destination().to_string());
            if let Some(promotion) = current.promotion() {
                value.push('=');
                value.push(piece_letter(promotion));
            }
            value
        }
    };

    let mut after = source;
    after.make_move(current)?;
    match after.status()? {
        GameStatus::Checkmate { .. } => san.push('#'),
        _ if after
            .position()
            .is_in_check(after.position().side_to_move()) =>
        {
            san.push('+');
        }
        _ => {}
    }
    Ok(san)
}

/// Formats a chronological move sequence rooted at the standard starting position.
///
/// This helper is intentionally explicit about its root. Android games currently
/// start from the standard position; callers with another root must replay from
/// their own [`Game`] and call [`move_to_san`] per move instead of guessing.
pub fn san_history_from_start(moves: &[Move]) -> Result<Vec<String>, GameError> {
    let mut replay = Game::starting();
    let mut san = Vec::with_capacity(moves.len());
    for &current in moves {
        san.push(move_to_san(&replay, current)?);
        replay.make_move(current)?;
    }
    Ok(san)
}

fn append_disambiguation(
    output: &mut String,
    source: &Game,
    legal_moves: &crate::MoveList,
    current: Move,
    piece_kind: PieceKind,
) {
    let conflicts = legal_moves.iter().filter(|candidate| {
        *candidate != current
            && candidate.destination() == current.destination()
            && source
                .position()
                .piece_at(candidate.source())
                .is_some_and(|piece| piece.kind == piece_kind)
    });

    let mut has_conflict = false;
    let mut same_file = false;
    let mut same_rank = false;
    for candidate in conflicts {
        has_conflict = true;
        same_file |= candidate.source().file() == current.source().file();
        same_rank |= candidate.source().rank() == current.source().rank();
    }
    if !has_conflict {
        return;
    }

    if !same_file {
        output.push(current.source().file_char());
    } else if !same_rank {
        output.push(char::from(b'0' + current.source().rank()));
    } else {
        output.push(current.source().file_char());
        output.push(char::from(b'0' + current.source().rank()));
    }
}

const fn piece_letter(kind: PieceKind) -> char {
    match kind {
        PieceKind::Pawn => 'P',
        PieceKind::Knight => 'N',
        PieceKind::Bishop => 'B',
        PieceKind::Rook => 'R',
        PieceKind::Queen => 'Q',
        PieceKind::King => 'K',
    }
}

#[cfg(test)]
mod tests {
    use crate::{Game, Move, Position, UciMove};

    use super::{move_to_san, san_history_from_start};

    fn game(fen: &str) -> Game {
        Game::new(fen.parse::<Position>().expect("test FEN is valid"))
    }

    fn resolve(game: &Game, text: &str) -> Move {
        let syntax = text.parse::<UciMove>().expect("test UCI is valid");
        let mut copy = game.clone();
        copy.legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal")
    }

    fn play(game: &mut Game, text: &str) {
        let current = resolve(game, text);
        game.make_move(current).expect("test move applies");
    }

    #[test]
    fn pawn_and_piece_quiet_moves_use_standard_notation() {
        let mut game = Game::starting();
        let e4 = resolve(&game, "e2e4");
        assert_eq!(move_to_san(&game, e4).expect("SAN"), "e4");
        game.make_move(e4).expect("e4 applies");
        play(&mut game, "a7a6");
        let knight = resolve(&game, "g1f3");
        assert_eq!(move_to_san(&game, knight).expect("SAN"), "Nf3");
    }

    #[test]
    fn pawn_capture_and_en_passant_use_capture_notation() {
        let capture = game("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1");
        let en_passant = resolve(&capture, "e5d6");
        assert_eq!(move_to_san(&capture, en_passant).expect("SAN"), "exd6");

        let ordinary = game("4k3/8/3p4/4P3/8/8/8/4K3 w - - 0 1");
        let pawn_capture = resolve(&ordinary, "e5d6");
        assert_eq!(move_to_san(&ordinary, pawn_capture).expect("SAN"), "exd6");
    }

    #[test]
    fn same_piece_file_disambiguation_is_emitted() {
        let game = game("4k3/8/8/8/8/2N1N3/8/4K3 w - - 0 1");
        let current = resolve(&game, "c3d5");
        assert_eq!(move_to_san(&game, current).expect("SAN"), "Ncd5");
    }

    #[test]
    fn same_piece_rank_disambiguation_is_emitted() {
        let game = game("4k3/8/8/8/8/R7/8/R3K3 w - - 0 1");
        let current = resolve(&game, "a1a2");
        assert_eq!(move_to_san(&game, current).expect("SAN"), "R1a2");
    }

    #[test]
    fn full_square_disambiguation_is_emitted_when_required() {
        let game = game("4k3/8/8/8/8/Q7/8/Q1Q1K3 w - - 0 1");
        let current = resolve(&game, "a1b2");
        assert_eq!(move_to_san(&game, current).expect("SAN"), "Qa1b2");
    }

    #[test]
    fn castling_uses_letter_o_not_zero() {
        let king_side = game("4k2r/8/8/8/8/8/8/4K2R w Kk - 0 1");
        let current = resolve(&king_side, "e1g1");
        assert_eq!(move_to_san(&king_side, current).expect("SAN"), "O-O");

        let queen_side = game("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 1");
        let current = resolve(&queen_side, "e1c1");
        assert_eq!(move_to_san(&queen_side, current).expect("SAN"), "O-O-O");
    }

    #[test]
    fn check_and_checkmate_suffixes_are_authoritative() {
        let check = game("4k3/8/8/8/8/8/4Q3/4K3 w - - 0 1");
        let current = resolve(&check, "e2e7");
        assert_eq!(move_to_san(&check, current).expect("SAN"), "Qe7+");

        let mate = game("7k/8/5KQ1/8/8/8/8/8 w - - 0 1");
        let current = resolve(&mate, "g6g7");
        assert_eq!(move_to_san(&mate, current).expect("SAN"), "Qg7#");
    }

    #[test]
    fn promotion_is_explicit_and_can_carry_check() {
        let quiet = game("8/4P3/k7/8/8/8/8/4K3 w - - 0 1");
        let current = resolve(&quiet, "e7e8q");
        assert_eq!(move_to_san(&quiet, current).expect("SAN"), "e8=Q");

        let check = game("k7/4P3/8/8/8/8/8/4K3 w - - 0 1");
        let current = resolve(&check, "e7e8q");
        assert_eq!(move_to_san(&check, current).expect("SAN"), "e8=Q+");
    }

    #[test]
    fn history_replays_from_standard_root_without_mutating_source() {
        let mut game = Game::starting();
        for current in ["e2e4", "c7c5", "g1f3"] {
            play(&mut game, current);
        }
        let before = game.clone();
        assert_eq!(
            san_history_from_start(game.moves()).expect("SAN history"),
            vec!["e4", "c5", "Nf3"]
        );
        assert_eq!(game, before);
    }
}
