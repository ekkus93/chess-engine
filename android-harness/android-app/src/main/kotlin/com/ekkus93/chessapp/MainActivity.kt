package com.ekkus93.chessapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import kotlin.math.roundToInt

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            RustChessTheme {
                ChessApp()
            }
        }
    }
}

private enum class Confirmation {
    NEW_GAME,
    RESTART,
    RESIGN,
}

internal enum class GameTab {
    MOVES,
    ENGINE,
}

@Composable
fun ChessApp(
    viewModel: ChessViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var confirmation by remember { mutableStateOf<Confirmation?>(null) }

    Scaffold(containerColor = AppBackground) { padding ->
        Surface(
            color = AppBackground,
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            if (state.isSetup) {
                SetupScreen(
                    state = state,
                    onSideChanged = viewModel::setHumanSide,
                    onDepthChanged = viewModel::setEngineDepth,
                    onStart = viewModel::startGame,
                )
            } else {
                GameScreen(
                    state = state,
                    onSquareTapped = viewModel::onSquareTapped,
                    onNewGame = { confirmation = Confirmation.NEW_GAME },
                    onRestart = { confirmation = Confirmation.RESTART },
                    onResign = { confirmation = Confirmation.RESIGN },
                )
            }
        }
    }

    state.errorMessage?.let { message ->
        AlertDialog(
            onDismissRequest = viewModel::clearError,
            confirmButton = {
                TextButton(onClick = viewModel::clearError) {
                    Text("OK")
                }
            },
            title = { Text("Chess engine error") },
            text = { Text(message) },
            containerColor = SurfaceElevated,
            titleContentColor = OnBackground,
            textContentColor = OnSurfaceMuted,
        )
    }

    if (state.promotionMoves.isNotEmpty()) {
        PromotionDialog(
            moves = state.promotionMoves,
            onChoose = viewModel::choosePromotion,
            onCancel = viewModel::cancelPromotion,
        )
    }

    confirmation?.let { pending ->
        val (title, text, confirmLabel) = when (pending) {
            Confirmation.NEW_GAME -> Triple(
                "Start a new game?",
                "The current game will be closed so you can choose a new side and strength.",
                "New game",
            )
            Confirmation.RESTART -> Triple(
                "Restart this game?",
                "The current position and move history will be discarded.",
                "Restart",
            )
            Confirmation.RESIGN -> Triple(
                "Resign this game?",
                "Resignation ends the current game immediately.",
                "Resign",
            )
        }
        AlertDialog(
            onDismissRequest = { confirmation = null },
            dismissButton = {
                TextButton(onClick = { confirmation = null }) {
                    Text("Cancel")
                }
            },
            confirmButton = {
                TextButton(
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = if (pending == Confirmation.RESIGN) Danger else PrimaryStrong,
                    ),
                    onClick = {
                        confirmation = null
                        when (pending) {
                            Confirmation.NEW_GAME -> viewModel.returnToSetup()
                            Confirmation.RESTART -> viewModel.restartGame()
                            Confirmation.RESIGN -> viewModel.resign()
                        }
                    },
                ) {
                    Text(confirmLabel)
                }
            },
            title = { Text(title) },
            text = { Text(text) },
            containerColor = SurfaceElevated,
            titleContentColor = OnBackground,
            textContentColor = OnSurfaceMuted,
        )
    }
}

