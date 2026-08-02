from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected one replacement target, found {count}: {old[:120]!r}"
        )
    write(path, text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + addition.strip() + "\n")


legal = "crates/chess-core/src/position/legal.rs"
replace_once(
    legal,
    "use crate::{Color, Move, MoveKind, MoveList, MoveListOverflow, PositionMutationError, Square};\n\nuse super::Position;",
    "use crate::{\n    CastlingRights, Color, FullmoveNumber, HalfmoveClock, Move, MoveKind, MoveList,\n    MoveListOverflow, PositionMutationError, Square, MAX_PSEUDO_LEGAL_MOVES,\n};\n\nuse super::{Position, PositionUndo};",
)
replace_once(
    legal,
    "    /// A caller requested a move that is not one of the exact legal identities.\n    IllegalMove { current: Move },\n    /// A generated move contradicted its encoded semantic identity.",
    "    /// A caller requested a move that is not one of the exact legal identities.\n    IllegalMove { current: Move },\n    /// A legal-move token was generated for a different source position.\n    LegalMoveTokenMismatch { current: Move },\n    /// A generated move contradicted its encoded semantic identity.",
)
replace_once(
    legal,
    "            Self::IllegalMove { current } => {\n                write!(formatter, \"move {} is not legal\", current.to_uci())\n            }\n            Self::InvalidGeneratedMove { current } => write!(",
    "            Self::IllegalMove { current } => {\n                write!(formatter, \"move {} is not legal\", current.to_uci())\n            }\n            Self::LegalMoveTokenMismatch { current } => write!(\n                formatter,\n                \"legal-move token for {} does not match the current position\",\n                current.to_uci()\n            ),\n            Self::InvalidGeneratedMove { current } => write!(",
)

token_types = r'''
/// Opaque proof that one move was legal in one exact source position.
///
/// Tokens are created only by [`Position::legal_move_tokens`]. They bind the
/// packed move identity to the complete non-board metadata and canonical hash
/// of the source position, allowing search to apply generated legal moves
/// without regenerating the legal move list.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct LegalMoveToken {
    current: Move,
    origin: LegalMoveOrigin,
}

impl LegalMoveToken {
    /// Returns the exact packed move represented by this token.
    #[must_use]
    pub const fn move_made(self) -> Move {
        self.current
    }
}

/// Bounded stack-backed storage for legal-move tokens.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LegalMoveTokenList {
    tokens: [Option<LegalMoveToken>; MAX_PSEUDO_LEGAL_MOVES],
    len: usize,
}

impl LegalMoveTokenList {
    const fn new() -> Self {
        Self {
            tokens: [None; MAX_PSEUDO_LEGAL_MOVES],
            len: 0,
        }
    }

    /// Returns the number of generated legal-move tokens.
    #[must_use]
    pub const fn len(&self) -> usize {
        self.len
    }

    /// Returns whether no legal-move token was generated.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns the token at `index`.
    #[must_use]
    pub fn get(&self, index: usize) -> Option<LegalMoveToken> {
        self.tokens.get(index).copied().flatten()
    }

    /// Iterates in deterministic legal move generation order.
    pub fn iter(&self) -> impl ExactSizeIterator<Item = LegalMoveToken> + '_ {
        self.tokens[..self.len]
            .iter()
            .copied()
            .map(|entry| entry.expect("occupied legal-token prefix contains tokens"))
    }

    fn push(&mut self, token: LegalMoveToken) {
        debug_assert!(self.len < MAX_PSEUDO_LEGAL_MOVES);
        self.tokens[self.len] = Some(token);
        self.len += 1;
    }
}

impl Default for LegalMoveTokenList {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct LegalMoveOrigin {
    zobrist: u64,
    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant: Option<Square>,
    halfmove_clock: HalfmoveClock,
    fullmove_number: FullmoveNumber,
}

impl LegalMoveOrigin {
    const fn from_position(position: &Position) -> Self {
        Self {
            zobrist: position.zobrist(),
            side_to_move: position.side_to_move(),
            castling_rights: position.castling_rights(),
            en_passant: position.en_passant(),
            halfmove_clock: position.halfmove_clock(),
            fullmove_number: position.fullmove_number(),
        }
    }

    const fn matches(self, position: &Position) -> bool {
        self.zobrist == position.zobrist()
            && self.side_to_move == position.side_to_move()
            && self.castling_rights.bits() == position.castling_rights().bits()
            && self.en_passant == position.en_passant()
            && self.halfmove_clock.get() == position.halfmove_clock().get()
            && self.fullmove_number.get() == position.fullmove_number().get()
    }
}
'''
replace_once(
    legal,
    "impl Position {\n    /// Generates every legal move",
    token_types + "\nimpl Position {\n    /// Generates every legal move",
)

