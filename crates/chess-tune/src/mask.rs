use crate::{
    EvaluationFeature, TunableParameter, TunableParameterDescriptor, TUNABLE_PARAMETER_COUNT,
};

/// Number of machine words required to represent every named evaluator parameter.
pub const TUNABLE_PARAMETER_MASK_WORD_COUNT: usize = TUNABLE_PARAMETER_COUNT.div_ceil(64);

const LAST_WORD_BITS: usize = TUNABLE_PARAMETER_COUNT % 64;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Fixed-size deterministic selection of named evaluator parameters.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TunableParameterMask {
    words: [u64; TUNABLE_PARAMETER_MASK_WORD_COUNT],
}

impl TunableParameterMask {
    /// Selects no parameters.
    #[must_use]
    pub const fn empty() -> Self {
        Self {
            words: [0; TUNABLE_PARAMETER_MASK_WORD_COUNT],
        }
    }

    /// Selects every named parameter.
    #[must_use]
    pub fn all() -> Self {
        let mut words = [u64::MAX; TUNABLE_PARAMETER_MASK_WORD_COUNT];
        if LAST_WORD_BITS != 0 {
            words[TUNABLE_PARAMETER_MASK_WORD_COUNT - 1] = (1_u64 << LAST_WORD_BITS) - 1;
        }
        Self { words }
    }

    /// Builds a selection from stable parameter identities.
    #[must_use]
    pub fn from_parameters(parameters: impl IntoIterator<Item = TunableParameter>) -> Self {
        let mut output = Self::empty();
        for parameter in parameters {
            output.set(parameter);
        }
        output
    }

    /// Returns whether one parameter is selected.
    #[must_use]
    pub const fn contains(self, parameter: TunableParameter) -> bool {
        let index = parameter.index();
        let word = index / 64;
        let bit = index % 64;
        self.words[word] & (1_u64 << bit) != 0
    }

    /// Returns the number of selected parameters.
    #[must_use]
    pub fn active_count(self) -> usize {
        self.words
            .iter()
            .map(|word| word.count_ones() as usize)
            .sum()
    }

    /// Returns whether no parameter is selected.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        let mut index = 0;
        while index < TUNABLE_PARAMETER_MASK_WORD_COUNT {
            if self.words[index] != 0 {
                return false;
            }
            index += 1;
        }
        true
    }

    /// Returns whether every named parameter is selected.
    #[must_use]
    pub fn is_all(self) -> bool {
        self == Self::all()
    }

    /// Returns the union of two selections.
    #[must_use]
    pub fn union(self, other: Self) -> Self {
        let mut output = Self::empty();
        for (destination, (left, right)) in output
            .words
            .iter_mut()
            .zip(self.words.into_iter().zip(other.words))
        {
            *destination = left | right;
        }
        output
    }

    /// Returns a stable FNV-1a identity over the raw selection words.
    #[must_use]
    pub fn fingerprint(self) -> u64 {
        let mut hash = FNV_OFFSET;
        for word in self.words {
            for byte in word.to_le_bytes() {
                hash ^= u64::from(byte);
                hash = hash.wrapping_mul(FNV_PRIME);
            }
        }
        hash
    }

    /// Returns the stable raw word image for provenance and tests.
    #[must_use]
    pub const fn words(self) -> [u64; TUNABLE_PARAMETER_MASK_WORD_COUNT] {
        self.words
    }

    fn set(&mut self, parameter: TunableParameter) {
        let index = parameter.index();
        self.words[index / 64] |= 1_u64 << (index % 64);
    }
}

/// S3's predeclared existing-evaluator tuning groups.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum EvaluationParameterGroup {
    /// Material values and all piece-square tables.
    MaterialAndPieceSquare,
    /// Mobility plus bishop-pair and rook-activity terms.
    MobilityAndActivity,
    /// Isolated, doubled, passed, and connected pawn terms.
    PawnStructure,
    /// King shield, king-zone pressure, and space.
    KingSafetyAndSpace,
    /// Both tapered components of the king-activity term.
    EndgameKingActivity,
    /// Every existing named evaluator parameter.
    FullExistingEvaluator,
}

impl EvaluationParameterGroup {
    /// Stable S3 group order.
    pub const ALL: [Self; 6] = [
        Self::MaterialAndPieceSquare,
        Self::MobilityAndActivity,
        Self::PawnStructure,
        Self::KingSafetyAndSpace,
        Self::EndgameKingActivity,
        Self::FullExistingEvaluator,
    ];

