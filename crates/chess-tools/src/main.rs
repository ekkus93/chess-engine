#![forbid(unsafe_code)]
//! Offline command-line tools for perft, divide, fixtures, benchmarks, and
//! self-play.
//!
//! Tooling may orchestrate the core and search crates but must not become a
//! dependency of them.

use std::{env, io, process::ExitCode};

use chess_tools::{divide, legal_uci, perft, play_uci, run_oracle, suite, STARTING_FEN};

fn usage() -> &'static str {
    "usage:\n  chess-tools legal [FEN]\n  chess-tools play UCI [FEN]\n  chess-tools perft DEPTH [FEN]\n  chess-tools divide DEPTH [FEN]\n  chess-tools suite MAX_DEPTH\n  chess-tools oracle"
}

fn parse_depth(value: &str) -> Result<u8, String> {
    value
        .parse::<u8>()
        .map_err(|error| format!("invalid depth {value:?}: {error}"))
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
