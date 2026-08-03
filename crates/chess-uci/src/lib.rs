#![forbid(unsafe_code)]
//! Universal Chess Interface parsing and session state for the Linux adapter.
//!
//! Task 17.1 deliberately stops at the protocol boundary. It parses complete
//! UCI commands, owns transactional game state, and emits typed search requests.
//! Task 17.2 will consume those requests on an adapter-owned worker thread.

use std::io::{self, BufRead, Write};

use chess_core::{Game, Position, UciMove};
use chess_search::DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES;

const ENGINE_NAME: &str = "chess-engine-rust";
const ENGINE_AUTHOR: &str = "Phillip Chin";
const MIN_HASH_MEBIBYTES: usize = 1;
const MAX_HASH_MEBIBYTES: usize = 65_536;

/// Mutable UCI options supported by the current adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EngineOptions {
    hash_mebibytes: usize,
    check_extension: bool,
}

impl EngineOptions {
    /// Returns the configured transposition-table capacity in MiB.
    #[must_use]
    pub const fn hash_mebibytes(self) -> usize {
        self.hash_mebibytes
    }

    /// Returns whether the bounded one-ply check extension is enabled.
    #[must_use]
    pub const fn check_extension(self) -> bool {
        self.check_extension
    }
}

impl Default for EngineOptions {
    fn default() -> Self {
        Self {
            hash_mebibytes: DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
            check_extension: false,
        }
    }
}

/// Parsed limits and clock fields from one UCI `go` command.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct GoCommand {
    depth: Option<u16>,
    nodes: Option<u64>,
    move_time_ms: Option<u64>,
    white_time_ms: Option<u64>,
    black_time_ms: Option<u64>,
    white_increment_ms: Option<u64>,
    black_increment_ms: Option<u64>,
    moves_to_go: Option<u32>,
    infinite: bool,
}

impl GoCommand {
    /// Returns the requested maximum completed depth.
    #[must_use]
    pub const fn depth(self) -> Option<u16> {
        self.depth
    }

    /// Returns the requested cumulative node limit.
    #[must_use]
    pub const fn nodes(self) -> Option<u64> {
        self.nodes
    }

    /// Returns the exact move-time request in milliseconds.
    #[must_use]
    pub const fn move_time_ms(self) -> Option<u64> {
        self.move_time_ms
    }

    /// Returns White's remaining clock in milliseconds.
    #[must_use]
    pub const fn white_time_ms(self) -> Option<u64> {
        self.white_time_ms
    }

    /// Returns Black's remaining clock in milliseconds.
    #[must_use]
    pub const fn black_time_ms(self) -> Option<u64> {
        self.black_time_ms
    }

    /// Returns White's increment in milliseconds.
    #[must_use]
    pub const fn white_increment_ms(self) -> Option<u64> {
        self.white_increment_ms
    }

    /// Returns Black's increment in milliseconds.
    #[must_use]
    pub const fn black_increment_ms(self) -> Option<u64> {
        self.black_increment_ms
    }

    /// Returns the optional moves-to-go clock horizon.
    #[must_use]
    pub const fn moves_to_go(self) -> Option<u32> {
        self.moves_to_go
    }

    /// Returns whether the request runs until an explicit stop.
    #[must_use]
    pub const fn is_infinite(self) -> bool {
        self.infinite
    }

    const fn has_clock_fields(self) -> bool {
        self.white_time_ms.is_some()
            || self.black_time_ms.is_some()
            || self.white_increment_ms.is_some()
            || self.black_increment_ms.is_some()
            || self.moves_to_go.is_some()
    }

    const fn has_automatic_limit(self) -> bool {
        self.depth.is_some()
            || self.nodes.is_some()
            || self.move_time_ms.is_some()
            || self.has_clock_fields()
    }
}

/// Immutable snapshot handed to the future UCI search worker.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SearchRequest {
    game: Game,
    command: GoCommand,
    options: EngineOptions,
}

