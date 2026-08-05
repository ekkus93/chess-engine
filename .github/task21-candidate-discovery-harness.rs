

    fn discovery_artifact(identifier: u64, weights: EvaluationWeights) -> NamedWeightArtifact {
        NamedWeightArtifact::new(
            identifier,
            TrainingMetadata::new(
                TrainingRunProvenance::new(20260804, [0x27; 20], 32, 8, 1),
                TrainingDatasetProvenance::new(1, 256, 32, 32),
            ),
            weights,
        )
        .expect("discovery candidate artifact")
    }

    fn discovery_openings(count: usize) -> OpeningSuite {
        let starting = Game::starting();
        let mut starting_position = starting.position().clone();
        let white_moves = starting_position
            .legal_moves()
            .expect("starting legal moves");
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

        let mut candidates = Vec::new();

        let mut material = EvaluationWeights::DEFAULT;
        material.material[1] = PhasedWeight::new(305, 300);
        material.material[2] = PhasedWeight::new(345, 330);
        material.material[3] = PhasedWeight::new(520, 540);
        material.material[4] = PhasedWeight::new(940, 940);
        candidates.push(("material", 0x4431_0000_0000_0001, material));

        let mut mobility = EvaluationWeights::DEFAULT;
        mobility.mobility[1] = PhasedWeight::new(6, 5);
        mobility.mobility[2] = PhasedWeight::new(7, 6);
        mobility.mobility[3] = PhasedWeight::new(3, 5);
        mobility.mobility[4] = PhasedWeight::new(2, 3);
        candidates.push(("mobility", 0x4431_0000_0000_0002, mobility));

        let mut pawns = EvaluationWeights::DEFAULT;
        pawns.isolated_pawn = PhasedWeight::new(-18, -14);
        pawns.doubled_pawn = PhasedWeight::new(-16, -18);
        pawns.passed_pawn = PhasedWeight::new(18, 38);
        pawns.connected_pawn = PhasedWeight::new(8, 15);
        candidates.push(("pawns", 0x4431_0000_0000_0003, pawns));

        let mut activity = EvaluationWeights::DEFAULT;
        activity.bishop_pair = PhasedWeight::new(38, 50);
        activity.rook_open_file = PhasedWeight::new(24, 14);
        activity.rook_semi_open_file = PhasedWeight::new(14, 8);
        activity.rook_seventh_rank = PhasedWeight::new(28, 38);
        activity.space = PhasedWeight::new(5, 2);
        activity.king_activity = PhasedWeight::new(0, 16);
        candidates.push(("activity", 0x4431_0000_0000_0004, activity));

        let mut safety = EvaluationWeights::DEFAULT;
        safety.king_shield = PhasedWeight::new(18, 3);
        safety.king_zone_attack = PhasedWeight::new(-12, -3);
        candidates.push(("safety", 0x4431_0000_0000_0005, safety));

        let mut combined = material;
        combined.mobility = mobility.mobility;
        combined.isolated_pawn = pawns.isolated_pawn;
        combined.doubled_pawn = pawns.doubled_pawn;
        combined.passed_pawn = pawns.passed_pawn;
        combined.connected_pawn = pawns.connected_pawn;
        combined.bishop_pair = activity.bishop_pair;
        combined.rook_open_file = activity.rook_open_file;
        combined.rook_semi_open_file = activity.rook_semi_open_file;
        combined.rook_seventh_rank = activity.rook_seventh_rank;
        combined.king_shield = safety.king_shield;
        combined.king_zone_attack = safety.king_zone_attack;
        combined.space = activity.space;
        combined.king_activity = activity.king_activity;
        candidates.push(("combined", 0x4431_0000_0000_0006, combined));

        let openings = discovery_openings(32);
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        for (name, identifier, weights) in candidates {
            let config = CandidateValidationConfig {
                pair_count: 32,
                seed: 0x2721_0000 ^ identifier,
                side,
                maximum_plies: 160,
                claimable_draw_policy: ClaimableDrawPolicy::Accept,
                minimum_score_margin: 0.0,
                maximum_unfinished_per_mille: 1_000,
            };
            let provenance = CandidateValidationProvenance::new(
                identifier,
                format!("task-21-discovery-{name}"),
                [0x27; 20],
                format!("task21 candidate discovery {name}"),
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
                "task21_discovery\tname={name}\twins={}\tdraws={}\tlosses={}\tunfinished={}\tmean={:.9}\tstderr={:.9}\tlower={:.9}\tdecision={}",
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
