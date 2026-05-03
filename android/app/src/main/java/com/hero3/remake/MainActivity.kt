package com.hero3.remake

import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.core.view.WindowCompat
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.GameView
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.VirtualKeypadView
import com.hero3.remake.scene.DialogueDemoScene
import com.hero3.remake.scene.EndingScene
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
        when (req) {
            SceneRequest.MainMenu -> pushScene(MainMenuScene(this, input, settings, this::handleSceneRequest))
            SceneRequest.MapWalk -> pushScene(MapWalkScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.NewGame -> {
                // 클리어 플래그는 슬롯에 종속되지 않도록 보존 (전회차 클리어 → ★ 유지)
                val prevCleared = gameState.gameCleared
                gameState.clear()
                if (prevCleared) gameState.gameCleared = true
                gameState.resetPosition(0, 17, 12)
                sceneStack.clear()
                pushScene(MapWalkScene(this, input, settings, gameState, this::handleSceneRequest))
            }
            SceneRequest.Status -> pushScene(StatusScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.Inventory -> pushScene(InventoryScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.Equipment -> pushScene(InventoryScene(this, input, settings, gameState, this::handleSceneRequest, startTab = 1))
            SceneRequest.DialogueDemo -> pushScene(DialogueDemoScene(this, input, settings, this::handleSceneRequest))
            SceneRequest.SpriteGallery -> pushScene(SpriteGalleryScene(assets, input, settings))
            SceneRequest.MapGallery -> pushScene(MapScene(assets, input))
            SceneRequest.SettingsScene -> pushScene(SettingsScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.SaveSlots -> pushScene(SaveSlotScene(this, input, gameState, this::handleSceneRequest))
            SceneRequest.Quests -> pushScene(QuestScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.Skills -> pushScene(SkillScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.Bestiary -> pushScene(BestiaryScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.Records -> pushScene(RecordsScene(this, input, settings, gameState, this::handleSceneRequest))
            SceneRequest.EventViewer -> pushScene(EventViewerScene(this, input, this::handleSceneRequest))
            SceneRequest.Travel -> pushScene(TravelScene(this, input, settings, gameState, this::handleSceneRequest))
            is SceneRequest.NpcDialogue -> pushScene(NpcDialogueScene(this, input, settings, gameState, req.npcId, this::handleSceneRequest))
            is SceneRequest.Shop -> pushScene(ShopScene(this, input, settings, gameState, req.npcId, this::handleSceneRequest))
            is SceneRequest.HealParty -> {
                if (gameState.gold >= req.cost) {
                    gameState.gold -= req.cost
                    val party = gameState.loadParty().map { it.copy(hp = it.hpMax, sp = it.spMax) }
                    gameState.saveParty(party)
                    com.hero3.remake.engine.EventBus.push(
                        if (settings.language == "en") "Rested. -${req.cost}G"
                        else "휴식. -${req.cost}G")
                } else {
                    com.hero3.remake.engine.EventBus.push(
                        if (settings.language == "en") "Not enough gold."
                        else "골드 부족.")
                }
            }
            SceneRequest.Battle -> pushScene(BattleScene(this, input, settings, gameState, this::handleSceneRequest))
            is SceneRequest.BattleEnemy -> pushScene(BattleScene(this, input, settings, gameState, this::handleSceneRequest, forcedEnemyId = req.enemyId))
            SceneRequest.Title -> {
                sceneStack.clear()
                pushScene(TitleScene(this, input, settings, this::handleSceneRequest))
            }
            SceneRequest.Ending -> {
                sceneStack.clear()
                pushScene(EndingScene(this, input, settings, gameState, this::handleSceneRequest, markCleared = true))
            }
            SceneRequest.CreditsView -> pushScene(EndingScene(this, input, settings, gameState, this::handleSceneRequest, markCleared = false))
            SceneRequest.Pop -> {
                if (sceneStack.size > 1) {
                    sceneStack.removeLast()
                    gameView.scene = sceneStack.last()
                } else {
                    finish()
                }
            }
            SceneRequest.CycleDemoScenes -> {
                val cycle = listOf(
                    SceneRequest.SpriteGallery,
                    SceneRequest.MapGallery,
                    SceneRequest.Title,
                )
                demoCycleIdx = (demoCycleIdx + 1) % cycle.size
                handleSceneRequest(cycle[demoCycleIdx])
            }
        }
    }

    private fun pushScene(scene: Scene) {
        sceneStack.addLast(scene)
        gameView.scene = scene
    }
}
