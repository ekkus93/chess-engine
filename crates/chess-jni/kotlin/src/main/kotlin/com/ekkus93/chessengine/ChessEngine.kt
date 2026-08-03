package com.ekkus93.chessengine

import java.io.Closeable
import java.lang.ref.PhantomReference
import java.lang.ref.ReferenceQueue
import java.util.Collections
import java.util.concurrent.Callable
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutionException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.ThreadFactory
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.locks.ReentrantReadWriteLock
import kotlin.concurrent.read
import kotlin.concurrent.write

/** Stable native result codes from the Rust C ABI. */
enum class ChessEngineErrorCode(val nativeCode: Int) {
    NULL_POINTER(1),
    INVALID_HANDLE(2),
    INVALID_UTF8(3),
    INVALID_ARGUMENT(4),
    ABI_MISMATCH(5),
    INVALID_FEN(10),
    INVALID_MOVE_SYNTAX(11),
    ILLEGAL_MOVE(12),
    GAME_OVER(13),
    GAME_ERROR(14),
    INVALID_WEIGHT_SET(15),
    SEARCH_ERROR(20),
    ALLOCATION_FAILURE(30),
    INVALID_BUFFER(31),
    INTERNAL_ERROR(100),
    PANIC(101),
    UNKNOWN(Int.MIN_VALUE);

    companion object {
        fun fromNative(value: Int): ChessEngineErrorCode =
            entries.firstOrNull { it.nativeCode == value } ?: UNKNOWN
    }
}

/** Typed exception thrown by every failed JNI operation. */
class ChessEngineException(
    val nativeCode: Int,
    message: String,
) : RuntimeException(message) {
    val code: ChessEngineErrorCode = ChessEngineErrorCode.fromNative(nativeCode)
}

enum class ChessColor(val nativeCode: Int) {
    NONE(0),
    WHITE(1),
    BLACK(2);

    companion object {
        fun fromNative(value: Int): ChessColor =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native color code: $value")
    }
}

enum class GameStatusKind(val nativeCode: Int) {
    ONGOING(0),
    CHECKMATE(1),
    STALEMATE(2),
    AUTOMATIC_DRAW(3),
    CLAIMABLE_DRAW(4);

    companion object {
        fun fromNative(value: Int): GameStatusKind =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native status code: $value")
    }
}

enum class DrawReason(val nativeCode: Int) {
    NONE(0),
    THREEFOLD_REPETITION(1),
    FIVEFOLD_REPETITION(2),
    FIFTY_MOVE_RULE(3),
    SEVENTY_FIVE_MOVE_RULE(4),
    DEAD_POSITION(5);

    companion object {
        fun fromNative(value: Int): DrawReason =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native draw code: $value")
    }
}

data class GameStatus(
    val kind: GameStatusKind,
    val winner: ChessColor,
    val drawReason: DrawReason,
) {
    companion object {
        internal fun parse(encoded: String): GameStatus {
            val fields = encoded.split(',')
            require(fields.size == 3) { "native game status must contain three fields" }
            return GameStatus(
                kind = GameStatusKind.fromNative(fields[0].toInt()),
                winner = ChessColor.fromNative(fields[1].toInt()),
                drawReason = DrawReason.fromNative(fields[2].toInt()),
            )
        }
    }
}

data class EvaluationWeightIdentity(
    val schemaVersion: UShort,
    val identifier: ULong,
    val checksum: ULong,
) {
    companion object {
        internal fun parse(encoded: String): EvaluationWeightIdentity {
            val fields = encoded.split(',')
            require(fields.size == 3) { "native weight identity must contain three fields" }
            return EvaluationWeightIdentity(
                schemaVersion = fields[0].toUShort(),
                identifier = fields[1].toULong(),
                checksum = fields[2].toULong(),
            )
        }
    }
}

enum class SearchScoreKind(val nativeCode: Int) {
    NONE(0),
    CENTIPAWNS(1),
    MATE(2);

    companion object {
        fun fromNative(value: Int): SearchScoreKind =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native score code: $value")
    }
}

enum class SearchTerminationKind(val nativeCode: Int) {
    NONE(0),
    DEPTH(1),
    NODES(2),
    SOFT_TIME(3),
    HARD_TIME(4),
    EXPLICIT_STOP(5),
    MAXIMUM_SUPPORTED_DEPTH(6);

