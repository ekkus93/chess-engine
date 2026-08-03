use core::fmt;

use chess_core::{LegalMoveError, Move, Position};

use crate::TranspositionTable;

/// Why safe principal-variation reconstruction stopped.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalVariationTermination {
    /// The line contains exactly the requested number of plies.
    ReachedRequestedDepth,
    /// The current position has no legal moves before the requested depth.
    TerminalPosition {
        /// Root-relative ply at which the terminal was observed.
        ply: u16,
    },
    /// The exact root result did not contain a move, such as a resolved draw.
    RootResultWithoutMove,
    /// No complete-key exact entry with sufficient depth and a move was available.
    MissingExactEntry {
        /// Root-relative ply that could not be extended.
        ply: u16,
        /// Depth still required from the current position.
        remaining_depth: u16,
    },
    /// A verified table entry contained a move that is not currently legal.
    IllegalTableMove {
        /// Root-relative ply at which the move was rejected.
        ply: u16,
        /// Rejected candidate.
        candidate: Move,
    },
    /// Following legal verified moves returned to a previously visited identity.
    RepeatedPosition {
        /// Number of legal PV moves already retained.
        ply: u16,
        /// Repeated complete position identity.
        verification_key: u64,
    },
}

/// A bounded legal principal variation reconstructed after one completed search.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalVariation {
    moves: Vec<Move>,
    termination: PrincipalVariationTermination,
}

impl PrincipalVariation {
    /// Returns the legal move sequence in root-to-leaf order.
    #[must_use]
    pub fn moves(&self) -> &[Move] {
        &self.moves
    }

    /// Returns the number of retained legal plies.
    #[must_use]
    pub fn len(&self) -> usize {
        self.moves.len()
    }

    /// Returns whether the reconstructed line contains no move.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.moves.is_empty()
    }

    /// Returns the opponent reply after the root best move, when available.
    #[must_use]
    pub fn ponder_move(&self) -> Option<Move> {
        self.moves.get(1).copied()
    }

    /// Returns the explicit reason reconstruction stopped.
    #[must_use]
    pub const fn termination(&self) -> PrincipalVariationTermination {
        self.termination
    }
}

/// Failure to allocate or legally validate a principal variation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalVariationError {
    /// The allocator rejected bounded move or cycle-detection storage.
    AllocationFailed {
        /// Requested maximum PV depth.
        requested_depth: u16,
    },
    /// Legal move generation or application failed unexpectedly.
    Rules {
        /// Root-relative ply being reconstructed.
        ply: u16,
        /// Underlying rule error.
        error: LegalMoveError,
    },
}

impl fmt::Display for PrincipalVariationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::AllocationFailed { requested_depth } => write!(
                formatter,
                "failed to reserve bounded principal-variation storage for depth {requested_depth}"
            ),
            Self::Rules { ply, error } => {
                write!(
                    formatter,
                    "principal-variation rules failed at ply {ply}: {error}"
                )
            }
        }
    }
}

impl std::error::Error for PrincipalVariationError {}

