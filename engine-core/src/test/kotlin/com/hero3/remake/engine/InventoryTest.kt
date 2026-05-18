package com.hero3.remake.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InventoryTest {

    @Test fun addStacksExisting() {
        val inv = Inventory()
        assertTrue(inv.add("potion_s", 3))
        assertTrue(inv.add("potion_s", 2))
        assertEquals(1, inv.all().size)
        assertEquals(5, inv.get(0)?.count)
    }

    @Test fun addNewItemUsesNewSlot() {
        val inv = Inventory()
        inv.add("potion_s", 1)
        inv.add("herb", 1)
        assertEquals(2, inv.all().size)
    }

    @Test fun removeFullDeletesSlot() {
        val inv = Inventory()
        inv.add("potion_s", 2)
        assertTrue(inv.remove(0, 2))
        assertEquals(0, inv.all().size)
        assertNull(inv.get(0))
    }

    @Test fun removePartialKeepsSlot() {
        val inv = Inventory()
        inv.add("potion_s", 5)
        inv.remove(0, 2)
        assertEquals(3, inv.get(0)?.count)
    }

    @Test fun fullInventoryRejectsNewItem() {
        val inv = Inventory()
        for (i in 0 until Inventory.MAX_SLOTS) {
            inv.add("herb_$i", 1)
        }
        assertTrue(inv.isFull())
        assertFalse(inv.add("potion_s", 1))
        // 기존 아이템 stack 은 가능
        assertTrue(inv.add("herb_0", 1))
    }

    @Test fun starterInventoryHasInitialItems() {
        val inv = Inventory.starter()
        assertTrue(inv.all().isNotEmpty())
        assertTrue(inv.all().any { it.itemId == "potion_s" })
    }
}
