#!/usr/bin/env python3
"""Compare Task 24 benchmark TSVs with conservative hosted-runner budgets."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

MEDIAN_LIMIT_PERCENT = 150
DISTRIBUTION_LIMIT_PERCENT = 125
FAST_MEDIAN_SLACK_NS = 50
FAST_DISTRIBUTION_SLACK_NS = 25
ALLOCATION_PERCENT = 125
ALLOCATION_COUNT_SLACK = 2
ALLOCATION_BYTE_SLACK = 65_536


@dataclass(frozen=True)
class Row:
    benchmark: str
    operations: int
    median_ns: int
    minimum_ns: int
    maximum_ns: int
    allocations: int
    allocated_bytes: int
    checksum: int


def read_rows(path: Path) -> dict[str, Row]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {
            "benchmark",
            "operations_per_sample",
            "median_ns_per_operation",
            "minimum_ns_per_operation",
            "maximum_ns_per_operation",
            "median_allocations_per_sample",
            "median_allocated_bytes_per_sample",
            "checksum",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: missing required Task 24 columns")
        rows: dict[str, Row] = {}
        for raw in reader:
            name = raw["benchmark"]
            if not name:
                raise ValueError(f"{path}: empty benchmark name")
            if name in rows:
                raise ValueError(f"{path}: duplicate benchmark {name}")
            rows[name] = Row(
                benchmark=name,
                operations=int(raw["operations_per_sample"]),
                median_ns=int(raw["median_ns_per_operation"]),
                minimum_ns=int(raw["minimum_ns_per_operation"]),
                maximum_ns=int(raw["maximum_ns_per_operation"]),
                allocations=int(raw["median_allocations_per_sample"]),
                allocated_bytes=int(raw["median_allocated_bytes_per_sample"]),
                checksum=int(raw["checksum"]),
            )
    if not rows:
        raise ValueError(f"{path}: no benchmark rows")
    return rows


def percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator * 100.0 / denominator:.1f}%"


def timing_regressed(expected: Row, observed: Row) -> bool:
    median_limit = max(
        expected.median_ns * MEDIAN_LIMIT_PERCENT // 100,
        expected.median_ns + FAST_MEDIAN_SLACK_NS,
    )
    distribution_limit = max(
        expected.maximum_ns * DISTRIBUTION_LIMIT_PERCENT // 100,
        expected.maximum_ns + FAST_DISTRIBUTION_SLACK_NS,
    )
    return observed.median_ns > median_limit and observed.minimum_ns > distribution_limit


def allocation_regressed(expected: Row, observed: Row) -> bool:
    count_limit = max(
        expected.allocations * ALLOCATION_PERCENT // 100,
        expected.allocations + ALLOCATION_COUNT_SLACK,
    )
    byte_limit = max(
        expected.allocated_bytes * ALLOCATION_PERCENT // 100,
        expected.allocated_bytes + ALLOCATION_BYTE_SLACK,
    )
    return observed.allocations > count_limit and observed.allocated_bytes > byte_limit


def compare(reference_path: Path, current_path: Path) -> int:
    reference = read_rows(reference_path)
    current = read_rows(current_path)
    if reference.keys() != current.keys():
        missing = sorted(reference.keys() - current.keys())
        unexpected = sorted(current.keys() - reference.keys())
        print(f"missing benchmarks: {missing}", file=sys.stderr)
        print(f"unexpected benchmarks: {unexpected}", file=sys.stderr)
        return 1

    failures: list[str] = []
    print(
        "benchmark\treference_median_ns\tcurrent_median_ns\tmedian_ratio\t"
        "reference_allocations\tcurrent_allocations\tstatus"
    )
    for name, expected in reference.items():
        observed = current[name]
        row_failures: list[str] = []
        if observed.operations != expected.operations:
            row_failures.append(
                f"operations changed from {expected.operations} to {observed.operations}"
            )
        if observed.checksum != expected.checksum:
            row_failures.append(
                f"checksum changed from {expected.checksum} to {observed.checksum}"
            )
        if timing_regressed(expected, observed):
            row_failures.append("timing exceeded both the median and distribution budgets")
        if allocation_regressed(expected, observed):
            row_failures.append(
                "allocation count and allocated bytes both exceeded their budgets"
            )

        status = "pass" if not row_failures else "regression"
        print(
            f"{name}\t{expected.median_ns}\t{observed.median_ns}\t"
            f"{percentage(observed.median_ns, expected.median_ns)}\t"
            f"{expected.allocations}\t{observed.allocations}\t{status}"
        )
        failures.extend(f"{name}: {failure}" for failure in row_failures)

    if failures:
        print("Task 24 performance comparison failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        "Task 24 performance comparison passed: benchmark identity, checksums, "
        "operation counts, broad timing budgets, and broad allocation budgets are intact."
    )
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: compare_performance.py REFERENCE.tsv CURRENT.tsv",
            file=sys.stderr,
        )
        return 2
    try:
        return compare(Path(argv[1]), Path(argv[2]))
    except (OSError, ValueError) as error:
        print(f"Task 24 performance comparison error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
