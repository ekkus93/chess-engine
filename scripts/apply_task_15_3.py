#!/usr/bin/env python3
"""Apply Task 15.3 mate-score normalization atomically."""

from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def apply(root: Path) -> None:
    transposition = root / "crates/chess-search/src/transposition.rs"
    replace_once(
        transposition,
        """/// A score already converted into the transposition table's storage domain.
///
/// Task 15.3 will define the mate-distance conversion between node-relative
/// [`Score`] values and this stored representation. Keeping the value in a
/// distinct type prevents an ordinary node score from being placed into an
/// entry accidentally once storage and probes are implemented.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct TranspositionScore(Score);

impl TranspositionScore {
    /// Wraps a score that the caller has already normalized for storage.
    ///
    /// Before Task 15.3 this constructor is the explicit boundary used by entry
    /// tests. Production search does not yet create or consume TT entries.
    #[must_use]
    pub const fn from_normalized(normalized: Score) -> Self {
        Self(normalized)
    }
""",
        """/// A score converted into the transposition table's storage domain.
///
/// Use [`TranspositionScore::normalize`] to convert a root-relative search
/// score at the storage ply and [`TranspositionScore::denormalize`] to recover
/// the correct root-relative value at a later probe ply. Keeping the value in a
/// distinct type prevents ordinary search scores from being confused with
/// position-relative stored scores.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct TranspositionScore(Score);

impl TranspositionScore {
    /// Wraps a score already proven to be in the normalized storage domain.
    ///
    /// Public callers must use [`TranspositionScore::normalize`]. This
    /// crate-private constructor remains available to the conversion module and
    /// focused entry-layout tests without exposing an unchecked public bypass.
    #[must_use]
    pub(crate) const fn from_normalized(normalized: Score) -> Self {
        Self(normalized)
    }
""",
    )
    replace_once(
        transposition,
        """/// entry retains the complete 64-bit position key as a verification key rather
/// than relying on the bucket index alone. The score must already be in the
/// normalized storage domain represented by [`TranspositionScore`].
""",
        """/// entry retains the complete 64-bit position key as a verification key rather
/// than relying on the bucket index alone. Scores enter the normalized storage
/// domain through [`TranspositionScore::normalize`].
""",
    )

    lib = root / "crates/chess-search/src/lib.rs"
    replace_once(
        lib,
        """mod search_common;
mod transposition;
mod weights;
""",
        """mod search_common;
mod transposition;
mod transposition_score;
mod weights;
""",
    )
    replace_once(
        lib,
        """pub use transposition::{
    TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
    TranspositionTableAllocationError, TRANSPOSITION_CLUSTER_SIZE,
};
""",
        """pub use transposition::{
    TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
    TranspositionTableAllocationError, TRANSPOSITION_CLUSTER_SIZE,
};
pub use transposition_score::TranspositionScoreConversionError;
""",
    )

    score_module = root / "crates/chess-search/src/transposition_score.rs"
    if score_module.exists():
        raise RuntimeError(f"{score_module}: already exists")
    score_module.write_text(
        '''use core::fmt;

use crate::{
    transposition::TranspositionScore, Score, MAX_EVALUATION, MAX_MATE_PLY,
};

/// Failure to convert between root-relative search scores and TT storage scores.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionScoreConversionError {
    /// The requested search ply exceeds the engine's supported mate-distance domain.
    UnsupportedPly {
        /// Requested root-relative search ply.
        ply: u16,
        /// Largest supported search ply.
        maximum: u16,
    },
    /// Normalizing the supplied search score would leave the supported score domain.
    NormalizationOutOfRange {
        /// Root-relative score supplied by search.
        score: Score,
        /// Ply at which the score would be stored.
        ply: u16,
    },
    /// Denormalizing the stored score would leave the supported score domain.
    DenormalizationOutOfRange {
        /// Position-relative score retained in storage.
        normalized_score: Score,
        /// Ply at which the score would be reused.
        ply: u16,
    },
}

impl fmt::Display for TranspositionScoreConversionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedPly { ply, maximum } => write!(
                formatter,
                "transposition-score ply {ply} exceeds supported maximum {maximum}"
            ),
            Self::NormalizationOutOfRange { score, ply } => write!(
                formatter,
                "normalizing search score {score} at ply {ply} leaves the supported score domain"
            ),
            Self::DenormalizationOutOfRange {
                normalized_score,
                ply,
            } => write!(
                formatter,
                "denormalizing stored score {normalized_score} at ply {ply} leaves the supported score domain"
            ),
        }
    }
}

impl std::error::Error for TranspositionScoreConversionError {}

impl TranspositionScore {
    /// Converts a root-relative search score into a position-relative TT score.
    ///
    /// Winning mate scores add `ply`; losing mate scores subtract `ply`. This
    /// removes the distance already travelled from the search root. Ordinary
    /// evaluation scores, including both evaluation boundaries, are preserved
    /// exactly.
    pub fn normalize(
        score: Score,
        ply: u16,
    ) -> Result<Self, TranspositionScoreConversionError> {
        validate_ply(ply)?;
        let centipawns = score.centipawns();
        let adjusted = if centipawns > MAX_EVALUATION {
            centipawns + i32::from(ply)
        } else if centipawns < -MAX_EVALUATION {
            centipawns - i32::from(ply)
        } else {
            centipawns
        };
        let normalized = Score::from_raw(adjusted).ok_or(
            TranspositionScoreConversionError::NormalizationOutOfRange { score, ply },
        )?;
        Ok(Self::from_normalized(normalized))
    }

    /// Converts a position-relative TT score into a root-relative search score.
    ///
    /// Winning mate scores subtract `ply`; losing mate scores add `ply`. This
    /// restores the distance from the current search root to the probed node.
    /// Ordinary evaluation scores are preserved exactly.
    pub fn denormalize(
        self,
        ply: u16,
    ) -> Result<Score, TranspositionScoreConversionError> {
        validate_ply(ply)?;
        let normalized_score = self.normalized();
        let centipawns = normalized_score.centipawns();
        let adjusted = if centipawns > MAX_EVALUATION {
            centipawns - i32::from(ply)
        } else if centipawns < -MAX_EVALUATION {
            centipawns + i32::from(ply)
        } else {
            centipawns
        };
        Score::from_raw(adjusted).ok_or(
            TranspositionScoreConversionError::DenormalizationOutOfRange {
                normalized_score,
                ply,
            },
        )
    }
}

fn validate_ply(ply: u16) -> Result<(), TranspositionScoreConversionError> {
    if ply > MAX_MATE_PLY {
        Err(TranspositionScoreConversionError::UnsupportedPly {
            ply,
            maximum: MAX_MATE_PLY,
        })
    } else {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::TranspositionScoreConversionError;
    use crate::{
        Score, TranspositionScore, MATE_SCORE, MAX_EVALUATION, MAX_MATE_PLY,
    };

    #[test]
    fn ordinary_evaluations_are_preserved_exactly_at_every_supported_ply() {
        for centipawns in [
            -MAX_EVALUATION,
            -417,
            0,
            892,
            MAX_EVALUATION,
        ] {
            let score = Score::from_evaluation(centipawns);
            let stored = TranspositionScore::normalize(score, MAX_MATE_PLY)
                .expect("evaluation normalization succeeds");

            assert_eq!(stored.normalized(), score);
            assert_eq!(stored.denormalize(0), Ok(score));
            assert_eq!(stored.denormalize(MAX_MATE_PLY), Ok(score));
        }
    }

    #[test]
    fn winning_mate_entry_round_trips_when_reached_at_different_plies() {
        let first_ply = 7;
        let second_ply = 19;
        let node_distance = 12;
        let first_score = Score::mate_in(first_ply + node_distance).expect("mate score");
        let second_score = Score::mate_in(second_ply + node_distance).expect("mate score");

        let stored = TranspositionScore::normalize(first_score, first_ply)
            .expect("winning mate normalizes");

        assert_eq!(stored.normalized().centipawns(), MATE_SCORE - i32::from(node_distance));
        assert_eq!(
            TranspositionScore::normalize(second_score, second_ply),
            Ok(stored)
        );
        assert_eq!(stored.denormalize(first_ply), Ok(first_score));
        assert_eq!(stored.denormalize(second_ply), Ok(second_score));
    }

    #[test]
    fn losing_mate_entry_round_trips_when_reached_at_different_plies() {
        let first_ply = 5;
        let second_ply = 23;
        let node_distance = 9;
        let first_score = Score::mated_in(first_ply + node_distance).expect("mate score");
        let second_score = Score::mated_in(second_ply + node_distance).expect("mate score");

        let stored = TranspositionScore::normalize(first_score, first_ply)
            .expect("losing mate normalizes");

        assert_eq!(stored.normalized().centipawns(), -MATE_SCORE + i32::from(node_distance));
        assert_eq!(
            TranspositionScore::normalize(second_score, second_ply),
            Ok(stored)
        );
        assert_eq!(stored.denormalize(first_ply), Ok(first_score));
        assert_eq!(stored.denormalize(second_ply), Ok(second_score));
    }

    #[test]
    fn maximum_supported_ply_reaches_both_immediate_mate_boundaries() {
        let winning = Score::mate_in(MAX_MATE_PLY).expect("maximum mate distance");
        let losing = Score::mated_in(MAX_MATE_PLY).expect("maximum mate distance");
        let stored_winning = TranspositionScore::normalize(winning, MAX_MATE_PLY)
            .expect("winning boundary normalizes");
        let stored_losing = TranspositionScore::normalize(losing, MAX_MATE_PLY)
            .expect("losing boundary normalizes");

        assert_eq!(stored_winning.normalized().centipawns(), MATE_SCORE);
        assert_eq!(stored_losing.normalized().centipawns(), -MATE_SCORE);
        assert_eq!(stored_winning.denormalize(MAX_MATE_PLY), Ok(winning));
        assert_eq!(stored_losing.denormalize(MAX_MATE_PLY), Ok(losing));
    }

    #[test]
    fn inconsistent_root_relative_mates_fail_before_storage() {
        let immediate_win = Score::mate_in(0).expect("immediate mate boundary");
        let immediate_loss = Score::mated_in(0).expect("immediate mate boundary");

        assert_eq!(
            TranspositionScore::normalize(immediate_win, 1),
            Err(TranspositionScoreConversionError::NormalizationOutOfRange {
                score: immediate_win,
                ply: 1,
            })
        );
        assert_eq!(
            TranspositionScore::normalize(immediate_loss, 1),
            Err(TranspositionScoreConversionError::NormalizationOutOfRange {
                score: immediate_loss,
                ply: 1,
            })
        );
    }

    #[test]
    fn unsupported_ply_is_rejected_for_both_conversion_directions() {
        let unsupported = MAX_MATE_PLY + 1;
        let score = Score::from_evaluation(17);
        let stored = TranspositionScore::normalize(score, 0).expect("root score normalizes");
        let expected = TranspositionScoreConversionError::UnsupportedPly {
            ply: unsupported,
            maximum: MAX_MATE_PLY,
        };

        assert_eq!(TranspositionScore::normalize(score, unsupported), Err(expected));
        assert_eq!(stored.denormalize(unsupported), Err(expected));
        assert_eq!(
            expected.to_string(),
            format!(
                "transposition-score ply {unsupported} exceeds supported maximum {MAX_MATE_PLY}"
            )
        );
    }
}
''',
        encoding="utf-8",
    )

    entry_doc = root / "docs/RUST_TRANSPOSITION_TABLE_ENTRY.md"
    replace_once(
        entry_doc,
        """4. **Normalized score:** `TranspositionScore`, a distinct wrapper around `Score`. Task 15.3 will provide the node-ply conversion rules for mate scores. The wrapper prevents ordinary node-relative scores from being confused with stored scores once probes are enabled.
""",
        """4. **Normalized score:** `TranspositionScore`, a distinct wrapper around `Score`. Task 15.3 provides the root-ply conversion rules for mate scores. The wrapper prevents root-relative search scores from being confused with position-relative stored scores once probes are enabled.
""",
    )
    replace_once(
        entry_doc,
        """## Score boundary

`TranspositionScore::from_normalized` is deliberately explicit. It accepts only a caller assertion that the supplied score is already in the storage domain. Task 15.3 will replace direct caller reasoning with tested normalization and denormalization helpers for ply-relative mate scores.

Static centipawn values remain unchanged by that future conversion. Mate values will be translated so the same stored entry can be reached and interpreted correctly at different search plies.
""",
        """## Score boundary

`TranspositionScore::normalize(score, ply)` is the public storage boundary. It converts root-relative winning and losing mate scores into position-relative values while preserving static centipawn scores exactly. `TranspositionScore::denormalize(ply)` performs the inverse conversion for a future probe.

The unchecked `from_normalized` constructor is crate-private. Public callers therefore cannot bypass the tested conversion contract. Conversion failures are typed and fail loudly when the ply is unsupported or normalization would leave the score domain.
""",
    )
    replace_once(
        entry_doc,
        """Task 15.2 will choose the fixed-memory bucket and cluster shape using this measured entry footprint. There is no heap table, map, allocation policy, empty-slot encoding, or replacement policy in Task 15.1.
""",
        """Task 15.2 chose the fixed-memory bucket and cluster shape using this measured entry footprint. Task 15.1 itself introduced no heap table, map, allocation policy, empty-slot encoding, or replacement policy.
""",
    )

    normalization_doc = root / "docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md"
    if normalization_doc.exists():
        raise RuntimeError(f"{normalization_doc}: already exists")
    normalization_doc.write_text(
        '''# Rust Transposition-Table Mate-Score Normalization

## Scope

This document defines Task 15.3 only: converting root-relative search mate scores into position-relative transposition-table scores and converting them back at a later search ply.

It does not define table probing, depth or bound cutoffs, repetition-sensitive reuse, replacement, diagnostics, or production search integration. Those remain Tasks 15.4 through 15.6.

## Why normalization is required

Search scores encode mate distance from the current search root. The same chess position can be reached at different plies in different searches, so storing that root-relative value directly would make the entry incorrect when reused from another root.

The table instead stores mate distance relative to the indexed position. Let `p` be the ply from the current root to that position.

For a winning mate score:

- storage adds `p`;
- retrieval subtracts the new probe ply.

For a losing mate score:

- storage subtracts `p`;
- retrieval adds the new probe ply.

This removes the already-travelled root distance when storing and restores the appropriate root distance when retrieving.

## Non-mate scores

Every score in the static-evaluation domain from `-MAX_EVALUATION` through `MAX_EVALUATION` is preserved exactly. Normalization and denormalization do not round, clamp, or otherwise alter ordinary evaluations.

## Public API

- `TranspositionScore::normalize(score, ply)` converts a root-relative `Score` into the storage domain.
- `TranspositionScore::denormalize(ply)` converts the stored value back into a root-relative `Score`.
- `TranspositionScoreConversionError` reports unsupported plies and any conversion that would leave the supported score domain.

The unchecked constructor used by entry-layout tests is crate-private, so external callers cannot place an arbitrary search score into the storage domain.

## Failure behavior

Both directions reject plies greater than `MAX_MATE_PLY`.

Normalization also rejects an inconsistent mate score whose adjustment would exceed `MATE_SCORE` or go below `-MATE_SCORE`. There is no saturation, clamping, or fallback score.

## Validation requirements

Task 15.3 tests prove:

- ordinary evaluations remain exact at root and maximum supported ply;
- one winning-mate entry normalizes identically when the same position is reached at different plies;
- one losing-mate entry normalizes identically when the same position is reached at different plies;
- maximum supported ply reaches and reverses both immediate-mate storage boundaries;
- inconsistent root-relative mate values fail before storage;
- unsupported plies fail in both conversion directions.
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_task_15_3.py <repository-root>")
    apply(Path(sys.argv[1]).resolve())
