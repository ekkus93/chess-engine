use chess_search::{EvaluationWeightSet, SearchPolicySet};

use super::ToolError;

/// Current engine-variant identity schema.
pub const ENGINE_VARIANT_SCHEMA_VERSION: u16 = 1;
/// Largest supported transposition-table configuration recorded in an identity.
pub const MAXIMUM_VARIANT_TRANSPOSITION_TABLE_MEBIBYTES: u64 = 65_536;

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Schema, identifier, and checksum for one semantic engine component.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct SemanticComponentIdentity {
    /// Component schema version.
    pub schema_version: u16,
    /// Stable semantic identifier.
    pub identifier: u64,
    /// Canonical semantic checksum.
    pub checksum: u64,
}

impl SemanticComponentIdentity {
    fn validate(self, component: &str) -> Result<(), ToolError> {
        if self.schema_version == 0 || self.identifier == 0 || self.checksum == 0 {
            return Err(ToolError::new(format!(
                "{component} identity requires non-zero schema, identifier, and checksum"
            )));
        }
        Ok(())
    }
}

/// Explicit identity of an optional externally supplied capability.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OptionalCapabilityIdentity {
    /// Capability is disabled and supplies no data.
    Disabled,
    /// Capability is enabled with exact implementation and data identities.
    Enabled {
        /// Stable implementation identifier.
        implementation_identifier: u64,
        /// Stable data-set identifier.
        data_identifier: u64,
        /// Canonical data/implementation checksum.
        checksum: u64,
    },
}

impl OptionalCapabilityIdentity {
    fn validate(self, capability: &str) -> Result<(), ToolError> {
        match self {
            Self::Disabled => Ok(()),
            Self::Enabled {
                implementation_identifier,
                data_identifier,
                checksum,
            } if implementation_identifier != 0 && data_identifier != 0 && checksum != 0 => Ok(()),
            Self::Enabled { .. } => Err(ToolError::new(format!(
                "enabled {capability} identity requires non-zero implementation, data, and checksum values"
            ))),
        }
    }

    fn hash(self, mut hash: u64) -> u64 {
        match self {
            Self::Disabled => hash_bytes(hash, &[0]),
            Self::Enabled {
                implementation_identifier,
                data_identifier,
                checksum,
            } => {
                hash = hash_bytes(hash, &[1]);
                hash = hash_bytes(hash, &implementation_identifier.to_le_bytes());
                hash = hash_bytes(hash, &data_identifier.to_le_bytes());
                hash_bytes(hash, &checksum.to_le_bytes())
            }
        }
    }
}

/// Caller-owned non-semantic provenance required to identify one engine build and invocation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineVariantDescriptor {
    /// Stable caller-selected complete-variant identifier.
    pub identifier: u64,
    /// Exact 20-byte source commit.
    pub source_commit: [u8; 20],
    /// Semantic engine/package version.
    pub engine_version: String,
    /// Opening-book state and data identity.
    pub opening_book: OptionalCapabilityIdentity,
    /// Tablebase state and data identity.
    pub tablebase: OptionalCapabilityIdentity,
    /// Exact transposition-table size.
    pub transposition_table_mebibytes: u64,
    /// Exact target/toolchain/profile/features build identity.
    pub build_identity: String,
    /// Exact command or equivalent invocation.
    pub exact_invocation: String,
}

impl EngineVariantDescriptor {
    fn validate(&self) -> Result<(), ToolError> {
        if self.identifier == 0 {
            return Err(ToolError::new("engine-variant identifier must be non-zero"));
        }
        if self.source_commit.iter().all(|byte| *byte == 0) {
            return Err(ToolError::new(
                "engine-variant source commit must be recorded",
            ));
        }
        if self.engine_version.trim().is_empty()
            || self.build_identity.trim().is_empty()
            || self.exact_invocation.trim().is_empty()
        {
            return Err(ToolError::new(
                "engine version, build identity, and exact invocation must be non-empty",
            ));
        }
        if self.transposition_table_mebibytes == 0
            || self.transposition_table_mebibytes
                > MAXIMUM_VARIANT_TRANSPOSITION_TABLE_MEBIBYTES
        {
            return Err(ToolError::new(format!(
                "transposition-table size must be between 1 and {MAXIMUM_VARIANT_TRANSPOSITION_TABLE_MEBIBYTES} MiB"
            )));
        }
        self.opening_book.validate("opening-book")?;
        self.tablebase.validate("tablebase")?;
        Ok(())
    }
}

/// Complete versioned identity for a reproducible engine variant.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct EngineVariantIdentity {
    schema_version: u16,
    identifier: u64,
    source_commit: [u8; 20],
    engine_version: String,
    search_policy: SemanticComponentIdentity,
    evaluation_weights: SemanticComponentIdentity,
    opening_book: OptionalCapabilityIdentity,
    tablebase: OptionalCapabilityIdentity,
    transposition_table_mebibytes: u64,
    build_identity: String,
    exact_invocation: String,
    checksum: u64,
}

