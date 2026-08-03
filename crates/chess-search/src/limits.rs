use core::fmt;
use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::{Duration, Instant},
};

use crate::{
    CheckExtensionDiagnostics, CheckExtensionEvent, SearchCancellationProbe, MAX_MATE_PLY,
};

/// Thread-safe explicit stop signal shared with a running search.
#[derive(Clone, Debug, Default)]
pub struct SearchStopFlag {
    requested: Arc<AtomicBool>,
}

impl SearchStopFlag {
    /// Creates a clear stop flag.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Requests an orderly search stop.
    pub fn request_stop(&self) {
        self.requested.store(true, Ordering::Release);
    }

    /// Clears a previously requested stop before a new search begins.
    pub fn reset(&self) {
        self.requested.store(false, Ordering::Release);
    }

    /// Returns whether a stop has been requested.
    #[must_use]
    pub fn is_stop_requested(&self) -> bool {
        self.requested.load(Ordering::Acquire)
    }
}

/// Typed limits for one iterative-deepening request.
#[derive(Clone, Debug, Default)]
pub struct SearchLimits {
    depth: Option<u16>,
    nodes: Option<u64>,
    soft_time: Option<Duration>,
    hard_time: Option<Duration>,
    infinite: bool,
    stop_flag: Option<SearchStopFlag>,
    check_extension: bool,
}

impl SearchLimits {
    /// Creates an empty request that must be completed with at least one limit.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            depth: None,
            nodes: None,
            soft_time: None,
            hard_time: None,
            infinite: false,
            stop_flag: None,
            check_extension: false,
        }
    }

    /// Adds a maximum completed depth.
    #[must_use]
    pub const fn with_depth(mut self, depth: u16) -> Self {
        self.depth = Some(depth);
        self
    }

    /// Adds a hard cumulative node budget across all attempts and depths.
    #[must_use]
    pub const fn with_nodes(mut self, nodes: u64) -> Self {
        self.nodes = Some(nodes);
        self
    }

    /// Adds a soft time budget checked only after a fully completed iteration.
    #[must_use]
    pub const fn with_soft_time(mut self, soft_time: Duration) -> Self {
        self.soft_time = Some(soft_time);
        self
    }

    /// Adds a hard time budget checked through the production search tree.
    #[must_use]
    pub const fn with_hard_time(mut self, hard_time: Duration) -> Self {
        self.hard_time = Some(hard_time);
        self
    }

    /// Selects explicit infinite-search mode.
    ///
    /// Infinite mode rejects automatic depth, node, and time limits and
    /// requires a [`SearchStopFlag`].
    #[must_use]
    pub const fn infinite(mut self) -> Self {
        self.infinite = true;
        self
    }

    /// Adds a shared explicit stop signal.
    #[must_use]
    pub fn with_stop_flag(mut self, stop_flag: SearchStopFlag) -> Self {
        self.stop_flag = Some(stop_flag);
        self
    }

    /// Enables the optional one-ply-per-line check extension.
    #[must_use]
    pub const fn with_check_extension(mut self) -> Self {
        self.check_extension = true;
        self
    }

    /// Returns the requested maximum depth.
    #[must_use]
    pub const fn depth(&self) -> Option<u16> {
        self.depth
    }

    /// Returns the cumulative node budget.
    #[must_use]
    pub const fn nodes(&self) -> Option<u64> {
        self.nodes
    }

    /// Returns the soft time budget.
    #[must_use]
    pub const fn soft_time(&self) -> Option<Duration> {
        self.soft_time
    }

    /// Returns the hard time budget.
    #[must_use]
    pub const fn hard_time(&self) -> Option<Duration> {
        self.hard_time
    }

    /// Returns whether explicit infinite mode was selected.
    #[must_use]
    pub const fn is_infinite(&self) -> bool {
        self.infinite
    }

    /// Returns the shared stop flag, when configured.
    #[must_use]
    pub const fn stop_flag(&self) -> Option<&SearchStopFlag> {
        self.stop_flag.as_ref()
    }

    /// Returns whether the optional bounded check extension is enabled.
    #[must_use]
    pub const fn check_extension_enabled(&self) -> bool {
        self.check_extension
    }

    /// Validates all values and combinations without mutating search state.
    pub fn validate(&self) -> Result<(), SearchLimitError> {
        if let Some(depth) = self.depth {
            if depth == 0 {
                return Err(SearchLimitError::ZeroDepth);
            }
            if depth > MAX_MATE_PLY {
                return Err(SearchLimitError::DepthTooLarge {
                    depth,
                    maximum: MAX_MATE_PLY,
                });
            }
        }
        if self.nodes == Some(0) {
            return Err(SearchLimitError::ZeroNodes);
        }
        if self.soft_time == Some(Duration::ZERO) {
            return Err(SearchLimitError::ZeroSoftTime);
        }
        if self.hard_time == Some(Duration::ZERO) {
            return Err(SearchLimitError::ZeroHardTime);
        }
        if let (Some(soft), Some(hard)) = (self.soft_time, self.hard_time) {
            if soft > hard {
                return Err(SearchLimitError::SoftTimeExceedsHardTime { soft, hard });
            }
        }

        let has_automatic_limit = self.depth.is_some()
            || self.nodes.is_some()
            || self.soft_time.is_some()
            || self.hard_time.is_some();
        if self.infinite {
            if has_automatic_limit {
                return Err(SearchLimitError::InfiniteConflictsWithAutomaticLimit);
            }
            if self.stop_flag.is_none() {
                return Err(SearchLimitError::InfiniteRequiresStopFlag);
            }
        } else if !has_automatic_limit {
            return Err(SearchLimitError::NoAutomaticLimit);
        }

        Ok(())
    }
}

