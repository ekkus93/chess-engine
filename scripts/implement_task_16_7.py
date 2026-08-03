from pathlib import Path
import sys

root = Path(sys.argv[1])


def read(path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(content: str, old: str, new: str, label: str) -> str:
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return content.replace(old, new, 1)


write(
    "crates/chess-search/src/check_extension.rs",
    r'''use crate::MAX_MATE_PLY;

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
                self.mate_domain_blocked_nodes =
                    self.mate_domain_blocked_nodes.saturating_add(1);
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
    use super::{
        decide_check_extension, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE,
    };
    use crate::MAX_MATE_PLY;

    #[test]
    fn one_check_consumes_the_complete_path_budget() {
        let decision = decide_check_extension(
            3,
            2,
            true,
            true,
            MAX_CHECK_EXTENSIONS_PER_LINE,
        );
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
''',
)

# cancellation.rs
path = "crates/chess-search/src/cancellation.rs"
content = read(path)
content = "use crate::CheckExtensionEvent;\n\n" + content
content = replace_once(
    content,
    "    fn on_quiescence_node(&mut self, _ply: u16) -> bool {\n        self.on_node()\n    }\n}",
    "    fn on_quiescence_node(&mut self, _ply: u16) -> bool {\n        self.on_node()\n    }\n\n    /// Records one optional bounded check-extension decision.\n    ///\n    /// The default is observationally inert. Limit-aware controllers override\n    /// this hook so diagnostics include completed and interrupted work.\n    fn on_check_extension(&mut self, _event: CheckExtensionEvent) {}\n}",
    "cancellation extension hook",
)
write(path, content)

# limits.rs
path = "crates/chess-search/src/limits.rs"
content = read(path)
content = replace_once(
    content,
    "use crate::{SearchCancellationProbe, MAX_MATE_PLY};",
    "use crate::{\n    CheckExtensionDiagnostics, CheckExtensionEvent, SearchCancellationProbe, MAX_MATE_PLY,\n};",
    "limits imports",
)
content = replace_once(
    content,
    "    infinite: bool,\n    stop_flag: Option<SearchStopFlag>,",
    "    infinite: bool,\n    stop_flag: Option<SearchStopFlag>,\n    check_extension: bool,",
    "limits field",
)
content = replace_once(
    content,
    "            infinite: false,\n            stop_flag: None,",
    "            infinite: false,\n            stop_flag: None,\n            check_extension: false,",
    "limits constructor",
)
content = replace_once(
    content,
    "    pub fn with_stop_flag(mut self, stop_flag: SearchStopFlag) -> Self {\n        self.stop_flag = Some(stop_flag);\n        self\n    }",
    "    pub fn with_stop_flag(mut self, stop_flag: SearchStopFlag) -> Self {\n        self.stop_flag = Some(stop_flag);\n        self\n    }\n\n    /// Enables the optional one-ply-per-line check extension.\n    #[must_use]\n    pub const fn with_check_extension(mut self) -> Self {\n        self.check_extension = true;\n        self\n    }",
    "limits builder",
)
content = replace_once(
    content,
    "    pub const fn stop_flag(&self) -> Option<&SearchStopFlag> {\n        self.stop_flag.as_ref()\n    }",
    "    pub const fn stop_flag(&self) -> Option<&SearchStopFlag> {\n        self.stop_flag.as_ref()\n    }\n\n    /// Returns whether the optional bounded check extension is enabled.\n    #[must_use]\n    pub const fn check_extension_enabled(&self) -> bool {\n        self.check_extension\n    }",
    "limits getter",
)
content = replace_once(
    content,
    "    selective_depth: u16,\n    termination: Option<SearchLimitTermination>,",
    "    selective_depth: u16,\n    check_extension_diagnostics: CheckExtensionDiagnostics,\n    termination: Option<SearchLimitTermination>,",
    "controller field",
)
content = replace_once(
    content,
    "            selective_depth: 0,\n            termination: None,",
    "            selective_depth: 0,\n            check_extension_diagnostics: CheckExtensionDiagnostics::default(),\n            termination: None,",
    "controller constructor",
)
content = replace_once(
    content,
    "    pub(crate) const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }",
    "    pub(crate) const fn selective_depth(&self) -> u16 {\n        self.selective_depth\n    }\n\n    pub(crate) const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }",
    "controller diagnostics getter",
)
content = replace_once(
    content,
    "    fn on_quiescence_node(&mut self, ply: u16) -> bool {\n        self.enter_node(ply, true)\n    }",
    "    fn on_quiescence_node(&mut self, ply: u16) -> bool {\n        self.enter_node(ply, true)\n    }\n\n    fn on_check_extension(&mut self, event: CheckExtensionEvent) {\n        self.check_extension_diagnostics.record(event);\n    }",
    "controller extension hook",
)
content = replace_once(
    content,
    "        let stop = SearchStopFlag::new();\n        assert!(SearchLimits::new()\n            .infinite()\n            .with_stop_flag(stop)\n            .validate()\n            .is_ok());",
    "        let stop = SearchStopFlag::new();\n        assert!(SearchLimits::new()\n            .infinite()\n            .with_stop_flag(stop)\n            .validate()\n            .is_ok());\n        assert!(!SearchLimits::new().with_depth(1).check_extension_enabled());\n        assert!(SearchLimits::new()\n            .with_depth(1)\n            .with_check_extension()\n            .check_extension_enabled());",
    "limits policy test",
)
write(path, content)

# transposition/probe.rs
path = "crates/chess-search/src/transposition/probe.rs"
content = read(path)
content = replace_once(
    content,
    "    /// Cached scores are suppressed because repetition history may affect value.\n    SuppressedForRepetition,",
    "    /// Cached scores are suppressed because repetition history may affect value.\n    SuppressedForRepetition,\n    /// Cached scores are suppressed because selective-extension budget is path-dependent.\n    SuppressedForSelectiveExtension,",
    "TT reuse variant",
)
content = replace_once(
    content,
    "    if request.score_reuse() == TranspositionScoreReuse::SuppressedForRepetition\n        || entry.depth() < request.required_depth()",
    "    if request.score_reuse() != TranspositionScoreReuse::Allowed\n        || entry.depth() < request.required_depth()",
    "TT reuse condition",
)
write(path, content)

# alpha_beta.rs
path = "crates/chess-search/src/alpha_beta.rs"
content = read(path)
content = replace_once(
    content,
    "    cancellation::NeverCancelled,\n    move_ordering::{ordered_legal_moves_with_state_and_tt_move, MoveOrdering, QuietOrderingState},",
    "    cancellation::NeverCancelled,\n    check_extension::{decide_check_extension, MAX_CHECK_EXTENSIONS_PER_LINE},\n    move_ordering::{ordered_legal_moves_with_state_and_tt_move, MoveOrdering, QuietOrderingState},",
    "alpha imports",
)
content = replace_once(
    content,
    "        AlphaBetaWindow::full(),\n        transposition_table,\n        cancellation,",
    "        AlphaBetaWindow::full(),\n        false,\n        transposition_table,\n        cancellation,",
    "default search policy",
)
content = replace_once(
    content,
    "    window: AlphaBetaWindow,\n    transposition_table: &mut TranspositionTable,",
    "    window: AlphaBetaWindow,\n    check_extension_enabled: bool,\n    transposition_table: &mut TranspositionTable,",
    "window function signature",
)
content = replace_once(
    content,
    "        window,\n        transposition_table,\n        cancellation,\n    )?;",
    "        window,\n        check_extension_enabled,\n        transposition_table,\n        cancellation,\n    )?;",
    "window function call",
)
content = replace_once(
    content,
    "    window: AlphaBetaWindow,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,\n) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>",
    "    window: AlphaBetaWindow,\n    check_extension_enabled: bool,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,\n) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>",
    "run search signature",
)
content = replace_once(
    content,
    "        transposition_table: Some(transposition_table),\n        cancellation,",
    "        transposition_table: Some(transposition_table),\n        check_extension_enabled,\n        cancellation,",
    "production context policy",
)
content = replace_once(
    content,
    "    transposition_table: Option<&'a mut TranspositionTable>,\n    cancellation: &'a mut Probe,",
    "    transposition_table: Option<&'a mut TranspositionTable>,\n    check_extension_enabled: bool,\n    cancellation: &'a mut Probe,",
    "context field",
)
old_search_header = """fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
"""
new_search_header = """fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let extension_budget = if context.check_extension_enabled {
        MAX_CHECK_EXTENSIONS_PER_LINE
    } else {
        0
    };
    search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        extension_budget,
        window,
        context,
    )
}

fn search_node_with_extensions<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    extension_budget: u16,
    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
"""
content = replace_once(content, old_search_header, new_search_header, "search wrapper")
content = replace_once(
    content,
    "    let score_reuse = transposition_score_reuse(position);",
    "    let score_reuse =\n        transposition_score_reuse(position, context.check_extension_enabled);",
    "score reuse call",
)
old_child = """        let child_window = AlphaBetaWindow {
            alpha: -beta,
            beta: -alpha,
        };
        let child = search_node(position, history, depth - 1, ply + 1, child_window, context);
"""
new_child = """        let child_window = AlphaBetaWindow {
            alpha: -beta,
            beta: -alpha,
        };
        let child_in_check = position.is_in_check(position.side_to_move());
        let extension = decide_check_extension(
            depth,
            ply,
            child_in_check,
            context.check_extension_enabled,
            extension_budget,
        );
        if let Some(event) = extension.event() {
            context.cancellation.on_check_extension(event);
        }
        let child = search_node_with_extensions(
            position,
            history,
            extension.child_depth(),
            ply + 1,
            extension.remaining_budget(),
            child_window,
            context,
        );
"""
content = replace_once(content, old_child, new_child, "extended child search")
content = replace_once(
    content,
    "fn transposition_score_reuse(position: &Position) -> TranspositionScoreReuse {\n    if position.halfmove_clock().get() == 0 {",
    "fn transposition_score_reuse(\n    position: &Position,\n    check_extension_enabled: bool,\n) -> TranspositionScoreReuse {\n    if check_extension_enabled {\n        TranspositionScoreReuse::SuppressedForSelectiveExtension\n    } else if position.halfmove_clock().get() == 0 {",
    "score reuse policy",
)
# Add disabled policy to every test-only context literal.
content = content.replace(
    "            transposition_table: None,\n            cancellation:",
    "            transposition_table: None,\n            check_extension_enabled: false,\n            cancellation:",
)
write(path, content)

# principal_variation.rs
path = "crates/chess-search/src/principal_variation.rs"
content = read(path)
content = replace_once(
    content,
    "pub(crate) fn reconstruct_principal_variation(\n    root: &Position,\n    requested_depth: u16,\n    root_best_move: Option<Move>,\n    transposition_table: &TranspositionTable,\n) -> Result<PrincipalVariation, PrincipalVariationError> {",
    "pub(crate) fn reconstruct_principal_variation(\n    root: &Position,\n    requested_depth: u16,\n    root_best_move: Option<Move>,\n    transposition_table: &TranspositionTable,\n) -> Result<PrincipalVariation, PrincipalVariationError> {\n    reconstruct_principal_variation_with_table_policy(\n        root,\n        requested_depth,\n        root_best_move,\n        transposition_table,\n        true,\n    )\n}\n\npub(crate) fn reconstruct_principal_variation_with_table_policy(\n    root: &Position,\n    requested_depth: u16,\n    root_best_move: Option<Move>,\n    transposition_table: &TranspositionTable,\n    allow_table_continuation: bool,\n) -> Result<PrincipalVariation, PrincipalVariationError> {",
    "PV policy wrapper",
)
content = replace_once(
    content,
    "        let candidate = if ply == 0 {\n            root_best_move\n        } else {\n            transposition_table.principal_variation_move(position.zobrist(), remaining_depth)\n        };",
    "        let candidate = if ply == 0 {\n            root_best_move\n        } else if allow_table_continuation {\n            transposition_table.principal_variation_move(position.zobrist(), remaining_depth)\n        } else {\n            None\n        };",
    "PV table policy",
)
write(path, content)

# iterative_deepening.rs
path = "crates/chess-search/src/iterative_deepening.rs"
content = read(path)
content = replace_once(
    content,
    "    cancellation::NeverCancelled,\n    limits::{",
    "    cancellation::NeverCancelled,\n    check_extension::CheckExtensionDiagnostics,\n    limits::{",
    "iterative imports check diagnostics",
)
content = replace_once(
    content,
    "    principal_variation::{reconstruct_principal_variation, PrincipalVariationError},",
    "    principal_variation::{\n        reconstruct_principal_variation_with_table_policy, PrincipalVariationError,\n    },",
    "iterative PV import",
)
content = replace_once(
    content,
    "    elapsed: Duration,\n    fallback: Option<SearchCancellationFallback>,",
    "    elapsed: Duration,\n    check_extension_diagnostics: CheckExtensionDiagnostics,\n    fallback: Option<SearchCancellationFallback>,",
    "search result diagnostics field",
)
content = replace_once(
    content,
    "    pub const fn elapsed(&self) -> Duration {\n        self.elapsed\n    }",
    "    pub const fn elapsed(&self) -> Duration {\n        self.elapsed\n    }\n\n    /// Returns request-wide bounded check-extension decisions, including partial work.\n    #[must_use]\n    pub const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {\n        self.check_extension_diagnostics\n    }",
    "search result diagnostics getter",
)
# Non-limited iteration policy argument.
content = replace_once(
    content,
    "            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n            transposition_table,",
    "            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n            false,\n            transposition_table,",
    "nonlimited iteration policy",
)
content = replace_once(
    content,
    "    let mut controller = SearchLimitController::new(limits, clock)\n        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;",
    "    let check_extension_enabled = limits.check_extension_enabled();\n    let mut controller = SearchLimitController::new(limits, clock)\n        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;",
    "limited policy capture",
)
content = replace_once(
    content,
    "            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n            transposition_table,\n            &mut controller,",
    "            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n            check_extension_enabled,\n            transposition_table,\n            &mut controller,",
    "limited iteration policy",
)
content = replace_once(
    content,
    "        elapsed: controller.elapsed(),\n        fallback,",
    "        elapsed: controller.elapsed(),\n        check_extension_diagnostics: controller.check_extension_diagnostics(),\n        fallback,",
    "limited result diagnostics",
)
content = replace_once(
    content,
    "        half_width_centipawns,\n        transposition_table,\n        &mut cancellation,",
    "        half_width_centipawns,\n        false,\n        transposition_table,\n        &mut cancellation,",
    "completed iteration default policy",
)
content = replace_once(
    content,
    "    half_width_centipawns: i32,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,",
    "    half_width_centipawns: i32,\n    check_extension_enabled: bool,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,",
    "completed iteration signature",
)
# Both attempt calls in one replacement operation.
content = content.replace(
    "        initial_window,\n        transposition_table,\n        cancellation,",
    "        initial_window,\n        check_extension_enabled,\n        transposition_table,\n        cancellation,",
)
content = content.replace(
    "                AlphaBetaWindow::full(),\n                transposition_table,\n                cancellation,",
    "                AlphaBetaWindow::full(),\n                check_extension_enabled,\n                transposition_table,\n                cancellation,",
)
content = replace_once(
    content,
    "    let principal_variation =\n        reconstruct_principal_variation(position, depth, result.best_move(), transposition_table)\n            .map_err(\n            |error| IterativeDeepeningSearchError::PrincipalVariationFailed { depth, error },\n        )?;",
    "    let principal_variation = reconstruct_principal_variation_with_table_policy(\n        position,\n        depth,\n        result.best_move(),\n        transposition_table,\n        !check_extension_enabled,\n    )\n    .map_err(|error| IterativeDeepeningSearchError::PrincipalVariationFailed { depth, error })?;",
    "PV extension policy",
)
content = replace_once(
    content,
    "    window: AlphaBetaWindow,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,\n) -> Result<(AlphaBetaRootWindowResult, AspirationWindowAttempt), IterativeDeepeningSearchError>",
    "    window: AlphaBetaWindow,\n    check_extension_enabled: bool,\n    transposition_table: &mut TranspositionTable,\n    cancellation: &mut Probe,\n) -> Result<(AlphaBetaRootWindowResult, AspirationWindowAttempt), IterativeDeepeningSearchError>",
    "run attempt signature",
)
content = replace_once(
    content,
    "        depth,\n        window,\n        transposition_table,",
    "        depth,\n        window,\n        check_extension_enabled,\n        transposition_table,",
    "alpha window policy call",
)
write(path, content)

# lib.rs
path = "crates/chess-search/src/lib.rs"
content = read(path)
content = replace_once(content, "mod cancellation;", "mod cancellation;\nmod check_extension;", "module declaration")
content = replace_once(
    content,
    "pub use cancellation::{SearchCancellationProbe, CANCELLATION_CHECK_INTERVAL_NODES};",
    "pub use cancellation::{SearchCancellationProbe, CANCELLATION_CHECK_INTERVAL_NODES};\npub use check_extension::{\n    CheckExtensionDiagnostics, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE,\n};",
    "module exports",
)
write(path, content)

# Focused integration tests.
write(
    "crates/chess-search/tests/search_check_extension.rs",
    r'''use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table, CheckExtensionDiagnostics,
    Score, SearchLimitTermination, SearchLimits, TranspositionBound, TranspositionEntry,
    TranspositionScore, TranspositionTable,
};

fn forcing_check_root() -> Position {
    "6k1/6pp/8/8/8/8/8/3Q2K1 w - - 0 1"
        .parse()
        .expect("forcing-check FEN is valid")
}

#[test]
fn check_extension_is_explicit_opt_in_and_records_applied_work() {
    let root = forcing_check_root();

    let mut baseline_position = root.clone();
    let baseline_snapshot = baseline_position.clone();
    let mut baseline_history = SearchHistory::from_position(&baseline_position);
    let baseline_history_snapshot = baseline_history.clone();
    let baseline = iterative_deepening_search_with_limits(
        &mut baseline_position,
        &mut baseline_history,
        SearchLimits::new().with_depth(1),
    )
    .expect("baseline search succeeds");
    assert_eq!(
        baseline.check_extension_diagnostics(),
        CheckExtensionDiagnostics::default()
    );
    assert_eq!(baseline_position, baseline_snapshot);
    assert_eq!(baseline_history, baseline_history_snapshot);

    let mut extended_position = root.clone();
    let extended_snapshot = extended_position.clone();
    let mut extended_history = SearchHistory::from_position(&extended_position);
    let extended_history_snapshot = extended_history.clone();
    let extended = iterative_deepening_search_with_limits(
        &mut extended_position,
        &mut extended_history,
        SearchLimits::new()
            .with_depth(1)
            .with_check_extension(),
    )
    .expect("extended search succeeds");
    let diagnostics = extended.check_extension_diagnostics();

    assert_eq!(
        extended.termination(),
        SearchLimitTermination::Depth { depth: 1 }
    );
    assert!(diagnostics.eligible_nodes() > 0);
    assert!(diagnostics.applied_extensions() > 0);
    assert_eq!(
        diagnostics.eligible_nodes(),
        diagnostics
            .applied_extensions()
            .saturating_add(diagnostics.budget_exhausted_nodes())
            .saturating_add(diagnostics.mate_domain_blocked_nodes())
    );
    assert_eq!(extended_position, extended_snapshot);
    assert_eq!(extended_history, extended_history_snapshot);
    assert_eq!(extended_position.zobrist(), extended_position.recomputed_zobrist());
}

#[test]
fn extension_search_is_deterministic_and_keeps_a_legal_root_pv() {
    let root = forcing_check_root();
    let mut first_position = root.clone();
    let mut first_history = SearchHistory::from_position(&first_position);
    let first = iterative_deepening_search_with_limits(
        &mut first_position,
        &mut first_history,
        SearchLimits::new()
            .with_depth(2)
            .with_check_extension(),
    )
    .expect("first extension search succeeds");

    let mut second_position = root.clone();
    let mut second_history = SearchHistory::from_position(&second_position);
    let second = iterative_deepening_search_with_limits(
        &mut second_position,
        &mut second_history,
        SearchLimits::new()
            .with_depth(2)
            .with_check_extension(),
    )
    .expect("second extension search succeeds");

    assert_eq!(first.best_move(), second.best_move());
    assert_eq!(first.score(), second.score());
    assert_eq!(first.nodes(), second.nodes());
    assert_eq!(
        first.check_extension_diagnostics(),
        second.check_extension_diagnostics()
    );
    assert_eq!(first.completed_depth(), 2);
    let pv = first
        .principal_variation()
        .expect("completed extension search retains a root PV");
    assert_eq!(pv.moves().first().copied(), first.best_move());
    assert!(pv.len() <= usize::from(first.completed_depth()));
    assert_eq!(first_position, root);
    assert_eq!(second_position, root);
}

#[test]
fn extension_enabled_search_cannot_reuse_a_baseline_tt_score() {
    let root = Position::starting();
    let mut position = root.clone();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let first_move = position
        .legal_move_tokens()
        .expect("starting legal moves generate")
        .iter()
        .next()
        .expect("starting position has a move")
        .move_made();
    let bogus = Score::from_evaluation(12_345);
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus score normalizes"),
        Some(first_move),
        table.generation(),
    ));

    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new()
            .with_depth(1)
            .with_check_extension(),
        &mut table,
    )
    .expect("extension search ignores path-incompatible TT score");

    assert_ne!(result.score(), Some(bogus));
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn tight_node_limit_preserves_partial_extension_diagnostics_and_root_state() {
    let root = forcing_check_root();
    let mut position = root.clone();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new()
            .with_nodes(64)
            .with_check_extension(),
    )
    .expect("node-limited extension search returns a snapshot");

    assert_eq!(result.termination(), SearchLimitTermination::Nodes { nodes: 64 });
    assert_eq!(result.nodes(), 64);
    assert!(result.check_extension_diagnostics().eligible_nodes() > 0);
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
''',
)

write(
    "docs/RUST_CHECK_EXTENSION.md",
    r'''# Rust bounded check extension

Task 16.7 adds one explicit, optional selective-search feature. It is disabled by
default and is enabled for a limit-controlled request with
`SearchLimits::with_check_extension()`.

## Exact bound

A checking move may add one ply to its child search. Each root-to-leaf path starts
with a budget of exactly one extension. Applying it consumes the complete budget;
later checks on that path are searched at their nominal depth and recorded as
budget-exhausted decisions. A second extension cannot occur on the same path.

The extension is also refused when the extra ply would leave the supported
mate-score domain. Quiescence retains its independent bounded tactical-ply guard.

## Transposition safety

The remaining extension budget is path-dependent and is not represented by the
normal position Zobrist key. Therefore an extension-enabled request suppresses TT
score reuse and TT score storage. Complete-key verified legal moves may still be
used only as move-ordering hints. This prevents a baseline or differently budgeted
entry from bypassing the selective search contract.

Because the current extension search does not create compatible exact TT chains,
PV reconstruction validates and returns the exact root move but does not continue
through pre-existing table entries. The returned PV remains legal and bounded by
the completed nominal depth.

## Diagnostics

`SearchResult::check_extension_diagnostics()` reports request-wide counts for:

- eligible checking children;
- applied extensions;
- checks skipped after the one-ply path budget was consumed;
- checks blocked by the mate-score ply ceiling.

The limit controller records events as they happen, so diagnostics include work
from a depth interrupted by node, time, or explicit-stop cancellation.

## Compatibility

Existing fixed-depth and limit-controlled calls remain extension-free unless the
new builder is selected. Node, qnode, selective-depth, elapsed-time, cancellation,
root-restoration, aspiration exactness, and legal-PV semantics remain unchanged.
''',
)

# Update existing contract docs with concise Task 16.7 notes.
path = "docs/RUST_SEARCH_LIMITS.md"
content = read(path)
content += """

## Optional bounded check extension

`SearchLimits::with_check_extension()` opts the request into the Task 16.7
one-ply-per-line check extension. The feature is not an automatic stopping limit
and is valid in finite or infinite mode. Its extra nodes remain subject to the
same node, hard-time, and explicit-stop checkpoints. Request-wide extension
diagnostics include interrupted partial work.
"""
write(path, content)

path = "docs/RUST_SEARCH_RESULT_API.md"
content = read(path)
content += """

## Check-extension diagnostics

The Task 16.7 opt-in policy adds
`SearchResult::check_extension_diagnostics()`. These request-wide counters cover
applied, exhausted-budget, and mate-domain-blocked decisions from both completed
and interrupted work. They do not turn partial search data into an exact score or
completed iteration.
"""
write(path, content)

print("Task 16.7 implementation applied")
