# Rust opening-book abstraction

Task 19.1 introduces the platform-neutral opening-book boundary in the dedicated `chess-book` workspace crate.

## Dependency placement

`chess-book` depends only on `chess-core` so it can accept the engine's validated `Position` and return the engine's semantic `Move` identity. Neither `chess-core` nor `chess-search` depends on `chess-book`, and neither core crate gains filesystem, asset, environment, networking, or platform APIs.

Adapters may depend on `chess-book` in later Task 19 slices. This avoids coupling the UCI, C/JNI, Android, self-play, or tooling adapters to one another.

## `BookMove`

`BookMove<M = ()>` contains exactly three format-neutral values:

- the candidate `chess_core::Move`;
- a `u32` relative weight; and
- optional backend-defined metadata.

Metadata is generic rather than prescribing a Polyglot or project-specific record shape before Task 19.2 chooses the backend format. Constructors support values with no metadata, one metadata value, or a prebuilt `Option<M>`. Accessors expose each component without exposing the engine move's private packed representation.

Task 19.1 does not assign semantics to zero weights, normalize weights, select a candidate, or validate candidate legality. Those policies belong to Task 19.3 and adapter integration.

## `OpeningBook`

`OpeningBook` is a `Send + Sync` query trait suitable for UCI and Android worker threads. A lookup receives a complete validated `Position` and returns every recorded candidate for that position.

- `Ok(Vec::new())` means that the loaded book has no entry for the supplied position.
- A corrupt record, unsupported format, decoding problem, or other backend failure must remain a typed error.
- Implementations must not convert failures into an empty result.
- The abstraction performs no candidate selection and no silent legality filtering.

The associated metadata and error types let adapters use static or dynamic dispatch without committing all backends to one diagnostic schema.

## `BookProvider`

`BookProvider` is the explicit adapter-owned construction boundary. It returns either:

- `Ok(Some(book))` for an explicitly configured book;
- `Ok(None)` when the adapter instance intentionally has no book; or
- a typed provider/loading error.

The trait defines no default filename, current-directory lookup, environment variable, bundled resource, Android asset, or global singleton. A provider implementation may perform platform-specific I/O, but the adapter must receive and invoke that provider explicitly. This preserves the project's no-auto-discovery and fail-visible error policies.

## Deferred work

Task 19.1 deliberately does not implement:

- Polyglot or project-specific file parsing;
- checksums, versioning, or endianness rules;
- deterministic or weighted-random candidate selection;
- local RNG seeding;
- legal-move filtering;
- UCI options;
- safe-facade or JNI integration; or
- Android asset loading.

Those remain owned by Tasks 19.2 through 19.5.

## Contract tests

The crate tests prove:

1. move, weight, absent metadata, and present metadata round-trip exactly;
2. `OpeningBook` can be injected through a trait object and queried with a validated position;
3. `BookProvider` requires explicit configuration and can represent no configured book; and
4. lookup failures remain typed and cannot be mistaken for an empty candidate list.

The permanent workspace workflow is the authoritative compiler, strict-Clippy, lockfile, rustdoc, test, perft, build, and differential-oracle gate for this contract.

## Completion evidence

- Exact validated implementation SHA: `6ce31141d0d4516696f1e9d17ee018606ef7bd4b`.
- Permanent Rust validation: run `30852253445`, job `91814805656`.
- Permanent Android regression validation: run `30852253399`, host JVM job `91814815286`, emulator job `91814815151`.
- Tracker-closure SHA: `a9bc63fac8e6fadc901186263236938d9d14f57f`.
- Temporary closure-workflow cleanup SHA: `7f6ce92b9ae745fab9ac91e031f624ef11d9514e`.
- Four focused `chess-book` tests passed; the complete workspace executed 310 non-doc Rust tests with zero failures.
- Release depth-four perft, rustdoc with warnings denied, debug/release builds, and the differential oracle all passed.
- Differential evidence: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The Android regression gate rebuilt and verified both JNI ABIs, passed host JVM tests, rebuilt the AAR/test APK, and passed the API-35 emulator lifecycle.
- The only implementation-validation correction was canonical rustfmt output.
- Task 19.1 is complete. Tasks 19.2–19.5 and the overall Task 19 gate remain open.
