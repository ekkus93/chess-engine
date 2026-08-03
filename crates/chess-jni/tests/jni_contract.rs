const KOTLIN_WRAPPER: &str =
    include_str!("../kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt");
const RUST_EXPORTS: &str = include_str!("../src/lib.rs");

fn occurrences(haystack: &str, needle: &str) -> usize {
    haystack.match_indices(needle).count()
}

#[test]
fn kotlin_native_declarations_match_exact_rust_export_names() {
    let methods = [
        "nativeVersion",
        "nativeCreate",
        "nativeDestroy",
        "nativeResetPosition",
        "nativeSetPosition",
        "nativeFen",
        "nativeLegalMoves",
        "nativePlayMove",
        "nativeGameStatus",
        "nativeWeightIdentity",
        "nativeCancellationCreate",
        "nativeCancellationDestroy",
        "nativeCancellationCancel",
        "nativeCancellationReset",
        "nativeCancellationIsCancelled",
        "nativeSearch",
    ];

    for method in methods {
        assert_eq!(
            occurrences(KOTLIN_WRAPPER, &format!("external fun {method}")),
            1,
            "Kotlin must declare {method} exactly once"
        );
        assert_eq!(
            occurrences(
                RUST_EXPORTS,
                &format!("Java_com_ekkus93_chessengine_NativeChessEngineBindings_{method}")
            ),
            1,
            "Rust must export {method} exactly once"
        );
    }
}

#[test]
fn kotlin_owner_contract_is_explicit_and_background_only() {
    for required in [
        "class ChessEngine private constructor",
        ") : Closeable",
        "override fun close()",
        "Executors.newSingleThreadExecutor",
        "only one search may be outstanding per engine",
        "NativeChessEngineBindings.nativeCancellationCancel",
        "PhantomReference<ChessEngine>",
        "private val lifecycleLock = ReentrantReadWriteLock()",
    ] {
        assert!(
            KOTLIN_WRAPPER.contains(required),
            "missing Kotlin ownership/search contract marker: {required}"
        );
    }

    assert!(!KOTLIN_WRAPPER.contains("fun searchBlocking"));
    assert!(!KOTLIN_WRAPPER.contains("System.gc()"));
}

#[test]
fn compact_search_record_field_count_is_shared_by_both_layers() {
    assert!(KOTLIN_WRAPPER.contains("private const val FIELD_COUNT = 13"));
    assert!(RUST_EXPORTS.contains("SearchArguments"));
}
