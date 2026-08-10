package com.ekkus93.chessapp

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ekkus93.chessengine.HumanSide

internal enum class Confirmation {
    NEW_GAME,
    RESTART,
    RESIGN,
}

@Composable
internal fun ConfirmationDialog(
    confirmation: Confirmation,
    onCancel: () -> Unit,
    onConfirm: () -> Unit,
) {
    val (title, text, confirmLabel) = when (confirmation) {
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
        onDismissRequest = onCancel,
        dismissButton = {
            TextButton(onClick = onCancel) {
                Text("Cancel")
            }
        },
        confirmButton = {
            TextButton(
                colors = ButtonDefaults.textButtonColors(
                    contentColor = if (confirmation == Confirmation.RESIGN) Danger else PrimaryStrong,
                ),
                onClick = onConfirm,
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

@Composable
internal fun ChessEngineErrorDialog(
    message: String,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("OK")
            }
        },
        title = { Text("Chess engine error") },
        text = {
            Box(
                modifier = Modifier
                    .heightIn(max = 240.dp)
                    .verticalScroll(rememberScrollState()),
            ) {
                Text(message)
            }
        },
        containerColor = SurfaceElevated,
        titleContentColor = OnBackground,
        textContentColor = OnSurfaceMuted,
    )
}

@Composable
internal fun PromotionDialog(
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

internal fun HumanSide.displayName(): String = when (this) {
    HumanSide.WHITE -> "White"
    HumanSide.BLACK -> "Black"
}

private fun promotionName(piece: Char): String = when (piece) {
    'q' -> "Queen"
    'r' -> "Rook"
    'b' -> "Bishop"
    'n' -> "Knight"
    else -> error("unknown promotion piece: $piece")
}
