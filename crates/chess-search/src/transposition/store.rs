use core::cmp::Reverse;

use super::{
    TranspositionCluster, TranspositionEntry, TranspositionTable, TRANSPOSITION_CLUSTER_SIZE,
};

/// How one transposition-table store changed its selected cluster.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionStoreAction {
    /// An existing complete-key match was updated in place.
    UpdatedSameKey {
        /// Entry replaced by the new observation.
        previous_entry: TranspositionEntry,
    },
    /// The new entry occupied the lowest-index empty slot.
    InsertedEmpty,
    /// A different-key entry was displaced from a full cluster.
    ReplacedCollision {
        /// Entry selected by the deterministic replacement policy.
        evicted_entry: TranspositionEntry,
    },
}

/// Exact cluster and slot selected by one transposition-table store.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionStoreResult {
    cluster_index: usize,
    slot_index: usize,
    action: TranspositionStoreAction,
}

impl TranspositionStoreResult {
    const fn new(
        cluster_index: usize,
        slot_index: usize,
        action: TranspositionStoreAction,
    ) -> Self {
        Self {
            cluster_index,
            slot_index,
            action,
        }
    }

    /// Returns the selected collision-cluster index.
    #[must_use]
    pub const fn cluster_index(self) -> usize {
        self.cluster_index
    }

    /// Returns the selected slot index within the four-entry cluster.
    #[must_use]
    pub const fn slot_index(self) -> usize {
        self.slot_index
    }

    /// Returns whether the store updated, inserted, or displaced an entry.
    #[must_use]
    pub const fn action(self) -> TranspositionStoreAction {
        self.action
    }
}

impl TranspositionTable {
    /// Stores one normalized entry using deterministic cluster replacement.
    ///
    /// The table generation is authoritative and replaces the generation carried
    /// by `entry`. A complete-key match is updated in its existing slot. Otherwise
    /// the lowest-index empty slot is used. A full collision cluster evicts the
    /// shallowest entry; equal depths prefer the oldest modulo-256 generation,
    /// and a remaining tie selects the lowest slot index.
    pub fn store(&mut self, entry: TranspositionEntry) -> TranspositionStoreResult {
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
}

fn collision_victim_slot(cluster: &TranspositionCluster, current_generation: u8) -> usize {
    cluster
        .entries
        .iter()
        .enumerate()
        .filter_map(|(slot_index, entry)| {
            (*entry).map(|entry| {
                let age = current_generation.wrapping_sub(entry.generation());
                (slot_index, entry.depth(), age)
            })
        })
        .min_by_key(|(slot_index, depth, age)| (*depth, Reverse(*age), *slot_index))
        .map(|(slot_index, _, _)| slot_index)
        .expect("full transposition cluster has a replacement candidate")
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Square};