    companion object {
        fun fromNative(value: Int): SearchTerminationKind =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native termination code: $value")
    }
}

enum class SearchFallbackKind(val nativeCode: Int) {
    NONE(0),
    FIRST_LEGAL_MOVE(1),
    NO_LEGAL_MOVE(2);

    companion object {
        fun fromNative(value: Int): SearchFallbackKind =
            entries.firstOrNull { it.nativeCode == value }
                ?: throw IllegalArgumentException("unknown native fallback code: $value")
    }
}

/** One explicit, immutable native search request. Zero means that limit is absent. */
data class SearchRequest(
    val depth: Int = 0,
    val nodes: Long = 0,
    val softTimeMilliseconds: Long = 0,
    val hardTimeMilliseconds: Long = 0,
    val infinite: Boolean = false,
    val checkExtension: Boolean = false,
) {
    init {
        require(depth >= 0) { "depth cannot be negative" }
        require(nodes >= 0) { "nodes cannot be negative" }
        require(softTimeMilliseconds >= 0) { "soft time cannot be negative" }
        require(hardTimeMilliseconds >= 0) { "hard time cannot be negative" }
        require(
            infinite || depth > 0 || nodes > 0 ||
                softTimeMilliseconds > 0 || hardTimeMilliseconds > 0,
        ) { "a finite search requires at least one automatic limit" }
    }
}

data class SearchResult(
    val bestMove: String?,
    val ponderMove: String?,
    val principalVariation: List<String>,
    val scoreKind: SearchScoreKind,
    val scoreValue: Int,
    val completedDepth: Int,
    val selectiveDepth: Int,
    val terminationKind: SearchTerminationKind,
    val fallbackKind: SearchFallbackKind,
    val terminationValue: ULong,
    val nodes: ULong,
    val quiescenceNodes: ULong,
    val elapsedMilliseconds: ULong,
) {
    companion object {
        private const val FIELD_COUNT = 13

        internal fun parse(encoded: String): SearchResult {
            val fields = encoded.split('\n', limit = FIELD_COUNT)
            require(fields.size == FIELD_COUNT) {
                "native search result must contain exactly $FIELD_COUNT fields"
            }
            return SearchResult(
                bestMove = fields[0].ifEmpty { null },
                ponderMove = fields[1].ifEmpty { null },
                principalVariation = fields[2]
                    .takeIf { it.isNotEmpty() }
                    ?.split(' ')
                    ?: emptyList(),
                scoreKind = SearchScoreKind.fromNative(fields[3].toInt()),
                scoreValue = fields[4].toInt(),
                completedDepth = fields[5].toInt(),
                selectiveDepth = fields[6].toInt(),
                terminationKind = SearchTerminationKind.fromNative(fields[7].toInt()),
                fallbackKind = SearchFallbackKind.fromNative(fields[8].toInt()),
                terminationValue = fields[9].toULong(),
                nodes = fields[10].toULong(),
                quiescenceNodes = fields[11].toULong(),
                elapsedMilliseconds = fields[12].toULong(),
            )
        }
    }
}

/**
 * One asynchronous native search. [cancel] requests an orderly Rust search stop;
 * it does not rely on Java thread interruption.
 */
class SearchOperation internal constructor(
    private val future: Future<SearchResult>,
    private val cancellation: AtomicLong,
) {
    fun cancel(): Boolean {
        val handle = cancellation.get()
        if (handle == 0L || future.isDone) {
            return false
        }
        return try {
            NativeChessEngineBindings.nativeCancellationCancel(handle)
            true
        } catch (error: ChessEngineException) {
            if (error.code == ChessEngineErrorCode.INVALID_HANDLE && future.isDone) {
                false
            } else {
                throw error
            }
        }
    }

    fun isDone(): Boolean = future.isDone

    fun await(): SearchResult = try {
        future.get()
    } catch (error: ExecutionException) {
        val cause = error.cause
        when (cause) {
            is RuntimeException -> throw cause
            is Error -> throw cause
            else -> throw IllegalStateException("native search failed", cause)
        }
    }
}

