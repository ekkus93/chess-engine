use core::fmt;
use std::time::Duration;

use chess_core::Color;
use chess_uci::GoCommand;

/// Default clock horizon when the GUI does not provide `movestogo`.
pub(crate) const DEFAULT_MOVES_TO_GO: u32 = 30;
/// Minimum wall-clock reserve for clocks large enough to retain it.
pub(crate) const MINIMUM_SAFETY_RESERVE_MS: u64 = 10;
/// Five percent of the side-to-move clock is reserved for protocol and scheduling delay.
const SAFETY_RESERVE_DIVISOR: u64 = 20;
/// Three quarters of the increment may contribute to the current move budget.
const INCREMENT_SHARE_NUMERATOR: u64 = 3;
const INCREMENT_SHARE_DENOMINATOR: u64 = 4;
/// The hard budget is at most twice the soft budget.
const HARD_BUDGET_MULTIPLIER: u64 = 2;

/// Deterministic soft and hard wall-clock limits for one UCI search request.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct UciTimeBudget {
    soft: Duration,
    hard: Duration,
    safety_reserve: Duration,
}

impl UciTimeBudget {
    /// Returns the iteration-boundary budget.
    #[must_use]
    pub(crate) const fn soft(self) -> Duration {
        self.soft
    }

    /// Returns the in-tree cancellation budget.
    #[must_use]
    pub(crate) const fn hard(self) -> Duration {
        self.hard
    }

    /// Returns the clock time deliberately excluded from both budgets.
    #[must_use]
    pub(crate) const fn safety_reserve(self) -> Duration {
        self.safety_reserve
    }
}

/// Invalid or incomplete UCI clock input for the side to move.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum UciTimeManagerError {
    /// At least one clock field was supplied, but the side-to-move clock was absent.
    MissingSideToMoveClock { side: Color },
    /// A zero side-to-move clock cannot produce a nonzero validated search budget.
    ZeroSideToMoveClock { side: Color },
}

impl fmt::Display for UciTimeManagerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingSideToMoveClock { side } => write!(
                formatter,
                "clock-based search is missing the {} side-to-move clock",
                side_name(*side)
            ),
            Self::ZeroSideToMoveClock { side } => write!(
                formatter,
                "clock-based search has no usable time on the {} side-to-move clock",
                side_name(*side)
            ),
        }
    }
}

impl std::error::Error for UciTimeManagerError {}

/// Converts UCI clock fields into deterministic soft and hard search budgets.
///
/// Requests without clock fields return `Ok(None)` so fixed depth, node,
/// move-time, and infinite behavior remain unchanged.
pub(crate) fn allocate_time_budget(
    command: GoCommand,
    side_to_move: Color,
) -> Result<Option<UciTimeBudget>, UciTimeManagerError> {
    if !has_clock_fields(command) {
        return Ok(None);
    }

    let remaining_ms = side_time_ms(command, side_to_move)
        .ok_or(UciTimeManagerError::MissingSideToMoveClock { side: side_to_move })?;
    if remaining_ms == 0 {
        return Err(UciTimeManagerError::ZeroSideToMoveClock { side: side_to_move });
    }

    let increment_ms = side_increment_ms(command, side_to_move).unwrap_or(0);
    let moves_to_go = u64::from(command.moves_to_go().unwrap_or(DEFAULT_MOVES_TO_GO));
    let safety_reserve_ms = safety_reserve_ms(remaining_ms);
    let usable_ms = remaining_ms - safety_reserve_ms;

    let base_share_ms = (usable_ms / moves_to_go).max(1);
    let increment_share_ms = scaled_fraction(
        increment_ms,
        INCREMENT_SHARE_NUMERATOR,
        INCREMENT_SHARE_DENOMINATOR,
    );
    let soft_ms = base_share_ms
        .saturating_add(increment_share_ms)
        .min(usable_ms)
        .max(1);
    let hard_ms = soft_ms
        .saturating_mul(HARD_BUDGET_MULTIPLIER)
        .min(usable_ms)
        .max(soft_ms);

    Ok(Some(UciTimeBudget {
        soft: Duration::from_millis(soft_ms),
        hard: Duration::from_millis(hard_ms),
        safety_reserve: Duration::from_millis(safety_reserve_ms),
    }))
}

const fn has_clock_fields(command: GoCommand) -> bool {
    command.white_time_ms().is_some()
        || command.black_time_ms().is_some()
        || command.white_increment_ms().is_some()
        || command.black_increment_ms().is_some()
        || command.moves_to_go().is_some()
}

const fn side_time_ms(command: GoCommand, side: Color) -> Option<u64> {
    match side {
        Color::White => command.white_time_ms(),
        Color::Black => command.black_time_ms(),
    }
}

const fn side_increment_ms(command: GoCommand, side: Color) -> Option<u64> {
    match side {
        Color::White => command.white_increment_ms(),
        Color::Black => command.black_increment_ms(),
    }
}

const fn safety_reserve_ms(remaining_ms: u64) -> u64 {
    if remaining_ms <= 1 {
        return 0;
    }
    let proportional = remaining_ms / SAFETY_RESERVE_DIVISOR;
    let requested = if proportional > MINIMUM_SAFETY_RESERVE_MS {
        proportional
    } else {
        MINIMUM_SAFETY_RESERVE_MS
    };
    let maximum = remaining_ms - 1;
    if requested < maximum {
        requested
    } else {
        maximum
    }
}

const fn scaled_fraction(value: u64, numerator: u64, denominator: u64) -> u64 {
    let quotient = value / denominator;
    let remainder = value % denominator;
    quotient * numerator + remainder * numerator / denominator
}

