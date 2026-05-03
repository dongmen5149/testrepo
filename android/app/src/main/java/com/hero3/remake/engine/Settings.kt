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

    /** 인카운터 배수. 0.0 = 비활성, 0.5 = 절반, 1.0 = 기본, 2.0 = 두 배. */
    var encounterMultiplier: Float
        get() = prefs.getFloat(KEY_ENCOUNTER, 1.0f)
        set(value) { prefs.edit().putFloat(KEY_ENCOUNTER, value).apply() }

    /** MapWalk 미니맵 표시 여부. */
    var minimapVisible: Boolean
        get() = prefs.getBoolean(KEY_MINIMAP, true)
        set(value) { prefs.edit().putBoolean(KEY_MINIMAP, value).apply() }

    /** 현재 품질에 따른 sprite asset 디렉토리. */
    fun spritesDir(): String = if (qualityHd) "sprites_hd" else "sprites"

    companion object {
        private const val KEY_LANGUAGE = "language"
        private const val KEY_QUALITY_HD = "quality_hd"
        private const val KEY_ENCOUNTER = "encounter_multiplier"
        private const val KEY_MINIMAP   = "minimap_visible"
    }
}
