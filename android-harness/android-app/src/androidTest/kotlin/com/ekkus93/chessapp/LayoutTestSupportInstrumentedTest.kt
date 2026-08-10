package com.ekkus93.chessapp

import androidx.compose.ui.geometry.Rect
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LayoutTestSupportInstrumentedTest {
    @Test
    fun toleranceIsExplicitAndBounded() {
        val base = Rect(0f, 0f, 100f, 100f)
        assertTrue(boundsApproximatelyEqual(base, Rect(0.25f, 0.25f, 100.25f, 100.25f)))
        assertFalse(boundsApproximatelyEqual(base, Rect(0.75f, 0f, 100f, 100f)))
    }

    @Test
    fun pxNormalizationPreservesDpMeaningAtNonUnitDensity() {
        assertEquals(Rect(0f, 0f, 10f, 5f), pxRectToDp(Rect(0f, 0f, 20f, 10f), 2f))
    }
}
