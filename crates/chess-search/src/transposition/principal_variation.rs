use chess_core::Move;

use super::{TranspositionBound, TranspositionTable};

impl TranspositionTable {
    /// Returns a complete-key, exact-bound move with sufficient remaining depth.
    ///
    /// Principal-variation reconstruction is observational: it does not mutate
    /// table diagnostics, generation, allocation, or replacement state.
    pub(crate) fn principal_variation_move(
        &self,
        verification_key: u64,
        required_depth: u16,
    ) -> Option<Move> {
        let cluster = &self.clusters[self.cluster_index(verification_key)];
        cluster
            .entries
            .iter()
            .flatten()
            .copied()
            .find(|entry| {
                entry.verification_key() == verification_key
                    && entry.bound() == TranspositionBound::Exact
                    && entry.depth() >= required_depth
            })
            .and_then(|entry| entry.best_move())
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Square};

    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn square(text: &str) -> Square {
        text.parse().expect("PV lookup square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush)
    }

    fn entry(
        key: u64,
        depth: u16,
        bound: TranspositionBound,
        current: Option<Move>,
    ) -> TranspositionEntry {
        TranspositionEntry::new(
            key,
            depth,
            bound,
            TranspositionScore::normalize(Score::ZERO, 0).expect("zero score normalizes"),
            current,
            0,
        )
    }

    #[test]
    fn lookup_requires_complete_key_exact_bound_depth_and_move() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key: u64 = 0x1234_5678_9abc_def0;
        let collision = key.wrapping_add(table.cluster_count() as u64);
        table.store(entry(
            collision,
            12,
            TranspositionBound::Exact,
            Some(best_move()),
        ));
        table.store(entry(key, 11, TranspositionBound::Lower, Some(best_move())));

        assert_eq!(table.principal_variation_move(key, 1), None);

        table.store(entry(key, 5, TranspositionBound::Exact, Some(best_move())));
        assert_eq!(table.principal_variation_move(key, 6), None);
        assert_eq!(table.principal_variation_move(key, 5), Some(best_move()));

        table.store(entry(key, 7, TranspositionBound::Exact, None));
        assert_eq!(table.principal_variation_move(key, 1), None);
    }

    #[test]
    fn lookup_does_not_change_search_diagnostics() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 9;
        table.store(entry(key, 3, TranspositionBound::Exact, Some(best_move())));
        table.reset_diagnostics();
        let before = table.diagnostics();

        assert_eq!(table.principal_variation_move(key, 3), Some(best_move()));
        assert_eq!(table.diagnostics(), before);
        assert_eq!(before, TranspositionTableDiagnostics::default());
    }
}