impl SearchRequest {
    /// Returns the exact game and repetition history at request time.
    #[must_use]
    pub const fn game(&self) -> &Game {
        &self.game
    }

    /// Returns parsed limits and clock fields.
    #[must_use]
    pub const fn command(&self) -> GoCommand {
        self.command
    }

    /// Returns the option snapshot bound to this request.
    #[must_use]
    pub const fn options(&self) -> EngineOptions {
        self.options
    }
}

/// Non-text action produced by one parsed protocol command.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum UciEvent {
    /// Start a search from an immutable session snapshot.
    StartSearch(Box<SearchRequest>),
    /// Stop the current worker search, when one exists.
    StopSearch,
    /// Terminate the process after pending output is flushed.
    Quit,
}

/// Text output and optional action produced by one input line.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct UciResponse {
    lines: Vec<String>,
    event: Option<UciEvent>,
}

impl UciResponse {
    /// Returns protocol output lines without trailing newline characters.
    #[must_use]
    pub fn lines(&self) -> &[String] {
        &self.lines
    }

    /// Returns the optional non-text action.
    #[must_use]
    pub const fn event(&self) -> Option<&UciEvent> {
        self.event.as_ref()
    }

    fn with_lines(lines: Vec<String>) -> Self {
        Self { lines, event: None }
    }

    fn with_event(event: UciEvent) -> Self {
        Self {
            lines: Vec::new(),
            event: Some(event),
        }
    }

    fn error(message: impl Into<String>) -> Self {
        Self::with_lines(vec![format!("info string error: {}", message.into())])
    }
}

/// Stateful command parser for one UCI process session.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct UciSession {
    game: Game,
    options: EngineOptions,
}

impl UciSession {
    /// Creates a session in the standard starting position.
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Returns the current game and exact replay history.
    #[must_use]
    pub const fn game(&self) -> &Game {
        &self.game
    }

    /// Returns the currently configured supported options.
    #[must_use]
    pub const fn options(&self) -> EngineOptions {
        self.options
    }

    /// Parses and applies one complete UCI input line.
    pub fn handle_line(&mut self, line: &str) -> UciResponse {
        let tokens: Vec<&str> = line.split_whitespace().collect();
        let Some(command) = tokens.first().copied() else {
            return UciResponse::default();
        };

        match command {
            "uci" => self.uci_response(),
            "isready" => UciResponse::with_lines(vec!["readyok".to_owned()]),
            "ucinewgame" => {
                self.game.reset_to_starting();
                UciResponse::default()
            }
            "setoption" => self.handle_setoption(&tokens[1..]),
            "position" => self.handle_position(&tokens[1..]),
            "go" => self.handle_go(&tokens[1..]),
            "stop" => UciResponse::with_event(UciEvent::StopSearch),
            "quit" => UciResponse::with_event(UciEvent::Quit),
            _ => UciResponse::default(),
        }
    }

    fn uci_response(&self) -> UciResponse {
        UciResponse::with_lines(vec![
            format!("id name {ENGINE_NAME} {}", env!("CARGO_PKG_VERSION")),
            format!("id author {ENGINE_AUTHOR}"),
            format!(
                "option name Hash type spin default {} min {MIN_HASH_MEBIBYTES} max {MAX_HASH_MEBIBYTES}",
                DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES
            ),
            "option name CheckExtension type check default false".to_owned(),
            "uciok".to_owned(),
        ])
    }

    fn handle_setoption(&mut self, tokens: &[&str]) -> UciResponse {
        match parse_setoption(tokens) {
            Ok(("Hash", value)) => match parse_hash_mebibytes(&value) {
                Ok(hash_mebibytes) => {
                    self.options.hash_mebibytes = hash_mebibytes;
                    UciResponse::default()
                }
                Err(error) => UciResponse::error(error),
            },
            Ok(("CheckExtension", value)) => match parse_boolean(&value) {
                Ok(check_extension) => {
                    self.options.check_extension = check_extension;
                    UciResponse::default()
                }
                Err(error) => UciResponse::error(error),
            },
            Ok((name, _)) => UciResponse::error(format!("unsupported option {name:?}")),
            Err(error) => UciResponse::error(error),
        }
    }

