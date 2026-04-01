#!/usr/bin/env python3
"""Fix en passant coordinate errors"""

def fix_en_passant_tests():
    filepath = "tests/test_special_moves.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix test_en_passant_black_captures_white_pawn
    # White pawn should move from e2 (ROW_2) to e4 (ROW_4), not e3 (ROW_3)
    # This sets en_passant_target to e3 (ROW_3)
    content = content.replace(
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_3, col=COL_E)
            )
        )
        is True)
    assert board.en_passant_target == ConstantSquare(row=ROW_3, col=COL_E)''',
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_4, col=COL_E)
            )
        )
        is True)
    assert board.en_passant_target == ConstantSquare(row=ROW_3, col=COL_E)'''
    )
    
    # Fix test_en_passant_expires_after_one_turn
    # Black pawn should move from d7 (ROW_7) to d5 (ROW_5)
    # White pawn should move from e2 (ROW_2) to e6 (ROW_6) - en passant capture
    content = content.replace(
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
            )
        )
        is True)
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_A), ConstantSquare(row=ROW_2, col=COL_B)
        )
        is True)''',
        '''assert (
            board.make_move(
                ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
            )
        )
        is True)
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_A), ConstantSquare(row=ROW_2, col=COL_B)
        )
        is True)
    
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)
        )
        is True)'''
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_en_passant_tests()
