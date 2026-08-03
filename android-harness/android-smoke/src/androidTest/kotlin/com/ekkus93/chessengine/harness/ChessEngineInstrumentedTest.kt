package com.ekkus93.chessengine.harness

import android.os.Looper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.ekkus93.chessengine.ChessEngine
import com.ekkus93.chessengine.GameStatusKind
import com.ekkus93.chessengine.SearchOperation
import com.ekkus93.chessengine.SearchRequest
import com.ekkus93.chessengine.SearchTerminationKind
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessEngineInstrumentedTest {
    @Test(timeout = 60_000L)
    fun realJniLifecycleRunsOnTheEmulator() {
        ChessEngine.create().use { engine ->
            val startingFen = engine.fen()
            val legalMoves = engine.legalMoves()
            assertEquals(20, legalMoves.size)
            assertTrue("e2e4" in legalMoves)
            assertEquals(GameStatusKind.ONGOING, engine.gameStatus().kind)

            val result = engine.search(SearchRequest(depth = 2)).await()
            assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
            assertEquals(2, result.completedDepth)
            assertTrue((result.bestMove ?: error("missing best move")) in legalMoves)

            engine.playMove("e2e4")
            assertTrue(engine.fen().contains(" b "))
            engine.resetPosition()
            assertEquals(startingFen, engine.fen())
        }
    }

    @Test(timeout = 60_000L)
    fun packagedIndexedBookAssetIsExplicitAndMissingEntriesFallThrough() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        ChessEngineAssetFactory.create(context).use { engine ->
            assertEquals("e2e4", engine.openingBookMove())
            engine.playMove("e2e4")
            assertNull(engine.openingBookMove())
            val result = engine.search(SearchRequest(depth = 1)).await()
            assertEquals(SearchTerminationKind.DEPTH, result.terminationKind)
            assertTrue(result.bestMove in engine.legalMoves())
        }

        ChessEngine.create().use { engine ->
            assertNull(engine.openingBookMove())
            assertTrue(engine.search(SearchRequest(depth = 1)).await().bestMove != null)
        }
    }

    @Test(timeout = 60_000L)
    fun sampleMainThreadEntryRunsTheNativeCallOnTheWorker() {
        val controller = ChessEngineSampleController.create()
        try {
            val operation = AtomicReference<SearchOperation>()
            val instrumentation = InstrumentationRegistry.getInstrumentation()
            instrumentation.runOnMainSync {
                assertSame(Looper.getMainLooper(), Looper.myLooper())
                operation.set(controller.startInfiniteSearch())
            }

            val worker = waitForNativeSearchThread()
            assertEquals("chess-engine-search", worker.name)
            assertNotEquals(Looper.getMainLooper().thread, worker)
            assertTrue(operation.get().cancel())

            val result = operation.get().await()
            assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
            assertTrue(
                (result.bestMove ?: error("missing fallback move")) in controller.legalMoves(),
            )
        } finally {
            controller.close()
        }
    }

    @Test(timeout = 120_000L)
    fun repeatedCreateSearchStopDestroyIsStableOnAndroid() {
        repeat(16) { iteration ->
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