    fn handle_position(&mut self, tokens: &[&str]) -> UciResponse {
        match parse_position(tokens) {
            Ok(game) => {
                self.game = game;
                UciResponse::default()
            }
            Err(error) => UciResponse::error(error),
        }
    }

    fn handle_go(&self, tokens: &[&str]) -> UciResponse {
        match parse_go(tokens) {
            Ok(command) => UciResponse::with_event(UciEvent::StartSearch(Box::new(
                SearchRequest {
                    game: self.game.clone(),
                    command,
                    options: self.options,
                },
            ))),
            Err(error) => UciResponse::error(error),
        }
    }
}

/// Runs the Task 17.1 protocol loop over arbitrary buffered input and output.
///
/// Search requests are parsed and acknowledged with an `info string` until the
/// adapter-owned worker lands in Task 17.2. Handshake, options, position state,
/// stop, and clean process termination are fully active now.
pub fn run_protocol_loop<R, W>(input: R, mut output: W) -> io::Result<()>
where
    R: BufRead,
    W: Write,
{
    let mut session = UciSession::new();
    for line in input.lines() {
        let response = session.handle_line(&line?);
        for current in response.lines {
            writeln!(output, "{current}")?;
        }
        match response.event {
            Some(UciEvent::StartSearch(_)) => {
                writeln!(output, "info string search worker pending Task 17.2")?;
            }
            Some(UciEvent::StopSearch) | None => {}
            Some(UciEvent::Quit) => {
                output.flush()?;
                return Ok(());
            }
        }
        output.flush()?;
    }
    Ok(())
}

/// Runs the Linux stdin/stdout UCI process adapter.
pub fn run_stdio() -> io::Result<()> {
    let stdin = io::stdin();
    let stdout = io::stdout();
    run_protocol_loop(stdin.lock(), stdout.lock())
}

fn parse_setoption(tokens: &[&str]) -> Result<(&str, String), String> {
    if tokens.first().copied() != Some("name") {
        return Err("setoption requires `name <option> value <value>`".to_owned());
    }
    let value_index = tokens
        .iter()
        .position(|token| *token == "value")
        .ok_or_else(|| "setoption requires a value".to_owned())?;
    if value_index <= 1 {
        return Err("setoption option name is empty".to_owned());
    }
    if value_index + 1 >= tokens.len() {
        return Err("setoption value is empty".to_owned());
    }
    let name = tokens[1..value_index].join(" ");
    let value = tokens[value_index + 1..].join(" ");
    match name.as_str() {
        "Hash" => Ok(("Hash", value)),
        "CheckExtension" => Ok(("CheckExtension", value)),
        _ => Ok((Box::leak(name.into_boxed_str()), value)),
    }
}

fn parse_hash_mebibytes(value: &str) -> Result<usize, String> {
    let parsed = value
        .parse::<usize>()
        .map_err(|_| format!("Hash must be an integer, found {value:?}"))?;
    if !(MIN_HASH_MEBIBYTES..=MAX_HASH_MEBIBYTES).contains(&parsed) {
        return Err(format!(
            "Hash must be between {MIN_HASH_MEBIBYTES} and {MAX_HASH_MEBIBYTES} MiB"
        ));
    }
    Ok(parsed)
}

fn parse_boolean(value: &str) -> Result<bool, String> {
    match value {
        "true" => Ok(true),
        "false" => Ok(false),
        _ => Err(format!("boolean option must be true or false, found {value:?}")),
    }
}

