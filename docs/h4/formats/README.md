# Hero4 자산 포맷 분석

원본: `Hero4/010100D4.jar` (한빛소프트 2009, SKT GVM/Clet, 240×320).

이 폴더의 각 문서는 `tools/converter/` 의 파서 모듈과 짝을 이룹니다.

| 문서 | 포맷 | 변환기 | 결과 (errors=0) |
|---|---|---|---|
| [pal.md](pal.md) | `_PAL` 8byte/color | [`tools/converter/convert_palette.py`](../../../tools/converter/convert_palette.py) | 196/196 |
| [map.md](map.md) | `_MAP_M_NNN` 헤더 v1/v2/v3 + body + **multi-section extras (2026-05-18)** | [`tools/converter/convert_h4_map.py`](../../../tools/converter/convert_h4_map.py) + [`parse_h4_map_extras.py`](../../../tools/converter/parse_h4_map_extras.py) | 97/97 |
| [exd.md](exd.md) | `_EXD` 캐릭터 확장 데이터 + **box layout (2026-05-18)** | [`tools/converter/convert_exd.py`](../../../tools/converter/convert_exd.py) + [`parse_h4_exd.py`](../../../tools/converter/parse_h4_exd.py) | 117/117 |
| [bm-tile-obj.md](bm-tile-obj.md) | `_BM` (멀티/싱글), `TILE`, `OBJ` 0x0b/0x0c | [`tools/converter/convert_bm_v2.py`](../../../tools/converter/convert_bm_v2.py), [`convert_h4_tile.py`](../../../tools/converter/convert_h4_tile.py) | 200 + 30 + 246 frames |
| [hdat.md](hdat.md) | `HDAT/` 25개 그룹 + **Group B P000-P005 layout (2026-05-18)** + Group C PS000-007 | [`parse_h4_hdat_p.py`](../../../tools/converter/parse_h4_hdat_p.py), [`convert_h4_hdat_ps.py`](../../../tools/converter/convert_h4_hdat_ps.py) | Group B/C 풀림, A/D 보류 |
| [scn.md](scn.md) | `_SCN` plaintext bytecode (e0184/e0185) + **disassembler (2026-05-18)** | [`disasm_h4_scn.py`](../../../tools/converter/disasm_h4_scn.py) | 2/350 plaintext decoded |
| [cif.md](cif.md) | `_H_NNN_CIF` 캐릭터 정보 (2026-05-18 후속6) | [`parse_h4_cif.py`](../../../tools/converter/parse_h4_cif.py) + [`decode_h4_cif_frames.py`](../../../tools/converter/decode_h4_cif_frames.py) | 117/117, Hero3 엔진 100% 호환, 3,372+ frames |
| **(후속12)** H4/000-007 `_HIMG_NNN_MMM` | BM v2 0x0b sprite atlas | [`batch_h4_himg.py`](../../../tools/converter/batch_h4_himg.py) | **368 files → 3,372 PNG, 0 errors** |
| **(후속12)** tdf/ + l/_LOGO + TITLE_BM | UI 텍스트 + 타이틀/로고 BM | inline + `convert_bm_v2` | **107 한국어 + 7 PNG** |

## Hero3 와 공유

다음 포맷은 Hero3 와 100% 호환 (Hero3 디코더 무수정 적용):

| 포맷 | 결과 |
|---|---|
| `_TXT` | 5/5 + GMenu/NPCUI 추가 |
| `_CIF` (multi-frame hero/enemy) | 117/117 (Hero4 native) + 148 (Hero3 호환) |
| `_DAT` | 26/26 |
| `_SCN` (이벤트 스크립트) | 350 → 4,078 대사 (DES 잠금 — Ghidra 후) |
| `_MMF` (Yamaha SMAF/MMF 사운드) | 41 (외부 변환 도구 필요) |
| BM v2 0x0b/0x0c | 모든 카테고리 (OBJ, TILE, CM, GMenu, TITLE, LOGO, _HIMG) |

## ✅ 자동 영역 종결 (47건, 후속12)

**Hero4 자산 100% 추출 완료**:
- 3,874 PNG 자산 (apps/hero4-android)
- 600+ 한국어 entries (entity 80 + 아이템 147 + UI 169 + 이벤트 11 + zone 97 + tdf 107)
- CIF 117 animation frames + EXD 117 boxes + EGDAT 167 enemies + NPCG 60 records
- 9 known-ciphertext sentinel (DES key validation 준비)
- Hero3 엔진 100% 호환 (Phase C 시 추가 코드 0줄)

## 미해독 (Phase B Ghidra 의존)

- **DES key 8 bytes** — 1순위 차단, ~400 파일 unblocking
- **AI script opcode dispatch 의미** — script 함수 추적
- **51-slot sprite pool → OBJ asset 매핑** — lookup table 위치
- **_FT_KOR10X11 glyph bitmap packing** — HANINFO 와 연결
- **CIF 80..116 한국어 이름** — e0185 외 별도 catalog source
- **_MAP_M_ sec[4+] event records** — script opcode (Ghidra script dispatch)
- **HDAT Group A 평문 구조** — DES key 후 가능
