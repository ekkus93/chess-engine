from pathlib import Path


alpha_beta = Path("crates/chess-search/src/alpha_beta.rs")
text = alpha_beta.read_text()
start_marker = "pub(crate) fn alpha_beta_search_window_in_current_generation<Probe>("
end_marker = "pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>("
if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    raise SystemExit("unexpected alpha-beta weighted-window functions")
start = text.index(start_marker)
end = text.index(end_marker)
if end <= start:
    raise SystemExit("weighted alpha-beta function precedes compatibility wrapper")
alpha_beta.write_text(text[:start] + text[end:])


iterative = Path("crates/chess-search/src/iterative_deepening.rs")
text = iterative.read_text()
import_line = "        alpha_beta_search_window_in_current_generation,\n"
if text.count(import_line) != 1:
    raise SystemExit("unexpected default alpha-beta window import")
iterative.write_text(text.replace(import_line, "", 1))
