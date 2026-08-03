/// Maximum production-node interval between cooperative cancellation checks.
///
/// The current correctness-first policy checks every alpha-beta and quiescence
/// node. Child boundaries also check before applying the next move, so an
/// observed request cannot require completion of an arbitrary subtree or depth.
pub const CANCELLATION_CHECK_INTERVAL_NODES: u64 = 1;

/// Cooperative cancellation source for recursive search.
///
/// Search calls `on_node` exactly once for each production node and calls
/// `should_cancel` at child boundaries. Returning `true` requests an orderly
/// unwind: active line-history entries are popped and active position moves are
/// unmade before the cancellation error reaches the root.
pub trait SearchCancellationProbe {
    /// Returns whether the current search should stop at a non-node checkpoint.
    fn should_cancel(&mut self) -> bool;

    /// Enters one production search node and returns whether it should stop.
    ///
    /// The default checks the source for every node, which satisfies
    /// [`CANCELLATION_CHECK_INTERVAL_NODES`]. Limit-aware controllers override
    /// this hook to account one node while retaining the same polling bound.
    fn on_node(&mut self) -> bool {
        self.should_cancel()
    }
}

impl<Callback> SearchCancellationProbe for Callback
where
    Callback: FnMut() -> bool,
{
    fn should_cancel(&mut self) -> bool {
        self()
    }
}

#[derive(Default)]
pub(crate) struct NeverCancelled;

impl SearchCancellationProbe for NeverCancelled {
    fn should_cancel(&mut self) -> bool {
        false
    }
}
