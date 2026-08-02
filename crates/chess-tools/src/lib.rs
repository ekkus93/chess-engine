#![forbid(unsafe_code)]
//! Deterministic offline validation primitives for the Rust chess engine.

use core::fmt;
use std::io::{BufRead, Write};

use chess_core::{Move, Position, UciMove};

/// Canonical standard starting-position FEN.
pub const STARTING_FEN: &str =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

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
        other => Err(ToolError::new(format!(
            "unknown oracle command {other:?}"
        ))),
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

    use super::{divide, legal_uci, perft_fixtures, play_uci, run_oracle, STARTING_FEN};

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
}
