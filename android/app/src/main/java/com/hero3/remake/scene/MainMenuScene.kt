package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 메인 메뉴 — 원본 게임의 6개 메뉴 항목 + 디버그/설정.
 *
 *   상태보기 (STATUS)    → StatusScene
 *   가방   (INVENTORY)   → InventoryScene
 *   장비   (EQUIPMENT)   → InventoryScene (탭 분리 예정)
 *   스킬   (SKILL)
 *   퀘스트  (QUEST)
 *   시스템  (SYSTEM)     → SettingsScene
 *
 *   [디버그] 스프라이트 갤러리 / 맵 갤러리 / 대화 데모
 */
class MainMenuScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class MenuItem(
        val labelResId: Int,
        val request: MainActivity.SceneRequest,
        val isDebug: Boolean = false,
    )

    private val items = listOf(
        // res/values 의 txt_NNN 키 사용
        MenuItem(R.string.txt_007, MainActivity.SceneRequest.Status),       // 상태보기
        MenuItem(R.string.txt_008, MainActivity.SceneRequest.Inventory),    // 가방
        MenuItem(R.string.txt_009, MainActivity.SceneRequest.Inventory),    // 장비
        MenuItem(R.string.txt_010, MainActivity.SceneRequest.Status),       // 스킬 (placeholder)
        MenuItem(R.string.txt_011, MainActivity.SceneRequest.Status),       // 퀘스트 (placeholder)
        MenuItem(R.string.txt_013, MainActivity.SceneRequest.SaveSlots),    // 세이브
        MenuItem(R.string.txt_012, MainActivity.SceneRequest.SettingsScene),// 시스템 → Settings
        MenuItem(R.string.scene_dialogue_demo, MainActivity.SceneRequest.DialogueDemo, isDebug = true),
        MenuItem(R.string.scene_sprite_gallery, MainActivity.SceneRequest.SpriteGallery, isDebug = true),
        MenuItem(R.string.scene_map_gallery, MainActivity.SceneRequest.MapGallery, isDebug = true),
    )

    private var selected = 0

    private val bgPaint = Paint().apply { color = Color.rgb(20, 20, 35) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_UP))   { selected = (selected - 1 + items.size) % items.size }
        if (input.pressedOnce(InputController.K_DOWN)) { selected = (selected + 1) % items.size }
        if (input.pressedOnce(InputController.K_OK))   { onRequest(items[selected].request) }
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bgPaint)
        UiKit.drawHeader(canvas, virtualWidth,
            context.getString(R.string.scene_main_menu),
            context.getString(R.string.main_title))

        val itemH = 22f
        val totalH = items.size * itemH
        val startY = (virtualHeight - totalH) / 2f - 10f
        for ((i, item) in items.withIndex()) {
            val y = startY + i * itemH
            val label = context.getString(item.labelResId) + if (item.isDebug) " [debug]" else ""
            UiKit.drawMenuItem(canvas, 20f, y, virtualWidth - 40f, itemH - 2f, label, i == selected)
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            context.getString(R.string.hint_dpad_navigate) + "  " +
            context.getString(R.string.hint_ok_select) + "  " +
            context.getString(R.string.hint_back_cancel))
    }
}
