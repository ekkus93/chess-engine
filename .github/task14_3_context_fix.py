#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / "crates/chess-search/src/alpha_beta.rs"
text = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    """    let mut quiet_ordering = QuietOrderingState::new();
    let result = search_node(
        position,
        history,
        depth,
        0,
        window,
        MoveOrdering::Quiet,
        &mut quiet_ordering,
        cancellation,
    );""",
    """    let mut quiet_ordering = QuietOrderingState::new();
    let mut context = AlphaBetaContext {
        ordering: MoveOrdering::Quiet,
        quiet_ordering: &mut quiet_ordering,
        cancellation,
    };
    let result = search_node(position, history, depth, 0, window, &mut context);""",
    "root context",
)
replace_once(
    """struct AlphaBetaWindow {
    alpha: Score,
    beta: Score,
}

fn search_node<Probe>(""",
    """struct AlphaBetaWindow {
    alpha: Score,
    beta: Score,
}

struct AlphaBetaContext<'a, Probe>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    ordering: MoveOrdering,
    quiet_ordering: &'a mut QuietOrderingState,
    cancellation: &'a mut Probe,
}

fn search_node<Probe>(""",
    "search context definition",
)
replace_once(
    """    window: AlphaBetaWindow,
    ordering: MoveOrdering,
    quiet_ordering: &mut QuietOrderingState,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>""",
    """    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>""",
    "search-node context argument",
)
count = text.count("cancellation.should_cancel()")
if count != 2:
    raise SystemExit(f"cancellation probes: expected two matches, found {count}")
text = text.replace("cancellation.should_cancel()", "context.cancellation.should_cancel()")
replace_once(
    """        let context = QuiescenceContext {
            ply,
            quiescence_ply: 0,
            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        };
        return search_quiescence_node(
            position,
            history,
            context,""",
    """        let quiescence_context = QuiescenceContext {
            ply,
            quiescence_ply: 0,
            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        };
        return search_quiescence_node(
            position,
            history,
            quiescence_context,""",
    "quiescence local name",
)
replace_once(
    """            ordering,
            cancellation,
        );""",
    """            context.ordering,
            &mut *context.cancellation,
        );""",
    "quiescence context",
)
replace_once(
    """    let ordered_tokens =
        ordered_legal_moves_with_state(position, &tokens, ordering, ply, quiet_ordering);""",
    """    let ordered_tokens = ordered_legal_moves_with_state(
        position,
        &tokens,
        context.ordering,
        ply,
        context.quiet_ordering,
    );""",
    "ordering context",
)
replace_once(
    """            child_window,
            ordering,
            quiet_ordering,
            cancellation,
        );""",
    """            child_window,
            context,
        );""",
    "recursive context",
)
replace_once(
    """            if ordering == MoveOrdering::Quiet {
                quiet_ordering.record_quiet_cutoff(""",
    """            if context.ordering == MoveOrdering::Quiet {
                context.quiet_ordering.record_quiet_cutoff(""",
    "cutoff context",
)
replace_once(
    """    use super::{search_node, AlphaBetaSearchResult, AlphaBetaWindow};""",
    """    use super::{
        search_node, AlphaBetaContext, AlphaBetaSearchResult, AlphaBetaWindow,
    };""",
    "test context import",
)
replace_once(
    """        let mut cancellation = NeverCancelled;
        let result = search_node(
            &mut position,
            &mut history,
            depth,
            0,
            window,
            ordering,
            &mut quiet_ordering,
            &mut cancellation,
        )
        .expect("ordering benchmark search succeeds");""",
    """        let mut cancellation = NeverCancelled;
        let mut context = AlphaBetaContext {
            ordering,
            quiet_ordering: &mut quiet_ordering,
            cancellation: &mut cancellation,
        };
        let result = search_node(
            &mut position,
            &mut history,
            depth,
            0,
            window,
            &mut context,
        )
        .expect("ordering benchmark search succeeds");""",
    "test search context",
)
replace_once(
    """        let mut cancellation = NeverCancelled;
        let child = search_node(
            position,
            history,
            0,
            1,
            full_window(),
            MoveOrdering::Generation,
            &mut quiet_ordering,
            &mut cancellation,
        );""",
    """        let mut cancellation = NeverCancelled;
        let mut context = AlphaBetaContext {
            ordering: MoveOrdering::Generation,
            quiet_ordering: &mut quiet_ordering,
            cancellation: &mut cancellation,
        };
        let child = search_node(position, history, 0, 1, full_window(), &mut context);""",
    "root-move test context",
)
path.write_text(text)
print("Task 14.3 recursive context fix applied")