impl EngineVariantIdentity {
    /// Constructs and validates a complete identity from exact component identities.
    pub fn new(
        descriptor: EngineVariantDescriptor,
        search_policy: &SearchPolicySet,
        evaluation_weights: &EvaluationWeightSet,
    ) -> Result<Self, ToolError> {
        descriptor.validate()?;
        search_policy
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))?;
        evaluation_weights
            .validate()
            .map_err(|error| ToolError::new(error.to_string()))?;

        let mut identity = Self {
            schema_version: ENGINE_VARIANT_SCHEMA_VERSION,
            identifier: descriptor.identifier,
            source_commit: descriptor.source_commit,
            engine_version: descriptor.engine_version,
            search_policy: SemanticComponentIdentity {
                schema_version: search_policy.schema_version,
                identifier: search_policy.identifier,
                checksum: search_policy.checksum,
            },
            evaluation_weights: SemanticComponentIdentity {
                schema_version: evaluation_weights.schema_version,
                identifier: evaluation_weights.identifier,
                checksum: evaluation_weights.checksum,
            },
            opening_book: descriptor.opening_book,
            tablebase: descriptor.tablebase,
            transposition_table_mebibytes: descriptor.transposition_table_mebibytes,
            build_identity: descriptor.build_identity,
            exact_invocation: descriptor.exact_invocation,
            checksum: 0,
        };
        identity.checksum = identity.computed_checksum();
        identity.validate()?;
        Ok(identity)
    }

    /// Returns the variant schema.
    #[must_use]
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }

    /// Returns the stable complete-variant identifier.
    #[must_use]
    pub const fn identifier(&self) -> u64 {
        self.identifier
    }

    /// Returns the exact source commit.
    #[must_use]
    pub const fn source_commit(&self) -> [u8; 20] {
        self.source_commit
    }

    /// Returns the semantic engine version.
    #[must_use]
    pub fn engine_version(&self) -> &str {
        &self.engine_version
    }

    /// Returns the search-policy identity independently from weights.
    #[must_use]
    pub const fn search_policy_identity(&self) -> SemanticComponentIdentity {
        self.search_policy
    }

    /// Returns the evaluation-weight identity independently from policy.
    #[must_use]
    pub const fn evaluation_weight_identity(&self) -> SemanticComponentIdentity {
        self.evaluation_weights
    }

    /// Returns the explicit opening-book identity.
    #[must_use]
    pub const fn opening_book_identity(&self) -> OptionalCapabilityIdentity {
        self.opening_book
    }

    /// Returns the explicit tablebase identity.
    #[must_use]
    pub const fn tablebase_identity(&self) -> OptionalCapabilityIdentity {
        self.tablebase
    }

    /// Returns the exact TT size.
    #[must_use]
    pub const fn transposition_table_mebibytes(&self) -> u64 {
        self.transposition_table_mebibytes
    }

    /// Returns the exact build identity.
    #[must_use]
    pub fn build_identity(&self) -> &str {
        &self.build_identity
    }

    /// Returns the exact invocation.
    #[must_use]
    pub fn exact_invocation(&self) -> &str {
        &self.exact_invocation
    }

    /// Returns the canonical complete-variant checksum.
    #[must_use]
    pub const fn checksum(&self) -> u64 {
        self.checksum
    }

    /// Recomputes the complete-variant checksum.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.identifier.to_le_bytes());
        hash = hash_bytes(hash, &self.source_commit);
        hash = hash_string(hash, &self.engine_version);
        hash = hash_component(hash, self.search_policy);
        hash = hash_component(hash, self.evaluation_weights);
        hash = self.opening_book.hash(hash);
        hash = self.tablebase.hash(hash);
        hash = hash_bytes(hash, &self.transposition_table_mebibytes.to_le_bytes());
        hash = hash_string(hash, &self.build_identity);
        hash_string(hash, &self.exact_invocation)
    }

    /// Validates all required fields and checksum.
    pub fn validate(&self) -> Result<(), ToolError> {
        if self.schema_version != ENGINE_VARIANT_SCHEMA_VERSION {
            return Err(ToolError::new(format!(
                "expected engine-variant schema {ENGINE_VARIANT_SCHEMA_VERSION}, found {}",
                self.schema_version
            )));
        }
        let descriptor = EngineVariantDescriptor {
            identifier: self.identifier,
            source_commit: self.source_commit,
            engine_version: self.engine_version.clone(),
            opening_book: self.opening_book,
            tablebase: self.tablebase,
            transposition_table_mebibytes: self.transposition_table_mebibytes,
            build_identity: self.build_identity.clone(),
            exact_invocation: self.exact_invocation.clone(),
        };
        descriptor.validate()?;
        self.search_policy.validate("search-policy")?;
        self.evaluation_weights.validate("evaluation-weight")?;
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(ToolError::new(format!(
                "engine-variant checksum mismatch: expected {expected:016x}, found {:016x}",
                self.checksum
            )));
        }
        Ok(())
    }
}

