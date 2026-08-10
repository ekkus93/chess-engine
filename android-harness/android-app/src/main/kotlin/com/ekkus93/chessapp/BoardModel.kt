package com.ekkus93.chessapp

import com.ekkus93.chessengine.HumanSide

/** Presentation-only projection of authoritative Rust FEN. */
data class BoardPosition(
    val pieces: Map<String, Char>,
) {
    companion object {
        fun parse(fen: String): BoardPosition {
            val placement = fen.split(' ').firstOrNull()
                ?: error("FEN is missing piece placement")
            val ranks = placement.split('/')
            require(ranks.size == 8) { "FEN placement must contain eight ranks" }
            val pieces = mutableMapOf<String, Char>()
            ranks.forEachIndexed { rankIndex, encodedRank ->
                var fileIndex = 0
                encodedRank.forEach { token ->
                    if (token in '1'..'8') {
                        fileIndex += token.digitToInt()
                    } else {
                        require(token in "pnbrqkPNBRQK") {
                            "invalid FEN piece token: $token"
                        }
                        require(fileIndex < 8) { "FEN rank exceeds eight files" }
                        val file = 'a' + fileIndex
                        val rank = 8 - rankIndex
                        pieces["$file$rank"] = token
                        fileIndex += 1
                    }
                    require(fileIndex <= 8) { "FEN rank exceeds eight files" }
                }
                require(fileIndex == 8) { "FEN rank does not contain eight files" }
            }
            return BoardPosition(pieces)
        }
    }
}

data class LastMoveSquares(
    val source: String,
    val destination: String,
)

data class MoveRow(
    val number: Int,
    val white: String,
    val black: String?,
)

fun visibleFiles(side: HumanSide): List<Char> = when (side) {
    HumanSide.WHITE -> ('a'..'h').toList()
    HumanSide.BLACK -> ('h' downTo 'a').toList()
}

fun visibleRanks(side: HumanSide): List<Int> = when (side) {
    HumanSide.WHITE -> (8 downTo 1).toList()
    HumanSide.BLACK -> (1..8).toList()
}

fun isLightSquare(file: Char, rank: Int): Boolean {
    require(file in 'a'..'h') { "board file must be a through h" }
    require(rank in 1..8) { "board rank must be one through eight" }
    return ((file - 'a') + rank) % 2 == 0
}

fun candidateMoves(
    legalMoves: List<String>,
    from: String,
    to: String,
): List<String> = legalMoves.filter { move ->
    move.length >= 4 && move.substring(0, 2) == from && move.substring(2, 4) == to
}

fun selectableSources(legalMoves: List<String>): Set<String> = legalMoves
    .asSequence()
    .filter { it.length >= 4 }
    .map { it.substring(0, 2) }
    .toSet()

fun legalTargets(legalMoves: List<String>, from: String?): Set<String> {
    if (from == null) {
        return emptySet()
    }
    return legalMoves
        .asSequence()
        .filter { it.length >= 4 && it.substring(0, 2) == from }
        .map { it.substring(2, 4) }
        .toSet()
}

fun lastMoveSquares(moves: List<String>): LastMoveSquares? {
    val move = moves.lastOrNull() ?: return null
    require(move.length in 4..5) { "authoritative UCI move must contain four or five characters" }
    return LastMoveSquares(
        source = move.substring(0, 2),
        destination = move.substring(2, 4),
    )
}

fun moveRows(sanMoves: List<String>): List<MoveRow> = sanMoves
    .chunked(2)
    .mapIndexed { index, pair ->
        MoveRow(
            number = index + 1,
            white = pair[0],
            black = pair.getOrNull(1),
        )
    }
