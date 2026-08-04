use chess_tools::self_play::{
    generate_self_play_dataset, ClaimableDrawPolicy, DatasetSplit, DatasetSplitPercentages,
    OpeningPositionPolicy, OpeningSuite, PositionFilterReason, SelfPlayConfig, SelfPlayDataset,
    SelfPlayFileConfig, SelfPlayLimit, SelfPlayResult, SelfPlaySideConfig, SelfPlayTermination,
    SELF_PLAY_DATASET_SCHEMA_VERSION, SELF_PLAY_ENGINE_VERSION,
};
use chess_tools::STARTING_FEN;

const MATE_FEN: &str = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1";

fn side(limit: SelfPlayLimit) -> SelfPlaySideConfig {
    SelfPlaySideConfig::new(1, limit)
}

fn mate_openings() -> OpeningSuite {
    OpeningSuite::from_text(&format!(
        "CHESS_SELF_PLAY_OPENINGS\t1\nmate-a\t{MATE_FEN}\t-\nmate-b\t{MATE_FEN}\t-\n"
    ))
    .expect("mate opening suite is valid")
}

fn starting_opening() -> OpeningSuite {
    OpeningSuite::from_text(&format!(
        "CHESS_SELF_PLAY_OPENINGS\t1\nstart\t{STARTING_FEN}\t-\n"
    ))
    .expect("starting opening suite is valid")
}

#[test]
fn seeded_small_run_is_stable_deduplicated_versioned_and_replayable() {
    let config = SelfPlayConfig::new(
        4,
        0,
        side(SelfPlayLimit::Depth(1)),
        side(SelfPlayLimit::Depth(1)),
    )
    .with_maximum_plies(4)
    .with_claimable_draw_policy(ClaimableDrawPolicy::Accept)
    .with_opening_position_policy(OpeningPositionPolicy::Exclude)
    .with_splits(DatasetSplitPercentages::new(80, 10, 10).expect("split is valid"));
    let openings = mate_openings();

    let first = generate_self_play_dataset(&config, &openings, "task20.tsv")
        .expect("first deterministic run succeeds");
    let second = generate_self_play_dataset(&config, &openings, "task20.tsv")
        .expect("second deterministic run succeeds");
    assert_eq!(first, second);
    assert_eq!(first.games().len(), 4);
    assert!(first.games().iter().all(|game| {
        game.split() == DatasetSplit::Train
            && game.result() == SelfPlayResult::WhiteWin
            && game.termination() == SelfPlayTermination::Checkmate(chess_core::Color::White)
            && game.white().engine_version() == SELF_PLAY_ENGINE_VERSION
            && game.black().engine_version() == SELF_PLAY_ENGINE_VERSION
            && game.white().config() == config.white()
            && game.black().config() == config.black()
            && game.replay_command().contains("self-play-replay task20.tsv")
    }));

    assert_eq!(first.positions().len(), 1);
    let position = &first.positions()[0];
    assert_eq!(position.split(), DatasetSplit::Train);
    assert_eq!(position.filter_reason(), PositionFilterReason::Eligible);
    assert!(position.eligible());
    assert!(!position.opening_position());
    assert_eq!(position.occurrences(), 4);

    let text = first.to_text();
    assert!(text.starts_with(&format!(
        "CHESS_SELF_PLAY_DATASET\t{SELF_PLAY_DATASET_SCHEMA_VERSION}\n"
    )));
    let parsed = SelfPlayDataset::from_text(&text).expect("dataset round-trip validates");
    assert_eq!(parsed, first);
    for game in parsed.games() {
        let replay = parsed
            .replay_game(game.game_id())
            .expect("recorded game replays");
        assert_eq!(replay.final_fen(), game.final_fen());
        assert_eq!(replay.result(), game.result());
        assert_eq!(replay.termination(), game.termination());
        assert_eq!(
            replay.plies(),
            u32::try_from(game.moves().len()).expect("test move count fits u32")
        );
    }
}

