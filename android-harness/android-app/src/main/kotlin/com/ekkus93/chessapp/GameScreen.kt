package com.ekkus93.chessapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
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
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ekkus93.chessengine.ChessGameSnapshot

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
    val moveListState = rememberLazyListState()

    LaunchedEffect(snapshot.moves.isEmpty()) {
        if (snapshot.moves.isEmpty()) {
            selectedTab = GameTab.MOVES
            moveListState.scrollToItem(0)
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
        val tabHeight = 40.dp
        val actionHeight = 48.dp
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
                    GameTab.MOVES -> MoveHistoryPanel(snapshot.sanMoves, moveListState)
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
                Spacer(Modifier.size(9.dp))
            } else {
                Box(
                    modifier = Modifier
                        .size(9.dp)
                        .background(
                            color = if (snapshot.gameOver) Warning else Success,
                            shape = androidx.compose.foundation.shape.CircleShape,
                        ),
                )
                Spacer(Modifier.size(9.dp))
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
                        this.selected = isSelected
                        contentDescription = buildString {
                            append(if (tab == GameTab.MOVES) "Moves tab" else "Engine tab")
                            if (isSelected) append(", selected")
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = buildString {
                        if (isSelected) append("✓ ")
                        append(if (tab == GameTab.MOVES) "Moves" else "Engine")
                    },
                    style = MaterialTheme.typography.labelLarge,
                    color = if (isSelected) PrimaryStrong else OnSurfaceMuted,
                )
            }
        }
    }
}