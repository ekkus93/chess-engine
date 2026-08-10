package com.ekkus93.chessapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.ekkus93.chessengine.ChessGameSnapshot

@Composable
internal fun MoveHistoryPanel(
    sanMoves: List<String>,
    listState: LazyListState,
) {
    val rows = remember(sanMoves) { moveRows(sanMoves) }
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
internal fun EnginePanel(snapshot: ChessGameSnapshot) {
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
internal fun GameActions(
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

private fun formatCount(value: Long): String = when {
    value >= 1_000_000 -> "%.1fM".format(value / 1_000_000.0)
    value >= 1_000 -> "%.0fk".format(value / 1_000.0)
    else -> value.toString()
}
