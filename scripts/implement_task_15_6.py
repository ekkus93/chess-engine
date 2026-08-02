from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1))


diagnostics = r'''use super::{
    TranspositionEntry, TranspositionTable, TRANSPOSITION_CLUSTER_SIZE,
};

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
        sampled_flat_index, TranspositionTableDiagnostics,
        TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,
    };
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionProbeError,
        TranspositionProbeRequest, TranspositionScore, TranspositionScoreReuse,
        TranspositionTable, TRANSPOSITION_CLUSTER_SIZE,
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
        table.store(entry(
            exact_key,
            8,
            TranspositionBound::Exact,
            25,
            99,
        ));
        table.store(entry(
            lower_key,
            8,
            TranspositionBound::Lower,
            80,
            99,
        ));
        table.store(entry(
            upper_key,
            8,
            TranspositionBound::Upper,
            -80,
            99,
        ));
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
        assert_eq!(table.diagnostics(), TranspositionTableDiagnostics::default());

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
        table.store(entry(
            base_key,
            8,
            TranspositionBound::Exact,
            0,
            0,
        ));
        table.store(entry(
            base_key,
            9,
            TranspositionBound::Exact,
            1,
            0,
        ));
        for offset in 1..TRANSPOSITION_CLUSTER_SIZE {
            let key = base_key + table.cluster_count() as u64 * offset as u64;
            table.store(entry(key, 8, TranspositionBound::Exact, 0, 0));
        }
        let replacement_key =
            base_key + table.cluster_count() as u64 * TRANSPOSITION_CLUSTER_SIZE as u64;
        table.store(entry(
            replacement_key,
            12,
            TranspositionBound::Exact,
            0,
            0,
        ));

        let diagnostics = table.diagnostics();
        assert_eq!(diagnostics.stores(), 6);
        assert_eq!(diagnostics.same_key_updates(), 1);
        assert_eq!(diagnostics.empty_inserts(), 4);
        assert_eq!(diagnostics.collision_replacements(), 1);

        let hash_full_before_reset = table.hash_full();
        table.reset_diagnostics();
        assert_eq!(table.diagnostics(), TranspositionTableDiagnostics::default());
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
'''
(root / "crates/chess-search/src/transposition/diagnostics.rs").write_text(diagnostics)

replace_once(
    "crates/chess-search/src/transposition.rs",
    "mod probe;\nmod store;\npub use probe::{",
    "mod diagnostics;\nmod probe;\nmod store;\npub use diagnostics::{\n    TranspositionHashFull, TranspositionTableDiagnostics,\n    TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,\n};\npub use probe::{",
)
replace_once(
    "crates/chess-search/src/transposition.rs",
    "    allocated_bytes: usize,\n}",
    "    allocated_bytes: usize,\n    diagnostics: TranspositionTableDiagnostics,\n}",
)
replace_once(
    "crates/chess-search/src/transposition.rs",
    "            requested_mebibytes: mebibytes,\n            allocated_bytes,\n        })",
    "            requested_mebibytes: mebibytes,\n            allocated_bytes,\n            diagnostics: TranspositionTableDiagnostics::default(),\n        })",
)

