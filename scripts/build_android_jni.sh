#!/usr/bin/env bash
set -euo pipefail

TARGET="aarch64-linux-android"
API_LEVEL="${ANDROID_API_LEVEL:-24}"
NDK_HOME="${ANDROID_NDK_HOME:-${ANDROID_NDK_ROOT:-}}"
HOST_TAG="${ANDROID_NDK_HOST_TAG:-linux-x86_64}"

if [[ -z "${NDK_HOME}" ]]; then
  echo "ANDROID_NDK_HOME or ANDROID_NDK_ROOT must name an installed Android NDK." >&2
  exit 2
fi

TOOLCHAIN="${NDK_HOME}/toolchains/llvm/prebuilt/${HOST_TAG}"
LINKER="${TOOLCHAIN}/bin/aarch64-linux-android${API_LEVEL}-clang"
AR="${TOOLCHAIN}/bin/llvm-ar"

if [[ ! -x "${LINKER}" ]]; then
  echo "Android AArch64 linker not found: ${LINKER}" >&2
  exit 2
fi
if [[ ! -x "${AR}" ]]; then
  echo "Android LLVM archiver not found: ${AR}" >&2
  exit 2
fi

rustup target add "${TARGET}"

export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="${LINKER}"
export CARGO_TARGET_AARCH64_LINUX_ANDROID_AR="${AR}"
export CC_aarch64_linux_android="${LINKER}"
export AR_aarch64_linux_android="${AR}"

cargo build --locked -p chess-jni --target "${TARGET}" --release

LIBRARY="target/${TARGET}/release/libchess_jni.so"
if [[ ! -s "${LIBRARY}" ]]; then
  echo "Expected nonempty Android JNI library was not produced: ${LIBRARY}" >&2
  exit 1
fi

printf '%s\n' "${LIBRARY}"
