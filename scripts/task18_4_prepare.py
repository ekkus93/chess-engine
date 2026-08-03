#!/usr/bin/env python3
from pathlib import Path

bridge_path = Path("crates/chess-jni/src/bridge.rs")
bridge = bridge_path.read_text()
old_search = '''pub(crate) fn search(handle: jlong, arguments: SearchArguments) -> BridgeResult<String> {
    let request = search_request(arguments)?;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result records are complete and live for the call.
    ensure_code(unsafe {
        chess_engine_search(token_from_jlong(handle), &request, &mut result)
    })?;

    let best_move = copied_text(&result.best_move, "best move");
    let ponder_move = copied_text(&result.ponder_move, "ponder move");
    let principal_variation = copied_text(&result.principal_variation, "principal variation");

    // SAFETY: `result` is the unchanged current-version record returned above.
    let free_result = unsafe { chess_engine_search_result_free(&mut result) };
    ensure_code(free_result)?;

    let fields = [
        best_move?,
        ponder_move?,
        principal_variation?,
        (result.score_kind as i32).to_string(),
        result.score_value.to_string(),
        result.completed_depth.to_string(),
        result.selective_depth.to_string(),
        (result.termination_kind as i32).to_string(),
        (result.fallback_kind as i32).to_string(),
        result.termination_value.to_string(),
        result.nodes.to_string(),
        result.qnodes.to_string(),
        result.elapsed_milliseconds.to_string(),
    ];
    Ok(fields.join("\\n"))
}
'''
new_search = '''pub(crate) fn search(handle: jlong, arguments: SearchArguments) -> BridgeResult<String> {
    let request = search_request(arguments)?;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result records are complete and live for the call.
    ensure_code(unsafe {
        chess_engine_search(token_from_jlong(handle), &request, &mut result)
    })?;

    let best_move = copied_text(&result.best_move, "best move");
    let ponder_move = copied_text(&result.ponder_move, "ponder move");
    let principal_variation = copied_text(&result.principal_variation, "principal variation");
    let score_kind = result.score_kind as i32;
    let score_value = result.score_value;
    let completed_depth = result.completed_depth;
    let selective_depth = result.selective_depth;
    let termination_kind = result.termination_kind as i32;
    let fallback_kind = result.fallback_kind as i32;
    let termination_value = result.termination_value;
    let nodes = result.nodes;
    let qnodes = result.qnodes;
    let elapsed_milliseconds = result.elapsed_milliseconds;

    // SAFETY: `result` is the unchanged current-version record returned above.
    let free_result = unsafe { chess_engine_search_result_free(&mut result) };
    ensure_code(free_result)?;

    let fields = [
        best_move?,
        ponder_move?,
        principal_variation?,
        score_kind.to_string(),
        score_value.to_string(),
        completed_depth.to_string(),
        selective_depth.to_string(),
        termination_kind.to_string(),
        fallback_kind.to_string(),
        termination_value.to_string(),
        nodes.to_string(),
        qnodes.to_string(),
        elapsed_milliseconds.to_string(),
    ];
    Ok(fields.join("\\n"))
}
'''
if bridge.count(old_search) != 1:
    raise SystemExit("expected exactly one pre-normalization search implementation")
bridge = bridge.replace(old_search, new_search)

