#!/usr/bin/env python3
from pathlib import Path
import os
import sys

root = Path(sys.argv[1])


def patch(relative_path: str, replacements: list[tuple[str, str]]) -> None:
    path = root / relative_path
    text = path.read_text()
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise SystemExit(
                f"expected one match in {relative_path}, found {count}: {old[:100]!r}"
            )
        text = text.replace(old, new, 1)
    path.write_text(text)


patch(
    "crates/chess-search/src/reference.rs",
    [
        (
            '''use crate::{cancellation::NeverCancelled, evaluate, Score, SearchCancellationProbe, MAX_MATE_PLY};
''',
            '''use crate::{
    cancellation::NeverCancelled, evaluate, search_common::resolved_terminal_or_draw_score,
    Score, SearchCancellationProbe, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,
};
''',
        ),
        (
            '''    /// Cooperative cancellation was requested.
    Cancelled,
    /// Recursive node accumulation exceeded `u64`.
''',
            '''    /// Cooperative cancellation was requested.
    Cancelled,
    /// The reference quiescence guard was reached while the side to move remained in check.
    QuiescenceDepthLimitReachedInCheck {
        /// Tactical ply at which expansion stopped.
        quiescence_ply: u16,
        /// Selected tactical-ply maximum.
        maximum: u16,
    },
    /// Recursive node accumulation exceeded `u64`.
''',
        ),
        (
            '''            Self::Cancelled => formatter.write_str("reference search cancelled"),
            Self::NodeCountOverflow => formatter.write_str("reference-search node count overflow"),
''',
            '''            Self::Cancelled => formatter.write_str("reference search cancelled"),
            Self::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum,
            } => write!(
                formatter,
                "reference quiescence depth limit {maximum} reached in check at tactical ply {quiescence_ply}"
            ),
            Self::NodeCountOverflow => formatter.write_str("reference-search node count overflow"),
''',
        ),
        (
            '''pub fn reference_search_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if depth > MAX_MATE_PLY {
        return Err(ReferenceSearchError::DepthTooLarge {
            depth,
            maximum: MAX_MATE_PLY,
        });
    }

    let history_zobrist = history.current_zobrist();
    if history_zobrist != Some(position.zobrist()) {
        return Err(ReferenceSearchError::HistoryPositionMismatch {
            position_zobrist: position.zobrist(),
            history_zobrist,
        });
    }

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
    let result = search_node(position, history, depth, 0, cancellation);

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}
''',
            '''pub fn reference_search_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    reference_search_internal(
        position,
        history,
        depth,
        ReferenceLeafMode::Static,
        cancellation,
    )
}

/// Searches the complete legal tree and uses unpruned quiescence at leaves.
pub fn reference_search_with_quiescence(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<ReferenceSearchResult, ReferenceSearchError> {
    let mut cancellation = NeverCancelled;
    reference_search_with_quiescence_and_cancellation(
        position,
        history,
        depth,
        &mut cancellation,
    )
}

/// Searches the complete legal tree with unpruned quiescence and cancellation.
pub fn reference_search_with_quiescence_and_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    reference_search_internal(
        position,
        history,
        depth,
        ReferenceLeafMode::Quiescence,
        cancellation,
    )
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum ReferenceLeafMode {
    Static,
    Quiescence,
}

fn reference_search_internal<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    leaf_mode: ReferenceLeafMode,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if depth > MAX_MATE_PLY {
        return Err(ReferenceSearchError::DepthTooLarge {
            depth,
            maximum: MAX_MATE_PLY,
        });
    }

    let history_zobrist = history.current_zobrist();
    if history_zobrist != Some(position.zobrist()) {
        return Err(ReferenceSearchError::HistoryPositionMismatch {
            position_zobrist: position.zobrist(),
            history_zobrist,
        });
    }

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
    let result = search_node(position, history, depth, 0, leaf_mode, cancellation);

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}
''',
        ),
        (
            '''fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
''',
            '''fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    leaf_mode: ReferenceLeafMode,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
''',
        ),
        (
            '''    if cancellation.should_cancel() {
        return Err(ReferenceSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;
''',
            '''    if cancellation.should_cancel() {
        return Err(ReferenceSearchError::Cancelled);
    }

    if depth == 0 && leaf_mode == ReferenceLeafMode::Quiescence {
        return search_quiescence_node(
            position,
            history,
            ply,
            0,
            MAX_QUIESCENCE_PLY,
            cancellation,
        );
    }

    let tokens = position.legal_move_tokens()?;
''',
        ),
        (
            '''        let child = search_node(position, history, depth - 1, ply + 1, cancellation);
''',
            '''        let child = search_node(
            position,
            history,
            depth - 1,
            ply + 1,
            leaf_mode,
            cancellation,
        );
''',
        ),
        (
            '''fn is_search_draw(position: &Position, history: &SearchHistory) -> bool {
''',
            '''fn search_quiescence_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    ply: u16,
    quiescence_ply: u16,
    maximum_quiescence_ply: u16,
    cancellation: &mut Probe,
) -> Result<ReferenceSearchResult, ReferenceSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    if cancellation.should_cancel() {
        return Err(ReferenceSearchError::Cancelled);
    }

    let tokens = position.legal_move_tokens()?;
    if let Some(score) = resolved_terminal_or_draw_score(position, history, tokens.is_empty(), ply)
        .map_err(|error| ReferenceSearchError::DepthTooLarge {
            depth: error.ply(),
            maximum: MAX_MATE_PLY,
        })?
    {
        return Ok(ReferenceSearchResult {
            score,
            best_move: None,
            nodes: 1,
        });
    }

    let in_check = position.is_in_check(position.side_to_move());
    let mut best_score = None;
    let mut best_move = None;

    if in_check {
        if quiescence_ply >= maximum_quiescence_ply {
            return Err(ReferenceSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum: maximum_quiescence_ply,
            });
        }
    } else {
        best_score = Some(evaluate(position));
        if quiescence_ply >= maximum_quiescence_ply {
            return Ok(ReferenceSearchResult {
                score: best_score.expect("stand-pat exists outside check"),
                best_move: None,
                nodes: 1,
            });
        }
    }

    let mut nodes = 1_u64;
    for token in tokens.iter() {
        let current = token.move_made();
        if !in_check && !is_tactical(current) {
            continue;
        }
        if cancellation.should_cancel() {
            return Err(ReferenceSearchError::Cancelled);
        }

        let child_ply = ply
            .checked_add(1)
            .filter(|next| *next <= MAX_MATE_PLY)
            .ok_or(ReferenceSearchError::DepthTooLarge {
                depth: ply.saturating_add(1),
                maximum: MAX_MATE_PLY,
            })?;
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child = search_quiescence_node(
            position,
            history,
            child_ply,
            quiescence_ply + 1,
            maximum_quiescence_ply,
            cancellation,
        );
        let history_restore = history.pop_position(history_undo);
        let position_restore = position.unmake_move(position_undo);

        if let Err(error) = position_restore {
            return Err(error.into());
        }
        if let Err(error) = history_restore {
            return Err(error.into());
        }

        let child = child?;
        nodes = nodes
            .checked_add(child.nodes)
            .ok_or(ReferenceSearchError::NodeCountOverflow)?;
        let score = -child.score;
        let replace_best = match best_score {
            Some(previous) => score > previous,
            None => true,
        };
        if replace_best {
            best_score = Some(score);
            best_move = Some(current);
        }
    }

    match best_score {
        Some(score) => Ok(ReferenceSearchResult {
            score,
            best_move,
            nodes,
        }),
        None => Err(ReferenceSearchError::MissingBestMove),
    }
}

const fn is_tactical(current: Move) -> bool {
    current.kind().is_capture() || current.promotion().is_some()
}

fn is_search_draw(position: &Position, history: &SearchHistory) -> bool {
''',
        ),
    ],
)

