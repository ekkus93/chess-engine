package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ReviewFixInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun newestMoveMarkerTargetsOnlyLatestPly() {
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 160.dp)) {
                    MoveHistoryPanel(listOf("e4", "c5", "Nf3"), LazyListState())
                }
            }
        }
        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(1)
        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nf3")
    }

    @Test
    fun appendingMoveTransfersNewestMarker() {
        val moves = mutableStateOf(listOf("e4", "c5", "Nf3"))
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 160.dp)) {
                    MoveHistoryPanel(moves.value, LazyListState())
                }
            }
        }
        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nf3")
        composeRule.runOnUiThread { moves.value = moves.value + "Nc6" }
        composeRule.waitForIdle()
        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(1)
        composeRule.onNodeWithTag("latest-move").assertTextEquals("Nc6")
    }

    @Test
    fun emptyHistoryHasNoNewestMarker() {
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 160.dp)) {
                    MoveHistoryPanel(emptyList(), LazyListState())
                }
            }
        }
        composeRule.onAllNodesWithTag("latest-move").assertCountEquals(0)
    }
}
