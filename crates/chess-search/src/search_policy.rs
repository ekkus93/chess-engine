use core::fmt;

use crate::{
    aspiration::DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
    check_extension::MAX_CHECK_EXTENSIONS_PER_LINE, quiescence::MAX_QUIESCENCE_PLY, MAX_MATE_PLY,
};

/// Current serialized search-policy schema.
pub const SEARCH_POLICY_SCHEMA_VERSION: u16 = 1;
/// Stable identifier for the authoritative v0.1 search policy.
pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;
/// Canonical checksum of the authoritative v0.1 search policy.
pub const V0_1_SEARCH_POLICY_CHECKSUM: u64 = 0x0c07_69ef_9d03_4770;
/// Stable identifier for the inactive S2-5 SEE capture-ordering candidate.
pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;
/// Stable identifier for the inactive S2-6 SEE quiescence-pruning candidate.
pub const SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3653_4545_5031;
/// Stable identifier for the inactive S2-6 SEE-plus-delta candidate.
pub const SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3644_454c_5031;
/// Largest accepted aspiration half-width.
pub const MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS: u16 = 10_000;
/// Largest accepted bounded check-extension budget.
pub const MAXIMUM_CHECK_EXTENSIONS_PER_LINE: u16 = 4;

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Authoritative alpha-beta semantic family.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum AlphaBetaMode {
    /// Full-window, fail-soft negamax alpha-beta.
    FullWindowFailSoft = 1,
}

impl AlphaBetaMode {
    /// Stable canonical text name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::FullWindowFailSoft => "full_window_fail_soft",
        }
    }

    const fn code(self) -> u8 {
        self as u8
    }
}

/// Authoritative transposition-table semantic family.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum TranspositionPolicy {
    /// Clustered full-key table with generation-aware replacement.
    ClusteredFullKey = 1,
}

impl TranspositionPolicy {
    /// Stable canonical text name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::ClusteredFullKey => "clustered_full_key",
        }
    }

    const fn code(self) -> u8 {
        self as u8
    }
}

/// Authoritative move-ordering semantic family.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum MoveOrderingPolicy {
    /// TT move, promotions, MVV-LVA captures, killers, history, deterministic tie-break.
    V0_1MvvLvaKillersHistory = 1,
}

impl MoveOrderingPolicy {
    /// Stable canonical text name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::V0_1MvvLvaKillersHistory => "v0_1_mvv_lva_killers_history",
        }
    }

    const fn code(self) -> u8 {
        self as u8
    }
}

/// Authoritative quiescence semantic family.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[repr(u8)]
pub enum QuiescencePolicy {
    /// Stand pat outside check; captures/promotions; all evasions in check.
    CapturesPromotionsAndEvasions = 1,
}

impl QuiescencePolicy {
    /// Stable canonical text name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::CapturesPromotionsAndEvasions => "captures_promotions_and_evasions",
        }
    }

    const fn code(self) -> u8 {
        self as u8
    }
}

/// Experimental feature represented in policy identity but unavailable until its task lands.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExperimentalSearchFeature {
    /// Static-exchange capture ordering.
    SeeCaptureOrdering,
    /// Static-exchange quiescence pruning.
    SeeQuiescencePruning,
    /// Delta pruning in quiescence.
    DeltaPruning,
    /// Principal Variation Search.
    PrincipalVariationSearch,
    /// Late Move Reductions.
    LateMoveReductions,
    /// Null-move pruning.
    NullMovePruning,
    /// Futility pruning.
    FutilityPruning,
    /// Razoring.
    Razoring,
    /// Late quiet-move pruning.
    LateMovePruning,
}

impl ExperimentalSearchFeature {
    const fn bit(self) -> u64 {
        match self {
            Self::SeeCaptureOrdering => 1 << 0,
            Self::SeeQuiescencePruning => 1 << 1,
            Self::DeltaPruning => 1 << 2,
            Self::PrincipalVariationSearch => 1 << 3,
            Self::LateMoveReductions => 1 << 4,
            Self::NullMovePruning => 1 << 5,
            Self::FutilityPruning => 1 << 6,
            Self::Razoring => 1 << 7,
            Self::LateMovePruning => 1 << 8,
        }
    }

