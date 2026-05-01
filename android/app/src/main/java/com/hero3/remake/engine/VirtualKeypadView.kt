package com.hero3.remake.engine

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.view.MotionEvent
import android.view.View

/**
 * 화면 위에 떠 있는 가상 키패드. D-pad + OK + Soft1/Soft2 만 우선 제공.
 * 각 버튼은 [InputController]에 적절한 K_* 비트를 기록.
 */
class VirtualKeypadView(context: Context, private val input: InputController) : View(context) {

    var onPoundKey: (() -> Unit)? = null


    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(140, 255, 255, 255) }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textAlign = Paint.Align.CENTER
        textSize = 36f
        isFakeBoldText = true
    }

    private data class Button(val key: Int, val label: String, val rect: RectF, var pointerId: Int = -1)

    private var buttons: List<Button> = emptyList()

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        val r = minOf(w, h) / 9f       // 단일 버튼 반경
        val padX = w * 0.06f
        val padY = h - r * 4f - h * 0.06f      // 하단 여백
        val cx = padX + r * 1.6f
        val cy = padY + r * 1.6f
        val s = r * 1.4f                        // 간격
        val size = r * 1.2f                     // 버튼 크기

        fun rect(x: Float, y: Float) = RectF(x - size / 2, y - size / 2, x + size / 2, y + size / 2)

        val dpadUp     = Button(InputController.K_UP,    "▲", rect(cx,     cy - s))
        val dpadDown   = Button(InputController.K_DOWN,  "▼", rect(cx,     cy + s))
        val dpadLeft   = Button(InputController.K_LEFT,  "◀", rect(cx - s, cy))
        val dpadRight  = Button(InputController.K_RIGHT, "▶", rect(cx + s, cy))
        val ok         = Button(InputController.K_OK,    "OK", rect(cx, cy))

        // 우측에 Soft1 / Soft2
        val rcx = w - padX - r * 1.4f
        val rcy = cy
        val soft1 = Button(InputController.K_SOFT1, "L", rect(rcx, rcy - s))
        val soft2 = Button(InputController.K_SOFT2, "R", rect(rcx, rcy + s))
        // 씬 전환용 # 버튼
        val pound = Button(InputController.K_POUND, "#", rect(rcx + s, rcy))

        buttons = listOf(dpadUp, dpadDown, dpadLeft, dpadRight, ok, soft1, soft2, pound)
    }

    override fun onDraw(canvas: Canvas) {
        for (b in buttons) {
            paint.alpha = if (b.pointerId >= 0) 220 else 100
            canvas.drawRoundRect(b.rect, 12f, 12f, paint)
            canvas.drawText(b.label, b.rect.centerX(), b.rect.centerY() + 12f, labelPaint)
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_POINTER_DOWN -> {
                val idx = event.actionIndex
                val pid = event.getPointerId(idx)
                hitTest(event.getX(idx), event.getY(idx))?.let {
                    it.pointerId = pid
                    input.setPressed(it.key, true)
                    if (it.key == InputController.K_POUND) onPoundKey?.invoke()
                }
                invalidate()
            }
            MotionEvent.ACTION_MOVE -> {
                for (i in 0 until event.pointerCount) {
                    val pid = event.getPointerId(i)
                    val nowHit = hitTest(event.getX(i), event.getY(i))
                    val prev = buttons.firstOrNull { it.pointerId == pid }
                    if (prev != null && prev != nowHit) {
                        prev.pointerId = -1
                        input.setPressed(prev.key, false)
                    }
                    if (nowHit != null && nowHit.pointerId == -1) {
                        nowHit.pointerId = pid
                        input.setPressed(nowHit.key, true)
                    }
                }
                invalidate()
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_POINTER_UP, MotionEvent.ACTION_CANCEL -> {
                val idx = event.actionIndex
                val pid = event.getPointerId(idx)
                buttons.firstOrNull { it.pointerId == pid }?.let {
                    it.pointerId = -1
                    input.setPressed(it.key, false)
                }
                invalidate()
            }
        }
        return true
    }

    private fun hitTest(x: Float, y: Float): Button? = buttons.firstOrNull { it.rect.contains(x, y) }
}
