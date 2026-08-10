package com.ekkus93.chessapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

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
