use chess_core::Move;

use crate::Score;

/// Search-window meaning of a stored transposition-table score.
///
/// The tag describes how the score may eventually be reused by a probe. Task
/// 15.4 owns the cutoff rules; this type only makes the three meanings explicit
/// and impossible to confuse with one another.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
#[repr(u8)]
pub enum TranspositionBound {
    /// The stored score is the exact minimax value for the searched depth.
    Exact = 0,
    /// The stored score is a lower bound produced by a fail-high search.
    Lower = 1,
    /// The stored score is an upper bound produced by a fail-low search.
    Upper = 2,
}

/// A score already converted into the transposition table's storage domain.
///
/// Task 15.3 will define the mate-distance conversion between node-relative
/// [`Score`] values and this stored representation. Keeping the value in a
/// distinct type prevents an ordinary node score from being placed into an
/// entry accidentally once storage and probes are implemented.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct TranspositionScore(Score);

impl TranspositionScore {
    /// Wraps a score that the caller has already normalized for storage.
    ///
    /// Before Task 15.3 this constructor is the explicit boundary used by entry
    /// tests. Production search does not yet create or consume TT entries.
    #[must_use]
    pub const fn from_normalized(normalized: Score) -> Self {
        Self(normalized)
    }

    /// Returns the normalized score stored in the entry.
    #[must_use]
    pub const fn normalized(self) -> Score {
        self.0
    }
}

/// Complete payload stored for one transposition-table position.
///
/// Slot selection and collision handling belong to Tasks 15.2 and 15.5. The
/// entry retains the complete 64-bit position key as a verification key rather
/// than relying on the bucket index alone. The score must already be in the
/// normalized storage domain represented by [`TranspositionScore`].
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
#[repr(C)]
pub struct TranspositionEntry {
    verification_key: u64,
    normalized_score: TranspositionScore,
    best_move: Option<Move>,
    depth: u16,
    bound: TranspositionBound,
    generation: u8,
}

impl TranspositionEntry {
    /// Constructs one complete transposition-table entry.
    #[must_use]
    pub const fn new(
        verification_key: u64,
        depth: u16,
        bound: TranspositionBound,
        normalized_score: TranspositionScore,
        best_move: Option<Move>,
        generation: u8,
    ) -> Self {
        Self {
            verification_key,
            normalized_score,
            best_move,
            depth,
            bound,
            generation,
        }
    }

    /// Returns the complete position-verification key.
    #[must_use]
    pub const fn verification_key(self) -> u64 {
        self.verification_key
    }

    /// Returns the searched depth in plies.
    #[must_use]
    pub const fn depth(self) -> u16 {
        self.depth
    }

    /// Returns the exact/lower/upper meaning of the stored score.
    #[must_use]
    pub const fn bound(self) -> TranspositionBound {
        self.bound
    }

    /// Returns the score in its normalized storage domain.
    #[must_use]
    pub const fn normalized_score(self) -> TranspositionScore {
        self.normalized_score
    }

    /// Returns the best move retained for future move ordering, when available.
    #[must_use]
    pub const fn best_move(self) -> Option<Move> {
        self.best_move
    }

    /// Returns the table generation associated with this entry.
    #[must_use]
    pub const fn generation(self) -> u8 {
        self.generation
    }
}

#[cfg(test)]
mod tests {
    use core::mem::{align_of, size_of};

    use chess_core::{Move, MoveKind, Square};

    use super::{TranspositionBound, TranspositionEntry, TranspositionScore};
    use crate::{Score, MATE_SCORE};

    fn square(text: &str) -> Square {
        text.parse().expect("entry-test square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush)
    }

    #[test]
    fn bound_tags_are_complete_and_have_stable_compact_codes() {
        assert_eq!(TranspositionBound::Exact as u8, 0);
        assert_eq!(TranspositionBound::Lower as u8, 1);
        assert_eq!(TranspositionBound::Upper as u8, 2);
        assert_eq!(size_of::<TranspositionBound>(), 1);
    }

    #[test]
    fn entry_round_trips_every_required_field() {
        let score = TranspositionScore::from_normalized(
            Score::from_raw(MATE_SCORE - 17).expect("stored score is in range"),
        );
        let current = TranspositionEntry::new(
            0xfedc_ba98_7654_3210,
            23,
            TranspositionBound::Lower,
            score,
            Some(best_move()),
            197,
        );

        assert_eq!(current.verification_key(), 0xfedc_ba98_7654_3210);
        assert_eq!(current.depth(), 23);
        assert_eq!(current.bound(), TranspositionBound::Lower);
        assert_eq!(current.normalized_score(), score);
        assert_eq!(current.normalized_score().normalized().centipawns(), MATE_SCORE - 17);
        assert_eq!(current.best_move(), Some(best_move()));
        assert_eq!(current.generation(), 197);
    }

    #[test]
    fn entries_support_all_bounds_and_an_absent_best_move() {
        let normalized = TranspositionScore::from_normalized(Score::from_evaluation(-42));

        for bound in [
            TranspositionBound::Exact,
            TranspositionBound::Lower,
            TranspositionBound::Upper,
        ] {
            let current = TranspositionEntry::new(7, 0, bound, normalized, None, 0);
            assert_eq!(current.bound(), bound);
            assert_eq!(current.best_move(), None);
            assert_eq!(current.normalized_score().normalized().centipawns(), -42);
        }
    }

    #[test]
    fn verification_uses_the_complete_key_and_entries_are_value_types() {
        let score = TranspositionScore::from_normalized(Score::ZERO);
        let low = TranspositionEntry::new(
            0x0000_0000_89ab_cdef,
            4,
            TranspositionBound::Exact,
            score,
            Some(best_move()),
            3,
        );
        let high = TranspositionEntry::new(
            0x1234_5678_89ab_cdef,
            4,
            TranspositionBound::Exact,
            score,
            Some(best_move()),
            3,
        );
        let copied = high;

        assert_ne!(low, high);
        assert_eq!(copied, high);
        assert_eq!(high.verification_key(), 0x1234_5678_89ab_cdef);
    }

    #[test]
    fn entry_layout_is_bounded_and_score_wrapper_has_no_overhead() {
        assert_eq!(size_of::<TranspositionScore>(), size_of::<Score>());
        assert!(size_of::<TranspositionEntry>() <= 24);
        assert!(align_of::<TranspositionEntry>() <= align_of::<u64>());
    }
}
