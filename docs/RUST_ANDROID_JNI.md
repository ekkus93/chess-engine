# Android JNI adapter contract

Task 18.4 adds an Android-facing JNI adapter without moving chess rules, search behavior, filesystem access, or ownership registries into the Android layer.

## Layering

The dependency direction remains:

```text
Kotlin application code
        |
        v
chess-jni exported JNI methods
        |
        v
chess-ffi stable C ABI
        |
        v
safe Rust facade -> chess-search -> chess-core
```

`chess-jni` reuses the Task 18.2 opaque engine and cancellation tokens. It does not create a second engine registry, reinterpret Rust engine layouts, or duplicate C ABI result-code mapping.

## Native library

`chess-jni` produces both an `rlib` for host tests and a `cdylib` named `libchess_jni.so` for Android.

The committed AArch64 build entry point is:

```text
ANDROID_NDK_HOME=/path/to/android-ndk \
ANDROID_API_LEVEL=24 \
./scripts/build_android_jni.sh
```

The script targets `aarch64-linux-android`, selects the NDK LLVM linker and archiver explicitly, runs a locked release build, and fails unless a nonempty `target/aarch64-linux-android/release/libchess_jni.so` exists. It performs no artifact copying or Android-project discovery.

## JNI surface

The private Kotlin object `NativeChessEngineBindings` owns the raw JNI declarations. Exported Rust symbols use that class's fully qualified JNI names and cover:

- semantic version;
- engine create/destroy;
- position reset and strict FEN replacement;
- canonical FEN and legal UCI moves;
- legal move application and game status;
- evaluation-weight identity;
- cancellation create/destroy/cancel/reset/query; and
- synchronous typed search.

Strings crossing JNI are Java `String` values. The JNI adapter converts them to explicit Rust UTF-8 strings before calling the C ABI, which then continues to use its explicit `(pointer, length)` contract. No modified UTF-8 pointer is retained after a JNI call.

Compact native result strings are private implementation details between `NativeChessEngineBindings` and the Kotlin wrapper:

- legal moves are newline-separated canonical UCI moves;
- game status is three comma-separated numeric fields;
- weight identity is three comma-separated unsigned fields; and
- search is exactly thirteen newline-separated fields.

The public Kotlin API immediately parses these into typed enums and data classes. Application code does not consume the compact records directly.

## Error mapping and panic containment

Every exported JNI function enters one shared `catch_unwind` boundary. C ABI failures retain their exact stable numeric result code and thread-local diagnostic. JNI conversion failures map to an internal error. A contained Rust panic maps to result code `101`.

Failures are thrown as:

```text
com.ekkus93.chessengine.ChessEngineException
```

The exception constructor receives both the numeric native code and message. If that application class cannot be created, the adapter clears the failed lookup and throws `java.lang.RuntimeException` with the same code and message rather than returning a silent sentinel.

## Kotlin ownership

`ChessEngine` is the only public owner of an engine token.

- `create` obtains exactly one nonzero native handle.
- Every ordinary operation takes a read lock and rejects a closed owner.
- `close` is idempotent, requests cancellation for an active search, obtains the write lock, destroys the token once, and shuts down the worker.
- Only one search may be outstanding per engine.
- A phantom-reference reaper destroys a leaked token as a last-resort fallback. Explicit `close` remains authoritative because the fallback cannot report cleanup errors to an unreachable owner.

Opaque `u64` tokens round-trip through signed JVM `long` values by preserving their complete bit patterns. Kotlin code must treat them as opaque values and never require positivity.

## Background search and cancellation

The public `ChessEngine.search` method never invokes native search on the caller's thread. It submits the synchronous JNI call to a private single-thread executor and returns a `SearchOperation`.

Each operation owns one native cancellation token. `SearchOperation.cancel` may be called from any thread and requests the C ABI stop flag; it does not depend on Java interruption. The worker destroys the token in a `finally` block after success, cancellation, or failure.

`close` first requests active cancellation, then waits for the search call to leave the read-locked section before destroying the engine. The C ABI's resolved in-flight references preserve object safety even if an external token is invalidated concurrently.

## Validation boundary

Task 18.4 host validation covers:

- locked host compilation and strict Clippy for the JNI crate;
- complete workspace tests and existing C ABI lifecycle coverage;
- JNI token bit-preservation and search-request conversion tests;
- a Rust-through-JNI-adapter lifecycle and active cancellation test that avoids requiring a JVM;
- static agreement between the Kotlin native declaration names and Rust export symbols; and
- an actual locked AArch64 Android release build of `libchess_jni.so`.

Task 18.5 remains responsible for compiling and executing the Kotlin wrapper in a host JVM/Android project, emulator or instrumented smoke testing, main-thread exclusion verification, repeated Android lifecycle tests, and final Android integration instructions.
