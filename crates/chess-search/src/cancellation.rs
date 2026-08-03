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
    /// The default preserves the historical callback contract. Limit-aware
    /// controllers override this hook to account one node before searching it.
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
