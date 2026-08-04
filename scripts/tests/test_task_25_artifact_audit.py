import unittest

from scripts.task_25_artifact_audit import transient_generated_path, unsafe_filename


class Task25ArtifactAuditTests(unittest.TestCase):
    def test_unsafe_filename_characters_are_rejected(self) -> None:
        self.assertTrue(unsafe_filename("docs/CODE_REVIEW18*.md"))
        self.assertTrue(unsafe_filename("bad:name.txt"))
        self.assertFalse(unsafe_filename("docs/RUST_GENERATED_ARTIFACT_POLICY.md"))

    def test_transient_outputs_are_rejected_but_fixtures_are_retained(self) -> None:
        for path in (
            "target/release/chess-uci",
            "fuzz/target/debug/fuzzer",
            "tmp/report.txt",
            ".venv-oracle/bin/python",
            "tuning-output/checkpoint.bin",
            "android-harness/android-smoke/build/outputs/app.apk",
            "performance-linux-x86-64.tsv",
            "callgrind.search.out",
        ):
            self.assertTrue(transient_generated_path(path), path)
        self.assertFalse(transient_generated_path("fixtures/perft.tsv"))
        self.assertFalse(transient_generated_path("benchmarks/task24/performance-linux-arm64.tsv"))


if __name__ == "__main__":
    unittest.main()
