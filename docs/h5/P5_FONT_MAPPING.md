# Hero5 P5 — 한글 비트맵 폰트 매핑 분석 (2026-05-09)

원본 노트: 시스템 폰트(Noto Sans CJK KR)로 게임이 정상 동작하므로 polish 작업.
이 문서는 kor.fnt 의 581 글리프 ↔ 코드포인트 매핑이 어디에 있는지를 정리.

---

## 1. 정정: table.dat 는 **EUC-KR 이 아니라 Unicode BMP**

`tools/converter/convert_h5_fnt2png.py` 가 이전에 "2350 EUC-KR codepoints"
라 기록했지만, 실 값은:

```
range:  0x8861 ─ 0xd3b7
distribution:
  Hanja (CJK Unified, 0x4E00-0x9FFF) : 773
  Hangul Syllables (0xAC00-0xD7AF)    : 1,246
  나머지                              : 331  (0x8861-0xACFF 사이의 한자 보충)
```

EUC-KR 이라면 lead-byte ≥ 0xA1 이어야 하는데, table.dat 첫 항목 0x8861 은
EUC-KR 범위 밖. **strictly sorted BE u16 array**. 위에 적힌 분포로 봐도
명백한 Unicode codepoint 리스트.

검증: `python3 -c "print(hex(0x8861))" → 衡` (Unicode CJK Unified).

산출 JSON `assets/fonts/eucKR_index.json` 도 정정 (0x8861, mapping_status 추가).

---

## 2. 581 ↔ 2350 매핑은 native lookup 안에

폰트 그리기 호출 경로 (capstone disasm 으로 추적):

```
MX_fntDrawString         (0x0003f1e4, 360B)   ─ public 진입점
  ↓
_midas_funcFntGroup_SetCurrentID  (0x3246c)
_midas_funcFntInvalidate          (0x32da4)   ─ ★ codepoint→glyph 매핑이 여기
_midas_funcFntDrawString          (0x3a758)
_midas_funcFntGroup_RowModule     (0x39d8c)
```

`MX_fntGetStringWidth` (0x0003a5a0) 의 character-walk 부분에서:

| 명령 | 의미 |
|---|---|
| `tst r3, #0x80` | 첫 바이트의 MSB 검사 — 한글/한자면 wide |
| `ldr r2, [ip, #0xc]` | ASCII 폭 (ip+0xC) |
| `ldr r1, [ip, #0x4]`  | wide 폭 (ip+0x4) |
| `ldrsb r2, [ip, #0x28]` | per-font 가산값 (1 = 1pt 추가, etc) |
| `add r2, r2, #2`        | wide char → 2 byte 진행 |

→ 이 레벨에선 codepoint → glyph 매핑이 안 보이고, `funcFntInvalidate` 가
실제 lookup 을 내부에서 한다. type.dat (148B) 가 helper data 일 가능성 높음.

---

## 3. type.dat (148 bytes) — 후속 분석 단서

`first 32B = 00 00 01 00 01 00 01 00 01 02 04 04 04 02 03 05 05 05 03 02 04 00 06 06 07 06 07 06 07 06 07 08`

byte 분포 (max = 0x08):

| 값 | 빈도 |
|---:|---:|
| 0x01 | 22 |
| 0x00 | 21 |
| 0x06 | 20 |
| 0x02 | 18 |
| 0x04 | 15 |
| 0x03 | 13 |
| 0x05 | 11 |
| 0x08 | 9 |

148 / 581 ≠ 정수 → 직접적 per-glyph 메타가 아님. **148 = block-of-16 단위 분류** 가설:
codepoint range 를 16 단위로 쪼갠 카테고리 (총 148 블록 ≈ 2350 / 16 ≈ 147). 정확한
사용처는 `_midas_funcFntInvalidate` 디스어셈블 시 드러남.

---

## 4. 결론: 게임 영향 0, 후속 옵션 2 가지

**현재**: Godot 프로젝트는 시스템 Noto Sans CJK KR 폰트로 텍스트를 렌더 →
한글 18,837 unique 코퍼스 모두 정상 표시.

**후속 옵션**:
1. **Noto Sans CJK KR 유지** (권장) — bitmap 581 글리프보다 화질·커버리지 우수.
2. **원본 비트맵 재현이 필요할 때**:
   - `_midas_funcFntInvalidate` (size 미지) 디스어셈블 → codepoint→glyph_index 함수 추출
   - kor.png 의 581 글리프 grid 를 BitmapFont 로 만들고 한글 텍스트 → 581 인덱스 매핑 테이블 생성

---

## 5. 산출

- `apps/hero5-godot/assets/fonts/eucKR_index.json` — codepoint 분류 메타 (정정됨)
- 본 문서 — 매핑 위치/구조 정리
- `tools/h5_extract_battle_funcs.py` 패턴 그대로 `_midas_funcFntInvalidate` 분석에 재사용 가능
