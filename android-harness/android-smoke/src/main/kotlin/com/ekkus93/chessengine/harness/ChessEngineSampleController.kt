package com.ekkus93.chessengine.harness

import androidx.annotation.MainThread
import com.ekkus93.chessengine.ChessEngine
import com.ekkus93.chessengine.SearchOperation
import com.ekkus93.chessengine.SearchRequest
import java.io.Closeable

/** Minimal UI-facing integration that delegates all search work to [ChessEngine]. */
class ChessEngineSampleController private constructor(
    private val engine: ChessEngine,
) : Closeable {
    @MainThread
    fun startDepthSearch(depth: Int): SearchOperation =
        engine.search(SearchRequest(depth = depth))

    @MainThread
    fun startInfiniteSearch(): SearchOperation =
        engine.search(SearchRequest(infinite = true))

    fun legalMoves(): List<String> = engine.legalMoves()

    override fun close() = engine.close()

    companion object {
        fun create(): ChessEngineSampleController =
            ChessEngineSampleController(ChessEngine.create())
    }
}
