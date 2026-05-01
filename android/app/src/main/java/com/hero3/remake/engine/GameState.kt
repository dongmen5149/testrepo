package com.hero3.remake.engine

import android.content.Context
import android.content.SharedPreferences
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

    fun copyFrom(other: GameState) {
        prefs.edit()
            .putInt(KEY_MAP_ID, other.currentMapId)
            .putInt(KEY_HERO_X, other.heroX)
            .putInt(KEY_HERO_Y, other.heroY)
            .putInt(KEY_HERO_FACING, other.heroFacing)
            .putInt(KEY_PARTY_LEADER, other.partyLeader)
            .apply()
    }

    companion object {
        private const val KEY_MAP_ID = "current_map_id"
        private const val KEY_HERO_X = "hero_x"
        private const val KEY_HERO_Y = "hero_y"
        private const val KEY_HERO_FACING = "hero_facing"
        private const val KEY_PARTY_LEADER = "party_leader"

        const val FACING_DOWN = 0
        const val FACING_UP = 1
        const val FACING_LEFT = 2
        const val FACING_RIGHT = 3
    }
}