pub(crate) fn reconstruct_principal_variation(
    root: &Position,
    requested_depth: u16,
    root_best_move: Option<Move>,
    transposition_table: &TranspositionTable,
) -> Result<PrincipalVariation, PrincipalVariationError> {
    let mut moves = Vec::new();
    moves
        .try_reserve_exact(usize::from(requested_depth))
        .map_err(|_| PrincipalVariationError::AllocationFailed { requested_depth })?;
    let mut visited_keys = Vec::new();
    visited_keys
        .try_reserve_exact(usize::from(requested_depth) + 1)
        .map_err(|_| PrincipalVariationError::AllocationFailed { requested_depth })?;

    let mut position = root.clone();
    visited_keys.push(position.zobrist());
    let mut remaining_depth = requested_depth;
    let mut ply = 0_u16;

    while remaining_depth > 0 {
        let tokens = position
            .legal_move_tokens()
            .map_err(|error| PrincipalVariationError::Rules { ply, error })?;
        if tokens.is_empty() {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::TerminalPosition { ply },
            });
        }

        let candidate = if ply == 0 {
            root_best_move
        } else {
            transposition_table.principal_variation_move(position.zobrist(), remaining_depth)
        };
        let Some(candidate) = candidate else {
            let termination = if ply == 0 {
                PrincipalVariationTermination::RootResultWithoutMove
            } else {
                PrincipalVariationTermination::MissingExactEntry {
                    ply,
                    remaining_depth,
                }
            };
            return Ok(PrincipalVariation { moves, termination });
        };

        let Some(token) = tokens.iter().find(|token| token.move_made() == candidate) else {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::IllegalTableMove { ply, candidate },
            });
        };

        position
            .make_legal_token(token)
            .map_err(|error| PrincipalVariationError::Rules { ply, error })?;
        moves.push(candidate);
        ply += 1;
        remaining_depth -= 1;

        if remaining_depth == 0 {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::ReachedRequestedDepth,
            });
        }

        let verification_key = position.zobrist();
        if visited_keys.contains(&verification_key) {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::RepeatedPosition {
                    ply,
                    verification_key,
                },
            });
        }
        visited_keys.push(verification_key);
    }

    Ok(PrincipalVariation {
        moves,
        termination: PrincipalVariationTermination::ReachedRequestedDepth,
    })
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Position, Square, UciMove};

    use super::{reconstruct_principal_variation, PrincipalVariationTermination};
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn resolve(position: &mut Position, text: &str) -> Move {
        let syntax = text.parse::<UciMove>().expect("PV UCI syntax is valid");
        position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| syntax.matches(token.move_made()))
            .expect("PV fixture move is legal")
            .move_made()
    }

    fn play(position: &mut Position, text: &str) -> Move {
        let current = resolve(position, text);
        let token = position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| token.move_made() == current)
            .expect("PV token is present");
        position
            .make_legal_token(token)
            .expect("PV fixture move applies");
        current
    }

    fn store_exact(table: &mut TranspositionTable, position: &Position, depth: u16, current: Move) {
        table.store(TranspositionEntry::new(
            position.zobrist(),
            depth,
            TranspositionBound::Exact,
            TranspositionScore::normalize(Score::ZERO, 0).expect("PV score normalizes"),
            Some(current),
            table.generation(),
        ));
    }

    #[test]
    fn complete_exact_chain_is_legal_bounded_and_returns_ponder_move() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let reply = resolve(&mut cursor, "e7e5");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 2, reply);
        let _reply = play(&mut cursor, "e7e5");
        let third = resolve(&mut cursor, "g1f3");
        store_exact(&mut table, &cursor, 1, third);
        table.reset_diagnostics();

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move, reply, third]);
        assert_eq!(pv.ponder_move(), Some(reply));
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::ReachedRequestedDepth
        );
        assert_eq!(
            table.diagnostics(),
            TranspositionTableDiagnostics::default()
        );
    }

    #[test]
    fn complete_key_collision_cannot_extend_the_line() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let reply = resolve(&mut cursor, "e7e5");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        let collision_key = cursor.zobrist().wrapping_add(table.cluster_count() as u64);
        table.store(TranspositionEntry::new(
            collision_key,
            2,
            TranspositionBound::Exact,
            TranspositionScore::normalize(Score::ZERO, 0).expect("PV score normalizes"),
            Some(reply),
            table.generation(),
        ));

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::MissingExactEntry {
                ply: 1,
                remaining_depth: 2,
            }
        );
    }

    #[test]
    fn illegal_table_move_is_rejected_before_it_enters_the_pv() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let illegal = Move::new(
            "a1".parse::<Square>().expect("a1 is valid"),
            "a8".parse::<Square>().expect("a8 is valid"),
            MoveKind::Quiet,
        );
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 2, illegal);

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::IllegalTableMove {
                ply: 1,
                candidate: illegal,
            }
        );
    }

    #[test]
    fn repeated_position_terminates_a_legal_tt_cycle() {
        let root = Position::starting();
        let root_key = root.zobrist();
        let mut cursor = root.clone();
        let first = play(&mut cursor, "g1f3");
        let second = resolve(&mut cursor, "g8f6");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 7, second);
        let _second = play(&mut cursor, "g8f6");
        let third = resolve(&mut cursor, "f3g1");
        store_exact(&mut table, &cursor, 6, third);
        let _third = play(&mut cursor, "f3g1");
        let fourth = resolve(&mut cursor, "f6g8");
        store_exact(&mut table, &cursor, 5, fourth);

        let pv = reconstruct_principal_variation(&root, 8, Some(first), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[first, second, third, fourth]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::RepeatedPosition {
                ply: 4,
                verification_key: root_key,
            }
        );
    }
}
