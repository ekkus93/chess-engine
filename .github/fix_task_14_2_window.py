#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1]) / "crates/chess-search/src/alpha_beta.rs"
text = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    """    let result = search_node(
        position,
        history,
        depth,
        0,
        alpha,
        beta,
        MoveOrdering::Tactical,
        cancellation,
    );
""",
    """    let window = AlphaBetaWindow { alpha, beta };
    let result = search_node(
        position,
        history,
        depth,
        0,
        window,
        MoveOrdering::Tactical,
        cancellation,
    );
""",
    "root window",
)
replace_once(
    "fn search_node<Probe>(\n",
    """#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct AlphaBetaWindow {
    alpha: Score,
    beta: Score,
}

fn search_node<Probe>(
""",
    "window type",
)
replace_once(
    """    depth: u16,
    ply: u16,
    mut alpha: Score,
    beta: Score,
    ordering: MoveOrdering,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if cancellation.should_cancel() {
""",
    """    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    ordering: MoveOrdering,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let mut alpha = window.alpha;
    let beta = window.beta;
    if cancellation.should_cancel() {
""",
    "node window parameter",
)
replace_once(
    """        let child = search_node(
            position,
            history,
            depth - 1,
            ply + 1,
            -beta,
            -alpha,
            ordering,
            cancellation,
        );
""",
    """        let child_window = AlphaBetaWindow {
            alpha: -beta,
            beta: -alpha,
        };
        let child = search_node(
            position,
            history,
            depth - 1,
            ply + 1,
            child_window,
            ordering,
            cancellation,
        );
""",
    "child window",
)

path.write_text(text)
print("Task 14.2 alpha-beta window refactor applied")
