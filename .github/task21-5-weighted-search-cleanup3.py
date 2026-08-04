from pathlib import Path


alpha_beta = Path("crates/chess-search/src/alpha_beta.rs")
text = alpha_beta.read_text()
old = '''        Self {
            window,
            check_extension_enabled,
            weights,
        }
    }
}

pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights'''
new = '''        Self {
            window,
            check_extension_enabled,
            weights,
        }
    }

    pub(crate) const fn window(self) -> AlphaBetaWindow {
        self.window
    }
}

pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights'''
if text.count(old) != 1:
    raise SystemExit("unexpected AlphaBetaSearchPolicy implementation")
alpha_beta.write_text(text.replace(old, new, 1))


iterative = Path("crates/chess-search/src/iterative_deepening.rs")
text = iterative.read_text()
for old, new in (
    ("policy.window.alpha()", "policy.window().alpha()"),
    ("policy.window.beta()", "policy.window().beta()"),
):
    if text.count(old) != 1:
        raise SystemExit(f"unexpected policy-window use: {old}")
    text = text.replace(old, new, 1)
iterative.write_text(text)
