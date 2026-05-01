package com.hero3.remake.engine

/**
 * 맵별 NPC 정의 — 임시 하드코딩 (Ghidra 후 _mp extras 파싱으로 자동화 예정).
 *
 * 각 NPC 는:
 *  - id: 고유 식별자
 *  - mapId: 등장 맵
 *  - x, y: 타일 좌표
 *  - spriteDir: assets/sprites/<dir> 안의 첫 frame PNG 사용
 *  - nameKo / nameEn: 화자 이름
 *  - dialoguesKo / dialoguesEn: 대사 라인 (OK 키 누를 때마다 다음 라인)
 */
data class Npc(
    val id: String,
    val mapId: Int,
    val x: Int,
    val y: Int,
    val spriteDir: String,
    val nameKo: String,
    val nameEn: String,
    val dialoguesKo: List<String>,
    val dialoguesEn: List<String>,
)

object NpcRegistry {

    /** NEOSOLTIA (map0) 의 NPC 들. */
    private val map0Npcs = listOf(
        Npc(
            id = "soltia_elder",
            mapId = 0, x = 17, y = 12,
            spriteDir = "npc/npc0000_bm",
            nameKo = "솔티아 촌장",
            nameEn = "Soltia Elder",
            dialoguesKo = listOf(
                "어서 오게, 젊은 영웅이여.",
                "솔티아의 평화는 자네에게 달려 있다.",
                "운명의 수레바퀴가 돌기 시작했네...",
            ),
            dialoguesEn = listOf(
                "Welcome, young hero.",
                "The peace of Soltia depends on you.",
                "The wheel of destiny has begun to turn...",
            ),
        ),
        Npc(
            id = "merchant_bo",
            mapId = 0, x = 22, y = 10,
            spriteDir = "npc/npc0001_bm",
            nameKo = "상인 보",
            nameEn = "Merchant Bo",
            dialoguesKo = listOf(
                "어서오세요! 좋은 물건 많아요.",
                "물약과 무기를 팝니다.",
            ),
            dialoguesEn = listOf(
                "Welcome! I have great items.",
                "I sell potions and weapons.",
            ),
        ),
        Npc(
            id = "guard_kim",
            mapId = 0, x = 8, y = 18,
            spriteDir = "npc/npc0002_bm",
            nameKo = "경비병 김",
            nameEn = "Guard Kim",
            dialoguesKo = listOf(
                "마을 밖은 위험합니다.",
                "조심하세요.",
            ),
            dialoguesEn = listOf(
                "It's dangerous outside the village.",
                "Be careful.",
            ),
        ),
        Npc(
            id = "kid_ria",
            mapId = 0, x = 14, y = 20,
            spriteDir = "npc/npc0003_bm",
            nameKo = "아이 리아",
            nameEn = "Child Ria",
            dialoguesKo = listOf(
                "헤헤, 안녕!",
                "여기는 내가 자주 노는 곳이야.",
            ),
            dialoguesEn = listOf(
                "Hehe, hello!",
                "This is where I usually play.",
            ),
        ),
    )

    private val all: List<Npc> = map0Npcs

    fun forMap(mapId: Int): List<Npc> = all.filter { it.mapId == mapId }

    fun adjacent(mapId: Int, x: Int, y: Int): Npc? {
        return forMap(mapId).firstOrNull { npc ->
            val dx = kotlin.math.abs(npc.x - x)
            val dy = kotlin.math.abs(npc.y - y)
            (dx + dy) == 1   // Manhattan 거리 1 (인접 4방향)
        }
    }
}
