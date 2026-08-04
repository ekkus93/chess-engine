from pathlib import Path

path = Path('crates/chess-tools/src/candidate_validation.rs')
text = path.read_text()
old_import = '''    use chess_search::EvaluationWeights;

    use crate::self_play::SelfPlayLimit;
'''
new_import = '''    use chess_core::Game;
    use chess_search::EvaluationWeights;

    use crate::{self_play::SelfPlayLimit, STARTING_FEN};
'''
if text.count(old_import) != 1:
    raise SystemExit('unexpected candidate test imports')
text = text.replace(old_import, new_import, 1)

marker = '''    #[test]
    fn production_configuration_enforces_four_hundred_games() {
'''
insert = '''    fn production_openings() -> OpeningSuite {
        let starting = Game::starting();
        let mut starting_position = starting.position().clone();
        let white_moves = starting_position
            .legal_moves()
            .expect("starting legal moves");
        let mut text = String::from("CHESS_SELF_PLAY_OPENINGS\\t1\\n");
        let mut count = 0_usize;
        for white in white_moves.iter() {
            let mut after_white = starting.clone();
            after_white
                .make_move(white)
                .expect("generated White move is legal");
            let mut black_position = after_white.position().clone();
            let black_moves = black_position
                .legal_moves()
                .expect("Black legal replies");
            for black in black_moves.iter() {
                writeln!(
                    text,
                    "control-{count:03}\\t{STARTING_FEN}\\t{} {}",
                    white.to_uci(),
                    black.to_uci()
                )
                .expect("writing opening text cannot fail");
                count += 1;
                if count == MINIMUM_VALIDATION_PAIRS as usize {
                    return OpeningSuite::from_text(&text)
                        .expect("generated production opening suite");
                }
            }
        }
        panic!("starting two-ply tree did not contain 200 openings");
    }

    #[test]
    #[ignore = "production 200-pair control match"]
    fn production_control_match_runs_four_hundred_games() {
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let config = CandidateValidationConfig::new(MINIMUM_VALIDATION_PAIRS, 0x2150_400, side)
            .expect("production config")
            .with_maximum_plies(4)
            .expect("short control games")
            .with_maximum_unfinished_per_mille(1_000)
            .expect("control unfinished ceiling");
        let provenance = CandidateValidationProvenance::new(
            0x5441_534b_3231_3501,
            "task-21.5-production-control".to_owned(),
            [0x21; 20],
            "cargo test -p chess-tools production_control_match_runs_four_hundred_games -- --ignored --nocapture".to_owned(),
        )
        .expect("control provenance");
        let report = run_candidate_validation(
            provenance,
            config,
            &production_openings(),
            &artifact(),
        )
        .expect("production control match");

        assert_eq!(report.games.len(), 400);
        assert_eq!(report.opening_count, 200);
        assert_eq!(report.mean_pair_score, 0.5);
        assert_eq!(report.pair_score_standard_error, 0.0);
        assert_eq!(report.lower_confidence_bound, 0.5);
        assert_eq!(report.decision, CandidateValidationDecision::RejectedStrength);
        assert!(!report.activated());
        assert_eq!(report.checksum, report.computed_checksum());
        println!(
            "task21_5_control\\tpairs={}\\tgames={}\\twins={}\\tdraws={}\\tlosses={}\\tunfinished={}\\tmean={:.17e}\\tstderr={:.17e}\\tlower={:.17e}\\tdecision={}\\tactivated={}\\tchecksum={:016x}",
            report.config.pair_count(),
            report.games.len(),
            report.candidate_wins,
            report.draws,
            report.candidate_losses,
            report.unfinished,
            report.mean_pair_score,
            report.pair_score_standard_error,
            report.lower_confidence_bound,
            report.decision,
            report.activated(),
            report.checksum,
        );
    }

'''
if text.count(marker) != 1:
    raise SystemExit('unexpected production configuration test marker')
path.write_text(text.replace(marker, insert + marker, 1))
