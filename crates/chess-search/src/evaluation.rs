use chess_core::{
    bishop_attacks, king_attacks, knight_attacks, pawn_attacks, queen_attacks, rook_attacks,
    Bitboard, Color, PieceKind, Position, Square,
};

use crate::{EvaluationWeights, PhasedWeight, Score};

const MAX_PHASE: u8 = 24;
const FILE_B_TO_G: u64 = 0x7e7e_7e7e_7e7e_7e7e;
const WHITE_SPACE_HALF: u64 = 0x0000_0000_ffff_ffff;
const BLACK_SPACE_HALF: u64 = 0xffff_ffff_0000_0000;

/// Coarse evaluator groups exposed for deterministic microbenchmarks.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EvaluationTerm {
    /// Material and piece-square tables.
    MaterialAndPieceSquare,
    /// Pawn-structure terms.
    PawnStructure,
    /// Mobility, bishop pair, and rook activity.
    MobilityAndActivity,
    /// King safety, space, and endgame king activity.
    KingAndSpace,
    /// Complete static evaluation.
    Full,
}

impl EvaluationTerm {
    /// Every benchmarkable evaluator group in stable order.
    pub const ALL: [Self; 5] = [
        Self::MaterialAndPieceSquare,
        Self::PawnStructure,
        Self::MobilityAndActivity,
        Self::KingAndSpace,
        Self::Full,
    ];

    /// Stable machine-readable term name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::MaterialAndPieceSquare => "material_psqt",
            Self::PawnStructure => "pawn_structure",
            Self::MobilityAndActivity => "mobility_activity",
            Self::KingAndSpace => "king_space",
            Self::Full => "full",
        }
    }
}

/// Fixed, allocation-free named evaluation breakdown.
///
/// Every component and `total` use the public side-to-move score convention.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct EvaluationTrace {
    /// Remaining middlegame phase in the inclusive range zero through 24.
    pub phase: u8,
    /// Material contribution.
    pub material: i32,
    /// Piece-square contribution.
    pub piece_square: i32,
    /// Mobility contribution.
    pub mobility: i32,
    /// Isolated-pawn contribution.
    pub isolated_pawns: i32,
    /// Doubled-pawn contribution.
    pub doubled_pawns: i32,
    /// Passed-pawn contribution.
    pub passed_pawns: i32,
    /// Connected-pawn contribution.
    pub connected_pawns: i32,
    /// Bishop-pair contribution.
    pub bishop_pair: i32,
    /// Open and semi-open rook-file contribution.
    pub rook_files: i32,
    /// Seventh-rank rook contribution.
    pub rook_seventh: i32,
    /// Pawn-shield contribution.
    pub king_shield: i32,
    /// Enemy pressure around the king.
    pub king_zone_attack: i32,
    /// Controlled enemy-space contribution.
    pub space: i32,
    /// Endgame king-activity contribution.
    pub king_activity: i32,
    /// Exact sum of every named component.
    pub total: i32,
}

impl EvaluationTrace {
    /// Returns the exact sum of all named score components.
    #[must_use]
    pub const fn component_sum(self) -> i32 {
        self.material
            + self.piece_square
            + self.mobility
            + self.isolated_pawns
            + self.doubled_pawns
            + self.passed_pawns
            + self.connected_pawns
            + self.bishop_pair
            + self.rook_files
            + self.rook_seventh
            + self.king_shield
            + self.king_zone_attack
            + self.space
            + self.king_activity
    }
}

/// Evaluates `position` with the explicit built-in baseline weights.
#[must_use]
pub fn evaluate(position: &Position) -> Score {
    evaluate_with_weights(position, &EvaluationWeights::DEFAULT)
}

/// Evaluates `position` with caller-supplied weights.
#[must_use]
pub fn evaluate_with_weights(position: &Position, weights: &EvaluationWeights) -> Score {
    Score::from_evaluation(raw_evaluation(position, weights).to_trace(position.side_to_move()).total)
}

/// Returns the allocation-free named trace for the baseline weights.
#[must_use]
pub fn evaluate_trace(position: &Position) -> EvaluationTrace {
    evaluate_trace_with_weights(position, &EvaluationWeights::DEFAULT)
}

/// Returns the allocation-free named trace for caller-supplied weights.
#[must_use]
pub fn evaluate_trace_with_weights(
    position: &Position,
    weights: &EvaluationWeights,
) -> EvaluationTrace {
    raw_evaluation(position, weights).to_trace(position.side_to_move())
}

