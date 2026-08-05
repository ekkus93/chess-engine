from pathlib import Path

path = Path("crates/chess-search/src/alpha_beta.rs")
text = path.read_text(encoding="utf-8")

old_call = '''        let child = search_child_with_optional_pvs(
            position,
            history,
            extension.child_depth(),
            ply + 1,
            extension.remaining_budget(),
            move_index,
            alpha,
            beta,
            context,
            &mut diagnostics,
        );
'''
new_call = '''        let child = search_child_with_optional_pvs(
            position,
            history,
            PvsChildSearch {
                depth: extension.child_depth(),
                ply: ply + 1,
                extension_budget: extension.remaining_budget(),
                move_index,
                alpha,
                beta,
            },
            context,
            &mut diagnostics,
        );
'''
if text.count(old_call) != 1:
    raise SystemExit("expected exactly one generated PVS child call")
text = text.replace(old_call, new_call, 1)

old_helper = '''fn search_child_with_optional_pvs<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    extension_budget: u16,
    move_index: usize,
    alpha: Score,
    beta: Score,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
'''
new_helper = '''#[derive(Clone, Copy)]
struct PvsChildSearch {
    depth: u16,
    ply: u16,
    extension_budget: u16,
    move_index: usize,
    alpha: Score,
    beta: Score,
}

fn search_child_with_optional_pvs<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    request: PvsChildSearch,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let PvsChildSearch {
        depth,
        ply,
        extension_budget,
        move_index,
        alpha,
        beta,
    } = request;
'''
if text.count(old_helper) != 1:
    raise SystemExit("expected exactly one generated PVS helper")
text = text.replace(old_helper, new_helper, 1)

# Ensure every internal AlphaBetaContext initializer explicitly sets the new flag.
needle = "AlphaBetaContext {"
search_from = 0
parts = []
while True:
    start = text.find(needle, search_from)
    if start == -1:
        parts.append(text[search_from:])
        break
    parts.append(text[search_from:start])
    brace = text.find("{", start)
    depth = 0
    end = None
    for index in range(brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise SystemExit("unterminated AlphaBetaContext initializer")
    block = text[start:end]
    if "principal_variation_search:" not in block:
        weight_marker = "            weights:"
        if weight_marker not in block:
            raise SystemExit("AlphaBetaContext initializer has no weights marker")
        block = block.replace(
            weight_marker,
            "            principal_variation_search: false,\n" + weight_marker,
            1,
        )
    parts.append(block)
    search_from = end
text = "".join(parts)

path.write_text(text, encoding="utf-8")
Path(".github/s2_7_repair.py").unlink()