old_tests = '''    #[test]
    fn zero_search_values_remain_absent() {
        let request = search_request(SearchArguments {
            depth: 0,
            nodes: 0,
            soft_time_milliseconds: 0,
            hard_time_milliseconds: 0,
            infinite: JNI_FALSE,
            check_extension: JNI_FALSE,
            cancellation_handle: 0,
        })
        .expect("zero values create the intentionally incomplete request");
        assert_eq!(request.flags, 0);
    }
}
'''
new_tests = '''    #[test]
    fn zero_search_values_remain_absent() {
        let request = search_request(SearchArguments {
            depth: 0,
            nodes: 0,
            soft_time_milliseconds: 0,
            hard_time_milliseconds: 0,
            infinite: JNI_FALSE,
            check_extension: JNI_FALSE,
            cancellation_handle: 0,
        })
        .expect("zero values create the intentionally incomplete request");
        assert_eq!(request.flags, 0);
    }

    #[test]
    fn bridge_lifecycle_preserves_typed_c_abi_behavior() {
        let engine = super::create_engine(1).expect("bridge engine constructs");
        assert_eq!(
            super::fen(engine).expect("starting FEN is available"),
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        );
        let legal = super::legal_moves(engine).expect("legal moves are available");
        assert_eq!(legal.lines().count(), 20);
        assert!(legal.lines().any(|current| current == "e2e4"));

        super::play_move(engine, "e2e4").expect("legal move applies");
        assert!(super::game_status(engine)
            .expect("status is available")
            .starts_with("0,"));

        let result = super::search(
            engine,
            SearchArguments {
                depth: 2,
                nodes: 0,
                soft_time_milliseconds: 0,
                hard_time_milliseconds: 0,
                infinite: JNI_FALSE,
                check_extension: JNI_FALSE,
                cancellation_handle: 0,
            },
        )
        .expect("fixed-depth JNI bridge search succeeds");
        let fields = result.split('\\n').collect::<Vec<_>>();
        assert_eq!(fields.len(), 13);
        assert!(!fields[0].is_empty());
        assert_eq!(fields[5], "2");
        assert_eq!(fields[7], "1");

        super::reset_position(engine).expect("position reset succeeds");
        super::destroy_engine(engine).expect("engine destroy succeeds");
    }

    #[test]
    fn invalid_fen_keeps_exact_result_code_and_position() {
        let engine = super::create_engine(1).expect("bridge engine constructs");
        let before = super::fen(engine).expect("starting FEN is available");
        let error = super::set_position(engine, "not a fen")
            .expect_err("malformed FEN must fail through the JNI bridge");
        assert_eq!(error.code(), ChessEngineResultCode::InvalidFen);
        assert_eq!(super::fen(engine).expect("FEN remains readable"), before);
        super::destroy_engine(engine).expect("engine destroy succeeds");
    }

    #[test]
    fn infinite_bridge_search_stops_from_another_thread() {
        use std::{sync::mpsc, thread, time::Duration};

        let engine = super::create_engine(1).expect("bridge engine constructs");
        let cancellation = super::create_cancellation().expect("cancellation token constructs");
        let (started_sender, started_receiver) = mpsc::sync_channel(0);
        let (result_sender, result_receiver) = mpsc::channel();

        let worker = thread::spawn(move || {
            started_sender
                .send(())
                .expect("controller remains connected");
            let result = super::search(
                engine,
                SearchArguments {
                    depth: 0,
                    nodes: 0,
                    soft_time_milliseconds: 0,
                    hard_time_milliseconds: 0,
                    infinite: JNI_TRUE,
                    check_extension: JNI_FALSE,
                    cancellation_handle: cancellation,
                },
            );
            result_sender
                .send(result)
                .expect("result receiver remains connected");
        });

        started_receiver
            .recv_timeout(Duration::from_secs(1))
            .expect("worker reaches search boundary");
        thread::sleep(Duration::from_millis(20));
        super::cancel(cancellation).expect("cross-thread cancellation succeeds");
        let result = result_receiver
            .recv_timeout(Duration::from_secs(5))
            .expect("cancelled search returns within deadline")
            .expect("cancelled search returns a typed snapshot");
        worker.join().expect("search worker does not panic");

        let fields = result.split('\\n').collect::<Vec<_>>();
        assert_eq!(fields.len(), 13);
        assert_eq!(fields[7], "5");
        assert!(!fields[0].is_empty());
        super::destroy_cancellation(cancellation).expect("cancellation token destroys");
        super::destroy_engine(engine).expect("engine destroys");
    }
}
'''
if bridge.count(old_tests) != 1:
    raise SystemExit("expected exactly one bridge test tail")
bridge_path.write_text(bridge.replace(old_tests, new_tests))

kotlin_path = Path(
    "crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt"
)
kotlin = kotlin_path.read_text()
if kotlin.count("import java.util.Collections\n") != 1:
    raise SystemExit("expected one unused Collections import")
kotlin = kotlin.replace("import java.util.Collections\n", "")
if kotlin.count("private const val DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES = 16L") != 1:
    raise SystemExit("expected one pre-normalization Kotlin table default")
kotlin = kotlin.replace(
    "private const val DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES = 16L",
    "private const val DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES = 1L",
)
kotlin_path.write_text(kotlin)
