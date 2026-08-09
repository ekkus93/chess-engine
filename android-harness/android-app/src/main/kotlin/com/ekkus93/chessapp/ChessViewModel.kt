package com.ekkus93.chessapp

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ekkus93.chessengine.ChessGame
import com.ekkus93.chessengine.ChessGameSnapshot
import com.ekkus93.chessengine.HumanSide
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private const val SEARCH_POLL_MILLISECONDS = 50L
private const val LOG_TAG = "RustChess"

data class ChessUiState(
    val humanSide: HumanSide = HumanSide.WHITE,
    val engineDepth: Int = 3,
    val snapshot: ChessGameSnapshot? = null,
    val selectedSquare: String? = null,
    val promotionMoves: List<String> = emptyList(),
    val busy: Boolean = false,
    val errorMessage: String? = null,
) {
    val isSetup: Boolean
        get() = snapshot == null
}

class ChessViewModel : ViewModel() {
    private val mutableState = MutableStateFlow(ChessUiState())
    val state: StateFlow<ChessUiState> = mutableState.asStateFlow()

    private var game: ChessGame? = null
    private var monitorJob: Job? = null
    private var operationGeneration = 0L

    fun setHumanSide(side: HumanSide) {
        if (mutableState.value.isSetup && !mutableState.value.busy) {
            mutableState.update { it.copy(humanSide = side) }
        }
    }

    fun setEngineDepth(depth: Int) {
        if (mutableState.value.isSetup && !mutableState.value.busy && depth in 1..12) {
            mutableState.update { it.copy(engineDepth = depth) }
        }
    }

    fun startGame() {
        val configuration = mutableState.value
        if (!configuration.isSetup || configuration.busy) {
            return
        }
        if (game != null) {
            mutableState.update {
                it.copy(errorMessage = "A native game is still active; close it before starting another.")
            }
            return
        }
        val generation = nextOperation()
        mutableState.update { it.copy(busy = true, errorMessage = null) }
        viewModelScope.launch {
            val created = try {
                withContext(Dispatchers.Default) {
                    ChessGame.create(configuration.humanSide, configuration.engineDepth)
                }
            } catch (error: RuntimeException) {
                publishError(generation, error)
                return@launch
            }
            if (!isCurrent(generation)) {
                withContext(Dispatchers.Default) { created.close() }
                return@launch
            }
            val snapshot = try {
                withContext(Dispatchers.Default) { created.snapshot() }
            } catch (error: RuntimeException) {
                withContext(Dispatchers.Default) {
                    try {
                        created.close()
                    } catch (closeError: RuntimeException) {
                        Log.e(LOG_TAG, "failed to close game after snapshot failure", closeError)
                    }
                }
                publishError(generation, error)
                return@launch
            }
            game = created
            publishSnapshot(generation, snapshot)
            monitorSearch(created, generation, snapshot)
        }
    }

    fun returnToSetup() {
        val current = game ?: run {
            mutableState.update {
                it.copy(
                    snapshot = null,
                    selectedSquare = null,
                    promotionMoves = emptyList(),
                    busy = false,
                    errorMessage = null,
                )
            }
            return
        }
        val generation = nextOperation()
        mutableState.update {
            it.copy(
                busy = true,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = null,
            )
        }
        viewModelScope.launch {
            try {
                withContext(Dispatchers.Default) { current.close() }
            } catch (error: RuntimeException) {
                publishError(generation, error)
                return@launch
            }
            if (!isCurrent(generation)) {
                return@launch
            }
            check(game === current) { "native game ownership changed during close" }
            game = null
            mutableState.update {
                it.copy(
                    snapshot = null,
                    selectedSquare = null,
                    promotionMoves = emptyList(),
                    busy = false,
                    errorMessage = null,
                )
            }
        }
    }

    fun restartGame() {
        val current = game ?: return
        val generation = nextOperation()
        mutableState.update {
            it.copy(
                busy = true,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = null,
            )
        }
        viewModelScope.launch {
            val snapshot = try {
                withContext(Dispatchers.Default) { current.restart() }
            } catch (error: RuntimeException) {
                publishError(generation, error)
                return@launch
            }
            publishSnapshot(generation, snapshot)
            monitorSearch(current, generation, snapshot)
        }
    }

