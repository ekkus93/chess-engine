package com.ekkus93.chessapp

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.ekkus93.chessengine.HumanSide
import kotlin.math.roundToInt

@Composable
internal fun SetupScreen(
    state: ChessUiState,
    onSideChanged: (HumanSide) -> Unit,
    onDepthChanged: (Int) -> Unit,
    onStart: () -> Unit,
    onRetryCleanup: () -> Unit = {},
) {
    val configurationEnabled = !state.busy && !state.cleanupRequired
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
                    ChessPiece(piece = 'N', modifier = Modifier.size(46.dp))
                }
            }
            Text(
                text = "Rust Chess",
                style = MaterialTheme.typography.headlineLarge,
                color = OnBackground,
            )
            Text(
                text = if (state.cleanupRequired) {
                    "Cleanup must finish before another game can start."
                } else {
                    "Play against the Rust chess engine."
                },
                style = MaterialTheme.typography.bodyLarge,
                color = if (state.cleanupRequired) Warning else OnSurfaceMuted,
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
                        enabled = configurationEnabled,
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
                        onValueChange = { onDepthChanged(it.roundToInt().coerceIn(1, 12)) },
                        valueRange = 1f..12f,
                        steps = 0,
                        enabled = configurationEnabled,
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
                        Text(
                            "Faster",
                            style = MaterialTheme.typography.bodySmall,
                            color = OnSurfaceMuted,
                        )
                        Text(
                            "Stronger",
                            style = MaterialTheme.typography.bodySmall,
                            color = OnSurfaceMuted,
                        )
                    }
                }
            }
        }

        Button(
            onClick = if (state.cleanupRequired) onRetryCleanup else onStart,
            enabled = !state.busy,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
                .testTag(if (state.cleanupRequired) "retry-cleanup" else "start-game"),
            shape = MaterialTheme.shapes.medium,
            colors = ButtonDefaults.buttonColors(
                containerColor = if (state.cleanupRequired) Warning else Primary,
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
                Text(
                    if (state.cleanupRequired) "Retry cleanup" else "Start game",
                    style = MaterialTheme.typography.labelLarge,
                )
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
            .height(54.dp)
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
                        this.selected = isSelected
                        contentDescription = buildString {
                            append("Play as ${side.displayName()}")
                            if (isSelected) append(", selected")
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (isSelected) "✓ ${side.displayName()}" else side.displayName(),
                    style = MaterialTheme.typography.labelLarge,
                    color = if (isSelected) PrimaryStrong else OnSurfaceMuted,
                )
            }
        }
    }
}

internal fun depthLabel(depth: Int): String = when (depth) {
    in 1..2 -> "Quick"
    in 3..5 -> "Balanced"
    in 6..8 -> "Strong"
    in 9..12 -> "Deep"
    else -> error("engine depth must be between 1 and 12")
}
