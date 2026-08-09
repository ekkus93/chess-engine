pub use chess_app::text::{
    board_lines, color_name, draw_reason_name, format_duration, format_move_history, format_outcome,
    format_score, format_search_metrics, orientation_for_config, piece_symbol, turn_status,
    BoardOrientation,
};

pub const MIN_TERMINAL_WIDTH: u16 = 58;
pub const MIN_TERMINAL_HEIGHT: u16 = 32;
pub const WIDE_TERMINAL_WIDTH: u16 = 80;
pub const STACKED_MIN_TERMINAL_HEIGHT: u16 = 46;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LayoutDecision {
    TooSmall,
    Horizontal,
    Vertical,
}

#[must_use]
pub const fn layout_decision(width: u16, height: u16) -> LayoutDecision {
    if width >= WIDE_TERMINAL_WIDTH && height >= MIN_TERMINAL_HEIGHT {
        LayoutDecision::Horizontal
    } else if width >= MIN_TERMINAL_WIDTH && height >= STACKED_MIN_TERMINAL_HEIGHT {
        LayoutDecision::Vertical
    } else {
        LayoutDecision::TooSmall
    }
}

#[cfg(test)]
mod tests {
    use super::{layout_decision, LayoutDecision};

    #[test]
    fn responsive_layout_boundaries_remain_tui_owned() {
        assert_eq!(layout_decision(80, 32), LayoutDecision::Horizontal);
        assert_eq!(layout_decision(58, 46), LayoutDecision::Vertical);
        assert_eq!(layout_decision(57, 100), LayoutDecision::TooSmall);
        assert_eq!(layout_decision(100, 31), LayoutDecision::TooSmall);
    }
}

#[cfg(test)]
mod hardening_tests;
