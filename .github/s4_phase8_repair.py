from pathlib import Path

path = Path('.github/s4_phase8.py')
text = path.read_text()
old = '    let candidate_weights = EvaluationWeightSet::new(artifact.identifier, artifact.weights)?;'
new = '    let candidate_weights = EvaluationWeightSet::new(artifact.identifier, artifact.weights);'
if text.count(old) != 1:
    raise SystemExit('candidate weight construction anchor missing')
path.write_text(text.replace(old, new, 1))
