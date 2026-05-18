# Phase C Step 1 — engine-core 모듈 추출 (2026-05-19)

> **세션**: Phase C 시작, 첫 컨테인 단계
> **이전**: [Hero4 R69](../h4/round69-skill-catalog-and-batch-decrypt.md) 완료, Hero4 Phase A 100% 종결
> **다음**: Phase C Step 2 — GameStateView interface 추출 + Quest/ShopRegistry commonMain 이전

## TL;DR

Hero3 의 `android/app/src/main/java/com/hero3/remake/engine/` 에서 **GameState 의존 없는 12 Kotlin 파일** 을 새 모듈 `engine-core/` 로 추출 (git mv 사용). `:engine-core` Gradle 모듈 신설, `:app` 이 `implementation(project(":engine-core"))` 로 참조. **assembleDebug + unitTest 통과**.

목표: Hero3 안정 상태 유지하면서 향후 Hero4 + KMM commonMain 으로 발전할 수 있는 멀티모듈 토대 마련.

## 변경 사항

### 모듈 구조

```
android/                              ← Hero3 Gradle root (그대로)
├── settings.gradle.kts               ← include(":engine-core") 추가 (../engine-core 경로)
├── build.gradle.kts                  ← kotlin.jvm 2.0.20 plugin 추가
└── app/build.gradle.kts              ← implementation(project(":engine-core")) 추가

engine-core/                          ← NEW (Phase C Step 1)
├── build.gradle.kts                  ← Kotlin/JVM library (JDK 17 target)
└── src/
    ├── main/kotlin/com/hero3/remake/engine/  (12 files)
    │   ├── Character.kt              (149 lines)
    │   ├── ChestRegistry.kt          (31)
    │   ├── EncounterTable.kt         (31)
    │   ├── Enemy.kt                  (63)
    │   ├── EventBus.kt               (16)
    │   ├── InputController.kt        (63)
    │   ├── Item.kt                   (104)
    │   ├── MapGraph.kt               (54)
    │   ├── NpcRegistry.kt            (418)
    │   ├── PartyTurnOrder.kt         (41)
    │   ├── SfxBus.kt                 (31)
    │   └── Skill.kt                  (68)
    └── test/kotlin/com/hero3/remake/engine/
        ├── CharacterTest.kt
        ├── InventoryTest.kt
        ├── PartyTurnOrderTest.kt
        └── SkillTest.kt
```

### 분류 기준

| 분류 | 파일 수 | 위치 |
|---|---|---|
| ✅ Pure Kotlin (engine-core 이전 완료) | 12 | `engine-core/` |
| ⏸ GameState 의존 (Step 2 대기) | 2 | `android/app/.../engine/` (Quest.kt, ShopRegistry.kt) |
| ❌ Android 의존 (`android.graphics.Canvas` 등) | 7 | `android/app/.../engine/` (GameState/GameView/Scene/Settings/Strings/UiKit/VirtualKeypadView) |
| (UI scenes) | 23 | `android/app/.../scene/` |

### 동시 fix

- `NpcDialogueScene.kt:84-92` — cross-module smart cast 해결 (`n?.startsQuestId` 을 local val 로)
- 패키지명 `com.hero3.remake.engine` 그대로 유지 (Step 2 에서 `com.gameremake.engine.core` 로 리네임 예정)

## 빌드 검증

```bash
# Hero3 안드로이드 (engine-core 의존 포함)
cd c:/gameRemake/testrepo/android
JAVA_HOME=".../jdk-21" ./gradlew :engine-core:build :app:assembleDebug :app:testDebugUnitTest
# 결과: BUILD SUCCESSFUL
```

## 다음 단계

### Step 2 — ✅ 완료 (commit `5e511839`, 2026-05-19)

`engine-core/src/main/kotlin/com/hero3/remake/engine/GameStateView.kt` 신설:

```kotlin
interface GameStateView {
    var activeQuestIds: Set<String>
    var doneQuestIds: Set<String>
    var gold: Int
    fun isBossDefeated(id: String): Boolean
    fun saveInventory(inv: Inventory)
}
```

`GameState.kt` 가 implement (5 멤버에 `override` 추가). `Quest.kt` + `ShopRegistry.kt` 의 `GameState` 참조 → `GameStateView`. 두 파일 engine-core 로 이전. `QuestScene.kt` cross-module smart cast 우회.

