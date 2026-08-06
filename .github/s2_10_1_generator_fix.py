from pathlib import Path

# The generator workflow expects a second repair payload. This stage is intentionally
# empty; all review corrections are applied by s2_10_1_generator.py.
Path(__file__).unlink()
