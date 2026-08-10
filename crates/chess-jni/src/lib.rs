//! Android JNI adapters for the stable engine boundary and shared interactive app layer.
//!
//! `NativeChessEngineBindings` continues to expose the established low-level
//! `chess-ffi` API. `NativeChessAppBindings` adds a high-level Human-vs-Engine
//! session API backed by `chess-app`, so Android presentation code does not
//! duplicate game lifecycle, search scheduling, stale-result rejection, or
//! interactive fail-closed search policy.

mod app_bridge;
mod bridge;

use bridge::{boundary, null_jstring, output_string, SearchArguments};
use jni::{
    objects::{JByteArray, JObject, JString},
    sys::{jboolean, jint, jlong, jstring, JNI_FALSE},
    JNIEnv,
};

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeVersion"]
pub extern "system" fn native_version(mut env: JNIEnv<'_>, _binding: JObject<'_>) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::version()?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCreate"]
pub extern "system" fn native_create(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    transposition_table_mebibytes: jlong,
) -> jlong {
    boundary(&mut env, 0, |_env| {
        bridge::create_engine(transposition_table_mebibytes)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCreateWithIndexedBook"]
pub extern "system" fn native_create_with_indexed_book(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    transposition_table_mebibytes: jlong,
    book_data: JByteArray<'_>,
    enabled: jboolean,
) -> jlong {
    boundary(&mut env, 0, |env| {
        if book_data.is_null() {
            return Err(bridge::BridgeError::InvalidArgument(
                "opening-book byte array is null".to_owned(),
            ));
        }
        let bytes = env.convert_byte_array(&book_data)?;
        bridge::create_engine_with_indexed_book(transposition_table_mebibytes, &bytes, enabled)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeDestroy"]
pub extern "system" fn native_destroy(mut env: JNIEnv<'_>, _binding: JObject<'_>, handle: jlong) {
    boundary(&mut env, (), |_env| bridge::destroy_engine(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeResetPosition"]
pub extern "system" fn native_reset_position(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) {
    boundary(&mut env, (), |_env| bridge::reset_position(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeSetPosition"]
pub extern "system" fn native_set_position(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
    fen: JString<'_>,
) {
    boundary(&mut env, (), |env| {
        let fen = bridge::java_string(env, fen)?;
        bridge::set_position(handle, &fen)
    });
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeFen"]
pub extern "system" fn native_fen(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::fen(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeOpeningBookMove"]
pub extern "system" fn native_opening_book_move(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::opening_book_move(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeLegalMoves"]
pub extern "system" fn native_legal_moves(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::legal_moves(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativePlayMove"]
pub extern "system" fn native_play_move(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
    move_text: JString<'_>,
) {
    boundary(&mut env, (), |env| {
        let move_text = bridge::java_string(env, move_text)?;
        bridge::play_move(handle, &move_text)
    });
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeGameStatus"]
pub extern "system" fn native_game_status(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::game_status(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeWeightIdentity"]
pub extern "system" fn native_weight_identity(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &bridge::weight_identity(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCancellationCreate"]
pub extern "system" fn native_cancellation_create(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
) -> jlong {
    boundary(&mut env, 0, |_env| bridge::create_cancellation())
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCancellationDestroy"]
pub extern "system" fn native_cancellation_destroy(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) {
    boundary(&mut env, (), |_env| bridge::destroy_cancellation(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCancellationCancel"]
pub extern "system" fn native_cancellation_cancel(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) {
    boundary(&mut env, (), |_env| bridge::cancel(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCancellationReset"]
pub extern "system" fn native_cancellation_reset(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) {
    boundary(&mut env, (), |_env| bridge::reset_cancellation(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeCancellationIsCancelled"]
pub extern "system" fn native_cancellation_is_cancelled(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jboolean {
    boundary(&mut env, JNI_FALSE, |_env| {
        bridge::cancellation_is_cancelled(handle)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeSearch"]
pub extern "system" fn native_search(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
    depth: jint,
    nodes: jlong,
    soft_time_milliseconds: jlong,
    hard_time_milliseconds: jlong,
    infinite: jboolean,
    check_extension: jboolean,
    cancellation_handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        let result = bridge::search(
            handle,
            SearchArguments {
                depth,
                nodes,
                soft_time_milliseconds,
                hard_time_milliseconds,
                infinite,
                check_extension,
                cancellation_handle,
            },
        )?;
        output_string(env, &result)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeCreate"]
pub extern "system" fn native_app_create(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    human_color: jint,
    depth: jint,
) -> jlong {
    boundary(&mut env, 0, |_env| {
        app_bridge::create_game(human_color, depth)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeDestroy"]
pub extern "system" fn native_app_destroy(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) {
    boundary(&mut env, (), |_env| app_bridge::destroy_game(handle));
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeSnapshot"]
pub extern "system" fn native_app_snapshot(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &app_bridge::snapshot(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativePoll"]
pub extern "system" fn native_app_poll(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &app_bridge::poll(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeSubmitMove"]
pub extern "system" fn native_app_submit_move(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
    move_text: JString<'_>,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        let move_text = bridge::java_string(env, move_text)?;
        output_string(env, &app_bridge::submit_move(handle, &move_text)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeRestart"]
pub extern "system" fn native_app_restart(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &app_bridge::restart(handle)?)
    })
}

#[export_name = "Java_com_ekkus93_chessengine_NativeChessAppBindings_nativeResign"]
pub extern "system" fn native_app_resign(
    mut env: JNIEnv<'_>,
    _binding: JObject<'_>,
    handle: jlong,
) -> jstring {
    boundary(&mut env, null_jstring(), |env| {
        output_string(env, &app_bridge::resign(handle)?)
    })
}
