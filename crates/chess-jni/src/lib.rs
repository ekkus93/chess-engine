//! Android JNI adapter over the stable `chess-ffi` C boundary.
//!
//! The exported methods use the opaque engine and cancellation tokens from the
//! stable C ABI. JNI conversion, Java exception creation, and the small amount
//! of required unsafe pointer access remain isolated in this crate. Chess rules,
//! search behavior, ownership registries, and result-code semantics are not
//! duplicated here.

mod bridge;

use bridge::{boundary, null_jstring, output_string, SearchArguments};
use jni::{
    objects::{JObject, JString},
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
