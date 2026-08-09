#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SMOKE_OUTPUT_ROOT="${ANDROID_HARNESS_JNI_LIBS_DIR:-${ROOT_DIR}/android-harness/android-smoke/src/main/jniLibs}"
APP_OUTPUT_ROOT="${ANDROID_APP_JNI_LIBS_DIR:-${ROOT_DIR}/android-harness/android-app/src/main/jniLibs}"

rm -rf "${SMOKE_OUTPUT_ROOT}" "${APP_OUTPUT_ROOT}"
mkdir -p "${SMOKE_OUTPUT_ROOT}" "${APP_OUTPUT_ROOT}"

build_and_copy() {
  local target="$1"
  local abi="$2"
  ANDROID_RUST_TARGET="${target}" "${ROOT_DIR}/scripts/build_android_jni.sh"
  local source="${ROOT_DIR}/target/${target}/release/libchess_jni.so"
  local smoke_destination="${SMOKE_OUTPUT_ROOT}/${abi}/libchess_jni.so"
  local app_destination="${APP_OUTPUT_ROOT}/${abi}/libchess_jni.so"
  install -D -m 0755 "${source}" "${smoke_destination}"
  install -D -m 0755 "${source}" "${app_destination}"
  test -s "${smoke_destination}"
  test -s "${app_destination}"
  printf '%s\n' "${smoke_destination}" "${app_destination}"
}

build_and_copy aarch64-linux-android arm64-v8a
build_and_copy x86_64-linux-android x86_64