@Composable
internal fun SetupScreen(
    state: ChessUiState,
    onSideChanged: (HumanSide) -> Unit,
    onDepthChanged: (Int) -> Unit,
    onStart: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AppBackground)
            .padding(horizontal = 24.dp, vertical = 20.dp)
            .testTag("setup-screen"),
        verticalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Surface(
                modifier = Modifier.size(58.dp),
                shape = RoundedCornerShape(18.dp),
                color = SurfaceElevated,
                border = BorderStroke(1.dp, Border),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    ChessPiece(
                        piece = 'N',
                        modifier = Modifier.size(46.dp),
                    )
                }
            }
            Text(
                text = "Rust Chess",
                style = MaterialTheme.typography.headlineLarge,
                color = OnBackground,
            )
            Text(
                text = "Play against the native Rust chess engine.",
                style = MaterialTheme.typography.bodyLarge,
                color = OnSurfaceMuted,
            )
        }

        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.large,
            color = Surface,
            border = BorderStroke(1.dp, Border),
        ) {
            Column(
                modifier = Modifier.padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(18.dp),
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        text = "Play as",
                        style = MaterialTheme.typography.titleMedium,
                        color = OnBackground,
                    )
                    SideSelector(
                        selected = state.humanSide,
                        enabled = !state.busy,
                        onSideChanged = onSideChanged,
                    )
                }

                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = "Engine strength",
                            style = MaterialTheme.typography.titleMedium,
                            color = OnBackground,
                        )
                        Text(
                            text = "Depth ${state.engineDepth} · ${depthLabel(state.engineDepth)}",
                            style = MaterialTheme.typography.labelMedium,
                            color = PrimaryStrong,
                        )
                    }
                    Slider(
                        value = state.engineDepth.toFloat(),
                        onValueChange = {
                            onDepthChanged(it.roundToInt().coerceIn(1, 12))
                        },
                        valueRange = 1f..12f,
                        steps = 0,
                        enabled = !state.busy,
                        colors = SliderDefaults.colors(
                            thumbColor = PrimaryStrong,
                            activeTrackColor = Primary,
                            inactiveTrackColor = Border,
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("depth-control")
                            .semantics {
                                contentDescription = "Engine depth ${state.engineDepth}"
                            },
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text("Faster", style = MaterialTheme.typography.bodySmall, color = OnSurfaceMuted)
                        Text("Stronger", style = MaterialTheme.typography.bodySmall, color = OnSurfaceMuted)
                    }
                }
            }
        }

        Button(
            onClick = onStart,
            enabled = !state.busy,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
                .testTag("start-game"),
            shape = MaterialTheme.shapes.medium,
            colors = ButtonDefaults.buttonColors(
                containerColor = Primary,
                contentColor = AppBackground,
            ),
        ) {
            if (state.busy) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = AppBackground,
                    strokeWidth = 2.dp,
                )
            } else {
                Text("Start game", style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@Composable
private fun SideSelector(
    selected: HumanSide,
    enabled: Boolean,
    onSideChanged: (HumanSide) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(46.dp)
            .clip(MaterialTheme.shapes.medium)
            .background(SurfaceMuted)
            .border(1.dp, Border, MaterialTheme.shapes.medium)
            .padding(3.dp),
    ) {
        HumanSide.entries.forEach { side ->
            val isSelected = selected == side
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxSize()
                    .clip(MaterialTheme.shapes.small)
                    .background(if (isSelected) SurfaceElevated else Color.Transparent)
                    .clickable(enabled = enabled) { onSideChanged(side) }
                    .testTag(if (side == HumanSide.WHITE) "side-white" else "side-black")
                    .semantics {
                        contentDescription = buildString {
                            append("Play as ${side.displayName()}")
                            if (isSelected) append(", selected")
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = side.displayName(),
                    style = MaterialTheme.typography.labelLarge,
                    color = if (isSelected) PrimaryStrong else OnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
internal fun GameScreen(
    state: ChessUiState,
    onSquareTapped: (String) -> Unit,
    onNewGame: () -> Unit,
    onRestart: () -> Unit,
    onResign: () -> Unit,
) {
    val snapshot = requireNotNull(state.snapshot)
    val board = remember(snapshot.fen) { BoardPosition.parse(snapshot.fen) }
    val targets = remember(snapshot.legalMoves, state.selectedSquare) {
        legalTargets(snapshot.legalMoves, state.selectedSquare)
    }
    val lastMove = remember(snapshot.moves) { lastMoveSquares(snapshot.moves) }
    var selectedTab by rememberSaveable { mutableStateOf(GameTab.MOVES) }
    LaunchedEffect(snapshot.moves.isEmpty()) {
        if (snapshot.moves.isEmpty()) {
            selectedTab = GameTab.MOVES
        }
    }

    BoxWithConstraints(
        modifier = Modifier
            .fillMaxSize()
            .background(AppBackground)
            .padding(horizontal = 10.dp, vertical = 8.dp)
            .testTag("game-screen"),
    ) {
        val gap = 6.dp
        val statusHeight = 54.dp
        val tabHeight = 38.dp
        val actionHeight = 46.dp
        val minimumPanelHeight = 100.dp
        val nonBoardHeight = statusHeight + tabHeight + actionHeight + minimumPanelHeight + gap * 4
        val boardSize = minOf(
            maxWidth,
            (maxHeight - nonBoardHeight).coerceAtLeast(0.dp),
        )

        Column(modifier = Modifier.fillMaxSize()) {
            GameStatusBar(
                snapshot = snapshot,
                configuredDepth = state.engineDepth,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(statusHeight),
            )
            Spacer(Modifier.height(gap))
            ChessBoard(
                board = board,
                orientation = snapshot.humanSide,
                selectedSquare = state.selectedSquare,
                legalTargets = targets,
                lastMove = lastMove,
                enabled = !state.busy && snapshot.humanToMove,
                onSquareTapped = onSquareTapped,
                modifier = Modifier
                    .size(boardSize)
                    .align(Alignment.CenterHorizontally),
            )
            Spacer(Modifier.height(gap))
            GameTabs(
                selected = selectedTab,
                onSelected = { selectedTab = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(tabHeight),
            )
            Spacer(Modifier.height(gap))
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .testTag("game-tab-body"),
                shape = MaterialTheme.shapes.medium,
                color = Surface,
                border = BorderStroke(1.dp, Border),
            ) {
                when (selectedTab) {
                    GameTab.MOVES -> MoveHistoryPanel(snapshot.sanMoves)
                    GameTab.ENGINE -> EnginePanel(snapshot)
                }
            }
            Spacer(Modifier.height(gap))
            GameActions(
                gameOver = snapshot.gameOver,
                busy = state.busy,
                onNewGame = onNewGame,
                onRestart = onRestart,
                onResign = onResign,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(actionHeight),
            )
        }
    }
}

@Composable
private fun GameStatusBar(
    snapshot: ChessGameSnapshot,
    configuredDepth: Int,
    modifier: Modifier = Modifier,
) {
    val title = when {
        snapshot.outcome != null -> snapshot.outcome
        snapshot.thinking -> "Engine thinking…"
        snapshot.humanToMove -> "Your move"
        else -> "Engine turn"
    }
    Surface(
        modifier = modifier.testTag("status-region"),
        shape = MaterialTheme.shapes.medium,
        color = Surface,
        border = BorderStroke(1.dp, Border),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (snapshot.thinking) {
                CircularProgressIndicator(
                    modifier = Modifier.size(18.dp),
                    color = PrimaryStrong,
                    strokeWidth = 2.dp,
                )
                Spacer(Modifier.width(9.dp))
            } else {
                Box(
                    modifier = Modifier
                        .size(9.dp)
                        .background(
                            color = if (snapshot.gameOver) Warning else Success,
                            shape = CircleShape,
                        ),
                )
                Spacer(Modifier.width(9.dp))
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    color = OnBackground,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = snapshot.statusMessage?.takeIf { it.isNotBlank() }
                        ?: if (snapshot.moves.isEmpty()) "Game ready" else "Game in progress",
                    style = MaterialTheme.typography.bodySmall,
                    color = OnSurfaceMuted,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = snapshot.humanSide.displayName(),
                    style = MaterialTheme.typography.labelMedium,
                    color = OnBackground,
                )
                Text(
                    text = "Depth $configuredDepth",
                    style = MaterialTheme.typography.bodySmall,
                    color = OnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
internal fun ChessBoard(
    board: BoardPosition,
    orientation: HumanSide,
    selectedSquare: String?,
    legalTargets: Set<String>,
    lastMove: LastMoveSquares?,
    enabled: Boolean,
    onSquareTapped: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val files = visibleFiles(orientation)
    val ranks = visibleRanks(orientation)
    Column(
        modifier = modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(6.dp))
            .border(1.dp, Border, RoundedCornerShape(6.dp))
            .testTag("chess-board")
            .semantics { contentDescription = "Chess board" },
    ) {
        ranks.forEach { rank ->
            Row(modifier = Modifier.weight(1f)) {
                files.forEach { file ->
                    val square = "$file$rank"
                    val baseColor = if (((file - 'a') + rank) % 2 == 0) BoardLight else BoardDark
                    val isLastMove = square == lastMove?.source || square == lastMove?.destination
                    val piece = board.pieces[square]
                    val isTarget = square in legalTargets
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxSize()
                            .background(
                                if (isLastMove) lerp(baseColor, PrimaryStrong, 0.30f) else baseColor,
                            )
                            .then(
                                if (enabled) {
                                    Modifier.clickable { onSquareTapped(square) }
                                } else {
                                    Modifier
                                },
                            )
                            .semantics {
                                contentDescription = buildString {
                                    append(square)
                                    piece?.let {
                                        append(' ')
                                        append(pieceName(it))
                                    }
                                    if (isLastMove) append(" last move")
                                    if (square == selectedSquare) append(" selected")
                                    if (isTarget) {
                                        if (piece == null) append(" legal target")
                                        else append(" legal capture")
                                    }
                                }
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        if (square == selectedSquare) {
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(BoardSelected),
                            )
                        }
                        if (isTarget) {
                            Canvas(modifier = Modifier.fillMaxSize()) {
                                if (piece == null) {
                                    drawCircle(
                                        color = BoardLegalTarget,
                                        radius = size.minDimension * 0.12f,
                                    )
                                } else {
                                    drawCircle(
                                        color = BoardLegalTarget,
                                        radius = size.minDimension * 0.38f,
                                        style = Stroke(width = size.minDimension * 0.07f),
                                    )
                                }
                            }
                        }
                        piece?.let {
                            ChessPiece(
                                piece = it,
                                modifier = Modifier.fillMaxSize(0.80f),
                            )
                        }
                        if (file == files.first()) {
                            Text(
                                text = rank.toString(),
                                modifier = Modifier
                                    .align(Alignment.TopStart)
                                    .padding(2.dp),
                                fontSize = 8.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = Color.Black.copy(alpha = 0.58f),
                            )
                        }
                        if (rank == ranks.last()) {
                            Text(
                                text = file.toString(),
                                modifier = Modifier
                                    .align(Alignment.BottomEnd)
                                    .padding(2.dp),
                                fontSize = 8.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = Color.Black.copy(alpha = 0.58f),
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun GameTabs(
    selected: GameTab,
    onSelected: (GameTab) -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .clip(MaterialTheme.shapes.medium)
            .background(SurfaceMuted)
            .border(1.dp, Border, MaterialTheme.shapes.medium)
            .padding(3.dp)
            .testTag("game-tabs"),
    ) {
        GameTab.entries.forEach { tab ->
            val isSelected = selected == tab
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxSize()
                    .clip(MaterialTheme.shapes.small)
                    .background(if (isSelected) SurfaceElevated else Color.Transparent)
                    .clickable { onSelected(tab) }
                    .testTag(if (tab == GameTab.MOVES) "tab-moves" else "tab-engine")
                    .semantics {
                        contentDescription = buildString {
                            append(if (tab == GameTab.MOVES) "Moves tab" else "Engine tab")
                            if (isSelected) append(", selected")
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (tab == GameTab.MOVES) "Moves" else "Engine",
                    style = MaterialTheme.typography.labelLarge,
                    color = if (isSelected) PrimaryStrong else OnSurfaceMuted,
                )
            }
        }
    }
}

@Composable
private fun MoveHistoryPanel(sanMoves: List<String>) {
    val rows = remember(sanMoves) { moveRows(sanMoves) }
    val listState = rememberLazyListState()
    LaunchedEffect(rows.size) {
        if (rows.isEmpty()) {
            return@LaunchedEffect
        }
        val layout = listState.layoutInfo
        val lastVisible = layout.visibleItemsInfo.lastOrNull()?.index
        val wasNearBottom = layout.totalItemsCount == 0 ||
            lastVisible == null || lastVisible >= layout.totalItemsCount - 2
        if (wasNearBottom) {
            listState.animateScrollToItem(rows.lastIndex)
        }
    }

    if (rows.isEmpty()) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .testTag("moves-list"),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = "No moves yet",
                style = MaterialTheme.typography.bodyMedium,
                color = OnSurfaceMuted,
            )
        }
        return
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .testTag("moves-list"),
        state = listState,
        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp),
        verticalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        items(rows.size, key = { rows[it].number }) { index ->
            val row = rows[index]
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 2.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "${row.number}.",
                    modifier = Modifier.width(34.dp),
                    style = MaterialTheme.typography.bodySmall,
                    color = OnSurfaceMuted,
                )
                Text(
                    text = row.white,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = FontFamily.Monospace,
                    color = OnBackground,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Text(
                    text = row.black.orEmpty(),
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodyMedium,
                    fontFamily = FontFamily.Monospace,
                    color = if (row.black == null) OnSurfaceMuted else OnBackground,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

@Composable
private fun EnginePanel(snapshot: ChessGameSnapshot) {
    val hasMetrics = snapshot.engineDepth != null || snapshot.engineScore != null ||
        snapshot.engineNodes != null || snapshot.engineNps != null ||
        snapshot.engineElapsed != null || snapshot.principalVariation.isNotEmpty()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 10.dp, vertical = 7.dp)
            .testTag("engine-panel"),
        verticalArrangement = Arrangement.spacedBy(5.dp),
    ) {
        if (!hasMetrics) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(
                    text = "No completed search metrics yet",
                    style = MaterialTheme.typography.bodyMedium,
                    color = OnSurfaceMuted,
                )
            }
            return@Column
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(5.dp),
        ) {
            EngineMetric("Depth", snapshot.engineDepth?.toString(), Modifier.weight(1f))
            EngineMetric("Score", snapshot.engineScore, Modifier.weight(1f))
            EngineMetric("Nodes", snapshot.engineNodes?.let(::formatCount), Modifier.weight(1f))
            EngineMetric("NPS", snapshot.engineNps?.let(::formatCount), Modifier.weight(1f))
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.Top,
        ) {
            Text(
                text = "Time ${snapshot.engineElapsed ?: "—"}",
                modifier = Modifier.width(92.dp),
                style = MaterialTheme.typography.bodySmall,
                color = OnSurfaceMuted,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = if (snapshot.principalVariation.isEmpty()) {
                    "PV —"
                } else {
                    "PV ${snapshot.principalVariation.joinToString(" ")}"
                },
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.bodySmall,
                color = OnSurfaceMuted,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun EngineMetric(
    label: String,
    value: String?,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = MaterialTheme.shapes.small,
        color = SurfaceMuted,
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 7.dp, vertical = 5.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = value ?: "—",
                style = MaterialTheme.typography.labelMedium,
                color = OnBackground,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = OnSurfaceMuted,
                maxLines = 1,
            )
        }
    }
}

@Composable
private fun GameActions(
    gameOver: Boolean,
    busy: Boolean,
    onNewGame: () -> Unit,
    onRestart: () -> Unit,
    onResign: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier.testTag("game-actions"),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Button(
            onClick = onNewGame,
            enabled = !busy,
            modifier = Modifier
                .weight(1f)
                .fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 6.dp),
            shape = MaterialTheme.shapes.small,
            colors = ButtonDefaults.buttonColors(
                containerColor = Primary,
                contentColor = AppBackground,
            ),
        ) {
            Text("New game", maxLines = 1, style = MaterialTheme.typography.labelMedium)
        }
        OutlinedButton(
            onClick = onRestart,
            enabled = !busy,
            modifier = Modifier
                .weight(1f)
                .fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 6.dp),
            shape = MaterialTheme.shapes.small,
            border = BorderStroke(1.dp, Border),
        ) {
            Text("Restart", maxLines = 1, style = MaterialTheme.typography.labelMedium)
        }
        OutlinedButton(
            onClick = onResign,
            enabled = !busy && !gameOver,
            modifier = Modifier
                .weight(1f)
                .fillMaxSize(),
            contentPadding = PaddingValues(horizontal = 6.dp),
            shape = MaterialTheme.shapes.small,
            border = BorderStroke(1.dp, Danger.copy(alpha = 0.65f)),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = Danger),
        ) {
            Text("Resign", maxLines = 1, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
private fun PromotionDialog(
    moves: List<String>,
    onChoose: (String) -> Unit,
    onCancel: () -> Unit,
) {
    val ordered = listOf('q', 'r', 'b', 'n').mapNotNull { piece ->
        moves.firstOrNull { it.lastOrNull() == piece }
    }
    AlertDialog(
        onDismissRequest = onCancel,
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onCancel) {
                Text("Cancel")
            }
        },
        title = { Text("Choose promotion") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                ordered.forEach { move ->
                    Button(
                        onClick = { onChoose(move) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SurfaceMuted,
                            contentColor = OnBackground,
                        ),
                    ) {
                        Text(promotionName(move.last()))
                    }
                }
            }
        },
        containerColor = SurfaceElevated,
        titleContentColor = OnBackground,
        textContentColor = OnSurfaceMuted,
    )
}

private fun depthLabel(depth: Int): String = when (depth) {
    in 1..2 -> "Quick"
    in 3..5 -> "Balanced"
    in 6..8 -> "Strong"
    else -> "Deep"
}

private fun formatCount(value: Long): String = when {
    value >= 1_000_000 -> "%.1fM".format(value / 1_000_000.0)
    value >= 1_000 -> "%.0fk".format(value / 1_000.0)
    else -> value.toString()
}

private fun HumanSide.displayName(): String = when (this) {
    HumanSide.WHITE -> "White"
    HumanSide.BLACK -> "Black"
}

private fun pieceName(piece: Char): String = when (piece.lowercaseChar()) {
    'k' -> "king"
    'q' -> "queen"
    'r' -> "rook"
    'b' -> "bishop"
    'n' -> "knight"
    'p' -> "pawn"
    else -> error("unknown FEN piece: $piece")
}

private fun promotionName(piece: Char): String = when (piece) {
    'q' -> "Queen"
    'r' -> "Rook"
    'b' -> "Bishop"
    'n' -> "Knight"
    else -> error("unknown promotion piece: $piece")
}
