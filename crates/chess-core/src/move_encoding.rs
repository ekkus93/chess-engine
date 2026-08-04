use crate::{PieceKind, Square};

/// Semantic identity of a chess move.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum MoveKind {
    /// Non-capturing, non-special move.
    Quiet = 0,
    /// Two-square pawn advance.
    DoublePawnPush = 1,
    /// King-side castling.
    KingCastle = 2,
    /// Queen-side castling.
    QueenCastle = 3,
    /// Ordinary capture.
    Capture = 4,
    /// En-passant capture.
    EnPassant = 5,
    /// Quiet knight promotion.
    KnightPromotion = 6,
    /// Quiet bishop promotion.
    BishopPromotion = 7,
    /// Quiet rook promotion.
    RookPromotion = 8,
    /// Quiet queen promotion.
    QueenPromotion = 9,
    /// Knight promotion capture.
    KnightPromotionCapture = 10,
    /// Bishop promotion capture.
    BishopPromotionCapture = 11,
    /// Rook promotion capture.
    RookPromotionCapture = 12,
    /// Queen promotion capture.
    QueenPromotionCapture = 13,
}

impl MoveKind {
    /// All semantic move identities in packed-code order.
    pub const ALL: [Self; 14] = [
        Self::Quiet,
        Self::DoublePawnPush,
        Self::KingCastle,
        Self::QueenCastle,
        Self::Capture,
        Self::EnPassant,
        Self::KnightPromotion,
        Self::BishopPromotion,
        Self::RookPromotion,
        Self::QueenPromotion,
        Self::KnightPromotionCapture,
        Self::BishopPromotionCapture,
        Self::RookPromotionCapture,
        Self::QueenPromotionCapture,
    ];

    const fn from_code(code: u16) -> Self {
        match code {
            0 => Self::Quiet,
            1 => Self::DoublePawnPush,
            2 => Self::KingCastle,
            3 => Self::QueenCastle,
            4 => Self::Capture,
            5 => Self::EnPassant,
            6 => Self::KnightPromotion,
            7 => Self::BishopPromotion,
            8 => Self::RookPromotion,
            9 => Self::QueenPromotion,
            10 => Self::KnightPromotionCapture,
            11 => Self::BishopPromotionCapture,
            12 => Self::RookPromotionCapture,
            13 => Self::QueenPromotionCapture,
            _ => unreachable!(),
        }
    }

    /// Returns the promoted piece kind, when this is a promotion move.
    #[must_use]
    pub const fn promotion(self) -> Option<PieceKind> {
        match self {
            Self::KnightPromotion | Self::KnightPromotionCapture => Some(PieceKind::Knight),
            Self::BishopPromotion | Self::BishopPromotionCapture => Some(PieceKind::Bishop),
            Self::RookPromotion | Self::RookPromotionCapture => Some(PieceKind::Rook),
            Self::QueenPromotion | Self::QueenPromotionCapture => Some(PieceKind::Queen),
            Self::Quiet
            | Self::DoublePawnPush
            | Self::KingCastle
            | Self::QueenCastle
            | Self::Capture
            | Self::EnPassant => None,
        }
    }

    /// Returns whether this move removes an opposing piece.
    #[must_use]
    pub const fn is_capture(self) -> bool {
        matches!(
            self,
            Self::Capture
                | Self::EnPassant
                | Self::KnightPromotionCapture
                | Self::BishopPromotionCapture
                | Self::RookPromotionCapture
                | Self::QueenPromotionCapture
        )
    }
}

/// The engine's single compact internal move identity.
///
/// The packed bit layout is private and is not an external ABI contract.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct Move(u16);

impl Move {
    const SQUARE_MASK: u16 = 0x3f;
    const DESTINATION_SHIFT: u32 = 6;
    const KIND_SHIFT: u32 = 12;
    const KIND_MASK: u16 = 0x0f;

    /// Creates a packed move from validated values.
    #[must_use]
    pub const fn new(source: Square, destination: Square, kind: MoveKind) -> Self {
        let source_bits = source.index() as u16;
        let destination_bits = (destination.index() as u16) << Self::DESTINATION_SHIFT;
        let kind_bits = (kind as u16) << Self::KIND_SHIFT;
        Self(source_bits | destination_bits | kind_bits)
    }

    /// Returns the source square.
    #[must_use]
    pub const fn source(self) -> Square {
        Square::from_index_unchecked((self.0 & Self::SQUARE_MASK) as u8)
    }

    /// Returns the destination square.
    #[must_use]
    pub const fn destination(self) -> Square {
        let index = (self.0 >> Self::DESTINATION_SHIFT) & Self::SQUARE_MASK;
        Square::from_index_unchecked(index as u8)
    }

    /// Returns the semantic move kind.
    #[must_use]
    pub const fn kind(self) -> MoveKind {
        let code = (self.0 >> Self::KIND_SHIFT) & Self::KIND_MASK;
        MoveKind::from_code(code)
    }

    /// Returns the promoted piece kind, when applicable.
    #[must_use]
    pub const fn promotion(self) -> Option<PieceKind> {
        self.kind().promotion()
    }
}

#[cfg(test)]
mod tests {
    use core::mem::size_of;
    use std::collections::HashSet;

    use crate::{PieceKind, Square};

    use super::{Move, MoveKind};

    fn square(value: &str) -> Square {
        value.parse().expect("test square is valid")
    }

    #[test]
    fn every_move_kind_round_trips_through_packed_identity() {
        let source = square("e2");
        let destination = square("e4");
        let mut identities = HashSet::new();

        for kind in MoveKind::ALL {
            let current = Move::new(source, destination, kind);
            assert_eq!(current.source(), source);
            assert_eq!(current.destination(), destination);
            assert_eq!(current.kind(), kind);
            assert_eq!(current.promotion(), kind.promotion());
            assert!(identities.insert(current));
        }
        assert_eq!(identities.len(), MoveKind::ALL.len());
        assert_eq!(size_of::<Move>(), 2);
    }

    #[test]
    fn promotion_and_capture_identities_remain_distinct() {
        let source = square("a7");
        let destination = square("b8");
        let expected = [
            (MoveKind::KnightPromotion, PieceKind::Knight, false),
            (MoveKind::BishopPromotion, PieceKind::Bishop, false),
            (MoveKind::RookPromotion, PieceKind::Rook, false),
            (MoveKind::QueenPromotion, PieceKind::Queen, false),
            (MoveKind::KnightPromotionCapture, PieceKind::Knight, true),
            (MoveKind::BishopPromotionCapture, PieceKind::Bishop, true),
            (MoveKind::RookPromotionCapture, PieceKind::Rook, true),
            (MoveKind::QueenPromotionCapture, PieceKind::Queen, true),
        ];
        let mut moves = HashSet::new();

        for (kind, promotion, capture) in expected {
            let current = Move::new(source, destination, kind);
            assert_eq!(current.promotion(), Some(promotion));
            assert_eq!(kind.is_capture(), capture);
            assert!(moves.insert(current));
        }
        assert_eq!(moves.len(), expected.len());
    }

    #[test]
    fn ordering_and_hashing_are_stable_value_semantics() {
        let a = Move::new(square("a2"), square("a3"), MoveKind::Quiet);
        let b = Move::new(square("a2"), square("a4"), MoveKind::DoublePawnPush);
        assert_ne!(a, b);
        assert!(a < b);
    }
}
