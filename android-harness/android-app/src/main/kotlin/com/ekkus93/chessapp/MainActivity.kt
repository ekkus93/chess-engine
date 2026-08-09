package com.ekkus93.chessapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
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

@Composable
fun ChessApp(
    viewModel: ChessViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var confirmation by remember { mutableStateOf<Confirmation?>(null) }

    Scaffold { padding ->
        Surface(
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
                "The current game will be closed and you can choose a new side and depth.",
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
        )
    }
}

@Composable
private fun SetupScreen(
    state: ChessUiState,
    onSideChanged: (HumanSide) -> Unit,
    onDepthChanged: (Int) -> Unit,
    onStart: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp)
            .testTag("setup-screen"),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Text(
            text = "Rust Chess",
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = "Play against the native Rust engine. Game rules, move validation, and engine turns are controlled by the shared Rust application layer.",
            style = MaterialTheme.typography.bodyLarge,
        )

        Text("Play as", style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            FilterChip(
                selected = state.humanSide == HumanSide.WHITE,
                onClick = { onSideChanged(HumanSide.WHITE) },
                label = { Text("White") },
                enabled = !state.busy,
            )
            FilterChip(
                selected = state.humanSide == HumanSide.BLACK,
                onClick = { onSideChanged(HumanSide.BLACK) },
                label = { Text("Black") },
                enabled = !state.busy,
            )
        }

        Text(
            text = "Engine depth ${state.engineDepth}",
            style = MaterialTheme.typography.titleMedium,
        )
        Slider(
            value = state.engineDepth.toFloat(),
            onValueChange = { onDepthChanged(it.toInt().coerceIn(1, 12)) },
            valueRange = 1f..12f,
            steps = 10,
            enabled = !state.busy,
            modifier = Modifier.semantics {
                contentDescription = "Engine depth ${state.engineDepth}"
            },
        )
        Text(
            text = "Higher depth is stronger but can take longer on a phone.",
            style = MaterialTheme.typography.bodySmall,
        )

        Button(
            onClick = onStart,
            enabled = !state.busy,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (state.busy) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                )
            } else {
                Text("Start game")
            }
        }
    }
}

@Composable
private fun GameScreen(
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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp)
            .testTag("game-screen"),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        GameStatusCard(snapshot)
        ChessBoard(
            board = board,
            orientation = snapshot.humanSide,
            selectedSquare = state.selectedSquare,
            legalTargets = targets,
            enabled = !state.busy && snapshot.humanToMove,
            onSquareTapped = onSquareTapped,
        )
        GameActions(
            gameOver = snapshot.gameOver,
            busy = state.busy,
            onNewGame = onNewGame,
            onRestart = onRestart,
            onResign = onResign,
        )
        EngineCard(snapshot)
        MoveHistoryCard(snapshot.moves)
    }
}

@Composable
private fun GameStatusCard(snapshot: ChessGameSnapshot) {
    val title = when {
        snapshot.outcome != null -> snapshot.outcome
        snapshot.thinking -> "Engine thinking…"
        snapshot.humanToMove -> "Your move"
        else -> "Engine turn"
    }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            snapshot.statusMessage?.takeIf { it.isNotBlank() }?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium)
            }
            Text(
                text = "You are ${snapshot.humanSide.displayName()}",
                style = MaterialTheme.typography.bodySmall,
            )
            if (snapshot.thinking) {
                Spacer(Modifier.height(2.dp))
                androidx.compose.material3.LinearProgressIndicator(
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
    }
}

