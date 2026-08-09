use std::{
    ffi::OsString,
    fs, io,
    path::{Path, PathBuf},
};

/// Writes `contents` through a same-directory temporary file and atomic rename.
///
/// Interactive frontends must report any returned error; this function never
/// converts a failed write into success and cleans up its temporary artifact on
/// both write and rename failure paths.
pub fn atomic_write(path: &Path, contents: &str) -> io::Result<()> {
    let temp_path = temp_write_path(path);
    if let Err(error) = fs::write(&temp_path, contents) {
        let _cleanup_result = fs::remove_file(&temp_path);
        return Err(error);
    }
    if let Err(error) = fs::rename(&temp_path, path) {
        let _cleanup_result = fs::remove_file(&temp_path);
        return Err(error);
    }
    Ok(())
}

fn temp_write_path(path: &Path) -> PathBuf {
    let temp_name = path.file_name().map_or_else(
        || OsString::from(".chess-save.tmp"),
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

    use super::{atomic_write, temp_write_path};

    fn unique_path(label: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .expect("clock after epoch")
            .as_nanos();
        std::env::temp_dir().join(format!("chess-app-{label}-{}-{stamp}.txt", process::id()))
    }

    #[test]
    fn successful_write_is_exact_and_leaves_no_temp_file() {
        let path = unique_path("write");
        let temp = temp_write_path(&path);
        atomic_write(&path, "exact\ncontents\n").expect("write succeeds");
        assert_eq!(
            fs::read_to_string(&path).expect("read"),
            "exact\ncontents\n"
        );
        assert!(!temp.exists());
        fs::remove_file(path).expect("cleanup");
    }

    #[test]
    fn overwrite_atomically_replaces_content() {
        let path = unique_path("overwrite");
        atomic_write(&path, "first").expect("first");
        atomic_write(&path, "second").expect("second");
        assert_eq!(fs::read_to_string(&path).expect("read"), "second");
        fs::remove_file(path).expect("cleanup");
    }

    #[test]
    fn missing_parent_failure_is_visible() {
        let path = unique_path("missing-parent").join("game.txt");
        let error = atomic_write(&path, "data").expect_err("missing parent fails");
        assert_eq!(error.kind(), std::io::ErrorKind::NotFound);
        assert!(!temp_write_path(&path).exists());
    }
}
