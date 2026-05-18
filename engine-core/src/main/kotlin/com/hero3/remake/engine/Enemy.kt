package com.hero3.remake.engine

/**
 * 적 데이터 — enemy_dat.json 한국어 이름 기반.
 * 실 stat 바이트는 미해독이라 placeholder 수치.
 */
data class EnemyDef(
    val id: String,
    val nameKo: String,
    val nameEn: String,
    val hpMax: Int,
    val atk: Int,
    val def: Int,
    val expReward: Int,
    val goldReward: Int,
    /** assets/sprites/<spriteDir> 안의 첫 PNG 사용. enemy_dat 순서 기반 매핑. */
    val spriteDir: String,
    /** 처치 시 드롭 가능한 (itemId, 확률[0..1]) 쌍. 모두 굴려서 드롭. */
    val dropTable: List<Pair<String, Float>> = emptyList(),
)

data class EnemyInstance(
    val def: EnemyDef,
    var hp: Int,
)

object EnemyRegistry {
    val all: List<EnemyDef> = listOf(
        EnemyDef("askran_guard",   "아스크란가드",  "Askran Guard",     hpMax = 60,  atk = 12, def = 6,  expReward = 8,  goldReward = 12, spriteDir = "enemy/e0100_bm",
                 dropTable = listOf("herb" to 0.4f, "potion_s" to 0.15f)),
        EnemyDef("corvus_warrior", "코르버스워리어","Corvus Warrior",   hpMax = 80,  atk = 15, def = 8,  expReward = 12, goldReward = 18, spriteDir = "enemy/e0101_bm",
                 dropTable = listOf("potion_s" to 0.2f, "ether_s" to 0.1f)),
        EnemyDef("askran_warrior", "아스크란워리어","Askran Warrior",   hpMax = 90,  atk = 16, def = 9,  expReward = 14, goldReward = 22, spriteDir = "enemy/e0102_bm",
                 dropTable = listOf("potion_s" to 0.25f, "sword_iron" to 0.05f)),
        EnemyDef("soltian_warrior","솔티안워리어",  "Soltian Warrior",  hpMax = 70,  atk = 13, def = 7,  expReward = 10, goldReward = 15, spriteDir = "enemy/e0103_bm",
                 dropTable = listOf("herb" to 0.3f, "potion_s" to 0.2f)),
        EnemyDef("askran_templar", "아스크란템플러","Askran Templar",   hpMax = 110, atk = 18, def = 12, expReward = 22, goldReward = 35, spriteDir = "enemy/e0104_bm",
                 dropTable = listOf("ether_s" to 0.3f, "potion_m" to 0.1f)),
        EnemyDef("soltian_rogue",  "솔티안로그",    "Soltian Rogue",    hpMax = 50,  atk = 17, def = 4,  expReward = 11, goldReward = 20, spriteDir = "enemy/e0105_bm",
                 dropTable = listOf("potion_s" to 0.3f)),
        EnemyDef("thief",          "도적",          "Thief",            hpMax = 45,  atk = 14, def = 4,  expReward = 9,  goldReward = 25, spriteDir = "enemy/e0106_bm",
                 dropTable = listOf("herb" to 0.5f)),
        EnemyDef("corvus_rogue",   "코르버스로그",  "Corvus Rogue",     hpMax = 55,  atk = 18, def = 5,  expReward = 13, goldReward = 22, spriteDir = "enemy/e0107_bm",
                 dropTable = listOf("potion_s" to 0.3f, "ether_s" to 0.1f)),
        EnemyDef("askran_chaser",  "아스크란체이서","Askran Chaser",    hpMax = 65,  atk = 20, def = 6,  expReward = 16, goldReward = 28, spriteDir = "enemy/e0108_bm",
                 dropTable = listOf("potion_m" to 0.15f, "armor_lthr" to 0.05f)),
        EnemyDef("corvus_assassin","코르버스어쌔신","Corvus Assassin",  hpMax = 60,  atk = 24, def = 5,  expReward = 20, goldReward = 32, spriteDir = "enemy/e0109_bm",
                 dropTable = listOf("potion_m" to 0.2f, "ether_m" to 0.1f)),
        // 보스 — id 가 boss_ 로 시작하면 처치 시 GameState 에 영구 기록
        EnemyDef("boss_guardian",  "고대 가디언",  "Ancient Guardian", hpMax = 400, atk = 32, def = 20, expReward = 200, goldReward = 500, spriteDir = "boss/boss9000_bm"),
        EnemyDef("boss_chaos",     "혼돈의 군주",  "Chaos Lord",       hpMax = 800, atk = 48, def = 28, expReward = 500, goldReward = 1200, spriteDir = "boss/boss9001_bm"),
        EnemyDef("boss_sealed",    "봉인된 신",    "Sealed God",       hpMax = 1500, atk = 64, def = 38, expReward = 1200, goldReward = 3000, spriteDir = "boss/boss9002_bm"),
    )
    private val byId = all.associateBy { it.id }

    fun get(id: String): EnemyDef? = byId[id]

    /** 무작위 적 1마리 (영웅 레벨에 따라 풀 제한). */
    fun random(heroLevel: Int): EnemyDef {
        val pool = all.take((heroLevel + 2).coerceAtMost(all.size))
        return pool.random()
    }
}