/// Invalid search-limit configuration.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchLimitError {
    /// Finite mode requires at least one automatic limit.
    NoAutomaticLimit,
    /// A depth limit of zero cannot complete an iteration.
    ZeroDepth,
    /// The requested depth exceeds the supported mate-distance domain.
    DepthTooLarge {
        /// Requested maximum depth.
        depth: u16,
        /// Largest supported depth.
        maximum: u16,
    },
    /// A zero-node request cannot enter the root node.
    ZeroNodes,
    /// A zero soft-time request is ambiguous and rejected.
    ZeroSoftTime,
    /// A zero hard-time request is ambiguous and rejected.
    ZeroHardTime,
    /// The soft budget must not exceed the hard budget.
    SoftTimeExceedsHardTime {
        /// Requested soft budget.
        soft: Duration,
        /// Requested hard budget.
        hard: Duration,
    },
    /// Infinite mode cannot be combined with automatic limits.
    InfiniteConflictsWithAutomaticLimit,
    /// Infinite mode requires an externally shareable stop flag.
    InfiniteRequiresStopFlag,
}

impl fmt::Display for SearchLimitError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NoAutomaticLimit => {
                formatter.write_str("finite search requires at least one automatic limit")
            }
            Self::ZeroDepth => formatter.write_str("search depth limit must be at least one"),
            Self::DepthTooLarge { depth, maximum } => write!(
                formatter,
                "search depth limit {depth} exceeds supported maximum {maximum}"
            ),
            Self::ZeroNodes => formatter.write_str("search node limit must be at least one"),
            Self::ZeroSoftTime => formatter.write_str("soft time limit must be nonzero"),
            Self::ZeroHardTime => formatter.write_str("hard time limit must be nonzero"),
            Self::SoftTimeExceedsHardTime { soft, hard } => write!(
                formatter,
                "soft time limit {soft:?} exceeds hard time limit {hard:?}"
            ),
            Self::InfiniteConflictsWithAutomaticLimit => formatter.write_str(
                "infinite search cannot include depth, node, soft-time, or hard-time limits",
            ),
            Self::InfiniteRequiresStopFlag => {
                formatter.write_str("infinite search requires an explicit stop flag")
            }
        }
    }
}

impl std::error::Error for SearchLimitError {}

