package com.ekkus93.chessengine

import java.io.File
import java.util.LinkedHashMap
import java.util.concurrent.TimeUnit
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout

class PromotionPathEvidenceTest {
    private data class State(
        val fen: String,
        val humanMoves: List<String>,
    )

    @Test
    @Timeout(value = 20, unit = TimeUnit.MINUTES)
    fun boundedRealEngineSearchRecordsPromotionPathEvidence() {
        val evidenceFile = File(
            System.getenv("PROMOTION_EVIDENCE_PATH")
                ?: error("PROMOTION_EVIDENCE_PATH must be set by the evidence workflow"),
        )
        evidenceFile.parentFile?.mkdirs()

        val report = mutableListOf<String>()
        report += "SEARCH=real-jni-chess-engine"
        report += "HUMAN_SIDE=white"
        report += "MAX_HUMAN_TURNS=$MAX_HUMAN_TURNS"
        report += "BEAM_WIDTH=$BEAM_WIDTH"
        report += "BRANCH_CAP=$BRANCH_CAP"
        report += "OPPONENT_POLICY=opening-book-else-exact-depth-1"

        ChessEngine.create().use { engine ->
            engine.resetPosition()
            var beam: List<State> = listOf(State(engine.fen(), emptyList()))
            var foundPromotion: State? = null
            var foundMove: String? = null

            for (turn in 1..MAX_HUMAN_TURNS) {
                val candidates = LinkedHashMap<String, State>()
                var expanded = 0
                var searchedReplies = 0

                for (state in beam) {
                    engine.setPosition(state.fen)
                    val positionFen = engine.fen()
                    val legalMoves: List<String> = engine.legalMoves()
                        .sortedWith(
                            compareByDescending<String> { move -> movePriority(positionFen, move) }
                                .thenBy { move -> move },
                        )
                        .take(BRANCH_CAP)

                    for (humanMove in legalMoves) {
                        expanded += 1
                        if (isPromotionMove(humanMove)) {
                            foundPromotion = state
                            foundMove = humanMove
                            break
                        }

                        engine.setPosition(state.fen)
                        engine.playMove(humanMove)
                        if (engine.gameStatus().kind != GameStatusKind.ONGOING) {
                            continue
                        }

                        val reply = engine.openingBookMove() ?: run {
                            val result = engine.search(SearchRequest(depth = 1)).await()
                            assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                            assertEquals(SearchFallbackKind.NONE, result.fallbackKind)
                            searchedReplies += 1
                            result.bestMove ?: error("depth-1 opponent search returned no move in ongoing game")
                        }
                        engine.playMove(reply)
                        if (engine.gameStatus().kind != GameStatusKind.ONGOING) {
                            continue
                        }

                        val next = State(
                            fen = engine.fen(),
                            humanMoves = state.humanMoves + humanMove,
                        )
                        candidates.putIfAbsent(next.fen, next)
                    }
                    if (foundMove != null) {
                        break
                    }
                }

                report += "TURN_$turn beam=${beam.size} expanded=$expanded unique=${candidates.size} depth1_replies=$searchedReplies"
                if (foundMove != null) {
                    break
                }

                beam = candidates.values
                    .sortedWith(
                        compareByDescending<State> { state -> positionPriority(state.fen) }
                            .thenBy { state -> state.humanMoves.joinToString(" ") },
                    )
                    .take(BEAM_WIDTH)

                if (beam.isEmpty()) {
                    report += "STOP=no-continuing-states"
                    break
                }
            }

            if (foundMove != null) {
                report += "RESULT=FOUND"
                report += "FOUND_MOVE=$foundMove"
                report += "HUMAN_PATH=${foundPromotion!!.humanMoves.joinToString(" ")}"
                evidenceFile.writeText(report.joinToString("\n", postfix = "\n"))
                error("bounded search found a promotion path; documented blocker is invalid")
            }
        }

        report += "RESULT=NOT_FOUND"
        evidenceFile.writeText(report.joinToString("\n", postfix = "\n"))
        assertNull(report.firstOrNull { it.startsWith("FOUND_MOVE=") })
    }

    private fun isPromotionMove(move: String): Boolean =
        move.length == 5 && move.last().lowercaseChar() in setOf('q', 'r', 'b', 'n')

    private fun movePriority(fen: String, move: String): Int {
        if (isPromotionMove(move)) {
            return 1_000_000
        }
        val piece = pieceAt(fen, move.substring(0, 2))
        val targetRank = move[3].digitToInt()
        return if (piece == 'P') {
            100_000 + targetRank * 1_000 + if (move[0] != move[2]) 100 else 0
        } else {
            targetRank
        }
    }

    private fun positionPriority(fen: String): Int {
        val board = fen.substringBefore(' ')
        var bestWhitePawnRank = 0
        var rank = 8
        var file = 0
        for (ch in board) {
            when {
                ch == '/' -> {
                    rank -= 1
                    file = 0
                }
                ch.isDigit() -> file += ch.digitToInt()
                else -> {
                    if (ch == 'P') {
                        bestWhitePawnRank = maxOf(bestWhitePawnRank, rank)
                    }
                    file += 1
                }
            }
        }
        return bestWhitePawnRank
    }

    private fun pieceAt(fen: String, square: String): Char? {
        val wantedFile = square[0] - 'a'
        val wantedRank = square[1].digitToInt()
        var rank = 8
        var file = 0
        for (ch in fen.substringBefore(' ')) {
            when {
                ch == '/' -> {
                    rank -= 1
                    file = 0
                }
                ch.isDigit() -> file += ch.digitToInt()
                else -> {
                    if (rank == wantedRank && file == wantedFile) {
                        return ch
                    }
                    file += 1
                }
            }
        }
        return null
    }

    companion object {
        private const val MAX_HUMAN_TURNS = 12
        private const val BEAM_WIDTH = 24
        private const val BRANCH_CAP = 10
    }
}
