from pathlib import Path

source = Path('crates/chess-tools/src/candidate_validation.rs')
text = source.read_text()
old = '''    if openings.lines().is_empty() {
        return Err(ToolError::new(
            "candidate validation opening suite is empty",
        ));
    }

    let baseline = EvaluationWeightSet::baseline();
'''
new = '''    if openings.lines().is_empty() {
        return Err(ToolError::new(
            "candidate validation opening suite is empty",
        ));
    }
    let required_openings = usize::try_from(config.pair_count)
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
if text.count(old) != 1:
    raise SystemExit('unexpected opening validation block')
text = text.replace(old, new, 1)

test_marker = '''    #[test]
    fn candidate_score_is_color_relative_and_unfinished_is_separate() {
'''
test_insert = '''    #[test]
    fn every_independent_pair_requires_a_distinct_opening() {
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
            &openings(),
            &artifact(),
            1,
            1,
        )
        .expect_err("one opening cannot support two independent pairs");
        assert!(error.to_string().contains("distinct opening per pair"));
    }

'''
if text.count(test_marker) != 1:
    raise SystemExit('unexpected candidate-score test marker')
text = text.replace(test_marker, test_insert + test_marker, 1)

old_tail = '''        assert!(first
            .serialize()
            .expect("serialize")
            .contains("activated=false"));
    }
}
'''
new_tail = '''        let serialized = first.serialize().expect("serialize");
        assert!(serialized.contains("activated=false"));

        let destination = std::env::temp_dir().join(format!(
            "chess-candidate-validation-{}-{:016x}.txt",
            std::process::id(),
            first.checksum
        ));
        let temporary = destination.with_extension("tmp");
        let _ = std::fs::remove_file(&destination);
        let _ = std::fs::remove_file(&temporary);
        write_candidate_validation_report_atomic(&destination, &temporary, &first)
            .expect("atomic report write");
        assert_eq!(
            std::fs::read_to_string(&destination).expect("read report"),
            serialized
        );
        assert!(!temporary.exists());
        std::fs::remove_file(destination).expect("remove report");
    }
}
'''
if text.count(old_tail) != 1:
    raise SystemExit('unexpected candidate test tail')
source.write_text(text.replace(old_tail, new_tail, 1))


doc = Path('docs/RUST_CANDIDATE_VALIDATION.md')
text = doc.read_text()
old = '''The production minimum is **200 independent opening pairs**, which means **400 games**.

For each pair:
'''
new = '''The production minimum is **200 independent opening pairs**, which means **400 games**. The fixed suite must contain at least 200 distinct opening lines; production validation rejects any configuration that would reuse an opening as a second independent pair.

For each pair:
'''
if text.count(old) != 1:
    raise SystemExit('unexpected documentation sample-size paragraph')
doc.write_text(text.replace(old, new, 1))
