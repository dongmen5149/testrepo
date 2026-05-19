package com.hero3.remake.catalog

/**
 * Hero3Catalog 의 process-scoped lazy holder.
 *
 * MainActivity가 시작 시 [install] 호출 → scene/registry 들이 [get] / [require] 로 접근.
 * 테스트 환경에서는 [installCatalog] 로 직접 주입 가능.
 *
 * 설계 의도 (R80): scene 의 constructor 에 Hero3Catalog 를 매번 통과시키지 않고
 * 전역 lazy 접근을 제공하여 BattleScene/ShopScene 등의 기존 시그니처 보존.
 */
object Hero3CatalogProvider {
    @Volatile private var instance: Hero3Catalog? = null

    /** MainActivity 가 onCreate 에서 호출. lazy provider 등록. */
    fun install(loader: () -> Hero3Catalog) {
        if (instance == null) {
            synchronized(this) {
                if (instance == null) {
                    instance = loader()
                }
            }
        }
    }

    /** Test 환경 등에서 직접 catalog 주입. */
    fun installCatalog(catalog: Hero3Catalog) {
        instance = catalog
    }

    /** Provider 에 catalog 가 설치돼 있으면 반환, 아니면 null. */
    fun get(): Hero3Catalog? = instance

    /** catalog 가 반드시 있어야 하는 경로에서 호출. */
    fun require(): Hero3Catalog =
        instance ?: error("Hero3CatalogProvider not installed — call install() in MainActivity.onCreate")

    /** 테스트 정리용. */
    fun reset() { instance = null }
}
