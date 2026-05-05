package com.hero4.remake

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

/**
 * Hero4 Android 진입점 — Phase 3 (KMM 공유 엔진 분리) 대기 중인 placeholder.
 *
 * Phase 3 작업:
 *   - Hero3 의 android/app/src/main/java/com/hero3/remake/engine/* 를 commonMain 모듈로 분리
 *   - 이 Activity 가 commonMain 의 GameView/Scene 시스템을 마운트
 *   - Hero4 게임 콘텐츠 (Hero4 자산을 읽는 Scene 들) wiring
 *
 * 자산은 이미 src/main/assets/ 에 prepare_android_assets.py 로 배포되어 있음.
 */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
        }
        layout.addView(TextView(this).apply {
            text = "영웅서기4 - 환영의검\nRemake (Hero4)\n\nPhase 3 통합 대기 중"
            setTextColor(Color.WHITE)
            textSize = 18f
            gravity = Gravity.CENTER
        })
        setContentView(layout)
    }
}
