use core::{fmt, mem::size_of};

use chess_core::Move;

use crate::Score;

mod diagnostics;
mod principal_variation;
mod probe;
mod store;
pub use diagnostics::{
    TranspositionHashFull, TranspositionTableDiagnostics, TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,
};
pub use probe::{
    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeResult,
    TranspositionProbeScore, TranspositionScoreReuse,
};
pub use store::{TranspositionStoreAction, TranspositionStoreResult};

const BYTES_PER_MEBIBYTE: usize = 1024 * 1024;

/// Number of transposition entries stored in one collision cluster.
pub const TRANSPOSITION_CLUSTER_SIZE: usize = 4;

/// Search-window meaning of a stored transposition-table score.
///
/// The tag describes how [`TranspositionTable::probe`] may reuse the score.
/// Keeping all three meanings explicit prevents a bound from being mistaken for
/// an exact minimax value.
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

/// A score converted into the transposition table's storage domain.
///
/// Use [`TranspositionScore::normalize`] to convert a root-relative search
/// score at the storage ply and [`TranspositionScore::denormalize`] to recover
/// the correct root-relative value at a later probe ply. Keeping the value in a
/// distinct type prevents ordinary search scores from being confused with
/// position-relative stored scores.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct TranspositionScore(Score);

impl TranspositionScore {
    /// Wraps a score already proven to be in the normalized storage domain.
    ///
    /// Public callers must use [`TranspositionScore::normalize`]. This
    /// crate-private constructor remains available to the conversion module and
    /// focused entry-layout tests without exposing an unchecked public bypass.
    #[must_use]
    pub(crate) const fn from_normalized(normalized: Score) -> Self {
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
/// than relying on the bucket index alone. Scores enter the normalized storage
/// domain through [`TranspositionScore::normalize`].
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

    pub(crate) const fn with_generation(mut self, generation: u8) -> Self {
        self.generation = generation;
        self
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(C)]
struct TranspositionCluster {
    entries: [Option<TranspositionEntry>; TRANSPOSITION_CLUSTER_SIZE],
}

impl TranspositionCluster {
    const EMPTY: Self = Self {
        entries: [None; TRANSPOSITION_CLUSTER_SIZE],
    };

    fn clear(&mut self) {
        self.entries.fill(None);
    }
}

/// Failure to configure or allocate a fixed-capacity transposition table.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionTableAllocationError {
    /// A zero-MiB table cannot contain a cluster.
    ZeroMebibytes,
    /// Converting the requested MiB count into bytes overflowed `usize`.
    SizeOverflow {
        /// Requested table size in MiB.
        mebibytes: usize,
    },
    /// The requested byte budget cannot contain one complete cluster.
    NoWholeCluster {
        /// Requested byte budget.
        requested_bytes: usize,
        /// Size of one cluster in bytes.
        cluster_bytes: usize,
    },
    /// The allocator rejected the complete fixed-size cluster reservation.
    AllocationFailed {
        /// Requested byte budget.
        requested_bytes: usize,
        /// Number of complete clusters requested.
        cluster_count: usize,
    },
}

impl fmt::Display for TranspositionTableAllocationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroMebibytes => {
                write!(formatter, "transposition-table size must be at least 1 MiB")
            }
            Self::SizeOverflow { mebibytes } => write!(
                formatter,
                "transposition-table size of {mebibytes} MiB exceeds the addressable byte range"
            ),
            Self::NoWholeCluster {
                requested_bytes,
                cluster_bytes,
            } => write!(
                formatter,
                "transposition-table budget of {requested_bytes} bytes cannot contain one {cluster_bytes}-byte cluster"
            ),
            Self::AllocationFailed {
                requested_bytes,
                cluster_count,
            } => write!(
                formatter,
                "failed to allocate {cluster_count} transposition clusters within the {requested_bytes}-byte budget"
            ),
        }
    }
}

impl std::error::Error for TranspositionTableAllocationError {}

