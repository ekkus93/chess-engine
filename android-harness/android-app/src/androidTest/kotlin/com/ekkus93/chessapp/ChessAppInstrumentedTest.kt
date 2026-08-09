package com.ekkus93.chessapp

import android.os.SystemClock
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.ekkus93.chessengine.ChessGame
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ChessAppInstrumentedTest {
    @Test
    fun launcherActivityStarts() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                assertFalse(activity.isFinishing)
                assertFalse(activity.isDestroyed)
            }
        }
    }

    @Test
    fun humanWhiteUsesSharedRustControllerForEngineReply() {
        ChessGame.create(HumanSide.WHITE, engineDepth = 1).use { game ->
            val initial = game.snapshot()
            assertTrue(initial.humanToMove)
            assertEquals(HumanSide.WHITE, initial.sideToMove)
            assertTrue("e2e4" in initial.legalMoves)

            val afterHuman = game.submitMove("e2e4")
            assertTrue(afterHuman.thinking)
            val afterEngine = awaitIdle(game, afterHuman)
            assertEquals(2, afterEngine.moves.size)
            assertTrue(afterEngine.humanToMove || afterEngine.gameOver)
        }
    }

    @Test
    fun humanBlackReceivesEngineFirstMove() {
        ChessGame.create(HumanSide.BLACK, engineDepth = 1).use { game ->
            val initial = game.snapshot()
            assertTrue(initial.thinking)
            assertEquals(HumanSide.WHITE, initial.sideToMove)

            val afterEngine = awaitIdle(game, initial)
            assertEquals(1, afterEngine.moves.size)
            assertEquals(HumanSide.BLACK, afterEngine.sideToMove)
            assertTrue(afterEngine.humanToMove)
        }
    }

    private fun awaitIdle(
        game: ChessGame,
        initial: ChessGameSnapshot,
    ): ChessGameSnapshot {
        var snapshot = initial
        repeat(300) {
            if (!snapshot.thinking) {
                return snapshot
            }
            SystemClock.sleep(10)
            snapshot = game.poll()
        }
        error("shared Rust search did not complete before the bounded test deadline")
    }
}
