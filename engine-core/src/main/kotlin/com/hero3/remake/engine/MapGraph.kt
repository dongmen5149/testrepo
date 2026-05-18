package com.hero3.remake.engine

/**
 * 맵 간 연결 — `_mp` extras 의 출구 데이터가 미해독이라 임시 수동 정의.
 *
 * Ghidra 후 `tools/converter/convert_mp.py` 가 extras 를 파싱하면
 * 자동 생성으로 교체.
 *
 * 방향:
 *   N = up edge (y == 0)
 *   S = down edge (y == h-1)
 *   W = left edge (x == 0)
 *   E = right edge (x == w-1)
 */
object MapGraph {

    enum class Side { N, S, W, E }

    data class Edge(val from: Int, val side: Side, val to: Int)

    private val edges: List<Edge> = listOf(
        // map0 (NEOSOLTIA) ↔ map1 — placeholder until extras 디코드
        Edge(0, Side.E, 1),
        Edge(1, Side.W, 0),
        Edge(0, Side.S, 10),
        Edge(10, Side.N, 0),
        // 가디언 동굴 → 혼돈의 영역 (map11)
        Edge(10, Side.S, 11),
        Edge(11, Side.N, 10),
        // 혼돈 → 봉인의 사원 (map12, 동쪽 더 깊이)
        Edge(11, Side.E, 12),
        Edge(12, Side.W, 11),
    )

    fun neighborOf(mapId: Int, side: Side): Int? =
        edges.firstOrNull { it.from == mapId && it.side == side }?.to

    /** dx,dy 에 의해 맵 밖으로 나가는 방향을 Side 로 변환. */
    fun sideOf(dx: Int, dy: Int): Side? = when {
        dy < 0 -> Side.N
        dy > 0 -> Side.S
        dx < 0 -> Side.W
        dx > 0 -> Side.E
        else -> null
    }

    /** 반대편 진입 좌표 — 새 맵의 어느 위치에 영웅을 둘지. */
    fun entryPoint(side: Side, fromX: Int, fromY: Int, newW: Int, newH: Int): Pair<Int, Int> = when (side) {
        Side.N -> fromX.coerceIn(0, newW - 1) to (newH - 1)   // 북쪽으로 나갔으니 새 맵의 남쪽으로 진입
        Side.S -> fromX.coerceIn(0, newW - 1) to 0
        Side.W -> (newW - 1) to fromY.coerceIn(0, newH - 1)
        Side.E -> 0 to fromY.coerceIn(0, newH - 1)
    }
}