fn parse_position(tokens: &[&str]) -> Result<Game, String> {
    let Some(kind) = tokens.first().copied() else {
        return Err("position requires `startpos` or `fen`".to_owned());
    };

    let (mut game, moves_index) = match kind {
        "startpos" => (Game::starting(), 1),
        "fen" => {
            if tokens.len() < 7 {
                return Err("position fen requires exactly six FEN fields".to_owned());
            }
            let fen = tokens[1..7].join(" ");
            let position = Position::from_fen(&fen)
                .map_err(|error| format!("invalid position FEN: {error}"))?;
            (Game::new(position), 7)
        }
        _ => return Err(format!("unsupported position form {kind:?}")),
    };

    if moves_index == tokens.len() {
        return Ok(game);
    }
    if tokens.get(moves_index).copied() != Some("moves") {
        return Err("position suffix must begin with `moves`".to_owned());
    }
    apply_moves(&mut game, &tokens[moves_index + 1..])?;
    Ok(game)
}

fn apply_moves(game: &mut Game, moves: &[&str]) -> Result<(), String> {
    for (ply, text) in moves.iter().copied().enumerate() {
        let syntax = text
            .parse::<UciMove>()
            .map_err(|error| format!("invalid UCI move at replay ply {}: {error}", ply + 1))?;
        let legal_moves = game
            .legal_moves()
            .map_err(|error| format!("could not generate replay moves at ply {}: {error}", ply + 1))?;
        let current = legal_moves
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .ok_or_else(|| format!("illegal UCI move {text:?} at replay ply {}", ply + 1))?;
        game.make_move(current)
            .map_err(|error| format!("could not replay move {text:?} at ply {}: {error}", ply + 1))?;
    }
    Ok(())
}

fn parse_go(tokens: &[&str]) -> Result<GoCommand, String> {
    let mut command = GoCommand::default();
    let mut index = 0;
    while index < tokens.len() {
        let name = tokens[index];
        if name == "infinite" {
            if command.infinite {
                return Err("go infinite was specified more than once".to_owned());
            }
            command.infinite = true;
            index += 1;
            continue;
        }

        let value = tokens
            .get(index + 1)
            .copied()
            .ok_or_else(|| format!("go parameter {name:?} requires a value"))?;
        match name {
            "depth" => set_once(
                &mut command.depth,
                parse_positive_u16(value, "depth")?,
                name,
            )?,
            "nodes" => set_once(
                &mut command.nodes,
                parse_positive_u64(value, "nodes")?,
                name,
            )?,
            "movetime" => set_once(
                &mut command.move_time_ms,
                parse_positive_u64(value, "movetime")?,
                name,
            )?,
            "wtime" => set_once(
                &mut command.white_time_ms,
                parse_nonnegative_u64(value, "wtime")?,
                name,
            )?,
            "btime" => set_once(
                &mut command.black_time_ms,
                parse_nonnegative_u64(value, "btime")?,
                name,
            )?,
            "winc" => set_once(
                &mut command.white_increment_ms,
                parse_nonnegative_u64(value, "winc")?,
                name,
            )?,
            "binc" => set_once(
                &mut command.black_increment_ms,
                parse_nonnegative_u64(value, "binc")?,
                name,
            )?,
            "movestogo" => set_once(
                &mut command.moves_to_go,
                parse_positive_u32(value, "movestogo")?,
                name,
            )?,
            _ => return Err(format!("unsupported go parameter {name:?}")),
        }
        index += 2;
    }

    if tokens.is_empty() {
        command.infinite = true;
    }
    if command.infinite && command.has_automatic_limit() {
        return Err("go infinite cannot be combined with automatic limits or clocks".to_owned());
    }
    if command.move_time_ms.is_some() && command.has_clock_fields() {
        return Err("go movetime cannot be combined with clock fields".to_owned());
    }
    Ok(command)
}

fn set_once<T>(slot: &mut Option<T>, value: T, name: &str) -> Result<(), String> {
    if slot.is_some() {
        return Err(format!("go parameter {name:?} was specified more than once"));
    }
    *slot = Some(value);
    Ok(())
}

fn parse_positive_u16(value: &str, name: &str) -> Result<u16, String> {
    let parsed = value
        .parse::<u16>()
        .map_err(|_| format!("go {name} must be a positive integer, found {value:?}"))?;
    if parsed == 0 {
        return Err(format!("go {name} must be greater than zero"));
    }
    Ok(parsed)
}

