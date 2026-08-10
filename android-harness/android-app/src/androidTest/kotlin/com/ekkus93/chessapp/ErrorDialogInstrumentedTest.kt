package com.ekkus93.chessapp

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ErrorDialogInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun errorMessageRendersAndDismissesOnlyThroughCallback() {
        var dismissed = false
        val message = "Deterministic engine failure 8472"
        composeRule.setContent { RustChessTheme { ChessEngineErrorDialog(message) { dismissed = true } } }
        composeRule.onNodeWithText(message).assertExists()
        composeRule.onNodeWithText("OK").performClick()
        composeRule.runOnIdle { assertTrue(dismissed) }
    }
}
