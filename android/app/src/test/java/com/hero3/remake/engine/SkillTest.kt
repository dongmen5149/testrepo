package com.hero3.remake.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SkillTest {

    @Test fun skillsFilteredByLevel() {
        val lv1 = SkillRegistry.forClass("kei_berserker", level = 1)
        val lv99 = SkillRegistry.forClass("kei_berserker", level = 99)
        assertTrue(lv99.size >= lv1.size)
        assertTrue(lv1.all { it.requiredLevel <= 1 })
    }

    @Test fun bloodFuryRequiresLevel8() {
        val lv7 = SkillRegistry.forClass("kei_berserker", level = 7).map { it.id }
        val lv8 = SkillRegistry.forClass("kei_berserker", level = 8).map { it.id }
        assertTrue("kei_bloodfury" !in lv7)
        assertTrue("kei_bloodfury" in lv8)
    }

    @Test fun unknownClassReturnsEmpty() {
        assertEquals(0, SkillRegistry.forClass("no_such", 99).size)
    }

    @Test fun healSkillsExist() {
        val templarSkills = SkillRegistry.forClass("ritz_templar", 99)
        assertTrue(templarSkills.any { it.heal })
    }
}