private class NativeHandleState(initialHandle: Long) {
    private val handle = AtomicLong(initialHandle)

    fun requireOpen(): Long = handle.get().takeIf { it != 0L }
        ?: throw IllegalStateException("chess engine is closed")

    fun take(): Long = handle.getAndSet(0L)
}

private object NativeEngineReaper {
    private val queue = ReferenceQueue<ChessEngine>()
    private val references = ConcurrentHashMap.newKeySet<EngineReference>()

    init {
        Thread(
            {
                while (true) {
                    val reference = queue.remove() as EngineReference
                    references.remove(reference)
                    reference.destroyLeakedHandle()
                    reference.clear()
                }
            },
            "chess-engine-native-reaper",
        ).apply {
            isDaemon = true
            start()
        }
    }

    fun register(owner: ChessEngine, state: NativeHandleState): EngineReference {
        val reference = EngineReference(owner, state, queue)
        references.add(reference)
        return reference
    }

    fun unregister(reference: EngineReference) {
        references.remove(reference)
        reference.clear()
    }

    class EngineReference(
        owner: ChessEngine,
        private val state: NativeHandleState,
        queue: ReferenceQueue<ChessEngine>,
    ) : PhantomReference<ChessEngine>(owner, queue) {
        fun destroyLeakedHandle() {
            val handle = state.take()
            if (handle != 0L) {
                try {
                    NativeChessEngineBindings.nativeDestroy(handle)
                } catch (_: RuntimeException) {
                    // The fallback cannot report to an unreachable owner. Explicit close is authoritative.
                }
            }
        }
    }
}

private class SearchThreadFactory : ThreadFactory {
    override fun newThread(task: Runnable): Thread =
        Thread(task, "chess-engine-search").apply { isDaemon = true }
}

/**
 * Deterministic Kotlin owner for one native Rust engine.
 *
 * Search is never executed by a public method on the caller's thread. [search]
 * schedules the synchronous native call on a private single-worker executor and
 * returns a request-local [SearchOperation] whose cancellation token may be used
 * from any thread.
 *
 * [close] is idempotent and authoritative. It cancels an active request, waits
 * for the worker to leave the native call, destroys the opaque engine token, and
 * shuts down the worker. A phantom-reference reaper is only a leak fallback; it
 * is not a substitute for explicit close and intentionally does not hide errors.
 */
