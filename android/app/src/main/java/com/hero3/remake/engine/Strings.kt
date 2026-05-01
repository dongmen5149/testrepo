package com.hero3.remake.engine

import android.content.Context
import org.json.JSONObject

/**
 * 단순 i18n 헬퍼.
 *
 * 우선순위:
 *   1. R.string 리소스 (res/values{,-ko}/strings.xml) — Android 시스템이 알아서 처리
 *   2. assets/strings/InGame_txt.json (한국어 원본) — 폴백
 *
 * Settings.language 가 "en" 이면 시스템 locale 을 무시하고 영어로 강제 (Configuration override).
 */
object Strings {

    fun get(context: Context, resId: Int): String = context.getString(resId)

    /**
     * InGame_txt 인덱스 → 문자열.
     * 영어/한국어 자동 (Configuration locale 기반). string resource 우선.
     */
    fun ingameTxt(context: Context, index: Int): String {
        val resName = "txt_%03d".format(index)
        val resId = context.resources.getIdentifier(resName, "string", context.packageName)
        return if (resId != 0) context.getString(resId) else "[?$index]"
    }
}