    use super::{TranspositionStoreAction, TRANSPOSITION_CLUSTER_SIZE};
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
    };

    fn square(text: &str) -> Square {
        text.parse().expect("store-test square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("g1"), square("f3"), MoveKind::Quiet)
    }

    fn entry(verification_key: u64, depth: u16) -> TranspositionEntry {
        TranspositionEntry::new(
            verification_key,
            depth,
            TranspositionBound::Exact,
            TranspositionScore::from_normalized(Score::from_evaluation(i32::from(depth))),
            Some(best_move()),
            211,
        )
    }

    fn colliding_key(table: &TranspositionTable, base_key: u64, collision_offset: u64) -> u64 {
        base_key + table.cluster_count() as u64 * collision_offset
    }

    fn selected_cluster(
        table: &TranspositionTable,
        verification_key: u64,
    ) -> [Option<TranspositionEntry>; TRANSPOSITION_CLUSTER_SIZE] {
        table.clusters[table.cluster_index(verification_key)].entries
    }

    #[test]
    fn same_key_updates_in_place_without_creating_a_duplicate() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 17;
        let first = table.store(entry(key, 14));
        assert_eq!(first.slot_index(), 0);
        assert_eq!(first.action(), TranspositionStoreAction::InsertedEmpty);

        table.advance_generation();
        let update = table.store(entry(key, 4));
        let previous_entry = match update.action() {
            TranspositionStoreAction::UpdatedSameKey { previous_entry } => previous_entry,
            other => panic!("expected same-key update, received {other:?}"),
        };
        let slots = selected_cluster(&table, key);

        assert_eq!(update.cluster_index(), table.cluster_index(key));
        assert_eq!(update.slot_index(), 0);
        assert_eq!(previous_entry.depth(), 14);
        assert_eq!(previous_entry.generation(), 0);
        assert_eq!(
            slots
                .iter()
                .flatten()
                .filter(|stored| stored.verification_key() == key)
                .count(),
            1
        );
        assert_eq!(slots[0].expect("updated slot").depth(), 4);
        assert_eq!(slots[0].expect("updated slot").generation(), 1);
    }

    #[test]
    fn empty_slots_are_filled_in_stable_lowest_index_order() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let base_key = 23;

        for expected_slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            let key = colliding_key(&table, base_key, expected_slot as u64);
            let result = table.store(entry(key, 8));
            assert_eq!(result.cluster_index(), table.cluster_index(base_key));
            assert_eq!(result.slot_index(), expected_slot);
            assert_eq!(result.action(), TranspositionStoreAction::InsertedEmpty);
        }
    }

    #[test]
    fn full_cluster_replaces_shallowest_entry_before_considering_age() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let base_key = 31;
        let depths = [9, 3, 6, 8];
        let generations = [0, 10, 0, 0];

        for slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            table.generation = generations[slot];
            let key = colliding_key(&table, base_key, slot as u64);
            assert_eq!(table.store(entry(key, depths[slot])).slot_index(), slot);
        }

        table.generation = 10;
        let before = selected_cluster(&table, base_key);
        let incoming_key = colliding_key(&table, base_key, 4);
        let result = table.store(entry(incoming_key, 1));
        let evicted_entry = match result.action() {
            TranspositionStoreAction::ReplacedCollision { evicted_entry } => evicted_entry,
            other => panic!("expected collision replacement, received {other:?}"),
        };
        let after = selected_cluster(&table, base_key);

        assert_eq!(result.slot_index(), 1);
        assert_eq!(evicted_entry, before[1].expect("victim exists"));
        assert_eq!(evicted_entry.depth(), 3);
        assert_eq!(after[0], before[0]);
        assert_eq!(after[2], before[2]);
        assert_eq!(after[3], before[3]);
        assert_eq!(
            after[1].expect("replacement exists").verification_key(),
            incoming_key
        );
        assert_eq!(after[1].expect("replacement exists").generation(), 10);
    }

    #[test]
    fn equal_depth_prefers_oldest_generation_across_wraparound() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let base_key = 41;
        let generations = [1, u8::MAX, 0, 2];

        for slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            table.generation = generations[slot];
            let key = colliding_key(&table, base_key, slot as u64);
            table.store(entry(key, 7));
        }

        table.generation = 2;
        let before = selected_cluster(&table, base_key);
        let result = table.store(entry(colliding_key(&table, base_key, 4), 11));
        let evicted_entry = match result.action() {
            TranspositionStoreAction::ReplacedCollision { evicted_entry } => evicted_entry,
            other => panic!("expected collision replacement, received {other:?}"),
        };

        assert_eq!(result.slot_index(), 1);
        assert_eq!(evicted_entry, before[1].expect("oldest entry exists"));
        assert_eq!(evicted_entry.generation(), u8::MAX);
        assert_eq!(2_u8.wrapping_sub(evicted_entry.generation()), 3);
    }

    #[test]
    fn equal_depth_and_age_use_lowest_slot_as_final_tie_break() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let base_key = 53;
        table.generation = 19;

        for slot in 0..TRANSPOSITION_CLUSTER_SIZE {
            let key = colliding_key(&table, base_key, slot as u64);
            table.store(entry(key, 5));
        }

        let before = selected_cluster(&table, base_key);
        let result = table.store(entry(colliding_key(&table, base_key, 4), 12));
        let evicted_entry = match result.action() {
            TranspositionStoreAction::ReplacedCollision { evicted_entry } => evicted_entry,
            other => panic!("expected collision replacement, received {other:?}"),
        };

        assert_eq!(result.slot_index(), 0);
        assert_eq!(evicted_entry, before[0].expect("tie-break victim exists"));
    }
}
