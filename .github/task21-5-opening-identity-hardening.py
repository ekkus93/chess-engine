from pathlib import Path

source = Path('crates/chess-tools/src/candidate_validation.rs')
text = source.read_text()
old_import = '''use std::{
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write as _,
    path::Path,
};
'''
new_import = '''use std::{
    collections::HashSet,
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write as _,
    path::Path,
};
'''
if text.count(old_import) != 1:
    raise SystemExit('unexpected std import block')
text = text.replace(old_import, new_import, 1)

old_validation = '''    let required_openings = usize::try_from(config.pair_count)
        .map_err(|_| ToolError::new("candidate pair count exceeds usize"))?;
    if openings.lines().len() < required_openings {
        return Err(ToolError::new(format!(
            "candidate validation requires at least one distinct opening per pair: {} pairs but only {} openings",
            config.pair_count,
            openings.lines().len()
        )));
    }

    let baseline = EvaluationWeightSet::baseline();
'''
new_validation = '''    let required_openings = usize::try_from(config.pair_count)
        .map_err(|_| ToolError::new("candidate pair count exceeds usize"))?;
    if openings.lines().len() < required_openings {
        return Err(ToolError::new(format!(
            "candidate validation requires at least one distinct opening per pair: {} pairs but only {} openings",
            config.pair_count,
            openings.lines().len()
        )));
    }
    let mut semantic_openings = HashSet::with_capacity(openings.lines().len());
    for opening in openings.lines() {
        let key = (
            opening.initial_fen().to_owned(),
            opening.moves().to_vec(),
        );
        if !semantic_openings.insert(key) {
            return Err(ToolError::new(
                "candidate validation opening suite contains duplicate semantic openings",
            ));
        }
    }

    let baseline = EvaluationWeightSet::baseline();
'''
if text.count(old_validation) != 1:
    raise SystemExit('unexpected distinct-opening validation block')
text = text.replace(old_validation, new_validation, 1)

marker = '''    #[test]
    fn candidate_score_is_color_relative_and_unfinished_is_separate() {
'''
insert = '''    #[test]
    fn differently_named_duplicate_openings_are_rejected() {
        let duplicate_openings = OpeningSuite::from_text(concat!(
            "CHESS_SELF_PLAY_OPENINGS\\t1\\n",
            "first\\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\\te2e4 e7e5\\n",
            "second\\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\\te2e4 e7e5\\n",
        ))
        .expect("syntactically valid duplicate opening suite");
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = CandidateValidationConfig {
            pair_count: 2,
            seed: 42,
            side,
            maximum_plies: 6,
            claimable_draw_policy: ClaimableDrawPolicy::Accept,
            minimum_score_margin: 0.0,
            maximum_unfinished_per_mille: 1_000,
        };
        let provenance = CandidateValidationProvenance::new(
            1,
            "test".to_owned(),
            [1; 20],
            "candidate-test".to_owned(),
        )
        .expect("provenance");
        let error = run_candidate_validation_internal(
            provenance,
            config,
            &duplicate_openings,
            &artifact(),
            1,
            1,
        )
        .expect_err("semantic duplicates must fail");
        assert!(error.to_string().contains("duplicate semantic openings"));
    }

'''
if text.count(marker) != 1:
    raise SystemExit('unexpected candidate score test marker')
source.write_text(text.replace(marker, insert + marker, 1))


doc = Path('docs/RUST_CANDIDATE_VALIDATION.md')
text = doc.read_text()
old = '''The production minimum is **200 independent opening pairs**, which means **400 games**. The fixed suite must contain at least 200 distinct opening lines; production validation rejects any configuration that would reuse an opening as a second independent pair.
'''
new = '''The production minimum is **200 independent opening pairs**, which means **400 games**. The fixed suite must contain at least 200 semantically distinct opening lines. Production validation rejects both an undersized suite and differently named rows that resolve to the same canonical initial FEN and opening-move sequence, so an opening cannot be reused as a second independent pair.
'''
if text.count(old) != 1:
    raise SystemExit('unexpected distinct-opening documentation paragraph')
doc.write_text(text.replace(old, new, 1))
