from pathlib import Path

path = Path('.github/s3_phase2.py')
text = path.read_text()
old = 'end = text.index("fn loss_dataset_fingerprint(\\n", start)'
new = 'end = text.index("fn loss_dataset_fingerprint(", start)'
if text.count(old) != 1:
    raise SystemExit(f'expected one phase2 helper boundary witness, found {text.count(old)}')
text = text.replace(old, new, 1)

marker = 'opt.write_text(text)\n'
if text.count(marker) != 1:
    raise SystemExit(f'expected one optimizer write marker, found {text.count(marker)}')
patch = '''# Patch objective call sites that intentionally share the same trailing shape.\nremaining_objective = "            self.config.regularization_strength,\\n        )?;"\nif text.count(remaining_objective) != 2:\n    raise SystemExit(f"expected two remaining objective call sites, found {text.count(remaining_objective)}")\ntext = text.replace(\n    remaining_objective,\n    "            self.config.regularization_strength,\\n            self.config.parameter_mask,\\n        )?;",\n    2,\n)\nopt.write_text(text)\n'''
text = text.replace(marker, patch, 1)
path.write_text(text)
