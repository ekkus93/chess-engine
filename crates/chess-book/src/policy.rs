use core::fmt;
use std::error::Error;

use chess_core::{LegalMoveError, Move, Position, UciMove};

use crate::{BookMove, IndexedBook, IndexedBookError, OpeningBook};

const SPLITMIX64_INCREMENT: u64 = 0x9e37_79b9_7f4a_7c15;
const SPLITMIX64_MULTIPLIER_ONE: u64 = 0xbf58_476d_1ce4_e5b9;
const SPLITMIX64_MULTIPLIER_TWO: u64 = 0x94d0_49bb_1331_11eb;

/// Available opening-book move-selection policies.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BookSelectionMode {
    /// Select the greatest weight, resolving ties by ascending UCI move text.
    DeterministicHighestWeight,
    /// Select proportionally to weight using selector-local seeded state.
    WeightedRandom,
}

/// Stateful, adapter-owned opening-book move selector.
///
/// Deterministic mode has no random state. Weighted-random mode uses a
/// selector-local SplitMix64 stream initialized from the explicit caller seed.
/// It never reads process-global randomness, clocks, files, or platform state.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BookSelector {
    mode: BookSelectionMode,
    initial_seed: Option<u64>,
    rng_state: Option<u64>,
}

impl BookSelector {
    /// Creates the default deterministic highest-weight selector.
    #[must_use]
    pub const fn deterministic_highest_weight() -> Self {
        Self {
            mode: BookSelectionMode::DeterministicHighestWeight,
            initial_seed: None,
            rng_state: None,
        }
    }

    /// Creates an opt-in weighted selector with one explicit local seed.
    #[must_use]
    pub const fn weighted_random(seed: u64) -> Self {
        Self {
            mode: BookSelectionMode::WeightedRandom,
            initial_seed: Some(seed),
            rng_state: Some(seed),
        }
    }

    /// Returns the configured selection mode.
    #[must_use]
    pub const fn mode(&self) -> BookSelectionMode {
        self.mode
    }

    /// Returns the explicit initial seed for weighted mode.
    #[must_use]
    pub const fn seed(&self) -> Option<u64> {
        self.initial_seed
    }

    /// Queries, validates, canonically orders, and selects one book move.
    ///
    /// `Ok(None)` means the book contains no candidate for this position.
    /// Every nonempty candidate set is checked against the exact generated
    /// legal move identities before either policy may return a move.
    pub fn select<B>(
        &mut self,
        book: &B,
        position: &Position,
    ) -> Result<Option<BookMove<B::Metadata>>, BookSelectionError<B::Error>>
    where
        B: OpeningBook,
    {
        let mut candidates = book
            .candidates(position)
            .map_err(BookSelectionError::Book)?;
        if candidates.is_empty() {
            return Ok(None);
        }

        validate_legal_candidates(position, &candidates)?;
        candidates.sort_by_key(|candidate| candidate.chess_move().to_uci());
        for pair in candidates.windows(2) {
            if pair[0].chess_move() == pair[1].chess_move() {
                return Err(BookSelectionError::DuplicateCandidate {
                    chess_move: pair[0].chess_move(),
                });
            }
        }

        match self.mode {
            BookSelectionMode::DeterministicHighestWeight => {
                let mut best_index = 0;
                let mut best_weight = candidates[0].weight();
                for (index, candidate) in candidates.iter().enumerate().skip(1) {
                    if candidate.weight() > best_weight {
                        best_index = index;
                        best_weight = candidate.weight();
                    }
                }
                Ok(Some(candidates.remove(best_index)))
            }
            BookSelectionMode::WeightedRandom => {
                let total_weight = candidates.iter().try_fold(0_u64, |total, candidate| {
                    total
                        .checked_add(u64::from(candidate.weight()))
                        .ok_or(BookSelectionError::TotalWeightOverflow)
                })?;
                if total_weight == 0 {
                    return Err(BookSelectionError::ZeroTotalWeight);
                }

                let mut target = self.sample_below(total_weight);
                let selected_index = candidates
                    .iter()
                    .enumerate()
                    .find_map(|(index, candidate)| {
                        let weight = u64::from(candidate.weight());
                        if target < weight {
                            Some(index)
                        } else {
                            target -= weight;
                            None
                        }
                    })
                    .expect("a sample below positive total weight selects one candidate");
                Ok(Some(candidates.remove(selected_index)))
            }
        }
    }

