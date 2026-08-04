from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "compare_performance.py"
MODULE_NAME = "compare_performance"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load compare_performance.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = MODULE
SPEC.loader.exec_module(MODULE)

HEADER = (
    "benchmark\tsamples\toperations_per_sample\tmedian_ns_per_operation\t"
    "minimum_ns_per_operation\tmaximum_ns_per_operation\t"
    "median_allocations_per_sample\tmedian_allocated_bytes_per_sample\t"
    "maximum_allocations_per_sample\tchecksum\n"
)
REFERENCE = (
    HEADER
    + "fast\t7\t100\t2\t2\t2\t0\t0\t0\t1\n"
    + "slow\t7\t1\t1000\t900\t1100\t10\t1000\t10\t2\n"
)


class ComparePerformanceTests(unittest.TestCase):
    def compare(self, current: str) -> int:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference_path = root / "reference.tsv"
            current_path = root / "current.tsv"
            reference_path.write_text(REFERENCE, encoding="utf-8")
            current_path.write_text(current, encoding="utf-8")
            return MODULE.compare(reference_path, current_path)

    def test_identical_results_pass(self) -> None:
        self.assertEqual(0, self.compare(REFERENCE))

    def test_fast_operation_absolute_slack_avoids_nanosecond_noise(self) -> None:
        current = (
            HEADER
            + "fast\t7\t100\t40\t30\t45\t0\t0\t0\t1\n"
            + "slow\t7\t1\t1000\t900\t1100\t10\t1000\t10\t2\n"
        )
        self.assertEqual(0, self.compare(current))

    def test_one_timing_signal_alone_does_not_fail(self) -> None:
        current = (
            HEADER
            + "fast\t7\t100\t2\t2\t2\t0\t0\t0\t1\n"
            + "slow\t7\t1\t1600\t1000\t1700\t10\t1000\t10\t2\n"
        )
        self.assertEqual(0, self.compare(current))

    def test_distribution_confirmed_timing_regression_fails(self) -> None:
        current = (
            HEADER
            + "fast\t7\t100\t2\t2\t2\t0\t0\t0\t1\n"
            + "slow\t7\t1\t1600\t1500\t1700\t10\t1000\t10\t2\n"
        )
        self.assertEqual(1, self.compare(current))

    def test_checksum_change_fails(self) -> None:
        current = (
            HEADER
            + "fast\t7\t100\t2\t2\t2\t0\t0\t0\t99\n"
            + "slow\t7\t1\t1000\t900\t1100\t10\t1000\t10\t2\n"
        )
        self.assertEqual(1, self.compare(current))

    def test_count_and_bytes_allocation_regression_fails(self) -> None:
        current = (
            HEADER
            + "fast\t7\t100\t2\t2\t2\t0\t0\t0\t1\n"
            + "slow\t7\t1\t1000\t900\t1100\t20\t70000\t20\t2\n"
        )
        self.assertEqual(1, self.compare(current))


if __name__ == "__main__":
    unittest.main()
