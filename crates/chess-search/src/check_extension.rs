use crate::MAX_MATE_PLY;

/// Maximum number of check extensions permitted on one root-to-leaf path.
///
/// Task 16.7 deliberately permits exactly one additional ply. The remaining
/// budget is passed by value to each child, so sibling searches cannot consume
/// one another's allowance and checking sequences cannot extend without bound.
pub const MAX_CHECK_EXTENSIONS_PER_LINE: u16 = 1;

/// One observable check-extension decision.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckExtensionEvent {
    /// A checking move consumed the one-ply path budget.
    Applied,
    /// A checking move was observed after the path budget was already consumed.
    BudgetExhausted,
    /// A checking move could not extend beyond the supported mate-score ply domain.
    MateDomainBlocked,
}

/// Request-wide diagnostics for the optional bounded check extension.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct CheckExtensionDiagnostics {
    eligible_nodes: u64,
    applied_extensions: u64,
    budget_exhausted_nodes: u64,
    mate_domain_blocked_nodes: u64,
}

impl CheckExtensionDiagnostics {
    /// Returns checking child nodes considered by the enabled policy.
    #[must_use]
    pub const fn eligible_nodes(self) -> u64 {
        self.eligible_nodes
    }

    /// Returns one-ply extensions that were actually applied.
    #[must_use]
    pub const fn applied_extensions(self) -> u64 {
        self.applied_extensions
    }

    /// Returns eligible checking nodes skipped because the path budget was spent.
    #[must_use]
    pub const fn budget_exhausted_nodes(self) -> u64 {
        self.budget_exhausted_nodes
    }

    /// Returns eligible checking nodes skipped at the mate-score ply ceiling.
    #[must_use]
    pub const fn mate_domain_blocked_nodes(self) -> u64 {
        self.mate_domain_blocked_nodes
    }

    /// Returns whether no extension decision was observed.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.eligible_nodes == 0
    }

    pub(crate) fn record(&mut self, event: CheckExtensionEvent) {
        self.eligible_nodes = self.eligible_nodes.saturating_add(1);
        match event {
            CheckExtensionEvent::Applied => {
                self.applied_extensions = self.applied_extensions.saturating_add(1);
            }
            CheckExtensionEvent::BudgetExhausted => {
                self.budget_exhausted_nodes = self.budget_exhausted_nodes.saturating_add(1);
            }
            CheckExtensionEvent::MateDomainBlocked => {
                self.mate_domain_blocked_nodes = self.mate_domain_blocked_nodes.saturating_add(1);
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct CheckExtensionDecision {
    child_depth: u16,
    remaining_budget: u16,
    event: Option<CheckExtensionEvent>,
}

impl CheckExtensionDecision {
    pub(crate) const fn child_depth(self) -> u16 {
        self.child_depth
    }

    pub(crate) const fn remaining_budget(self) -> u16 {
        self.remaining_budget
    }

    pub(crate) const fn event(self) -> Option<CheckExtensionEvent> {
        self.event
    }
}

pub(crate) fn decide_check_extension(
    depth: u16,
    ply: u16,
    child_in_check: bool,
    enabled: bool,
    remaining_budget: u16,
) -> CheckExtensionDecision {
    debug_assert!(depth > 0);
    let nominal_child_depth = depth - 1;
    if !enabled || !child_in_check {
        return CheckExtensionDecision {
            child_depth: nominal_child_depth,
            remaining_budget,
            event: None,
        };
    }

    if remaining_budget == 0 {
        return CheckExtensionDecision {
            child_depth: nominal_child_depth,
            remaining_budget,
            event: Some(CheckExtensionEvent::BudgetExhausted),
        };
    }

    let nominal_leaf_ply = ply.checked_add(depth);
    if nominal_leaf_ply.is_none() || nominal_leaf_ply == Some(MAX_MATE_PLY) {
        return CheckExtensionDecision {
            child_depth: nominal_child_depth,
            remaining_budget,
            event: Some(CheckExtensionEvent::MateDomainBlocked),
        };
    }

    CheckExtensionDecision {
        child_depth: depth,
        remaining_budget: remaining_budget - 1,
        event: Some(CheckExtensionEvent::Applied),
    }
}

#[cfg(test)]
mod tests {
    use super::{decide_check_extension, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE};
    use crate::MAX_MATE_PLY;

    #[test]
    fn one_check_consumes_the_complete_path_budget() {
        let decision = decide_check_extension(3, 2, true, true, MAX_CHECK_EXTENSIONS_PER_LINE);
        assert_eq!(decision.child_depth(), 3);
        assert_eq!(decision.remaining_budget(), 0);
        assert_eq!(decision.event(), Some(CheckExtensionEvent::Applied));

        let exhausted = decide_check_extension(
            decision.child_depth(),
            3,
            true,
            true,
            decision.remaining_budget(),
        );
        assert_eq!(exhausted.child_depth(), 2);
        assert_eq!(exhausted.remaining_budget(), 0);
        assert_eq!(
            exhausted.event(),
            Some(CheckExtensionEvent::BudgetExhausted)
        );
    }

    #[test]
    fn disabled_and_nonchecking_children_never_extend() {
        let disabled = decide_check_extension(2, 0, true, false, 1);
        assert_eq!(disabled.child_depth(), 1);
        assert_eq!(disabled.remaining_budget(), 1);
        assert_eq!(disabled.event(), None);

        let quiet = decide_check_extension(2, 0, false, true, 1);
        assert_eq!(quiet.child_depth(), 1);
        assert_eq!(quiet.remaining_budget(), 1);
        assert_eq!(quiet.event(), None);
    }

    #[test]
    fn mate_score_domain_prevents_an_extra_ply() {
        let blocked = decide_check_extension(MAX_MATE_PLY, 0, true, true, 1);
        assert_eq!(blocked.child_depth(), MAX_MATE_PLY - 1);
        assert_eq!(blocked.remaining_budget(), 1);
        assert_eq!(
            blocked.event(),
            Some(CheckExtensionEvent::MateDomainBlocked)
        );
    }
}