fn parse_positive_u32(value: &str, name: &str) -> Result<u32, String> {
    let parsed = value
        .parse::<u32>()
        .map_err(|_| format!("go {name} must be a positive integer, found {value:?}"))?;
    if parsed == 0 {
        return Err(format!("go {name} must be greater than zero"));
    }
    Ok(parsed)
}

fn parse_positive_u64(value: &str, name: &str) -> Result<u64, String> {
    let parsed = parse_nonnegative_u64(value, name)?;
    if parsed == 0 {
        return Err(format!("go {name} must be greater than zero"));
    }
    Ok(parsed)
}

fn parse_nonnegative_u64(value: &str, name: &str) -> Result<u64, String> {
    value
        .parse::<u64>()
        .map_err(|_| format!("go {name} must be a nonnegative integer, found {value:?}"))
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::{
        run_protocol_loop, EngineOptions, GoCommand, UciEvent, UciResponse, UciSession,
        DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
    };

    fn search_command(response: &UciResponse) -> GoCommand {
        match response.event() {
            Some(UciEvent::StartSearch(request)) => request.command(),
            other => panic!("expected start-search event, found {other:?}"),
        }
    }

    #[test]
    fn uci_handshake_advertises_identity_and_supported_options() {
        let response = UciSession::new().handle_line("uci");
        assert_eq!(
            response.lines(),
            &[
                "id name chess-engine-rust 0.1.0",
                "id author Phillip Chin",
                "option name Hash type spin default 1 min 1 max 65536",
                "option name CheckExtension type check default false",
                "uciok",
            ]
        );
    }

    #[test]
    fn isready_is_immediate() {
        assert_eq!(
            UciSession::new().handle_line("isready").lines(),
            &["readyok"]
        );
    }

    #[test]
    fn supported_options_update_session_state() {
        let mut session = UciSession::new();
        assert!(session
            .handle_line("setoption name Hash value 32")
            .lines()
            .is_empty());
        assert!(session
            .handle_line("setoption name CheckExtension value true")
            .lines()
            .is_empty());
        assert_eq!(
            session.options(),
            EngineOptions {
                hash_mebibytes: 32,
                check_extension: true,
            }
        );
    }

    #[test]
    fn invalid_option_does_not_mutate_state() {
        let mut session = UciSession::new();
        let before = session.options();
        let response = session.handle_line("setoption name Hash value 0");
        assert_eq!(session.options(), before);
        assert_eq!(response.lines().len(), 1);
        assert!(response.lines()[0].contains("Hash must be between"));
    }

    #[test]
    fn position_startpos_replays_moves_with_history() {
        let mut session = UciSession::new();
        let response = session.handle_line("position startpos moves e2e4 e7e5");
        assert!(response.lines().is_empty());
        assert_eq!(session.game().ply_count(), 2);
        assert_eq!(
            session.game().position().to_fen(),
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        );
    }

    #[test]
    fn position_fen_consumes_exactly_six_fields_and_replays_moves() {
        let mut session = UciSession::new();
        let response = session.handle_line(
            "position fen 7k/8/8/8/8/8/4K3/R7 w - - 0 1 moves a1a8",
        );
        assert!(response.lines().is_empty());
        assert_eq!(session.game().ply_count(), 1);
        assert_eq!(
            session.game().position().to_fen(),
            "R6k/8/8/8/8/8/4K3/8 b - - 1 1"
        );
    }

    #[test]
    fn invalid_position_command_is_transactional() {
        let mut session = UciSession::new();
        let _response = session.handle_line("position startpos moves e2e4");
        let before = session.game().clone();
        let response = session.handle_line("position startpos moves e2e5");
        assert_eq!(session.game(), &before);
        assert_eq!(response.lines().len(), 1);
        assert!(response.lines()[0].contains("illegal UCI move"));
    }

    #[test]
    fn ucinewgame_restores_starting_position_and_history() {
        let mut session = UciSession::new();
        let _response = session.handle_line("position startpos moves e2e4 e7e5");
        let response = session.handle_line("ucinewgame");
        assert!(response.lines().is_empty());
        assert_eq!(session.game().ply_count(), 0);
        assert_eq!(session.game().position(), &chess_core::Position::starting());
    }

    #[test]
    fn go_depth_and_nodes_are_typed() {
        let command = search_command(UciSession::new().handle_line("go depth 6 nodes 9000"));
        assert_eq!(command.depth(), Some(6));
        assert_eq!(command.nodes(), Some(9000));
        assert!(!command.is_infinite());
    }

    #[test]
    fn go_movetime_is_typed() {
        let command = search_command(UciSession::new().handle_line("go movetime 250"));
        assert_eq!(command.move_time_ms(), Some(250));
    }

    #[test]
    fn go_clock_fields_are_typed() {
        let command = search_command(UciSession::new().handle_line(
            "go wtime 60000 btime 55000 winc 1000 binc 500 movestogo 20",
        ));
        assert_eq!(command.white_time_ms(), Some(60000));
        assert_eq!(command.black_time_ms(), Some(55000));
        assert_eq!(command.white_increment_ms(), Some(1000));
        assert_eq!(command.black_increment_ms(), Some(500));
        assert_eq!(command.moves_to_go(), Some(20));
    }

    #[test]
    fn go_infinite_and_empty_go_require_explicit_stop() {
        assert!(search_command(UciSession::new().handle_line("go infinite")).is_infinite());
        assert!(search_command(UciSession::new().handle_line("go")).is_infinite());
    }

    #[test]
    fn incompatible_or_duplicate_go_fields_fail_loudly() {
        for input in [
            "go infinite depth 4",
            "go movetime 1000 wtime 5000",
            "go depth 3 depth 4",
            "go nodes 0",
            "go searchmoves e2e4",
        ] {
            let response = UciSession::new().handle_line(input);
            assert!(response.event().is_none(), "unexpected event for {input}");
            assert_eq!(response.lines().len(), 1, "missing error for {input}");
        }
    }

    #[test]
    fn search_request_captures_game_and_option_snapshots() {
        let mut session = UciSession::new();
        let _response = session.handle_line("setoption name Hash value 16");
        let _response = session.handle_line("setoption name CheckExtension value true");
        let _response = session.handle_line("position startpos moves d2d4");
        let response = session.handle_line("go depth 2");
        match response.event() {
            Some(UciEvent::StartSearch(request)) => {
                assert_eq!(request.game().ply_count(), 1);
                assert_eq!(request.options().hash_mebibytes(), 16);
                assert!(request.options().check_extension());
            }
            other => panic!("expected start-search event, found {other:?}"),
        }
    }

    #[test]
    fn stop_and_quit_are_distinct_events() {
        assert!(matches!(
            UciSession::new().handle_line("stop").event(),
            Some(UciEvent::StopSearch)
        ));
        assert!(matches!(
            UciSession::new().handle_line("quit").event(),
            Some(UciEvent::Quit)
        ));
    }

    #[test]
    fn unknown_commands_are_ignored() {
        assert_eq!(
            UciSession::new().handle_line("future-command argument"),
            UciResponse::default()
        );
    }

    #[test]
    fn protocol_loop_flushes_handshake_and_exits_on_quit() {
        let input = Cursor::new(b"uci\nisready\nquit\nisready\n".as_slice());
        let mut output = Vec::new();
        run_protocol_loop(input, &mut output).expect("protocol loop succeeds");
        let output = String::from_utf8(output).expect("protocol output is UTF-8");
        assert!(output.contains("id name chess-engine-rust 0.1.0\n"));
        assert!(output.contains("readyok\n"));
        assert_eq!(output.matches("readyok\n").count(), 1);
    }

    #[test]
    fn defaults_follow_search_crate_capacity() {
        assert_eq!(
            UciSession::new().options().hash_mebibytes(),
            DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES
        );
    }
}
