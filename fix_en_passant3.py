#!/usr/bin/env python3
"""Fix remaining en passant coordinate errors"""

def fix_en_passant_tests():
    filepath = "tests/test_special_moves.py"
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix line numbers - find the test_en_passant_black_captures_white_pawn function
    # and fix the move coordinates
    
    new_lines = []
    for i, line in enumerate(lines):
        # Fix test_en_passant_black_captures_white_pawn
        # Change ROW_1, COL_F to ROW_7, COL_F (f7 not f1)
        if 'ConstantSquare(row=ROW_1, col=COL_F)' in line and i > 1000:
            new_lines.append('            ConstantSquare(row=ROW_7, col=COL_F),\n')
            continue
        
        # Fix test_en_passant_expires_after_one_turn
        # Change capture from ROW_6, COL_D to ROW_3, COL_D
        if 'ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)' in line:
            new_lines.append('        ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_3, col=COL_D)\n')
            continue
        
        new_lines.append(line)
    
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_en_passant_tests()
