#![forbid(unsafe_code)]
//! Deterministic offline validation primitives for the Rust chess engine.

pub mod self_play;
mod weights_io;

use core::fmt;
use std::{
    hint::black_box,
    io::{BufRead, Write},
    time::Instant,
};

use chess_core::{Move, Position, SearchHistory, UciMove};
use chess_search::{
    alpha_beta_search_with_cancellation, evaluate_term, evaluate_trace as search_evaluate_trace,
    AlphaBetaSearchError, EvaluationTerm, EvaluationTrace, EvaluationWeightSet, Score,
    SearchCancellationProbe, TranspositionBound, TranspositionEntry, TranspositionProbeRequest,
    TranspositionProbeScore, TranspositionScore, TranspositionScoreReuse, TranspositionStoreAction,
    TranspositionTable, CANCELLATION_CHECK_INTERVAL_NODES,
};

pub use weights_io::{deserialize_weight_set, serialize_weight_set};

/// Canonical standard starting-position FEN.
pub const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

const PERFT_FIXTURES: &str = include_str!("../../../fixtures/perft.tsv");

/// A deterministic tooling error intended for command-line diagnostics.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ToolError {
    message: String,
}

impl ToolError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl fmt::Display for ToolError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl std::error::Error for ToolError {}

/// One authoritative perft fixture and its depth-one through depth-five counts.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PerftFixture<'a> {
    /// Stable fixture identifier.
    pub name: &'a str,
    /// Complete six-field FEN.
    pub fen: &'a str,
    /// Exact node counts for depths one through five.
    pub expected: [u64; 5],
}

/// Parses the repository's compile-time authoritative perft manifest.
pub fn perft_fixtures() -> Result<Vec<PerftFixture<'static>>, ToolError> {
    PERFT_FIXTURES
        .lines()
        .skip(1)
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let fields: Vec<_> = line.split('\t').collect();
            if fields.len() != 7 {
                return Err(ToolError::new(format!(
                    "invalid perft fixture row with {} fields: {line}",
                    fields.len()
                )));
            }
            let parse_count = |field: &str, depth: u8| {
                field.parse::<u64>().map_err(|error| {
                    ToolError::new(format!(
                        "invalid depth-{depth} count for {}: {error}",
                        fields[0]
                    ))
                })
            };
            Ok(PerftFixture {
                name: fields[0],
                fen: fields[1],
                expected: [
                    parse_count(fields[2], 1)?,
                    parse_count(fields[3], 2)?,
                    parse_count(fields[4], 3)?,
                    parse_count(fields[5], 4)?,
                    parse_count(fields[6], 5)?,
                ],
            })
        })
        .collect()
}

fn parse_position(fen: &str) -> Result<Position, ToolError> {
    Position::from_fen(fen).map_err(|error| ToolError::new(error.to_string()))
}

fn resolve_uci(position: &mut Position, value: &str) -> Result<Move, ToolError> {
    let syntax = value
        .parse::<UciMove>()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let legal = position
        .legal_moves()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut matches = legal.iter().filter(|candidate| syntax.matches(*candidate));
    let current = matches
        .next()
        .ok_or_else(|| ToolError::new(format!("move {value} is not legal")))?;
    if matches.next().is_some() {
        return Err(ToolError::new(format!(
            "move {value} resolved to more than one legal identity"
        )));
    }
    Ok(current)
}

/// Returns the sorted legal UCI move set for `fen`.
pub fn legal_uci(fen: &str) -> Result<Vec<String>, ToolError> {
    let mut position = parse_position(fen)?;
    let mut moves: Vec<_> = position
        .legal_moves()
        .map_err(|error| ToolError::new(error.to_string()))?
        .iter()
        .map(Move::to_uci)
        .collect();
    moves.sort_unstable();
    Ok(moves)
}

