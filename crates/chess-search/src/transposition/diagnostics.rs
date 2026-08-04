use super::{TranspositionTable, TRANSPOSITION_CLUSTER_SIZE};

/// Maximum number of entry slots inspected by one hash-full estimate.
pub const TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT: usize = 1_000;

/// Saturating transposition-table operation counters.
///
/// Counters are observational only. They never affect probe, score-reuse, or
/// replacement decisions and remain bounded to this fixed-size value object.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct TranspositionTableDiagnostics {
    probes: u64,
    hits: u64,
    exact_hits: u64,
    lower_bound_cutoffs: u64,
    upper_bound_cutoffs: u64,
    stores: u64,
    same_key_updates: u64,
    empty_inserts: u64,
    collision_replacements: u64,
}

impl TranspositionTableDiagnostics {
    /// Returns the number of valid probe requests that performed a table lookup.
    #[must_use]
    pub const fn probes(self) -> u64 {
        self.probes
    }

    /// Returns the number of complete-key matches.
    #[must_use]
    pub const fn hits(self) -> u64 {
        self.hits
    }

    /// Returns complete-key misses derived from probes and hits.
    #[must_use]
    pub const fn misses(self) -> u64 {
        self.probes.saturating_sub(self.hits)
    }

    /// Returns exact scores reused by probes.
    #[must_use]
    pub const fn exact_hits(self) -> u64 {
        self.exact_hits
    }

    /// Returns lower-bound fail-high cutoffs reused by probes.
    #[must_use]
    pub const fn lower_bound_cutoffs(self) -> u64 {
        self.lower_bound_cutoffs
    }

    /// Returns upper-bound fail-low cutoffs reused by probes.
    #[must_use]
    pub const fn upper_bound_cutoffs(self) -> u64 {
        self.upper_bound_cutoffs
    }

    /// Returns all store calls.
    #[must_use]
    pub const fn stores(self) -> u64 {
        self.stores
    }

    /// Returns stores that updated an existing complete-key match.
    #[must_use]
    pub const fn same_key_updates(self) -> u64 {
        self.same_key_updates
    }

    /// Returns stores that occupied an empty cluster slot.
    #[must_use]
    pub const fn empty_inserts(self) -> u64 {
        self.empty_inserts
    }

    /// Returns stores that evicted a different-key entry.
    #[must_use]
    pub const fn collision_replacements(self) -> u64 {
        self.collision_replacements
    }

    /// Returns the field-wise saturating sum of two snapshots.
    #[must_use]
    pub const fn saturating_add(self, other: Self) -> Self {
        Self {
            probes: self.probes.saturating_add(other.probes),
            hits: self.hits.saturating_add(other.hits),
            exact_hits: self.exact_hits.saturating_add(other.exact_hits),
            lower_bound_cutoffs: self
                .lower_bound_cutoffs
                .saturating_add(other.lower_bound_cutoffs),
            upper_bound_cutoffs: self
                .upper_bound_cutoffs
                .saturating_add(other.upper_bound_cutoffs),
            stores: self.stores.saturating_add(other.stores),
            same_key_updates: self.same_key_updates.saturating_add(other.same_key_updates),
            empty_inserts: self.empty_inserts.saturating_add(other.empty_inserts),
            collision_replacements: self
                .collision_replacements
                .saturating_add(other.collision_replacements),
        }
    }

    pub(super) fn record_probe(&mut self) {
        self.probes = self.probes.saturating_add(1);
    }

    pub(super) fn record_hit(&mut self) {
        self.hits = self.hits.saturating_add(1);
    }

    pub(super) fn record_exact_hit(&mut self) {
        self.exact_hits = self.exact_hits.saturating_add(1);
    }

    pub(super) fn record_lower_bound_cutoff(&mut self) {
        self.lower_bound_cutoffs = self.lower_bound_cutoffs.saturating_add(1);
    }

    pub(super) fn record_upper_bound_cutoff(&mut self) {
        self.upper_bound_cutoffs = self.upper_bound_cutoffs.saturating_add(1);
    }

    pub(super) fn record_store(&mut self) {
        self.stores = self.stores.saturating_add(1);
    }

    pub(super) fn record_same_key_update(&mut self) {
        self.same_key_updates = self.same_key_updates.saturating_add(1);
    }

    pub(super) fn record_empty_insert(&mut self) {
        self.empty_inserts = self.empty_inserts.saturating_add(1);
    }

    pub(super) fn record_collision_replacement(&mut self) {
        self.collision_replacements = self.collision_replacements.saturating_add(1);
    }
}

/// Bounded, deterministic estimate of current-generation table occupancy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionHashFull {
    sampled_slots: usize,
    occupied_current_generation: usize,
}

