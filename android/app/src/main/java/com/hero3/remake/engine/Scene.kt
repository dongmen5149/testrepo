package com.hero3.remake.engine

import android.graphics.Canvas

/**
 * 장면 추상화. 가상 240×320 캔버스에 직접 그림.
 * GameView의 렌더 루프가 [update]/[render]를 매 프레임 호출.
 */
interface Scene {

    /** 가상 캔버스 폭/높이. 원본 피처폰과 동일. */
    val virtualWidth: Int get() = 240
    val virtualHeight: Int get() = 320

    /** true 면 # 키를 씬 내부에서 처리(데모 씬 전환 비활성화). */
    val consumesPoundKey: Boolean get() = false

    fun update(deltaMs: Long)

    /** [canvas]는 이미 가상 좌표계로 스케일·평행이동되어 있음. (0,0)–(240,320)에 그리면 됨. */
    fun render(canvas: Canvas)
}
