package com.ekkus93.chessapp

import android.graphics.Bitmap
import android.os.Build
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.graphics.blue
import androidx.core.graphics.green
import androidx.core.graphics.red
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.io.FileOutputStream
import kotlin.math.abs
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SystemBarAppearanceInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun api35SystemBarsRenderDarkProductBackground() {
        assertEquals("permanent Android CI observation must run on API 35", 35, Build.VERSION.SDK_INT)
        composeRule.waitForIdle()

        val activity = composeRule.activity
        val window = activity.window
        val controller = WindowCompat.getInsetsController(window, window.decorView)
        assertFalse(controller.isAppearanceLightStatusBars)
        assertFalse(controller.isAppearanceLightNavigationBars)

        val insets = requireNotNull(ViewCompat.getRootWindowInsets(window.decorView))
        val statusHeight = insets.getInsets(WindowInsetsCompat.Type.statusBars()).top
        val navigationHeight = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom
        assertTrue("status bar inset must be visible", statusHeight > 0)
        assertTrue("navigation bar inset must be visible", navigationHeight > 0)

        val screenshot = requireNotNull(InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot())
        preserveScreenshot(screenshot)
        val expected = AppBackground.toArgb()
        val statusRatio = matchingRatio(
            screenshot,
            left = screenshot.width / 4,
            top = 0,
            right = screenshot.width * 3 / 4,
            bottom = statusHeight,
            expected = expected,
        )
        val navigationRatio = matchingRatio(
            screenshot,
            left = screenshot.width / 10,
            top = screenshot.height - navigationHeight,
            right = screenshot.width * 4 / 10,
            bottom = screenshot.height,
            expected = expected,
        )
        assertTrue("status bar product-background pixel ratio $statusRatio < 0.70", statusRatio >= 0.70)
        assertTrue("navigation bar product-background pixel ratio $navigationRatio < 0.70", navigationRatio >= 0.70)
    }

    private fun matchingRatio(
        bitmap: Bitmap,
        left: Int,
        top: Int,
        right: Int,
        bottom: Int,
        expected: Int,
    ): Double {
        var matches = 0L
        var total = 0L
        for (y in top.coerceAtLeast(0) until bottom.coerceAtMost(bitmap.height)) {
            for (x in left.coerceAtLeast(0) until right.coerceAtMost(bitmap.width)) {
                val actual = bitmap.getPixel(x, y)
                if (
                    abs(actual.red - expected.red) <= 12 &&
                    abs(actual.green - expected.green) <= 12 &&
                    abs(actual.blue - expected.blue) <= 12
                ) {
                    matches += 1
                }
                total += 1
            }
        }
        require(total > 0) { "system-bar pixel sample must not be empty" }
        return matches.toDouble() / total.toDouble()
    }

    private fun preserveScreenshot(bitmap: Bitmap) {
        val directory = File("/sdcard/Download/RustChessEvidence").apply { mkdirs() }
        FileOutputStream(File(directory, "system-bars-api35.png")).use { output ->
            check(bitmap.compress(Bitmap.CompressFormat.PNG, 100, output))
        }
    }
}
