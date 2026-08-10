package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performScrollToIndex
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MoveHistoryAutoScrollInstrumentedTest {
    @get:Rule
    val composeRule = createComposeRule()

    @Test
    fun newestRowStaysVisibleWhenHistoryWasAtBottom() {
        val moves = mutableStateOf(history(20))
        val listState = LazyListState()
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 120.dp)) {
                    MoveHistoryPanel(moves.value, listState)
                }
            }
        }

        composeRule.onNodeWithTag("moves-list").performScrollToIndex(19)
        composeRule.runOnIdle {
            moves.value = history(21)
        }
        composeRule.waitForIdle()

        composeRule.runOnIdle {
            assertEquals(20, listState.layoutInfo.visibleItemsInfo.last().index)
        }
    }

    @Test
    fun newRowDoesNotStealManualHistoricalPosition() {
        val moves = mutableStateOf(history(20))
        val listState = LazyListState()
        composeRule.setContent {
            RustChessTheme {
                Box(Modifier.requiredSize(360.dp, 120.dp)) {
                    MoveHistoryPanel(moves.value, listState)
                }
            }
        }

        composeRule.onNodeWithTag("moves-list").performScrollToIndex(4)
        var historicalIndex = -1
        composeRule.runOnIdle {
            historicalIndex = listState.firstVisibleItemIndex
            assertTrue(historicalIndex < 10)
            moves.value = history(21)
        }
        composeRule.waitForIdle()

        composeRule.runOnIdle {
            assertEquals(historicalIndex, listState.firstVisibleItemIndex)
            assertTrue(listState.layoutInfo.visibleItemsInfo.last().index < 20)
        }
    }

    private fun history(rows: Int): List<String> = List(rows * 2) { ply ->
        if (ply % 2 == 0) "Nf3" else "Nc6"
    }
}
