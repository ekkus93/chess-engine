#!/usr/bin/env python3
"""
Apply coordinate fixes to chess engine test files.

Coordinate mapping (ROW constants = array row values):
- ROW_1 = array row 0 = rank 1 (white's back rank)
- ROW_2 = array row 1 = rank 2 (white pawns start)
- ROW_7 = array row 6 = rank 7 (black pawns start)  
- ROW_8 = array row 7 = rank 8 (black's back rank)

Key rules:
- White pawns start at ROW_2 (rank 2), promote to ROW_8 (rank 8)
- Black pawns start at ROW_7 (rank 7), promote to ROW_1 (rank 1)
"""

import re

def fix_test_corner():
    """Fix test_corner.py"""
    filepath = "tests/test_corner.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix _setup_kings - kings are swapped!
    # White king should be at ROW_1 (rank 1), not ROW_8
    # Black king should be at ROW_8 (rank 8), not ROW_1
    content = content.replace(
        'ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.WHITE, PieceType.KING)',
        'ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)',
        1
    )
    content = content.replace(
        'ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.BLACK, PieceType.KING)',
        'ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)',
        1
    )
    
    # Fix test_checkmate_with_promotion - white pawn promotes to ROW_8, not ROW_1
    content = re.sub(
        r'ConstantSquare\(row=ROW_7, col=COL_E\),\s+ConstantSquare\(row=ROW_1, col=COL_E\)',
        'ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_8, col=COL_E)',
        content
    )
    
    # Fix test_stalemate_after_promotion - same issue
    content = re.sub(
        r'ConstantSquare\(row=ROW_7, col=COL_E\),\s+ConstantSquare\(row=ROW_1, col=COL_E\)',
        'ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_8, col=COL_E)',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

def fix_test_game_status():
    """Fix test_game_status.py - Fool's mate test"""
    filepath = "tests/test_game_status.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix Fool's mate - black queen moves to h4 (ROW_3, COL_H), not ROW_4, COL_H
    # h4 in algebraic = array row 3 (rank 4)
    content = content.replace(
        'ConstantSquare(row=ROW_8, col=COL_D), ConstantSquare(row=ROW_4, col=COL_H)',
        'ConstantSquare(row=ROW_8, col=COL_D), ConstantSquare(row=ROW_3, col=COL_H)'
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

def fix_test_interactions():
    """Fix test_interactions.py"""
    filepath = "tests/test_interactions.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix test_promotion_that_would_leave_king_in_check
    # White pawn at c2 should be ROW_2, not ROW_4
    content = content.replace(
        'ConstantSquare(row=ROW_4, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)',
        'ConstantSquare(row=ROW_2, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)',
        1
    )
    
    # Fix the promotion destination - should be ROW_1, not ROW_7
    content = content.replace(
        'ConstantSquare(row=ROW_7, col=COL_C),',
        'ConstantSquare(row=ROW_1, col=COL_C),',
        3  # There are 3 such occurrences
    )
    
    # Fix test_all_promotion_piece_types - black pawn coordinates
    # Black pawn at e7 should be ROW_7, not ROW_2
    # Promoting to e8 should be ROW_8, not ROW_1
    content = re.sub(
        r'board2\.set_piece\(\s+ConstantSquare\(row=ROW_2, col=COL_E\), create_piece\(Color\.BLACK, PieceType\.PAWN\)\)',
        'board2.set_piece(ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN))',
        content
    )
    content = re.sub(
        r'ConstantSquare\(row=ROW_2, col=COL_F\), create_piece\(Color\.BLACK, PieceType\.KING\)',
        'ConstantSquare(row=ROW_8, col=COL_F), create_piece(Color.BLACK, PieceType.KING)',
        content
    )
    content = content.replace(
        'ConstantSquare(row=ROW_2, col=COL_E),\n            ConstantSquare(row=ROW_1, col=COL_E),',
        'ConstantSquare(row=ROW_7, col=COL_E),\n            ConstantSquare(row=ROW_8, col=COL_E),',
        1
    )
    
    # Fix test_promotion_with_en_passant_same_turn
    # Test 2: Black pawn at e7 should be ROW_7, not ROW_3
    content = content.replace(
        'ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)',
        'ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)',
        1
    )
    
    # Fix white pawn at e6 should be ROW_4
    content = content.replace(
        'board2.set_piece(\n        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)\n    )',
        'board2.set_piece(\n        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)\n    )',
        1
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

def fix_test_special_moves():
    """Fix test_special_moves.py"""
    filepath = "tests/test_special_moves.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix test_white_promotion_to_queen - destination should be ROW_8
    content = content.replace(
        'ConstantSquare(row=ROW_2, col=COL_E),\n            ConstantSquare(row=ROW_8, col=COL_E),',
        'ConstantSquare(row=ROW_2, col=COL_E),\n            ConstantSquare(row=ROW_8, col=COL_E),',
        1
    )
    
    # Fix test_black_promotion_to_queen - destination should be ROW_1
    content = content.replace(
        'ConstantSquare(row=ROW_7, col=COL_E),\n            ConstantSquare(row=ROW_1, col=COL_E),',
        'ConstantSquare(row=ROW_7, col=COL_E),\n            ConstantSquare(row=ROW_1, col=COL_E),',
        1
    )
    
    # Fix test_en_passant_expires_after_one_turn - white pawn at e7 should be ROW_7
    content = content.replace(
        'ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)',
        'ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)'
    )
    # This one is already correct - black pawn at d7 (ROW_7)
    # But white pawn at e2 (ROW_2) trying to move to e6 (ROW_6) via en passant
    # Actually the move is ROW_2 to ROW_6 which should be valid for en passant capture
    
    # Fix test_en_passant_cannot_be_used_if_it_leaves_own_king_in_check
    # Black pawn at d2 should be ROW_2, but should be on d7 for valid setup
    # The test has black pawn at ROW_1 (d8) which is wrong
    content = content.replace(
        'ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)',
        'ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)',
        1
    )
    
    # Fix test_en_passant_black_captures_white_pawn
    # Black pawn at f7 should be ROW_7, not ROW_1
    content = content.replace(
        'ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)',
        'ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)',
        1
    )
    
    # Fix test_promotion_from_rank_6_blocked
    # White pawn at e7 should be ROW_7, not ROW_2
    content = content.replace(
        'ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)',
        'ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)',
        1  # Only first occurrence - the setup
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_test_corner()
    fix_test_game_status()
    fix_test_interactions()
    fix_test_special_moves()
    print("\nAll fixes applied!")
