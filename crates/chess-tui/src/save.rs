use std::{
    ffi::OsString,
    fs, io,
    path::{Path, PathBuf},
};

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

/// Writes `contents` to `path` atomically (RF-006.5): writes to a temporary
/// file in the same directory first, then renames it into place. This
/// avoids a torn/partial file being left behind (and, since `mark_saved`
/// only runs after this returns `Ok`, being reported as saved) if the
/// process is interrupted mid-write. `fs::rename` also atomically replaces
/// an existing destination, so this pairs correctly with the overwrite
/// confirmation in `ui.rs::save_current_game`.
pub fn write_game(path: &Path, contents: &str) -> io::Result<()> {
    let temp_path = temp_write_path(path);
    if let Err(error) = fs::write(&temp_path, contents) {
        let _ = fs::remove_file(&temp_path);
        return Err(error);
    }
    if let Err(error) = fs::rename(&temp_path, path) {
        let _ = fs::remove_file(&temp_path);
        return Err(error);
    }
    Ok(())
}

/// Derives a same-directory temporary path so the final `fs::rename` stays
/// on one filesystem (required for it to be atomic). A fixed, non-random
/// suffix is deliberate: this crate never writes to the same destination
/// concurrently (saves are one explicit user action at a time), so a leftover
/// temp file from an interrupted prior write is simply overwritten by the
/// next attempt rather than accumulating.
fn temp_write_path(path: &Path) -> PathBuf {
    let temp_name = path.file_name().map_or_else(
        || OsString::from(".chess-tui-save.tmp"),
        |name| {
            let mut temp_name = OsString::from(".");
            temp_name.push(name);
            temp_name.push(".tmp");
            temp_name
        },
    );
    path.with_file_name(temp_name)
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
    fn successful_write_leaves_no_temp_file_behind() {
        // RF-006.5: write_game writes to a same-directory temp file and
        // renames it into place; confirm the temp artifact doesn't survive
        // a successful write.
        let path = unique_path("no-temp-leak");
        write_game(&path, "contents").expect("write succeeds");
        let temp_name = format!(
            ".{}.tmp",
            path.file_name()
                .expect("path has a file name")
                .to_string_lossy()
        );
        let temp_path = path.with_file_name(temp_name);
        assert!(
            !temp_path.exists(),
            "temp file must not remain after a successful write: {}",
            temp_path.display()
        );
        fs::remove_file(path).expect("temporary save is removed");
    }

    #[test]
    fn overwriting_an_existing_file_replaces_its_contents_atomically() {
        let path = unique_path("overwrite-atomic");
        write_game(&path, "first version").expect("first write succeeds");
        write_game(&path, "second version").expect("second write succeeds");
        assert_eq!(
            fs::read_to_string(&path).expect("read succeeds"),
            "second version"
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

#[cfg(test)]
mod hardening_tests;