token_methods = r'''
    /// Generates opaque tokens for every legal move in the current position.
    ///
    /// The position is restored exactly before return. Each token records the
    /// source position identity and can later be passed to
    /// [`Position::make_legal_token`] without regenerating the legal move list.
    pub fn legal_move_tokens(&mut self) -> Result<LegalMoveTokenList, LegalMoveError> {
        let origin = LegalMoveOrigin::from_position(self);
        let moves = self.legal_moves()?;
        debug_assert!(origin.matches(self));
        let mut tokens = LegalMoveTokenList::new();
        for current in moves.iter() {
            tokens.push(LegalMoveToken { current, origin });
        }
        Ok(tokens)
    }

    /// Applies one token generated for the exact current position.
    ///
    /// Origin mismatch is rejected before mutation. A valid token uses the
    /// existing generated-legal reversible path and therefore does not
    /// regenerate legal moves.
    pub fn make_legal_token(
        &mut self,
        token: LegalMoveToken,
    ) -> Result<PositionUndo, LegalMoveError> {
        if !token.origin.matches(self) {
            return Err(LegalMoveError::LegalMoveTokenMismatch {
                current: token.current,
            });
        }
        self.make_generated_legal_move(token.current)
    }

'''
replace_once(
    legal,
    "    /// Returns whether `candidate` is one of the exact generated legal moves.\n",
    token_methods + "    /// Returns whether `candidate` is one of the exact generated legal moves.\n",
)

replace_once(
    "crates/chess-core/src/position/mod.rs",
    "pub use legal::LegalMoveError;",
    "pub use legal::{LegalMoveError, LegalMoveToken, LegalMoveTokenList};",
)
replace_once(
    "crates/chess-core/src/lib.rs",
    "mod game;\nmod move_encoding;",
    "mod game;\nmod game_reset;\nmod move_encoding;",
)
replace_once(
    "crates/chess-core/src/lib.rs",
    "    FenError, LegalMoveError, Position, PositionBuildError, PositionInvariantError, PositionUndo,\n",
    "    FenError, LegalMoveError, LegalMoveToken, LegalMoveTokenList, Position, PositionBuildError,\n    PositionInvariantError, PositionUndo,\n",
)

Path("crates/chess-core/src/game_reset.rs").write_text(
    r'''use crate::{Game, Position};

impl Game {
    /// Replaces this game with the standard starting position and fresh history.
    pub fn reset_to_starting(&mut self) {
        *self = Self::starting();
    }

    /// Replaces this game root and discards all prior move and repetition history.
    ///
    /// `Position` is already validated, so replacement is infallible. The new
    /// hash history contains exactly the supplied root position.
    pub fn set_position(&mut self, position: Position) {
        *self = Self::new(position);
    }
}

#[cfg(test)]
mod tests {
    use crate::{Color, Game, GameError, GameStatus, Position, UciMove};

    fn play(game: &mut Game, text: &str) -> crate::GameUndo {
        let syntax = text.parse::<UciMove>().expect("test UCI syntax is valid");
        let current = game
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal");
        game.make_move(current).expect("test move is playable")
    }

    #[test]
    fn reset_to_starting_discards_position_and_history() {
        let mut game = Game::starting();
        let stale = play(&mut game, "e2e4");
        let _reply = play(&mut game, "e7e5");

        game.reset_to_starting();

        assert_eq!(game, Game::starting());
        assert_eq!(game.ply_count(), 0);
        assert_eq!(game.position_hashes(), &[Position::starting().zobrist()]);
        assert!(matches!(
            game.unmake_move(stale),
            Err(GameError::HistoryStateMismatch { .. })
        ));
    }

    #[test]
    fn set_position_establishes_one_new_root() {
        let mut game = Game::starting();
        let stale = play(&mut game, "g1f3");
        let mate = Position::from_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
            .expect("mate FEN is valid");
        let expected_hash = mate.zobrist();

        game.set_position(mate);

        assert_eq!(game.ply_count(), 0);
        assert!(game.moves().is_empty());
        assert_eq!(game.position_hashes(), &[expected_hash]);
        assert_eq!(
            game.status(),
            Ok(GameStatus::Checkmate {
                winner: Color::White
            })
        );
        let history = game.search_history();
        assert_eq!(history.root_len(), 1);
        assert_eq!(history.line_len(), 0);
        assert_eq!(history.current_zobrist(), Some(expected_hash));
        assert!(matches!(
            game.unmake_move(stale),
            Err(GameError::HistoryStateMismatch { .. })
        ));
    }
}
''',
    encoding="utf-8",
)