old_probe = r'''    pub fn probe(
        &self,
        request: TranspositionProbeRequest,
    ) -> Result<Option<TranspositionProbeResult>, TranspositionProbeError> {
        if request.alpha() >= request.beta() {
            return Err(TranspositionProbeError::InvalidWindow {
                alpha: request.alpha(),
                beta: request.beta(),
            });
        }

        let cluster = &self.clusters[self.cluster_index(request.verification_key())];
        let Some(entry) = cluster
            .entries
            .iter()
            .flatten()
            .copied()
            .find(|entry| entry.verification_key() == request.verification_key())
        else {
            return Ok(None);
        };

        let score = reusable_score(entry, request)?;
        Ok(Some(TranspositionProbeResult::new(
            entry.best_move(),
            score,
        )))
    }
'''
new_probe = r'''    pub fn probe(
        &mut self,
        request: TranspositionProbeRequest,
    ) -> Result<Option<TranspositionProbeResult>, TranspositionProbeError> {
        if request.alpha() >= request.beta() {
            return Err(TranspositionProbeError::InvalidWindow {
                alpha: request.alpha(),
                beta: request.beta(),
            });
        }

        self.diagnostics.record_probe();
        let cluster = &self.clusters[self.cluster_index(request.verification_key())];
        let Some(entry) = cluster
            .entries
            .iter()
            .flatten()
            .copied()
            .find(|entry| entry.verification_key() == request.verification_key())
        else {
            return Ok(None);
        };

        self.diagnostics.record_hit();
        let score = reusable_score(entry, request)?;
        match score {
            Some(TranspositionProbeScore::Exact(_)) => self.diagnostics.record_exact_hit(),
            Some(TranspositionProbeScore::LowerBoundCutoff(_)) => {
                self.diagnostics.record_lower_bound_cutoff();
            }
            Some(TranspositionProbeScore::UpperBoundCutoff(_)) => {
                self.diagnostics.record_upper_bound_cutoff();
            }
            None => {}
        }
        Ok(Some(TranspositionProbeResult::new(
            entry.best_move(),
            score,
        )))
    }
'''
replace_once("crates/chess-search/src/transposition/probe.rs", old_probe, new_probe)
replace_once(
    "crates/chess-search/src/transposition/probe.rs",
    '        let table = TranspositionTable::new(1).expect("table allocates");\n        let alpha = Score::from_evaluation(25);',
    '        let mut table = TranspositionTable::new(1).expect("table allocates");\n        let alpha = Score::from_evaluation(25);',
)

old_store = r'''    pub fn store(&mut self, entry: TranspositionEntry) -> TranspositionStoreResult {
        let entry = entry.with_generation(self.generation);
        let cluster_index = self.cluster_index(entry.verification_key());
        let cluster = &mut self.clusters[cluster_index];

        if let Some(slot_index) = cluster.entries.iter().position(|slot| {
            slot.as_ref()
                .is_some_and(|stored| stored.verification_key() == entry.verification_key())
        }) {
            let previous_entry = cluster.entries[slot_index]
                .replace(entry)
                .expect("matching transposition slot is occupied");
            return TranspositionStoreResult::new(
                cluster_index,
                slot_index,
                TranspositionStoreAction::UpdatedSameKey { previous_entry },
            );
        }

        if let Some(slot_index) = cluster.entries.iter().position(Option::is_none) {
            cluster.entries[slot_index] = Some(entry);
            return TranspositionStoreResult::new(
                cluster_index,
                slot_index,
                TranspositionStoreAction::InsertedEmpty,
            );
        }

        let slot_index = collision_victim_slot(cluster, self.generation);
        let evicted_entry = cluster.entries[slot_index]
            .replace(entry)
            .expect("full transposition cluster has an occupied victim");
        TranspositionStoreResult::new(
            cluster_index,
            slot_index,
            TranspositionStoreAction::ReplacedCollision { evicted_entry },
        )
    }
'''
new_store = r'''    pub fn store(&mut self, entry: TranspositionEntry) -> TranspositionStoreResult {
        self.diagnostics.record_store();
        let entry = entry.with_generation(self.generation);
        let cluster_index = self.cluster_index(entry.verification_key());
        let cluster = &mut self.clusters[cluster_index];

        let result = if let Some(slot_index) = cluster.entries.iter().position(|slot| {
            slot.as_ref()
                .is_some_and(|stored| stored.verification_key() == entry.verification_key())
        }) {
            let previous_entry = cluster.entries[slot_index]
                .replace(entry)
                .expect("matching transposition slot is occupied");
            TranspositionStoreResult::new(
                cluster_index,
                slot_index,
                TranspositionStoreAction::UpdatedSameKey { previous_entry },
            )
        } else if let Some(slot_index) = cluster.entries.iter().position(Option::is_none) {
            cluster.entries[slot_index] = Some(entry);
            TranspositionStoreResult::new(
                cluster_index,
                slot_index,
                TranspositionStoreAction::InsertedEmpty,
            )
        } else {
            let slot_index = collision_victim_slot(cluster, self.generation);
            let evicted_entry = cluster.entries[slot_index]
                .replace(entry)
                .expect("full transposition cluster has an occupied victim");
            TranspositionStoreResult::new(
                cluster_index,
                slot_index,
                TranspositionStoreAction::ReplacedCollision { evicted_entry },
            )
        };

        match result.action() {
            TranspositionStoreAction::UpdatedSameKey { .. } => {
                self.diagnostics.record_same_key_update();
            }
            TranspositionStoreAction::InsertedEmpty => self.diagnostics.record_empty_insert(),
            TranspositionStoreAction::ReplacedCollision { .. } => {
                self.diagnostics.record_collision_replacement();
            }
        }
        result
    }
'''
replace_once("crates/chess-search/src/transposition/store.rs", old_store, new_store)