fn hash_component(mut hash: u64, identity: SemanticComponentIdentity) -> u64 {
    hash = hash_bytes(hash, &identity.schema_version.to_le_bytes());
    hash = hash_bytes(hash, &identity.identifier.to_le_bytes());
    hash_bytes(hash, &identity.checksum.to_le_bytes())
}

fn hash_string(mut hash: u64, value: &str) -> u64 {
    hash = hash_bytes(hash, &(value.len() as u64).to_le_bytes());
    hash_bytes(hash, value.as_bytes())
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use chess_core::PieceKind;
    use chess_search::{
        EvaluationWeightSet, EvaluationWeights, SearchPolicy, SearchPolicySet,
    };

    use super::{
        EngineVariantDescriptor, EngineVariantIdentity, OptionalCapabilityIdentity,
    };

    fn descriptor() -> EngineVariantDescriptor {
        EngineVariantDescriptor {
            identifier: 0x5641_5249_414e_5431,
            source_commit: [0x11; 20],
            engine_version: "0.1.0".to_owned(),
            opening_book: OptionalCapabilityIdentity::Disabled,
            tablebase: OptionalCapabilityIdentity::Disabled,
            transposition_table_mebibytes: 1,
            build_identity: "rustc-1.97.1|x86_64-unknown-linux-gnu|release|default"
                .to_owned(),
            exact_invocation: "chess-tools variant-smoke".to_owned(),
        }
    }

    fn identity(
        descriptor: EngineVariantDescriptor,
        policy: &SearchPolicySet,
        weights: &EvaluationWeightSet,
    ) -> EngineVariantIdentity {
        EngineVariantIdentity::new(descriptor, policy, weights)
            .expect("complete variant identity validates")
    }

    #[test]
    fn policy_and_weight_identities_are_distinct_components() {
        let policy = SearchPolicySet::baseline();
        let weights = EvaluationWeightSet::baseline();
        let variant = identity(descriptor(), &policy, &weights);
        assert_eq!(variant.search_policy_identity().identifier, policy.identifier);
        assert_eq!(variant.search_policy_identity().checksum, policy.checksum);
        assert_eq!(
            variant.evaluation_weight_identity().identifier,
            weights.identifier
        );
        assert_eq!(
            variant.evaluation_weight_identity().checksum,
            weights.checksum
        );
        assert_eq!(variant.validate(), Ok(()));
        assert_eq!(variant.computed_checksum(), variant.checksum());
    }

    #[test]
    fn every_behavior_or_provenance_change_changes_variant_identity() {
        let policy = SearchPolicySet::baseline();
        let weights = EvaluationWeightSet::baseline();
        let baseline = identity(descriptor(), &policy, &weights);
        let mut checksums = Vec::new();

        let mut changed_descriptor = descriptor();
        changed_descriptor.source_commit[0] ^= 1;
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.engine_version = "0.1.1".to_owned();
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut parameters = SearchPolicy::V0_1.parameters();
        parameters.aspiration_half_width_centipawns += 1;
        let changed_policy = SearchPolicySet::new(policy.identifier, SearchPolicy::new(parameters));
        checksums.push(identity(descriptor(), &changed_policy, &weights).checksum());

        let mut changed_weights: EvaluationWeights = weights.weights;
        changed_weights.material[PieceKind::Pawn.index()].middlegame += 1;
        let changed_weights = EvaluationWeightSet::new(weights.identifier, changed_weights);
        changed_weights.validate().expect("small material change remains valid");
        checksums.push(identity(descriptor(), &policy, &changed_weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.opening_book = OptionalCapabilityIdentity::Enabled {
            implementation_identifier: 1,
            data_identifier: 2,
            checksum: 3,
        };
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.tablebase = OptionalCapabilityIdentity::Enabled {
            implementation_identifier: 4,
            data_identifier: 5,
            checksum: 6,
        };
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.transposition_table_mebibytes = 2;
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.build_identity.push_str("|feature-x");
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        let mut changed_descriptor = descriptor();
        changed_descriptor.exact_invocation.push_str(" --nodes 10");
        checksums.push(identity(changed_descriptor, &policy, &weights).checksum());

        assert!(checksums
            .into_iter()
            .all(|checksum| checksum != baseline.checksum()));
    }

    #[test]
    fn incomplete_or_implicit_identity_is_rejected() {
        let policy = SearchPolicySet::baseline();
        let weights = EvaluationWeightSet::baseline();
        let mut invalid = descriptor();
        invalid.source_commit = [0; 20];
        assert!(EngineVariantIdentity::new(invalid, &policy, &weights).is_err());

        let mut invalid = descriptor();
        invalid.exact_invocation.clear();
        assert!(EngineVariantIdentity::new(invalid, &policy, &weights).is_err());

        let mut invalid = descriptor();
        invalid.opening_book = OptionalCapabilityIdentity::Enabled {
            implementation_identifier: 0,
            data_identifier: 1,
            checksum: 1,
        };
        assert!(EngineVariantIdentity::new(invalid, &policy, &weights).is_err());
    }
}
