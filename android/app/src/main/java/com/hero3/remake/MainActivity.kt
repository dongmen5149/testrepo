package com.hero3.remake

import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.core.view.WindowCompat
import com.hero3.remake.catalog.Hero3Catalog
import com.hero3.remake.catalog.Hero3CatalogLoader
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.GameView
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.VirtualKeypadView
import com.hero3.remake.platform.AndroidAssetReader
import com.hero3.remake.scene.CatalogViewerScene
import com.hero3.remake.scene.DialogueDemoScene
import com.hero3.remake.scene.EndingScene
import com.hero3.remake.scene.ForgeScene
import com.hero3.remake.scene.EventViewerScene
import com.hero3.remake.scene.InventoryScene
import com.hero3.remake.scene.MainMenuScene
import com.hero3.remake.scene.MapScene
import com.hero3.remake.scene.MapWalkScene
import com.hero3.remake.scene.NpcDialogueScene
import com.hero3.remake.scene.QuestScene
import com.hero3.remake.scene.RecordsScene
import com.hero3.remake.scene.SaveSlotScene
import com.hero3.remake.scene.BattleScene
import com.hero3.remake.scene.BestiaryScene
import com.hero3.remake.scene.SettingsScene
import com.hero3.remake.scene.SkillScene
import com.hero3.remake.scene.TravelScene
import com.hero3.remake.scene.ShopScene
import com.hero3.remake.scene.SpriteGalleryScene
import com.hero3.remake.scene.StatusScene
import com.hero3.remake.scene.TitleScene
import java.util.Locale

class MainActivity : ComponentActivity() {

    private lateinit var settings: Settings
    private lateinit var gameState: GameState
    private lateinit var input: InputController
    private lateinit var gameView: GameView
    private lateinit var keypad: VirtualKeypadView
    private val sceneStack = ArrayDeque<Scene>()

    /** R71 산출물 — game_balance.json v1.1 (582KB) 의 typed Kotlin 표현.
     *  Lazy 로딩 — 첫 사용 시점 (CatalogViewerScene / BestiaryScene boss section 등) 에 한 번만 파싱.
     *  R80: Hero3CatalogProvider 로도 process-scoped 노출 (scene 들이 catalog 인자 없이 접근). */
    val catalog: Hero3Catalog by lazy {
        Hero3CatalogLoader.load(AndroidAssetReader(this)).also {
            com.hero3.remake.catalog.Hero3CatalogProvider.installCatalog(it)
            // R82 — catalog 의 핵심 items 를 ItemRegistry 에 추가 등록.
            // ForgeScene 의 recipe matching / Inventory display 범위 확장.
            com.hero3.remake.engine.ItemRegistry.registerExtra(
                com.hero3.remake.catalog.Hero3CatalogBridge.catalogItemPool(it)
            )
        }
    }

    override fun attachBaseContext(newBase: Context) {
        val s = Settings(newBase)
        super.attachBaseContext(applyLocale(newBase, s.language))
    }