    /// Stable machine-readable feature name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::SeeCaptureOrdering => "see_capture_ordering",
            Self::SeeQuiescencePruning => "see_quiescence_pruning",
            Self::DeltaPruning => "delta_pruning",
            Self::PrincipalVariationSearch => "principal_variation_search",
            Self::LateMoveReductions => "late_move_reductions",
            Self::NullMovePruning => "null_move_pruning",
            Self::FutilityPruning => "futility_pruning",
            Self::Razoring => "razoring",
            Self::LateMovePruning => "late_move_pruning",
        }
    }
}

/// Compact deterministic experimental-feature bitset.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct ExperimentalSearchFeatures {
    bits: u64,
}

impl ExperimentalSearchFeatures {
    /// No experimental behavior enabled.
    pub const NONE: Self = Self { bits: 0 };
    /// Inactive S2-5 SEE capture-ordering candidate.
    pub const SEE_CAPTURE_ORDERING: Self = Self {
        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit(),
    };
    /// Inactive S2-6 SEE quiescence-pruning candidate.
    pub const SEE_QUIESCENCE_PRUNING: Self = Self {
        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit(),
    };
    /// Inactive S2-6 SEE pruning followed by delta pruning.
    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self = Self {
        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit()
            | ExperimentalSearchFeature::DeltaPruning.bit(),
    };
    /// All currently assigned feature bits.
    pub const KNOWN_BITS: u64 = (1_u64 << 9) - 1;

    /// Constructs a bitset while rejecting unknown future bits.
    pub const fn from_bits(bits: u64) -> Result<Self, SearchPolicyValidationError> {
        let unknown = bits & !Self::KNOWN_BITS;
        if unknown != 0 {
            return Err(
                SearchPolicyValidationError::UnknownExperimentalFeatureBits { bits: unknown },
            );
        }
        Ok(Self { bits })
    }

    /// Returns the canonical raw bitset.
    #[must_use]
    pub const fn bits(self) -> u64 {
        self.bits
    }

    /// Returns whether every experimental feature is disabled.
    #[must_use]
    pub const fn is_empty(self) -> bool {
        self.bits == 0
    }

    /// Returns whether one assigned feature is enabled.
    #[must_use]
    pub const fn contains(self, feature: ExperimentalSearchFeature) -> bool {
        self.bits & feature.bit() != 0
    }

    fn first_unsupported_enabled(self) -> Option<ExperimentalSearchFeature> {
        const FEATURES: [(u64, ExperimentalSearchFeature); 9] = [
            (1 << 0, ExperimentalSearchFeature::SeeCaptureOrdering),
            (1 << 1, ExperimentalSearchFeature::SeeQuiescencePruning),
            (1 << 2, ExperimentalSearchFeature::DeltaPruning),
            (1 << 3, ExperimentalSearchFeature::PrincipalVariationSearch),
            (1 << 4, ExperimentalSearchFeature::LateMoveReductions),
            (1 << 5, ExperimentalSearchFeature::NullMovePruning),
            (1 << 6, ExperimentalSearchFeature::FutilityPruning),
            (1 << 7, ExperimentalSearchFeature::Razoring),
            (1 << 8, ExperimentalSearchFeature::LateMovePruning),
        ];
        FEATURES.into_iter().find_map(|(bit, feature)| {
            let implemented = matches!(
                feature,
                ExperimentalSearchFeature::SeeCaptureOrdering
                    | ExperimentalSearchFeature::SeeQuiescencePruning
                    | ExperimentalSearchFeature::DeltaPruning
            );
            (self.bits & bit != 0 && !implemented).then_some(feature)
        })
    }
}

/// Complete typed search-policy parameter set.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SearchPolicyParameters {
    /// Alpha-beta semantic family.
    pub alpha_beta: AlphaBetaMode,
    /// Transposition-table semantic family.
    pub transposition: TranspositionPolicy,
    /// Move-ordering semantic family.
    pub move_ordering: MoveOrderingPolicy,
    /// Quiescence semantic family.
    pub quiescence: QuiescencePolicy,
    /// Whether later completed depths use aspiration windows.
    pub aspiration_windows: bool,
    /// Aspiration half-width in centipawns, or zero when disabled.
    pub aspiration_half_width_centipawns: u16,
    /// Maximum tactical plies beyond a normal frontier.
    pub maximum_quiescence_ply: u16,
    /// Maximum optional check extensions on one search line.
    pub maximum_check_extensions_per_line: u16,
    /// Inactive future feature bits.
    pub experimental_features: ExperimentalSearchFeatures,
}

