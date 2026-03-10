# Chess Rules Engine

## Description
A correct, test-driven chess rules engine with a small CLI front-end.

## Features
- Complete chess board representation
- Legal move validation for all pieces
- Turn-based gameplay
- Standard chess rules implementation
- CLI interface

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python chess_game/main.py
```

## Testing
```bash
test -f tests/test_board.py
```

### Testing Note
`tests/conftest.py` defines a local `record_xml_attribute` fixture intentionally.
This avoids `PytestExperimentalApiWarning` caused by auto-loaded third-party
pytest plugins requesting pytest's experimental fixture of the same name.
Do not remove it unless plugin loading behavior is changed explicitly.

## Project Structure
```sh
chess_game/
  board.py
  main.py
tests/
  test_board.py
```

## Future Features
- Python GUI with tkinter/pygame (planned)
- AI engines (planned)
