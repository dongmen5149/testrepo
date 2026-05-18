package com.hero3.remake.engine

/**
 * 게임 영구 설정 — engine-core 가 사용하는 슬림 인터페이스.
 *
 * Phase C Step 4a (2026-05-19) 에서 신설. 안드로이드는 `SharedPreferences` 백킹,
 * 향후 iOS 는 `NSUserDefaults`, JVM 테스트는 in-memory 구현으로 actual 가능.
 *
 * Hero3 의 `Settings` 클래스 (android/app/.../engine/Settings.kt) 가 이 인터페이스를 구현.
 * Hero4 도 향후 자체 implement 가능 (또는 같은 Settings 클래스 재사용).
 */
interface AppSettings {

    /** 언어 코드. "ko" (default) / "en". */
    var language: String

    /** 4× HD asset 사용 여부. */
    var qualityHd: Boolean

    /** 인카운터 배수. 0.0 = 비활성, 0.5 = 절반, 1.0 = 기본, 2.0 = 두 배. */
    var encounterMultiplier: Float

    /** MapWalk 미니맵 표시 여부. */
    var minimapVisible: Boolean

    /** 현재 품질에 따른 sprite asset 디렉토리. */
    fun spritesDir(): String = if (qualityHd) "sprites_hd" else "sprites"

    /** 현재 언어가 영어인지. */
    val isEn: Boolean get() = language == "en"

    /** 한·영 분기 헬퍼. 한국어가 기본 언어이므로 ko 인자가 앞. */
    fun lang(ko: String, en: String): String = if (isEn) en else ko
}
