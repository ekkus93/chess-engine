//! RF-004.3: structural evidence that no chess-tui source file other than
//! `save.rs` can write to the filesystem. `save.rs::write_game` is the sole
//! sanctioned filesystem-write path, reachable only through the explicit
//! save action (`ui.rs::save_current_game`). This complements
//! `tests/workflows.rs::self_play_never_marks_a_save_without_an_explicit_save_action`,
//! which proves the same property at runtime for a real self-play sequence:
//! together they show self-play cannot write tuning/evaluation/save files on
//! its own, both by direct observation and by the absence of any code path
//! that could do so.

use std::{fs, path::Path};

/// Filesystem-write APIs a source file must not reference outside `save.rs`.
/// This intentionally does not forbid *reads* (`fs::read`, config loading is
/// out of scope) or `std::env::temp_dir`/`PathBuf` construction — only the
/// APIs that actually create or modify a file on disk.
const WRITE_MARKERS: &[&str] = &[
    "fs::write",
    "fs::create_dir",
    "fs::remove",
    "fs::rename",
    "File::create",
    "OpenOptions",
];

#[test]
fn only_save_rs_references_filesystem_write_apis() {
    let src_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let mut offenders = Vec::new();
    scan_dir(&src_dir, &mut offenders);
    assert!(
        offenders.is_empty(),
        "filesystem-write APIs must only appear in save.rs, found in: {offenders:?}"
    );
}

fn scan_dir(dir: &Path, offenders: &mut Vec<String>) {
    let entries = fs::read_dir(dir).expect("src directory is readable");
    for entry in entries {
        let entry = entry.expect("directory entry is readable");
        let path = entry.path();
        if path.is_dir() {
            scan_dir(&path, offenders);
            continue;
        }
        if path.extension().and_then(|ext| ext.to_str()) != Some("rs") {
            continue;
        }
        // save.rs (and its own hardening_tests submodule) is the sanctioned
        // write path. Every `hardening_tests.rs` file is #[cfg(test)]-only
        // and several legitimately clean up their own temp fixtures (e.g.
        // ui/hardening_tests.rs exercising the save overlay) — exclude test
        // modules generally, since this check is about what production code
        // can reach, not what test fixtures do to set up/tear down.
        let relative = path
            .strip_prefix(Path::new(env!("CARGO_MANIFEST_DIR")).join("src"))
            .expect("path is under src");
        let relative_str = relative.to_string_lossy();
        if relative_str.starts_with("save.rs")
            || relative_str.starts_with("save/")
            || relative_str.ends_with("hardening_tests.rs")
        {
            continue;
        }
        let contents = fs::read_to_string(&path).expect("source file is valid UTF-8");
        for marker in WRITE_MARKERS {
            if contents.contains(marker) {
                offenders.push(format!("{}: {marker}", relative.display()));
            }
        }
    }
}
