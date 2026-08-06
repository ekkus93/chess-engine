from pathlib import Path

tracker_path = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
audit_path = Path("scripts/task_s2_9_null_move_validation_audit.sh")

tracker = tracker_path.read_text(encoding="utf-8")
old = "- S2-9.4 correctness, development strength, and final disposition are not claimed."
new = "- S2-9.3 itself did not claim S2-9.4 correctness, development strength, or final disposition; those are recorded independently below."
if tracker.count(old) != 1:
    raise SystemExit(f"expected one stale S2-9.4 disclaimer, found {tracker.count(old)}")
tracker_path.write_text(tracker.replace(old, new, 1), encoding="utf-8")

audit = audit_path.read_text(encoding="utf-8")nmarker = "grep -Fq '## S2-9.4 validation record' \"$tracker\" || fail \"validation record is missing\"\n"
insert = marker + "if grep -Fq -- '- S2-9.4 correctness, development strength, and final disposition are not claimed.' \"$tracker\"; then\n  fail \"stale pre-validation disclaimer remains\"\nfi\n"
if audit.count(marker) != 1:
    raise SystemExit(f"expected one audit insertion marker, found {audit.count(marker)}")
audit_path.write_text(audit.replace(marker, insert, 1), encoding="utf-8")

Path(__file__).unlink()