replace_once(
    "crates/chess-search/src/lib.rs",
    "    TranspositionStoreAction, TranspositionStoreResult, TranspositionTable,\n    TranspositionTableAllocationError, TRANSPOSITION_CLUSTER_SIZE,",
    "    TranspositionHashFull, TranspositionStoreAction, TranspositionStoreResult,\n    TranspositionTable, TranspositionTableAllocationError, TranspositionTableDiagnostics,\n    TRANSPOSITION_CLUSTER_SIZE, TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,",
)

replace_once(
    "crates/chess-tools/src/lib.rs",
    "    evaluate_term, evaluate_trace as search_evaluate_trace, EvaluationTerm, EvaluationTrace,\n    EvaluationWeightSet,\n};",
    "    evaluate_term, evaluate_trace as search_evaluate_trace, EvaluationTerm, EvaluationTrace,\n    EvaluationWeightSet, Score, TranspositionBound, TranspositionEntry, TranspositionProbeRequest,\n    TranspositionProbeScore, TranspositionScore, TranspositionScoreReuse, TranspositionStoreAction,\n    TranspositionTable,\n};",
)

benchmark_code = r'''
/// One stable transposition-table microbenchmark result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionBenchmarkRow {
    /// Stable operation name: `store` or `probe`.
    pub operation: &'static str,
    /// Number of timed operations performed.
    pub iterations: u64,
    /// Wall-clock duration in nanoseconds.
    pub elapsed_nanos: u128,
    /// Deterministic accumulator preventing dead-code elimination.
    pub checksum: u64,
}

const TRANSPOSITION_BENCHMARK_MEBIBYTES: usize = 1;
const TRANSPOSITION_BENCHMARK_FIXTURE_ENTRIES: usize = 4_096;

fn transposition_benchmark_key(index: u64) -> u64 {
    index
        .wrapping_mul(0x9e37_79b9_7f4a_7c15)
        .rotate_left(17)
        ^ 0xd1b5_4a32_d192_ed03
}

/// Benchmarks deterministic fixed-fixture transposition stores and probes.
///
/// Timing is informational and is not a correctness threshold. The checksum,
/// operation ordering, table size, fixture population, and three-hit/one-miss
/// probe pattern are deterministic for a fixed iteration count.
pub fn benchmark_transposition(
    iterations: u64,
) -> Result<Vec<TranspositionBenchmarkRow>, ToolError> {
    if iterations == 0 {
        return Err(ToolError::new(
            "transposition benchmark requires at least one iteration",
        ));
    }

    let normalized_zero = TranspositionScore::normalize(Score::ZERO, 0)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut store_table = TranspositionTable::new(TRANSPOSITION_BENCHMARK_MEBIBYTES)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let store_started = Instant::now();
    let mut store_checksum = 0_u64;
    for iteration in 0..iterations {
        let key = black_box(transposition_benchmark_key(iteration));
        let depth = u16::try_from(iteration % 64 + 1).expect("benchmark depth is bounded");
        let entry = TranspositionEntry::new(
            key,
            depth,
            TranspositionBound::Exact,
            normalized_zero,
            None,
            0,
        );
        let result = black_box(store_table.store(black_box(entry)));
        let action_code = match result.action() {
            TranspositionStoreAction::UpdatedSameKey { .. } => 1_u64,
            TranspositionStoreAction::InsertedEmpty => 2,
            TranspositionStoreAction::ReplacedCollision { .. } => 3,
        };
        store_checksum = store_checksum
            .wrapping_add(key)
            .wrapping_add(result.cluster_index() as u64)
            .wrapping_add(result.slot_index() as u64)
            .wrapping_add(action_code);
    }
    let store_row = TranspositionBenchmarkRow {
        operation: "store",
        iterations,
        elapsed_nanos: store_started.elapsed().as_nanos(),
        checksum: black_box(store_checksum),
    };

    let mut probe_table = TranspositionTable::new(TRANSPOSITION_BENCHMARK_MEBIBYTES)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let fixture_entries = probe_table
        .entry_capacity()
        .min(TRANSPOSITION_BENCHMARK_FIXTURE_ENTRIES);
    for fixture_index in 0..fixture_entries {
        let key = fixture_index as u64 * 2 + 1;
        probe_table.store(TranspositionEntry::new(
            key,
            32,
            TranspositionBound::Exact,
            normalized_zero,
            None,
            0,
        ));
    }
    probe_table.reset_diagnostics();

    let probe_started = Instant::now();
    let mut probe_checksum = 0_u64;
    for iteration in 0..iterations {
        let fixture_index = iteration % fixture_entries as u64;
        let key = fixture_index * 2 + if iteration & 3 == 3 { 2 } else { 1 };
        let request = TranspositionProbeRequest::new(
            key,
            16,
            0,
            Score::from_evaluation(-1_000),
            Score::from_evaluation(1_000),
            TranspositionScoreReuse::Allowed,
        );
        let result = black_box(probe_table.probe(black_box(request)))
            .map_err(|error| ToolError::new(error.to_string()))?;
        let result_code = match result {
            None => 1_u64,
            Some(hit) => match hit.score() {
                Some(TranspositionProbeScore::Exact(_)) => 2,
                Some(TranspositionProbeScore::LowerBoundCutoff(_)) => 3,
                Some(TranspositionProbeScore::UpperBoundCutoff(_)) => 4,
                None => 5,
            },
        };
        probe_checksum = probe_checksum
            .wrapping_add(key)
            .wrapping_add(result_code);
    }
    let probe_row = TranspositionBenchmarkRow {
        operation: "probe",
        iterations,
        elapsed_nanos: probe_started.elapsed().as_nanos(),
        checksum: black_box(probe_checksum),
    };

    Ok(vec![store_row, probe_row])
}

'''
replace_once(
    "crates/chess-tools/src/lib.rs",
    "fn sanitize_error(error: &ToolError) -> String {",
    benchmark_code + "fn sanitize_error(error: &ToolError) -> String {",
)
replace_once(
    "crates/chess-tools/src/lib.rs",
    "    use super::{divide, legal_uci, perft_fixtures, play_uci, run_oracle, STARTING_FEN};",
    "    use super::{\n        benchmark_transposition, divide, legal_uci, perft_fixtures, play_uci, run_oracle,\n        STARTING_FEN,\n    };",
)
replace_once(
    "crates/chess-tools/src/lib.rs",
    r'''    #[test]
    fn oracle_protocol_is_machine_readable() {
        let input = format!("perft\t2\t{STARTING_FEN}\nlegal\t{STARTING_FEN}\nquit\n");
        let mut output = Vec::new();
        run_oracle(Cursor::new(input), &mut output).expect("oracle stream succeeds");
        let output = String::from_utf8(output).expect("oracle output is UTF-8");
        let lines: Vec<_> = output.lines().collect();
        assert_eq!(lines[0], "ok\t400");
        assert!(lines[1].starts_with("ok\t"));
        assert_eq!(lines[2], "ok\tbye");
    }
}''',
    r'''    #[test]
    fn oracle_protocol_is_machine_readable() {
        let input = format!("perft\t2\t{STARTING_FEN}\nlegal\t{STARTING_FEN}\nquit\n");
        let mut output = Vec::new();
        run_oracle(Cursor::new(input), &mut output).expect("oracle stream succeeds");
        let output = String::from_utf8(output).expect("oracle output is UTF-8");
        let lines: Vec<_> = output.lines().collect();
        assert_eq!(lines[0], "ok\t400");
        assert!(lines[1].starts_with("ok\t"));
        assert_eq!(lines[2], "ok\tbye");
    }

    #[test]
    fn transposition_benchmark_fixtures_and_checksums_are_reproducible() {
        assert!(benchmark_transposition(0).is_err());
        let first = benchmark_transposition(128).expect("benchmark succeeds");
        let second = benchmark_transposition(128).expect("benchmark repeats");

        assert_eq!(first.len(), 2);
        assert_eq!(first[0].operation, "store");
        assert_eq!(first[1].operation, "probe");
        assert!(first.iter().all(|row| row.iterations == 128));
        assert_eq!(first[0].checksum, second[0].checksum);
        assert_eq!(first[1].checksum, second[1].checksum);
    }
}''',
)

