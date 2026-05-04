package com.hero3.remake.engine

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

/**
 * 게임 진행 상태. SharedPreferences 로 영구 저장.
 *
 * 향후 확장:
 *  - 인벤토리 (slot 별 item id, count, attributes)
 *  - 파티 (캐릭터 ID 목록, 레벨, 경험치)
 *  - 퀘스트 플래그
 *  - 게임 시간/일자
 */
class GameState(context: Context, slotId: Int = 0) {
    private val prefs: SharedPreferences =
        context.getSharedPreferences("hero3_gamestate_slot$slotId", Context.MODE_PRIVATE)
    val slotId: Int = slotId

    /** 현재 맵 ID (예: 0 → map0_mp, 100 → map100_mp). 기본 = 0 (NEOSOLTIA). */
    var currentMapId: Int
        get() = prefs.getInt(KEY_MAP_ID, 0)
        set(v) { prefs.edit().putInt(KEY_MAP_ID, v).apply() }

    /** 영웅 타일 좌표. 기본 = 맵 중앙 부근. */
    var heroX: Int
        get() = prefs.getInt(KEY_HERO_X, -1)
        set(v) { prefs.edit().putInt(KEY_HERO_X, v).apply() }

    var heroY: Int
        get() = prefs.getInt(KEY_HERO_Y, -1)
        set(v) { prefs.edit().putInt(KEY_HERO_Y, v).apply() }

    /** 영웅 바라보는 방향: 0=DOWN, 1=UP, 2=LEFT, 3=RIGHT. */
    var heroFacing: Int
        get() = prefs.getInt(KEY_HERO_FACING, FACING_DOWN)
        set(v) { prefs.edit().putInt(KEY_HERO_FACING, v).apply() }

    /** 파티 리더 캐릭터 ID (현재는 단일 영웅 = 0). */
    var partyLeader: Int
        get() = prefs.getInt(KEY_PARTY_LEADER, 0)
        set(v) { prefs.edit().putInt(KEY_PARTY_LEADER, v).apply() }

    /** 활성/완료 퀘스트 id 집합 (StringSet 영구). */
    var activeQuestIds: Set<String>
        get() = prefs.getStringSet(KEY_QUESTS_ACTIVE, emptySet()) ?: emptySet()
        set(v) { prefs.edit().putStringSet(KEY_QUESTS_ACTIVE, v).apply() }

    var doneQuestIds: Set<String>
        get() = prefs.getStringSet(KEY_QUESTS_DONE, emptySet()) ?: emptySet()
        set(v) { prefs.edit().putStringSet(KEY_QUESTS_DONE, v).apply() }

    /** 방문한 맵 id 집합 (fast travel 후보). */
    var visitedMapIds: Set<Int>
        get() = (prefs.getStringSet(KEY_VISITED, emptySet()) ?: emptySet()).map { it.toIntOrNull() ?: 0 }.toSet()
        set(v) { prefs.edit().putStringSet(KEY_VISITED, v.map { it.toString() }.toSet()).apply() }

    fun markVisited(mapId: Int) {
        visitedMapIds = visitedMapIds + mapId
    }

    /** 첫 MapWalk 진입 튜토리얼 노출 여부. */
    var tutorialShown: Boolean
        get() = prefs.getBoolean(KEY_TUTORIAL, false)
        set(v) { prefs.edit().putBoolean(KEY_TUTORIAL, v).apply() }

    /** 누적 플레이 시간 (ms). MapWalkScene 등이 deltaMs 만큼 누적. */
    var playTimeMs: Long
        get() = prefs.getLong(KEY_PLAYTIME, 0L)
        set(v) { prefs.edit().putLong(KEY_PLAYTIME, v).apply() }

    fun addPlayTime(deltaMs: Long) {
        if (deltaMs <= 0) return
        prefs.edit().putLong(KEY_PLAYTIME, playTimeMs + deltaMs).apply()
    }

    /**
     * 마지막으로 사용자가 SAVE / LOAD 한 수동 슬롯 번호 (1..3). 0 이면 미설정.
     * 보스 처치 등 체크포인트에서 자동 미러링 대상으로 사용.
     */
    var lastSavedSlot: Int
        get() = prefs.getInt(KEY_LAST_SAVED_SLOT, 0)
        set(v) { prefs.edit().putInt(KEY_LAST_SAVED_SLOT, v).apply() }

    /** 게임 클리어(봉인된 신 처치) 플래그. EndingScene 진입 시 set. */
    var gameCleared: Boolean
        get() = prefs.getBoolean(KEY_CLEARED, false)
        set(v) { prefs.edit().putBoolean(KEY_CLEARED, v).apply() }

