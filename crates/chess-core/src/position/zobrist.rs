use crate::{
    bishop_attacks, king_attacks, knight_attacks, pawn_attacks, rook_attacks, CastlingRights,
    Color, Piece, PieceKind, Square,
};

use super::Position;

const PIECE_SQUARE_KEY_COUNT: u64 = 2 * 6 * 64;
const SIDE_TO_MOVE_KEY_INDEX: u64 = PIECE_SQUARE_KEY_COUNT;
const CASTLING_KEY_START: u64 = SIDE_TO_MOVE_KEY_INDEX + 1;
const EN_PASSANT_KEY_START: u64 = CASTLING_KEY_START + 16;
const ZOBRIST_SEED: u64 = 0x9d39_247e_3377_6d41;
const SPLITMIX_GAMMA: u64 = 0x9e37_79b9_7f4a_7c15;

const PIECE_SQUARE_KEYS: [[[u64; 64]; 6]; 2] = build_piece_square_keys();
const SIDE_TO_MOVE_KEY: u64 = generated_key(SIDE_TO_MOVE_KEY_INDEX);
const CASTLING_KEYS: [u64; 16] = build_castling_keys();
const EN_PASSANT_FILE_KEYS: [u64; 8] = build_en_passant_file_keys();

impl Position {
    /// Version of the deterministic Zobrist key schedule.
    ///
    /// Increment this value whenever the seed, table layout, or canonical
    /// repetition policy changes. Persisted hashes from different versions are
    /// not interchangeable.
    pub const ZOBRIST_VERSION: u32 = 1;

    /// Recomputes the canonical repetition hash from authoritative position state.
    ///
    /// Halfmove and fullmove counters are intentionally excluded. En-passant is
    /// included only when the side to move has at least one legal en-passant
    /// capture, because only then does the target change the legal move set.
    #[must_use]
    pub fn recomputed_zobrist(&self) -> u64 {
        let mut key = castling_state_key(self.castling_rights());
        if self.side_to_move() == Color::Black {
            key ^= side_to_move_key();
        }

        for index in 0..Square::COUNT {
            let square = Square::new(index).expect("board iteration index is valid");
            if let Some(piece) = self.piece_at(square) {
                key ^= piece_square_key(piece, square);
            }
        }

        key ^ self.canonical_en_passant_key()
    }

    pub(super) fn canonical_en_passant_key(&self) -> u64 {
        self.canonical_en_passant_file()
            .map_or(0, |file| EN_PASSANT_FILE_KEYS[file])
    }

    fn canonical_en_passant_file(&self) -> Option<usize> {
        let target = self.en_passant()?;
        if self.piece_at(target).is_some() {
            return None;
        }

        let side = self.side_to_move();
        let source_row = match side {
            Color::White => target.row().checked_add(1)?,
            Color::Black => target.row().checked_sub(1)?,
        };
        let captured = Square::from_row_file(source_row, target.file())?;
        if self.piece_at(captured) != Some(Piece::new(side.opposite(), PieceKind::Pawn)) {
            return None;
        }

        for file_delta in [-1_i8, 1_i8] {
            let source_file = target.file() as i8 + file_delta;
            if !(0_i8..8_i8).contains(&source_file) {
                continue;
            }
            let source = Square::from_row_file(source_row, source_file as u8)
                .expect("en-passant source coordinates were bounds checked");
            if self.piece_at(source) == Some(Piece::new(side, PieceKind::Pawn))
                && !self.king_is_attacked_after_en_passant(source, target, captured, side)
            {
                return Some(target.file() as usize);
            }
        }

        None
    }

    fn king_is_attacked_after_en_passant(
        &self,
        source: Square,
        target: Square,
        captured: Square,
        side: Color,
    ) -> bool {
        let enemy = side.opposite();
        let king = self.king_square(side);
        let mut occupancy = self.all_occupancy();
        occupancy.clear(source);
        occupancy.clear(captured);
        occupancy.set(target);

        let mut enemy_pawns = self.piece_bitboard(enemy, PieceKind::Pawn);
        enemy_pawns.clear(captured);
        let pawn_attackers = pawn_attacks(enemy.opposite(), king) & enemy_pawns;
        let knight_attackers =
            knight_attacks(king) & self.piece_bitboard(enemy, PieceKind::Knight);
        let king_attackers = king_attacks(king) & self.piece_bitboard(enemy, PieceKind::King);
        let diagonal_attackers = bishop_attacks(king, occupancy)
            & (self.piece_bitboard(enemy, PieceKind::Bishop)
                | self.piece_bitboard(enemy, PieceKind::Queen));
        let orthogonal_attackers = rook_attacks(king, occupancy)
            & (self.piece_bitboard(enemy, PieceKind::Rook)
                | self.piece_bitboard(enemy, PieceKind::Queen));

        !(pawn_attackers
            | knight_attackers
            | king_attackers
            | diagonal_attackers
            | orthogonal_attackers)
            .is_empty()
    }
}

