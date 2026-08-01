    use crate::{CastleSide, CastlingRights, Color, Piece, PieceKind, Square};

    use super::{Position, PositionBuildError, PositionBuilder, PositionInvariantError};

    fn square(value: &str) -> Square {
        value.parse().expect("test square is valid")
    }

    fn kings_only_builder() -> PositionBuilder {
        let mut builder = PositionBuilder::empty();
        builder
            .place_piece(
                square("e1"),
                Piece::new(Color::White, PieceKind::King),
            )
            .expect("white king square is empty");
        builder
            .place_piece(
                square("e8"),
                Piece::new(Color::Black, PieceKind::King),
            )
            .expect("black king square is empty");
        builder
    }

    #[test]
    fn starting_position_has_expected_state_and_invariants() {
        let position = Position::starting();
        assert_eq!(position.validate_invariants(), Ok(()));
        assert_eq!(position.side_to_move(), Color::White);
        assert_eq!(position.castling_rights(), CastlingRights::ALL);
        assert_eq!(position.en_passant(), None);
        assert_eq!(position.halfmove_clock().get(), 0);
        assert_eq!(position.fullmove_number().get(), 1);
        assert_eq!(position.zobrist(), 0);
        assert_eq!(position.occupancy(Color::White).count(), 16);
        assert_eq!(position.occupancy(Color::Black).count(), 16);
        assert_eq!(position.all_occupancy().count(), 32);
        assert_eq!(position.king_square(Color::White), square("e1"));
        assert_eq!(position.king_square(Color::Black), square("e8"));
        assert_eq!(
            position.piece_at(square("a8")),
            Some(Piece::new(Color::Black, PieceKind::Rook))
        );
        assert_eq!(
            position.piece_at(square("d1")),
            Some(Piece::new(Color::White, PieceKind::Queen))
        );
        assert_eq!(position.piece_at(square("e4")), None);
    }

    #[test]
    fn playable_builder_requires_exactly_one_king_per_color() {
        let missing = PositionBuilder::empty().build_playable();
        assert_eq!(
            missing,
            Err(PositionBuildError::MissingKing {
                color: Color::White
            })
        );

        let mut multiple = kings_only_builder();
        multiple
            .place_piece(
                square("d1"),
                Piece::new(Color::White, PieceKind::King),
            )
            .expect("second white king uses an empty square");
        assert_eq!(
            multiple.build_playable(),
            Err(PositionBuildError::MultipleKings {
                color: Color::White,
                count: 2
            })
        );
    }

    #[test]
    fn duplicate_builder_placement_is_fail_loud_and_non_mutating() {
        let mut builder = PositionBuilder::empty();
        let square = square("e1");
        let king = Piece::new(Color::White, PieceKind::King);
        builder
            .place_piece(square, king)
            .expect("first placement succeeds");
        let snapshot = builder.clone();
        assert_eq!(
            builder.place_piece(square, Piece::new(Color::White, PieceKind::Queen)),
            Err(PositionBuildError::OccupiedSquare { square })
        );
        assert_eq!(builder, snapshot);
    }

    #[test]
    fn metadata_and_en_passant_invariants_are_preserved() {
        let builder = kings_only_builder()
            .with_side_to_move(Color::Black)
            .with_castling_rights(
                CastlingRights::NONE.with(Color::White, CastleSide::QueenSide),
            )
            .with_en_passant(Some(square("e3")))
            .with_halfmove_clock(crate::HalfmoveClock::new(17))
            .with_fullmove_number(crate::FullmoveNumber::new(42).expect("42 is nonzero"))
            .with_zobrist(1234);
        let position = builder.build_playable().expect("metadata is valid");
        assert_eq!(position.validate_invariants(), Ok(()));
        assert_eq!(position.side_to_move(), Color::Black);
        assert_eq!(position.en_passant(), Some(square("e3")));
        assert_eq!(position.halfmove_clock().get(), 17);
        assert_eq!(position.fullmove_number().get(), 42);
        assert_eq!(position.zobrist(), 1234);
        assert!(position
            .castling_rights()
            .contains(Color::White, CastleSide::QueenSide));
    }

    #[test]
    fn invalid_en_passant_metadata_is_rejected() {
        let wrong_rank = kings_only_builder()
            .with_side_to_move(Color::Black)
            .with_en_passant(Some(square("e6")))
            .build_playable();
        assert_eq!(
            wrong_rank,
            Err(PositionBuildError::Invariant(
                PositionInvariantError::InvalidEnPassantRank {
                    side_to_move: Color::Black,
                    square: square("e6")
                }
            ))
        );

        let mut occupied = kings_only_builder()
            .with_side_to_move(Color::Black)
            .with_en_passant(Some(square("e3")));
        occupied
            .place_piece(
                square("e3"),
                Piece::new(Color::White, PieceKind::Pawn),
            )
            .expect("target square starts empty");
        assert_eq!(
            occupied.build_playable(),
            Err(PositionBuildError::Invariant(
                PositionInvariantError::OccupiedEnPassantSquare {
                    square: square("e3")
                }
            ))
        );
    }

    #[test]
    fn internal_editor_updates_all_redundant_structures() {
        let mut position = kings_only_builder().build_playable().expect("kings are valid");
        let knight = Piece::new(Color::White, PieceKind::Knight);
        position
            .editor()
            .add_piece(square("b1"), knight)
            .expect("b1 is empty");
        assert_eq!(position.validate_invariants(), Ok(()));
        assert!(position
            .piece_bitboard(Color::White, PieceKind::Knight)
            .contains(square("b1")));

        position
            .editor()
            .move_piece(square("b1"), square("c3"))
            .expect("c3 is empty");
        assert_eq!(position.validate_invariants(), Ok(()));
        assert_eq!(position.piece_at(square("b1")), None);
        assert_eq!(position.piece_at(square("c3")), Some(knight));

        let removed = position
            .editor()
            .remove_piece(square("c3"))
            .expect("c3 contains the knight");
        assert_eq!(removed, knight);
        assert_eq!(position.validate_invariants(), Ok(()));
        assert_eq!(position.all_occupancy().count(), 2);

        position
            .editor()
            .move_piece(square("e1"), square("f1"))
            .expect("f1 is empty");
        assert_eq!(position.validate_invariants(), Ok(()));
        assert_eq!(position.king_square(Color::White), square("f1"));
    }

    #[test]
    fn failed_internal_edits_do_not_change_logical_state() {
        let mut position = kings_only_builder().build_playable().expect("kings are valid");
        let snapshot = position.clone();
        assert!(position
            .editor()
            .remove_piece(square("e1"))
            .is_err());
        assert_eq!(position, snapshot);

        assert!(position
            .editor()
            .move_piece(square("a1"), square("a2"))
            .is_err());
        assert_eq!(position, snapshot);

        assert!(position
            .editor()
            .move_piece(square("e1"), square("e8"))
            .is_err());
        assert_eq!(position, snapshot);
    }

    #[test]
    fn clone_is_a_logical_snapshot_not_a_search_policy() {
        let position = Position::starting();
        let snapshot = position.clone();
        assert_eq!(snapshot, position);
        assert_eq!(snapshot.validate_invariants(), Ok(()));
    }