    /** 연 보물상자 id 집합. */
    var openedChestIds: Set<String>
        get() = prefs.getStringSet(KEY_CHESTS, emptySet()) ?: emptySet()
        set(v) { prefs.edit().putStringSet(KEY_CHESTS, v).apply() }

    /** 한 번이라도 처치한 적 id 집합 (도감용). */
    var defeatedEnemyIds: Set<String>
        get() = prefs.getStringSet(KEY_DEFEATED, emptySet()) ?: emptySet()
        set(v) { prefs.edit().putStringSet(KEY_DEFEATED, v).apply() }

    fun markEnemyDefeated(id: String) {
        defeatedEnemyIds = defeatedEnemyIds + id
    }

    /** 처치한 보스 id 집합. */
    fun isBossDefeated(id: String): Boolean =
        prefs.getStringSet(KEY_BOSSES, emptySet())?.contains(id) == true

    fun markBossDefeated(id: String) {
        val s = (prefs.getStringSet(KEY_BOSSES, emptySet()) ?: emptySet()).toMutableSet()
        s.add(id)
        prefs.edit().putStringSet(KEY_BOSSES, s).apply()
    }

    /** 소지금. 새 게임 = 200G. */
    var gold: Int
        get() = prefs.getInt(KEY_GOLD, 200)
        set(v) { prefs.edit().putInt(KEY_GOLD, v).apply() }

    /** 파티 멤버 목록 (영구). 비어있으면 기본 파티 반환. */
    fun loadParty(): List<Character> {
        val raw = prefs.getString(KEY_PARTY, null) ?: return CharacterRegistry.defaultParty()
        return try {
            val arr = JSONArray(raw)
            (0 until arr.length()).map { i ->
                val o = arr.getJSONObject(i)
                Character(
                    id      = o.getString("id"),
                    classId = o.getString("classId"),
                    level   = o.getInt("level"),
                    hp      = o.getInt("hp"),    hpMax = o.getInt("hpMax"),
                    sp      = o.getInt("sp"),    spMax = o.getInt("spMax"),
                    exp     = o.getInt("exp"),
                    equipWeapon    = o.optString("eqW", "").ifEmpty { null },
                    equipArmor     = o.optString("eqA", "").ifEmpty { null },
                    equipAccessory = o.optString("eqR", "").ifEmpty { null },
                )
            }
        } catch (_: Exception) {
            CharacterRegistry.defaultParty()
        }
    }

    fun saveParty(party: List<Character>) {
        val arr = JSONArray()
        for (c in party) {
            arr.put(JSONObject()
                .put("id", c.id).put("classId", c.classId).put("level", c.level)
                .put("hp", c.hp).put("hpMax", c.hpMax)
                .put("sp", c.sp).put("spMax", c.spMax)
                .put("exp", c.exp)
                .put("eqW", c.equipWeapon ?: "")
                .put("eqA", c.equipArmor ?: "")
                .put("eqR", c.equipAccessory ?: ""))
        }
        prefs.edit().putString(KEY_PARTY, arr.toString()).apply()
    }

    /** 인벤토리 (가방). 비어있으면 starter() 반환. */
    fun loadInventory(): Inventory {
        val raw = prefs.getString(KEY_INVENTORY, null) ?: return Inventory.starter()
        return try {
            val arr = JSONArray(raw)
            val slots = (0 until arr.length()).map { i ->
                val o = arr.getJSONObject(i)
                InventorySlot(o.getString("itemId"), o.getInt("count"))
            }
            Inventory(slots)
        } catch (_: Exception) {
            Inventory.starter()
        }
    }

    fun saveInventory(inv: Inventory) {
        val arr = JSONArray()
        for (s in inv.all()) {
            arr.put(JSONObject().put("itemId", s.itemId).put("count", s.count))
        }
        prefs.edit().putString(KEY_INVENTORY, arr.toString()).apply()
    }

    /** 위치 초기화 (새 게임 또는 맵 전환 시). */
    fun resetPosition(mapId: Int, x: Int, y: Int, facing: Int = FACING_DOWN) {
        prefs.edit()
            .putInt(KEY_MAP_ID, mapId)
            .putInt(KEY_HERO_X, x)
            .putInt(KEY_HERO_Y, y)
            .putInt(KEY_HERO_FACING, facing)
            .apply()
    }

    fun toJson(): JSONObject = JSONObject().apply {
        put("currentMapId", currentMapId)
        put("heroX", heroX)
        put("heroY", heroY)
        put("heroFacing", heroFacing)
        put("partyLeader", partyLeader)
    }