replace_once(
    "crates/chess-tools/src/main.rs",
    "    benchmark_evaluation, deserialize_weight_set, divide, evaluation_trace, legal_uci, perft,\n    play_uci, run_oracle, serialize_weight_set, suite, STARTING_FEN,",
    "    benchmark_evaluation, benchmark_transposition, deserialize_weight_set, divide,\n    evaluation_trace, legal_uci, perft, play_uci, run_oracle, serialize_weight_set, suite,\n    STARTING_FEN,",
)
replace_once(
    "crates/chess-tools/src/main.rs",
    "  chess-tools eval-bench ITERATIONS [FEN]\\n  chess-tools weights-export",
    "  chess-tools eval-bench ITERATIONS [FEN]\\n  chess-tools tt-bench ITERATIONS\\n  chess-tools weights-export",
)
replace_once(
    "crates/chess-tools/src/main.rs",
    r'''        "weights-export" => {
            if arguments.len() != 1 {
                return Err(usage().to_owned());
            }
''',
    r'''        "tt-bench" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let iterations = parse_iterations(&arguments[1])?;
            for row in benchmark_transposition(iterations).map_err(|error| error.to_string())? {
                println!(
                    "{}\t{}\t{}\t{}",
                    row.operation, row.iterations, row.elapsed_nanos, row.checksum
                );
            }
        }
        "weights-export" => {
            if arguments.len() != 1 {
                return Err(usage().to_owned());
            }
''',
)

