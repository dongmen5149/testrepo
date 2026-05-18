package com.hero4.remake.platform

import android.content.Context
import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import java.io.IOException

/**
 * Android `Context.assets` 백킹의 [AssetReader] 구현.
 *
 * Phase C Step 4c (2026-05-19) — Hero4 catalog loader 가 Context 대신 이 추상화 사용.
 * Hero3 도 향후 동일 구현체 사용 가능 (현재는 scene 들이 Context.assets 직접 사용).
 */
class AndroidAssetReader(private val context: Context) : AssetReader {

    override fun readText(path: String): String = try {
        context.assets.open(path).bufferedReader().use { it.readText() }
    } catch (e: IOException) {
        throw AssetNotFound(path, e)
    }

    override fun readBytes(path: String): ByteArray = try {
        context.assets.open(path).use { it.readBytes() }
    } catch (e: IOException) {
        throw AssetNotFound(path, e)
    }
}