/// Reason a limited iterative-deepening request stopped.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchLimitTermination {
    /// The requested completed depth was reached.
    Depth {
        /// Requested and completed depth.
        depth: u16,
    },
    /// The cumulative node budget was exhausted.
    Nodes {
        /// Configured node budget.
        nodes: u64,
    },
    /// A completed iteration crossed the soft budget.
    SoftTime {
        /// Configured soft budget.
        limit: Duration,
    },
    /// A tree checkpoint crossed the hard budget.
    HardTime {
        /// Configured hard budget.
        limit: Duration,
    },
    /// The shared explicit stop flag was set.
    ExplicitStop,
    /// An unbounded-by-depth request reached the engine's supported depth ceiling.
    MaximumSupportedDepth {
        /// Largest supported completed depth.
        depth: u16,
    },
}

pub(crate) trait SearchClock {
    fn elapsed(&self) -> Duration;
}

pub(crate) struct WallClock {
    started: Instant,
}

impl WallClock {
    pub(crate) fn start() -> Self {
        Self {
            started: Instant::now(),
        }
    }
}

impl SearchClock for WallClock {
    fn elapsed(&self) -> Duration {
        self.started.elapsed()
    }
}

pub(crate) struct SearchLimitController<Clock> {
    limits: SearchLimits,
    clock: Clock,
    visited_nodes: u64,
    visited_qnodes: u64,
    selective_depth: u16,
    check_extension_diagnostics: CheckExtensionDiagnostics,
    termination: Option<SearchLimitTermination>,
}

impl<Clock> SearchLimitController<Clock>
where
    Clock: SearchClock,
{
    pub(crate) fn new(limits: SearchLimits, clock: Clock) -> Result<Self, SearchLimitError> {
        limits.validate()?;
        Ok(Self {
            limits,
            clock,
            visited_nodes: 0,
            visited_qnodes: 0,
            selective_depth: 0,
            check_extension_diagnostics: CheckExtensionDiagnostics::default(),
            termination: None,
        })
    }

    pub(crate) const fn visited_nodes(&self) -> u64 {
        self.visited_nodes
    }

    pub(crate) const fn visited_qnodes(&self) -> u64 {
        self.visited_qnodes
    }

    pub(crate) const fn selective_depth(&self) -> u16 {
        self.selective_depth
    }

    pub(crate) const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {
        self.check_extension_diagnostics
    }

    pub(crate) fn elapsed(&self) -> Duration {
        self.clock.elapsed()
    }

    pub(crate) const fn termination(&self) -> Option<SearchLimitTermination> {
        self.termination
    }

    pub(crate) const fn iteration_ceiling(&self) -> u16 {
        match self.limits.depth {
            Some(depth) => depth,
            None => MAX_MATE_PLY,
        }
    }

    pub(crate) fn boundary_termination(
        &mut self,
        completed_depth: u16,
    ) -> Option<SearchLimitTermination> {
        if let Some(reason) = self.immediate_termination() {
            return Some(reason);
        }
        if self.limits.depth == Some(completed_depth) {
            return self.set_termination(SearchLimitTermination::Depth {
                depth: completed_depth,
            });
        }
        if completed_depth > 0 {
            if let Some(limit) = self.limits.soft_time {
                if self.clock.elapsed() >= limit {
                    return self.set_termination(SearchLimitTermination::SoftTime { limit });
                }
            }
        }
        if completed_depth == MAX_MATE_PLY && self.limits.depth.is_none() {
            return self.set_termination(SearchLimitTermination::MaximumSupportedDepth {
                depth: MAX_MATE_PLY,
            });
        }
        None
    }

    fn immediate_termination(&mut self) -> Option<SearchLimitTermination> {
        if let Some(reason) = self.termination {
            return Some(reason);
        }
        if self
            .limits
            .stop_flag
            .as_ref()
            .is_some_and(SearchStopFlag::is_stop_requested)
        {
            return self.set_termination(SearchLimitTermination::ExplicitStop);
        }
        if let Some(limit) = self.limits.hard_time {
            if self.clock.elapsed() >= limit {
                return self.set_termination(SearchLimitTermination::HardTime { limit });
            }
        }
        if let Some(nodes) = self.limits.nodes {
            if self.visited_nodes >= nodes {
                return self.set_termination(SearchLimitTermination::Nodes { nodes });
            }
        }
        None
    }

    fn set_termination(
        &mut self,
        reason: SearchLimitTermination,
    ) -> Option<SearchLimitTermination> {
        self.termination = Some(reason);
        self.termination
    }

    fn enter_node(&mut self, ply: u16, quiescence: bool) -> bool {
        if self.should_cancel() {
            return true;
        }
        self.visited_nodes = self.visited_nodes.saturating_add(1);
        if quiescence {
            self.visited_qnodes = self.visited_qnodes.saturating_add(1);
        }
        self.selective_depth = self.selective_depth.max(ply);
        false
    }
}

