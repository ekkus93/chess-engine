#![forbid(unsafe_code)]
//! Offline command-line tools for perft, divide, fixtures, benchmarks, and
//! self-play.
//!
//! Tooling may orchestrate the core and search crates but must not become a
//! dependency of them.

use std::{env, fs, io, process::ExitCode};

use chess_search::EvaluationWeightSet;
use chess_tools::{
    benchmark_evaluation, deserialize_weight_set, divide, evaluation_trace, legal_uci, perft,
    play_uci, run_oracle, serialize_weight_set, suite, STARTING_FEN,
};

fn usage() -> &'static str {
    "usage:\n  chess-tools legal [FEN]\n  chess-tools play UCI [FEN]\n  chess-tools perft DEPTH [FEN]\n  chess-tools divide DEPTH [FEN]\n  chess-tools suite MAX_DEPTH\n  chess-tools eval [FEN]\n  chess-tools eval-bench ITERATIONS [FEN]\n  chess-tools weights-export\n  chess-tools weights-validate PATH\n  chess-tools oracle"
}

fn parse_depth(value: &str) -> Result<u8, String> {
    value
        .parse::<u8>()
        .map_err(|error| format!("invalid depth {value:?}: {error}"))
}

fn parse_iterations(value: &str) -> Result<u64, String> {
    let iterations = value
        .parse::<u64>()
        .map_err(|error| format!("invalid iteration count {value:?}: {error}"))?;
    if iterations == 0 {
        return Err("iteration count must be greater than zero".to_owned());
    }
    Ok(iterations)
}

fn optional_fen(arguments: &[String], index: usize) -> Result<&str, String> {
    match arguments.get(index) {
        Some(fen) if arguments.len() == index + 1 => Ok(fen),
        None if arguments.len() == index => Ok(STARTING_FEN),
        _ => Err(usage().to_owned()),
    }
}

fn run(arguments: &[String]) -> Result<(), String> {
    let command = arguments.first().ok_or_else(|| usage().to_owned())?;
    match command.as_str() {
        "legal" => {
            let fen = optional_fen(arguments, 1)?;
            for current in legal_uci(fen).map_err(|error| error.to_string())? {
                println!("{current}");
            }
        }
        "play" => {
            let current = arguments.get(1).ok_or_else(|| usage().to_owned())?;
            let fen = optional_fen(arguments, 2)?;
            println!(
                "{}",
                play_uci(fen, current).map_err(|error| error.to_string())?
            );
        }
        "perft" => {
            let depth = parse_depth(arguments.get(1).ok_or_else(|| usage().to_owned())?)?;
            let fen = optional_fen(arguments, 2)?;
            println!("{}", perft(fen, depth).map_err(|error| error.to_string())?);
        }
        "divide" => {
            let depth = parse_depth(arguments.get(1).ok_or_else(|| usage().to_owned())?)?;
            let fen = optional_fen(arguments, 2)?;
            let rows = divide(fen, depth).map_err(|error| error.to_string())?;
            let total = rows
                .iter()
                .try_fold(0_u64, |sum, (_, nodes)| sum.checked_add(*nodes))
                .ok_or_else(|| "divide total overflow".to_owned())?;
            for (current, nodes) in rows {
                println!("{current}\t{nodes}");
            }
            println!("total\t{total}");
        }
        "suite" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let depth = parse_depth(&arguments[1])?;
            for row in suite(depth).map_err(|error| error.to_string())? {
                println!("{row}");
            }
        }
        "eval" => {
            let fen = optional_fen(arguments, 1)?;
            let trace = evaluation_trace(fen).map_err(|error| error.to_string())?;
            println!("phase\t{}", trace.phase);
            println!("material\t{}", trace.material);
            println!("piece_square\t{}", trace.piece_square);
            println!("mobility\t{}", trace.mobility);
            println!("isolated_pawns\t{}", trace.isolated_pawns);
            println!("doubled_pawns\t{}", trace.doubled_pawns);
            println!("passed_pawns\t{}", trace.passed_pawns);
            println!("connected_pawns\t{}", trace.connected_pawns);
            println!("bishop_pair\t{}", trace.bishop_pair);
            println!("rook_files\t{}", trace.rook_files);
            println!("rook_seventh\t{}", trace.rook_seventh);
            println!("king_shield\t{}", trace.king_shield);
            println!("king_zone_attack\t{}", trace.king_zone_attack);
            println!("space\t{}", trace.space);
            println!("king_activity\t{}", trace.king_activity);
            println!("total\t{}", trace.total);
        }
        "eval-bench" => {
            let iterations = parse_iterations(arguments.get(1).ok_or_else(|| usage().to_owned())?)?;
            let fen = optional_fen(arguments, 2)?;
            for row in benchmark_evaluation(fen, iterations).map_err(|error| error.to_string())? {
                println!(
                    "{}\t{}\t{}\t{}",
                    row.term, row.iterations, row.elapsed_nanos, row.checksum
                );
            }
        }
        "weights-export" => {
            if arguments.len() != 1 {
                return Err(usage().to_owned());
            }
            print!(
                "{}",
                serialize_weight_set(&EvaluationWeightSet::baseline())
                    .map_err(|error| error.to_string())?
            );
        }
        "weights-validate" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let text = fs::read_to_string(&arguments[1])
                .map_err(|error| format!("failed to read {:?}: {error}", arguments[1]))?;
            let set = deserialize_weight_set(&text).map_err(|error| error.to_string())?;
            println!("identifier\t{:016x}", set.identifier);
            println!("checksum\t{:016x}", set.checksum);
        }
        "oracle" => {
            if arguments.len() != 1 {
                return Err(usage().to_owned());
            }
            let stdin = io::stdin();
            let stdout = io::stdout();
            run_oracle(stdin.lock(), stdout.lock()).map_err(|error| error.to_string())?;
        }
        _ => return Err(usage().to_owned()),
    }
    Ok(())
}

fn main() -> ExitCode {
    let arguments: Vec<_> = env::args().skip(1).collect();
    match run(&arguments) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("chess-tools: {error}");
            ExitCode::FAILURE
        }
    }
}
