package com.ekkus93.chessengine

import java.io.Closeable
import java.lang.ref.PhantomReference
import java.lang.ref.ReferenceQueue
import java.util.concurrent.ConcurrentHashMap
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
    val sanMoves: List<String>,
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
        private const val FIELD_COUNT = 18
        private const val VERSION = "2"
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
            require(fields[17] == END) { "native Android game snapshot terminator is missing" }
            return ChessGameSnapshot(
                fen = fields[1],
                legalMoves = fields[2].words(),
                moves = fields[3].words(),
                sanMoves = fields[4].words(),
                humanSide = parseSide(fields[5]),
                sideToMove = parseSide(fields[6]),
                thinking = parseBoolean(fields[7]),
                outcome = fields[8].ifEmpty { null },
                statusMessage = fields[9].ifEmpty { null },
                engineDepth = fields[10].toIntOrNull(),
                engineScore = fields[11].ifEmpty { null },
                engineNodes = fields[12].toLongOrNull(),
                engineNps = fields[13].toLongOrNull(),
                engineElapsed = fields[14].ifEmpty { null },
                principalVariation = fields[15].words(),
                hashFullPerMille = fields[16].toIntOrNull(),
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

private class NativeGameHandleState(initialHandle: Long) {
    private val handle = AtomicLong(initialHandle)

    fun current(): Long = handle.get()

    fun requireOpen(): Long = current().takeIf { it != 0L }
        ?: throw IllegalStateException("Android chess game is closed")

    fun clear(expected: Long): Boolean = handle.compareAndSet(expected, 0L)

    fun take(): Long = handle.getAndSet(0L)
}

/**
 * Leak fallback for a forgotten [ChessGame.close]. Explicit close remains authoritative.
 * An unreachable owner cannot receive a cleanup exception, so this mirrors the existing
 * low-level ChessEngine reaper rather than pretending GC cleanup is a normal success path.
 */
private object NativeGameReaper {
    private val queue = ReferenceQueue<ChessGame>()
    private val references = ConcurrentHashMap.newKeySet<GameReference>()

    init {
        Thread(
            {
                while (true) {
                    val reference = queue.remove() as GameReference
                    references.remove(reference)
                    reference.destroyLeakedHandle()
                    reference.clear()
                }
            },
            "chess-app-native-reaper",
        ).apply {
            isDaemon = true
            start()
        }
    }

    fun register(owner: ChessGame, state: NativeGameHandleState): GameReference {
        val reference = GameReference(owner, state, queue)
        references.add(reference)
        return reference
    }

    fun unregister(reference: GameReference) {
        references.remove(reference)
        reference.clear()
    }

    class GameReference(
        owner: ChessGame,
        private val state: NativeGameHandleState,
        queue: ReferenceQueue<ChessGame>,
    ) : PhantomReference<ChessGame>(owner, queue) {
        fun destroyLeakedHandle() {
            val handle = state.take()
            if (handle != 0L) {
                try {
                    NativeChessAppBindings.nativeDestroy(handle)
                } catch (_: RuntimeException) {
                    // An unreachable owner cannot receive the failure. Explicit close is authoritative.
                }
            }
        }
    }
}

/**
 * High-level Android owner for one Human-vs-Engine game.
 *
 * Game legality, turn ownership, search scheduling, stale-result rejection,
 * exact-search-result policy, SAN history, and terminal outcomes live in Rust.
 * Kotlin owns presentation and periodically calls [poll] while [ChessGameSnapshot.thinking]
 * is true so completed Rust worker events are folded into the shared controller.
 */
class ChessGame private constructor(
    private val state: NativeGameHandleState,
) : Closeable {
    private val reaperReference = NativeGameReaper.register(this, state)

    @Synchronized
    fun snapshot(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeSnapshot(state.requireOpen()))

    @Synchronized
    fun poll(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativePoll(state.requireOpen()))

    @Synchronized
    fun submitMove(move: String): ChessGameSnapshot {
        require(move.isNotBlank()) { "move must not be blank" }
        return ChessGameSnapshot.parse(
            NativeChessAppBindings.nativeSubmitMove(state.requireOpen(), move),
        )
    }

    @Synchronized
    fun restart(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeRestart(state.requireOpen()))

    @Synchronized
    fun resign(): ChessGameSnapshot =
        ChessGameSnapshot.parse(NativeChessAppBindings.nativeResign(state.requireOpen()))

    @Synchronized
    override fun close() {
        val current = state.current()
        if (current == 0L) {
            return
        }
        NativeChessAppBindings.nativeDestroy(current)
        check(state.clear(current)) { "Android chess game handle changed during close" }
        NativeGameReaper.unregister(reaperReference)
    }

    companion object {
        fun create(
            humanSide: HumanSide = HumanSide.WHITE,
            engineDepth: Int = 3,
        ): ChessGame {
            require(engineDepth in 1..12) { "engine depth must be between 1 and 12" }
            val handle = NativeChessAppBindings.nativeCreate(humanSide.nativeCode, engineDepth)
            check(handle != 0L) { "native Android game returned a null handle" }
            return ChessGame(NativeGameHandleState(handle))
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
