# Seed corpus

Each directory matches one `cargo-fuzz` target. These files are small deterministic starting inputs, not a claim of exhaustive coverage. Mutation findings must be minimized and copied to `fuzz/regressions/<target>/` with a descriptive filename before the associated defect is closed.
