package com.hero3.remake.engine

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.KeyEvent
import android.view.SurfaceHolder
import android.view.SurfaceView

/**
 * 240×320 가상 캔버스를 letterbox 스케일로 디바이스 화면에 그리는 SurfaceView.
 * 별도 렌더 스레드에서 [Scene.render]를 호출.
 *
 * 하드웨어 키 이벤트도 여기서 받아 [InputController]로 전달.
 */
class GameView(context: Context, private val input: InputController) :
    SurfaceView(context), SurfaceHolder.Callback {

    var scene: Scene? = null
    var onPoundKey: (() -> Unit)? = null

    private var renderThread: RenderThread? = null
    private val backgroundPaint = Paint().apply { color = Color.BLACK }

    init {
        holder.addCallback(this)
        isFocusable = true
        isFocusableInTouchMode = true
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        renderThread = RenderThread(holder).also { it.start() }
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        renderThread?.viewportSize(width, height)
    }

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        renderThread?.shutdown()
        renderThread = null
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_POUND) {
            onPoundKey?.invoke()
            input.setPressed(InputController.K_POUND, true)
            return true
        }
        return mapKey(keyCode)?.let {
            input.setPressed(it, true); true
        } ?: super.onKeyDown(keyCode, event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        return mapKey(keyCode)?.let {
            input.setPressed(it, false); true
        } ?: super.onKeyUp(keyCode, event)
    }

    private fun mapKey(keyCode: Int): Int? = when (keyCode) {
        KeyEvent.KEYCODE_DPAD_UP -> InputController.K_UP
        KeyEvent.KEYCODE_DPAD_DOWN -> InputController.K_DOWN
        KeyEvent.KEYCODE_DPAD_LEFT -> InputController.K_LEFT
        KeyEvent.KEYCODE_DPAD_RIGHT -> InputController.K_RIGHT
        KeyEvent.KEYCODE_DPAD_CENTER, KeyEvent.KEYCODE_ENTER -> InputController.K_OK
        KeyEvent.KEYCODE_BACK -> InputController.K_SOFT2
        KeyEvent.KEYCODE_MENU -> InputController.K_SOFT1
        KeyEvent.KEYCODE_0 -> InputController.K_NUM0
        KeyEvent.KEYCODE_1 -> InputController.K_NUM1
        KeyEvent.KEYCODE_2 -> InputController.K_NUM2
        KeyEvent.KEYCODE_3 -> InputController.K_NUM3
        KeyEvent.KEYCODE_4 -> InputController.K_NUM4
        KeyEvent.KEYCODE_5 -> InputController.K_NUM5
        KeyEvent.KEYCODE_6 -> InputController.K_NUM6
        KeyEvent.KEYCODE_7 -> InputController.K_NUM7
        KeyEvent.KEYCODE_8 -> InputController.K_NUM8
        KeyEvent.KEYCODE_9 -> InputController.K_NUM9
        KeyEvent.KEYCODE_STAR -> InputController.K_STAR
        KeyEvent.KEYCODE_POUND -> InputController.K_POUND
        else -> null
    }

    private inner class RenderThread(private val surfaceHolder: SurfaceHolder) : Thread("Hero3-Render") {
        @Volatile private var running = true
        @Volatile private var viewportWidth = 1
        @Volatile private var viewportHeight = 1

        fun viewportSize(w: Int, h: Int) { viewportWidth = w; viewportHeight = h }

        fun shutdown() {
            running = false
            try { join(200) } catch (_: InterruptedException) {}
        }

        override fun run() {
            var lastNanos = System.nanoTime()
            while (running) {
                val now = System.nanoTime()
                val deltaMs = (now - lastNanos) / 1_000_000L
                lastNanos = now

                val s = scene
                s?.update(deltaMs)

                val canvas: Canvas? = try { surfaceHolder.lockCanvas() } catch (_: IllegalStateException) { null }
                if (canvas != null) {
                    try {
                        canvas.drawRect(0f, 0f, viewportWidth.toFloat(), viewportHeight.toFloat(), backgroundPaint)
                        if (s != null) {
                            applyLetterbox(canvas, s.virtualWidth, s.virtualHeight)
                            s.render(canvas)
                            canvas.restore()
                        }
                    } finally {
                        try { surfaceHolder.unlockCanvasAndPost(canvas) } catch (_: IllegalStateException) {}
                    }
                }

                // 60Hz cap
                val frameMs = (System.nanoTime() - now) / 1_000_000L
                val sleep = 16L - frameMs
                if (sleep > 0) try { sleep(sleep) } catch (_: InterruptedException) {}
            }
        }

        private fun applyLetterbox(canvas: Canvas, vw: Int, vh: Int) {
            canvas.save()
            val scale = minOf(viewportWidth.toFloat() / vw, viewportHeight.toFloat() / vh)
            val tx = (viewportWidth - vw * scale) / 2f
            val ty = (viewportHeight - vh * scale) / 2f
            canvas.translate(tx, ty)
            canvas.scale(scale, scale)
        }
    }
}