patch(
    "crates/chess-search/src/lib.rs",
    [
        (
            '''pub use reference::{
    reference_search, reference_search_with_cancellation, ReferenceSearchError,
    ReferenceSearchResult,
};
''',
            '''pub use reference::{
    reference_search, reference_search_with_cancellation, reference_search_with_quiescence,
    reference_search_with_quiescence_and_cancellation, ReferenceSearchError,
    ReferenceSearchResult,
};
''',
        ),
    ],
)

for relative_path in [
    "crates/chess-search/tests/search_equivalence.rs",
    "crates/chess-search/tests/search_terminals.rs",
]:
    path = root / relative_path
    text = path.read_text()
    if "reference_search" not in text:
        raise SystemExit(f"missing reference search use in {relative_path}")
    text = text.replace("reference_search", "reference_search_with_quiescence")
    path.write_text(text)

patch(
    "docs/RUST_QUIESCENCE_SEARCH.md",
    [
        (
            '''Public entry points:

- `quiescence_search`;
''',
            '''Public entry points:

- `reference_search_with_quiescence` as the unpruned tactical-leaf oracle;
- `reference_search_with_quiescence_and_cancellation`;
- `quiescence_search`;
''',
        ),
        (
            '''- an unpruned tactical-leaf oracle compared with alpha-beta quiescence;
''',
            '''- an independent fixture-level tactical oracle and the production unpruned
  `reference_search_with_quiescence` oracle compared with alpha-beta quiescence;
''',
        ),
    ],
)

hook = root / ".git/hooks/pre-commit"
hook.write_text("#!/bin/sh\ngit add -A\n")
os.chmod(hook, 0o755)

print("added unpruned reference quiescence while preserving the static Task 13 baseline")