/// Fixed-capacity clustered transposition-table storage.
///
/// Construction performs one fallible reservation for all clusters. The table
/// never grows after construction and has no unbounded map fallback. Probes
/// verify complete keys and apply depth, bound, mate, and repetition safety. Stores
/// update same-key entries and use deterministic depth- and generation-aware
/// collision replacement.
#[derive(Debug)]
pub struct TranspositionTable {
    clusters: Vec<TranspositionCluster>,
    generation: u8,
    requested_mebibytes: usize,
    allocated_bytes: usize,
    diagnostics: TranspositionTableDiagnostics,
}

impl TranspositionTable {
    /// Allocates a fixed table within the requested MiB budget.
    ///
    /// The byte budget is rounded down to a whole number of four-entry clusters.
    /// No partial cluster is allocated and allocation failure is returned as a
    /// typed error.
    pub fn new(mebibytes: usize) -> Result<Self, TranspositionTableAllocationError> {
        let requested_bytes = requested_bytes(mebibytes)?;
        let cluster_bytes = size_of::<TranspositionCluster>();
        let cluster_count = requested_bytes / cluster_bytes;

        if cluster_count == 0 {
            return Err(TranspositionTableAllocationError::NoWholeCluster {
                requested_bytes,
                cluster_bytes,
            });
        }

        let allocated_bytes = cluster_count * cluster_bytes;
        let mut clusters = Vec::new();
        clusters.try_reserve_exact(cluster_count).map_err(|_| {
            TranspositionTableAllocationError::AllocationFailed {
                requested_bytes,
                cluster_count,
            }
        })?;
        clusters.resize(cluster_count, TranspositionCluster::EMPTY);

        Ok(Self {
            clusters,
            generation: 0,
            requested_mebibytes: mebibytes,
            allocated_bytes,
            diagnostics: TranspositionTableDiagnostics::default(),
        })
    }

    /// Returns the configured table budget in MiB.
    #[must_use]
    pub const fn requested_mebibytes(&self) -> usize {
        self.requested_mebibytes
    }

    /// Returns the bytes occupied by complete logical clusters.
    #[must_use]
    pub const fn allocated_bytes(&self) -> usize {
        self.allocated_bytes
    }

    /// Returns the fixed number of collision clusters.
    #[must_use]
    pub fn cluster_count(&self) -> usize {
        self.clusters.len()
    }

    /// Returns the fixed number of entry slots across all clusters.
    #[must_use]
    pub fn entry_capacity(&self) -> usize {
        self.clusters.len() * TRANSPOSITION_CLUSTER_SIZE
    }

    /// Returns the generation assigned to newly stored entries.
    #[must_use]
    pub const fn generation(&self) -> u8 {
        self.generation
    }

    /// Returns the deterministic cluster index for a complete verification key.
    ///
    /// Keys can share this index; occupied entries retain the complete key so a
    /// later probe can reject collisions safely.
    #[must_use]
    pub fn cluster_index(&self, verification_key: u64) -> usize {
        (verification_key % self.clusters.len() as u64) as usize
    }

    /// Removes every entry without changing allocation or generation.
    pub fn clear(&mut self) {
        for cluster in &mut self.clusters {
            cluster.clear();
        }
    }

    /// Advances to a new generation using defined wrapping arithmetic.
    ///
    /// Existing entries remain present so the later replacement policy can
    /// compare their age with the current generation.
    pub fn advance_generation(&mut self) -> u8 {
        self.generation = self.generation.wrapping_add(1);
        self.generation
    }
}

fn requested_bytes(mebibytes: usize) -> Result<usize, TranspositionTableAllocationError> {
    if mebibytes == 0 {
        return Err(TranspositionTableAllocationError::ZeroMebibytes);
    }

    mebibytes
        .checked_mul(BYTES_PER_MEBIBYTE)
        .ok_or(TranspositionTableAllocationError::SizeOverflow { mebibytes })
}

