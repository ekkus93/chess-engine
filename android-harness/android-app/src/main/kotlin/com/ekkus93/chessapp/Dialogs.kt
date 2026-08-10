package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ekkus93.chessengine.HumanSide

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
