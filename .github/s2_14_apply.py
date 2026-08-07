from pathlib import Path


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


policy_path = Path("crates/chess-search/src/search_policy.rs")
text = policy_path.read_text()

text = replace_once(
    text,
    "/// Stable identifier for the inactive S2-8 Late Move Reductions candidate.\n"
    "pub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID: u64 = 0x5332_384c_4d52_3031;\n"
    "/// Stable identifier for the inactive S2-9 null-move pruning candidate.",
    "/// Stable identifier for the inactive S2-8 Late Move Reductions candidate.\n"
    "pub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID: u64 = 0x5332_384c_4d52_3031;\n"
    "/// Stable identifier for the frozen inactive S2-14 SEE-ordering plus LMR candidate.\n"
    "pub const S2_14_SEE_LMR_SEARCH_POLICY_ID: u64 = 0x5332_3134_534c_4d31;\n"
    "/// Stable identifier for the inactive S2-9 null-move pruning candidate.",
)

text = replace_once(
    text,
    "    /// Inactive S2-8 Late Move Reductions candidate.\n"
    "    pub const LATE_MOVE_REDUCTIONS: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::LateMoveReductions.bit(),\n"
    "    };\n"
    "    /// Inactive S2-9 conservative null-move pruning candidate.",
    "    /// Inactive S2-8 Late Move Reductions candidate.\n"
    "    pub const LATE_MOVE_REDUCTIONS: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::LateMoveReductions.bit(),\n"
    "    };\n"
    "    /// Frozen inactive S2-14 combination: SEE capture ordering plus verified LMR.\n"
    "    pub const S2_14_SEE_LMR: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit()\n"
    "            | ExperimentalSearchFeature::LateMoveReductions.bit(),\n"
    "    };\n"
    "    /// Inactive S2-9 conservative null-move pruning candidate.",
)

marker = "    /// Inactive S2-9 candidate: baseline semantics plus conservative verified null move.\n"
combo = """    /// Frozen inactive S2-14 candidate: SEE capture ordering plus bounded verified LMR.
    pub const S2_14_SEE_LMR: Self = Self::new(SearchPolicyParameters {
        alpha_beta: AlphaBetaMode::FullWindowFailSoft,
        transposition: TranspositionPolicy::ClusteredFullKey,
        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,
        aspiration_windows: true,
        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,
        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,
        experimental_features: ExperimentalSearchFeatures::S2_14_SEE_LMR,
    });

"""
text = replace_once(text, marker, combo + marker)

text = replace_once(
    text,
    "        if self.late_move_reductions_enabled()\n"
    "            && self.parameters.experimental_features.bits()\n"
    "                != ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS.bits()\n"
    "        {\n"
    "            return Err(SearchPolicyValidationError::LateMoveReductionsMustBeIsolated);\n"
    "        }",
    "        if self.late_move_reductions_enabled() {\n"
    "            let enabled = self.parameters.experimental_features.bits();\n"
    "            if enabled != ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS.bits()\n"
    "                && enabled != ExperimentalSearchFeatures::S2_14_SEE_LMR.bits()\n"
    "            {\n"
    "                return Err(SearchPolicyValidationError::LateMoveReductionsMustBeIsolated);\n"
    "            }\n"
    "        }",
)

factory_marker = "    /// Returns the inactive S2-9 conservative null-move candidate.\n"
factory = """    /// Returns the frozen inactive S2-14 SEE-ordering plus LMR candidate.
    #[must_use]
    pub fn s2_14_see_lmr_candidate() -> Self {
        Self::new(S2_14_SEE_LMR_SEARCH_POLICY_ID, SearchPolicy::S2_14_SEE_LMR)
    }

"""
text = replace_once(text, factory_marker, factory + factory_marker)

text = replace_once(
    text,
    "    /// LMR was combined with another unevaluated experimental feature.\n"
    "    LateMoveReductionsMustBeIsolated,",
    "    /// LMR was combined outside the isolated S2-8 or frozen S2-14 SEE+LMR policies.\n"
    "    LateMoveReductionsMustBeIsolated,",
)
text = replace_once(
    text,
    "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n"
    "                \"late move reductions must be evaluated as an isolated policy candidate\",\n"
    "            ),",
    "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n"
    "                \"late move reductions are valid only as isolated S2-8 or frozen S2-14 SEE+LMR policy\",\n"
    "            ),",
)
text = replace_once(
    text,
    "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n"
    "        NULL_MOVE_PRUNING_SEARCH_POLICY_ID, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,",
    "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n"
    "        NULL_MOVE_PRUNING_SEARCH_POLICY_ID, S2_14_SEE_LMR_SEARCH_POLICY_ID,\n"
    "        SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,",
)

