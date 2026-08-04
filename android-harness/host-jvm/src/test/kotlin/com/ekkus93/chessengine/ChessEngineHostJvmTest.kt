package com.ekkus93.chessengine

import java.util.concurrent.TimeUnit
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout

class ChessEngineHostJvmTest {
    @Test
    @Timeout(30)
    fun publicLifecycleUsesTheRealNativeLibrary() {
        val engine = ChessEngine.create()
        val startingFen = engine.fen()
        val legalMoves = engine.legalMoves()

        assertEquals("0.1.0", engine.version)
        assertEquals(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            startingFen,
        )
        assertEquals(20, legalMoves.size)
        assertTrue("e2e4" in legalMoves)
        assertEquals(GameStatusKind.ONGOING, engine.gameStatus().kind)
        assertTrue(engine.weightIdentity().schemaVersion.toInt() > 0)

        val result = engine.search(SearchRequest(depth = 2)).await()
        assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
        assertEquals(2, result.completedDepth)
        assertTrue((result.bestMove ?: error("missing best move")) in legalMoves)
        assertTrue(result.nodes > 0uL)

        engine.playMove("e2e4")
        assertTrue(engine.fen().contains(" b "))
        engine.resetPosition()
        assertEquals(startingFen, engine.fen())

        engine.close()
        engine.close()
        assertThrows(IllegalStateException::class.java) { engine.fen() }
    }

    @Test
    @Timeout(30)
    fun invalidFenMapsToTypedExceptionAndPreservesState() {
        ChessEngine.create().use { engine ->
            val before = engine.fen()
            val error = assertThrows(ChessEngineException::class.java) {
                engine.setPosition("not a fen")
            }
            assertEquals(ChessEngineErrorCode.INVALID_FEN, error.code)
            assertEquals(before, engine.fen())
        }
    }

    @Test
    @Timeout(30)
    fun infiniteSearchRunsInsideTheWorkerAndStopsThroughNativeCancellation() {
        ChessEngine.create().use { engine ->
            val legalMoves = engine.legalMoves()
            val operation = engine.search(SearchRequest(infinite = true))
            val worker = waitForNativeSearchThread()
            assertEquals("chess-engine-search", worker.name)
            assertNotEquals(Thread.currentThread(), worker)
            assertTrue(operation.cancel())

            val result = operation.await()
            assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
            assertTrue((result.bestMove ?: error("missing fallback move")) in legalMoves)
            assertFalse(operation.cancel())
        }
    }

    @Test
    @Timeout(60)
    fun repeatedCreateSearchStopDestroyIsStable() {
        repeat(24) { iteration ->
            ChessEngine.create().use { engine ->
                val operation = if (iteration % 2 == 0) {
                    engine.search(SearchRequest(depth = 1))
                } else {
                    engine.search(SearchRequest(infinite = true)).also {
                        waitForNativeSearchThread()
                        assertTrue(it.cancel())
                    }
                }
                val result = operation.await()
                if (iteration % 2 == 0) {
                    assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
                } else {
                    assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
                }
                assertTrue(
                    (result.bestMove ?: error("missing lifecycle move")) in engine.legalMoves(),
                )
            }
        }
    }

    private fun waitForNativeSearchThread(): Thread {
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
        while (System.nanoTime() < deadline) {
            val match = Thread.getAllStackTraces().entries.firstOrNull { (thread, stack) ->
                thread.name == "chess-engine-search" && stack.any {
                    it.className ==
                        "com.ekkus93.chessengine.NativeChessEngineBindings" &&
                        it.methodName == "nativeSearch"
                }
            }
            if (match != null) {
                return match.key
            }
            Thread.sleep(10)
        }
        error("native search did not become observable on chess-engine-search")
    }
}