    fn sample_below(&mut self, upper_bound: u64) -> u64 {
        debug_assert!(upper_bound > 0);
        let rejection_threshold = upper_bound.wrapping_neg() % upper_bound;
        loop {
            let sample = self.next_random_u64();
            if sample >= rejection_threshold {
                return sample % upper_bound;
            }
        }
    }

    fn next_random_u64(&mut self) -> u64 {
        let state = self
            .rng_state
            .as_mut()
            .expect("weighted mode always owns local RNG state");
        *state = state.wrapping_add(SPLITMIX64_INCREMENT);
        let mut value = *state;
        value = (value ^ (value >> 30)).wrapping_mul(SPLITMIX64_MULTIPLIER_ONE);
        value = (value ^ (value >> 27)).wrapping_mul(SPLITMIX64_MULTIPLIER_TWO);
        value ^ (value >> 31)
    }
}

impl Default for BookSelector {
    fn default() -> Self {
        Self::deterministic_highest_weight()
    }
}

/// Fail-visible lookup, legality, and policy error.
#[derive(Debug, Eq, PartialEq)]
pub enum BookSelectionError<E> {
    /// The configured opening-book backend failed.
    Book(E),
    /// Exact legal-move generation failed.
    LegalMoveGeneration(LegalMoveError),
    /// A backend returned a move that is not an exact legal identity.
    IllegalCandidate { chess_move: Move },
    /// A backend returned the same legal move more than once.
    DuplicateCandidate { chess_move: Move },
    /// Candidate weights could not be accumulated safely.
    TotalWeightOverflow,
    /// Weighted selection was requested but every candidate weight was zero.
    ZeroTotalWeight,
}

impl<E> fmt::Display for BookSelectionError<E>
where
    E: fmt::Display,
{
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Book(error) => write!(formatter, "opening-book lookup failed: {error}"),
            Self::LegalMoveGeneration(error) => {
                write!(formatter, "opening-book legal-move generation failed: {error}")
            }
            Self::IllegalCandidate { chess_move } => write!(
                formatter,
                "opening-book candidate {} is not an exact legal move",
                chess_move.to_uci()
            ),
            Self::DuplicateCandidate { chess_move } => write!(
                formatter,
                "opening-book backend returned duplicate candidate {}",
                chess_move.to_uci()
            ),
            Self::TotalWeightOverflow => {
                formatter.write_str("opening-book candidate weight total overflowed")
            }
            Self::ZeroTotalWeight => {
                formatter.write_str("weighted opening-book selection has zero total weight")
            }
        }
    }
}

impl<E> Error for BookSelectionError<E>
where
    E: Error + 'static,
{
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Book(error) => Some(error),
            Self::LegalMoveGeneration(error) => Some(error),
            Self::IllegalCandidate { .. }
            | Self::DuplicateCandidate { .. }
            | Self::TotalWeightOverflow
            | Self::ZeroTotalWeight => None,
        }
    }
}

/// Fail-visible indexed-book lookup and legal-resolution error.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum IndexedBookQueryError {
    /// Canonical position-key derivation failed.
    Indexed(IndexedBookError),
    /// Exact legal-move generation failed.
    LegalMoveGeneration(LegalMoveError),
    /// One syntax-valid indexed record does not identify a legal move.
    IllegalMove { uci_move: UciMove },
    /// One indexed record unexpectedly matched more than one legal identity.
    AmbiguousMove { uci_move: UciMove },
}