/// Returns the canonical FEN after applying one exact legal UCI move.
pub fn play_uci(fen: &str, value: &str) -> Result<String, ToolError> {
    let mut position = parse_position(fen)?;
    let current = resolve_uci(&mut position, value)?;
    let _undo = position
        .make_move(current)
        .map_err(|error| ToolError::new(error.to_string()))?;
    Ok(position.to_fen())
}

/// Returns the exact legal leaf count for `fen` and `depth`.
pub fn perft(fen: &str, depth: u8) -> Result<u64, ToolError> {
    let mut position = parse_position(fen)?;
    position
        .perft(depth)
        .map_err(|error| ToolError::new(error.to_string()))
}

/// Returns deterministic UCI-sorted root divide counts.
pub fn divide(fen: &str, depth: u8) -> Result<Vec<(String, u64)>, ToolError> {
    let mut position = parse_position(fen)?;
    let mut rows: Vec<_> = position
        .divide(depth)
        .map_err(|error| ToolError::new(error.to_string()))?
        .into_iter()
        .map(|(current, nodes)| (current.to_uci(), nodes))
        .collect();
    rows.sort_unstable_by(|left, right| left.0.cmp(&right.0));
    Ok(rows)
}

/// Runs every authoritative fixture through `max_depth`, returning stable rows.
pub fn suite(max_depth: u8) -> Result<Vec<String>, ToolError> {
    if !(1..=5).contains(&max_depth) {
        return Err(ToolError::new(format!(
            "suite depth must be between one and five, found {max_depth}"
        )));
    }
    let mut rows = Vec::new();
    for fixture in perft_fixtures()? {
        for depth in 1..=max_depth {
            let expected = fixture.expected[usize::from(depth - 1)];
            let actual = perft(fixture.fen, depth)?;
            if actual != expected {
                return Err(ToolError::new(format!(
                    "{} depth {depth}: expected {expected}, found {actual}",
                    fixture.name
                )));
            }
            rows.push(format!(
                "{}\t{}\t{}\t{}",
                fixture.name, depth, actual, fixture.fen
            ));
        }
    }
    Ok(rows)
}

/// One stable evaluator benchmark result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EvaluationBenchmarkRow {
    /// Stable coarse evaluator term name.
    pub term: &'static str,
    /// Number of evaluations performed.
    pub iterations: u64,
    /// Wall-clock duration in nanoseconds.
    pub elapsed_nanos: u128,
    /// Deterministic accumulator preventing dead-code elimination.
    pub checksum: i64,
}

/// Returns the named static-evaluation trace for `fen`.
pub fn evaluation_trace(fen: &str) -> Result<EvaluationTrace, ToolError> {
    let position = parse_position(fen)?;
    Ok(search_evaluate_trace(&position))
}

/// Benchmarks every major evaluator group and the complete evaluation.
pub fn benchmark_evaluation(
    fen: &str,
    iterations: u64,
) -> Result<Vec<EvaluationBenchmarkRow>, ToolError> {
    if iterations == 0 {
        return Err(ToolError::new(
            "evaluation benchmark requires at least one iteration",
        ));
    }
    let position = parse_position(fen)?;
    let weight_set = EvaluationWeightSet::baseline();
    weight_set
        .validate()
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut rows = Vec::with_capacity(EvaluationTerm::ALL.len());
    for term in EvaluationTerm::ALL {
        let started = Instant::now();
        let mut checksum = 0_i64;
        for _ in 0..iterations {
            let score = evaluate_term(
                black_box(&position),
                black_box(&weight_set.weights),
                black_box(term),
            );
            checksum = checksum.wrapping_add(i64::from(black_box(score.centipawns())));
        }
        rows.push(EvaluationBenchmarkRow {
            term: term.name(),
            iterations,
            elapsed_nanos: started.elapsed().as_nanos(),
            checksum,
        });
    }
    Ok(rows)
}

/// One stable transposition-table microbenchmark result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionBenchmarkRow {
    /// Stable operation name: `store` or `probe`.
    pub operation: &'static str,
    /// Number of timed operations performed.
    pub iterations: u64,
    /// Wall-clock duration in nanoseconds.
    pub elapsed_nanos: u128,
    /// Deterministic accumulator preventing dead-code elimination.
    pub checksum: u64,
}

