use core::fmt::Write as _;
use std::{
    io::{self, Write},
    sync::{Mutex, MutexGuard},
    time::Duration,
};

use chess_search::{Score, SearchProgress, SearchResult, MATE_SCORE};

/// Thread-safe output boundary shared by the protocol and one search worker.
pub(crate) trait SearchOutput: Send + Sync {
    /// Emits one exact completed-iteration information record.
    fn report_progress(&self, progress: SearchProgress<'_>, elapsed: Duration) -> io::Result<()>;

    /// Emits the single final move record for a completed or explicitly stopped request.
    fn report_bestmove(&self, result: &SearchResult) -> io::Result<()>;

    /// Emits one fail-loud adapter error record.
    fn report_error(&self, message: &str) -> io::Result<()>;
}

/// Mutex-serialized UCI writer used by the main thread and search worker.
pub(crate) struct SharedUciOutput<W> {
    writer: Mutex<W>,
}

impl<W> SharedUciOutput<W> {
    /// Wraps one owned output stream.
    pub(crate) const fn new(writer: W) -> Self {
        Self {
            writer: Mutex::new(writer),
        }
    }

    /// Writes and flushes one complete protocol line atomically.
    pub(crate) fn write_line(&self, line: &str) -> io::Result<()>
    where
        W: Write,
    {
        let mut writer = self.lock_writer()?;
        writeln!(writer, "{line}")?;
        writer.flush()
    }

    fn lock_writer(&self) -> io::Result<MutexGuard<'_, W>> {
        self.writer
            .lock()
            .map_err(|_| io::Error::other("UCI output lock is poisoned"))
    }
}

impl<W> SearchOutput for SharedUciOutput<W>
where
    W: Write + Send + 'static,
{
    fn report_progress(&self, progress: SearchProgress<'_>, elapsed: Duration) -> io::Result<()> {
        self.write_line(&format_info(progress, elapsed))
    }

    fn report_bestmove(&self, result: &SearchResult) -> io::Result<()> {
        self.write_line(&format_bestmove(result))
    }

    fn report_error(&self, message: &str) -> io::Result<()> {
        self.write_line(&format!("info string error: {message}"))
    }
}

fn format_info(progress: SearchProgress<'_>, elapsed: Duration) -> String {
    let iteration = progress.iteration();
    let elapsed_ms = elapsed_milliseconds(elapsed);
    let mut line = String::new();
    write!(
        line,
        "info depth {} seldepth {} score {} nodes {} nps {} time {} hashfull {}",
        iteration.depth(),
        progress.selective_depth(),
        score_text(iteration.score()),
        progress.nodes(),
        nodes_per_second(progress.nodes(), elapsed_ms),
        elapsed_ms,
        iteration.hash_full().per_mille(),
    )
    .expect("writing to an owned String cannot fail");

    let principal_variation = iteration.principal_variation().moves();
    if !principal_variation.is_empty() {
        line.push_str(" pv");
        for current in principal_variation {
            line.push(' ');
            line.push_str(&current.to_uci());
        }
    }
    line
}

fn format_bestmove(result: &SearchResult) -> String {
    format_bestmove_moves(result.best_move(), result.ponder_move())
}

fn format_bestmove_moves(
    best_move: Option<chess_core::Move>,
    ponder_move: Option<chess_core::Move>,
) -> String {
    let Some(best_move) = best_move else {
        return "bestmove 0000".to_owned();
    };

    let mut line = format!("bestmove {}", best_move.to_uci());
    if let Some(ponder_move) = ponder_move {
        write!(line, " ponder {}", ponder_move.to_uci())
            .expect("writing to an owned String cannot fail");
    }
    line
}

fn score_text(score: Score) -> String {
    if !score.is_mate() {
        return format!("cp {}", score.centipawns());
    }

    let raw = score.centipawns();
    let distance_plies = MATE_SCORE.saturating_sub(raw.abs());
    let distance_moves = distance_plies.saturating_add(1) / 2;
    let signed_moves = if raw < 0 {
        -distance_moves
    } else {
        distance_moves
    };
    format!("mate {signed_moves}")
}

fn elapsed_milliseconds(elapsed: Duration) -> u64 {
    u64::try_from(elapsed.as_millis()).unwrap_or(u64::MAX)
}

fn nodes_per_second(nodes: u64, elapsed_ms: u64) -> u64 {
    let scaled = u128::from(nodes).saturating_mul(1_000);
    let rate = scaled / u128::from(elapsed_ms.max(1));
    u64::try_from(rate).unwrap_or(u64::MAX)
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use chess_core::{Position, SearchHistory};
    use chess_search::{
        iterative_deepening_search_with_limits_and_transposition_table_and_observer, Score,
        SearchLimits, TranspositionTable,
    };

    use super::{
        format_bestmove, format_bestmove_moves, format_info, nodes_per_second, score_text,
    };

    #[test]
    fn score_format_distinguishes_centipawns_and_signed_mate_distance() {
        assert_eq!(score_text(Score::from_evaluation(37)), "cp 37");
        assert_eq!(
            score_text(Score::mate_in(3).expect("mate distance is supported")),
            "mate 2"
        );
        assert_eq!(
            score_text(Score::mated_in(1).expect("mate distance is supported")),
            "mate -1"
        );
    }

    #[test]
    fn nps_is_defined_at_zero_time_and_saturates_safely() {
        assert_eq!(nodes_per_second(25, 0), 25_000);
        assert_eq!(nodes_per_second(1_000, 250), 4_000);
        assert_eq!(nodes_per_second(u64::MAX, 1), u64::MAX);
    }

    #[test]
    fn completed_iteration_formats_all_required_uci_fields() {
        let mut position = Position::starting();
        let mut history = SearchHistory::from_position(&position);
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let mut lines = Vec::new();

        let result = iterative_deepening_search_with_limits_and_transposition_table_and_observer(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(2),
            &mut table,
            |progress| lines.push(format_info(progress, Duration::from_millis(10))),
        )
        .expect("observed search succeeds");

        assert_eq!(result.completed_depth(), 2);
        assert_eq!(lines.len(), 2);
        for (index, line) in lines.iter().enumerate() {
            assert!(line.starts_with(&format!("info depth {} seldepth ", index + 1)));
            assert!(line.contains(" score cp "));
            assert!(line.contains(" nodes "));
            assert!(line.contains(" nps "));
            assert!(line.contains(" time 10 "));
            assert!(line.contains(" hashfull "));
            assert!(line.contains(" pv "));
        }
    }

    #[test]
    fn final_output_contains_bestmove_and_available_ponder() {
        let mut position = Position::starting();
        let moves: Vec<_> = position
            .legal_move_tokens()
            .expect("starting position has legal moves")
            .iter()
            .take(2)
            .map(|token| token.move_made())
            .collect();
        let best_move = moves[0];
        let ponder_move = moves[1];

        assert_eq!(
            format_bestmove_moves(Some(best_move), Some(ponder_move)),
            format!(
                "bestmove {} ponder {}",
                best_move.to_uci(),
                ponder_move.to_uci()
            )
        );
    }

    #[test]
    fn terminal_root_uses_uci_null_bestmove() {
        let mut position: Position = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
            .parse()
            .expect("terminal FEN is valid");
        let mut history = SearchHistory::from_position(&position);
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let result = iterative_deepening_search_with_limits_and_transposition_table_and_observer(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(1),
            &mut table,
            |_| {},
        )
        .expect("terminal search succeeds");

        assert_eq!(format_bestmove(&result), "bestmove 0000");
    }
}
