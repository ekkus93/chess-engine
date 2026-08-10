package com.ekkus93.chessapp

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.requiredSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SetupTitleInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun titleIsTaggedVisibleAndContained() {
        composeRule.setContent { RustChessTheme { Box(Modifier.requiredSize(360.dp, 640.dp)) { SetupScreen(ChessUiState(), {}, {}, {}) } } }
        composeRule.onNodeWithTag("setup-title").assertTextEquals("Rust Chess")
        composeRule.assertContained("setup-screen", listOf("setup-title"))
    }
}