const TRANSPOSITION_BENCHMARK_MEBIBYTES: usize = 1;
const TRANSPOSITION_BENCHMARK_FIXTURE_ENTRIES: usize = 4_096;

fn transposition_benchmark_key(index: u64) -> u64 {
    index.wrapping_mul(0x9e37_79b9_7f4a_7c15).rotate_left(17) ^ 0xd1b5_4a32_d192_ed03
}

/// Benchmarks deterministic fixed-fixture transposition stores and probes.
///
/// Timing is informational and is not a correctness threshold. The checksum,
/// operation ordering, table size, fixture population, and three-hit/one-miss
/// probe pattern are deterministic for a fixed iteration count.
pub fn benchmark_transposition(
    iterations: u64,
) -> Result<Vec<TranspositionBenchmarkRow>, ToolError> {
    if iterations == 0 {
        return Err(ToolError::new(
            "transposition benchmark requires at least one iteration",
        ));
    }

    let normalized_zero = TranspositionScore::normalize(Score::ZERO, 0)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut store_table = TranspositionTable::new(TRANSPOSITION_BENCHMARK_MEBIBYTES)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let store_started = Instant::now();
    let mut store_checksum = 0_u64;
    for iteration in 0..iterations {
        let key = black_box(transposition_benchmark_key(iteration));
        let depth = u16::try_from(iteration % 64 + 1).expect("benchmark depth is bounded");
        let entry = TranspositionEntry::new(
            key,
            depth,
            TranspositionBound::Exact,
            normalized_zero,
            None,
            0,
        );
        let result = black_box(store_table.store(black_box(entry)));
        let action_code = match result.action() {
            TranspositionStoreAction::UpdatedSameKey { .. } => 1_u64,
            TranspositionStoreAction::InsertedEmpty => 2,
            TranspositionStoreAction::ReplacedCollision { .. } => 3,
        };
        store_checksum = store_checksum
            .wrapping_add(key)
            .wrapping_add(result.cluster_index() as u64)
            .wrapping_add(result.slot_index() as u64)
            .wrapping_add(action_code);
    }
    let store_row = TranspositionBenchmarkRow {
        operation: "store",
        iterations,
        elapsed_nanos: store_started.elapsed().as_nanos(),
        checksum: black_box(store_checksum),
    };

    let mut probe_table = TranspositionTable::new(TRANSPOSITION_BENCHMARK_MEBIBYTES)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let fixture_entries = probe_table
        .entry_capacity()
        .min(TRANSPOSITION_BENCHMARK_FIXTURE_ENTRIES);
    for fixture_index in 0..fixture_entries {
        let key = fixture_index as u64 * 2 + 1;
        probe_table.store(TranspositionEntry::new(
            key,
            32,
            TranspositionBound::Exact,
            normalized_zero,
            None,
            0,
        ));
    }
    probe_table.reset_diagnostics();

    let probe_started = Instant::now();
    let mut probe_checksum = 0_u64;
    for iteration in 0..iterations {
        let fixture_index = iteration % fixture_entries as u64;
        let key = fixture_index * 2 + if iteration & 3 == 3 { 2 } else { 1 };
        let request = TranspositionProbeRequest::new(
            key,
            16,
            0,
            Score::from_evaluation(-1_000),
            Score::from_evaluation(1_000),
            TranspositionScoreReuse::Allowed,
        );
        let result = black_box(probe_table.probe(black_box(request)))
            .map_err(|error| ToolError::new(error.to_string()))?;
        let result_code = match result {
            None => 1_u64,
            Some(hit) => match hit.score() {
                Some(TranspositionProbeScore::Exact(_)) => 2,
                Some(TranspositionProbeScore::LowerBoundCutoff(_)) => 3,
                Some(TranspositionProbeScore::UpperBoundCutoff(_)) => 4,
                None => 5,
            },
        };
        probe_checksum = probe_checksum.wrapping_add(key).wrapping_add(result_code);
    }
    let probe_row = TranspositionBenchmarkRow {
        operation: "probe",
        iterations,
        elapsed_nanos: probe_started.elapsed().as_nanos(),
        checksum: black_box(probe_checksum),
    };

    Ok(vec![store_row, probe_row])
}

