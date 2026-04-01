#!/usr/bin/env python3
"""Fix remaining en passant coordinate errors"""

def fix_en_passant_tests():
    filepath = "tests/test_special_moves.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix the en passant capture move - should be to ROW_3, not ROW_6
    # White pawn at e2 (ROW_2) captures en passant at d3 (ROW_3), not d5 (ROW_6)
    content = content.replace(
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)
            )
        )
        is True)''',
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_3, col=COL_D)
            )
        )
        is True)'''
    )
    
    # Fix test_en_passant_black_captures_white_pawn - same issue
    # Black pawn at f7 (ROW_7) captures at e3 (ROW_3), not e3 from ROW_1
    content = content.replace(
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_1, col=COL_F), ConstantSquare(row=ROW_3, col=COL_E)
            )
        )
        is True)

    # Verify: black pawn on e3 (row 3), white pawn removed from e3 (row 3)
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_3, col=COL_E)) == PieceType.PAWN
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_E)) is None''',
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_3, col=COL_E)
            )
        )
        is True)

    # Verify: black pawn on e3 (row 3), white pawn removed from e3 (row 3)
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_3, col=COL_E)) == PieceType.PAWN
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_E)) is None'''
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_en_passant_tests()
