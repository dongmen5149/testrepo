# `_SCN` plaintext bytecode (Hero4)

350개 SCN 파일 중 **2개는 DES 처리 안 된 raw plaintext** (8-byte misaligned outlier).

| 파일 | size | 특이점 |
|---|---|---|
| `e0184_scn` | 30B | "VALUE" 문자열 포함, 최소 메타데이터 SCN |
| `e0185_scn` | 6313B | Hero4 글로벌 entity catalog (87 strings, 캐릭터/객체 이름 정의) |

나머지 348 SCN 은 DES (custom S1) 로 암호화. 본 문서는 plaintext 2개에서 추론한 **SCN bytecode 구조** 정리.

## 공통 헤더 signature (2026-05-18 발견)

두 plaintext SCN 의 첫 12 byte 비교:

```
e0184: 01 00 01 53 00 01 a1 ff ff ff ff ff
e0185: 01 02 01 53 00 01 c8 ff ff ff ff ff
```

**5-byte fixed signature: `01 ?? 01 53 00 01 ?? ?? ff ff ff ff ff`**
- byte 0 = 0x01 (constant)
- byte 1 = file type variant (0x00 / 0x02 — 2종 발견)
- byte 2 = 0x01 (constant)
- byte 3 = 0x53 (`S` — magic letter)
- byte 4 = 0x00 (constant)
- byte 5 = 0x01 (constant)
- byte 6 = attribute (size? checksum? — 0xa1 / 0xc8)
- byte 7..11 = `ff ff ff ff ff` (5-byte 0xff separator)

총 40 known bits → **DES known-plaintext crib** (348 encrypted SCN 의 첫 cipher block 도 같은 plaintext signature 를 가질 가능성 매우 높음).

## bytecode 영역 (offset 12+)

### e0184 (30B 전체) 분해

```
[12..14]  01 07 00          ← record header: opcode=0x01 param=7
[15..16]  00 00             ← (padding or extended param)
[17..20]  ff 0c 00 ff       ← separator + value=0x0c (= 12) + separator
[21..22]  00 01             ← record header: opcode=0x01 (string follows)
[23]      06                ← string length (6 = 5 chars + null)
[24..28]  V A L U E         ← ASCII string
[29]      00                ← null terminator
```

### e0185 (6313B) 같은 영역

```
e0185 bytes 12..21: 02 23 07 00 00 00 ff 0c 00 ff
e0184 bytes 12..20: 01 07 00 00 00 ff 0c 00 ff
```

두 파일 모두 **bytes 15..20 = `00 00 ff 0c 00 ff`** (6 byte 공유). 이는 SCN body 시작 부분의 형식 marker.

## 구조 가설

```
[Magic header — 12B] (signature + variant + attribute + 0xff sep)
[Record list]
    record = [opcode: 1B] [length/param: 1B] [body: length B]
    opcode 0x01: string entry (1B opcode + 1B length + N bytes string + 0x00)
    opcode 0x02: ?
    opcode 0x0c: small immediate value (1B opcode + 1B value)
```

`0xff` byte 가 **record separator** 역할로 보임 (Hero3 SCN 의 `0xff ff ff` magic 과 유사).

## e0185 의 의미 — 글로벌 entity catalog

87 null-terminated strings 추출 (`work/h4/converted/e0185_name_table.json`):

- ASCII 라벨 5개 (`NPC1`, `NPC2`, `NPC3`, `FGI`, `PLAYER`)
- 캐릭터/NPC 33개 (앨리스, 브리안, 디어드리, 노덴스, 누아다 등 — 켈트 신화 Tuatha Dé Danann)
- 직업 19개 (인간/선주 + 직업명 = 인간 대장장이, 선주 연금술사 등)
- 게임 상태/객체 30개 (출구, 결계, 블라인드, 대미지, 어택, 넉백 등)

Hero4 전체 SCN 이 이 catalog 를 **글로벌 인덱스로 참조** 하는 구조일 가능성 매우 높음 (DES key 발견 후 검증).

→ [translation_dict.py CHARACTERS_H4](../../../tools/i18n/translation_dict.py) 52 entries 로 prefill 완료.

## DES 복호화 후 재검증 항목

키 발견 시:
1. encrypted SCN 첫 8 byte decrypt → `01 ?? 01 53 00 01 ?? ??` 매치 확인 (best validation)
2. decrypted SCN 의 bytecode 구조가 위 가설과 일치 확인
3. e0185 catalog 의 string index 를 다른 SCN 이 참조하는지 확인 (이름 raw bytes 가 아닌 1-byte index)

## 디스어셈블러 (2026-05-18 후속4)

[tools/converter/disasm_h4_scn.py](../../../tools/converter/disasm_h4_scn.py) — plaintext SCN tokenizer + catalog 추출.

```bash
HERO_GAME=h4 python tools/converter/disasm_h4_scn.py
# 결과: work/h4/converted/{e0184,e0185}_scn_disasm.json
#       work/h4/converted/e0185_name_table.json (80 entries)
```

기능:
- 12B 헤더 검증 (signature_ok flag)
- 0xff 단위로 record tokenize
- known opcode pattern detection (0x01 string-like, 0x07 magic, 0x0c immediate, 0xf7 3-arg bind)
- EUC-KR catalog 시작점 자동 감지 (e0185 의 offset 5589 ~)
- record-kind 통계

e0185 분석 결과:
- bytecode 영역: 5577B = 1110 tokens
- token kinds: `op_0x01` 462회 (가장 흔한 — string-like 또는 entity ref), `op_0x30` 45회, `op_0x00` 35회, `op_0x02` 9회
- 555개 0xff separator

### op_0x01 record 정밀 구조 (2026-05-18 후속5)

462 records 모두 다음 일관된 형식:

```
[01]                   ← record start byte
[00 07 00 00 00]       ← 5-byte fixed prefix (REFERENCE_ENTITY opcode 추정)
[middle: 2~4 bytes]    ← 가변 indices/ids (string index, sub-id 등)
[2e]                   ← terminator byte ('.')
```

길이 분포:
- 392 records 가 9 bytes (middle = 2 bytes)
- 45 records 가 5 bytes (단축 형식)
- 19 records 가 7 bytes (확장 형식)
- 4 records 가 14 bytes (긴 형식)
- 기타 작은 수

샘플:
- `01 00 07 00 00 00 01 01 2e` — entity ref (1, 1)
- `01 00 07 00 00 00 02 01 2e` — entity ref (2, 1)
- `01 00 07 00 00 00 03 01 2e` — entity ref (3, 1)
- `01 00 07 00 00 00 01 00 01 2e` — entity ref with sub-id (1, 0, 1)

462 references / 80 catalog entries ≈ **6 references per entity** — Hero4 전체 SCN 이 e0185 catalog 의 entity index 를 참조하는 핵심 구조 확정.

DES key 발견 시: encrypted SCN 350개를 같은 disassembler 로 통과시켜 token 분포 + op_0x01 reference 패턴 cross-validate 가능.