    private fun applyLocale(ctx: Context, lang: String): Context {
        val locale = Locale(lang)
        Locale.setDefault(locale)
        val config = Configuration(ctx.resources.configuration)
        config.setLocale(locale)
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N)
            ctx.createConfigurationContext(config)
        else {
            @Suppress("DEPRECATION")
            ctx.resources.updateConfiguration(config, ctx.resources.displayMetrics)
            ctx
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        settings = Settings(this)
        gameState = GameState(this)
        input = InputController()

        // R82 — catalog lazy 강제 트리거 (provider install + ItemRegistry extra 등록).
        // MapWalkScene 의 encounter 가 카탈로그 161 enemies 사용 가능하도록.
        try { catalog } catch (_: Throwable) { /* asset 미존재 시 등 — graceful */ }

        gameView = GameView(this, input)
        keypad = VirtualKeypadView(this, input)

        // 시작 씬: TitleScene
        pushScene(TitleScene(this, input, settings, this::handleSceneRequest))

        val switchToNext = {
            // # 키: 현재 씬이 consumesPoundKey 면 무시. 그 외에는 데모 씬 전환.
            if (sceneStack.lastOrNull()?.consumesPoundKey != true) {
                handleSceneRequest(SceneRequest.CycleDemoScenes)
            }
        }
        gameView.onPoundKey = switchToNext
        keypad.onPoundKey = switchToNext

        val root = FrameLayout(this).apply {
            addView(gameView, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ))
            addView(keypad, FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ))
        }
        setContentView(root)
    }

    /** Scene 들이 다음 화면 요청을 발행. */
    sealed class SceneRequest {
        data object MainMenu : SceneRequest()
        data object MapWalk : SceneRequest()
        data object NewGame : SceneRequest()
        data object Status : SceneRequest()
        data object Inventory : SceneRequest()
        data object Equipment : SceneRequest()
        data object DialogueDemo : SceneRequest()
        data object SpriteGallery : SceneRequest()
        data object MapGallery : SceneRequest()
        data object SettingsScene : SceneRequest()
        data object SaveSlots : SceneRequest()
        data object Quests : SceneRequest()
        data object Skills : SceneRequest()
        data object Bestiary : SceneRequest()
        data object Records : SceneRequest()
        data object EventViewer : SceneRequest()
        data object CatalogViewer : SceneRequest()
        data object Forge : SceneRequest()  // R81 — 단조 (forge recipes)
        data object Travel : SceneRequest()
        data class NpcDialogue(val npcId: String) : SceneRequest()
        data class Shop(val npcId: String) : SceneRequest()
        data class HealParty(val cost: Int) : SceneRequest()
        data object Battle : SceneRequest()
        data class BattleEnemy(val enemyId: String) : SceneRequest()
        data object Title : SceneRequest()
        data object Ending : SceneRequest()
        data object CreditsView : SceneRequest()
        data object Pop : SceneRequest()
        data object CycleDemoScenes : SceneRequest()
    }

    private var demoCycleIdx = 0

    private fun handleSceneRequest(req: SceneRequest) {
        // ctx/cb 는 매 분기마다 반복되던 (this, ::handleSceneRequest) 단축.
        val ctx = this
        val cb = ::handleSceneRequest
        when (req) {
            SceneRequest.MainMenu     -> pushScene(MainMenuScene(ctx, input, settings, cb))
            SceneRequest.MapWalk      -> pushScene(MapWalkScene(ctx, input, settings, gameState, cb))
            SceneRequest.Status       -> pushScene(StatusScene(ctx, input, settings, gameState, cb))
            SceneRequest.Inventory    -> pushScene(InventoryScene(ctx, input, settings, gameState, cb))
            SceneRequest.Equipment    -> pushScene(InventoryScene(ctx, input, settings, gameState, cb, startTab = 1))
            SceneRequest.DialogueDemo -> pushScene(DialogueDemoScene(ctx, input, settings, cb))
            SceneRequest.SpriteGallery -> pushScene(SpriteGalleryScene(assets, input, settings))
            SceneRequest.MapGallery   -> pushScene(MapScene(assets, input))
            SceneRequest.SettingsScene -> pushScene(SettingsScene(ctx, input, settings, gameState, cb))
            SceneRequest.SaveSlots    -> pushScene(SaveSlotScene(ctx, input, gameState, cb))
            SceneRequest.Quests       -> pushScene(QuestScene(ctx, input, settings, gameState, cb))
            SceneRequest.Skills       -> pushScene(SkillScene(ctx, input, settings, gameState, cb))
            SceneRequest.Bestiary     -> pushScene(BestiaryScene(ctx, input, settings, gameState, cb))
            SceneRequest.Records      -> pushScene(RecordsScene(ctx, input, settings, gameState, cb))
            SceneRequest.EventViewer  -> pushScene(EventViewerScene(ctx, input, cb))
            SceneRequest.CatalogViewer -> pushScene(CatalogViewerScene(ctx, input, settings, catalog, cb))
            SceneRequest.Forge        -> pushScene(ForgeScene(ctx, input, settings, gameState, cb))
            SceneRequest.Travel       -> pushScene(TravelScene(ctx, input, settings, gameState, cb))
            SceneRequest.Battle       -> pushScene(BattleScene(ctx, input, settings, gameState, cb))
            is SceneRequest.NpcDialogue -> pushScene(NpcDialogueScene(ctx, input, settings, gameState, req.npcId, cb))
            is SceneRequest.Shop      -> pushScene(ShopScene(ctx, input, settings, gameState, req.npcId, cb))
            is SceneRequest.BattleEnemy -> pushScene(BattleScene(ctx, input, settings, gameState, cb, forcedEnemyId = req.enemyId))
            SceneRequest.CreditsView  -> pushScene(EndingScene(ctx, input, settings, gameState, cb, markCleared = false))

            SceneRequest.NewGame -> {
                // 클리어 플래그는 슬롯에 종속되지 않도록 보존 (전회차 클리어 → ★ 유지)
                val prevCleared = gameState.gameCleared
                gameState.clear()
                if (prevCleared) gameState.gameCleared = true
                gameState.resetPosition(0, 17, 12)
                sceneStack.clear()
                pushScene(MapWalkScene(ctx, input, settings, gameState, cb))
            }
            SceneRequest.Title -> {
                sceneStack.clear()
                pushScene(TitleScene(ctx, input, settings, cb))
            }
            SceneRequest.Ending -> {
                sceneStack.clear()
                pushScene(EndingScene(ctx, input, settings, gameState, cb, markCleared = true))
            }
            SceneRequest.Pop -> popScene()
            SceneRequest.CycleDemoScenes -> {
                demoCycleIdx = (demoCycleIdx + 1) % DEMO_CYCLE.size
                handleSceneRequest(DEMO_CYCLE[demoCycleIdx])
            }
            is SceneRequest.HealParty -> healParty(req.cost)
        }
    }

    private fun healParty(cost: Int) {
        val msg = if (gameState.gold >= cost) {
            gameState.gold -= cost
            val party = gameState.loadParty().map { it.copy(hp = it.hpMax, sp = it.spMax) }
            gameState.saveParty(party)
            settings.lang("휴식. -${cost}G", "Rested. -${cost}G")
        } else {
            settings.lang("골드 부족.", "Not enough gold.")
        }
        com.hero3.remake.engine.EventBus.push(msg)
    }

    private fun pushScene(scene: Scene) {
        sceneStack.addLast(scene)
        gameView.scene = scene
    }

    private fun popScene() {
        if (sceneStack.size > 1) {
            sceneStack.removeLast()
            gameView.scene = sceneStack.last()
        } else {
            finish()
        }
    }

    companion object {
        private val DEMO_CYCLE = listOf(
            SceneRequest.SpriteGallery,
            SceneRequest.MapGallery,
            SceneRequest.Title,
        )
    }
}
