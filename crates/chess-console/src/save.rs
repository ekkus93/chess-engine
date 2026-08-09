use std::{io, path::Path};

use chess_app::{text::{color_name, format_outcome}, GameConfig, GameSession};

#[must_use]
pub fn serialize_game(session: &GameSession, timestamp: Option<&str>) -> String {
    let mut lines = vec!["Chess Engine Rust Console save v1".to_owned()];
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
    lines.push(format!(
        "moves: {}",
        session
            .game
            .moves()
            .iter()
            .map(|current| current.to_uci())
            .collect::<Vec<_>>()
            .join(" ")
    ));
    lines.push(format!(
        "result: {}",
        session
            .outcome
            .map_or_else(|| "ongoing".to_owned(), format_outcome)
    ));
    lines.push(String::new());
    lines.join("\n")
}

pub fn write_game(path: &Path, contents: &str) -> io::Result<()> {
    chess_app::save::atomic_write(path, contents)
}

#[cfg(test)]
mod tests {
    use std::{fs, path::PathBuf, process, time::SystemTime};

    use chess_app::{GameConfig, GameController};
    use chess_core::Color;

    use super::{serialize_game, write_game};

    fn unique_path(label: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .expect("clock after epoch")
            .as_nanos();
        std::env::temp_dir().join(format!(
            "chess-console-{label}-{}-{stamp}.txt",
            process::id()
        ))
    }

    #[test]
    fn console_serialization_is_deterministic_and_not_pgn() {
        let mut controller = GameController::new();
        controller
            .start_game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 3,
            })
            .expect("game starts");
        controller.submit_human_move("e2e4").expect("move applies");
        let saved = serialize_game(
            controller.session.as_ref().expect("session"),
            Some("fixed-time"),
        );
        assert_eq!(
            saved,
            "Chess Engine Rust Console save v1\ndate: fixed-time\nmode: human-vs-engine\nhuman-color: White\nengine-depth: 3\nmoves: e2e4\nresult: ongoing\n"
        );
        assert!(!saved.contains("PGN"));
    }

    #[test]
    fn console_write_success_and_failure_are_explicit() {
        let path = unique_path("save");
        write_game(&path, "exact\n").expect("write succeeds");
        assert_eq!(fs::read_to_string(&path).expect("read"), "exact\n");
        fs::remove_file(&path).expect("cleanup");

        let missing = unique_path("missing-parent").join("game.txt");
        assert_eq!(
            write_game(&missing, "data").expect_err("must fail").kind(),
            std::io::ErrorKind::NotFound
        );
    }
}
