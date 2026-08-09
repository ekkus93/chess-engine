package com.ekkus93.chessengine

import java.io.Closeable
import java.util.concurrent.atomic.AtomicLong

/** Human side for the high-level interactive Android game API. */
enum class HumanSide(val nativeCode: Int) {
    WHITE(1),
    BLACK(2),
}

/** Immutable application/session snapshot produced by the shared Rust `chess-app` layer. */
data class ChessGameSnapshot(
    val fen: String,
    val legalMoves: List<String>,
    val moves: List<String>,
    val humanSide: HumanSide,
    val sideToMove: HumanSide,
    val thinking: Boolean,
    val outcome: String?,
    val statusMessage: String?,
    val engineDepth: Int?,
    val engineScore: String?,
    val engineNodes: Long?,
    val engineNps: Long?,
    val engineElapsed: String?,
    val principalVariation: List<String>,
    val hashFullPerMille: Int?,
) {
    val gameOver: Boolean
        get() = outcome != null

    val humanToMove: Boolean
        get() = !thinking && !gameOver && sideToMove == humanSide

    companion object {
        private const val FIELD_COUNT = 17
        private const val VERSION = "1"
        private const val END = "END"
        private const val SEPARATOR = '\u001f'

        internal fun parse(encoded: String): ChessGameSnapshot {
            val fields = encoded.split(SEPARATOR)
            require(fields.size == FIELD_COUNT) {
                "native Android game snapshot must contain $FIELD_COUNT fields"
            }
            require(fields[0] == VERSION) {
                "unsupported native Android game snapshot version: ${fields[0]}"
            }
            require(fields[16] == END) { "native Android game snapshot terminator is missing" }
            return ChessGameSnapshot(
                fen = fields[1],
                legalMoves = fields[2].words(),
                moves = fields[3].words(),
                humanSide = parseSide(fields[4]),
                sideToMove = parseSide(fields[5]),
                thinking = parseBoolean(fields[6]),
                outcome = fields[7].ifEmpty { null },
                statusMessage = fields[8].ifEmpty { null },
                engineDepth = fields[9].toIntOrNull(),
                engineScore = fields[10].ifEmpty { null },
                engineNodes = fields[11].toLongOrNull(),
                engineNps = fields[12].toLongOrNull(),
                engineElapsed = fields[13].ifEmpty { null },
                principalVariation = fields[14].words(),
                hashFullPerMille = fields[15].toIntOrNull(),
            )
        }

        private fun parseSide(value: String): HumanSide = when (value) {
            "white" -> HumanSide.WHITE
            "black" -> HumanSide.BLACK
            else -> error("unknown native side: $value")
        }

        private fun parseBoolean(value: String): Boolean = when (value) {
            "0" -> false
            "1" -> true
            else -> error("unknown native boolean: $value")
        }

        private fun String.words(): List<String> =
            takeIf { it.isNotEmpty() }?.split(' ') ?: emptyList()
    }
}

/**
 * High-level Android owner for one Human-vs-Engine game.
 *
 * Game legality, turn ownership, search scheduling, stale-result rejection,
 * exact-search-result policy, and terminal outcomes live in Rust `chess-app`.
 * Kotlin owns presentation and periodically calls [poll] while [ChessGameSnapshot.thinking]
 * is true so completed Rust worker events are folded into the shared controller.
 */
class ChessGame private constructor(
    private val handle: AtomicLong,
) : Closeable {
    @Synchronized
    fun snapshot(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeSnapshot(requireOpen()))

    @Synchronized
    fun poll(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativePoll(requireOpen()))

    @Synchronized
    fun submitMove(move: String): ChessGameSnapshot {
        require(move.isNotBlank()) { "move must not be blank" }
        return ChessGameSnapshot.parse(
            NativeChessAppBindings.nativeSubmitMove(requireOpen(), move),
        )
    }

    @Synchronized
    fun restart(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeRestart(requireOpen()))

    @Synchronized
    fun resign(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeResign(requireOpen()))

    @Synchronized
    override fun close() {
        val current = handle.get()
        if (current == 0L) {
            return
        }
        NativeChessAppBindings.nativeDestroy(current)
        check(handle.compareAndSet(current, 0L)) {
            "Android chess game handle changed during close"
        }
    }

    private fun requireOpen(): Long = handle.get().takeIf { it != 0L }
        ?: throw IllegalStateException("Android chess game is closed")

    companion object {
        fun create(
            humanSide: HumanSide = HumanSide.WHITE,
            engineDepth: Int = 3,
        ): ChessGame {
            require(engineDepth in 1..12) { "engine depth must be between 1 and 12" }
            val handle = NativeChessAppBindings.nativeCreate(humanSide.nativeCode, engineDepth)
            check(handle != 0L) { "native Android game returned a null handle" }
            return ChessGame(AtomicLong(handle))
        }
    }
}

private object NativeChessAppBindings {
    init {
        System.loadLibrary("chess_jni")
    }

    external fun nativeCreate(humanColor: Int, depth: Int): Long
    external fun nativeDestroy(handle: Long)
    external fun nativeSnapshot(handle: Long): String
    external fun nativePoll(handle: Long): String
    external fun nativeSubmitMove(handle: Long, move: String): String
    external fun nativeRestart(handle: Long): String
    external fun nativeResign(handle: Long): String
}
