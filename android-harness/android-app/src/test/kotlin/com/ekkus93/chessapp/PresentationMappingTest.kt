package com.ekkus93.chessapp

import org.junit.Assert.assertEquals
import org.junit.Test

class PresentationMappingTest {
    @Test
    fun depthDescriptorsCoverExactSupportedRange() {
        assertEquals("Quick", depthLabel(1))
        assertEquals("Quick", depthLabel(2))
        assertEquals("Balanced", depthLabel(3))
        assertEquals("Balanced", depthLabel(5))
        assertEquals("Strong", depthLabel(6))
        assertEquals("Strong", depthLabel(8))
        assertEquals("Deep", depthLabel(9))
        assertEquals("Deep", depthLabel(12))
    }

    @Test(expected = IllegalStateException::class)
    fun unsupportedDepthDoesNotReceivePresentationDescriptor() {
        depthLabel(13)
    }

    @Test
    fun promotionChoicesPreserveExactAuthoritativeMovesInPlayerOrder() {
        val authoritative = listOf("a7a8n", "a7a8q", "a7a8b", "a7a8r")
        assertEquals(
            listOf("a7a8q", "a7a8r", "a7a8b", "a7a8n"),
            orderedPromotionMoves(authoritative),
        )
    }
}