/// One cancellation-response benchmark result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CancellationBenchmarkRow {
    /// Stable operation name.
    pub operation: &'static str,
    /// Number of independent cancellation samples.
    pub iterations: u64,
    /// Production nodes entered before the synthetic external request.
    pub request_after_nodes: u64,
    /// Largest observed number of additional node entries after the request.
    pub maximum_response_nodes: u64,
    /// Sum of measured request-to-return latency in nanoseconds.
    pub total_latency_nanos: u128,
    /// Largest measured request-to-return latency in nanoseconds.
    pub maximum_latency_nanos: u128,
    /// Deterministic accumulator over node and restoration evidence.
    pub checksum: u64,
}

const CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES: u64 = 64;
const CANCELLATION_BENCHMARK_DEPTH: u16 = 5;

struct CancellationLatencyProbe {
    entered_nodes: u64,
    request_after_nodes: u64,
    requested_at_node: Option<u64>,
    observed_at_node: Option<u64>,
    requested_at: Option<Instant>,
    observed_latency_nanos: Option<u128>,
}

impl CancellationLatencyProbe {
    const fn new(request_after_nodes: u64) -> Self {
        Self {
            entered_nodes: 0,
            request_after_nodes,
            requested_at_node: None,
            observed_at_node: None,
            requested_at: None,
            observed_latency_nanos: None,
        }
    }

    fn observe(&mut self) {
        if self.observed_at_node.is_none() {
            self.observed_at_node = Some(self.entered_nodes);
            self.observed_latency_nanos = Some(
                self.requested_at
                    .expect("benchmark request timestamp exists")
                    .elapsed()
                    .as_nanos(),
            );
        }
    }
}

impl SearchCancellationProbe for CancellationLatencyProbe {
    fn should_cancel(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        if self.entered_nodes >= self.request_after_nodes {
            self.requested_at_node = Some(self.entered_nodes);
            self.requested_at = Some(Instant::now());
        }
        false
    }

    fn on_node(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        self.entered_nodes = self.entered_nodes.saturating_add(1);
        false
    }
}

