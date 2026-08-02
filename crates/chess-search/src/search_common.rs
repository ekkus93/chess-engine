use chess_core::{Position, SearchHistory};

use crate::{evaluate, Score};

const CLAIMABLE_REPETITION_COUNT: usize = 3;
const CLAIMABLE_HALFMOVE_COUNT: u16 = 100;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct UnsupportedMatePly {
    ply: u16,
}

impl UnsupportedMatePly {
    #[must_use]
    pub(crate) const fn ply(self) -> u16 {
        self.ply
    }
}

pub(crate) fn resolved_terminal_or_draw_score(
    position: &Position,
    history: &SearchHistory,
    legal_moves_empty: bool,
    ply: u16,
) -> Result<Option<Score>, UnsupportedMatePly> {
    if legal_moves_empty {
        let score = if position.is_in_check(position.side_to_move()) {
            Score::mated_in(ply).ok_or(UnsupportedMatePly { ply })?
        } else {
            Score::ZERO
        };
        return Ok(Some(score));
    }

    if is_search_draw(position, history) {
        return Ok(Some(Score::ZERO));
    }

    Ok(None)
}

pub(crate) fn resolved_node_score(
    position: &Position,
    history: &SearchHistory,
    legal_moves_empty: bool,
    depth: u16,
    ply: u16,
) -> Result<Option<Score>, UnsupportedMatePly> {
    if let Some(score) = resolved_terminal_or_draw_score(position, history, legal_moves_empty, ply)?
    {
        return Ok(Some(score));
    }

    if depth == 0 {
        return Ok(Some(evaluate(position)));
    }

    Ok(None)
}

fn is_search_draw(position: &Position, history: &SearchHistory) -> bool {
    position.is_dead_position()
        || history.repetition_count(position) >= CLAIMABLE_REPETITION_COUNT
        || position.halfmove_clock().get() >= CLAIMABLE_HALFMOVE_COUNT
}
