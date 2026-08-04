package com.ekkus93.chessengine.harness

import android.content.Context
import com.ekkus93.chessengine.ChessEngine

/** Explicit Android adapter that supplies one packaged indexed book asset. */
object ChessEngineAssetFactory {
    fun create(
        context: Context,
        assetName: String = "opening-book-v1.bin",
        transpositionTableMebibytes: Long = 1L,
        openingBookEnabled: Boolean = true,
    ): ChessEngine {
        val bytes = context.assets.open(assetName).use { it.readBytes() }
        return ChessEngine.createWithIndexedBook(
            indexedBook = bytes,
            transpositionTableMebibytes = transpositionTableMebibytes,
            openingBookEnabled = openingBookEnabled,
        )
    }
}
