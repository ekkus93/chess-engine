package com.ekkus93.chessapp

import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import kotlin.math.abs

internal const val BOUNDS_TOLERANCE_DP = 0.5f

internal fun pxRectToDp(rect: Rect, density: Float): Rect {
    require(density > 0f)
    return Rect(rect.left / density, rect.top / density, rect.right / density, rect.bottom / density)
}

internal fun boundsApproximatelyEqual(a: Rect, b: Rect, toleranceDp: Float = BOUNDS_TOLERANCE_DP): Boolean =
    abs(a.left - b.left) <= toleranceDp &&
        abs(a.top - b.top) <= toleranceDp &&
        abs(a.right - b.right) <= toleranceDp &&
        abs(a.bottom - b.bottom) <= toleranceDp

internal fun ComposeContentTestRule.boundsDp(tag: String): Rect {
    val density = InstrumentationRegistry.getInstrumentation().targetContext.resources.displayMetrics.density
    return pxRectToDp(onNodeWithTag(tag).fetchSemanticsNode().boundsInRoot, density)
}

internal fun ComposeContentTestRule.assertContained(rootTag: String, childTags: List<String>) {
    val root = boundsDp(rootTag)
    childTags.forEach { tag ->
        val child = boundsDp(tag)
        assertTrue("$tag left edge escaped $rootTag", child.left + BOUNDS_TOLERANCE_DP >= root.left)
        assertTrue("$tag top edge escaped $rootTag", child.top + BOUNDS_TOLERANCE_DP >= root.top)
        assertTrue("$tag right edge escaped $rootTag", child.right - BOUNDS_TOLERANCE_DP <= root.right)
        assertTrue("$tag bottom edge escaped $rootTag", child.bottom - BOUNDS_TOLERANCE_DP <= root.bottom)
        assertTrue("$tag must have positive width", child.width > 0f)
        assertTrue("$tag must have positive height", child.height > 0f)
    }
}

internal fun ComposeContentTestRule.assertNoRootScroll(tag: String) {
    val node = onNodeWithTag(tag).fetchSemanticsNode()
    assertFalse("$tag must not expose a root scroll action", node.config.contains(SemanticsActions.ScrollBy))
}

internal fun ComposeContentTestRule.assertSquare(tag: String) {
    val value = boundsDp(tag)
    assertTrue("$tag must remain square", abs(value.width - value.height) <= BOUNDS_TOLERANCE_DP)
}

internal fun assertBoundsEqual(expected: Rect, actual: Rect, label: String) {
    assertTrue("$label bounds changed: expected=$expected actual=$actual", boundsApproximatelyEqual(expected, actual))
}