impl TranspositionHashFull {
    const fn new(sampled_slots: usize, occupied_current_generation: usize) -> Self {
        Self {
            sampled_slots,
            occupied_current_generation,
        }
    }

    /// Returns the number of slots inspected, never more than 1,000.
    #[must_use]
    pub const fn sampled_slots(self) -> usize {
        self.sampled_slots
    }

    /// Returns sampled slots occupied by entries from the current generation.
    #[must_use]
    pub const fn occupied_current_generation(self) -> usize {
        self.occupied_current_generation
    }

    /// Returns the current-generation occupancy estimate in per mille.
    #[must_use]
    pub const fn per_mille(self) -> u16 {
        if self.sampled_slots == 0 {
            return 0;
        }
        ((self.occupied_current_generation * 1_000) / self.sampled_slots) as u16
    }
}

impl TranspositionTable {
    /// Returns a copy of all current diagnostic counters.
    #[must_use]
    pub const fn diagnostics(&self) -> TranspositionTableDiagnostics {
        self.diagnostics
    }

    /// Resets diagnostic counters without changing allocation, entries, or generation.
    pub fn reset_diagnostics(&mut self) {
        self.diagnostics = TranspositionTableDiagnostics::default();
    }

    /// Samples at most 1,000 evenly distributed slots for current-generation occupancy.
    ///
    /// The bounded scan is deterministic for a fixed table state and never walks
    /// the entire table when capacity exceeds the sample limit.
    #[must_use]
    pub fn hash_full(&self) -> TranspositionHashFull {
        let capacity = self.entry_capacity();
        let sampled_slots = capacity.min(TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT);
        let mut occupied_current_generation = 0;

        for sample_index in 0..sampled_slots {
            let flat_index = sampled_flat_index(sample_index, capacity, sampled_slots);
            let cluster_index = flat_index / TRANSPOSITION_CLUSTER_SIZE;
            let slot_index = flat_index % TRANSPOSITION_CLUSTER_SIZE;
            if self.clusters[cluster_index].entries[slot_index]
                .is_some_and(|entry| entry.generation() == self.generation)
            {
                occupied_current_generation += 1;
            }
        }

        TranspositionHashFull::new(sampled_slots, occupied_current_generation)
    }
}

