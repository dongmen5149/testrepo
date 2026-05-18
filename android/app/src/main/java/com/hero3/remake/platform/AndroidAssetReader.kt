package com.hero3.remake.platform

import android.content.Context
import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import java.io.IOException

/**
 * Android `Context.assets` 백킹의 [AssetReader] 구현 (Hero3 app).
 *
 * Phase C Step 4c (2026-05-19) — Hero4 와 동일 패턴. Hero3CatalogLoader (R71) 가 사용.
 * apps/hero4-android 의 동일 클래스와 1:1 동일 (engine-core 의 AssetReader interface 구현).
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
