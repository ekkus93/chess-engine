from pathlib import Path

path = Path("scripts/task_s2_9_search_null_transition_audit.sh")
text = path.read_text(encoding="utf-8")
replacements = {
    "grep -Fq '^            previous_halfmove_clock: self.halfmove_clock(),'": "grep -Fq 'previous_halfmove_clock: self.halfmove_clock(),'",
    "grep -Fq '^            previous_fullmove_number: self.fullmove_number(),'": "grep -Fq 'previous_fullmove_number: self.fullmove_number(),'",
    "grep -Fq '^            previous_zobrist: self.zobrist(),'": "grep -Fq 'previous_zobrist: self.zobrist(),'",
    "grep -Fq '^                ^ self.canonical_en_passant_key()'": "grep -Fq '^ self.canonical_en_passant_key()'",
    "grep -Fq '^                ^ side_to_move_key(),'": "grep -Fq '^ side_to_move_key(),'",
}
for old, new in replacements.items():
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one occurrence of {old!r}, found {count}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
Path(__file__).unlink()