impl fmt::Display for IndexedBookQueryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Indexed(error) => write!(formatter, "indexed opening-book lookup failed: {error}"),
            Self::LegalMoveGeneration(error) => {
                write!(formatter, "indexed opening-book legal-move generation failed: {error}")
            }
            Self::IllegalMove { uci_move } => {
                write!(formatter, "indexed opening-book move {uci_move} is not legal")
            }
            Self::AmbiguousMove { uci_move } => write!(
                formatter,
                "indexed opening-book move {uci_move} matched multiple legal identities"
            ),
        }
    }
}

impl Error for IndexedBookQueryError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Indexed(error) => Some(error),
            Self::LegalMoveGeneration(error) => Some(error),
            Self::IllegalMove { .. } | Self::AmbiguousMove { .. } => None,
        }
    }
}

impl OpeningBook for IndexedBook {
    type Metadata = u32;
    type Error = IndexedBookQueryError;

    fn candidates(
        &self,
        position: &Position,
    ) -> Result<Vec<BookMove<Self::Metadata>>, Self::Error> {
        let records = self
            .records_for_position(position)
            .map_err(IndexedBookQueryError::Indexed)?;
        if records.is_empty() {
            return Ok(Vec::new());
        }

        let mut legal_position = position.clone();
        let legal_moves = legal_position
            .legal_moves()
            .map_err(IndexedBookQueryError::LegalMoveGeneration)?;
        let mut candidates = Vec::with_capacity(records.len());

        for record in records {
            let uci_move = record.uci_move();
            let mut matches = legal_moves
                .iter()
                .filter(|candidate| uci_move.matches(*candidate));
            let Some(chess_move) = matches.next() else {
                return Err(IndexedBookQueryError::IllegalMove { uci_move });
            };
            if matches.next().is_some() {
                return Err(IndexedBookQueryError::AmbiguousMove { uci_move });
            }
            candidates.push(BookMove::from_parts(
                chess_move,
                record.weight(),
                record.metadata(),
            ));
        }

        Ok(candidates)
    }
}