document = r'''# Rust Transposition-Table Diagnostics and Benchmarks

Task 15.6 adds bounded observability to the fixed-capacity transposition table without changing search or replacement semantics.

## Diagnostic snapshot

`TranspositionTable::diagnostics()` returns a copy of `TranspositionTableDiagnostics`. Every counter is a saturating `u64`; overflow stops at `u64::MAX` rather than wrapping or affecting engine behavior.

The snapshot reports:

- valid probes that reached table lookup;
- complete-key hits and derived misses;
- exact scores actually reused;
- lower-bound and upper-bound cutoffs actually reused;
- all stores;
- same-key updates;
- empty-slot insertions;
- different-key collision replacements.

An invalid alpha-beta window fails before lookup and is not counted as a probe. A complete-key match is counted as a hit even when depth, repetition sensitivity, or a non-cutting bound prevents score reuse. Exact and bound counters count only reusable score outcomes.

`TranspositionTable::reset_diagnostics()` clears the snapshot only. It does not clear entries, change generation, resize storage, or alter replacement order.

## Bounded hash-full estimate

`TranspositionTable::hash_full()` returns `TranspositionHashFull` with:

- sampled slot count;
- sampled slots occupied by the current generation;
- occupancy in per mille.

The scan inspects at most `TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT`, currently 1,000, evenly distributed flattened slots. Tables smaller than the limit inspect every slot. Older generations do not count as current hash fullness. Sampling is deterministic for a fixed table state, performs no allocation, and never scans an arbitrarily large table.

## Reproducible microbenchmarks

Run the release-mode benchmark with:

```text
cargo run --locked -p chess-tools --release -- tt-bench ITERATIONS
```

It prints two tab-separated rows:

```text
operation<TAB>iterations<TAB>elapsed_nanos<TAB>checksum
```

The `store` benchmark uses a fixed one-MiB table, deterministic keys, bounded depths, and the production replacement path. The `probe` benchmark preloads a fixed one-MiB table and executes a deterministic three-hit/one-miss pattern through the production probe path. Checksums and fixture behavior are reproducible for a fixed iteration count; wall-clock timing is informational and intentionally is not a cross-machine pass/fail threshold.

## Scope boundary

Task 15.6 does not connect the table to production alpha-beta. Fixed capacity, complete-key verification, mate normalization, repetition-sensitive score suppression, and deterministic replacement remain unchanged. Production integration and a correctness-plus-node-reduction witness belong to the overall Task 15 gate.
'''
(root / "docs/RUST_TRANSPOSITION_TABLE_DIAGNOSTICS.md").write_text(document)
