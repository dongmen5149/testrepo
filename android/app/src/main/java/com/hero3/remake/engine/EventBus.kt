package com.hero3.remake.engine

/**
 * 매우 단순한 토스트/이벤트 큐.
 * 씬 간 일회성 알림 전달 — 레벨업, 퀘스트 완료, 보스 처치 등.
 */
object EventBus {
    private val queue = ArrayDeque<String>()

    fun push(message: String) {
        queue.addLast(message)
        while (queue.size > 8) queue.removeFirst()
    }

    fun pop(): String? = if (queue.isEmpty()) null else queue.removeFirst()
}
