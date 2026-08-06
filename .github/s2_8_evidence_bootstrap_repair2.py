from pathlib import Path

path = Path('.github/s2_8_evidence_bootstrap.py')
text = path.read_text(encoding='utf-8')
old = '''source = replace_once(
    source,
    "        (\\n"
    "            &mut aggregate.lmr_verification_searches,\\n"
    "            diagnostics.lmr_verification_searches(),\\n"
    "        ),\\n",
    "        (\\n"
    "            &mut aggregate.lmr_reduced_fail_highs,\\n"
    "            diagnostics.lmr_reduced_fail_highs(),\\n"
    "        ),\\n"
    "        (\\n"
    "            &mut aggregate.lmr_verification_searches,\\n"
    "            diagnostics.lmr_verification_searches(),\\n"
    "        ),\\n",
    "benchmark aggregate fail-high",
)
'''
new = '''source = replace_once(
    source,
    "        (&mut aggregate.lmr_verification_searches, diagnostics.lmr_verification_searches()),\\n",
    "        (&mut aggregate.lmr_reduced_fail_highs, diagnostics.lmr_reduced_fail_highs()),\\n"
    "        (&mut aggregate.lmr_verification_searches, diagnostics.lmr_verification_searches()),\\n",
    "benchmark aggregate fail-high",
)
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'aggregate bootstrap repair: expected exactly one occurrence, found {count}')
text = text.replace(old, new, 1)
text = text.replace(
    'Path(".github/s2_8_evidence_bootstrap_repair.py").unlink()\\n',
    'Path(".github/s2_8_evidence_bootstrap_repair.py").unlink()\\n'
    'Path(".github/s2_8_evidence_bootstrap_repair2.py").unlink()\\n',
    1,
)
path.write_text(text, encoding='utf-8')
Path(__file__).unlink()
