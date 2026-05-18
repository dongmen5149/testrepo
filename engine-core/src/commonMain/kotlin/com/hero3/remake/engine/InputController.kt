package com.hero3.remake.engine

/**
 * 피처폰 키패드 매핑 + Android KeyEvent + 가상 터치 키패드를 통합한 입력 컨트롤러.
 *
 * 비트마스크 기반: 매 프레임 [pressedMask]를 폴링하면 됨.
 * 단발 입력은 [pressedOnce]로 잡음 (한 번 true 반환 후 해당 비트 클리어).
 */
class InputController {

    @Volatile private var pressedMask = 0
    @Volatile private var edgeMask = 0   // 이번 프레임에 눌렸다는 신호

    fun setPressed(key: Int, down: Boolean) {
        val bit = 1 shl key
        synchronized(this) {
            if (down) {
                if (pressedMask and bit == 0) edgeMask = edgeMask or bit
                pressedMask = pressedMask or bit
            } else {
                pressedMask = pressedMask and bit.inv()
            }
        }
    }

    /** 폴링용. 현재 눌려 있는 키들의 비트마스크 (연속 입력 가능). */
    fun pressedMask(): Int = pressedMask

    fun isPressed(key: Int): Boolean = pressedMask and (1 shl key) != 0

    /** 단발용. 이번 프레임에 새로 눌렸으면 true 한 번. */
    fun pressedOnce(key: Int): Boolean {
        val bit = 1 shl key
        synchronized(this) {
            val hit = edgeMask and bit != 0
            if (hit) edgeMask = edgeMask and bit.inv()
            return hit
        }
    }

    companion object {
        // MIDP-style 키 인덱스. 비트 위치로 사용.
        const val K_UP = 0
        const val K_DOWN = 1
        const val K_LEFT = 2
        const val K_RIGHT = 3
        const val K_OK = 4         // 중앙 / Fire / Select
        const val K_SOFT1 = 5      // 좌측 소프트 (메뉴/확인)
        const val K_SOFT2 = 6      // 우측 소프트 (취소/뒤로)
        const val K_NUM0 = 7
        const val K_NUM1 = 8
        const val K_NUM2 = 9
        const val K_NUM3 = 10
        const val K_NUM4 = 11
        const val K_NUM5 = 12
        const val K_NUM6 = 13
        const val K_NUM7 = 14
        const val K_NUM8 = 15
        const val K_NUM9 = 16
        const val K_STAR = 17
        const val K_POUND = 18
    }
}
