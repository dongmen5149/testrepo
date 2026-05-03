package com.hero3.remake.engine

/**
 * 사운드 이펙트 stub. 현재는 호출만 받고 무시 — 향후 SMAF→OGG 변환 후
 * MediaPlayer 연동 시 [play]/[playMusic] 만 구현하면 된다 (PROGRESS §4.5).
 *
 * 이 인터페이스를 미리 두는 이유:
 *  - BattleScene 등 호출처를 미리 wired up 해 두면 audio engine 도입 시 편함.
 *  - 디버그 빌드에서 어떤 효과음이 필요한지 EventBus 처럼 가시화 가능.
 */
object SfxBus {
    enum class Sfx { HIT, HEAL, LEVEL_UP, BOSS_INTRO, BOSS_DEFEAT, MENU_MOVE, MENU_OK, CHEST }
    enum class Bgm { TITLE, FIELD, BATTLE, BOSS, ENDING }

    /** debug=true 면 EventBus 토스트로 시각화 (개발 중 hook 확인용). */
    var debugToast: Boolean = false

    fun play(sfx: Sfx) {
        if (debugToast) EventBus.push("[sfx] $sfx")
        // TODO: MediaPlayer / SoundPool 연결
    }

    fun playMusic(bgm: Bgm) {
        if (debugToast) EventBus.push("[bgm] $bgm")
        // TODO
    }

    fun stopMusic() {
        // TODO
    }
}