    /// Stable machine-readable group name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::MaterialAndPieceSquare => "material_and_piece_square",
            Self::MobilityAndActivity => "mobility_and_activity",
            Self::PawnStructure => "pawn_structure",
            Self::KingSafetyAndSpace => "king_safety_and_space",
            Self::EndgameKingActivity => "endgame_king_activity",
            Self::FullExistingEvaluator => "full_existing_evaluator",
        }
    }

    /// Returns the exact deterministic parameter mask for this group.
    #[must_use]
    pub fn mask(self) -> TunableParameterMask {
        if self == Self::FullExistingEvaluator {
            return TunableParameterMask::all();
        }
        TunableParameterMask::from_parameters(TunableParameter::all().filter(|parameter| {
            match (self, parameter.descriptor()) {
                (
                    Self::MaterialAndPieceSquare,
                    TunableParameterDescriptor::Material { .. }
                    | TunableParameterDescriptor::PieceSquare { .. },
                ) => true,
                (Self::MobilityAndActivity, TunableParameterDescriptor::Mobility { .. }) => true,
                (
                    Self::MobilityAndActivity,
                    TunableParameterDescriptor::Feature { feature, .. },
                ) => matches!(
                    feature,
                    EvaluationFeature::BishopPair
                        | EvaluationFeature::RookOpenFile
                        | EvaluationFeature::RookSemiOpenFile
                        | EvaluationFeature::RookSeventhRank
                ),
                (Self::PawnStructure, TunableParameterDescriptor::Feature { feature, .. }) => {
                    matches!(
                        feature,
                        EvaluationFeature::IsolatedPawn
                            | EvaluationFeature::DoubledPawn
                            | EvaluationFeature::PassedPawn
                            | EvaluationFeature::ConnectedPawn
                    )
                }
                (Self::KingSafetyAndSpace, TunableParameterDescriptor::Feature { feature, .. }) => {
                    matches!(
                        feature,
                        EvaluationFeature::KingShield
                            | EvaluationFeature::KingZoneAttack
                            | EvaluationFeature::Space
                    )
                }
                (
                    Self::EndgameKingActivity,
                    TunableParameterDescriptor::Feature {
                        feature: EvaluationFeature::KingActivity,
                        ..
                    },
                ) => true,
                _ => false,
            }
        }))
    }

    /// Stable identity of the exact group mask.
    #[must_use]
    pub fn mask_fingerprint(self) -> u64 {
        self.mask().fingerprint()
    }
}

#[cfg(test)]
mod tests {
    use super::{EvaluationParameterGroup, TunableParameterMask};
    use crate::{TunableParameter, TUNABLE_PARAMETER_COUNT};

    #[test]
    fn group_masks_cover_the_existing_evaluator_without_overlap() {
        let expected = [778, 16, 8, 6, 2, 810];
        for (group, count) in EvaluationParameterGroup::ALL.into_iter().zip(expected) {
            assert_eq!(group.mask().active_count(), count, "{}", group.name());
            assert_ne!(group.mask_fingerprint(), 0);
        }

        let mut union = TunableParameterMask::empty();
        for group in EvaluationParameterGroup::ALL.into_iter().take(5) {
            let mask = group.mask();
            for parameter in TunableParameter::all() {
                assert!(
                    !(union.contains(parameter) && mask.contains(parameter)),
                    "parameter {} appears in more than one pre-full group",
                    parameter.name()
                );
            }
            union = union.union(mask);
        }
        assert_eq!(union.active_count(), TUNABLE_PARAMETER_COUNT);
        assert_eq!(union, TunableParameterMask::all());
    }

    #[test]
    fn raw_mask_round_trip_is_stable() {
        let selected = TunableParameterMask::from_parameters([
            TunableParameter::from_index(0).expect("first parameter"),
            TunableParameter::from_index(TUNABLE_PARAMETER_COUNT - 1).expect("last parameter"),
        ]);
        assert_eq!(selected.active_count(), 2);
        assert!(!selected.is_all());
        assert!(!selected.is_empty());
        assert_ne!(
            selected.fingerprint(),
            TunableParameterMask::all().fingerprint()
        );
    }
}
