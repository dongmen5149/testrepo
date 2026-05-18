package com.hero3.remake.engine

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class CharacterTest {

    @Test fun newCharacterHasFullHpSp() {
        val c = CharacterRegistry.newCharacter("kei", "kei_berserker")
        assertEquals(c.hpMax, c.hp)
        assertEquals(c.spMax, c.sp)
        assertEquals(1, c.level)
        assertEquals(0, c.exp)
    }

    @Test fun gainExpReturnsLevelsGained() {
        val c = CharacterRegistry.newCharacter("kei", "kei_berserker")
        // Lv1→2 needs 1*1*20 = 20 exp
        val gained = c.gainExp(20)
        assertEquals(1, gained)
        assertEquals(2, c.level)
    }

    @Test fun gainExpFullHealsOnLevelUp() {
        val c = CharacterRegistry.newCharacter("kei", "kei_berserker")
        c.hp = 1
        c.sp = 0
        c.gainExp(20)
        assertEquals(c.hpMax, c.hp)
        assertEquals(c.spMax, c.sp)
    }

    @Test fun multiLevelUpAccumulates() {
        val c = CharacterRegistry.newCharacter("kei", "kei_berserker")
        // Lv1→2 = 20, Lv2→3 = 80, total 100 → 2 levels at 100 exp
        val gained = c.gainExp(100)
        assertEquals(2, gained)
        assertEquals(3, c.level)
    }

    @Test fun unknownClassFallsBackToFirst() {
        val c = CharacterRegistry.newCharacter("ghost", "no_such_class")
        assertTrue(c.hpMax > 0)
    }

    @Test fun effectiveAttackIncludesWeaponPower() {
        val c = CharacterRegistry.newCharacter("kei", "kei_berserker")
        val baseAtk = CharacterRegistry.effectiveAttack(c)
        // sword_iron 같은 무기가 있다고 가정하지 않고, ItemRegistry 의 첫 무기를 찾아 장착
        val weapon = ItemRegistry.all.firstOrNull { it.kind == ItemKind.WEAPON } ?: return
        c.equipWeapon = weapon.id
        val withWeapon = CharacterRegistry.effectiveAttack(c)
        assertEquals(baseAtk + weapon.power, withWeapon)
    }

    @Test fun defaultPartyHasTwoMembers() {
        val party = CharacterRegistry.defaultParty()
        assertEquals(2, party.size)
        assertEquals("kei", party[0].id)
        assertEquals("ritz", party[1].id)
    }
}