test_marker = "    #[test]\n    fn s2_9_null_move_candidate_is_distinct_valid_and_inactive_by_default() {"
combo_test = """    #[test]
    fn s2_14_see_lmr_candidate_is_exact_distinct_and_inactive_by_default() {
        let baseline = SearchPolicySet::baseline();
        let candidate = SearchPolicySet::s2_14_see_lmr_candidate();
        assert_eq!(candidate.identifier, S2_14_SEE_LMR_SEARCH_POLICY_ID);
        assert_eq!(candidate.validate(), Ok(()));
        assert!(candidate.policy.see_capture_ordering_enabled());
        assert!(candidate.policy.late_move_reductions_enabled());
        assert!(!candidate.policy.principal_variation_search_enabled());
        assert!(!candidate.policy.null_move_pruning_enabled());
        assert_ne!(candidate.identifier, baseline.identifier);
        assert_ne!(candidate.checksum, baseline.checksum);
    }

"""
text = replace_once(text, test_marker, combo_test + test_marker)
policy_path.write_text(text)

# Candidate correctness/performance harness derived mechanically from the validated S2-8 harness.
source = Path("crates/chess-tools/src/bin/s2_8_lmr.rs").read_text()
candidate = source
for old, new in [
    ("s2_8_lmr", "s2_14_candidate"),
    ("S2-8 LMR", "S2-14 SEE+LMR candidate"),
    ("S2-8", "S2-14"),
    ("S2_8", "S2_14"),
    ("s2-8", "s2-14"),
    ("SearchPolicySet::late_move_reductions_candidate()", "SearchPolicySet::s2_14_see_lmr_candidate()"),
    ("0x5332_3842_4153_4531", "0x5332_3134_4241_5345"),
    ("0x5332_3843_414e_4431", "0x5332_3134_4341_4e44"),
    ("0x5332_3844_4556_3031", "0x5332_3134_4445_5631"),
]:
    candidate = candidate.replace(old, new)

candidate = candidate.replace(
    "    if baseline_policy.policy.late_move_reductions_enabled()\n"
    "        || !candidate_policy.policy.late_move_reductions_enabled()\n"
    "    {\n"
    "        return Err(\"S2-14 policy activation boundary is inverted\".into());\n"
    "    }",
    "    if baseline_policy.policy.late_move_reductions_enabled()\n"
    "        || baseline_policy.policy.see_capture_ordering_enabled()\n"
    "        || !candidate_policy.policy.late_move_reductions_enabled()\n"
    "        || !candidate_policy.policy.see_capture_ordering_enabled()\n"
    "        || candidate_policy.policy.principal_variation_search_enabled()\n"
    "        || candidate_policy.policy.null_move_pruning_enabled()\n"
    "    {\n"
    "        return Err(\"S2-14 frozen candidate activation boundary is invalid\".into());\n"
    "    }",
)
Path("crates/chess-tools/src/bin/s2_14_candidate.rs").write_text(candidate)

# Production complete-variant harness derived from the validated S2-13 control harness.
prod = Path("crates/chess-tools/src/bin/s2_13_variant_control.rs").read_text()
for old, new in [
    ("s2_13_variant_control", "s2_14_production"),
    ("S2_13", "S2_14"),
    ("S2-13", "S2-14"),
    ("s2-13", "s2-14"),
    ("CONTROL_MAXIMUM_PLIES: u32 = 4", "CONTROL_MAXIMUM_PLIES: u32 = 256"),
    ("FIXED_NODE_BUDGET: u64 = 8", "FIXED_NODE_BUDGET: u64 = 2_000"),
    ("0x5332_3133_4241_5345", "0x5332_3134_4241_5345"),
    ("0x5332_3133_4341_4e44", "0x5332_3134_4341_4e44"),
    ("pair_count: 200,", "pair_count: 1_000,"),
]:
    prod = prod.replace(old, new)

old_policy = """    let policy = SearchPolicySet::baseline();
    let weights = EvaluationWeightSet::baseline();
    policy.validate()?;
    weights.validate()?;"""
new_policy = """    let policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::s2_14_see_lmr_candidate();
    let weights = EvaluationWeightSet::baseline();
    policy.validate()?;
    candidate_policy.validate()?;
    weights.validate()?;
    if policy.policy.see_capture_ordering_enabled()
        || policy.policy.late_move_reductions_enabled()
        || !candidate_policy.policy.see_capture_ordering_enabled()
        || !candidate_policy.policy.late_move_reductions_enabled()
        || candidate_policy.policy.principal_variation_search_enabled()
        || candidate_policy.policy.null_move_pruning_enabled()
    {
        return Err("S2-14 candidate policy boundary is invalid".into());
    }"""
prod = replace_once(prod, old_policy, new_policy)

old_candidate_identity = """        &policy,
        &weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, &policy, &weights)?;
    let candidate = EngineVariantRuntime::new(&candidate_identity, &policy, &weights)?;"""
new_candidate_identity = """        &candidate_policy,
        &weights,
    )?;
    let baseline = EngineVariantRuntime::new(&baseline_identity, &policy, &weights)?;
    let candidate =
        EngineVariantRuntime::new(&candidate_identity, &candidate_policy, &weights)?;"""
prod = replace_once(prod, old_candidate_identity, new_candidate_identity)

prod = replace_once(
    prod,
    ".with_maximum_unfinished_per_mille(1_000)?\n    .with_claimable_draw_policy(ClaimableDrawPolicy::Continue);",
    ".with_maximum_unfinished_per_mille(if plan.tier == EngineVariantValidationTier::Production { 50 } else { 1_000 })?\n"
    "    .with_claimable_draw_policy(ClaimableDrawPolicy::Accept);",
)

