use std::{fs, io, path::Path};

use crate::{
    app::{GameConfig, GameSession},
    render::{color_name, format_outcome},
};

#[must_use]
pub fn serialize_game(session: &GameSession, timestamp: Option<&str>) -> String {
    let mut lines = Vec::new();
    lines.push("Chess Engine Rust TUI save v1".to_owned());
    if let Some(timestamp) = timestamp {
        lines.push(format!("date: {timestamp}"));
    }
    match session.config {
        GameConfig::HumanVsEngine {
            human_color,
            engine_depth,
        } => {
            lines.push("mode: human-vs-engine".to_owned());
            lines.push(format!("human-color: {}", color_name(human_color)));
            lines.push(format!("engine-depth: {engine_depth}"));
        }
        GameConfig::SelfPlay {
            white_depth,
            black_depth,
        } => {
            lines.push("mode: self-play".to_owned());
            lines.push(format!("white-depth: {white_depth}"));
            lines.push(format!("black-depth: {black_depth}"));
        }
    }
    let moves = session
        .game
        .moves()
        .iter()
        .map(|current| current.to_uci())
        .collect::<Vec<_>>()
        .join(" ");
    lines.push(format!("moves: {moves}"));
    let result = session
        .outcome
        .map_or_else(|| "ongoing".to_owned(), format_outcome);
    lines.push(format!("result: {result}"));
    lines.push(String::new());
    lines.join("\n")
}

pub fn write_game(path: &Path, contents: &str) -> io::Result<()> {
    fs::write(path, contents)
}

#[cfg(test)]
mod tests {
    use std::{fs, path::PathBuf, process, time::SystemTime};

    use chess_core::Color;

    use crate::app::{AppState, GameConfig};

    use super::{serialize_game, write_game};

    fn unique_path(label: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .expect("clock is after epoch")
            .as_nanos();
        std::env::temp_dir().join(format!("chess-tui-{label}-{}-{stamp}.txt", process::id()))
    }

    #[test]
    fn serialization_is_deterministic_and_explicit() {
        let mut app = AppState::new();
        app.start_game(GameConfig::HumanVsEngine {
            human_color: Color::White,
            engine_depth: 3,
        })
        .expect("game starts");
        app.submit_human_move("e2e4").expect("move applies");
        let session = app.session.as_ref().expect("session");
        let saved = serialize_game(session, Some("2026-08-07T12:00:00Z"));
        assert_eq!(
            saved,
            "Chess Engine Rust TUI save v1\ndate: 2026-08-07T12:00:00Z\nmode: human-vs-engine\nhuman-color: White\nengine-depth: 3\nmoves: e2e4\nresult: ongoing\n"
        );
        assert!(!saved.contains("PGN"));
    }

    #[test]
    fn successful_write_persists_exact_serialization() {
        let path = unique_path("write");
        write_game(&path, "exact\ncontents\n").expect("write succeeds");
        assert_eq!(
            fs::read_to_string(&path).expect("read succeeds"),
            "exact\ncontents\n"
        );
        fs::remove_file(path).expect("temporary save is removed");
    }

    #[test]
    fn failed_write_is_reported() {
        let path = unique_path("missing-parent").join("game.txt");
        let error = write_game(&path, "data").expect_err("missing parent must fail");
        assert_eq!(error.kind(), std::io::ErrorKind::NotFound);
    }
}
