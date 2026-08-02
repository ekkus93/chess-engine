from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected one replacement target, found {count}: {old[:120]!r}"
        )
    write(path, text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker in text:
        return
    write(path, text.rstrip() + "\n\n" + addition.strip() + "\n")


main = "crates/chess-tools/src/main.rs"
replace_once(
    main,
    "use std::{env, fs, io, process::ExitCode};",
    "use std::{env, fs, io, process::ExitCode, time::Instant};",
)

divide_helper = r'''
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

'''
replace_once(
    main,
    "fn run(arguments: &[String]) -> Result<(), String> {",
    divide_helper + "fn run(arguments: &[String]) -> Result<(), String> {",
)
replace_once(
    main,
    '''        "divide" => {
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
''',
    '''        "divide" => {
            let depth = parse_depth(arguments.get(1).ok_or_else(|| usage().to_owned())?)?;
            let fen = optional_fen(arguments, 2)?;
            for line in divide_output(fen, depth)? {
                println!("{line}");
            }
        }
''',
)
append_once(
    main,
    "fn divide_output_is_sorted_totalled_and_timed()",
    r'''
#[cfg(test)]
mod tests {
    use super::{divide_output, STARTING_FEN};

    #[test]
    fn divide_output_is_sorted_totalled_and_timed() {
        let lines = divide_output(STARTING_FEN, 2).expect("divide output succeeds");
        assert_eq!(lines.len(), 22);
        assert!(lines[..20].windows(2).all(|pair| {
            pair[0].split('\t').next() < pair[1].split('\t').next()
        }));
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
''',
)

append_once(
    "docs/RUST_MAKE_UNMAKE.md",
    "## Public generated-legal token API",
    r'''
## Public generated-legal token API

Task 13 lives in the separate `chess-search` crate, so the crate-private generated path cannot be called directly. `Position::legal_move_tokens()` exposes a bounded list of opaque `LegalMoveToken` values. Each token binds one exact packed move to the source position's canonical Zobrist key, side to move, castling rights, raw en-passant target, halfmove clock, and fullmove number.

`Position::make_legal_token()` verifies this origin before mutation and then delegates to the existing generated-legal reversible primitive. A stale token or a token from a different source position returns `LegalMoveError::LegalMoveTokenMismatch` without changing any field. A valid token does not regenerate legal moves. The fully checked `Position::make_move(Move)` remains the public path for callers that have only a raw move identity.
''',
)
append_once(
    "docs/RUST_GAME_HISTORY_AND_DRAWS.md",
    "## Root replacement",
    r'''
## Root replacement

`Game::reset_to_starting()` replaces the game with a fresh standard starting position. `Game::set_position(Position)` establishes a caller-supplied validated position as a new root. Both operations clear the played-move list and replace position-hash history with exactly one root key. Prior repetition history is never merged into the new root, and old `GameUndo` tokens cannot be applied successfully after replacement.

These APIs are infallible because `Position` values are already structurally validated. They provide the explicit state-replacement semantics needed by future UCI `ucinewgame` and `position` handling without exposing mutable access to the internal position.
''',
)
replace_once(
    "docs/RUST_PERFT_AND_DIFFERENTIAL_VALIDATION.md",
    "Legal moves and divide rows are sorted by canonical UCI text. Divide emits one tab-delimited move/count row followed by a tab-delimited total, so a perft mismatch can be localized to a root move and compared mechanically.",
    "Legal moves and divide rows are sorted by canonical UCI text. Divide emits one tab-delimited move/count row followed by `total\\t<N>` and `elapsed_nanos\\t<N>`. The stable timing field measures divide calculation and total accumulation before output, while the move rows remain mechanically comparable.",
)
append_once(
    "docs/RUST_FEN_AND_UCI_NOTATION.md",
    "## FEN validation policy",
    r'''
## FEN validation policy

`Position::from_fen` is a strict syntax and structural **analysis-position** parser. It does not attempt to prove that a position is reachable from the standard initial position.

It rejects malformed field counts and placement, invalid piece or counter syntax, pawns on rank one or eight, invalid en-passant target ranks, occupied en-passant targets, and positions without exactly one king of each color. It constructs a fresh position and validates mailbox, bitboard, occupancy, cached-king, en-passant, and hash invariants before returning.

It intentionally accepts structurally coherent analysis states that may be illegal or unreachable in an actual game, including:

- castling rights without the matching home rook or with the king away from its home square;
- a correctly ranked but non-capturable en-passant target;
- adjacent kings;
- both kings in check;
- either the side to move or the side not to move already being in check;
- unusual material that cannot arise from the standard initial set.

Legal move generation remains fail-safe for these states: it never permits king capture, refuses castling when required pieces or safety conditions are absent, and filters moves against king attack. Zobrist repetition identity includes an en-passant file only when a legal en-passant capture exists, so accepted non-capturable targets do not create a false repetition distinction. The committed differential corpus remains restricted to positions accepted as valid by the pinned independent oracle.
''',
)
