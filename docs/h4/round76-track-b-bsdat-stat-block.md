# Hero4 Round 76 (Track B) — BSDAT body = boss stat block

> R72 의 가설 ("BSDAT body = SCN bytecode 유사") 을 정정. **boss stat block** 으로 확정.

## TL;DR

3 `_BSDAT_{0,1,2}` 파일은 **같은 88 boss entry 의 난이도/단계 3 버전** 이다.

근거:
- 같은 boss 이름 (루칸/브리안/누아다/...) 이 3 파일 모두 **정확히 동일 body 길이** (루칸=105B, 브리안=49B)
- byte 위치별 값이 0/1/2 인덱스에 비례하여 증가 — stat scaling
- LE16 overflow 패턴 명확:
  - 루칸 pos[31-32]: `82/0` → `61/1` → `29/3` = **82 / 317 / 797** (HP/EXP 같은 지수 증가)
  - 루칸 pos[29-30]: `46/0` → `159/0` → `24/1` = **46 / 159 / 280**
- SCN op_0x01 reference pattern (`01 00 07 00 00 00 ?? ?? 2e`) **0회 매칭** → bytecode 아님
- byte 0x00 비율 37% (stat padding) — script 라기엔 너무 많은 zero

## 데이터

| boss 이름 | body length | _BSDAT_0/1/2 변동 위치 수 |
|---|---|---|
| 루칸 | 105B | 46 |
| 브리안 | 49B | 24 |
| 누아다 | 49B | (분석 필요) |
| 래비 | 105B | (분석 필요) |
| 케프네스 | 49B | (분석 필요) |

→ 49B vs 105B 두 가지 body size 가 존재 = **보스 등급/유형 2종** (일반 보스 49B + 메인 보스 105B 추정).

## ESDAT 와의 차이

ESDAT (471 entries) 는 별개 분석 필요:
- 0xff separator 평균 1.7회/entry (BSDAT 의 0.1 대비 17배)
- top opcode `0x3f 0x65` (= `?e`) 274회 — script-like text record 가능성

ESDAT 는 SCN script 변종일 가능성이 BSDAT 보다 높다. 후속 분석 대상.

## 후속 트랙

1. **BSDAT stat field mapping** (~1h): pos[29..38] LE16 stat 의 의미 (HP/ATK/DEF/EXP/gold) — Hero3 boss stat 패턴 참조
2. **ESDAT script analysis**: `0x3f` opcode dispatch (event trigger 추정)
3. **49B vs 105B body 구분**: 메인 vs 일반 보스 분류

## commit

- `tools/analysis/bsdat_body_opcodes.py` (신규)
- `tools/analysis/bsdat_stat_block.py` (신규)
- `work/h4/converted/h4_bsdat_body_opcodes.json` (gitignore)
- `work/h4/converted/h4_bsdat_stat_analysis.json` (gitignore)
- `docs/h4/round76-track-b-bsdat-stat-block.md` (이 문서)
