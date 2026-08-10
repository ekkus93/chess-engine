package com.ekkus93.chessapp

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ekkus93.chessengine.HumanSide

@Composable
internal fun ChessBoard(
    board: BoardPosition,
    orientation: HumanSide,
    selectedSquare: String?,
    legalTargets: Set<String>,
    lastMove: LastMoveSquares?,
    enabled: Boolean,
    onSquareTapped: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val files = visibleFiles(orientation)
    val ranks = visibleRanks(orientation)
    Column(
        modifier = modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(6.dp))
            .border(1.dp, Border, RoundedCornerShape(6.dp))
            .testTag("chess-board")
            .semantics { contentDescription = "Chess board" },
    ) {
        ranks.forEach { rank ->
            Row(modifier = Modifier.weight(1f)) {
                files.forEach { file ->
                    val square = "$file$rank"
                    val baseColor = if (isLightSquare(file, rank)) BoardLight else BoardDark
                    val isLastMove = square == lastMove?.source || square == lastMove?.destination
                    val isSelected = square == selectedSquare
                    val piece = board.pieces[square]
                    val isTarget = square in legalTargets
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxSize()
                            .background(
                                if (isLastMove) lerp(baseColor, PrimaryStrong, 0.30f) else baseColor,
                            )
                            .then(
                                if (enabled) {
                                    Modifier.clickable { onSquareTapped(square) }
                                } else {
                                    Modifier
                                },
                            )
                            .semantics {
                                selected = isSelected
                                contentDescription = buildString {
                                    append(square)
                                    piece?.let {
                                        append(' ')
                                        append(pieceName(it))
                                    }
                                    if (isLastMove) append(" last move")
                                    if (isSelected) append(" selected")
                                    if (isTarget) {
                                        if (piece == null) append(" legal target")
                                        else append(" legal capture")
                                    }
                                }
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        if (isSelected) {
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(BoardSelected)
                                    .border(2.dp, PrimaryStrong),
                            )
                        }
                        if (isTarget) {
                            Canvas(modifier = Modifier.fillMaxSize()) {
                                if (piece == null) {
                                    drawCircle(
                                        color = BoardLegalTarget,
                                        radius = size.minDimension * 0.12f,
                                    )
                                } else {
                                    drawCircle(
                                        color = BoardLegalTarget,
                                        radius = size.minDimension * 0.38f,
                                        style = Stroke(width = size.minDimension * 0.07f),
                                    )
                                }
                            }
                        }
                        piece?.let {
                            ChessPiece(
                                piece = it,
                                modifier = Modifier.fillMaxSize(0.80f),
                            )
                        }
                        if (file == files.first()) {
                            Text(
                                text = rank.toString(),
                                modifier = Modifier
                                    .align(Alignment.TopStart)
                                    .padding(2.dp),
                                fontSize = 8.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = Color.Black.copy(alpha = 0.58f),
                            )
                        }
                        if (rank == ranks.last()) {
                            Text(
                                text = file.toString(),
                                modifier = Modifier
                                    .align(Alignment.BottomEnd)
                                    .padding(2.dp),
                                fontSize = 8.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = Color.Black.copy(alpha = 0.58f),
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun pieceName(piece: Char): String = when (piece.lowercaseChar()) {
    'k' -> "king"
    'q' -> "queen"
    'r' -> "rook"
    'b' -> "bishop"
    'n' -> "knight"
    'p' -> "pawn"
    else -> error("unknown FEN piece: $piece")
}
