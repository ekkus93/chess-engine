from pathlib import Path

path = Path("crates/chess-search/src/search_policy.rs")
text = path.read_text(encoding="utf-8")
old = "parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 3)"
new = "parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 4)"
if text.count(old) != 1:
    raise SystemExit("expected one obsolete PVS unsupported-feature witness")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
Path(".github/s2_7_policy_test_repair.py").unlink()
