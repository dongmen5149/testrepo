package com.hero3.remake.catalog

import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test
import java.io.File

/**
 * Hero3CatalogProvider — R80 process-scoped catalog holder 검증.
 *
 * scene 들이 인자 없이 catalog 접근할 수 있는지 + lazy install 패턴 동작 검증.
 */
class Hero3CatalogProviderTest {

    @After fun cleanup() { Hero3CatalogProvider.reset() }

    private class FileAssetReader(private val baseDir: File) : AssetReader {
        override fun readText(path: String): String = try {
            File(baseDir, path).readText(Charsets.UTF_8)
        } catch (e: Exception) { throw AssetNotFound(path, e) }
        override fun readBytes(path: String): ByteArray = try {
            File(baseDir, path).readBytes()
        } catch (e: Exception) { throw AssetNotFound(path, e) }
    }

    @Test fun get_returns_null_before_install() {
        assertNull(Hero3CatalogProvider.get())
    }

    @Test fun require_throws_before_install() {
        assertThrows(IllegalStateException::class.java) { Hero3CatalogProvider.require() }
    }

    @Test fun install_runs_loader_once_then_caches() {
        var calls = 0
        val reader = FileAssetReader(File("src/main/assets"))
        Hero3CatalogProvider.install {
            calls++
            Hero3CatalogLoader.load(reader)
        }
        // 두 번째 install 호출은 cached 본 사용
        Hero3CatalogProvider.install {
            calls++
            Hero3CatalogLoader.load(reader)
        }
        assertEquals(1, calls)
        assertNotNull(Hero3CatalogProvider.get())
        assertEquals("1.2", Hero3CatalogProvider.require().schemaVersion)
    }

    @Test fun installCatalog_replaces_instance() {
        val reader = FileAssetReader(File("src/main/assets"))
        val first = Hero3CatalogLoader.load(reader)
        Hero3CatalogProvider.installCatalog(first)
        assertNotNull(Hero3CatalogProvider.get())
        Hero3CatalogProvider.reset()
        assertNull(Hero3CatalogProvider.get())
    }
}