    fun isEmpty(): Boolean = heroX < 0 && heroY < 0

    fun clear() {
        prefs.edit().clear().apply()
    }

    /**
     * 모든 pending edits 를 디스크에 동기 flush. 보스 처치 직후 같은 체크포인트에서
     * 앱이 강제 종료되어도 진행 보존되게 한다.
     */
    fun flush() {
        prefs.edit().commit()
    }

    /**
     * lastSavedSlot 이 1..3 이면 현 활성 슬롯 상태를 그 수동 슬롯으로 미러링.
     * 호출자는 GameState(context, slotId=0) (live) 인 인스턴스에서 호출.
     */
    fun mirrorToLastSavedSlot(context: Context): Int {
        val n = lastSavedSlot
        if (n !in 1..3) return 0
        GameState(context, slotId = n).also { it.copyFrom(this); it.flush() }
        return n
    }

    fun copyFrom(other: GameState) {
        val edit = prefs.edit()
            .putInt(KEY_MAP_ID, other.currentMapId)
            .putInt(KEY_HERO_X, other.heroX)
            .putInt(KEY_HERO_Y, other.heroY)
            .putInt(KEY_HERO_FACING, other.heroFacing)
            .putInt(KEY_PARTY_LEADER, other.partyLeader)
            .putInt(KEY_GOLD, other.gold)
            .putLong(KEY_PLAYTIME, other.playTimeMs)
            .putBoolean(KEY_CLEARED, other.gameCleared)
            .putBoolean(KEY_TUTORIAL, other.tutorialShown)
        other.prefs.getString(KEY_PARTY, null)?.let { edit.putString(KEY_PARTY, it) }
        other.prefs.getString(KEY_INVENTORY, null)?.let { edit.putString(KEY_INVENTORY, it) }
        edit.putStringSet(KEY_BOSSES,        other.prefs.getStringSet(KEY_BOSSES, emptySet()))
        edit.putStringSet(KEY_DEFEATED,      other.prefs.getStringSet(KEY_DEFEATED, emptySet()))
        edit.putStringSet(KEY_QUESTS_ACTIVE, other.prefs.getStringSet(KEY_QUESTS_ACTIVE, emptySet()))
        edit.putStringSet(KEY_QUESTS_DONE,   other.prefs.getStringSet(KEY_QUESTS_DONE, emptySet()))
        edit.putStringSet(KEY_CHESTS,        other.prefs.getStringSet(KEY_CHESTS, emptySet()))
        edit.putStringSet(KEY_VISITED,       other.prefs.getStringSet(KEY_VISITED, emptySet()))
        edit.apply()
    }

    companion object {
        private const val KEY_MAP_ID = "current_map_id"
        private const val KEY_HERO_X = "hero_x"
        private const val KEY_HERO_Y = "hero_y"
        private const val KEY_HERO_FACING = "hero_facing"
        private const val KEY_PARTY_LEADER = "party_leader"
        private const val KEY_PARTY = "party_json"
        private const val KEY_INVENTORY = "inventory_json"
        private const val KEY_GOLD = "gold"
        private const val KEY_BOSSES = "bosses_defeated"
        private const val KEY_QUESTS_ACTIVE = "quests_active"
        private const val KEY_QUESTS_DONE   = "quests_done"
        private const val KEY_CHESTS        = "chests_opened"
        private const val KEY_CLEARED       = "game_cleared"
        private const val KEY_DEFEATED      = "defeated_enemies"
        private const val KEY_PLAYTIME      = "play_time_ms"
        private const val KEY_TUTORIAL      = "tutorial_shown"
        private const val KEY_VISITED       = "visited_maps"
        private const val KEY_LAST_SAVED_SLOT = "last_saved_slot"

        fun formatPlayTime(ms: Long): String {
            val totalSec = ms / 1000
            val h = totalSec / 3600
            val m = (totalSec / 60) % 60
            val s = totalSec % 60
            return "%02d:%02d:%02d".format(h, m, s)
        }

        /** 어떤 slot 이라도 클리어했는지. */
        fun anySlotCleared(context: Context): Boolean {
            for (i in 0..3) {
                val p = context.getSharedPreferences("hero3_gamestate_slot$i", Context.MODE_PRIVATE)
                if (p.getBoolean(KEY_CLEARED, false)) return true
            }
            return false
        }

        const val FACING_DOWN = 0
        const val FACING_UP = 1
        const val FACING_LEFT = 2
        const val FACING_RIGHT = 3
    }
}
