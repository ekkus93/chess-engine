#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

tracker="docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
definitions="docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
postport_record="docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md"
v0_2_spec="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md"
v0_2_todo="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
s3_spec="docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md"
s3_todo="docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md"
legacy_index="docs/LEGACY_TODO_INDEX.md"
fen_doc="docs/RUST_FEN_AND_UCI_NOTATION.md"
fen_source="crates/chess-core/src/position/fen.rs"

for required in \
    "$tracker" \
    "$definitions" \
    "$postport_record" \
    "$v0_2_spec" \
    "$v0_2_todo" \
    "$s3_spec" \
    "$s3_todo" \
    "$legacy_index" \
    "$fen_doc" \
    "$fen_source"; do
    test -f "$required"
done

grep -Eq '^# Task 21: .* — COMPLETE$' "$tracker"
if grep -Eq '^# Task 21: .* — IN PROGRESS$' "$tracker"; then
    echo "stale Task 21 IN PROGRESS heading remains" >&2
    exit 1
fi
grep -Fq 'activated=false' "$tracker"
grep -Fqi 'baseline weights remain authoritative' "$tracker"
grep -Fqi 'separate strength change' "$tracker"
grep -Fq '**Status:** Complete' "$postport_record"
grep -Fq '**Status:** Complete — program closed without v0.2 promotion' "$v0_2_todo"
if grep -Fq '| Active v0.2 strength program |' "$legacy_index"; then
    echo "closed v0.2 strength TODO is still classified as active" >&2
    exit 1
fi

authority_todos=(
    "$s3_todo"
    "$tracker"
    "$definitions"
)
for authority in "${authority_todos[@]}"; do
    grep -Fq "\`$authority\`" "$legacy_index"
done
grep -Fq "\`$legacy_index\`" "$legacy_index"
grep -Fq "\`$postport_record\`" "$legacy_index"
grep -Fq "\`$v0_2_todo\`" "$legacy_index"
grep -Fq 'Apart from this authority index, every other Markdown file directly under `docs/` whose filename contains `TODO` and is not one of the three authority documents above' "$legacy_index"
grep -Fq 'Active S3 evaluation strength program' "$legacy_index"
grep -Fq "73 TODO-named files total; 3 authority documents; 1 authority index; 69 historical" "$legacy_index"
grep -Fq "**Companion TODO:** \`$v0_2_todo\`" "$v0_2_spec"
grep -Fq "**Specification:** \`$v0_2_spec\`" "$v0_2_todo"
grep -Fq "**Companion TODO:** \`$s3_todo\`" "$s3_spec"
grep -Fq "**Specification:** \`$s3_spec\`" "$s3_todo"
grep -Fq '**Status:** Active — not yet implemented' "$s3_todo"
grep -Fq '# Task S3-0: Authority registration and v0.1 baseline freeze — NOT STARTED' "$s3_todo"
grep -Fq '# Task S3-12: Final report and closure — NOT STARTED' "$s3_todo"

while IFS= read -r todo_path; do
    case "$todo_path" in
        "$s3_todo"|"$tracker"|"$definitions"|"$legacy_index")
            ;;
        *)
            grep -Fq "\`$todo_path\`" "$legacy_index" || {
                echo "historical TODO missing from index: $todo_path" >&2
                exit 1
            }
            ;;
    esac
done < <(find docs -maxdepth 1 -type f -name '*TODO*.md' -print | sort)

grep -Fq 'strict syntax and structural **analysis-position** parser' "$fen_doc"
grep -Fq 'Structural acceptance is not certification of legal game reachability.' "$fen_doc"
grep -Fq 'remain a safe input to legal move generation' "$fen_doc"
grep -Fq 'Parses strict structural six-field FEN for safe analysis positions.' "$fen_source"
grep -Fq 'it is not proof that' "$fen_source"

for temporary in \
    ".github/ppr_implementation.py" \
    ".github/workflows/ppr-implementation.yml" \
    ".github/ppr_close.py" \
    ".github/workflows/ppr-closure.yml"; do
    if test -e "$temporary"; then
        echo "temporary post-port helper remains: $temporary" >&2
        exit 1
    fi
done

bash scripts/task_26_v0_1_audit.sh
bash scripts/task_27_full_port_audit.sh

echo "post-port review fix and TODO-authority audit passed"
