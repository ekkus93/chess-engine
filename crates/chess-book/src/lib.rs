#![forbid(unsafe_code)]
//! Platform-neutral opening-book contracts for engine adapters.
//!
//! This crate defines only value types and dependency-injection traits. It
//! performs no filesystem, asset, environment, network, or process-global
//! discovery. Platform adapters may implement [`BookProvider`] with whatever
//! explicit I/O policy they require, while [`OpeningBook`] remains a pure query
//! over a caller-supplied validated [`Position`].

use std::error::Error;

use chess_core::{Move, Position};

/// One weighted move returned by an opening book.
///
/// Metadata is deliberately generic because a Polyglot backend, a project-
/// specific indexed backend, and an Android asset backend may expose different
/// diagnostics without changing the common move-and-weight contract.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BookMove<M = ()> {
    chess_move: Move,
    weight: u32,
    metadata: Option<M>,
}

impl BookMove<()> {
    /// Creates a book move without backend metadata.
    #[must_use]
    pub const fn new(chess_move: Move, weight: u32) -> Self {
        Self {
            chess_move,
            weight,
            metadata: None,
        }
    }
}

impl<M> BookMove<M> {
    /// Creates a book move with backend-defined metadata.
    #[must_use]
    pub const fn with_metadata(chess_move: Move, weight: u32, metadata: M) -> Self {
        Self {
            chess_move,
            weight,
            metadata: Some(metadata),
        }
    }

    /// Creates a book move from its complete format-neutral parts.
    #[must_use]
    pub const fn from_parts(chess_move: Move, weight: u32, metadata: Option<M>) -> Self {
        Self {
            chess_move,
            weight,
            metadata,
        }
    }

    /// Returns the engine move identity supplied by the backend.
    #[must_use]
    pub const fn chess_move(&self) -> Move {
        self.chess_move
    }

    /// Returns the backend-supplied relative weight.
    #[must_use]
    pub const fn weight(&self) -> u32 {
        self.weight
    }

    /// Returns optional backend metadata without transferring ownership.
    #[must_use]
    pub const fn metadata(&self) -> Option<&M> {
        match &self.metadata {
            Some(metadata) => Some(metadata),
            None => None,
        }
    }

    /// Decomposes this value into its format-neutral parts.
    #[must_use]
    pub fn into_parts(self) -> (Move, u32, Option<M>) {
        (self.chess_move, self.weight, self.metadata)
    }
}

/// A loaded, queryable opening book supplied to an engine adapter.
///
/// The trait is intentionally independent of storage. Implementations receive
/// the complete validated position and return every candidate recorded for
/// that position. An empty vector means that the book has no entry. Backend
/// corruption, unsupported formats, and other failures must be returned as a
/// typed error rather than converted into an empty result.
///
/// Candidate legality validation and selection policy belong to later adapter
/// integration stages; this abstraction does not silently filter or select a
/// move.
pub trait OpeningBook: Send + Sync {
    /// Optional backend-defined diagnostics associated with each candidate.
    type Metadata: Send + Sync + 'static;

    /// Typed lookup failure returned without fallback or suppression.
    type Error: Error + Send + Sync + 'static;

    /// Returns all book candidates for `position`.
    fn candidates(
        &self,
        position: &Position,
    ) -> Result<Vec<BookMove<Self::Metadata>>, Self::Error>;
}

/// Explicit adapter-owned construction boundary for an opening book.
///
/// Providers may perform platform-specific I/O, but they must be passed to the
/// adapter explicitly. This contract defines no default path, environment
/// variable, bundled asset, current-directory lookup, or other auto-discovery.
/// Returning `Ok(None)` means that opening-book support is intentionally not
/// configured for the current adapter instance.
pub trait BookProvider: Send + Sync {
    /// Loaded book type returned by this provider.
    type Book: OpeningBook;

    /// Typed provider or loading failure.
    type Error: Error + Send + Sync + 'static;

    /// Explicitly constructs or obtains the configured book.
    fn open(&self) -> Result<Option<Self::Book>, Self::Error>;
}

#[cfg(test)]
mod tests {
    use std::fmt;

    use chess_core::{Color, MoveKind, Square};

    use super::{BookMove, BookProvider, OpeningBook, Position};

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    struct TestError(&'static str);

    impl fmt::Display for TestError {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str(self.0)
        }
    }

    impl std::error::Error for TestError {}

    fn square(value: &str) -> Square {
        value.parse().expect("test square is valid")
    }

    fn e2e4() -> chess_core::Move {
        chess_core::Move::new(
            square("e2"),
            square("e4"),
            MoveKind::DoublePawnPush,
        )
    }

    #[derive(Clone, Copy, Debug)]
    struct FakeBook;

    impl OpeningBook for FakeBook {
        type Metadata = &'static str;
        type Error = TestError;

        fn candidates(
            &self,
            position: &Position,
        ) -> Result<Vec<BookMove<Self::Metadata>>, Self::Error> {
            if position.side_to_move() != Color::White {
                return Err(TestError("unexpected side to move"));
            }
            Ok(vec![BookMove::with_metadata(e2e4(), 42, "main line")])
        }
    }

    #[derive(Clone, Copy, Debug)]
    struct FailingBook;

    impl OpeningBook for FailingBook {
        type Metadata = ();
        type Error = TestError;

        fn candidates(
            &self,
            _position: &Position,
        ) -> Result<Vec<BookMove<Self::Metadata>>, Self::Error> {
            Err(TestError("corrupt book"))
        }
    }

    #[derive(Clone, Copy, Debug)]
    struct FakeProvider {
        enabled: bool,
    }

    impl BookProvider for FakeProvider {
        type Book = FakeBook;
        type Error = TestError;

        fn open(&self) -> Result<Option<Self::Book>, Self::Error> {
            Ok(self.enabled.then_some(FakeBook))
        }
    }

    #[test]
    fn book_move_preserves_move_weight_and_optional_metadata() {
        let plain = BookMove::new(e2e4(), 7);
        assert_eq!(plain.chess_move(), e2e4());
        assert_eq!(plain.weight(), 7);
        assert_eq!(plain.metadata(), None);

        let annotated = BookMove::with_metadata(e2e4(), 11, "primary");
        assert_eq!(annotated.metadata(), Some(&"primary"));
        assert_eq!(annotated.into_parts(), (e2e4(), 11, Some("primary")));
    }

    #[test]
    fn opening_book_is_an_adapter_injectable_position_query() {
        let book: &dyn OpeningBook<Metadata = &'static str, Error = TestError> = &FakeBook;
        let candidates = book
            .candidates(&Position::starting())
            .expect("fake lookup succeeds");

        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].chess_move(), e2e4());
        assert_eq!(candidates[0].weight(), 42);
        assert_eq!(candidates[0].metadata(), Some(&"main line"));
    }

    #[test]
    fn provider_requires_explicit_configuration_and_can_return_no_book() {
        let enabled: &dyn BookProvider<Book = FakeBook, Error = TestError> =
            &FakeProvider { enabled: true };
        assert!(enabled.open().expect("provider succeeds").is_some());

        let disabled = FakeProvider { enabled: false };
        assert!(disabled.open().expect("provider succeeds").is_none());
    }

    #[test]
    fn lookup_errors_remain_typed_and_fail_visible() {
        let error = FailingBook
            .candidates(&Position::starting())
            .expect_err("failure must not become an empty candidate list");
        assert_eq!(error, TestError("corrupt book"));
    }
}
