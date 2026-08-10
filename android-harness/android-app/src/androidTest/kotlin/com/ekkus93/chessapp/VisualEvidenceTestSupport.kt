package com.ekkus93.chessapp

import android.content.ContentValues
import android.graphics.Bitmap
import android.os.Environment
import android.provider.MediaStore
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.test.platform.app.InstrumentationRegistry

internal fun saveVisualEvidence(name: String, image: ImageBitmap) {
    require(name.matches(Regex("[a-z0-9-]+"))) { "evidence name must be a safe lowercase slug" }
    val resolver = InstrumentationRegistry.getInstrumentation().targetContext.contentResolver
    val values = ContentValues().apply {
        put(MediaStore.Downloads.DISPLAY_NAME, "$name.png")
        put(MediaStore.Downloads.MIME_TYPE, "image/png")
        put(
            MediaStore.Downloads.RELATIVE_PATH,
            "${Environment.DIRECTORY_DOWNLOADS}/RustChessEvidence",
        )
        put(MediaStore.Downloads.IS_PENDING, 1)
    }
    val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
        ?: error("failed to allocate visual evidence media entry for $name")
    try {
        resolver.openOutputStream(uri)?.use { output ->
            check(image.asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, output)) {
                "failed to encode visual evidence image for $name"
            }
        } ?: error("failed to open visual evidence output stream for $name")
        values.clear()
        values.put(MediaStore.Downloads.IS_PENDING, 0)
        check(resolver.update(uri, values, null, null) == 1) {
            "failed to publish visual evidence image for $name"
        }
    } catch (error: RuntimeException) {
        resolver.delete(uri, null, null)
        throw error
    }
}
