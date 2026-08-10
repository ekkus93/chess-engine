package com.ekkus93.chessapp

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PromotionDialogInstrumentedTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun allPromotionButtonsReturnAuthoritativeMove() {
        var chosen: String? = null
        val moves = listOf("e7e8q", "e7e8r", "e7e8b", "e7e8n")
        composeRule.setContent { RustChessTheme { PromotionDialog(moves, { chosen = it }, {}) } }
        for ((label, expected) in listOf("Queen" to "e7e8q", "Rook" to "e7e8r", "Bishop" to "e7e8b", "Knight" to "e7e8n")) {
            composeRule.onNodeWithText(label).performClick()
            composeRule.runOnIdle { assertEquals(expected, chosen) }
        }
    }
}
