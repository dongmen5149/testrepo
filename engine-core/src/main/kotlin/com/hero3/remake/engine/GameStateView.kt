package com.hero3.remake.engine

/**
 * 게임 상태 중 engine-core 모듈이 의존하는 부분만 추출한 인터페이스.
 *
 * Phase C Step 2 (2026-05-19) 에서 신설. Quest / ShopRegistry 가 GameState
 * 직접 의존을 끊고 이 인터페이스만 받도록 변경 → engine-core 로 이전 가능.
 *
 * 안드로이드 측 GameState 는 SharedPreferences 백킹의 구현체이고,
 * 향후 KMM commonMain 이전 시 expect/actual 또는 멀티플랫폼 storage 로 교체.
 */
interface GameStateView {
    var activeQuestIds: Set<String>
    var doneQuestIds: Set<String>
    var gold: Int

    fun isBossDefeated(id: String): Boolean
    fun saveInventory(inv: Inventory)
}