/// Explicit search semantics used by controlled search entry points.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SearchPolicy {
    parameters: SearchPolicyParameters,
}

impl SearchPolicy {
    /// Exact authoritative v0.1 policy.
    pub const V0_1: Self = Self::new(SearchPolicyParameters {
        alpha_beta: AlphaBetaMode::FullWindowFailSoft,
        transposition: TranspositionPolicy::ClusteredFullKey,
        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,
        aspiration_windows: true,
        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,
        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,
        experimental_features: ExperimentalSearchFeatures::NONE,
    });

    /// Inactive S2-5 candidate: v0.1 semantics plus SEE capture ordering.
    pub const SEE_CAPTURE_ORDERING: Self = Self::new(SearchPolicyParameters {
        alpha_beta: AlphaBetaMode::FullWindowFailSoft,
        transposition: TranspositionPolicy::ClusteredFullKey,
        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,
        aspiration_windows: true,
        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,
        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,
        experimental_features: ExperimentalSearchFeatures::SEE_CAPTURE_ORDERING,
    });

    /// Inactive S2-6 candidate: baseline ordering plus conservative SEE pruning.
    pub const SEE_QUIESCENCE_PRUNING: Self = Self::new(SearchPolicyParameters {
        alpha_beta: AlphaBetaMode::FullWindowFailSoft,
        transposition: TranspositionPolicy::ClusteredFullKey,
        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,
        aspiration_windows: true,
        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,
        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,
        experimental_features: ExperimentalSearchFeatures::SEE_QUIESCENCE_PRUNING,
    });

    /// Inactive S2-6 candidate: SEE pruning followed by bounded delta pruning.
    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self = Self::new(SearchPolicyParameters {
        alpha_beta: AlphaBetaMode::FullWindowFailSoft,
        transposition: TranspositionPolicy::ClusteredFullKey,
        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,
        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,
        aspiration_windows: true,
        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,
        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,
        experimental_features: ExperimentalSearchFeatures::SEE_AND_DELTA_QUIESCENCE_PRUNING,
    });

    /// Constructs explicit typed parameters for subsequent validation.
    #[must_use]
    pub const fn new(parameters: SearchPolicyParameters) -> Self {
        Self { parameters }
    }

    /// Returns every canonical parameter.
    #[must_use]
    pub const fn parameters(self) -> SearchPolicyParameters {
        self.parameters
    }

    /// Returns whether aspiration windows are enabled.
    #[must_use]
    pub const fn aspiration_windows_enabled(self) -> bool {
        self.parameters.aspiration_windows
    }

    /// Returns the configured aspiration half-width.
    #[must_use]
    pub const fn aspiration_half_width_centipawns(self) -> u16 {
        self.parameters.aspiration_half_width_centipawns
    }

    /// Returns the configured tactical-ply guard.
    #[must_use]
    pub const fn maximum_quiescence_ply(self) -> u16 {
        self.parameters.maximum_quiescence_ply
    }

    /// Returns the configured per-line check-extension budget.
    #[must_use]
    pub const fn maximum_check_extensions_per_line(self) -> u16 {
        self.parameters.maximum_check_extensions_per_line
    }

    /// Returns whether the inactive S2-5 SEE ordering candidate is selected.
    #[must_use]
    pub const fn see_capture_ordering_enabled(self) -> bool {
        self.parameters
            .experimental_features
            .contains(ExperimentalSearchFeature::SeeCaptureOrdering)
    }

    /// Returns whether conservative SEE pruning is selected in quiescence.
    #[must_use]
    pub const fn see_quiescence_pruning_enabled(self) -> bool {
        self.parameters
            .experimental_features
            .contains(ExperimentalSearchFeature::SeeQuiescencePruning)
    }