fn sampled_flat_index(sample_index: usize, capacity: usize, sampled_slots: usize) -> usize {
    let base_width = capacity / sampled_slots;
    let wider_segments = capacity % sampled_slots;
    sample_index * base_width + sample_index.min(wider_segments)
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Square};

    use super::{
        sampled_flat_index, TranspositionTableDiagnostics, TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,
    };
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionProbeError,
        TranspositionProbeRequest, TranspositionScore, TranspositionScoreReuse, TranspositionTable,
        TRANSPOSITION_CLUSTER_SIZE,
    };

    fn square(text: &str) -> Square {
        text.parse().expect("diagnostic-test square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("g1"), square("f3"), MoveKind::Quiet)
    }

    fn entry(
        verification_key: u64,
        depth: u16,
        bound: TranspositionBound,
        score: i32,
        generation: u8,
    ) -> TranspositionEntry {
        TranspositionEntry::new(
            verification_key,
            depth,
            bound,
            TranspositionScore::normalize(Score::from_evaluation(score), 0)
                .expect("diagnostic score normalizes"),
            Some(best_move()),
            generation,
        )
    }

    fn request(
        verification_key: u64,
        alpha: i32,
        beta: i32,
        score_reuse: TranspositionScoreReuse,
    ) -> TranspositionProbeRequest {
        TranspositionProbeRequest::new(
            verification_key,
            4,
            0,
            Score::from_evaluation(alpha),
            Score::from_evaluation(beta),
            score_reuse,
        )
    }

    #[test]
    fn probe_snapshot_counts_verified_and_reusable_outcomes() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let exact_key = 11;
        let lower_key = 13;
        let upper_key = 17;
        table.store(entry(exact_key, 8, TranspositionBound::Exact, 25, 99));
        table.store(entry(lower_key, 8, TranspositionBound::Lower, 80, 99));
        table.store(entry(upper_key, 8, TranspositionBound::Upper, -80, 99));
        table.reset_diagnostics();

        let invalid = TranspositionProbeRequest::new(
            exact_key,
            4,
            0,
            Score::from_evaluation(5),
            Score::from_evaluation(5),
            TranspositionScoreReuse::Allowed,
        );
        assert!(matches!(
            table.probe(invalid),
            Err(TranspositionProbeError::InvalidWindow { .. })
        ));
        assert_eq!(
            table.diagnostics(),
            TranspositionTableDiagnostics::default()
        );

        assert_eq!(
            table
                .probe(request(19, -100, 100, TranspositionScoreReuse::Allowed))
                .expect("miss probe succeeds"),
            None
        );
        table
            .probe(request(
                exact_key,
                -100,
                100,
                TranspositionScoreReuse::Allowed,
            ))
            .expect("exact probe succeeds");
        table
            .probe(request(
                lower_key,
                -50,
                50,
                TranspositionScoreReuse::Allowed,
            ))
            .expect("lower cutoff succeeds");
        table
            .probe(request(
                lower_key,
                -50,
                100,
                TranspositionScoreReuse::Allowed,
            ))
            .expect("lower non-cutoff succeeds");
        table
            .probe(request(
                upper_key,
                -50,
                50,
                TranspositionScoreReuse::Allowed,
            ))
            .expect("upper cutoff succeeds");
        table
            .probe(request(
                exact_key,
                -100,
                100,
                TranspositionScoreReuse::SuppressedForRepetition,
            ))
            .expect("suppressed probe succeeds");

        let diagnostics = table.diagnostics();
        assert_eq!(diagnostics.probes(), 6);
        assert_eq!(diagnostics.hits(), 5);
        assert_eq!(diagnostics.misses(), 1);
        assert_eq!(diagnostics.exact_hits(), 1);
        assert_eq!(diagnostics.lower_bound_cutoffs(), 1);
        assert_eq!(diagnostics.upper_bound_cutoffs(), 1);
    }

    #[test]
    fn store_snapshot_classifies_every_deterministic_action_and_resets() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let base_key = 29;
        table.store(entry(base_key, 8, TranspositionBound::Exact, 0, 0));
        table.store(entry(base_key, 9, TranspositionBound::Exact, 1, 0));
        for offset in 1..TRANSPOSITION_CLUSTER_SIZE {
            let key = base_key + table.cluster_count() as u64 * offset as u64;
            table.store(entry(key, 8, TranspositionBound::Exact, 0, 0));
        }
        let replacement_key =
            base_key + table.cluster_count() as u64 * TRANSPOSITION_CLUSTER_SIZE as u64;
        table.store(entry(replacement_key, 12, TranspositionBound::Exact, 0, 0));

        let diagnostics = table.diagnostics();
        assert_eq!(diagnostics.stores(), 6);
        assert_eq!(diagnostics.same_key_updates(), 1);
        assert_eq!(diagnostics.empty_inserts(), 4);
        assert_eq!(diagnostics.collision_replacements(), 1);

        let hash_full_before_reset = table.hash_full();
        table.reset_diagnostics();
        assert_eq!(
            table.diagnostics(),
            TranspositionTableDiagnostics::default()
        );
        assert_eq!(table.hash_full(), hash_full_before_reset);
        assert!(table
            .probe(request(
                replacement_key,
                -100,
                100,
                TranspositionScoreReuse::Allowed,
            ))
            .expect("entry remains after reset")
            .is_some());
    }

    #[test]
    fn hash_full_sampling_is_bounded_deterministic_and_generation_aware() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let capacity = table.entry_capacity();
        let sampled_slots = capacity.min(TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT);
        assert_eq!(table.hash_full().sampled_slots(), sampled_slots);
        assert_eq!(table.hash_full().per_mille(), 0);

        for sample_index in 0..sampled_slots {
            let flat_index = sampled_flat_index(sample_index, capacity, sampled_slots);
            let cluster_index = flat_index / TRANSPOSITION_CLUSTER_SIZE;
            let slot_index = flat_index % TRANSPOSITION_CLUSTER_SIZE;
            table.clusters[cluster_index].entries[slot_index] = Some(entry(
                flat_index as u64 + 1,
                1,
                TranspositionBound::Exact,
                0,
                0,
            ));
        }
        let full = table.hash_full();
        assert_eq!(full.sampled_slots(), sampled_slots);
        assert_eq!(full.occupied_current_generation(), sampled_slots);
        assert_eq!(full.per_mille(), 1_000);
        assert_eq!(table.hash_full(), full);

        table.advance_generation();
        assert_eq!(table.hash_full().per_mille(), 0);
        for sample_index in 0..sampled_slots / 2 {
            let flat_index = sampled_flat_index(sample_index, capacity, sampled_slots);
            let cluster_index = flat_index / TRANSPOSITION_CLUSTER_SIZE;
            let slot_index = flat_index % TRANSPOSITION_CLUSTER_SIZE;
            table.clusters[cluster_index].entries[slot_index] = Some(entry(
                flat_index as u64 + 1,
                1,
                TranspositionBound::Exact,
                0,
                table.generation(),
            ));
        }
        let half = table.hash_full();
        assert_eq!(half.occupied_current_generation(), sampled_slots / 2);
        assert_eq!(half.per_mille(), 500);
    }
}
