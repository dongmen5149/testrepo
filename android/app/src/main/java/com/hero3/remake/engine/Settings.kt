package com.hero3.remake.engine

import android.content.Context
import android.content.SharedPreferences

/**
 * SharedPreferences 기반 영구 설정. engine-core 의 [AppSettings] 인터페이스 구현.
 *
 * - language: "ko" (default) / "en"
 * - quality:  "sd" (default) / "hd"  (sprites_hd 디렉토리에서 4× 자산 사용)
 *
 * Phase C Step 4a (2026-05-19) — 공유 가능한 동작 (spritesDir/isEn/lang) 은 interface
 * default 로 이전, 저장소 backed property 만 override.
 */
class Settings(context: Context) : AppSettings {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("hero3_remake", Context.MODE_PRIVATE)

    override var language: String
        get() = prefs.getString(KEY_LANGUAGE, "ko") ?: "ko"
        set(value) { prefs.edit().putString(KEY_LANGUAGE, value).apply() }

    override var qualityHd: Boolean
        get() = prefs.getBoolean(KEY_QUALITY_HD, false)
        set(value) { prefs.edit().putBoolean(KEY_QUALITY_HD, value).apply() }

    override var encounterMultiplier: Float
        get() = prefs.getFloat(KEY_ENCOUNTER, 1.0f)
        set(value) { prefs.edit().putFloat(KEY_ENCOUNTER, value).apply() }

    override var minimapVisible: Boolean
        get() = prefs.getBoolean(KEY_MINIMAP, true)
        set(value) { prefs.edit().putBoolean(KEY_MINIMAP, value).apply() }

    companion object {
        private const val KEY_LANGUAGE = "language"
        private const val KEY_QUALITY_HD = "quality_hd"
        private const val KEY_ENCOUNTER = "encounter_multiplier"
        private const val KEY_MINIMAP   = "minimap_visible"
    }
}
