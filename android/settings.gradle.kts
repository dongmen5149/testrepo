pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Hero3Remake"
include(":app")

// Phase C Step 1 (2026-05-19): shared engine module at repo root.
// 14 pure Kotlin engine files (Character/Enemy/Skill/Quest/etc.) extracted from app.
// Future steps: Hero4 wiring + KMM commonMain + Compose Multiplatform.
include(":engine-core")
project(":engine-core").projectDir = file("../engine-core")
