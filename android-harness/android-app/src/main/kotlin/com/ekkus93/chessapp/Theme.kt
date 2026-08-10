package com.ekkus93.chessapp

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.shape.RoundedCornerShape

internal val AppBackground = Color(0xFF0B1220)
internal val Surface = Color(0xFF121B2B)
internal val SurfaceElevated = Color(0xFF18243A)
internal val SurfaceMuted = Color(0xFF0F172A)
internal val Border = Color(0xFF2A3A52)
internal val Primary = Color(0xFF2DD4BF)
internal val PrimaryStrong = Color(0xFF5EEAD4)
internal val OnBackground = Color(0xFFF8FAFC)
internal val OnSurfaceMuted = Color(0xFF94A3B8)
internal val Success = Color(0xFF34D399)
internal val Warning = Color(0xFFFBBF24)
internal val Danger = Color(0xFFF87171)
internal val MoveLatest = PrimaryStrong
internal val BoardLight = Color(0xFFE7D7C4)
internal val BoardDark = Color(0xFF806A58)
internal val BoardLastMove = PrimaryStrong
internal val BoardSelected = Color(0x992DD4BF)
internal val BoardLegalTarget = Color(0xCC2DD4BF)
internal val PieceLightFill = Color(0xFFF7F3EA)
internal val PieceDarkFill = Color(0xFF172033)
internal val PieceLightStroke = Color(0xFF26364D)
internal val PieceDarkStroke = Color(0xFFE8EEF7)
internal val CoordinateLabelOnLight = AppBackground
internal val CoordinateLabelOnDark = OnBackground

private val ChessColorScheme = darkColorScheme(
    primary = Primary,
    onPrimary = AppBackground,
    primaryContainer = Color(0xFF134E4A),
    onPrimaryContainer = OnBackground,
    secondary = PrimaryStrong,
    onSecondary = AppBackground,
    tertiary = Warning,
    onTertiary = AppBackground,
    background = AppBackground,
    onBackground = OnBackground,
    surface = Surface,
    onSurface = OnBackground,
    surfaceVariant = SurfaceElevated,
    onSurfaceVariant = OnSurfaceMuted,
    outline = Border,
    error = Danger,
    onError = AppBackground,
)

private val ChessTypography = Typography(
    headlineLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 32.sp,
        lineHeight = 38.sp,
        letterSpacing = (-0.4).sp,
    ),
    headlineSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 22.sp,
        lineHeight = 28.sp,
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 19.sp,
        lineHeight = 24.sp,
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 15.sp,
        lineHeight = 20.sp,
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 22.sp,
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 19.sp,
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp,
    ),
    labelLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        lineHeight = 18.sp,
    ),
    labelMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
    ),
)

private val ChessShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small = RoundedCornerShape(10.dp),
    medium = RoundedCornerShape(14.dp),
    large = RoundedCornerShape(20.dp),
    extraLarge = RoundedCornerShape(28.dp),
)

@Composable
internal fun RustChessTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ChessColorScheme,
        typography = ChessTypography,
        shapes = ChessShapes,
        content = content,
    )
}