pub(super) const fn piece_square_key(piece: Piece, square: Square) -> u64 {
    PIECE_SQUARE_KEYS[piece.color.index()][piece.kind.index()][square.index() as usize]
}

pub(super) const fn side_to_move_key() -> u64 {
    SIDE_TO_MOVE_KEY
}

pub(super) const fn castling_state_key(rights: CastlingRights) -> u64 {
    CASTLING_KEYS[rights.bits() as usize]
}

const fn build_piece_square_keys() -> [[[u64; 64]; 6]; 2] {
    let mut keys = [[[0_u64; 64]; 6]; 2];
    let mut color = 0_usize;
    while color < 2 {
        let mut kind = 0_usize;
        while kind < 6 {
            let mut square = 0_usize;
            while square < 64 {
                let index = (color * 6 * 64 + kind * 64 + square) as u64;
                keys[color][kind][square] = generated_key(index);
                square += 1;
            }
            kind += 1;
        }
        color += 1;
    }
    keys
}

const fn build_castling_keys() -> [u64; 16] {
    let mut keys = [0_u64; 16];
    let mut index = 0_usize;
    while index < 16 {
        keys[index] = generated_key(CASTLING_KEY_START + index as u64);
        index += 1;
    }
    keys
}

const fn build_en_passant_file_keys() -> [u64; 8] {
    let mut keys = [0_u64; 8];
    let mut index = 0_usize;
    while index < 8 {
        keys[index] = generated_key(EN_PASSANT_KEY_START + index as u64);
        index += 1;
    }
    keys
}

const fn generated_key(index: u64) -> u64 {
    mix64(ZOBRIST_SEED.wrapping_add(index.wrapping_mul(SPLITMIX_GAMMA)))
}

const fn mix64(mut value: u64) -> u64 {
    value ^= value >> 30;
    value = value.wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value ^= value >> 27;
    value = value.wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}

#[cfg(test)]
mod tests {
    use crate::{Move, MoveKind, Position};

    fn legal_move(position: &mut Position, uci: &str) -> Move {
        position
            .legal_moves()
            .expect("legal moves")
            .iter()
            .find(|current| current.to_uci() == uci)
            .unwrap_or_else(|| panic!("expected legal move {uci}"))
    }

