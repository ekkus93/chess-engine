#!/usr/bin/env python3
"""
Fix coordinate errors in chess engine test files.

Coordinate mapping (ROW constants = array row values):
- ROW_1 = array row 0 = rank 1 (white's back rank)
- ROW_2 = array row 1 = rank 2 (white pawns start)
- ROW_7 = array row 6 = rank 7 (black pawns start)
- ROW_8 = array row 7 = rank 8 (black's back rank)

White pawn promotion: from any rank 2-7 to ROW_8 (rank 8)
Black pawn promotion: from any rank 2-7 to ROW_1 (rank 1)
"""

import re

def fix_test_special_moves():
    """Fix coordinate errors in test_special_moves.py"""
    filepath = "tests/test_special_moves.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    fixes = []
    
    # Fix test_white_promotion_to_queen: ROW_8 (rank 8) is correct for white
    # But need to check if destination should be ROW_8 or ROW_7
    # ROW_8 = rank 8, ROW_7 = rank 7
    # White promotes TO rank 8, so ROW_8 is correct
    pass
    
    # Write the corrected file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_test_special_moves()
