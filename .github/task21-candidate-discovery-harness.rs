

    fn discovery_artifact(identifier: u64, weights: EvaluationWeights) -> NamedWeightArtifact {
        NamedWeightArtifact::new(
            identifier,
            TrainingMetadata::new(
                TrainingRunProvenance::new(20260804, [0x27; 20], 8, 4, 1),
                TrainingDatasetProvenance::new(1, 64, 8, 8),
            ),
            weights,
        )
        .expect("discovery candidate artifact")
    }

    fn discovery_openings(count: usize) -> OpeningSuite {
        let starting = Game::starting();
        let mut starting_position = starting.position().clone();
        let white_moves = starting_position.legal_moves().expect("starting legal moves");
        let mut text = String::from("CHESS_SELF_PLAY_OPENINGS\t1\n");
        let mut current_count = 0_usize;
        for white in white_moves.iter() {
            let mut after_white = starting.clone();
            after_white.make_move(white).expect("legal White move");
            let mut black_position = after_white.position().clone();
            let black_moves = black_position.legal_moves().expect("Black replies");
            for black in black_moves.iter() {
                writeln!(
                    text,
                    "discovery-{current_count:03}\t{STARTING_FEN}\t{} {}",
                    white.to_uci(),
                    black.to_uci(),
                )
                .expect("opening text");
                current_count += 1;
                if current_count == count {
                    return OpeningSuite::from_text(&text).expect("discovery openings");
                }
            }
        }
        panic!("insufficient distinct openings")
    }

    #[test]
    #[ignore = "bounded Task 21 candidate discovery"]
    fn task21_candidate_discovery() {
        use chess_search::PhasedWeight;

        let mut mobility = EvaluationWeights::DEFAULT;
        mobility.mobility[1] = PhasedWeight::new(6, 5);
        mobility.mobility[2] = PhasedWeight::new(7, 6);
        mobility.mobility[3] = PhasedWeight::new(3, 5);
        mobility.mobility[4] = PhasedWeight::new(2, 3);

        let mut pawns = EvaluationWeights::DEFAULT;
        pawns.isolated_pawn = PhasedWeight::new(-18, -14);
        pawns.doubled_pawn = PhasedWeight::new(-16, -18);
        pawns.passed_pawn = PhasedWeight::new(18, 38);
        pawns.connected_pawn = PhasedWeight::new(8, 15);

        let mut activity = EvaluationWeights::DEFAULT;
        activity.bishop_pair = PhasedWeight::new(38, 50);
        activity.rook_open_file = PhasedWeight::new(24, 14);
        activity.rook_semi_open_file = PhasedWeight::new(14, 8);
        activity.rook_seventh_rank = PhasedWeight::new(28, 38);
        activity.space = PhasedWeight::new(5, 2);
        activity.king_activity = PhasedWeight::new(0, 16);

        let mut combined = EvaluationWeights::DEFAULT;
        combined.mobility = mobility.mobility;
        combined.isolated_pawn = pawns.isolated_pawn;
        combined.doubled_pawn = pawns.doubled_pawn;
        combined.passed_pawn = pawns.passed_pawn;
        combined.connected_pawn = pawns.connected_pawn;
        combined.bishop_pair = activity.bishop_pair;
        combined.rook_open_file = activity.rook_open_file;
        combined.rook_semi_open_file = activity.rook_semi_open_file;
        combined.rook_seventh_rank = activity.rook_seventh_rank;
        combined.space = activity.space;
        combined.king_activity = activity.king_activity;

        let candidates = [
            ("mobility", 0x4431_1000_0000_0001, mobility),
            ("pawns", 0x4431_1000_0000_0002, pawns),
            ("activity", 0x4431_1000_0000_0003, activity),
            ("combined", 0x4431_1000_0000_0004, combined),
        ];
        let openings = discovery_openings(8);
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        for (name, identifier, weights) in candidates {
            let config = CandidateValidationConfig {
                pair_count: 8,
                seed: 0x2721_0000,
                side,
                maximum_plies: 80,
                claimable_draw_policy: ClaimableDrawPolicy::Accept,
                minimum_score_margin: 0.0,
                maximum_unfinished_per_mille: 1_000,
            };
            let provenance = CandidateValidationProvenance::new(
                identifier,
                format!("task-21-quick-{name}"),
                [0x27; 20],
                format!("task21 quick candidate screen {name}"),
            )
            .expect("discovery provenance");
            let report = run_candidate_validation_internal(
                provenance,
                config,
                &openings,
                &discovery_artifact(identifier, weights),
                1,
                1,
            )
            .expect("discovery match");
            println!(
                "task21_quick\tname={name}\twins={}\tdraws={}\tlosses={}\tunfinished={}\tmean={:.9}\tstderr={:.9}\tlower={:.9}\tdecision={}",
                report.candidate_wins,
                report.draws,
                report.candidate_losses,
                report.unfinished,
                report.mean_pair_score,
                report.pair_score_standard_error,
                report.lower_confidence_bound,
                report.decision,
            );
        }
    }