fn validate_legal_candidates<E, M>(
    position: &Position,
    candidates: &[BookMove<M>],
) -> Result<(), BookSelectionError<E>> {
    let mut legal_position = position.clone();
    let legal_moves = legal_position
        .legal_moves()
        .map_err(BookSelectionError::LegalMoveGeneration)?;
    for candidate in candidates {
        if !legal_moves
            .iter()
            .any(|legal_move| legal_move == candidate.chess_move())
        {
            return Err(BookSelectionError::IllegalCandidate {
                chess_move: candidate.chess_move(),
            });
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use core::convert::Infallible;

    use chess_core::{MoveKind, Square};

    use super::*;
    use crate::IndexedBookRecord;

    #[derive(Clone, Debug)]
    struct StaticBook {
        candidates: Vec<BookMove<u32>>,
    }

    impl OpeningBook for StaticBook {
        type Metadata = u32;
        type Error = Infallible;

        fn candidates(
            &self,
            _position: &Position,
        ) -> Result<Vec<BookMove<Self::Metadata>>, Self::Error> {
            Ok(self.candidates.clone())
        }
    }

    fn legal_move(position: &Position, value: &str) -> Move {
        let uci_move = value.parse::<UciMove>().expect("test UCI syntax is valid");
        let mut legal_position = position.clone();
        let matches = legal_position
            .legal_moves()
            .expect("test position generates legal moves")
            .iter()
            .filter(|candidate| uci_move.matches(*candidate))
            .collect::<Vec<_>>();
        assert_eq!(matches.len(), 1);
        matches[0]
    }

    fn weighted_book(position: &Position) -> StaticBook {
        StaticBook {
            candidates: vec![
                BookMove::from_parts(legal_move(position, "g1f3"), 3, Some(3)),
                BookMove::from_parts(legal_move(position, "e2e4"), 7, Some(7)),
                BookMove::from_parts(legal_move(position, "d2d4"), 11, Some(11)),
            ],
        }
    }

    #[test]
    fn highest_weight_is_deterministic_and_ties_use_ascending_uci() {
        let position = Position::starting();
        let book = StaticBook {
            candidates: vec![
                BookMove::from_parts(legal_move(&position, "e2e4"), 20, None::<u32>),
                BookMove::from_parts(legal_move(&position, "d2d4"), 20, None::<u32>),
                BookMove::from_parts(legal_move(&position, "g1f3"), 10, None::<u32>),
            ],
        };
        let mut selector = BookSelector::deterministic_highest_weight();

        let selected = selector
            .select(&book, &position)
            .expect("selection succeeds")
            .expect("book has candidates");

        assert_eq!(selected.chess_move().to_uci(), "d2d4");
        assert_eq!(selector.mode(), BookSelectionMode::DeterministicHighestWeight);
        assert_eq!(selector.seed(), None);
    }

    #[test]
    fn weighted_selection_is_reproducible_from_explicit_local_seed() {
        let position = Position::starting();
        let book = weighted_book(&position);
        let seed = 0xc0ff_ee12_3456_789a;
        let mut first = BookSelector::weighted_random(seed);
        let mut second = BookSelector::weighted_random(seed);

        let first_sequence = (0..32)
            .map(|_| {
                first
                    .select(&book, &position)
                    .expect("selection succeeds")
                    .expect("book has candidates")
                    .chess_move()
            })
            .collect::<Vec<_>>();
        let second_sequence = (0..32)
            .map(|_| {
                second
                    .select(&book, &position)
                    .expect("selection succeeds")
                    .expect("book has candidates")
                    .chess_move()
            })
            .collect::<Vec<_>>();

        assert_eq!(first_sequence, second_sequence);
        assert_eq!(first.mode(), BookSelectionMode::WeightedRandom);
        assert_eq!(first.seed(), Some(seed));
    }

    #[test]
    fn every_candidate_is_validated_before_selection() {
        let position = Position::starting();
        let illegal = Move::new(
            "e2".parse::<Square>().expect("test square is valid"),
            "e5".parse::<Square>().expect("test square is valid"),
            MoveKind::Quiet,
        );
        let book = StaticBook {
            candidates: vec![BookMove::from_parts(illegal, u32::MAX, None::<u32>)],
        };
        let mut selector = BookSelector::deterministic_highest_weight();

        assert_eq!(
            selector.select(&book, &position),
            Err(BookSelectionError::IllegalCandidate {
                chess_move: illegal
            })
        );
    }

    #[test]
    fn weighted_selection_rejects_zero_total_weight() {
        let position = Position::starting();
        let book = StaticBook {
            candidates: vec![
                BookMove::from_parts(legal_move(&position, "e2e4"), 0, None::<u32>),
                BookMove::from_parts(legal_move(&position, "d2d4"), 0, None::<u32>),
            ],
        };
        let mut selector = BookSelector::weighted_random(7);

        assert_eq!(
            selector.select(&book, &position),
            Err(BookSelectionError::ZeroTotalWeight)
        );
    }

    #[test]
    fn indexed_book_resolves_only_exact_legal_moves() {
        let position = Position::starting();
        let record = IndexedBookRecord::with_metadata(
            &position,
            "e2e4".parse().expect("test UCI syntax is valid"),
            42,
            99,
        )
        .expect("test record is valid");
        let book = IndexedBook::from_records(vec![record]).expect("record set is valid");

        let candidates = book
            .candidates(&position)
            .expect("indexed lookup resolves legal move");
        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].chess_move().to_uci(), "e2e4");
        assert_eq!(candidates[0].weight(), 42);
        assert_eq!(candidates[0].metadata(), Some(&99));
    }

    #[test]
    fn indexed_book_rejects_syntax_valid_position_illegal_move() {
        let position = Position::starting();
        let record = IndexedBookRecord::new(
            &position,
            "e2e5".parse().expect("test UCI syntax is valid"),
            1,
        )
        .expect("format accepts unresolved syntax");
        let book = IndexedBook::from_records(vec![record]).expect("record set is valid");

        assert_eq!(
            book.candidates(&position),
            Err(IndexedBookQueryError::IllegalMove {
                uci_move: "e2e5".parse().expect("test UCI syntax is valid")
            })
        );
    }
}
