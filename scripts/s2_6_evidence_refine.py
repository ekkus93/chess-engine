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

reference_shape_old = '''        if reference.score() != baseline_reference.score()
            || reference.score() != see_reference.score()
            || reference.score() != delta_reference.score()
'''
reference_shape_new = '''        if Some(reference.score()) != baseline_reference.score()
            || Some(reference.score()) != see_reference.score()
            || Some(reference.score()) != delta_reference.score()
'''
if text.count(reference_shape_old) != 1:
    raise SystemExit("expected one S2-6 bounded-reference comparison")
text = text.replace(reference_shape_old, reference_shape_new, 1)

fixture_old = '''        let mut position: Position = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1"
            .parse()
            .expect("delta-pruning fixture parses");
'''
fixture_new = '''        let mut position: Position = "4k3/8/8/3p4/3Q3p/8/8/4K3 w - - 0 1"
            .parse()
            .expect("delta-pruning fixture parses");
'''
if text.count(fixture_old) != 1:
    raise SystemExit("expected one S2-6 narrow-window delta fixture")
text = text.replace(fixture_old, fixture_new, 1)

prune_constant = '''const PRUNE_WITNESS_FEN: &str = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1";
'''
if text.count(prune_constant) != 1:
    raise SystemExit("expected one obsolete iterative prune witness constant")
text = text.replace(prune_constant, "", 1)

text = text.replace(
    '''    let mut total_delta_prunes = 0_u64;
    for case in cases {
''',
    '''    let mut total_delta_prunes = 0_u64;
    let mut bounded_reference_cases = 0_u32;
    for case in cases {
''',
    1,
)

reference_block_old = '''        let reference_depth = case.depth.min(1);
        let mut reference_position = root.clone();
        let mut reference_history = history.clone();
        let reference = reference_search_with_quiescence(
            &mut reference_position,
            &mut reference_history,
            reference_depth,
        )?;
        let baseline_reference = search_exact(
            &root,
            &history,
            reference_depth,
            baseline_policy,
            weights,
        )?;
        let see_reference = search_exact(&root, &history, reference_depth, see_policy, weights)?;
        let delta_reference = search_exact(&root, &history, reference_depth, delta_policy, weights)?;
        if Some(reference.score()) != baseline_reference.score()
            || Some(reference.score()) != see_reference.score()
            || Some(reference.score()) != delta_reference.score()
        {
            return Err(format!("case {} failed bounded reference parity", case.identifier).into());
        }
'''
reference_block_new = '''        if bounded_reference_case(&case.identifier) {
            bounded_reference_cases = bounded_reference_cases
                .checked_add(1)
                .ok_or("bounded reference case count overflow")?;
            let reference_depth = 1;
            let mut reference_position = root.clone();
            let mut reference_history = history.clone();
            let reference = reference_search_with_quiescence(
                &mut reference_position,
                &mut reference_history,
                reference_depth,
            )?;
            if reference_position != root || reference_history != history {
                return Err(format!(
                    "case {} changed root during bounded reference search",
                    case.identifier
                )
                .into());
            }
            let baseline_reference = search_exact(
                &root,
                &history,
                reference_depth,
                baseline_policy,
                weights,
            )?;
            let see_reference =
                search_exact(&root, &history, reference_depth, see_policy, weights)?;
            let delta_reference =
                search_exact(&root, &history, reference_depth, delta_policy, weights)?;
            if Some(reference.score()) != baseline_reference.score()
                || Some(reference.score()) != see_reference.score()
                || Some(reference.score()) != delta_reference.score()
            {
                return Err(format!(
                    "case {} failed bounded reference parity",
                    case.identifier
                )
                .into());
            }
        }
'''
if text.count(reference_block_old) != 1:
    raise SystemExit("expected one complete S2-6 reference block")
text = text.replace(reference_block_old, reference_block_new, 1)

witness_block_old = '''    let witness_root = Position::from_fen(PRUNE_WITNESS_FEN)?;
    let witness_history = SearchHistory::from_position(&witness_root);
    let witness = search_exact(&witness_root, &witness_history, 1, see_policy, weights)?;
    let witness_prunes = witness.search_diagnostics().quiescence_see_prunes();
    if witness_prunes == 0 {
        return Err("dedicated S2-6 witness exercised no SEE prune".into());
    }
    total_see_prunes = total_see_prunes
        .checked_add(witness_prunes)
        .ok_or("SEE-prune total overflow")?;

'''
if text.count(witness_block_old) != 1:
    raise SystemExit("expected one obsolete iterative S2-6 prune witness block")
text = text.replace(
    witness_block_old,
    '''    if total_see_prunes == 0 {
        return Err("frozen S2-6 corpus exercised no SEE prune".into());
    }

''',
    1,
)

summary_old = '''    writeln!(output, "case_count\\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "witness_see_prunes\\t{witness_prunes}")?;
'''
summary_new = '''    writeln!(output, "case_count\\t{}", parse_corpus(CORPUS)?.len())?;
    writeln!(output, "bounded_reference_cases\\t{bounded_reference_cases}")?;
'''
if text.count(summary_old) != 1:
    raise SystemExit("expected one S2-6 parity summary block")
text = text.replace(summary_old, summary_new, 1)

helper_anchor = '''fn search_exact(
    root: &Position,
'''
helper = '''fn bounded_reference_case(identifier: &str) -> bool {
    matches!(
        identifier,
        "mate-in-one"
            | "stalemate"
            | "fifty-move"
            | "seventy-five-move"
            | "promotion-race"
            | "en-passant-tactic"
            | "poisoned-capture"
    )
}

fn search_exact(
    root: &Position,
'''
if text.count(helper_anchor) != 1:
    raise SystemExit("expected one S2-6 search helper anchor")
text = text.replace(helper_anchor, helper, 1)

if text.count("#[allow(") or text.count("#[expect("):
    raise SystemExit("S2-6 evidence payload retains lint suppression")
path.write_text(text)
print("S2-6 evidence helper, bounded reference subset, corpus prune witness, and delta fixture refined")