#[test]
fn maximum_ply_games_remain_unfinished_and_positions_are_filtered_explicitly() {
    let config = SelfPlayConfig::new(
        1,
        9,
        side(SelfPlayLimit::Depth(1)),
        side(SelfPlayLimit::Nodes(32)),
    )
    .with_maximum_plies(1)
    .with_opening_position_policy(OpeningPositionPolicy::Mark);
    let dataset = generate_self_play_dataset(&config, &starting_opening(), "maximum.tsv")
        .expect("bounded run succeeds");

    let game = &dataset.games()[0];
    assert_eq!(game.result(), SelfPlayResult::Unfinished);
    assert_eq!(game.termination(), SelfPlayTermination::MaximumPly(1));
    assert_eq!(game.moves().len(), 1);
    assert_eq!(dataset.positions().len(), 2);
    assert!(dataset.positions().iter().all(|position| !position.eligible()));
    assert_eq!(
        dataset.positions()[0].filter_reason(),
        PositionFilterReason::Opening
    );
    assert_eq!(
        dataset.positions()[1].filter_reason(),
        PositionFilterReason::UnfinishedMaximumPly
    );
    assert_eq!(dataset.positions()[1].outcome(), SelfPlayResult::Unfinished);
    dataset
        .replay_game(game.game_id())
        .expect("unfinished game replay validates");
}

#[test]
fn strict_file_configuration_supports_independent_node_and_time_limits() {
    let text = "\
schema=1\n\
games=3\n\
seed=42\n\
maximum_plies=80\n\
white_limit=nodes:1000\n\
white_tt_mib=2\n\
white_check_extension=true\n\
black_limit=time_ms:25\n\
black_tt_mib=3\n\
black_check_extension=false\n\
claimable_draw=continue\n\
opening_positions=mark\n\
split_train=70\n\
split_validation=20\n\
split_test=10\n\
opening_path=fixtures/task20-openings.tsv\n";
    let parsed = SelfPlayFileConfig::from_text(text).expect("config parses");
    assert_eq!(parsed.config().game_count(), 3);
    assert_eq!(parsed.config().seed(), 42);
    assert_eq!(parsed.config().maximum_plies(), 80);
    assert_eq!(parsed.config().white().limit(), SelfPlayLimit::Nodes(1000));
    assert_eq!(
        parsed.config().black().limit(),
        SelfPlayLimit::TimeMilliseconds(25)
    );
    assert!(parsed.config().white().check_extension_enabled());
    assert!(!parsed.config().black().check_extension_enabled());
    assert_eq!(
        parsed.config().claimable_draw_policy(),
        ClaimableDrawPolicy::Continue
    );
    assert_eq!(
        parsed.config().opening_position_policy(),
        OpeningPositionPolicy::Mark
    );
    assert_eq!(parsed.opening_path(), "fixtures/task20-openings.tsv");
    assert_eq!(
        "depth:2".parse::<SelfPlayLimit>(),
        Ok(SelfPlayLimit::Depth(2))
    );
}

#[test]
fn dataset_parser_rejects_zero_position_output() {
    let config = SelfPlayConfig::new(
        1,
        11,
        side(SelfPlayLimit::Depth(1)),
        side(SelfPlayLimit::Depth(1)),
    )
    .with_maximum_plies(1)
    .with_opening_position_policy(OpeningPositionPolicy::Mark);
    let dataset = generate_self_play_dataset(&config, &starting_opening(), "nonempty.tsv")
        .expect("source dataset succeeds");
    let mut lines = dataset
        .to_text()
        .lines()
        .map(str::to_owned)
        .collect::<Vec<_>>();
    let mut config_fields = lines[1].split('\t').map(str::to_owned).collect::<Vec<_>>();
    config_fields[17] = "0".to_owned();
    lines[1] = config_fields.join("\t");
    lines.retain(|line| !line.starts_with("POSITION\t"));
    let empty = lines.join("\n");
    let error = SelfPlayDataset::from_text(&empty).expect_err("empty positions fail loudly");
    assert!(error.to_string().contains("no position records"));
}
