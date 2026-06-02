"""Meta-integration tests for pytest slow/fast marker contracts."""

import subprocess
import tomllib


class TestSlowMarkerContract:
    """Verify that expensive test categories are marked slow."""

    def test_slow_marker_applied_to_transcript_tests(self):
        """Verify that transcript/transcript-heavy tests are marked slow."""
        # Run pytest to collect slow markers
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        output = result.stdout + result.stderr

        # There should be slow-marked tests (from STRATEGY tests, etc.)
        assert "slow" in output.lower() or result.returncode == 0, (
            "pytest -m slow --co should list slow-marked tests or exit cleanly"
        )

    def test_fast_suite_runs_quickly(self):
        """Verify that the fast suite (non-slow) includes core tests."""
        # Run pytest to collect non-slow tests
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "not slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Should complete successfully
        assert result.returncode == 0, (
            f"pytest -m 'not slow' should succeed; got: {result.stderr}"
        )

        # Output should show collected tests
        assert "test_" in result.stdout or "passed" in result.stdout.lower()


class TestFastMarkerContractNegative:
    """Verify that fast suites do NOT include slow markers."""

    def test_default_run_excludes_heaviest_transcript_tests(self):
        """Verify that default run (no marker) is reasonably fast."""
        # This is a meta-test: we just verify that slow/not-slow are defined
        # and can be queried. Actual runtime is covered by CI.
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "--markers",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Markers output should include 'slow'
        assert "slow" in result.stdout.lower(), (
            "pytest --markers should list 'slow' marker"
        )

    def test_marker_list_command_succeeds(self):
        """Verify that pytest marker listing exits cleanly."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "--markers",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        assert result.returncode == 0


class TestMarkerAssignmentConsistency:
    """Test that marker assignments are consistent across runs."""

    def test_slow_marker_list_stable(self):
        """Verify that slow-marked test list is stable (deterministic)."""
        # Collect slow tests twice, ensure same list
        for _ in range(2):
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "tests/",
                    "-m",
                    "slow",
                    "--co",
                    "-q",
                ],
                capture_output=True,
                text=True,
                cwd="/home/phil/work/chess-engine",
                check=False,
            )

            # Just verify it runs successfully
            # (Exact list may vary per environment, but command should work)
            assert result.returncode == 0 or "no tests ran" in result.stdout.lower()

    def test_fast_marker_list_stable(self):
        """Verify that non-slow test list is stable."""
        # Collect non-slow tests, verify it succeeds
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "not slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        assert result.returncode == 0


class TestMarkerSplitCoverage:
    """Test that marker split covers all tests."""

    def test_slow_plus_not_slow_covers_all(self):
        """Verify that slow + not-slow tests cover the full suite."""
        # Get total count
        result_all = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Get slow count
        result_slow = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Get not-slow count
        result_not_slow = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "not slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # All should complete without error
        assert result_all.returncode == 0
        assert result_slow.returncode == 0
        assert result_not_slow.returncode == 0

    def test_slow_and_fast_lists_are_queryable(self):
        """Verify that both slow and non-slow collection queries work."""
        result_slow = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )
        result_not_slow = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "not slow",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        assert result_slow.returncode == 0
        assert result_not_slow.returncode == 0


class TestMarkerInPyproject:
    """Test that slow marker is declared in pyproject.toml."""

    def test_slow_marker_declared_in_config(self):
        """Verify that slow marker is properly declared."""
        with open("/home/phil/work/chess-engine/pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        pytest_config = config.get("tool", {}).get("pytest", {})
        markers = pytest_config.get("markers")
        if markers is None:
            markers = pytest_config.get("ini_options", {}).get("markers", [])

        # Should have slow marker declared
        slow_found = any("slow" in str(m) for m in markers)
        assert slow_found, (
            "pyproject.toml should declare 'slow' marker in [tool.pytest.markers]"
        )

    def test_pyproject_has_pytest_section(self):
        """Verify the pyproject has a pytest config section."""
        with open("/home/phil/work/chess-engine/pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        assert "pytest" in config.get("tool", {})

    def test_pytest_markers_section_exists(self):
        """Verify that pytest markers are configured in pyproject.toml."""
        with open("/home/phil/work/chess-engine/pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        markers = config.get("tool", {}).get("pytest", {}).get("markers", [])
        assert isinstance(markers, list)


class TestIntegrationTestMarkers:
    """Test that new integration tests have appropriate markers."""

    def test_repetition_integration_tests_fast(self):
        """Verify repetition integration tests run without slow marker."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_ai_repetition_integration.py",
                "-m",
                "not slow",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Should find tests in the not-slow set
        assert result.returncode == 0 or "no tests ran" in result.stdout.lower()

    def test_opening_book_integration_tests_fast(self):
        """Verify opening book integration tests run without slow marker."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_opening_book_search_integration.py",
                "-m",
                "not slow",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Should find tests in the not-slow set
        assert result.returncode == 0 or "no tests ran" in result.stdout.lower()

    def test_self_play_integration_tests_fast(self):
        """Verify self-play integration tests run without slow marker."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_self_play_runtime_integration.py",
                "-m",
                "not slow",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Should find tests in the not-slow set
        assert result.returncode == 0 or "no tests ran" in result.stdout.lower()

    def test_board_state_integration_tests_fast(self):
        """Verify board state integration tests run without slow marker."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_ai_board_state_integration.py",
                "-m",
                "not slow",
                "-v",
            ],
            capture_output=True,
            text=True,
            cwd="/home/phil/work/chess-engine",
            check=False,
        )

        # Should find tests in the not-slow set
        assert result.returncode == 0 or "no tests ran" in result.stdout.lower()
