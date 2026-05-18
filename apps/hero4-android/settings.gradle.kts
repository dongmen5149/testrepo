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

rootProject.name = "Hero4Remake"
include(":app")

// Phase C Step 5 (2026-05-19): shared engine module at repo root.
// Hero3 (android/) 도 동일 모듈 참조. KMM (Android AAR + JVM JAR target).
include(":engine-core")
project(":engine-core").projectDir = file("../../engine-core")
