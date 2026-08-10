package com.ekkus93.chessengine

import org.junit.Assert.assertThrows
import org.junit.Test

class ChessGameSnapshotParseTest {
    private val validFields = listOf(
        "2",
        "8/8/8/8/8/8/4K3/7k w - - 0 1",
        "",
        "",
        "",
        "white",
        "white",
        "0",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "END",
    )

    private fun encoded(fields: List<String>): String = fields.joinToString("\u001f")

    @Test
    fun rejectsWrongFieldCount() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.dropLast(1)))
        }
    }

    @Test
    fun rejectsWrongVersion() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.toMutableList().apply { this[0] = "999" }))
        }
    }

    @Test
    fun rejectsCorruptedTerminator() {
        assertThrows(IllegalArgumentException::class.java) {
            ChessGameSnapshot.parse(encoded(validFields.toMutableList().apply { this[lastIndex] = "BROKEN" }))
        }
    }
}