impl<Clock> SearchCancellationProbe for SearchLimitController<Clock>
where
    Clock: SearchClock,
{
    fn should_cancel(&mut self) -> bool {
        self.immediate_termination().is_some()
    }

    fn on_node(&mut self) -> bool {
        self.enter_node(0, false)
    }

    fn on_alpha_beta_node(&mut self, ply: u16) -> bool {
        self.enter_node(ply, false)
    }

    fn on_quiescence_node(&mut self, ply: u16) -> bool {
        self.enter_node(ply, true)
    }

    fn on_check_extension(&mut self, event: CheckExtensionEvent) {
        self.check_extension_diagnostics.record(event);
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::{SearchLimitError, SearchLimits, SearchStopFlag};
    use crate::MAX_MATE_PLY;

    #[test]
    fn invalid_values_and_combinations_are_rejected() {
        assert_eq!(
            SearchLimits::new().validate(),
            Err(SearchLimitError::NoAutomaticLimit)
        );
        assert_eq!(
            SearchLimits::new().with_depth(0).validate(),
            Err(SearchLimitError::ZeroDepth)
        );
        assert_eq!(
            SearchLimits::new().with_depth(MAX_MATE_PLY + 1).validate(),
            Err(SearchLimitError::DepthTooLarge {
                depth: MAX_MATE_PLY + 1,
                maximum: MAX_MATE_PLY,
            })
        );
        assert_eq!(
            SearchLimits::new().with_nodes(0).validate(),
            Err(SearchLimitError::ZeroNodes)
        );
        assert_eq!(
            SearchLimits::new()
                .with_soft_time(Duration::ZERO)
                .validate(),
            Err(SearchLimitError::ZeroSoftTime)
        );
        assert_eq!(
            SearchLimits::new()
                .with_hard_time(Duration::ZERO)
                .validate(),
            Err(SearchLimitError::ZeroHardTime)
        );
        assert_eq!(
            SearchLimits::new()
                .with_soft_time(Duration::from_millis(2))
                .with_hard_time(Duration::from_millis(1))
                .validate(),
            Err(SearchLimitError::SoftTimeExceedsHardTime {
                soft: Duration::from_millis(2),
                hard: Duration::from_millis(1),
            })
        );
        assert_eq!(
            SearchLimits::new().infinite().validate(),
            Err(SearchLimitError::InfiniteRequiresStopFlag)
        );
        assert_eq!(
            SearchLimits::new().infinite().with_depth(1).validate(),
            Err(SearchLimitError::InfiniteConflictsWithAutomaticLimit)
        );

        let stop = SearchStopFlag::new();
        assert!(SearchLimits::new()
            .infinite()
            .with_stop_flag(stop)
            .validate()
            .is_ok());
        assert!(!SearchLimits::new().with_depth(1).check_extension_enabled());
        assert!(SearchLimits::new()
            .with_depth(1)
            .with_check_extension()
            .check_extension_enabled());
    }

    #[test]
    fn stop_flag_clones_share_one_atomic_state() {
        let first = SearchStopFlag::new();
        let second = first.clone();
        assert!(!first.is_stop_requested());
        second.request_stop();
        assert!(first.is_stop_requested());
        first.reset();
        assert!(!second.is_stop_requested());
    }
}
