package com.ekkus93.chessengine.harness

import android.os.Debug
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

    @Test(timeout = 120_000L)
    fun task24PerformanceEvidenceIsBoundedOnAndroid() {
        warmNativeRuntime()

        val legalIterations = 200
        val legalElapsedNanos = ChessEngine.create().use { engine ->
            val started = System.nanoTime()
            repeat(legalIterations) {
                assertEquals(20, engine.legalMoves().size)
            }
            System.nanoTime() - started
        }
        val legalAverageNanos = legalElapsedNanos / legalIterations
        assertTrue("legal-move JNI average exceeded 100 ms", legalAverageNanos < 100_000_000L)

        val (searchElapsedNanos, searchNodes) =
            ChessEngine.create(transpositionTableMebibytes = 16).use { engine ->
                val started = System.nanoTime()
                val result = engine.search(SearchRequest(nodes = 50_000)).await()
                val elapsed = System.nanoTime() - started
                assertEquals(SearchTerminationKind.NODES, result.terminationKind)
                assertTrue(result.bestMove in engine.legalMoves())
                elapsed to (result.nodes + result.quiescenceNodes)
            }
        val nodesPerSecond = if (searchElapsedNanos == 0L) {
            Long.MAX_VALUE
        } else {
            (searchNodes.toDouble() * TimeUnit.SECONDS.toNanos(1).toDouble() /
                searchElapsedNanos.toDouble()).toLong()
        }
        assertTrue("fixed-node search did not make measurable progress", nodesPerSecond > 100L)

        val smallHeapDelta = measuredNativeHeapDelta(1)
        val largeHeapDelta = measuredNativeHeapDelta(16)
        assertTrue(
            "16 MiB table did not produce a larger native heap delta",
            largeHeapDelta > smallHeapDelta,
        )
        assertTrue(
            "16 MiB table native heap delta was implausibly small",
            largeHeapDelta > 8L * MEBIBYTE,
        )
        assertTrue(
            "16 MiB table native heap delta exceeded the broad bound",
            largeHeapDelta < 64L * MEBIBYTE,
        )

        val cancellationElapsedNanos = ChessEngine.create().use { engine ->
            val operation = engine.search(SearchRequest(infinite = true))
            waitForNativeSearchThread()
            val started = System.nanoTime()
            assertTrue(operation.cancel())
            val result = operation.await()
            val elapsed = System.nanoTime() - started
            assertEquals(SearchTerminationKind.EXPLICIT_STOP, result.terminationKind)
            elapsed
        }
        assertTrue(
            "cancellation exceeded five seconds",
            cancellationElapsedNanos < TimeUnit.SECONDS.toNanos(5),
        )

        println("TASK24_ANDROID_METRIC legal_moves_average_ns=$legalAverageNanos")
        println("TASK24_ANDROID_METRIC fixed_node_total_nodes=$searchNodes")
        println("TASK24_ANDROID_METRIC fixed_node_wall_ns=$searchElapsedNanos")
        println("TASK24_ANDROID_METRIC fixed_node_nodes_per_second=$nodesPerSecond")
        println("TASK24_ANDROID_METRIC native_heap_delta_1mib=$smallHeapDelta")
        println("TASK24_ANDROID_METRIC native_heap_delta_16mib=$largeHeapDelta")
        println("TASK24_ANDROID_METRIC cancellation_ns=$cancellationElapsedNanos")
    }

    private fun warmNativeRuntime() {
        ChessEngine.create().use { engine ->
            assertEquals(20, engine.legalMoves().size)
        }
        Runtime.getRuntime().gc()
        Thread.sleep(50)
    }

    private fun measuredNativeHeapDelta(tableMebibytes: Long): Long {
        Runtime.getRuntime().gc()
        Thread.sleep(50)
        val before = Debug.getNativeHeapAllocatedSize()
        return ChessEngine.create(transpositionTableMebibytes = tableMebibytes).use { engine ->
            assertEquals(20, engine.legalMoves().size)
            (Debug.getNativeHeapAllocatedSize() - before).coerceAtLeast(0L)
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

    private companion object {
        const val MEBIBYTE = 1024L * 1024L
    }
}
