from pathlib import Path

path = Path('.github/s2_8_evidence_bootstrap.py')
text = path.read_text(encoding='utf-8')


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one occurrence, found {count}')
    text = text.replace(old, new, 1)


replace_once(
    '    "    let mut total_lmr_reductions = 0_u64;\\n"\n'
    '    "    let mut total_lmr_verification_searches = 0_u64;\\n",\n'
    '    "    let mut total_lmr_reductions = 0_u64;\\n"\n'
    '    "    let mut total_lmr_reduced_fail_highs = 0_u64;\\n"\n'
    '    "    let mut total_lmr_verification_searches = 0_u64;\\n",',
    '    "    let mut total_zero_window_searches = 0_u64;\\n"\n'
    '    "    let mut total_researches = 0_u64;\\n",\n'
    '    "    let mut total_zero_window_searches = 0_u64;\\n"\n'
    '    "    let mut total_reduced_fail_highs = 0_u64;\\n"\n'
    '    "    let mut total_researches = 0_u64;\\n",',
    'generic parity totals',
)
replace_once(
    '    "        total_lmr_verification_searches = total_lmr_verification_searches\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\\n"\n'
    '    "            .ok_or(\\"LMR re-search total overflow\\")?;\\n",\n'
    '    "        total_lmr_reduced_fail_highs = total_lmr_reduced_fail_highs\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_reduced_fail_highs())\\n"\n'
    '    "            .ok_or(\\"LMR reduced fail-high total overflow\\")?;\\n"\n'
    '    "        total_lmr_verification_searches = total_lmr_verification_searches\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\\n"\n'
    '    "            .ok_or(\\"LMR verification total overflow\\")?;\\n",',
    '    "        total_researches = total_researches\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\\n"\n'
    '    "            .ok_or(\\"LMR re-search total overflow\\")?;\\n",\n'
    '    "        total_reduced_fail_highs = total_reduced_fail_highs\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_reduced_fail_highs())\\n"\n'
    '    "            .ok_or(\\"LMR reduced fail-high total overflow\\")?;\\n"\n'
    '    "        total_researches = total_researches\\n"\n'
    '    "            .checked_add(candidate_diagnostics.lmr_verification_searches())\\n"\n'
    '    "            .ok_or(\\"LMR verification total overflow\\")?;\\n",',
    'generic parity accumulation',
)
replace_once(
    '    "    if total_lmr_verification_searches > total_lmr_reductions {\\n"\n'
    '    "        return Err(\\"LMR re-search total exceeds zero-window search total\\".into());\\n"\n'
    '    "    }\\n",\n'
    '    "    if total_lmr_reduced_fail_highs != total_lmr_verification_searches {\\n"\n'
    '    "        return Err(\\"LMR reduced fail-high and verification totals differ\\".into());\\n"\n'
    '    "    }\\n"\n'
    '    "    if total_lmr_verification_searches > total_lmr_reductions {\\n"\n'
    '    "        return Err(\\"LMR verification total exceeds reduction total\\".into());\\n"\n'
    '    "    }\\n",',
    '    "    if total_researches > total_zero_window_searches {\\n"\n'
    '    "        return Err(\\"LMR re-search total exceeds zero-window search total\\".into());\\n"\n'
    '    "    }\\n",\n'
    '    "    if total_reduced_fail_highs != total_researches {\\n"\n'
    '    "        return Err(\\"LMR reduced fail-high and verification totals differ\\".into());\\n"\n'
    '    "    }\\n"\n'
    '    "    if total_researches > total_zero_window_searches {\\n"\n'
    '    "        return Err(\\"LMR verification total exceeds reduction total\\".into());\\n"\n'
    '    "    }\\n",',
    'generic parity invariant',
)
replace_once(
    '    "    writeln!(output, \\"total_lmr_verification_searches\\t{total_lmr_verification_searches}\\")?;\\n",\n'
    '    "    writeln!(output, \\"total_lmr_reduced_fail_highs\\t{total_lmr_reduced_fail_highs}\\")?;\\n"\n'
    '    "    writeln!(output, \\"total_lmr_verification_searches\\t{total_lmr_verification_searches}\\")?;\\n",',
    '    "    writeln!(output, \\"total_lmr_verification_searches\\t{total_researches}\\")?;\\n",\n'
    '    "    writeln!(output, \\"total_lmr_reduced_fail_highs\\t{total_reduced_fail_highs}\\")?;\\n"\n'
    '    "    writeln!(output, \\"total_lmr_verification_searches\\t{total_researches}\\")?;\\n",',
    'generic parity summary',
)

text = text.replace(
    'Path(".github/s2_8_evidence_bootstrap.py").unlink()\n',
    'Path(".github/s2_8_evidence_bootstrap.py").unlink()\n'
    'Path(".github/s2_8_evidence_bootstrap_repair.py").unlink()\n',
    1,
)
path.write_text(text, encoding='utf-8')
Path(__file__).unlink()
