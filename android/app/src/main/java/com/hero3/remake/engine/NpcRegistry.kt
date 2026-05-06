package com.hero3.remake.engine

import kotlin.math.abs

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
/** 특정 보스 처치 후 대체 대사. 여러 단계 진행은 [Npc.postBoss] 리스트로 시간순 선언. */
data class PostBossDialogue(
    val bossId: String,
    val ko: List<String>,
    val en: List<String>,
)

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
    /** 대화 종료 시 추가 동작. 'heal' → 파티 풀 회복(여관). */
    val action: String? = null,
    /** action 비용 (gold). action != null 일 때만 의미 있음. */
    val actionCost: Int = 0,
    /** 보스 처치 후 대체 대사. 시간순(이른 보스→늦은 보스)으로 선언; 가장 늦게 처치된 보스의 대사가 우선. */
    val postBoss: List<PostBossDialogue> = emptyList(),
    /** 순찰 경로 — 빈 리스트면 정적. 매 1.5s 마다 다음 칸. */
    val patrolPath: List<Pair<Int, Int>> = emptyList(),
    /** 대화 종료 시 시작할 퀘스트 id. 이미 active/done 이면 무시. */
    val startsQuestId: String? = null,
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
            startsQuestId = "guardian_hunt",
            postBoss = listOf(
                PostBossDialogue(
                    bossId = "boss_guardian",
                    ko = listOf(
                        "가디언을 쓰러뜨렸다고? 정말 대단하군!",
                        "솔티아의 영웅이여, 자네에게 감사를 표한다.",
                        "이제 운명의 수레바퀴는 자네 손에 달렸네.",
                    ),
                    en = listOf(
                        "You defeated the Guardian? Astonishing!",
                        "Hero of Soltia, accept our gratitude.",
                        "The wheel of destiny is now in your hands.",
                    ),
                ),
                PostBossDialogue(
                    bossId = "boss_chaos",
                    ko = listOf(
                        "혼돈의 군주마저 쓰러뜨렸군...",
                        "솔티아의 진정한 영웅이 누구인지 모두가 알게 되었네.",
                        "운명의 수레바퀴는 자네의 손에 멈춰 섰다.",
                    ),
                    en = listOf(
                        "Even the Chaos Lord has fallen to you...",
                        "All shall now know who Soltia's true hero is.",
                        "The wheel of destiny has stopped in your hand.",
                    ),
                ),
                PostBossDialogue(
                    bossId = "boss_sealed",
                    ko = listOf(
                        "봉인된 신마저... 그대는 이미 신화의 영역에 있다.",
                        "솔티아는 영원히 그대의 이름을 노래할 것이다.",
                        "이제 운명의 수레바퀴는 멈추고, 새 시대가 열렸다.",
                    ),
                    en = listOf(
                        "Even the Sealed God... you walk in the realm of legend.",
                        "Soltia shall sing your name forever.",
                        "The wheel of destiny rests; a new age has begun.",
                    ),
                ),
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
            postBoss = listOf(
                PostBossDialogue(
                    bossId = "boss_guardian",
                    ko = listOf(
                        "가디언이 사라졌으니 이제 안심하고 거래할 수 있군.",
                        "강철검 같은 더 좋은 무기를 들여왔어.",
                    ),
                    en = listOf(
                        "Now that the Guardian is gone, trade is safe.",
                        "I've stocked finer gear like the steel sword.",
                    ),
                ),
                PostBossDialogue(
                    bossId = "boss_chaos",
                    ko = listOf(
                        "혼돈의 군주마저 잡혔다고? 자네에게 어울리는 신성한 장비를 갖췄네.",
                        "성검과 용비늘갑옷, 살펴보게.",
                    ),
                    en = listOf(
                        "The Chaos Lord too? I have sacred gear worthy of you.",
                        "Holy sword and dragon scale — take a look.",
                    ),
                ),
            ),
            patrolPath = listOf(22 to 10, 23 to 10, 22 to 10, 21 to 10),
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
            patrolPath = listOf(8 to 18, 9 to 18, 9 to 19, 8 to 19),
        ),
        Npc(
            id = "innkeeper_mae",
            mapId = 0, x = 26, y = 14,
            spriteDir = "npc/npc0007_bm",
            nameKo = "여관주인 매",
            nameEn = "Innkeeper Mae",
            dialoguesKo = listOf(
                "여관에 오신 것을 환영합니다.",
                "10G 으로 푹 쉬어 가시겠어요?",
            ),
            dialoguesEn = listOf(
                "Welcome to the inn.",
                "Rest for 10 gold?",
            ),
            action = "heal",
            actionCost = 10,
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
            patrolPath = listOf(14 to 20, 15 to 20, 15 to 21, 14 to 21),
        ),
    )

    /** map1 — 솔티아 외곽 (placeholder). */
    private val map1Npcs = listOf(
        Npc(
            id = "wanderer_lin",
            mapId = 1, x = 5, y = 5,
            spriteDir = "npc/npc0004_bm",
            nameKo = "방랑자 린",
            nameEn = "Wanderer Lin",
            dialoguesKo = listOf(
                "이 길을 따라가면 동굴이 나와.",
                "조심해. 도적들이 자주 출몰하니까.",
            ),
            dialoguesEn = listOf(
                "Follow this road to reach the cave.",
                "Be careful. Bandits often appear here.",
            ),
            patrolPath = listOf(5 to 5, 6 to 5, 6 to 6, 5 to 6),
        ),
        Npc(
            id = "farmer_dol",
            mapId = 1, x = 12, y = 8,
            spriteDir = "npc/npc0005_bm",
            nameKo = "농부 돌",
            nameEn = "Farmer Dol",
            dialoguesKo = listOf(
                "올해 수확이 좋네요.",
                "솔티아 마을은 서쪽이에요.",
            ),
            dialoguesEn = listOf(
                "Good harvest this year.",
                "Soltia village is to the west.",
            ),
            startsQuestId = "herb_gather",
        ),
    )

    /** map10 — 가디언 동굴 입구 (placeholder). */
    private val map10Npcs = listOf(
        Npc(
            id = "shrine_eli",
            mapId = 10, x = 3, y = 3,
            spriteDir = "npc/npc0010_bm",
            nameKo = "치유 신관 엘리",
            nameEn = "Shrine Priestess Eli",
            dialoguesKo = listOf(
                "동굴은 위험합니다.",
                "100G 으로 치유의 빛을 받으시겠어요?",
            ),
            dialoguesEn = listOf(
                "The cave is dangerous.",
                "Receive healing light for 100 gold?",
            ),
            action = "heal",
            actionCost = 100,
        ),
        Npc(
            id = "merchant_jin",
            mapId = 10, x = 12, y = 3,
            spriteDir = "npc/npc0011_bm",
            nameKo = "방랑 상인 진",
            nameEn = "Wandering Merchant Jin",
            dialoguesKo = listOf(
                "여기까지 오느라 고생했군.",
                "회복 아이템만 취급한다.",
            ),
            dialoguesEn = listOf(
                "You've come a long way.",
                "I deal only in recovery items.",
            ),
        ),
        Npc(
            id = "scholar_ed",
            mapId = 10, x = 6, y = 6,
            spriteDir = "npc/npc0006_bm",
            nameKo = "학자 에드",
            nameEn = "Scholar Ed",
            dialoguesKo = listOf(
                "고대의 가디언이 잠들어 있는 곳이라네.",
                "운명의 수레바퀴는 여기서부터 시작됐다.",
                "조심하시게...",
            ),
            dialoguesEn = listOf(
                "The ancient guardian sleeps here.",
                "The wheel of destiny began here.",
                "Be careful...",
            ),
            postBoss = listOf(
                PostBossDialogue(
                    bossId = "boss_guardian",
                    ko = listOf(
                        "가디언이 잠들었군... 자네가 해냈어.",
                        "이 유적의 비밀이 곧 풀릴 것이네.",
                    ),
                    en = listOf(
                        "The Guardian has fallen... you did it.",
                        "The secrets of this ruin will soon unravel.",
                    ),
                ),
            ),
        ),
    )

    /** map11 — 혼돈의 영역. */
    private val map11Npcs = listOf(
        Npc(
            id = "oracle_sera",
            mapId = 11, x = 4, y = 8,
            spriteDir = "npc/npc0008_bm",
            nameKo = "신탁관 세라",
            nameEn = "Oracle Sera",
            dialoguesKo = listOf(
                "운명의 끝이 가까워지고 있어.",
                "혼돈의 군주는 모든 빛을 삼킬 것이다.",
                "준비가 되었거든 더 깊이 들어가라.",
            ),
            dialoguesEn = listOf(
                "The end of destiny draws near.",
                "The Chaos Lord will swallow all light.",
                "Go deeper when you are ready.",
            ),
            postBoss = listOf(
                PostBossDialogue(
                    bossId = "boss_chaos",
                    ko = listOf(
                        "혼돈은 잠들었다. 빛이 다시 흐르네.",
                        "그대의 이름은 별이 되어 영원히 빛나리.",
                    ),
                    en = listOf(
                        "Chaos sleeps. The light flows once more.",
                        "Your name shall shine as a star, forever.",
                    ),
                ),
                PostBossDialogue(
                    bossId = "boss_sealed",
                    ko = listOf(
                        "봉인된 신... 그것이 진짜 운명이었다.",
                        "그대는 모든 예언을 넘어섰다.",
                        "이 세계는 그대 덕에 새로 태어났다.",
                    ),
                    en = listOf(
                        "The Sealed God... that was the true destiny.",
                        "You have surpassed every prophecy.",
                        "This world is reborn because of you.",
                    ),
                ),
            ),
            patrolPath = listOf(4 to 8, 4 to 9, 5 to 9, 5 to 8),
        ),
    )

    /** map12 — 봉인의 사원. */
    private val map12Npcs = listOf(
        Npc(
            id = "guardian_spirit",
            mapId = 12, x = 5, y = 5,
            spriteDir = "npc/npc0012_bm",
            nameKo = "수호 영혼",
            nameEn = "Guardian Spirit",
            dialoguesKo = listOf(
                "이곳은 시간이 멈춘 사원이다.",
                "봉인된 신이 잠들어 있다.",
                "그대가 정말로 깰 자격이 있는지...",
            ),
            dialoguesEn = listOf(
                "Time stands still in this temple.",
                "The Sealed God slumbers within.",
                "Whether you are truly worthy to wake him...",
            ),
            postBoss = listOf(
                PostBossDialogue(
                    bossId = "boss_sealed",
                    ko = listOf(
                        "신은 잠들었다... 영원히.",
                        "그대의 길은 신화가 되어 전해질 것이다.",
                    ),
                    en = listOf(
                        "The God has slept... forever.",
                        "Your path will be told as legend.",
                    ),
                ),
            ),
        ),
        Npc(
            id = "lost_priest",
            mapId = 12, x = 14, y = 11,
            spriteDir = "npc/npc0013_bm",
            nameKo = "잃어버린 사제",
            nameEn = "Lost Priest",
            dialoguesKo = listOf(
                "이 사원에 갇힌 지 천 년이 되었다.",
                "봉인을 푼다면... 부탁한다, 자비를.",
            ),
            dialoguesEn = listOf(
                "I've been trapped in this temple a thousand years.",
                "If you break the seal... I beg, mercy.",
            ),
            patrolPath = listOf(14 to 11, 15 to 11, 14 to 11, 13 to 11),
        ),
    )

    private val all: List<Npc> = map0Npcs + map1Npcs + map10Npcs + map11Npcs + map12Npcs

    fun forMap(mapId: Int): List<Npc> = all.filter { it.mapId == mapId }

    /** elapsedMs 기준 NPC 의 현재 타일 좌표. patrolPath 가 비면 base x,y. */
    fun effectivePos(npc: Npc, elapsedMs: Long): Pair<Int, Int> {
        if (npc.patrolPath.isEmpty()) return npc.x to npc.y
        val step = ((elapsedMs / 1500L) % npc.patrolPath.size).toInt()
        return npc.patrolPath[step]
    }

    fun adjacent(mapId: Int, x: Int, y: Int, elapsedMs: Long = 0L): Npc? {
        return forMap(mapId).firstOrNull { npc ->
            val (nx, ny) = effectivePos(npc, elapsedMs)
            val dx = abs(nx - x)
            val dy = abs(ny - y)
            (dx + dy) == 1   // Manhattan 거리 1 (인접 4방향)
        }
    }
}
