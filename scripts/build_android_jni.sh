#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

TARGET="${ANDROID_RUST_TARGET:-aarch64-linux-android}"
API_LEVEL="${ANDROID_API_LEVEL:-24}"
NDK_HOME="${ANDROID_NDK_HOME:-${ANDROID_NDK_ROOT:-}}"
HOST_TAG="${ANDROID_NDK_HOST_TAG:-linux-x86_64}"

if [[ -z "${NDK_HOME}" ]]; then
  echo "ANDROID_NDK_HOME or ANDROID_NDK_ROOT must name an installed Android NDK." >&2
  exit 2
fi

case "${TARGET}" in
  aarch64-linux-android)
    LINKER_TRIPLE="aarch64-linux-android"
    CARGO_PREFIX="AARCH64_LINUX_ANDROID"
    CC_VARIABLE="CC_aarch64_linux_android"
    AR_VARIABLE="AR_aarch64_linux_android"
    ;;
  x86_64-linux-android)
    LINKER_TRIPLE="x86_64-linux-android"
    CARGO_PREFIX="X86_64_LINUX_ANDROID"
    CC_VARIABLE="CC_x86_64_linux_android"
    AR_VARIABLE="AR_x86_64_linux_android"
    ;;
  *)
    echo "Unsupported Android Rust target: ${TARGET}" >&2
    echo "Supported targets: aarch64-linux-android, x86_64-linux-android" >&2
    exit 2
    ;;
esac

TOOLCHAIN="${NDK_HOME}/toolchains/llvm/prebuilt/${HOST_TAG}"
LINKER="${TOOLCHAIN}/bin/${LINKER_TRIPLE}${API_LEVEL}-clang"
AR="${TOOLCHAIN}/bin/llvm-ar"

if [[ ! -x "${LINKER}" ]]; then
  echo "Android linker not found: ${LINKER}" >&2
  exit 2
fi
if [[ ! -x "${AR}" ]]; then
  echo "Android LLVM archiver not found: ${AR}" >&2
  exit 2
fi

rustup target add "${TARGET}"

export "CARGO_TARGET_${CARGO_PREFIX}_LINKER=${LINKER}"
export "CARGO_TARGET_${CARGO_PREFIX}_AR=${AR}"
export "${CC_VARIABLE}=${LINKER}"
export "${AR_VARIABLE}=${AR}"

cargo build --locked -p chess-jni --target "${TARGET}" --release

LIBRARY="target/${TARGET}/release/libchess_jni.so"
if [[ ! -s "${LIBRARY}" ]]; then
  echo "Expected nonempty Android JNI library was not produced: ${LIBRARY}" >&2
  exit 1
fi

printf '%s\n' "${LIBRARY}"
