package com.hero3.remake.engine

/**
 * 퀘스트 데이터 + 진행 상태.
 *
 * 상태:
 *   미시작 (Active 도 Done 도 아님)
 *   ACTIVE  : 받은 상태
 *   DONE    : 완료
 *
 * 완료 조건은 두 종류:
 *   1) defeatBossId 가 처치되어 있으면 자동 완료 → 보상 지급
 *   2) 수동 (나중에 NPC 트리거 추가)
 */
data class Quest(
    val id: String,
    val titleKo: String,
    val titleEn: String,
    val descKo: String,
    val descEn: String,
    val defeatBossId: String? = null,
    val requiredItemId: String? = null,
    val requiredItemCount: Int = 0,
    val rewardGold: Int = 0,
    val rewardItemId: String? = null,
    /** 완료 시 자동 시작할 후속 퀘스트 id. */
    val followUpQuestId: String? = null,
)

object QuestRegistry {
    val all: List<Quest> = listOf(
        Quest(
            id = "guardian_hunt",
            titleKo = "고대 가디언 토벌",
            titleEn = "Slay the Ancient Guardian",
            descKo = "촌장의 의뢰: 가디언 동굴의 고대 가디언을 처치하라.",
            descEn = "Elder's request: defeat the Ancient Guardian in the cave.",
            defeatBossId = "boss_guardian",
            rewardGold = 300,
            rewardItemId = "potion_m",
            followUpQuestId = "chaos_lord",
        ),
        Quest(
            id = "chaos_lord",
            titleKo = "혼돈의 군주",
            titleEn = "The Chaos Lord",
            descKo = "촌장: 가디언 너머의 어둠을 잠재워라.",
            descEn = "Elder: silence the darkness beyond the Guardian.",
            defeatBossId = "boss_chaos",
            rewardGold = 1000,
            rewardItemId = "ring_mana",
            followUpQuestId = "sealed_god",
        ),
        Quest(
            id = "sealed_god",
            titleKo = "봉인된 신",
            titleEn = "The Sealed God",
            descKo = "신탁관 세라: 동쪽 사원의 봉인을 풀어라.",
            descEn = "Oracle Sera: break the seal at the eastern temple.",
            defeatBossId = "boss_sealed",
            rewardGold = 3000,
            rewardItemId = "ring_dest",
        ),
        Quest(
            id = "herb_gather",
            titleKo = "약초 모으기",
            titleEn = "Gather Herbs",
            descKo = "농부 돌의 부탁: 약초 5개를 모아 오라.",
            descEn = "Farmer Dol's request: gather 5 herbs.",
            requiredItemId = "herb",
            requiredItemCount = 5,
            rewardGold = 100,
        ),
    )

    private val byId = all.associateBy { it.id }
    fun get(id: String): Quest? = byId[id]
}

/**
 * GameState 위에서 퀘스트 상태를 관리하는 헬퍼.
 *  - SharedPreferences StringSet 두 개 (active / done) 사용
 *  - 보스 처치 자동 완료 + 보상 지급은 `tickAutoComplete()` 가 처리
 */
class QuestLog(private val gameState: GameState) {

    fun isActive(id: String): Boolean = gameState.activeQuestIds.contains(id)
    fun isDone(id: String): Boolean = gameState.doneQuestIds.contains(id)

    fun start(id: String) {
        if (isDone(id) || isActive(id)) return
        gameState.activeQuestIds = gameState.activeQuestIds + id
    }

    /**
     * 활성 퀘스트 중 자동 완료 가능한 것을 처리. 보상 지급.
     * @return 새로 완료된 퀘스트 id 목록
     */
    fun tickAutoComplete(inventory: Inventory): List<String> {
        val newlyDone = mutableListOf<String>()
        for (id in gameState.activeQuestIds.toList()) {
            val q = QuestRegistry.get(id) ?: continue
            val bossOk = q.defeatBossId?.let { gameState.isBossDefeated(it) } ?: false
            val itemOk = q.requiredItemId?.let { reqId ->
                val owned = inventory.all().filter { it.itemId == reqId }.sumOf { it.count }
                owned >= q.requiredItemCount
            } ?: false
            // 두 조건 중 하나라도 충족
            val canFinish = bossOk || itemOk
            if (!canFinish) continue
            // 아이템 요구 시 차감 (역순으로 안전하게)
            if (itemOk && q.requiredItemId != null) {
                var remaining = q.requiredItemCount
                while (remaining > 0) {
                    val all = inventory.all()
                    val slotIdx = all.indexOfLast { it.itemId == q.requiredItemId }
                    if (slotIdx < 0) break
                    val take = minOf(remaining, all[slotIdx].count)
                    inventory.remove(slotIdx, take)
                    remaining -= take
                }
            }
            run {
                gameState.activeQuestIds = gameState.activeQuestIds - id
                gameState.doneQuestIds   = gameState.doneQuestIds + id
                if (q.rewardGold > 0) gameState.gold += q.rewardGold
                q.rewardItemId?.let { inventory.add(it, 1) }
                newlyDone += id
                // 후속 퀘스트 자동 시작
                q.followUpQuestId?.let { followId ->
                    if (!isDone(followId) && !isActive(followId)) {
                        gameState.activeQuestIds = gameState.activeQuestIds + followId
                    }
                }
            }
        }
        if (newlyDone.isNotEmpty()) gameState.saveInventory(inventory)
        return newlyDone
    }
}
