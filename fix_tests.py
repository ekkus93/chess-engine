import re
import sys

files_to_fix = [
    'tests/test_ai.py',
    'tests/test_board_state.py',
    'tests/test_castling_edge_cases.py',
    'tests/test_checkmate.py',
    'tests/test_complex.py',
    'tests/test_corner.py',
    'tests/test_en_passant.py',
    'tests/test_en_passant_edge_cases.py',
    'tests/test_game_status.py',
    'tests/test_interactions.py',
    'tests/test_king_safety.py',
    'tests/test_legality.py',
    'tests/test_path_blocking.py',
    'tests/test_piece_moves.py',
    'tests/test_promotion.py',
    'tests/test_safety.py',
    'tests/test_setup.py',
    'tests/test_special_moves.py',
    'tests/test_turn_color.py',
]

for filename in files_to_fix:
    with open(filename, 'r') as f:
        content = f.read()
    
    # Fix ConstantSquare(row=ROW_X, col=COL_Y) patterns
    # ROW_1 = 0, ROW_2 = 1, ..., ROW_8 = 7
    # COL_A = 0, COL_B = 1, ..., COL_H = 7
    
    # Map ROW constants to numbers
    row_map = {
        'ROW_1': 0, 'ROW_2': 1, 'ROW_3': 2, 'ROW_4': 3, 'ROW_5': 4,
        'ROW_6': 5, 'ROW_7': 6, 'ROW_8': 7
    }
    
    # Map COL constants to numbers  
    col_map = {
        'COL_A': 0, 'COL_B': 1, 'COL_C': 2, 'COL_D': 3, 'COL_E': 4,
        'COL_F': 5, 'COL_G': 6, 'COL_H': 7
    }
    
    # Replace ConstantSquare(row=ROW_X, col=COL_Y) with get_square_constant(num, num)
    def replace_constant_square(match):
        content = match.group(0)
        # Extract row and col
        row_match = re.search(r'ROW_\d+', content)
        col_match = re.search(r'COL_[A-H]', content)
        
        if row_match and col_match:
            row_num = row_map[row_match.group(0)]
            col_num = col_map[col_match.group(0)]
            return f'get_square_constant({row_num}, {col_num})'
        return content
    
    content = re.sub(r'ConstantSquare\(row=ROW_\d+, col=COL_[A-H]\)', replace_constant_square, content)
    
    # Also fix ConstantSquare(row=get_row_constant(X), col=get_col_constant(Y))
    def replace_helper_functions(match):
        content = match.group(0)
        row_match = re.search(r'get_row_constant\((\d+)\)', content)
        col_match = re.search(r'get_col_constant\((\d+)\)', content)
        
        if row_match and col_match:
            return f'get_square_constant({row_match.group(1)}, {col_match.group(1)})'
        return content
    
    content = re.sub(r'ConstantSquare\(row=get_row_constant\(\d+\), col=get_col_constant\(\d+\)\)', replace_helper_functions, content)
    
    # Add get_square_constant to imports if not present
    if 'get_square_constant' not in content:
        # Find the imports section and add it
        import_pattern = r'(from chess_game\.constants import \()'
        if re.search(import_pattern, content):
            # Find the end of the imports
            content = re.sub(
                import_pattern,
                r'\1\n    get_square_constant,',
                content
            )
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filename}")

print("\nDone!")
