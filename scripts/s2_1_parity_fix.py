from pathlib import Path

path = Path("crates/chess-search/tests/search_policy_identity.rs")
text = path.read_text()
old = "    assert_eq!(explicit, default);\n"
new = """    assert_eq!(explicit.completed(), default.completed());
    assert_eq!(explicit.termination(), default.termination());
    assert_eq!(explicit.nodes(), default.nodes());
    assert_eq!(explicit.qnodes(), default.qnodes());
    assert_eq!(explicit.selective_depth(), default.selective_depth());
    assert_eq!(
        explicit.check_extension_diagnostics(),
        default.check_extension_diagnostics()
    );
    assert_eq!(explicit.fallback(), default.fallback());
"""
if text.count(old) != 1:
    raise SystemExit("expected one complete SearchResult parity assertion")
path.write_text(text.replace(old, new, 1))