    /// Returns whether bounded delta pruning is selected in quiescence.
    #[must_use]
    pub const fn delta_pruning_enabled(self) -> bool {
        self.parameters
            .experimental_features
            .contains(ExperimentalSearchFeature::DeltaPruning)
    }

    /// Validates supported ranges and rejects not-yet-implemented features.
    pub fn validate(self) -> Result<(), SearchPolicyValidationError> {
        let aspiration_width = self.parameters.aspiration_half_width_centipawns;
        if self.parameters.aspiration_windows {
            if aspiration_width == 0 || aspiration_width > MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS
            {
                return Err(SearchPolicyValidationError::AspirationHalfWidthOutOfRange {
                    enabled: true,
                    value: aspiration_width,
                    maximum: MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
                });
            }
        } else if aspiration_width != 0 {
            return Err(SearchPolicyValidationError::AspirationHalfWidthOutOfRange {
                enabled: false,
                value: aspiration_width,
                maximum: 0,
            });
        }

        let maximum_quiescence_ply = self.parameters.maximum_quiescence_ply;
        if maximum_quiescence_ply == 0 || maximum_quiescence_ply > MAX_MATE_PLY {
            return Err(SearchPolicyValidationError::QuiescenceMaximumOutOfRange {
                value: maximum_quiescence_ply,
                maximum: MAX_MATE_PLY,
            });
        }

        let maximum_check_extensions = self.parameters.maximum_check_extensions_per_line;
        if maximum_check_extensions > MAXIMUM_CHECK_EXTENSIONS_PER_LINE {
            return Err(
                SearchPolicyValidationError::CheckExtensionMaximumOutOfRange {
                    value: maximum_check_extensions,
                    maximum: MAXIMUM_CHECK_EXTENSIONS_PER_LINE,
                },
            );
        }

        if self.delta_pruning_enabled() && !self.see_quiescence_pruning_enabled() {
            return Err(SearchPolicyValidationError::DeltaPruningRequiresSeePruning);
        }
        if let Some(feature) = self
            .parameters
            .experimental_features
            .first_unsupported_enabled()
        {
            return Err(SearchPolicyValidationError::UnsupportedExperimentalFeature { feature });
        }
        Ok(())
    }
}

/// Versioned, identified, checksummed search policy.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SearchPolicySet {
    /// Serialized schema version.
    pub schema_version: u16,
    /// Stable caller-selected policy identifier.
    pub identifier: u64,
    /// Complete typed search policy.
    pub policy: SearchPolicy,
    /// Canonical FNV-1a checksum over schema, identity, and parameters.
    pub checksum: u64,
}

impl SearchPolicySet {
    /// Constructs a checksummed policy set.
    #[must_use]
    pub fn new(identifier: u64, policy: SearchPolicy) -> Self {
        let mut set = Self {
            schema_version: SEARCH_POLICY_SCHEMA_VERSION,
            identifier,
            policy,
            checksum: 0,
        };
        set.checksum = set.computed_checksum();
        set
    }

    /// Constructs serialized parts for subsequent fail-closed validation.
    #[must_use]
    pub const fn from_parts(
        schema_version: u16,
        identifier: u64,
        policy: SearchPolicy,
        checksum: u64,
    ) -> Self {
        Self {
            schema_version,
            identifier,
            policy,
            checksum,
        }
    }

    /// Returns the exact authoritative v0.1 set.
    #[must_use]
    pub fn baseline() -> Self {
        let set = Self::new(V0_1_SEARCH_POLICY_ID, SearchPolicy::V0_1);
        debug_assert_eq!(set.checksum, V0_1_SEARCH_POLICY_CHECKSUM);
        set
    }

    /// Returns the inactive S2-5 SEE capture-ordering candidate.
    #[must_use]
    pub fn see_capture_ordering_candidate() -> Self {
        Self::new(
            SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,
            SearchPolicy::SEE_CAPTURE_ORDERING,
        )
    }

    /// Returns the inactive S2-6 SEE quiescence-pruning candidate.
    #[must_use]
    pub fn see_quiescence_pruning_candidate() -> Self {
        Self::new(
            SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,
            SearchPolicy::SEE_QUIESCENCE_PRUNING,
        )
    }

