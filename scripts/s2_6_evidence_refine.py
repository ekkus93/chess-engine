#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().with_name("s2_6_evidence_apply.py")
text = path.read_text()
old = '''#[allow(clippy::too_many_arguments)]
fn run_development_match<'a>(
    source_commit: [u8; 20],
    build_identity: &str,
    openings: &OpeningSuite,
    baseline_policy: &'a SearchPolicySet,
    candidate_policy: &'a SearchPolicySet,
    weights: &'a EvaluationWeightSet,
    protocol: EngineVariantResourceProtocol,
    protocol_name: &str,
) -> Result<EngineVariantValidationReport, Box<dyn Error>> {
    let baseline_identity = identity(
'''
new = '''fn run_development_match<'a>(
    source_commit: [u8; 20],
    build_identity: &str,
    openings: &OpeningSuite,
    policies: (&'a SearchPolicySet, &'a SearchPolicySet),
    weights: &'a EvaluationWeightSet,
    protocol: EngineVariantResourceProtocol,
    protocol_name: &str,
) -> Result<EngineVariantValidationReport, Box<dyn Error>> {
    let (baseline_policy, candidate_policy) = policies;
    let baseline_identity = identity(
'''
if text.count(old) != 1:
    raise SystemExit("expected one S2-6 development helper signature")
text = text.replace(old, new, 1)
text = text.replace(
    '''            &baseline,
            candidate,
            &weights,
''',
    '''            (&baseline, candidate),
            &weights,
''',
)
reference_old = '''        if reference.score() != baseline_reference.score()
            || reference.score() != see_reference.score()
            || reference.score() != delta_reference.score()
'''
reference_new = '''        if Some(reference.score()) != baseline_reference.score()
            || Some(reference.score()) != see_reference.score()
            || Some(reference.score()) != delta_reference.score()
'''
if text.count(reference_old) != 1:
    raise SystemExit("expected one S2-6 bounded-reference comparison")
text = text.replace(reference_old, reference_new, 1)
if text.count("#[allow(") or text.count("#[expect("):
    raise SystemExit("S2-6 evidence payload retains lint suppression")
path.write_text(text)
print("S2-6 evidence helper and reference comparison refined")
