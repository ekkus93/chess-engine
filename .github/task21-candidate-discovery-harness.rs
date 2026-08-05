

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
    #[ignore = "fast Task 21 outcome-only candidate screen"]
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
            ("mobility", mobility),
            ("pawns", pawns),
            ("activity", activity),
            ("combined", combined),
        ];
        let openings = discovery_openings(8);
        let side = SelfPlaySideConfig::new(1, SelfPlayLimit::Depth(1));
        let game_config = WeightedValidationGameConfig::new(
            side,
            side,
            80,
            ClaimableDrawPolicy::Accept,
        )
        .expect("screen game config");

        for (name, weights) in candidates {
            let mut wins = 0_u32;
            let mut draws = 0_u32;
            let mut losses = 0_u32;
            let mut unfinished = 0_u32;
            let mut pair_scores = Vec::new();
            for opening in openings.lines() {
                let candidate_white = run_weighted_validation_game(
                    opening,
                    game_config,
                    &weights,
                    &EvaluationWeights::DEFAULT,
                )
                .expect("candidate-white game");
                let candidate_black = run_weighted_validation_game(
                    opening,
                    game_config,
                    &EvaluationWeights::DEFAULT,
                    &weights,
                )
                .expect("candidate-black game");
                let white_score = candidate_score(candidate_white.result(), CandidateColor::White);
                let black_score = candidate_score(candidate_black.result(), CandidateColor::Black);
                pair_scores.push((white_score + black_score) * 0.5);
                for (result, color) in [
                    (candidate_white.result(), CandidateColor::White),
                    (candidate_black.result(), CandidateColor::Black),
                ] {
                    match result {
                        SelfPlayResult::Draw => draws += 1,
                        SelfPlayResult::Unfinished => unfinished += 1,
                        SelfPlayResult::WhiteWin if color == CandidateColor::White => wins += 1,
                        SelfPlayResult::BlackWin if color == CandidateColor::Black => wins += 1,
                        SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => losses += 1,
                    }
                }
            }
            let (mean, stderr, lower) = summarize_pair_scores(&pair_scores).expect("screen stats");
            println!(
                "task21_fast\tname={name}\twins={wins}\tdraws={draws}\tlosses={losses}\tunfinished={unfinished}\tmean={mean:.9}\tstderr={stderr:.9}\tlower={lower:.9}",
            );
        }
    }
