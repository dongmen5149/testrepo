package com.hero3.remake.engine

import android.content.Context
import android.content.SharedPreferences

/**
 * SharedPreferences 기반 영구 설정.
 *
 * - language: "ko" (default) / "en"
 * - quality:  "sd" (default) / "hd"  (sprites_hd 디렉토리에서 4× 자산 사용)
 */
class Settings(context: Context) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("hero3_remake", Context.MODE_PRIVATE)

    var language: String
        get() = prefs.getString(KEY_LANGUAGE, "ko") ?: "ko"
        set(value) { prefs.edit().putString(KEY_LANGUAGE, value).apply() }

    var qualityHd: Boolean
        get() = prefs.getBoolean(KEY_QUALITY_HD, false)
        set(value) { prefs.edit().putBoolean(KEY_QUALITY_HD, value).apply() }

    /** 현재 품질에 따른 sprite asset 디렉토리. */
    fun spritesDir(): String = if (qualityHd) "sprites_hd" else "sprites"

    companion object {
        private const val KEY_LANGUAGE = "language"
        private const val KEY_QUALITY_HD = "quality_hd"
    }
}
