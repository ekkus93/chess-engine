#![forbid(unsafe_code)]
//! Offline command-line tools for perft, divide, fixtures, benchmarks, and
//! self-play.
//!
//! Tooling may orchestrate the core and search crates but must not become a
//! dependency of them.

use std::{env, fs, io, process::ExitCode, time::Instant};

mod tuning_cli;

use chess_search::EvaluationWeightSet;

use chess_tools::self_play::{
    generate_self_play_dataset, OpeningSuite, SelfPlayDataset, SelfPlayFileConfig,
    SELF_PLAY_DATASET_SCHEMA_VERSION,
};
use chess_tools::{
    benchmark_cancellation, benchmark_evaluation, benchmark_transposition, deserialize_weight_set,
    divide, evaluation_trace, legal_uci, perft, play_uci, run_oracle, serialize_weight_set, suite,
    STARTING_FEN,
};

fn usage() -> &'static str {
    "usage:\n  chess-tools legal [FEN]\n  chess-tools play UCI [FEN]\n  chess-tools perft DEPTH [FEN]\n  chess-tools divide DEPTH [FEN]\n  chess-tools suite MAX_DEPTH\n  chess-tools eval [FEN]\n  chess-tools eval-bench ITERATIONS [FEN]\n  chess-tools tt-bench ITERATIONS\n  chess-tools cancel-bench ITERATIONS\n  chess-tools weights-export\n  chess-tools weights-validate PATH\n  chess-tools self-play CONFIG_PATH OUTPUT_PATH\n  chess-tools self-play-validate DATASET_PATH\n  chess-tools self-play-replay DATASET_PATH GAME_ID\n  chess-tools tune CONFIG_PATH DATASET_PATH OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]\n  chess-tools oracle"
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

fn divide_output(fen: &str, depth: u8) -> Result<Vec<String>, String> {
    let started = Instant::now();
    let rows = divide(fen, depth).map_err(|error| error.to_string())?;
    let total = rows
        .iter()
        .try_fold(0_u64, |sum, (_, nodes)| sum.checked_add(*nodes))
        .ok_or_else(|| "divide total overflow".to_owned())?;
    let elapsed_nanos = started.elapsed().as_nanos();
    let mut output = Vec::with_capacity(rows.len() + 2);
    output.extend(
        rows.into_iter()
            .map(|(current, nodes)| format!("{current}\t{nodes}")),
    );
    output.push(format!("total\t{total}"));
    output.push(format!("elapsed_nanos\t{elapsed_nanos}"));
    Ok(output)
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
            for line in divide_output(fen, depth)? {
                println!("{line}");
            }
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
        "tt-bench" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let iterations = parse_iterations(&arguments[1])?;
            for row in benchmark_transposition(iterations).map_err(|error| error.to_string())? {
                println!(
                    "{}\t{}\t{}\t{}",
                    row.operation, row.iterations, row.elapsed_nanos, row.checksum
                );
            }
        }
        "cancel-bench" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let iterations = parse_iterations(&arguments[1])?;
            let row = benchmark_cancellation(iterations).map_err(|error| error.to_string())?;
            println!(
                "{}\t{}\t{}\t{}\t{}\t{}\t{}",
                row.operation,
                row.iterations,
                row.request_after_nodes,
                row.maximum_response_nodes,
                row.total_latency_nanos,
                row.maximum_latency_nanos,
                row.checksum
            );
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
        "self-play" => {
            if arguments.len() != 3 {
                return Err(usage().to_owned());
            }
            let config_text = fs::read_to_string(&arguments[1])
                .map_err(|error| format!("failed to read {:?}: {error}", arguments[1]))?;
            let file_config =
                SelfPlayFileConfig::from_text(&config_text).map_err(|error| error.to_string())?;
            let opening_text = fs::read_to_string(file_config.opening_path()).map_err(|error| {
                format!("failed to read {:?}: {error}", file_config.opening_path())
            })?;
            let openings =
                OpeningSuite::from_text(&opening_text).map_err(|error| error.to_string())?;
            let dataset =
                generate_self_play_dataset(file_config.config(), &openings, &arguments[2])
                    .map_err(|error| error.to_string())?;
            let output = dataset.to_text();
            fs::write(&arguments[2], output)
                .map_err(|error| format!("failed to write {:?}: {error}", arguments[2]))?;
            println!("schema\t{SELF_PLAY_DATASET_SCHEMA_VERSION}");
            println!("games\t{}", dataset.games().len());
            println!("positions\t{}", dataset.positions().len());
        }
        "self-play-validate" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let text = fs::read_to_string(&arguments[1])
                .map_err(|error| format!("failed to read {:?}: {error}", arguments[1]))?;
            let dataset = SelfPlayDataset::from_text(&text).map_err(|error| error.to_string())?;
            println!("schema\t{SELF_PLAY_DATASET_SCHEMA_VERSION}");
            println!("games\t{}", dataset.games().len());
            println!("positions\t{}", dataset.positions().len());
        }
        "self-play-replay" => {
            if arguments.len() != 3 {
                return Err(usage().to_owned());
            }
            let game_id = arguments[2]
                .parse::<u32>()
                .map_err(|error| format!("invalid game id {:?}: {error}", arguments[2]))?;
            let text = fs::read_to_string(&arguments[1])
                .map_err(|error| format!("failed to read {:?}: {error}", arguments[1]))?;
            let dataset = SelfPlayDataset::from_text(&text).map_err(|error| error.to_string())?;
            let replay = dataset
                .replay_game(game_id)
                .map_err(|error| error.to_string())?;
            println!("game\t{}", replay.game_id());
            println!("plies\t{}", replay.plies());
            println!("result\t{}", replay.result());
            println!("termination\t{}", replay.termination());
            println!("final_fen\t{}", replay.final_fen());
        }
        "tune" => {
            tuning_cli::run_tuning_command(&arguments[1..])?;
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

#[cfg(test)]
mod tests {
    use super::{divide_output, STARTING_FEN};

    #[test]
    fn divide_output_is_sorted_totalled_and_timed() {
        let lines = divide_output(STARTING_FEN, 2).expect("divide output succeeds");
        assert_eq!(lines.len(), 22);
        assert!(lines[..20]
            .windows(2)
            .all(|pair| { pair[0].split('\t').next() < pair[1].split('\t').next() }));
        assert_eq!(lines[20], "total\t400");
        let elapsed = lines[21]
            .strip_prefix("elapsed_nanos\t")
            .expect("elapsed field exists")
            .parse::<u128>()
            .expect("elapsed value is an unsigned integer");
        assert!(elapsed > 0);
    }

    #[test]
    fn depth_zero_divide_keeps_stable_summary_shape() {
        let lines = divide_output(STARTING_FEN, 0).expect("depth-zero divide succeeds");
        assert_eq!(lines.len(), 2);
        assert_eq!(lines[0], "total\t0");
        assert!(lines[1].starts_with("elapsed_nanos\t"));
    }
}
