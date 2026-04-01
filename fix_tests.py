import re

# Read the file
with open('tests/test_path_blocking.py', 'r') as f:
    content = f.read()

# Fix the test assertions to use attribute comparisons
# Pattern: move[0] == (ROW_1, COL_A) and move[1] == (ROW_1, COL_B)
# Should become: move[0].row == ROW_1 and move[0].col == COL_A and move[1].row == ROW_1 and move[1].col == COL_B

# This is complex, let me fix it more carefully
# I'll fix each specific pattern

# Fix 1: move[0] == (ROW_1, COL_A) and move[1] == (ROW_1, COL_B)
content = content.replace(
    'move[0] == (ROW_1, COL_A) and move[1] == (ROW_1, COL_B)',
    'move[0].row == ROW_1 and move[0].col == COL_A and move[1].row == ROW_1 and move[1].col == COL_B'
)

# Fix 2: (ROW_1, COL_E) not in legal_moves
content = content.replace(
    '(ROW_1, COL_E) not in legal_moves',
    'not any(move[0].row == ROW_1 and move[0].col == COL_E for move in legal_moves)'
)

# Fix 3: move[0] == (ROW_1, COL_A) and move[1] == (ROW_2, COL_B)
content = content.replace(
    'move[0] == (ROW_1, COL_A) and move[1] == (ROW_2, COL_B)',
    'move[0].row == ROW_1 and move[0].col == COL_A and move[1].row == ROW_2 and move[1].col == COL_B'
)

# Fix 4: move[0] == (ROW_1, COL_A) and move[1] == (ROW_3, COL_C)
content = content.replace(
    'move[0] == (ROW_1, COL_A) and move[1] == (ROW_3, COL_C)',
    'move[0].row == ROW_1 and move[0].col == COL_A and move[1].row == ROW_3 and move[1].col == COL_C'
)

# Fix 5: move[1] == (6, COL_B) - using raw integer
content = content.replace(
    'move[1] == (6, COL_B)',
    'move[1].row == 5 and move[1].col == COL_B'  # Row 5 = ROW_6
)

# Fix 6: move[1] == (5, COL_C)
content = content.replace(
    'move[1] == (5, COL_C)',
    'move[1].row == 4 and move[1].col == COL_C'  # Row 4 = ROW_5
)

# Fix 7: move[1] == (ROW_2, COL_E)
content = content.replace(
    'move[1] == (ROW_2, COL_E)',
    'move[1].row == ROW_2 and move[1].col == COL_E'
)

# Fix 8: move[1] == (ROW_4, COL_E)
content = content.replace(
    'move[1] == (ROW_4, COL_E)',
    'move[1].row == ROW_4 and move[1].col == COL_E'
)

# Fix 9: move[1] == (ROW_2, COL_E) - duplicate
content = content.replace(
    'move[1] == (ROW_2, COL_E)',
    'move[1].row == ROW_2 and move[1].col == COL_E'
)

# Fix 10: move[1] == (5, COL_C) - duplicate
content = content.replace(
    'move[1] == (5, COL_C)',
    'move[1].row == 4 and move[1].col == COL_C'
)

# Fix 11: move[1] == (ROW_2, COL_B)
content = content.replace(
    'move[1] == (ROW_2, COL_B)',
    'move[1].row == ROW_2 and move[1].col == COL_B'
)

# Fix 12: move[1] == (ROW_3, COL_C)
content = content.replace(
    'move[1] == (ROW_3, COL_C)',
    'move[1].row == ROW_3 and move[1].col == COL_C'
)

with open('tests/test_path_blocking.py', 'w') as f:
    f.write(content)

print("Fixed test_path_blocking.py")