#[cfg(test)]
mod tests {
    use core::mem::{align_of, size_of};

    use chess_core::{Move, MoveKind, Square};

    use super::{
        TranspositionBound, TranspositionCluster, TranspositionEntry, TranspositionScore,
        TranspositionTable, TranspositionTableAllocationError, BYTES_PER_MEBIBYTE,
        TRANSPOSITION_CLUSTER_SIZE,
    };
    use crate::{Score, MATE_SCORE};

    fn square(text: &str) -> Square {
        text.parse().expect("entry-test square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush)
    }

    fn entry(verification_key: u64, generation: u8) -> TranspositionEntry {
        TranspositionEntry::new(
            verification_key,
            8,
            TranspositionBound::Exact,
            TranspositionScore::from_normalized(Score::from_evaluation(31)),
            Some(best_move()),
            generation,
        )
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
        assert_eq!(
            current.normalized_score().normalized().centipawns(),
            MATE_SCORE - 17
        );
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

    #[test]
    fn invalid_table_sizes_fail_loudly_without_allocating() {
        assert!(matches!(
            TranspositionTable::new(0),
            Err(TranspositionTableAllocationError::ZeroMebibytes)
        ));
        assert!(matches!(
            TranspositionTable::new(usize::MAX),
            Err(TranspositionTableAllocationError::SizeOverflow {
                mebibytes: usize::MAX
            })
        ));
    }

    #[test]
    fn mib_budget_rounds_down_to_complete_fixed_clusters() {
        let table = TranspositionTable::new(1).expect("one MiB table allocates");
        let cluster_bytes = size_of::<TranspositionCluster>();

        assert_eq!(table.requested_mebibytes(), 1);
        assert!(table.allocated_bytes() <= BYTES_PER_MEBIBYTE);
        assert!(BYTES_PER_MEBIBYTE - table.allocated_bytes() < cluster_bytes);
        assert_eq!(
            table.allocated_bytes(),
            table.cluster_count() * cluster_bytes
        );
        assert_eq!(
            table.entry_capacity(),
            table.cluster_count() * TRANSPOSITION_CLUSTER_SIZE
        );
        assert_eq!(table.clusters.len(), table.cluster_count());
        assert!(table.clusters.capacity() >= table.clusters.len());
    }

    #[test]
    fn four_way_clusters_use_deterministic_collision_indexing() {
        let table = TranspositionTable::new(1).expect("table allocates");
        let key = 0x1234_5678_9abc_def0;
        let collision = key + table.cluster_count() as u64;
        let index = table.cluster_index(key);

        assert_eq!(TRANSPOSITION_CLUSTER_SIZE, 4);
        assert!(index < table.cluster_count());
        assert_eq!(index, table.cluster_index(key));
        assert_eq!(index, table.cluster_index(collision));
    }

    #[test]
    fn clear_preserves_allocation_and_generation() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 17;
        let index = table.cluster_index(key);
        table.clusters[index].entries[0] = Some(entry(key, table.generation()));
        table.advance_generation();

        let pointer = table.clusters.as_ptr();
        let capacity = table.clusters.capacity();
        let generation = table.generation();
        table.clear();

        assert_eq!(table.clusters.as_ptr(), pointer);
        assert_eq!(table.clusters.capacity(), capacity);
        assert_eq!(table.generation(), generation);
        assert!(table
            .clusters
            .iter()
            .all(|cluster| cluster.entries.iter().all(Option::is_none)));
    }

    #[test]
    fn generation_wraps_without_clearing_existing_entries() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 29;
        let index = table.cluster_index(key);
        table.clusters[index].entries[0] = Some(entry(key, u8::MAX));
        table.generation = u8::MAX;

        assert_eq!(table.advance_generation(), 0);
        assert_eq!(table.generation(), 0);
        assert_eq!(table.clusters[index].entries[0], Some(entry(key, u8::MAX)));
    }
}