const fn side_name(side: Color) -> &'static str {
    match side {
        Color::White => "White",
        Color::Black => "Black",
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::Color;
    use chess_uci::{GoCommand, UciEvent, UciSession};

    use super::{
        allocate_time_budget, UciTimeManagerError, DEFAULT_MOVES_TO_GO,
        MINIMUM_SAFETY_RESERVE_MS,
    };

    fn command(input: &str) -> GoCommand {
        let response = UciSession::new().handle_line(input);
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.command(),
            other => panic!("expected start-search event, found {other:?}"),
        }
    }

    #[test]
    fn requests_without_clock_fields_are_not_modified() {
        assert_eq!(
            allocate_time_budget(command("go depth 4 nodes 1000"), Color::White),
            Ok(None)
        );
        assert_eq!(DEFAULT_MOVES_TO_GO, 30);
        assert_eq!(MINIMUM_SAFETY_RESERVE_MS, 10);
    }

    #[test]
    fn moves_to_go_and_increment_produce_exact_budgets() {
        let budget = allocate_time_budget(
            command("go wtime 60000 btime 50000 winc 1000 binc 200 movestogo 20"),
            Color::White,
        )
        .expect("clock input is valid")
        .expect("clock budget exists");

        assert_eq!(budget.safety_reserve(), Duration::from_millis(3000));
        assert_eq!(budget.soft(), Duration::from_millis(3600));
        assert_eq!(budget.hard(), Duration::from_millis(7200));
    }

    #[test]
    fn missing_moves_to_go_uses_the_documented_default_horizon() {
        let budget = allocate_time_budget(
            command("go wtime 60000 btime 60000 winc 1000 binc 1000"),
            Color::White,
        )
        .expect("clock input is valid")
        .expect("clock budget exists");

        assert_eq!(budget.safety_reserve(), Duration::from_millis(3000));
        assert_eq!(budget.soft(), Duration::from_millis(2650));
        assert_eq!(budget.hard(), Duration::from_millis(5300));
    }

    #[test]
    fn asymmetric_clocks_and_increments_follow_the_side_to_move() {
        let command = command(
            "go wtime 90000 btime 12000 winc 5000 binc 400 movestogo 10",
        );
        let white = allocate_time_budget(command, Color::White)
            .expect("white clock is valid")
            .expect("white budget exists");
        let black = allocate_time_budget(command, Color::Black)
            .expect("black clock is valid")
            .expect("black budget exists");

        assert_eq!(white.safety_reserve(), Duration::from_millis(4500));
        assert_eq!(white.soft(), Duration::from_millis(12300));
        assert_eq!(white.hard(), Duration::from_millis(24600));
        assert_eq!(black.safety_reserve(), Duration::from_millis(600));
        assert_eq!(black.soft(), Duration::from_millis(1440));
        assert_eq!(black.hard(), Duration::from_millis(2880));
    }

    #[test]
    fn increment_contribution_is_bounded_and_deterministic() {
        let without_increment = allocate_time_budget(
            command("go wtime 60000 btime 60000 movestogo 20"),
            Color::White,
        )
        .expect("clock input is valid")
        .expect("clock budget exists");
        let with_increment = allocate_time_budget(
            command("go wtime 60000 btime 60000 winc 1000 movestogo 20"),
            Color::White,
        )
        .expect("clock input is valid")
        .expect("clock budget exists");

        assert_eq!(without_increment.soft(), Duration::from_millis(2850));
        assert_eq!(with_increment.soft(), Duration::from_millis(3600));
        assert!(with_increment.hard() <= Duration::from_millis(57000));
    }

    #[test]
    fn low_time_preserves_a_nonzero_budget_and_never_spends_the_reserve() {
        for (remaining_ms, reserve_ms, soft_ms, hard_ms) in
            [(1, 0, 1, 1), (10, 9, 1, 1), (100, 10, 3, 6)]
        {
            let budget = allocate_time_budget(
                command(&format!("go wtime {remaining_ms}")),
                Color::White,
            )
            .expect("positive clock is valid")
            .expect("clock budget exists");
            assert_eq!(budget.safety_reserve(), Duration::from_millis(reserve_ms));
            assert_eq!(budget.soft(), Duration::from_millis(soft_ms));
            assert_eq!(budget.hard(), Duration::from_millis(hard_ms));
            assert!(budget.soft() <= budget.hard());
            assert!(budget.hard() + budget.safety_reserve() <= Duration::from_millis(remaining_ms));
        }
    }

    #[test]
    fn missing_or_zero_side_to_move_clock_fails_loudly() {
        assert_eq!(
            allocate_time_budget(command("go btime 1000"), Color::White),
            Err(UciTimeManagerError::MissingSideToMoveClock {
                side: Color::White,
            })
        );
        assert_eq!(
            allocate_time_budget(command("go wtime 0 btime 1000"), Color::White),
            Err(UciTimeManagerError::ZeroSideToMoveClock {
                side: Color::White,
            })
        );
    }

    #[test]
    fn maximum_integer_inputs_do_not_overflow() {
        let maximum = u64::MAX;
        let budget = allocate_time_budget(
            command(&format!(
                "go wtime {maximum} btime {maximum} winc {maximum} movestogo 1"
            )),
            Color::White,
        )
        .expect("maximum clock input is valid")
        .expect("clock budget exists");

        assert!(budget.soft() <= budget.hard());
        assert!(budget.hard() + budget.safety_reserve() <= Duration::from_millis(maximum));
    }
}
