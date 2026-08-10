package com.ekkus93.chessapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
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
                    onRetryCleanup = viewModel::returnToSetup,
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
        ChessEngineErrorDialog(
            message = message,
            onDismiss = viewModel::clearError,
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
        ConfirmationDialog(
            confirmation = pending,
            onCancel = { confirmation = null },
            onConfirm = {
                confirmation = null
                when (pending) {
                    Confirmation.NEW_GAME -> viewModel.returnToSetup()
                    Confirmation.RESTART -> viewModel.restartGame()
                    Confirmation.RESIGN -> viewModel.resign()
                }
            },
        )
    }
}
