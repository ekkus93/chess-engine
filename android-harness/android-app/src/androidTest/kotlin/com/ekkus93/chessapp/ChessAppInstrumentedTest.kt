package com.ekkus93.chessapp

import android.os.SystemClock
import androidx.lifecycle.ViewModelProvider
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
    fun humanWhiteUsesSharedRustOpeningBookForEngineReply() {
        ChessGame.create(HumanSide.WHITE, engineDepth = 1).use { game ->
            val initial = game.snapshot()
            assertTrue(initial.humanToMove)
            assertEquals(HumanSide.WHITE, initial.sideToMove)
            assertTrue("e2e4" in initial.legalMoves)

            val afterHuman = game.submitMove("e2e4")
            assertTrue(afterHuman.thinking)
            val afterEngine = awaitIdle(game, afterHuman)
            assertEquals(listOf("e2e4", "c7c5"), afterEngine.moves)
            assertTrue(afterEngine.humanToMove || afterEngine.gameOver)
        }
    }

    @Test
    fun humanBlackReceivesSharedRustOpeningBookFirstMove() {
        ChessGame.create(HumanSide.BLACK, engineDepth = 1).use { game ->
            val initial = game.snapshot()
            assertTrue(initial.thinking)
            assertEquals(HumanSide.WHITE, initial.sideToMove)

            val afterEngine = awaitIdle(game, initial)
            assertEquals(listOf("e2e4"), afterEngine.moves)
            assertEquals(HumanSide.BLACK, afterEngine.sideToMove)
            assertTrue(afterEngine.humanToMove)
        }
    }

    @Test
    fun humanMoveRemainsVisibleBeforeAndroidRevealsEngineReply() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var viewModel: ChessViewModel
            scenario.onActivity { activity ->
                viewModel = ViewModelProvider(activity)[ChessViewModel::class.java]
                viewModel.setHumanSide(HumanSide.WHITE)
                viewModel.setEngineDepth(1)
                viewModel.startGame()
            }

            awaitUiState(viewModel) { state ->
                val snapshot = state.snapshot
                snapshot != null && !state.busy && snapshot.humanToMove
            }

            scenario.onActivity {
                viewModel.onSquareTapped("e2")
                viewModel.onSquareTapped("e4")
            }

            val afterHuman = awaitUiState(viewModel) { state ->
                state.snapshot?.moves == listOf("e2e4") && state.snapshot.thinking
            }
            assertEquals(listOf("e2e4"), afterHuman.snapshot?.moves)
            val humanMoveObservedAt = SystemClock.elapsedRealtime()

            SystemClock.sleep(900)
            val duringPause = viewModel.state.value
            assertEquals(listOf("e2e4"), duringPause.snapshot?.moves)
            assertTrue(duringPause.snapshot?.thinking == true)

            val afterEngine = awaitUiState(viewModel) { state ->
                state.snapshot?.moves == listOf("e2e4", "c7c5")
            }
            assertTrue(SystemClock.elapsedRealtime() - humanMoveObservedAt >= 900L)
            assertTrue(afterEngine.snapshot?.humanToMove == true || afterEngine.snapshot?.gameOver == true)
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

    private fun awaitUiState(
        viewModel: ChessViewModel,
        predicate: (ChessUiState) -> Boolean,
    ): ChessUiState {
        repeat(500) {
            val state = viewModel.state.value
            if (predicate(state)) {
                return state
            }
            SystemClock.sleep(10)
        }
        error("Android UI state did not reach the expected condition before the bounded deadline")
    }
}