@Composable
private fun ChessBoard(
    board: BoardPosition,
    orientation: HumanSide,
    selectedSquare: String?,
    legalTargets: Set<String>,
    enabled: Boolean,
    onSquareTapped: (String) -> Unit,
) {
    val files = visibleFiles(orientation)
    val ranks = visibleRanks(orientation)
    val light = Color(0xFFF0D9B5)
    val dark = Color(0xFFB58863)
    val selected = MaterialTheme.colorScheme.primaryContainer
    val target = MaterialTheme.colorScheme.tertiaryContainer

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1f)
            .semantics { contentDescription = "Chess board" },
    ) {
        ranks.forEach { rank ->
            Row(modifier = Modifier.weight(1f)) {
                files.forEach { file ->
                    val square = "$file$rank"
                    val baseColor = if (((file - 'a') + rank) % 2 == 1) light else dark
                    val squareColor = when {
                        square == selectedSquare -> selected
                        square in legalTargets -> target
                        else -> baseColor
                    }
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxSize()
                            .background(squareColor)
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
                                    board.pieces[square]?.let { piece ->
                                        append(' ')
                                        append(pieceName(piece))
                                    }
                                    if (square == selectedSquare) append(" selected")
                                    if (square in legalTargets) append(" legal target")
                                }
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        board.pieces[square]?.let { piece ->
                            Text(
                                text = pieceGlyph(piece),
                                fontSize = 34.sp,
                                fontFamily = FontFamily.Serif,
                                color = Color.Black,
                            )
                        }
                        if (file == files.first()) {
                            Text(
                                text = rank.toString(),
                                modifier = Modifier
                                    .align(Alignment.TopStart)
                                    .padding(2.dp),
                                fontSize = 9.sp,
                                color = Color.Black.copy(alpha = 0.65f),
                            )
                        }
                        if (rank == ranks.last()) {
                            Text(
                                text = file.toString(),
                                modifier = Modifier
                                    .align(Alignment.BottomEnd)
                                    .padding(2.dp),
                                fontSize = 9.sp,
                                color = Color.Black.copy(alpha = 0.65f),
                            )
                        }
                    }
                }
            }
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
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Button(
                onClick = onNewGame,
                enabled = !busy,
                modifier = Modifier.weight(1f),
            ) {
                Text("New game")
            }
            OutlinedButton(
                onClick = onRestart,
                enabled = !busy,
                modifier = Modifier.weight(1f),
            ) {
                Text("Restart")
            }
        }
        OutlinedButton(
            onClick = onResign,
            enabled = !busy && !gameOver,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Resign")
        }
    }
}

@Composable
private fun EngineCard(snapshot: ChessGameSnapshot) {
    val hasMetrics = snapshot.engineDepth != null || snapshot.engineScore != null ||
        snapshot.engineNodes != null || snapshot.engineNps != null ||
        snapshot.engineElapsed != null || snapshot.principalVariation.isNotEmpty() ||
        snapshot.hashFullPerMille != null

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text("Engine", style = MaterialTheme.typography.titleMedium)
            if (!hasMetrics) {
                Text("No completed search metrics yet.")
            } else {
                MetricLine("Depth", snapshot.engineDepth?.toString())
                MetricLine("Score", snapshot.engineScore)
                MetricLine("Nodes", snapshot.engineNodes?.toString())
                MetricLine("NPS", snapshot.engineNps?.toString())
                MetricLine("Time", snapshot.engineElapsed)
                MetricLine(
                    "Hash",
                    snapshot.hashFullPerMille?.let { "$it‰" },
                )
                MetricLine(
                    "PV",
                    snapshot.principalVariation.takeIf { it.isNotEmpty() }?.joinToString(" "),
                )
            }
        }
    }
}

@Composable
private fun MetricLine(label: String, value: String?) {
    if (value != null) {
        Text("$label: $value", style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun MoveHistoryCard(moves: List<String>) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text("Moves", style = MaterialTheme.typography.titleMedium)
            if (moves.isEmpty()) {
                Text("No moves yet.")
            } else {
                moves.chunked(2).forEachIndexed { index, pair ->
                    Text(
                        buildString {
                            append(index + 1)
                            append(". ")
                            append(pair[0])
                            if (pair.size == 2) {
                                append("  ")
                                append(pair[1])
                            }
                        },
                        fontFamily = FontFamily.Monospace,
                    )
                }
            }
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
                    ) {
                        Text(promotionName(move.last()))
                    }
                }
            }
        },
    )
}

private fun HumanSide.displayName(): String = when (this) {
    HumanSide.WHITE -> "White"
    HumanSide.BLACK -> "Black"
}

private fun pieceGlyph(piece: Char): String = when (piece) {
    'K' -> "♔"
    'Q' -> "♕"
    'R' -> "♖"
    'B' -> "♗"
    'N' -> "♘"
    'P' -> "♙"
    'k' -> "♚"
    'q' -> "♛"
    'r' -> "♜"
    'b' -> "♝"
    'n' -> "♞"
    'p' -> "♟"
    else -> error("unknown FEN piece: $piece")
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