/// Benchmarks deterministic mid-tree cancellation detection and unwind latency.
///
/// Wall-clock values are informational. The enforced correctness threshold is
/// the exported node interval: no sample may enter more than
/// `CANCELLATION_CHECK_INTERVAL_NODES` additional nodes after the request.
pub fn benchmark_cancellation(iterations: u64) -> Result<CancellationBenchmarkRow, ToolError> {
    if iterations == 0 {
        return Err(ToolError::new(
            "cancellation benchmark requires at least one iteration",
        ));
    }

    let mut maximum_response_nodes = 0_u64;
    let mut total_latency_nanos = 0_u128;
    let mut maximum_latency_nanos = 0_u128;
    let mut checksum = 0_u64;

    for sample in 0..iterations {
        let mut position = Position::starting();
        let position_snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut probe = CancellationLatencyProbe::new(CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES);

        let result = alpha_beta_search_with_cancellation(
            &mut position,
            &mut history,
            CANCELLATION_BENCHMARK_DEPTH,
            &mut probe,
        );
        if result != Err(AlphaBetaSearchError::Cancelled) {
            return Err(ToolError::new(
                "cancellation benchmark search did not terminate through cancellation",
            ));
        }
        if position != position_snapshot
            || history != history_snapshot
            || position.zobrist() != position.recomputed_zobrist()
            || history.current_zobrist() != Some(position.zobrist())
        {
            return Err(ToolError::new(
                "cancellation benchmark failed exact root restoration",
            ));
        }

        let requested_at_node = probe
            .requested_at_node
            .ok_or_else(|| ToolError::new("cancellation benchmark did not issue a request"))?;
        let observed_at_node = probe
            .observed_at_node
            .ok_or_else(|| ToolError::new("cancellation benchmark did not observe the request"))?;
        let response_nodes = observed_at_node.saturating_sub(requested_at_node);
        if response_nodes > CANCELLATION_CHECK_INTERVAL_NODES {
            return Err(ToolError::new(format!(
                "cancellation response used {response_nodes} nodes; bound is {CANCELLATION_CHECK_INTERVAL_NODES}"
            )));
        }
        let latency_nanos = probe
            .observed_latency_nanos
            .ok_or_else(|| ToolError::new("cancellation benchmark did not measure latency"))?;

        maximum_response_nodes = maximum_response_nodes.max(response_nodes);
        total_latency_nanos = total_latency_nanos.saturating_add(latency_nanos);
        maximum_latency_nanos = maximum_latency_nanos.max(latency_nanos);
        checksum = checksum
            .wrapping_mul(0x9e37_79b9_7f4a_7c15)
            .wrapping_add(requested_at_node.rotate_left(7))
            .wrapping_add(observed_at_node.rotate_left(17))
            .wrapping_add(position.zobrist())
            .wrapping_add(sample);
    }

    Ok(CancellationBenchmarkRow {
        operation: "cancel",
        iterations,
        request_after_nodes: CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES,
        maximum_response_nodes,
        total_latency_nanos,
        maximum_latency_nanos,
        checksum,
    })
}

fn sanitize_error(error: &ToolError) -> String {
    error
        .to_string()
        .chars()
        .map(|character| match character {
            '\t' | '\n' | '\r' => ' ',
            other => other,
        })
        .collect()
}

fn oracle_command(line: &str) -> Result<String, ToolError> {
    let mut fields = line.split('\t');
    let command = fields
        .next()
        .ok_or_else(|| ToolError::new("missing oracle command"))?;
    match command {
        "legal" => {
            let fen = fields
                .next()
                .ok_or_else(|| ToolError::new("legal requires a FEN"))?;
            if fields.next().is_some() {
                return Err(ToolError::new("legal received unexpected fields"));
            }
            Ok(legal_uci(fen)?.join(","))
        }
        "play" => {
            let value = fields
                .next()
                .ok_or_else(|| ToolError::new("play requires a UCI move"))?;
            let fen = fields
                .next()
                .ok_or_else(|| ToolError::new("play requires a FEN"))?;
            if fields.next().is_some() {
                return Err(ToolError::new("play received unexpected fields"));
            }
            play_uci(fen, value)
        }
        "perft" => {
            let depth = fields
                .next()
                .ok_or_else(|| ToolError::new("perft requires a depth"))?
                .parse::<u8>()
                .map_err(|error| ToolError::new(format!("invalid perft depth: {error}")))?;
            let fen = fields
                .next()
                .ok_or_else(|| ToolError::new("perft requires a FEN"))?;
            if fields.next().is_some() {
                return Err(ToolError::new("perft received unexpected fields"));
            }
            Ok(perft(fen, depth)?.to_string())
        }
        other => Err(ToolError::new(format!("unknown oracle command {other:?}"))),
    }
}

