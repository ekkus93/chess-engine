from pathlib import Path

path = Path("android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/MainActivity.kt")
text = path.read_text()

replacements = [
    (
        "import androidx.compose.foundation.lazy.LazyColumn\nimport androidx.compose.foundation.lazy.rememberLazyListState\n",
        "import androidx.compose.foundation.lazy.LazyColumn\nimport androidx.compose.foundation.lazy.LazyListState\nimport androidx.compose.foundation.lazy.rememberLazyListState\n",
    ),
    (
        "    var selectedTab by rememberSaveable { mutableStateOf(GameTab.MOVES) }\n"
        "    LaunchedEffect(snapshot.moves.isEmpty()) {\n"
        "        if (snapshot.moves.isEmpty()) {\n"
        "            selectedTab = GameTab.MOVES\n"
        "        }\n"
        "    }\n",
        "    var selectedTab by rememberSaveable { mutableStateOf(GameTab.MOVES) }\n"
        "    val moveListState = rememberLazyListState()\n"
        "    LaunchedEffect(snapshot.moves.isEmpty()) {\n"
        "        if (snapshot.moves.isEmpty()) {\n"
        "            selectedTab = GameTab.MOVES\n"
        "            moveListState.scrollToItem(0)\n"
        "        }\n"
        "    }\n",
    ),
    (
        "                    GameTab.MOVES -> MoveHistoryPanel(snapshot.sanMoves)\n",
        "                    GameTab.MOVES -> MoveHistoryPanel(snapshot.sanMoves, moveListState)\n",
    ),
    (
        "private fun MoveHistoryPanel(sanMoves: List<String>) {\n"
        "    val rows = remember(sanMoves) { moveRows(sanMoves) }\n"
        "    val listState = rememberLazyListState()\n",
        "private fun MoveHistoryPanel(\n"
        "    sanMoves: List<String>,\n"
        "    listState: LazyListState,\n"
        ") {\n"
        "    val rows = remember(sanMoves) { moveRows(sanMoves) }\n",
    ),
]

for before, after in replacements:
    count = text.count(before)
    if count != 1:
        raise SystemExit(f"expected exactly one match, found {count}: {before!r}")
    text = text.replace(before, after, 1)

path.write_text(text)
