#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="android-current-ui-gallery"
mkdir -p "${OUT_DIR}"
adb install -r android-harness/android-app/build/outputs/apk/debug/android-app-debug.apk

find_bounds() {
  local kind="$1"
  local needle="$2"
  adb shell uiautomator dump /sdcard/window.xml >/dev/null
  adb pull /sdcard/window.xml window.xml >/dev/null
  python3 - "$kind" "$needle" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET
kind, needle = sys.argv[1], sys.argv[2]
root = ET.parse("window.xml").getroot()
for node in root.iter("node"):
    text = node.attrib.get("text", "")
    desc = node.attrib.get("content-desc", "")
    matched = (kind == "text" and text == needle) or (
        kind == "desc-prefix" and (desc == needle or desc.startswith(needle + " "))
    )
    if matched:
        nums = [int(value) for value in re.findall(r"\d+", node.attrib["bounds"])]
        print(*nums)
        raise SystemExit(0)
raise SystemExit(f"UI node not found: {kind}={needle!r}")
PY
}

tap_bounds() {
  local bounds="$1"
  read -r x1 y1 x2 y2 <<<"${bounds}"
  adb shell input tap "$(( (x1 + x2) / 2 ))" "$(( (y1 + y2) / 2 ))"
}

tap_text() {
  tap_bounds "$(find_bounds text "$1")"
  sleep 1
}

tap_desc_prefix() {
  tap_bounds "$(find_bounds desc-prefix "$1")"
  sleep 0.35
}

capture() {
  adb exec-out screencap -p > "${OUT_DIR}/$1"
  test -s "${OUT_DIR}/$1"
}

launch_setup() {
  adb shell am force-stop com.ekkus93.chessapp
  adb shell am start -W -n com.ekkus93.chessapp/.MainActivity >/dev/null
  sleep 2
}

launch_setup
tap_text "Start game"
capture game-white-top.png

tap_desc_prefix "h2"
tap_desc_prefix "h3"
sleep 2
capture game-white-after-engine.png

# Scroll the single in-game page to expose actions, engine metrics, and move history.
adb shell input swipe 540 1650 540 650 500
sleep 1
capture game-white-lower.png

tap_text "New game"
capture dialog-new-game.png
tap_text "Cancel"

tap_text "Restart"
capture dialog-restart.png
tap_text "Cancel"

tap_text "Resign"
capture dialog-resign.png
tap_text "Cancel"

launch_setup
tap_text "Black"
tap_text "Start game"
sleep 2
capture game-black-top.png
