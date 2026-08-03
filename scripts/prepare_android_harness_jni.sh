#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_ROOT="${ANDROID_HARNESS_JNI_LIBS_DIR:-${ROOT_DIR}/android-harness/android-smoke/src/main/jniLibs}"

rm -rf "${OUTPUT_ROOT}"
mkdir -p "${OUTPUT_ROOT}"

build_and_copy() {
  local target="$1"
  local abi="$2"
  ANDROID_RUST_TARGET="${target}" "${ROOT_DIR}/scripts/build_android_jni.sh"
  local source="${ROOT_DIR}/target/${target}/release/libchess_jni.so"
  local destination="${OUTPUT_ROOT}/${abi}/libchess_jni.so"
  install -D -m 0755 "${source}" "${destination}"
  test -s "${destination}"
  printf '%s\n' "${destination}"
}

build_and_copy aarch64-linux-android arm64-v8a
build_and_copy x86_64-linux-android x86_64
