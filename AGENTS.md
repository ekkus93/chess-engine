# AGENTS.md

## Build, Lint, and Test Commands

### Running Tests
- Run all tests: `python -m pytest tests/ -v`
- Run a single test file: `python -m pytest tests/test_board.py -v`
- Run a specific test function: `python -m pytest tests/test_board.py::test_rook_move -v`
- Run tests with coverage: `python -m pytest tests/ --cov=chess_game`

### Linting and Formatting
- Lint with pylint: `pylint chess_game/`
- Format with black: `black chess_game/`
- Type checking with mypy: `mypy chess_game/`
- Run all checks: `./check.sh` (if exists)

### Project Structure
The project follows Python package structure with:
- Source code in `chess_game/` directory
- Tests in `tests/` directory
- Entry point in `chess_game/main.py`

## Code Style Guidelines

### Imports
- Use absolute imports: `from chess_game.chess.board import Board`
- Group imports in order: standard library, third-party, local
- Avoid wildcard imports (`from module import *`)

### Formatting
- Use Black code formatter (default settings)
- Maximum line length: 88 characters
- Use 4 spaces for indentation
- Add spaces around operators and after commas
- Use snake_case for functions and variables
- Use PascalCase for classes

### Type Hints
- Use type annotations for all function parameters and return values
- Import `List`, `Tuple`, `Optional` from `typing` module
- Example: `def make_move(self, start: Tuple[int, int], end: Tuple[int, int]) -> bool:`

### Naming Conventions
- Classes: PascalCase (Board, ChessEngine)
- Functions and variables: snake_case (create_board, make_move)
- Constants: UPPER_CASE (MAX_DEPTH, BOARD_SIZE)

### Error Handling
- Use descriptive error messages
- Validate input parameters early
- Handle file operations with try/except blocks
- Follow Python idioms for error handling

### Documentation
- Add docstrings for all public functions and classes
- Use Google or NumPy style docstrings
- Document function parameters and return values

### Testing
- All functions should have unit tests
- Test edge cases and invalid inputs
- Test both success and failure conditions
- Use pytest framework with fixtures when appropriate

### Code Structure
- Keep functions short and focused
- Avoid global variables
- Use classes to organize related functionality
- Follow single responsibility principle