    fun resign() {
        val current = game ?: return
        val snapshot = mutableState.value.snapshot ?: return
        if (snapshot.gameOver) {
            return
        }
        val generation = nextOperation()
        mutableState.update {
            it.copy(
                busy = true,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = null,
            )
        }
        viewModelScope.launch {
            val resigned = try {
                withContext(Dispatchers.Default) { current.resign() }
            } catch (error: RuntimeException) {
                publishError(generation, error)
                return@launch
            }
            publishSnapshot(generation, resigned)
        }
    }

    fun onSquareTapped(square: String) {
        val current = mutableState.value
        val snapshot = current.snapshot ?: return
        if (current.busy || !snapshot.humanToMove) {
            return
        }
        val sources = selectableSources(snapshot.legalMoves)
        val selected = current.selectedSquare
        if (selected == null) {
            if (square in sources) {
                mutableState.update { it.copy(selectedSquare = square, errorMessage = null) }
            }
            return
        }
        if (selected == square) {
            mutableState.update { it.copy(selectedSquare = null, promotionMoves = emptyList()) }
            return
        }
        val candidates = candidateMoves(snapshot.legalMoves, selected, square)
        when {
            candidates.isEmpty() -> mutableState.update {
                it.copy(
                    selectedSquare = square.takeIf { value -> value in sources },
                    promotionMoves = emptyList(),
                )
            }
            candidates.size == 1 -> submitMove(candidates.single())
            else -> mutableState.update { it.copy(promotionMoves = candidates) }
        }
    }

    fun choosePromotion(move: String) {
        if (move in mutableState.value.promotionMoves) {
            submitMove(move)
        }
    }

    fun cancelPromotion() {
        mutableState.update { it.copy(promotionMoves = emptyList()) }
    }

    fun clearError() {
        mutableState.update { it.copy(errorMessage = null) }
    }

    private fun submitMove(move: String) {
        val current = game ?: return
        val generation = nextOperation()
        mutableState.update {
            it.copy(
                busy = true,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = null,
            )
        }
        viewModelScope.launch {
            val snapshot = try {
                withContext(Dispatchers.Default) { current.submitMove(move) }
            } catch (error: RuntimeException) {
                publishError(generation, error)
                return@launch
            }
            publishSnapshot(generation, snapshot)
            monitorSearch(current, generation, snapshot)
        }
    }

    private fun monitorSearch(
        session: ChessGame,
        generation: Long,
        initial: ChessGameSnapshot,
    ) {
        monitorJob?.cancel()
        if (!initial.thinking || game !== session || !isCurrent(generation)) {
            return
        }
        monitorJob = viewModelScope.launch {
            var snapshot = initial
            while (snapshot.thinking && game === session && isCurrent(generation)) {
                delay(SEARCH_POLL_MILLISECONDS)
                snapshot = try {
                    withContext(Dispatchers.Default) { session.poll() }
                } catch (error: RuntimeException) {
                    publishError(generation, error)
                    return@launch
                }
                publishSnapshot(generation, snapshot)
            }
        }
    }

    private fun publishSnapshot(generation: Long, snapshot: ChessGameSnapshot) {
        if (!isCurrent(generation)) {
            return
        }
        mutableState.update {
            it.copy(
                snapshot = snapshot,
                busy = false,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = null,
            )
        }
    }

    private fun publishError(generation: Long, error: RuntimeException) {
        if (!isCurrent(generation)) {
            return
        }
        mutableState.update {
            it.copy(
                busy = false,
                selectedSquare = null,
                promotionMoves = emptyList(),
                errorMessage = displayMessage(error),
            )
        }
    }

    private fun nextOperation(): Long {
        operationGeneration += 1
        monitorJob?.cancel()
        monitorJob = null
        return operationGeneration
    }

    private fun isCurrent(generation: Long): Boolean = generation == operationGeneration

    override fun onCleared() {
        monitorJob?.cancel()
        val current = game
        if (current != null) {
            try {
                current.close()
                game = null
            } catch (error: RuntimeException) {
                Log.e(LOG_TAG, "failed to close native chess game during ViewModel cleanup", error)
            }
        }
        super.onCleared()
    }
}

private fun displayMessage(error: RuntimeException): String =
    error.message?.takeIf { it.isNotBlank() } ?: error::class.java.simpleName
