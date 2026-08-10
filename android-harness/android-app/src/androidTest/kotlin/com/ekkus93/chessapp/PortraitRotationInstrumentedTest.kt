package com.ekkus93.chessapp

import android.content.pm.ActivityInfo
import android.content.res.Configuration
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PortraitRotationInstrumentedTest {
    @get:Rule val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun rotationRequestKeepsPortraitAndPreservesPlayedMove() {
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        try {
            composeRule.onNodeWithTag("start-game").performClick()
            composeRule.waitUntil(30_000) {
                runCatching { composeRule.onNodeWithContentDescription("e2 pawn").fetchSemanticsNode() }.isSuccess
            }
            composeRule.onNodeWithContentDescription("e2 pawn").performClick()
            composeRule.onNodeWithContentDescription("e4 legal target").performClick()
            composeRule.waitUntil(30_000) {
                runCatching {
                    composeRule.onNodeWithContentDescription("e4 pawn", substring = true).fetchSemanticsNode()
                }.isSuccess
            }

            device.setOrientationLeft()
            device.waitForIdle()
            composeRule.waitForIdle()

            assertEquals(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT, composeRule.activity.requestedOrientation)
            assertEquals(Configuration.ORIENTATION_PORTRAIT, composeRule.activity.resources.configuration.orientation)
            composeRule.onNodeWithTag("chess-board").assertExists()
            composeRule.onNodeWithContentDescription("e2 pawn", substring = true).assertDoesNotExist()
            composeRule.onNodeWithContentDescription("e4 pawn", substring = true).assertExists()
        } finally {
            device.setOrientationNatural()
            device.waitForIdle()
        }
    }
}
