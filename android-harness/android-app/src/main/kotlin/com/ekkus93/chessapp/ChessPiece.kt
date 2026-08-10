package com.ekkus93.chessapp

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke

/**
 * First-party vector chess-piece artwork drawn entirely with Compose geometry.
 * No external font glyphs, images, or third-party piece assets are used.
 */
@Composable
internal fun ChessPiece(
    piece: Char,
    modifier: Modifier = Modifier,
) {
    val isWhite = piece.isUpperCase()
    val fill = if (isWhite) PieceLightFill else PieceDarkFill
    val stroke = if (isWhite) PieceLightStroke else PieceDarkStroke
    Canvas(modifier = modifier) {
        val side = size.minDimension
        val left = (size.width - side) / 2f
        val top = (size.height - side) / 2f
        when (piece.lowercaseChar()) {
            'p' -> drawPawn(left, top, side, fill, stroke)
            'n' -> drawKnight(left, top, side, fill, stroke)
            'b' -> drawBishop(left, top, side, fill, stroke)
            'r' -> drawRook(left, top, side, fill, stroke)
            'q' -> drawQueen(left, top, side, fill, stroke)
            'k' -> drawKing(left, top, side, fill, stroke)
            else -> error("unknown chess piece: $piece")
        }
    }
}

private fun DrawScope.drawPawn(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    drawCircle(
        color = fill,
        radius = side * 0.13f,
        center = Offset(left + side * 0.5f, top + side * 0.27f),
    )
    drawCircle(
        color = stroke,
        radius = side * 0.13f,
        center = Offset(left + side * 0.5f, top + side * 0.27f),
        style = Stroke(width),
    )
    val body = Path().apply {
        moveTo(left + side * 0.43f, top + side * 0.39f)
        cubicTo(
            left + side * 0.43f,
            top + side * 0.55f,
            left + side * 0.35f,
            top + side * 0.64f,
            left + side * 0.31f,
            top + side * 0.72f,
        )
        lineTo(left + side * 0.69f, top + side * 0.72f)
        cubicTo(
            left + side * 0.65f,
            top + side * 0.64f,
            left + side * 0.57f,
            top + side * 0.55f,
            left + side * 0.57f,
            top + side * 0.39f,
        )
        close()
    }
    drawPath(body, fill)
    drawPath(body, stroke, style = Stroke(width, join = StrokeJoin.Round))
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawKnight(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    val body = Path().apply {
        moveTo(left + side * 0.31f, top + side * 0.68f)
        cubicTo(
            left + side * 0.32f,
            top + side * 0.56f,
            left + side * 0.42f,
            top + side * 0.48f,
            left + side * 0.48f,
            top + side * 0.41f,
        )
        lineTo(left + side * 0.34f, top + side * 0.42f)
        lineTo(left + side * 0.43f, top + side * 0.22f)
        lineTo(left + side * 0.65f, top + side * 0.31f)
        cubicTo(
            left + side * 0.75f,
            top + side * 0.38f,
            left + side * 0.71f,
            top + side * 0.56f,
            left + side * 0.62f,
            top + side * 0.68f,
        )
        close()
    }
    drawPath(body, fill)
    drawPath(body, stroke, style = Stroke(width, join = StrokeJoin.Round))
    drawCircle(
        color = stroke,
        radius = side * 0.025f,
        center = Offset(left + side * 0.57f, top + side * 0.34f),
    )
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawBishop(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    drawOval(
        color = fill,
        topLeft = Offset(left + side * 0.37f, top + side * 0.19f),
        size = Size(side * 0.26f, side * 0.32f),
    )
    drawOval(
        color = stroke,
        topLeft = Offset(left + side * 0.37f, top + side * 0.19f),
        size = Size(side * 0.26f, side * 0.32f),
        style = Stroke(width),
    )
    drawLine(
        color = stroke,
        start = Offset(left + side * 0.53f, top + side * 0.22f),
        end = Offset(left + side * 0.45f, top + side * 0.40f),
        strokeWidth = width,
    )
    val body = Path().apply {
        moveTo(left + side * 0.43f, top + side * 0.48f)
        lineTo(left + side * 0.31f, top + side * 0.71f)
        lineTo(left + side * 0.69f, top + side * 0.71f)
        lineTo(left + side * 0.57f, top + side * 0.48f)
        close()
    }
    drawPath(body, fill)
    drawPath(body, stroke, style = Stroke(width, join = StrokeJoin.Round))
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawRook(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    val rook = Path().apply {
        moveTo(left + side * 0.30f, top + side * 0.22f)
        lineTo(left + side * 0.30f, top + side * 0.38f)
        lineTo(left + side * 0.36f, top + side * 0.42f)
        lineTo(left + side * 0.38f, top + side * 0.70f)
        lineTo(left + side * 0.62f, top + side * 0.70f)
        lineTo(left + side * 0.64f, top + side * 0.42f)
        lineTo(left + side * 0.70f, top + side * 0.38f)
        lineTo(left + side * 0.70f, top + side * 0.22f)
        lineTo(left + side * 0.59f, top + side * 0.22f)
        lineTo(left + side * 0.59f, top + side * 0.31f)
        lineTo(left + side * 0.53f, top + side * 0.31f)
        lineTo(left + side * 0.53f, top + side * 0.22f)
        lineTo(left + side * 0.47f, top + side * 0.22f)
        lineTo(left + side * 0.47f, top + side * 0.31f)
        lineTo(left + side * 0.41f, top + side * 0.31f)
        lineTo(left + side * 0.41f, top + side * 0.22f)
        close()
    }
    drawPath(rook, fill)
    drawPath(rook, stroke, style = Stroke(width, join = StrokeJoin.Round))
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawQueen(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    val crown = Path().apply {
        moveTo(left + side * 0.28f, top + side * 0.31f)
        lineTo(left + side * 0.36f, top + side * 0.45f)
        lineTo(left + side * 0.42f, top + side * 0.27f)
        lineTo(left + side * 0.50f, top + side * 0.45f)
        lineTo(left + side * 0.58f, top + side * 0.27f)
        lineTo(left + side * 0.64f, top + side * 0.45f)
        lineTo(left + side * 0.72f, top + side * 0.31f)
        lineTo(left + side * 0.64f, top + side * 0.70f)
        lineTo(left + side * 0.36f, top + side * 0.70f)
        close()
    }
    drawPath(crown, fill)
    drawPath(crown, stroke, style = Stroke(width, join = StrokeJoin.Round))
    for (x in listOf(0.28f, 0.42f, 0.58f, 0.72f)) {
        drawCircle(
            color = fill,
            radius = side * 0.035f,
            center = Offset(left + side * x, top + side * 0.27f),
        )
        drawCircle(
            color = stroke,
            radius = side * 0.035f,
            center = Offset(left + side * x, top + side * 0.27f),
            style = Stroke(width * 0.75f),
        )
    }
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawKing(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    drawLine(
        color = stroke,
        start = Offset(left + side * 0.50f, top + side * 0.16f),
        end = Offset(left + side * 0.50f, top + side * 0.34f),
        strokeWidth = width,
    )
    drawLine(
        color = stroke,
        start = Offset(left + side * 0.43f, top + side * 0.23f),
        end = Offset(left + side * 0.57f, top + side * 0.23f),
        strokeWidth = width,
    )
    val body = Path().apply {
        moveTo(left + side * 0.39f, top + side * 0.34f)
        cubicTo(
            left + side * 0.31f,
            top + side * 0.45f,
            left + side * 0.36f,
            top + side * 0.59f,
            left + side * 0.40f,
            top + side * 0.70f,
        )
        lineTo(left + side * 0.60f, top + side * 0.70f)
        cubicTo(
            left + side * 0.64f,
            top + side * 0.59f,
            left + side * 0.69f,
            top + side * 0.45f,
            left + side * 0.61f,
            top + side * 0.34f,
        )
        close()
    }
    drawPath(body, fill)
    drawPath(body, stroke, style = Stroke(width, join = StrokeJoin.Round))
    drawPieceBase(left, top, side, fill, stroke)
}

private fun DrawScope.drawPieceBase(
    left: Float,
    top: Float,
    side: Float,
    fill: Color,
    stroke: Color,
) {
    val width = side * 0.045f
    drawRoundRect(
        color = fill,
        topLeft = Offset(left + side * 0.25f, top + side * 0.70f),
        size = Size(side * 0.50f, side * 0.12f),
        cornerRadius = CornerRadius(side * 0.035f),
    )
    drawRoundRect(
        color = stroke,
        topLeft = Offset(left + side * 0.25f, top + side * 0.70f),
        size = Size(side * 0.50f, side * 0.12f),
        cornerRadius = CornerRadius(side * 0.035f),
        style = Stroke(width),
    )
}