/// Evaluates one coarse group for deterministic benchmarking.
#[must_use]
pub fn evaluate_term(
    position: &Position,
    weights: &EvaluationWeights,
    term: EvaluationTerm,
) -> Score {
    if term == EvaluationTerm::Full {
        return evaluate_with_weights(position, weights);
    }
    let phase = game_phase(position);
    let white_score = match term {
        EvaluationTerm::MaterialAndPieceSquare => {
            let mut raw = RawEvaluation::default();
            evaluate_material_and_piece_square(position, weights, &mut raw);
            raw.material.blend(phase) + raw.piece_square.blend(phase)
        }
        EvaluationTerm::PawnStructure => {
            let mut raw = RawEvaluation::default();
            evaluate_pawns(position, weights, &mut raw);
            raw.isolated_pawns.blend(phase)
                + raw.doubled_pawns.blend(phase)
                + raw.passed_pawns.blend(phase)
                + raw.connected_pawns.blend(phase)
        }
        EvaluationTerm::MobilityAndActivity => {
            let mut raw = RawEvaluation::default();
            evaluate_mobility_and_activity(position, weights, &mut raw);
            raw.mobility.blend(phase)
                + raw.bishop_pair.blend(phase)
                + raw.rook_files.blend(phase)
                + raw.rook_seventh.blend(phase)
        }
        EvaluationTerm::KingAndSpace => {
            let mut raw = RawEvaluation::default();
            evaluate_king_and_space(position, weights, &mut raw);
            raw.king_shield.blend(phase)
                + raw.king_zone_attack.blend(phase)
                + raw.space.blend(phase)
                + raw.king_activity.blend(phase)
        }
        EvaluationTerm::Full => unreachable!("full evaluation returned before term dispatch"),
    };
    Score::from_evaluation(oriented(white_score, position.side_to_move()))
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct TaperedScore {
    middlegame: i32,
    endgame: i32,
}

impl TaperedScore {
    fn add(&mut self, weight: PhasedWeight, factor: i32) {
        self.middlegame += i32::from(weight.middlegame) * factor;
        self.endgame += i32::from(weight.endgame) * factor;
    }

    fn blend(self, phase: u8) -> i32 {
        let middlegame = i32::from(phase);
        let endgame = i32::from(MAX_PHASE - phase);
        (self.middlegame * middlegame + self.endgame * endgame) / i32::from(MAX_PHASE)
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct RawEvaluation {
    phase: u8,
    material: TaperedScore,
    piece_square: TaperedScore,
    mobility: TaperedScore,
    isolated_pawns: TaperedScore,
    doubled_pawns: TaperedScore,
    passed_pawns: TaperedScore,
    connected_pawns: TaperedScore,
    bishop_pair: TaperedScore,
    rook_files: TaperedScore,
    rook_seventh: TaperedScore,
    king_shield: TaperedScore,
    king_zone_attack: TaperedScore,
    space: TaperedScore,
    king_activity: TaperedScore,
}

impl RawEvaluation {
    fn to_trace(self, side_to_move: Color) -> EvaluationTrace {
        let phase = self.phase;
        let mut trace = EvaluationTrace {
            phase,
            material: oriented(self.material.blend(phase), side_to_move),
            piece_square: oriented(self.piece_square.blend(phase), side_to_move),
            mobility: oriented(self.mobility.blend(phase), side_to_move),
            isolated_pawns: oriented(self.isolated_pawns.blend(phase), side_to_move),
            doubled_pawns: oriented(self.doubled_pawns.blend(phase), side_to_move),
            passed_pawns: oriented(self.passed_pawns.blend(phase), side_to_move),
            connected_pawns: oriented(self.connected_pawns.blend(phase), side_to_move),
            bishop_pair: oriented(self.bishop_pair.blend(phase), side_to_move),
            rook_files: oriented(self.rook_files.blend(phase), side_to_move),
            rook_seventh: oriented(self.rook_seventh.blend(phase), side_to_move),
            king_shield: oriented(self.king_shield.blend(phase), side_to_move),
            king_zone_attack: oriented(self.king_zone_attack.blend(phase), side_to_move),
            space: oriented(self.space.blend(phase), side_to_move),
            king_activity: oriented(self.king_activity.blend(phase), side_to_move),
            total: 0,
        };
        trace.total = trace.component_sum();
        trace
    }
}

fn raw_evaluation(position: &Position, weights: &EvaluationWeights) -> RawEvaluation {
    let mut raw = RawEvaluation {
        phase: game_phase(position),
        ..RawEvaluation::default()
    };
    evaluate_material_and_piece_square(position, weights, &mut raw);
    evaluate_pawns(position, weights, &mut raw);
    evaluate_mobility_and_activity(position, weights, &mut raw);
    evaluate_king_and_space(position, weights, &mut raw);
    raw
}

fn evaluate_material_and_piece_square(
    position: &Position,
    weights: &EvaluationWeights,
    raw: &mut RawEvaluation,
) {
    for index in 0..Square::COUNT {
        let square = Square::new(index).expect("board iteration index is valid");
        let Some(piece) = position.piece_at(square) else {
            continue;
        };
        let sign = color_sign(piece.color);
        raw.material.add(weights.material[piece.kind.index()], sign);
        raw.piece_square.add(
            weights.piece_square[piece.kind.index()][relative_square_index(piece.color, square)],
            sign,
        );
    }
}

fn evaluate_pawns(position: &Position, weights: &EvaluationWeights, raw: &mut RawEvaluation) {
    for color in [Color::White, Color::Black] {
        let sign = color_sign(color);
        let pawns = position.piece_bitboard(color, PieceKind::Pawn);
        let enemy_pawns = position.piece_bitboard(color.opposite(), PieceKind::Pawn);
        let file_counts = pawn_file_counts(pawns);
        for count in file_counts {
            if count > 1 {
                raw.doubled_pawns
                    .add(weights.doubled_pawn, sign * i32::from(count - 1));
            }
        }
        for square in pawns {
            let file = usize::from(square.file());
            let isolated = (file == 0 || file_counts[file - 1] == 0)
                && (file == 7 || file_counts[file + 1] == 0);
            if isolated {
                raw.isolated_pawns.add(weights.isolated_pawn, sign);
            }
            let advancement = pawn_advancement(color, square);
            if is_passed_pawn(color, square, enemy_pawns) {
                raw.passed_pawns
                    .add(weights.passed_pawn, sign * (1 + advancement));
            }
            if is_connected_pawn(square, pawns) {
                raw.connected_pawns
                    .add(weights.connected_pawn, sign * (1 + advancement / 2));
            }
        }
    }
}

fn evaluate_mobility_and_activity(
    position: &Position,
    weights: &EvaluationWeights,
    raw: &mut RawEvaluation,
) {
    for color in [Color::White, Color::Black] {
        let sign = color_sign(color);
        let own_occupancy = position.occupancy(color);
        for kind in [
            PieceKind::Knight,
            PieceKind::Bishop,
            PieceKind::Rook,
            PieceKind::Queen,
        ] {
            for square in position.piece_bitboard(color, kind) {
                let mobility = mobility_attacks(position, kind, square) & !own_occupancy;
                raw.mobility.add(
                    weights.mobility[kind.index()],
                    sign * i32::try_from(mobility.count()).expect("mobility count fits i32"),
                );
            }
        }
        if position.piece_bitboard(color, PieceKind::Bishop).count() >= 2 {
            raw.bishop_pair.add(weights.bishop_pair, sign);
        }
        let friendly_pawns = position.piece_bitboard(color, PieceKind::Pawn);
        let enemy_pawns = position.piece_bitboard(color.opposite(), PieceKind::Pawn);
        for square in position.piece_bitboard(color, PieceKind::Rook) {
            let file = file_mask(square.file());
            let friendly_on_file = !(friendly_pawns & file).is_empty();
            let enemy_on_file = !(enemy_pawns & file).is_empty();
            if !friendly_on_file && !enemy_on_file {
                raw.rook_files.add(weights.rook_open_file, sign);
            } else if !friendly_on_file {
                raw.rook_files.add(weights.rook_semi_open_file, sign);
            }
            let seventh_row = match color {
                Color::White => 1,
                Color::Black => 6,
            };
            if square.row() == seventh_row {
                raw.rook_seventh.add(weights.rook_seventh_rank, sign);
            }
        }
    }
}

fn evaluate_king_and_space(
    position: &Position,
    weights: &EvaluationWeights,
    raw: &mut RawEvaluation,
) {
    let attacks = [
        attacks_by_color(position, Color::White),
        attacks_by_color(position, Color::Black),
    ];
    for color in [Color::White, Color::Black] {
        let sign = color_sign(color);
        let king = position.king_square(color);
        raw.king_shield.add(
            weights.king_shield,
            sign * i32::from(king_shield_count(position, color, king)),
        );
        let zone = king_attacks(king) | Bitboard::from(king);
        let enemy_pressure = attacks[color.opposite().index()] & zone;
        raw.king_zone_attack.add(
            weights.king_zone_attack,
            sign * i32::try_from(enemy_pressure.count()).expect("king-zone count fits i32"),
        );
        let controlled_space = attacks[color.index()] & space_mask(color);
        raw.space.add(
            weights.space,
            sign * i32::try_from(controlled_space.count()).expect("space count fits i32"),
        );
        raw.king_activity
            .add(weights.king_activity, sign * square_center_bonus(king));
    }
}

fn game_phase(position: &Position) -> u8 {
    let mut phase = 0_u32;
    for color in [Color::White, Color::Black] {
        phase += position.piece_bitboard(color, PieceKind::Knight).count();
        phase += position.piece_bitboard(color, PieceKind::Bishop).count();
        phase += 2 * position.piece_bitboard(color, PieceKind::Rook).count();
        phase += 4 * position.piece_bitboard(color, PieceKind::Queen).count();
    }
    u8::try_from(phase.min(u32::from(MAX_PHASE))).expect("phase is clamped below 25")
}

fn mobility_attacks(position: &Position, kind: PieceKind, square: Square) -> Bitboard {
    match kind {
        PieceKind::Knight => knight_attacks(square),
        PieceKind::Bishop => bishop_attacks(square, position.all_occupancy()),
        PieceKind::Rook => rook_attacks(square, position.all_occupancy()),
        PieceKind::Queen => queen_attacks(square, position.all_occupancy()),
        PieceKind::Pawn | PieceKind::King => Bitboard::EMPTY,
    }
}

fn attacks_by_color(position: &Position, color: Color) -> Bitboard {
    let mut attacks = Bitboard::EMPTY;
    for square in position.piece_bitboard(color, PieceKind::Pawn) {
        attacks |= pawn_attacks(color, square);
    }
    for square in position.piece_bitboard(color, PieceKind::Knight) {
        attacks |= knight_attacks(square);
    }
    for square in position.piece_bitboard(color, PieceKind::Bishop) {
        attacks |= bishop_attacks(square, position.all_occupancy());
    }
    for square in position.piece_bitboard(color, PieceKind::Rook) {
        attacks |= rook_attacks(square, position.all_occupancy());
    }
    for square in position.piece_bitboard(color, PieceKind::Queen) {
        attacks |= queen_attacks(square, position.all_occupancy());
    }
    attacks | king_attacks(position.king_square(color))
}

fn pawn_file_counts(pawns: Bitboard) -> [u8; 8] {
    let mut counts = [0_u8; 8];
    for square in pawns {
        counts[usize::from(square.file())] += 1;
    }
    counts
}

fn is_passed_pawn(color: Color, square: Square, enemy_pawns: Bitboard) -> bool {
    !enemy_pawns.into_iter().any(|enemy| {
        let file_distance = absolute_difference(square.file(), enemy.file());
        let ahead = match color {
            Color::White => enemy.row() < square.row(),
            Color::Black => enemy.row() > square.row(),
        };
        file_distance <= 1 && ahead
    })
}

fn is_connected_pawn(square: Square, friendly_pawns: Bitboard) -> bool {
    friendly_pawns.into_iter().any(|other| {
        other != square
            && absolute_difference(square.file(), other.file()) == 1
            && absolute_difference(square.row(), other.row()) <= 1
    })
}

fn pawn_advancement(color: Color, square: Square) -> i32 {
    i32::from(match color {
        Color::White => 6_u8.saturating_sub(square.row()),
        Color::Black => square.row().saturating_sub(1),
    })
}

fn king_shield_count(position: &Position, color: Color, king: Square) -> u8 {
    let target_row = match color {
        Color::White => king.row().checked_sub(1),
        Color::Black => king.row().checked_add(1).filter(|row| *row < 8),
    };
    let Some(row) = target_row else {
        return 0;
    };
    let mut count = 0;
    let start = king.file().saturating_sub(1);
    let end = (king.file() + 1).min(7);
    for file in start..=end {
        let square = Square::from_row_file(row, file).expect("shield square is on board");
        if position.piece_at(square)
            == Some(chess_core::Piece::new(color, PieceKind::Pawn))
        {
            count += 1;
        }
    }
    count
}

fn file_mask(file: u8) -> Bitboard {
    Bitboard::from_bits(0x0101_0101_0101_0101_u64 << file)
}

fn space_mask(color: Color) -> Bitboard {
    let half = match color {
        Color::White => WHITE_SPACE_HALF,
        Color::Black => BLACK_SPACE_HALF,
    };
    Bitboard::from_bits(FILE_B_TO_G & half)
}

fn relative_square_index(color: Color, square: Square) -> usize {
    let row = match color {
        Color::White => square.row(),
        Color::Black => 7 - square.row(),
    };
    usize::from(row * 8 + square.file())
}

fn square_center_bonus(square: Square) -> i32 {
    i32::from(center_bonus(square.row()) + center_bonus(square.file()))
}

fn center_bonus(coordinate: u8) -> u8 {
    let distance_to_three = absolute_difference(coordinate, 3);
    let distance_to_four = absolute_difference(coordinate, 4);
    3 - distance_to_three.min(distance_to_four)
}

fn absolute_difference(left: u8, right: u8) -> u8 {
    left.abs_diff(right)
}

const fn color_sign(color: Color) -> i32 {
    match color {
        Color::White => 1,
        Color::Black => -1,
    }
}

const fn oriented(white_score: i32, side_to_move: Color) -> i32 {
    match side_to_move {
        Color::White => white_score,
        Color::Black => -white_score,
    }
}

#[cfg(test)]
mod tests {
    use chess_core::Position;

    use super::{evaluate, evaluate_term, evaluate_trace, EvaluationTerm};
    use crate::EvaluationWeights;

    fn position(fen: &str) -> Position {
        Position::from_fen(fen).expect("evaluation fixture is valid")
    }

    #[test]
    fn starting_position_is_exactly_symmetric() {
        let starting = Position::starting();
        let trace = evaluate_trace(&starting);
        assert_eq!(trace.total, 0);
        assert_eq!(evaluate(&starting).centipawns(), 0);
        assert_eq!(trace.component_sum(), trace.total);
        assert_eq!(trace.phase, 24);
    }

    #[test]
    fn side_to_move_convention_negates_the_same_board() {
        let white = position("4k3/8/8/8/8/8/Q7/4K3 w - - 0 1");
        let black = position("4k3/8/8/8/8/8/Q7/4K3 b - - 0 1");
        assert_eq!(evaluate(&white), -evaluate(&black));
        assert!(evaluate(&white).centipawns() > 0);
    }

    #[test]
    fn color_and_vertical_mirror_preserve_relative_score() {
        let white = position("4k3/8/8/3P4/8/2N5/Q7/4K3 w - - 0 1");
        let black = position("4k3/q7/2n5/8/3p4/8/8/4K3 b - - 0 1");
        assert_eq!(evaluate(&white), evaluate(&black));
        assert_eq!(evaluate_trace(&white).total, evaluate_trace(&black).total);
    }

    #[test]
    fn trace_components_sum_to_the_normal_evaluation() {
        let current = position(
            "r3k2r/pp1n1ppp/2pbpn2/3p4/3P4/2PBPN2/PP1N1PPP/R3K2R w KQkq - 0 10",
        );
        let trace = evaluate_trace(&current);
        assert_eq!(trace.component_sum(), trace.total);
        assert_eq!(trace.total, evaluate(&current).centipawns());
    }

    #[test]
    fn pawn_trace_identifies_structure_without_hidden_terms() {
        let current = position("4k3/8/8/3P4/2PP4/8/8/4K3 w - - 0 1");
        let trace = evaluate_trace(&current);
        assert!(trace.passed_pawns > 0);
        assert!(trace.connected_pawns > 0);
        assert_eq!(trace.doubled_pawns, 0);
    }

    #[test]
    fn coarse_benchmark_groups_reconstruct_the_full_score() {
        let current = position(
            "r2q1rk1/pp1nbppp/2p1pn2/3p4/3P4/2N1PN2/PPQ1BPPP/R3K2R w KQ - 4 10",
        );
        let weights = EvaluationWeights::DEFAULT;
        let grouped = [
            EvaluationTerm::MaterialAndPieceSquare,
            EvaluationTerm::PawnStructure,
            EvaluationTerm::MobilityAndActivity,
            EvaluationTerm::KingAndSpace,
        ]
        .into_iter()
        .map(|term| evaluate_term(&current, &weights, term).centipawns())
        .sum::<i32>();
        assert_eq!(grouped, evaluate(&current).centipawns());
        assert_eq!(
            evaluate_term(&current, &weights, EvaluationTerm::Full),
            evaluate(&current)
        );
    }
}
