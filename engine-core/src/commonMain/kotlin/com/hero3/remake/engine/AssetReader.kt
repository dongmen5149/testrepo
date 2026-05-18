package com.hero3.remake.engine

/**
 * 플랫폼-중립적 자산 읽기 인터페이스 — engine-core 가 JSON / 바이너리 자산을
 * 읽을 때 Android `Context.assets`, iOS `Bundle.main`, JVM `ClassLoader.getResource`
 * 등 platform 별 구현으로 위임.
 *
 * Phase C Step 4c (2026-05-19) 에서 신설. 첫 사용처는 Hero4 catalog loader.
 *
 * 구현체:
 *   - Android: `AndroidAssetReader(context)` → `context.assets.open(path)`
 *   - JVM (test): `ClasspathAssetReader` → `javaClass.classLoader.getResource(path)`
 *   - iOS (future): `BundleAssetReader` → `NSBundle.mainBundle`
 */
interface AssetReader {

    /** 자산 텍스트 (UTF-8) 로 읽기. 존재하지 않으면 [AssetNotFound] throw. */
    fun readText(path: String): String

    /** 자산 바이트 로 읽기. */
    fun readBytes(path: String): ByteArray

    /** 자산 존재 여부 (optional, default = readText 시도 후 catch). */
    fun exists(path: String): Boolean {
        return try {
            readBytes(path)
            true
        } catch (_: Throwable) {
            false
        }
    }
}

class AssetNotFound(path: String, cause: Throwable? = null) :
    RuntimeException("Asset not found: $path", cause)
