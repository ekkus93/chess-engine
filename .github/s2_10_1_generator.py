from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:120]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


alpha = "crates/chess-search/src/alpha_beta.rs"
replace_once(
    alpha,
    "    pub(crate) fn is_full(self) -> bool {\n        self == Self::full()\n    }\n\n",
    "    pub(crate) fn is_full(self) -> bool {\n        self == Self::full()\n    }\n\n    fn is_null(self) -> bool {\n        self.beta.centipawns().checked_sub(self.alpha.centipawns()) == Some(1)\n    }\n\n",
)
replace_once(
    alpha,
    "        || parent_in_check\n        || window.alpha().is_mate()\n",
    "        || parent_in_check\n        || !window.is_null()\n        || window.alpha().is_mate()\n",
)
replace_once(
    alpha,
    "            window(-200, 200),\n            true,\n            &EvaluationWeights::DEFAULT,\n        )\n        .expect(\"decision succeeds\")\n        .expect(\"frontier is eligible\");",
    "            window(-200, -199),\n            true,\n            &EvaluationWeights::DEFAULT,\n        )\n        .expect(\"decision succeeds\")\n        .expect(\"non-PV frontier is eligible\");",
)
replace_once(
    alpha,
    "    fn root_check_deeper_and_mate_sensitive_nodes_are_protected() {\n        let position = Position::starting();\n        for (depth, ply, parent_in_check, current_window) in [\n            (1, 0, false, window(-200, 200)),\n            (1, 1, true, window(-200, 200)),\n            (2, 1, false, window(-200, 200)),\n            (1, 1, false, AlphaBetaWindow::full()),\n        ] {",
    "    fn root_pv_check_deeper_and_mate_sensitive_nodes_are_protected() {\n        let position = Position::starting();\n        for (depth, ply, parent_in_check, current_window) in [\n            (1, 0, false, window(-200, -199)),\n            (1, 1, false, window(-200, 200)),\n            (1, 1, true, window(-200, -199)),\n            (2, 1, false, window(-200, -199)),\n            (1, 1, false, AlphaBetaWindow::full()),\n        ] {",
)

Path(__file__).unlink()