/// Serves a line-oriented, tab-delimited validation protocol.
///
/// Requests are `legal<TAB>FEN`, `play<TAB>UCI<TAB>FEN`, or
/// `perft<TAB>DEPTH<TAB>FEN`. Responses are `ok<TAB>VALUE` or
/// `error<TAB>MESSAGE`. `quit` terminates the stream after acknowledging it.
pub fn run_oracle<R: BufRead, W: Write>(reader: R, mut writer: W) -> Result<(), ToolError> {
    for line in reader.lines() {
        let line = line.map_err(|error| ToolError::new(error.to_string()))?;
        if line == "quit" {
            writeln!(writer, "ok\tbye").map_err(|error| ToolError::new(error.to_string()))?;
            writer
                .flush()
                .map_err(|error| ToolError::new(error.to_string()))?;
            break;
        }
        match oracle_command(&line) {
            Ok(value) => writeln!(writer, "ok\t{value}"),
            Err(error) => writeln!(writer, "error\t{}", sanitize_error(&error)),
        }
        .map_err(|error| ToolError::new(error.to_string()))?;
        writer
            .flush()
            .map_err(|error| ToolError::new(error.to_string()))?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use chess_search::CANCELLATION_CHECK_INTERVAL_NODES;

    use super::{
        benchmark_cancellation, benchmark_transposition, divide, legal_uci, perft_fixtures,
        play_uci, run_oracle, STARTING_FEN,
    };

    #[test]
    fn fixture_manifest_is_complete_and_stable() {
        let fixtures = perft_fixtures().expect("fixture manifest parses");
        assert_eq!(fixtures.len(), 6);
        assert_eq!(fixtures[0].name, "starting_position");
        assert_eq!(fixtures[0].expected, [20, 400, 8_902, 197_281, 4_865_609]);
    }

    #[test]
    fn legal_and_divide_output_is_sorted() {
        let legal = legal_uci(STARTING_FEN).expect("legal output succeeds");
        assert_eq!(legal.len(), 20);
        assert!(legal.windows(2).all(|pair| pair[0] < pair[1]));

        let rows = divide(STARTING_FEN, 2).expect("divide succeeds");
        assert_eq!(rows.len(), 20);
        assert!(rows.windows(2).all(|pair| pair[0].0 < pair[1].0));
        assert_eq!(rows.iter().map(|(_, nodes)| nodes).sum::<u64>(), 400);
    }

    #[test]
    fn legal_play_emits_canonical_child_fen() {
        assert_eq!(
            play_uci(STARTING_FEN, "e2e4").expect("legal play succeeds"),
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        );
    }

    #[test]
    fn oracle_protocol_is_machine_readable() {
        let input = format!("perft\t2\t{STARTING_FEN}\nlegal\t{STARTING_FEN}\nquit\n");
        let mut output = Vec::new();
        run_oracle(Cursor::new(input), &mut output).expect("oracle stream succeeds");
        let output = String::from_utf8(output).expect("oracle output is UTF-8");
        let lines: Vec<_> = output.lines().collect();
        assert_eq!(lines[0], "ok\t400");
        assert!(lines[1].starts_with("ok\t"));
        assert_eq!(lines[2], "ok\tbye");
    }

    #[test]
    fn cancellation_benchmark_enforces_the_node_bound_and_repeats_its_checksum() {
        assert!(benchmark_cancellation(0).is_err());
        let first = benchmark_cancellation(4).expect("cancellation benchmark succeeds");
        let second = benchmark_cancellation(4).expect("cancellation benchmark repeats");

        assert_eq!(first.operation, "cancel");
        assert_eq!(first.iterations, 4);
        assert_eq!(first.request_after_nodes, 64);
        assert!(first.maximum_response_nodes <= CANCELLATION_CHECK_INTERVAL_NODES);
        assert!(first.maximum_latency_nanos <= first.total_latency_nanos);
        assert_eq!(first.checksum, second.checksum);
    }

    #[test]
    fn transposition_benchmark_fixtures_and_checksums_are_reproducible() {
        assert!(benchmark_transposition(0).is_err());
        let first = benchmark_transposition(128).expect("benchmark succeeds");
        let second = benchmark_transposition(128).expect("benchmark repeats");

        assert_eq!(first.len(), 2);
        assert_eq!(first[0].operation, "store");
        assert_eq!(first[1].operation, "probe");
        assert!(first.iter().all(|row| row.iterations == 128));
        assert_eq!(first[0].checksum, second[0].checksum);
        assert_eq!(first[1].checksum, second[1].checksum);
    }
}