    /// Returns the inactive S2-6 SEE-plus-delta quiescence candidate.
    #[must_use]
    pub fn see_and_delta_quiescence_pruning_candidate() -> Self {
        Self::new(
            SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,
            SearchPolicy::SEE_AND_DELTA_QUIESCENCE_PRUNING,
        )
    }

    /// Computes the canonical checksum.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let parameters = self.policy.parameters();
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.identifier.to_le_bytes());
        hash = hash_bytes(hash, &[parameters.alpha_beta.code()]);
        hash = hash_bytes(hash, &[parameters.transposition.code()]);
        hash = hash_bytes(hash, &[parameters.move_ordering.code()]);
        hash = hash_bytes(hash, &[parameters.quiescence.code()]);
        hash = hash_bytes(hash, &[u8::from(parameters.aspiration_windows)]);
        hash = hash_bytes(
            hash,
            &parameters.aspiration_half_width_centipawns.to_le_bytes(),
        );
        hash = hash_bytes(hash, &parameters.maximum_quiescence_ply.to_le_bytes());
        hash = hash_bytes(
            hash,
            &parameters.maximum_check_extensions_per_line.to_le_bytes(),
        );
        hash_bytes(hash, &parameters.experimental_features.bits().to_le_bytes())
    }

    /// Validates schema, identity, parameters, and checksum.
    pub fn validate(&self) -> Result<(), SearchPolicyValidationError> {
        if self.schema_version != SEARCH_POLICY_SCHEMA_VERSION {
            return Err(SearchPolicyValidationError::SchemaVersion {
                expected: SEARCH_POLICY_SCHEMA_VERSION,
                found: self.schema_version,
            });
        }
        if self.identifier == 0 {
            return Err(SearchPolicyValidationError::EmptyIdentifier);
        }
        self.policy.validate()?;
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(SearchPolicyValidationError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }
}

/// Fail-closed policy validation error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchPolicyValidationError {
    /// Unsupported serialized schema.
    SchemaVersion { expected: u16, found: u16 },
    /// Zero is not a valid semantic identifier.
    EmptyIdentifier,
    /// Aspiration enablement and width disagree or exceed the bound.
    AspirationHalfWidthOutOfRange {
        enabled: bool,
        value: u16,
        maximum: u16,
    },
    /// Quiescence guard is zero or exceeds the mate-score domain.
    QuiescenceMaximumOutOfRange { value: u16, maximum: u16 },
    /// Check-extension budget exceeds the bounded supported limit.
    CheckExtensionMaximumOutOfRange { value: u16, maximum: u16 },
    /// Serialized feature bits contain an unknown assignment.
    UnknownExperimentalFeatureBits { bits: u64 },
    /// Delta pruning was enabled without its required SEE-pruning predecessor.
    DeltaPruningRequiresSeePruning,
    /// A known future feature was enabled before its implementation task.
    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },
    /// Serialized checksum does not match the canonical parameters.
    ChecksumMismatch { expected: u64, found: u64 },
}

impl fmt::Display for SearchPolicyValidationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::SchemaVersion { expected, found } => {
                write!(formatter, "expected search-policy schema {expected}, found {found}")
            }
            Self::EmptyIdentifier => formatter.write_str("search-policy identifier must be non-zero"),
            Self::AspirationHalfWidthOutOfRange {
                enabled,
                value,
                maximum,
            } => write!(
                formatter,
                "aspiration enabled={enabled} requires half-width in the supported range, found {value} with maximum {maximum}"
            ),
            Self::QuiescenceMaximumOutOfRange { value, maximum } => write!(
                formatter,
                "maximum quiescence ply must be between 1 and {maximum}, found {value}"
            ),
            Self::CheckExtensionMaximumOutOfRange { value, maximum } => write!(
                formatter,
                "maximum check extensions per line must not exceed {maximum}, found {value}"
            ),
            Self::UnknownExperimentalFeatureBits { bits } => {
                write!(formatter, "unknown experimental search-policy bits {bits:#018x}")
            }
            Self::DeltaPruningRequiresSeePruning => formatter.write_str(
                "delta pruning requires SEE quiescence pruning in the same policy",
            ),
            Self::UnsupportedExperimentalFeature { feature } => write!(
                formatter,
                "experimental search feature {} is not implemented and cannot be enabled",
                feature.name()
            ),
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "search-policy checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
        }
    }
}