append_once(
    "crates/chess-core/src/position/legal_tests.rs",
    "fn legal_move_tokens_bind_move_and_source_position()",
    r'''
#[test]
fn legal_move_tokens_bind_move_and_source_position() {
    for fen in [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
    ] {
        let mut position = Position::from_fen(fen).expect("token fixture is valid");
        let moves: Vec<_> = position
            .legal_moves()
            .expect("legal moves")
            .iter()
            .collect();
        let tokens = position.legal_move_tokens().expect("legal tokens");
        assert_eq!(tokens.len(), moves.len());
        assert_eq!(
            tokens.iter().map(|token| token.move_made()).collect::<Vec<_>>(),
            moves
        );
    }
}

#[test]
fn legal_move_tokens_apply_unmake_and_reject_stale_origins() {
    let mut position = Position::starting();
    let root = position.clone();
    let tokens = position.legal_move_tokens().expect("legal tokens");
    let e2e4 = tokens
        .iter()
        .find(|token| token.move_made().to_uci() == "e2e4")
        .expect("e2e4 token");
    let g1f3 = tokens
        .iter()
        .find(|token| token.move_made().to_uci() == "g1f3")
        .expect("g1f3 token");

    let undo = position.make_legal_token(e2e4).expect("token applies");
    position.validate_invariants().expect("child invariants");
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    let child = position.clone();
    assert_eq!(
        position.make_legal_token(g1f3),
        Err(LegalMoveError::LegalMoveTokenMismatch {
            current: g1f3.move_made()
        })
    );
    assert_eq!(position, child);
    position.unmake_move(undo).expect("token move unmakes");
    assert_eq!(position, root);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());

    let mut different_side = Position::from_fen(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    )
    .expect("different-side FEN is valid");
    let snapshot = different_side.clone();
    assert_eq!(
        different_side.make_legal_token(e2e4),
        Err(LegalMoveError::LegalMoveTokenMismatch {
            current: e2e4.move_made()
        })
    );
    assert_eq!(different_side, snapshot);
}

#[test]
fn every_curated_legal_token_restores_exactly() {
    for fen in [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "7k/8/8/3pP3/8/8/8/7K w - d6 0 1",
        "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
    ] {
        let mut position = Position::from_fen(fen).expect("curated token FEN is valid");
        let snapshot = position.clone();
        let tokens = position.legal_move_tokens().expect("legal tokens");
        for token in tokens.iter() {
            let undo = position.make_legal_token(token).expect("token applies");
            position.validate_invariants().expect("child invariants");
            assert_eq!(position.zobrist(), position.recomputed_zobrist());
            position.unmake_move(undo).expect("token unmake succeeds");
            assert_eq!(position, snapshot, "{} in {fen}", token.move_made());
            assert_eq!(position.zobrist(), position.recomputed_zobrist());
        }
    }
}
''',
)

append_once(
    "crates/chess-search/src/lib.rs",
    "fn public_legal_token_api_supports_search_crate_make_unmake()",
    r'''
#[cfg(test)]
mod core_api_tests {
    use chess_core::Position;

    use crate::evaluate;

    #[test]
    fn public_legal_token_api_supports_search_crate_make_unmake() {
        let mut position = Position::starting();
        let snapshot = position.clone();
        let token = position
            .legal_move_tokens()
            .expect("legal tokens")
            .iter()
            .find(|token| token.move_made().to_uci() == "e2e4")
            .expect("e2e4 token");

        let undo = position.make_legal_token(token).expect("token applies");
        let _child_score = evaluate(&position);
        position.unmake_move(undo).expect("token move unmakes");

        assert_eq!(position, snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }
}
''',
)

append_once(
    "crates/chess-core/src/position/fen_tests.rs",
    "fn analysis_position_policy_is_explicit_and_safe()",
    r'''
#[test]
fn analysis_position_policy_is_explicit_and_safe() {
    let accepted = [
        "4k3/8/8/8/8/8/8/4K3 w K - 0 1",
        "4k3/8/8/8/8/8/8/3K3 w K - 0 1",
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
        let _moves = position.legal_moves().expect("analysis legal generation is safe");
        assert_eq!(position.perft(0).expect("depth-zero perft succeeds"), 1);
        assert_eq!(
            Position::from_fen(&position.to_fen()).expect("canonical analysis FEN parses"),
            position
        );
    }
}
''',
)
