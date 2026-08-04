from pathlib import Path


path = Path("crates/chess-tools/src/self_play.rs")
text = path.read_text()
old_import = '''use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table, EvaluationWeightSet,
    SearchLimits, TranspositionTable,
};
'''
new_import = '''use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table,
    iterative_deepening_search_with_limits_and_transposition_table_and_weights,
    EvaluationWeightSet, EvaluationWeights, SearchLimits, TranspositionTable,
};
'''
if text.count(old_import) != 1:
    raise SystemExit("unexpected chess-search import block")
text = text.replace(old_import, new_import, 1)

marker = '''fn raw_position(game: &Game, opening_position: bool) -> Result<RawPosition, ToolError> {
'''
insert = '''/// Complete fixed configuration for one weighted validation game.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct WeightedValidationGameConfig {
    white: SelfPlaySideConfig,
    black: SelfPlaySideConfig,
    maximum_plies: u32,
    claimable_draw_policy: ClaimableDrawPolicy,
}

impl WeightedValidationGameConfig {
    pub(crate) fn new(
        white: SelfPlaySideConfig,
        black: SelfPlaySideConfig,
        maximum_plies: u32,
        claimable_draw_policy: ClaimableDrawPolicy,
    ) -> Result<Self, ToolError> {
        white.validate()?;
        black.validate()?;
        if maximum_plies == 0 || maximum_plies > MAX_SELF_PLAY_PLIES {
            return Err(ToolError::new(format!(
                "validation maximum plies must be between 1 and {MAX_SELF_PLAY_PLIES}, found {maximum_plies}"
            )));
        }
        Ok(Self {
            white,
            black,
            maximum_plies,
            claimable_draw_policy,
        })
    }
}

/// Result and replay payload for one evaluator-controlled validation game.
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct WeightedValidationGame {
    result: SelfPlayResult,
    termination: SelfPlayTermination,
    moves: Vec<String>,
    final_fen: String,
}

impl WeightedValidationGame {
    pub(crate) const fn result(&self) -> SelfPlayResult {
        self.result
    }

    pub(crate) const fn termination(&self) -> SelfPlayTermination {
        self.termination
    }

    pub(crate) fn moves(&self) -> &[String] {
        &self.moves
    }

    pub(crate) fn final_fen(&self) -> &str {
        &self.final_fen
    }
}

/// Plays one game with independently supplied, validated evaluator weights.
///
/// This uses the same opening replay, draw policy, maximum-ply handling, game
/// history, search limits, and separate per-color transposition tables as the
/// Task 20 self-play controller.
pub(crate) fn run_weighted_validation_game(
    opening: &OpeningLine,
    config: WeightedValidationGameConfig,
    white_weights: &EvaluationWeights,
    black_weights: &EvaluationWeights,
) -> Result<WeightedValidationGame, ToolError> {
    let mut game = opening.instantiate()?;
    let opening_plies = u32::try_from(game.ply_count())
        .map_err(|_| ToolError::new("opening ply count exceeds u32"))?;
    if opening_plies >= config.maximum_plies {
        return Err(ToolError::new(format!(
            "opening {:?} has {opening_plies} plies but validation maximum is {}",
            opening.identifier, config.maximum_plies
        )));
    }

    let mut white_table = TranspositionTable::new(config.white.transposition_table_mebibytes)
        .map_err(|error| ToolError::new(error.to_string()))?;
    let mut black_table = TranspositionTable::new(config.black.transposition_table_mebibytes)
        .map_err(|error| ToolError::new(error.to_string()))?;

    let (result, termination) = loop {
        let status = game
            .status()
            .map_err(|error| ToolError::new(error.to_string()))?;
        if let Some(completed) = completed_status(status, config.claimable_draw_policy) {
            break completed;
        }
        let ply_count = u32::try_from(game.ply_count())
            .map_err(|_| ToolError::new("game ply count exceeds u32"))?;
        if ply_count >= config.maximum_plies {
            break (
                SelfPlayResult::Unfinished,
                SelfPlayTermination::MaximumPly(config.maximum_plies),
            );
        }

        let (side_config, table, weights) = match game.position().side_to_move() {
            Color::White => (config.white, &mut white_table, white_weights),
            Color::Black => (config.black, &mut black_table, black_weights),
        };
        let mut position = game.position().clone();
        let mut history = game.search_history();
        let search = iterative_deepening_search_with_limits_and_transposition_table_and_weights(
            &mut position,
            &mut history,
            side_config.search_limits(),
            table,
            weights,
        )
        .map_err(|error| ToolError::new(error.to_string()))?;
        let current = search.best_move().ok_or_else(|| {
            ToolError::new(format!(
                "nonterminal weighted validation position at ply {ply_count} produced no move"
            ))
        })?;
        game.make_move(current)
            .map_err(|error| ToolError::new(error.to_string()))?;
    };

    Ok(WeightedValidationGame {
        result,
        termination,
        moves: game.moves().iter().map(|current| current.to_uci()).collect(),
        final_fen: game.position().to_fen(),
    })
}

'''
if text.count(marker) != 1:
    raise SystemExit("unexpected raw_position marker")
path.write_text(text.replace(marker, insert + marker, 1))