impl std::error::Error for SearchPolicyValidationError {}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use super::{
        ExperimentalSearchFeatures, SearchPolicy, SearchPolicyParameters, SearchPolicySet,
        SearchPolicyValidationError, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,
        SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,
        V0_1_SEARCH_POLICY_CHECKSUM,
    };

    #[test]
    fn v0_1_policy_identity_is_stable_and_valid() {
        let set = SearchPolicySet::baseline();
        assert_eq!(set.checksum, V0_1_SEARCH_POLICY_CHECKSUM);
        assert_eq!(set.computed_checksum(), set.checksum);
        assert_eq!(set.validate(), Ok(()));
    }

    #[test]
    fn see_capture_ordering_candidate_is_valid_distinct_and_inactive_by_default() {
        let baseline = SearchPolicySet::baseline();
        let candidate = SearchPolicySet::see_capture_ordering_candidate();
        assert_eq!(candidate.identifier, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID);
        assert_eq!(candidate.validate(), Ok(()));
        assert!(candidate.policy.see_capture_ordering_enabled());
        assert!(!baseline.policy.see_capture_ordering_enabled());
        assert_ne!(candidate.identifier, baseline.identifier);
        assert_ne!(candidate.checksum, baseline.checksum);
    }

    #[test]
    fn s2_6_quiescence_candidates_are_distinct_valid_and_inactive_by_default() {
        let baseline = SearchPolicySet::baseline();
        let see = SearchPolicySet::see_quiescence_pruning_candidate();
        let delta = SearchPolicySet::see_and_delta_quiescence_pruning_candidate();
        assert_eq!(see.identifier, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID);
        assert_eq!(
            delta.identifier,
            SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID
        );
        assert_eq!(see.validate(), Ok(()));
        assert_eq!(delta.validate(), Ok(()));
        assert!(!baseline.policy.see_quiescence_pruning_enabled());
        assert!(see.policy.see_quiescence_pruning_enabled());
        assert!(!see.policy.delta_pruning_enabled());
        assert!(delta.policy.see_quiescence_pruning_enabled());
        assert!(delta.policy.delta_pruning_enabled());
        assert_ne!(baseline.checksum, see.checksum);
        assert_ne!(see.checksum, delta.checksum);
    }

    #[test]
    fn delta_pruning_without_see_pruning_fails_loudly() {
        let mut parameters = SearchPolicy::V0_1.parameters();
        parameters.experimental_features =
            ExperimentalSearchFeatures::from_bits(1 << 2).expect("delta feature bit is assigned");
        let invalid = SearchPolicySet::new(0x5332_3644_454c_5441, SearchPolicy::new(parameters));
        assert_eq!(
            invalid.validate(),
            Err(SearchPolicyValidationError::DeltaPruningRequiresSeePruning)
        );
    }

    #[test]
    fn semantic_parameter_changes_change_the_checksum() {
        let baseline = SearchPolicySet::baseline();
        let mut parameters = SearchPolicy::V0_1.parameters();
        parameters.aspiration_half_width_centipawns += 1;
        let changed = SearchPolicySet::new(baseline.identifier, SearchPolicy::new(parameters));
        assert_eq!(changed.validate(), Ok(()));
        assert_ne!(changed.checksum, baseline.checksum);
    }

    #[test]
    fn corruption_and_unimplemented_features_fail_loudly() {
        let baseline = SearchPolicySet::baseline();
        let corrupt = SearchPolicySet::from_parts(
            baseline.schema_version,
            baseline.identifier,
            baseline.policy,
            baseline.checksum ^ 1,
        );
        assert!(matches!(
            corrupt.validate(),
            Err(SearchPolicyValidationError::ChecksumMismatch { .. })
        ));

        let mut parameters: SearchPolicyParameters = SearchPolicy::V0_1.parameters();
        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 3)
            .expect("assigned feature bit is recognized");
        let unsupported = SearchPolicySet::new(1, SearchPolicy::new(parameters));
        assert!(matches!(
            unsupported.validate(),
            Err(SearchPolicyValidationError::UnsupportedExperimentalFeature { .. })
        ));
    }
}
