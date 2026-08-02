/// Cooperative cancellation source for recursive search.
///
/// Search calls this probe at node and child boundaries. Returning `true`
/// requests an orderly unwind: active line-history entries are popped and
/// active position moves are unmade before the cancellation error reaches the
/// root. The probe does not define time limits, node limits, partial results,
/// or iterative-deepening policy.
pub trait SearchCancellationProbe {
    /// Returns whether the current search should stop.
    fn should_cancel(&mut self) -> bool;
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
