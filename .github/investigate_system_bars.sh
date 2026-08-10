#!/usr/bin/env bash
set -u

rm -rf isolated-systembar
mkdir -p isolated-systembar
adb shell rm -rf /sdcard/Download/RustChessEvidence || true

gradle -p android-harness :android-app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=com.ekkus93.chessapp.SystemBarAppearanceInstrumentedTest --no-daemon --stacktrace --console=plain
status=$?

adb pull /sdcard/Download/RustChessEvidence/system-bars-api35.png isolated-systembar/test-screenshot.png || true
adb exec-out screencap -p > isolated-systembar/post-test-screen.png || true
adb shell dumpsys window > isolated-systembar/dumpsys-window.txt || true

exit "${status}"
