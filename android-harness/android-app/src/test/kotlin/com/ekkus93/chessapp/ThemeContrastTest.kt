package com.ekkus93.chessapp

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import kotlin.math.max
import kotlin.math.min
import org.junit.Assert.assertTrue
import org.junit.Test

class ThemeContrastTest {
    private fun linear(c: Float): Double =
        if (c <= 0.04045f) c.toDouble() / 12.92 else Math.pow((c.toDouble() + 0.055) / 1.055, 2.4)

    private fun luminance(c: Color): Double =
        0.2126 * linear(c.red) + 0.7152 * linear(c.green) + 0.0722 * linear(c.blue)

    private fun contrast(a: Color, b: Color): Double {
        val l1 = luminance(a)
        val l2 = luminance(b)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    }

    private fun composite(fg: Color, bg: Color): Color {
        val a = fg.alpha + bg.alpha * (1f - fg.alpha)
        if (a == 0f) return Color.Transparent
        fun channel(f: Float, b: Float): Float = (f * fg.alpha + b * bg.alpha * (1f - fg.alpha)) / a
        return Color(channel(fg.red, bg.red), channel(fg.green, bg.green), channel(fg.blue, bg.blue), a)
    }

    private fun requireRatio(label: String, fg: Color, bg: Color, minimum: Double) {
        val value = contrast(fg, bg)
        assertTrue("$label contrast $value < $minimum", value >= minimum)
    }

    private fun pieceBoundary(label: String, fill: Color, stroke: Color, bg: Color) {
        val value = max(contrast(fill, bg), contrast(stroke, bg))
        assertTrue("$label silhouette boundary contrast $value < 3", value >= 3.0)
    }

    @Test
    fun textAndControlPairsMeetAa() {
        requireRatio("OnBackground/AppBackground", OnBackground, AppBackground, 4.5)
        requireRatio("OnSurfaceMuted/Surface", OnSurfaceMuted, Surface, 4.5)
        requireRatio("OnSurfaceMuted/SurfaceMuted", OnSurfaceMuted, SurfaceMuted, 4.5)
        requireRatio("primary label", AppBackground, Primary, 4.5)
        requireRatio("strong primary label", AppBackground, PrimaryStrong, 4.5)
        requireRatio("danger label", AppBackground, Danger, 4.5)
        requireRatio("resign dialog confirm", Danger, SurfaceElevated, 4.5)
        requireRatio("coordinate on light", CoordinateLabelOnLight, BoardLight, 4.5)
        requireRatio("coordinate on dark", CoordinateLabelOnDark, BoardDark, 4.5)
    }

    @Test
    fun piecesAndLegalTargetsRemainRecognizableAcrossBoardTreatments() {
        for ((squareName, base) in listOf("light" to BoardLight, "dark" to BoardDark)) {
            val backgrounds = listOf(
                "base" to base,
                "last" to lerp(base, BoardLastMove, 0.30f),
                "selected" to composite(BoardSelected, base),
                "last+selected" to composite(BoardSelected, lerp(base, BoardLastMove, 0.30f)),
            )
            for ((treatment, bg) in backgrounds) {
                pieceBoundary("light piece/$squareName/$treatment", PieceLightFill, PieceLightStroke, bg)
                pieceBoundary("dark piece/$squareName/$treatment", PieceDarkFill, PieceDarkStroke, bg)
                val marker = composite(BoardLegalTarget, bg)
                requireRatio("legal target/$squareName/$treatment", marker, bg, 3.0)
            }
        }
    }
}