빌드 검증: `:engine-core:build` (15 main files) + `:app:assembleDebug` + `:app:testDebugUnitTest` 통과.

**현재 engine-core 15 main + 4 test files** (총 ~1,344 lines). 잔류 in android/app: GameState, GameView, Scene, Settings, Strings, UiKit, VirtualKeypadView (7 files).

### Step 2 — (HISTORY) interface 설계 가이드

현재:
```kotlin
// engine/Quest.kt (android/app/...) — GameState 직접 사용
class QuestLog(private val gameState: GameState) {
    fun isActive(id: String) = gameState.activeQuestIds.contains(id)
    fun complete(id: String, reward: QuestReward) {
        gameState.gold += reward.gold
        ...
    }
}
```

목표:
```kotlin
// engine-core: interface 만 노출
interface GameStateView {
    var gold: Int
    val activeQuestIds: MutableSet<String>
    val doneQuestIds: MutableSet<String>
    val defeatedBossIds: Set<String>
    fun isBossDefeated(id: String): Boolean
}

class QuestLog(private val state: GameStateView) { ... }

// android/app: GameState implements GameStateView (declarative)
```

추출할 인터페이스 멤버 (Quest + ShopRegistry 양쪽 union):
- `gold: Int`
- `activeQuestIds: MutableSet<String>`
- `doneQuestIds: MutableSet<String>`
- `isBossDefeated(id: String): Boolean`
- `saveInventory(): Unit`

### Step 3 — ✅ 완료 (commit `4b5e056d`, 2026-05-19)

`engine-core/build.gradle.kts` 를 `org.jetbrains.kotlin.multiplatform` 으로 전환:

```kotlin
plugins {
    id("org.jetbrains.kotlin.multiplatform")
    id("com.android.library")
}
kotlin {
    androidTarget { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }
    jvm()
    sourceSets {
        commonTest { dependencies { implementation(kotlin("test")) } }
    }
}
android {
    namespace = "com.hero3.remake.engine"
    compileSdk = 35
    defaultConfig { minSdk = 24 }
}
```

- `src/main/kotlin` → `src/commonMain/kotlin` (15 main files)
- `src/test/kotlin` → `src/commonTest/kotlin` (4 test files)
- JUnit 4 → kotlin.test 마이그레이션 (signature 호환, 본문 무변경)
- root `android/build.gradle.kts` 에 plugin 등록 (kotlin.multiplatform 2.0.20 + com.android.library 8.7.2)
- expect/actual 필요 없음 (현재 15 main 파일 모두 순수 Kotlin)

빌드 검증: `:engine-core:build` 83 tasks 통과 (androidDebug + androidRelease + jvm 컴파일 + 테스트 모두) + `:app:assembleDebug`.

### Step 3 — (HISTORY) 가이드

### Step 4 — Compose Multiplatform UI

`Scene.kt` / `UiKit.kt` / `GameView.kt` 의 `android.graphics.Canvas` 사용 부분 → `androidx.compose.foundation.Canvas`. 이건 큰 작업 (~1-2 주).

### Step 5 — Hero4 wiring

`apps/hero4-android/app/build.gradle.kts` 도 `implementation(project(":engine-core"))` 추가 (현재는 self-contained Gradle project — 통합 settings.gradle.kts 필요).

`h4_catalog.json` (R69 산출) 을 engine-core 의 데이터 로딩 추상화로 import — Hero3 의 `NpcRegistry` 패턴 따라 `Hero4NpcRegistry` 클래스 작성.

## 의도적으로 미해결로 둔 것

- 패키지 리네임 (`com.hero3.remake.engine` → `com.gameremake.engine.core`): Step 2 에서 GameStateView interface 추출 시 같이
- 멀티 프로젝트 통합 (`android/` + `apps/hero4-android/` 별도 wrapper): Step 4 에서 루트 settings.gradle.kts 신설
- `dependencyResolutionManagement` 의 `FAIL_ON_PROJECT_REPOS`: 현재 그대로
- Hero4 의 `apps/hero4-android/` 는 이 단계에서 변경 없음

## 검증된 사실

- `:engine-core:build` 통과
- `:app:assembleDebug` 통과
- `:app:testDebugUnitTest` 통과
- `:engine-core:test` (junit) 통과 (4 test classes: CharacterTest, InventoryTest, PartyTurnOrderTest, SkillTest)