manifest_write = """    write_new(
        &output_directory.join("s2-14-control-manifest.tsv"),
        manifest.as_bytes(),
    )?;"""
manifest_write_new = """    let manifest = format!(
        "{manifest}candidate_policy_identifier\\t{:016x}\\ncandidate_policy_checksum\\t{:016x}\\nopening_provenance\\tfirst_party_deterministic_generator_v1\\nopening_license\\tMIT\\n",
        candidate_policy.identifier, candidate_policy.checksum
    );
    write_new(
        &output_directory.join("s2-14-control-manifest.tsv"),
        manifest.as_bytes(),
    )?;"""
prod = replace_once(prod, manifest_write, manifest_write_new)

start = prod.index("fn control_openings() -> Result<String, Box<dyn Error>> {")
end = prod.index("\nfn validate_control_report", start)
opening_fn = r'''fn control_openings() -> Result<String, Box<dyn Error>> {
    const OPENING_COUNT: usize = 1_200;
    const MAXIMUM_ATTEMPTS: usize = 100_000;
    let mut output = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
    let mut seen = std::collections::BTreeSet::new();
    let mut accepted = 0_usize;

    for attempt in 0..MAXIMUM_ATTEMPTS {
        if accepted == OPENING_COUNT {
            break;
        }
        let target_plies = 6 + ((attempt + accepted * 7) % 15);
        let mut game = Game::new(Position::starting());
        let mut moves = Vec::with_capacity(target_plies);
        let mut state = splitmix64(0x5332_3134_4f50_4e31_u64 ^ attempt as u64);
        let mut complete = true;

        for ply in 0..target_plies {
            let mut legal = game.legal_moves()?.iter().collect::<Vec<_>>();
            if legal.is_empty() {
                complete = false;
                break;
            }
            legal.sort_by_key(|current| current.to_uci());
            state = splitmix64(state ^ (ply as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15));
            let selected = legal[(state as usize) % legal.len()];
            game.make_move(selected)?;
            moves.push(selected.to_uci());
        }
        if !complete {
            continue;
        }
        let normalized = moves.join(" ");
        if !seen.insert(normalized.clone()) {
            continue;
        }
        writeln!(
            output,
            "production-{accepted:04}\t{STARTING_FEN}\t{normalized}"
        )?;
        accepted += 1;
    }

    if accepted != OPENING_COUNT {
        return Err(format!(
            "expected {OPENING_COUNT} deterministic production openings, found {accepted}"
        )
        .into());
    }
    Ok(output)
}

const fn splitmix64(mut value: u64) -> u64 {
    value = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    value ^ (value >> 31)
}
'''
prod = prod[:start] + opening_fn + prod[end:]
prod = prod.replace(
    "assert_eq!(text.lines().skip(1).count(), 200);",
    "assert_eq!(text.lines().skip(1).count(), 1_200);",
)
Path("crates/chess-tools/src/bin/s2_14_production.rs").write_text(prod)

audit = r'''#!/usr/bin/env bash
set -euo pipefail

policy='crates/chess-search/src/search_policy.rs'
candidate='crates/chess-tools/src/bin/s2_14_candidate.rs'
production='crates/chess-tools/src/bin/s2_14_production.rs'

grep -Fq 'S2_14_SEE_LMR_SEARCH_POLICY_ID' "$policy"
grep -Fq 'pub fn s2_14_see_lmr_candidate()' "$policy"
grep -Fq 'ExperimentalSearchFeatures::S2_14_SEE_LMR' "$policy"
grep -Fq 'candidate_policy = SearchPolicySet::s2_14_see_lmr_candidate()' "$production"
grep -Fq 'pair_count: 1_000' "$production"
grep -Fq 'const OPENING_COUNT: usize = 1_200' "$production"
grep -Fq 'opening_provenance\tfirst_party_deterministic_generator_v1' "$production"
grep -Fq 'opening_license\tMIT' "$production"

python3 - <<'PY2'
from pathlib import Path
text = Path('crates/chess-search/src/search_policy.rs').read_text()
start = text.index('/// Frozen inactive S2-14 candidate: SEE capture ordering plus bounded verified LMR.')
end = text.index('/// Inactive S2-9 candidate:', start)
block = text[start:end]
for forbidden in ('PRINCIPAL_VARIATION_SEARCH', 'NULL_MOVE_PRUNING', 'SEE_QUIESCENCE_PRUNING', 'DELTA_PRUNING'):
    if forbidden in block:
        raise SystemExit(f'forbidden S2-14 feature in frozen policy: {forbidden}')
PY2

! grep -R -E 'S2_14_SEE_LMR|s2_14_see_lmr' crates/chess-uci crates/chess-ffi android 2>/dev/null

echo 'S2-14 candidate audit passed'
'''
audit_path = Path("scripts/task_s2_14_candidate_audit.sh")
audit_path.write_text(audit)
audit_path.chmod(0o755)
