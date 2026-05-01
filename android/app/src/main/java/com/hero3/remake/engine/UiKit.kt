package com.hero3.remake.engine

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF

/**
 * 240×320 가상 캔버스 위에서 자주 쓰는 UI 그리기 도우미.
 * 픽셀 레트로 느낌을 살리기 위해 기본 폰트는 antialiasing 끔.
 */
object UiKit {

    val title: Paint = Paint().apply {
        color = Color.WHITE
        textSize = 14f
        isFakeBoldText = true
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }
    val body: Paint = Paint().apply {
        color = Color.WHITE
        textSize = 11f
    }
    val muted: Paint = Paint().apply {
        color = Color.rgb(180, 180, 200)
        textSize = 10f
    }
    val accent: Paint = Paint().apply {
        color = Color.rgb(255, 220, 90)
        textSize = 11f
        isFakeBoldText = true
    }

    private val boxFill = Paint().apply { color = Color.argb(200, 20, 20, 30) }
    private val boxBorder = Paint().apply {
        color = Color.rgb(180, 180, 220)
        style = Paint.Style.STROKE
        strokeWidth = 1f
    }
    private val highlightFill = Paint().apply { color = Color.argb(120, 255, 220, 90) }

    /** 모서리가 둥근 UI 박스. */
    fun drawBox(canvas: Canvas, x: Float, y: Float, w: Float, h: Float, radius: Float = 4f) {
        val r = RectF(x, y, x + w, y + h)
        canvas.drawRoundRect(r, radius, radius, boxFill)
        canvas.drawRoundRect(r, radius, radius, boxBorder)
    }

    /** 메뉴 항목 — 선택된 항목은 highlight. */
    fun drawMenuItem(canvas: Canvas, x: Float, y: Float, w: Float, h: Float,
                     label: String, selected: Boolean) {
        val r = RectF(x, y, x + w, y + h)
        if (selected) canvas.drawRoundRect(r, 3f, 3f, highlightFill)
        val paint = if (selected) accent else body
        canvas.drawText(label, x + 4f, y + h - 4f, paint)
    }

    /** 화면 하단의 hint 라인. */
    fun drawHints(canvas: Canvas, virtualWidth: Int, virtualHeight: Int, hint: String) {
        canvas.drawText(hint, 4f, virtualHeight - 4f, muted)
    }

    /** 화면 상단의 타이틀 라인. */
    fun drawHeader(canvas: Canvas, virtualWidth: Int, title: String, subtitle: String? = null) {
        canvas.drawText(title, 4f, 14f, this.title)
        if (subtitle != null) canvas.drawText(subtitle, 4f, 26f, muted)
    }

    /** 클래식 RPG 스타일 다이얼로그 박스 (하단). */
    fun drawDialogueBox(canvas: Canvas, virtualWidth: Int, virtualHeight: Int,
                        speaker: String?, lines: List<String>) {
        val boxH = 88f
        val y = virtualHeight - boxH - 4f
        drawBox(canvas, 4f, y, virtualWidth - 8f, boxH, radius = 6f)

        var ty = y + 14f
        if (!speaker.isNullOrEmpty()) {
            canvas.drawText(speaker, 10f, ty, accent)
            ty += 14f
        }
        for (line in lines.take(4)) {
            canvas.drawText(line, 10f, ty, body)
            ty += 14f
        }
    }
}