    fn assert_round_trip_hash(fen: &str, uci: &str, expected_kind: MoveKind) {
        let mut position = Position::from_fen(fen).expect("valid FEN");
        let snapshot = position.clone();
        let current = legal_move(&mut position, uci);
        assert_eq!(current.kind(), expected_kind);

        let undo = position
            .make_generated_legal_move(current)
            .expect("generated move succeeds");
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        position
            .unmake_generated_legal_move(undo)
            .expect("generated unmake succeeds");
        assert_eq!(position, snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn versioned_known_fixture_hashes_are_stable() {
        assert_eq!(Position::ZOBRIST_VERSION, 1);
        let fixtures = [
            (
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                0xd055_9a5a_21f4_beaa,
            ),
            ("7k/8/8/8/8/8/8/K7 w - - 0 1", 0x4d60_8879_69b7_62c1),
            ("7k/8/8/8/8/8/8/K7 b - - 0 1", 0x412b_0f12_cdff_2c33),
        ];

        for (fen, expected) in fixtures {
            let position = Position::from_fen(fen).expect("valid FEN");
            assert_eq!(position.zobrist(), expected, "{fen}");
            assert_eq!(position.recomputed_zobrist(), expected, "{fen}");
        }
    }

    #[test]
    fn clocks_do_not_change_repetition_identity() {
        let first = Position::from_fen("7k/8/8/8/8/8/8/K7 w - - 0 1").expect("valid FEN");
        let second =
            Position::from_fen("7k/8/8/8/8/8/8/K7 w - - 99 65535").expect("valid FEN");
        assert_eq!(first.zobrist(), second.zobrist());
    }

    #[test]
    fn en_passant_identity_requires_a_legal_capture() {
        let legal =
            Position::from_fen("7k/8/8/3pP3/8/8/8/7K w - d6 0 1").expect("valid FEN");
        let legal_without_target =
            Position::from_fen("7k/8/8/3pP3/8/8/8/7K w - - 0 1").expect("valid FEN");
        assert_ne!(legal.zobrist(), legal_without_target.zobrist());
        assert_eq!(legal.zobrist(), 0x5c81_a6d0_8443_f509);

        let non_capturable =
            Position::from_fen("7k/8/8/3p4/8/8/8/7K w - d6 0 1").expect("valid FEN");
        let non_capturable_without_target =
            Position::from_fen("7k/8/8/3p4/8/8/8/7K w - - 0 1").expect("valid FEN");
        assert_eq!(
            non_capturable.zobrist(),
            non_capturable_without_target.zobrist()
        );

        let pinned =
            Position::from_fen("4r2k/8/8/3pP3/8/8/8/4K3 w - d6 0 1").expect("valid FEN");
        let pinned_without_target =
            Position::from_fen("4r2k/8/8/3pP3/8/8/8/4K3 w - - 0 1").expect("valid FEN");
        assert_eq!(pinned.zobrist(), pinned_without_target.zobrist());
        assert_eq!(pinned.zobrist(), 0x9846_f032_6179_b115);
    }

    #[test]
    fn every_move_category_updates_and_restores_hash_exactly() {
        let start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
        let fixtures = [
            (start, "g1f3", MoveKind::Quiet),
            (start, "e2e4", MoveKind::DoublePawnPush),
            ("7k/8/8/8/4p3/3P4/8/7K w - - 0 1", "d3e4", MoveKind::Capture),
            (
                "7k/8/8/3pP3/8/8/8/7K w - d6 0 1",
                "e5d6",
                MoveKind::EnPassant,
            ),
            (
                "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                "e1g1",
                MoveKind::KingCastle,
            ),
            (
                "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                "e1c1",
                MoveKind::QueenCastle,
            ),
            (
                "7k/P7/8/8/8/8/8/7K w - - 0 1",
                "a7a8q",
                MoveKind::QueenPromotion,
            ),
            (
                "1r5k/P7/8/8/8/8/8/7K w - - 0 1",
                "a7b8n",
                MoveKind::KnightPromotionCapture,
            ),
            ("r3k3/8/8/8/8/8/8/R6K w q - 0 1", "a1a8", MoveKind::Capture),
        ];

        for (fen, uci, kind) in fixtures {
            assert_round_trip_hash(fen, uci, kind);
        }
    }

    #[derive(Clone, Copy)]
    struct DeterministicRng(u64);

    impl DeterministicRng {
        fn next(&mut self) -> u64 {
            self.0 = self
                .0
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            self.0
        }
    }

    #[test]
    fn randomized_incremental_hashes_match_recomputation() {
        for seed in [2, 7, 19, 43] {
            let mut position = Position::starting();
            let baseline = position.clone();
            let mut rng = DeterministicRng(seed);
            let mut history = Vec::new();

            for _ in 0..96 {
                let moves = position.legal_moves().expect("legal moves");
                if moves.is_empty() {
                    break;
                }
                let index = (rng.next() % moves.len() as u64) as usize;
                let current = moves
                    .iter()
                    .nth(index)
                    .expect("selected move index is in range");
                let undo = position
                    .make_generated_legal_move(current)
                    .expect("generated move succeeds");
                assert_eq!(
                    position.zobrist(),
                    position.recomputed_zobrist(),
                    "seed {seed}, move {}",
                    current.to_uci()
                );
                history.push(undo);
            }

            while let Some(undo) = history.pop() {
                position
                    .unmake_generated_legal_move(undo)
                    .expect("reverse move succeeds");
                assert_eq!(position.zobrist(), position.recomputed_zobrist());
            }
            assert_eq!(position, baseline, "seed {seed} did not restore");
        }
    }
}