class ChessEngine private constructor(
    private val state: NativeHandleState,
) : Closeable {
    private val lifecycleLock = ReentrantReadWriteLock()
    private val closed = AtomicBoolean(false)
    private val searchOutstanding = AtomicBoolean(false)
    private val activeCancellation = AtomicLong(0L)
    private val executor: ExecutorService =
        Executors.newSingleThreadExecutor(SearchThreadFactory())
    private val reaperReference = NativeEngineReaper.register(this, state)

    val version: String
        get() = NativeChessEngineBindings.nativeVersion()

    fun resetPosition() = withHandle(NativeChessEngineBindings::nativeResetPosition)

    fun setPosition(fen: String) =
        withHandle { handle -> NativeChessEngineBindings.nativeSetPosition(handle, fen) }

    fun fen(): String = withHandle(NativeChessEngineBindings::nativeFen)

    fun legalMoves(): List<String> =
        withHandle(NativeChessEngineBindings::nativeLegalMoves)
            .takeIf { it.isNotEmpty() }
            ?.split('\n')
            ?: emptyList()

    fun playMove(move: String) =
        withHandle { handle -> NativeChessEngineBindings.nativePlayMove(handle, move) }

    fun gameStatus(): GameStatus =
        GameStatus.parse(withHandle(NativeChessEngineBindings::nativeGameStatus))

    fun weightIdentity(): EvaluationWeightIdentity =
        EvaluationWeightIdentity.parse(
            withHandle(NativeChessEngineBindings::nativeWeightIdentity),
        )

    fun search(request: SearchRequest): SearchOperation {
        check(searchOutstanding.compareAndSet(false, true)) {
            "only one search may be outstanding per engine"
        }

        val cancellationHandle = try {
            lifecycleLock.read {
                state.requireOpen()
                NativeChessEngineBindings.nativeCancellationCreate()
            }
        } catch (error: Throwable) {
            searchOutstanding.set(false)
            throw error
        }
        activeCancellation.set(cancellationHandle)
        val operationCancellation = AtomicLong(cancellationHandle)

        val future = try {
            executor.submit(Callable {
                try {
                    lifecycleLock.read {
                        val handle = state.requireOpen()
                        SearchResult.parse(
                            NativeChessEngineBindings.nativeSearch(
                                handle = handle,
                                depth = request.depth,
                                nodes = request.nodes,
                                softTimeMilliseconds = request.softTimeMilliseconds,
                                hardTimeMilliseconds = request.hardTimeMilliseconds,
                                infinite = request.infinite,
                                checkExtension = request.checkExtension,
                                cancellationHandle = cancellationHandle,
                            ),
                        )
                    }
                } finally {
                    activeCancellation.compareAndSet(cancellationHandle, 0L)
                    operationCancellation.compareAndSet(cancellationHandle, 0L)
                    try {
                        NativeChessEngineBindings.nativeCancellationDestroy(cancellationHandle)
                    } finally {
                        searchOutstanding.set(false)
                    }
                }
            })
        } catch (error: Throwable) {
            activeCancellation.compareAndSet(cancellationHandle, 0L)
            operationCancellation.set(0L)
            searchOutstanding.set(false)
            NativeChessEngineBindings.nativeCancellationDestroy(cancellationHandle)
            throw error
        }

        return SearchOperation(future, operationCancellation)
    }

    override fun close() {
        if (!closed.compareAndSet(false, true)) {
            return
        }

        val cancellationHandle = activeCancellation.get()
        if (cancellationHandle != 0L) {
            try {
                NativeChessEngineBindings.nativeCancellationCancel(cancellationHandle)
            } catch (error: ChessEngineException) {
                if (error.code != ChessEngineErrorCode.INVALID_HANDLE) {
                    throw error
                }
            }
        }

        executor.shutdown()
        try {
            lifecycleLock.write {
                val handle = state.take()
                if (handle != 0L) {
                    NativeChessEngineBindings.nativeDestroy(handle)
                }
            }
        } finally {
            NativeEngineReaper.unregister(reaperReference)
        }

        check(executor.awaitTermination(CLOSE_TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
            "native search worker did not terminate after cancellation"
        }
    }

    private inline fun <T> withHandle(operation: (Long) -> T): T =
        lifecycleLock.read { operation(state.requireOpen()) }

    companion object {
        private const val DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES = 16L
        private const val CLOSE_TIMEOUT_SECONDS = 10L

        fun create(
            transpositionTableMebibytes: Long = DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
        ): ChessEngine {
            require(transpositionTableMebibytes > 0) {
                "transposition-table budget must be greater than zero"
            }
            return ChessEngine(
                NativeHandleState(
                    NativeChessEngineBindings.nativeCreate(transpositionTableMebibytes),
                ),
            )
        }
    }
}

/** Private raw JNI surface. Android application code should use [ChessEngine]. */
internal object NativeChessEngineBindings {
    init {
        System.loadLibrary("chess_jni")
    }

    external fun nativeVersion(): String
    external fun nativeCreate(transpositionTableMebibytes: Long): Long
    external fun nativeDestroy(handle: Long)
    external fun nativeResetPosition(handle: Long)
    external fun nativeSetPosition(handle: Long, fen: String)
    external fun nativeFen(handle: Long): String
    external fun nativeLegalMoves(handle: Long): String
    external fun nativePlayMove(handle: Long, move: String)
    external fun nativeGameStatus(handle: Long): String
    external fun nativeWeightIdentity(handle: Long): String
    external fun nativeCancellationCreate(): Long
    external fun nativeCancellationDestroy(handle: Long)
    external fun nativeCancellationCancel(handle: Long)
    external fun nativeCancellationReset(handle: Long)
    external fun nativeCancellationIsCancelled(handle: Long): Boolean

    external fun nativeSearch(
        handle: Long,
        depth: Int,
        nodes: Long,
        softTimeMilliseconds: Long,
        hardTimeMilliseconds: Long,
        infinite: Boolean,
        checkExtension: Boolean,
        cancellationHandle: Long,
    ): String
}
