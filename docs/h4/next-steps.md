# Hero4 다음 단계

Phase A (자산 변환) 종료. 이 문서는 사용자 (또는 다음 세션 Claude) 가 진행해야 할 작업을 우선순위 순으로 정리.

> 사용자 컨텍스트: "리메이크" 정의는 [`../REMAKE_METHODOLOGY.md`](../REMAKE_METHODOLOGY.md) 참조 — 최종 산출물은 Play Store + App Store 직배포.

---

## ⏭ "영웅서기4 다음 내용 진행해줘" 라고 했을 때 — 빠른 셀렉터

> **🏁 2026-05-18 후속12 — 자동 영역 완전 종결 (47건)**.
> Hero4 자산 100% 추출 완료 (3,874 PNG + 600+ 한국어 entries). **사용자가 다음에 가져올 것 = DES key 8 bytes (Ghidra GUI 결과)**. 키 발견 시 ~400 파일 자동 복호화 (~30분).

**가장 가능성 높은 시나리오**: 사용자가 Ghidra 작업 후 DES key 8 bytes 를 들고 옴.

### 시나리오 1: 사용자가 DES key 가져옴 ⭐ (1순위 예상)

**즉시 실행 (Claude가 자동으로 수행 가능)**:

```bash
cd d:/testrepo

# Step 0 — 1초 키 검증 (3 known-ciphertext block 으로)
KEY_HEX="<16HEX_FROM_USER>"   # 사용자가 ASCII 로 주면 hex 변환 필요
python -c "
from Crypto.Cipher import DES
k = bytes.fromhex('$KEY_HEX')
c = DES.new(k, DES.MODE_ECB)
p_sent = c.decrypt(bytes.fromhex('3b7af9a427907dac'))   # SCN 가장 흔한 last block (130회)
p_frst = c.decrypt(bytes.fromhex('4655b8f39c0fe0b2'))   # SCN 가장 흔한 first block (8회)
p_bsdt = c.decrypt(bytes.fromhex('d6c1b1be38099f0e'))   # BSDAT 첫 block (3 파일 공유)
print('sentinel:', p_sent.hex())
print('first:   ', p_frst.hex())
print('bsdat:   ', p_bsdt.hex())
# Best signature: first block 이 01 ?? 01 53 00 01 ?? ?? 매칭
sig_ok = p_frst[0]==0x01 and p_frst[2]==0x01 and p_frst[3]==0x53 and p_frst[4]==0x00 and p_frst[5]==0x01
print('KEY VALID:', sig_ok)
"

# Step 1 — 키 OK 면 자동 파이프라인 (~30분 총)
# 1a. SCN 348 일괄 복호화
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" --batch

# 1b. HDAT Group A 8 파일 (BH/BS/SA/SS/S000-S003) 같은 키
for f in _H_BH _H_BS _H_SA _H_SS _H_S000 _H_S001 _H_S002 _H_S003; do
    python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" \
        work/h4/extracted/HDAT/$f work/h4/decrypted/HDAT/$f
done

# 1c. ITM/DAT 16 파일 + E/BSDAT 3 + E/ESDAT 3 + NPC scripts ~7 + FR ~5 도 동일 키
# (총 confirmed 107 + likely 141 = ~400 파일)
# decrypt_h4_scn.py 가 `--input_dir`/`--output_dir` 옵션 지원하는지 확인 후 일괄 처리

# Step 2 — decrypted SC 를 extracted 로 백업-치환
cp -r work/h4/extracted/MAP/SC work/h4/extracted/MAP/SC.encrypted_backup
cp work/h4/decrypted/SC/* work/h4/extracted/MAP/SC/

# Step 3 — corpus 재생성 + Android 자산 재배포
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/converter/prepare_android_assets.py \
    work/h4/converted apps/hero4-android/app/src/main/assets

# Step 4 — A1 영어 번역 (Claude Haiku, ~30분, ~$0.30)
# translation_dict.py 의 CHARACTERS_H4 52 entries + CIF catalog 80 entries 활용
export ANTHROPIC_API_KEY="..."
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

**검증 정답 패턴**:
- `first` block decrypt 결과 `01 ?? 01 53 00 01 ?? ??` 매칭 (SCN signature, 40 known bits)
- 또는 `sentinel` block 이 `00*8`, `ff*8`, low-entropy 반복 패턴

### 시나리오 2: Ghidra 작업 중 부분 결과 보고

**예: "_DAT_DES xref 찾았는데 다음 단계 뭐야?"** → 안내:
- `/DAT/_DAT_DES` @ 0x86ecc 의 xref → `_DAT_DES` 파일 로더 함수
- 그 함수의 호출자 → SCN decryption setup 진입점
- 호출자 코드에서 8-byte literal 또는 키 파생 input 추출
- `J@IWO8N7L0E7E` (0x86edc) 도 같이 xref 추적 (키 후보 또는 키 파생 input)
- 자세한 가이드: [`ghidra-guide.md`](ghidra-guide.md) §5.1

### 시나리오 3: 사용자가 트랙 전환 결정

**Phase C 시작 (KMM 분리)**:
```bash
git tag v0.1-pre-kmm   # Hero3 안정 상태 저장
# Hero3 엔진을 shared/commonMain/ 으로 이전 시작
# Hero4 는 CIF/BM/_TXT 디코더 100% 호환이라 자동 inherit
```
- 참조: [docs/h3/PROGRESS.md](../h3/PROGRESS.md) + 본 문서 §"C. Phase C"

**Hero3 잔여 / Hero5 트랙**:
- Hero3: `docs/h3/PROGRESS.md` — i18n 완료, Ghidra/SMAF/LLM/디자인 남음
- Hero5: `docs/h5/PROGRESS.md` — 진척 ≈77%

### 시나리오 4: 단순히 "이어서 진행" 만 (정보 부족)

**Claude 응답**:
> "자동 영역 47건 모두 종결됨. DES key (Ghidra 결과) 가져오시거나 Phase C/D 결정 알려주세요. Hero3/Hero5 트랙도 가능."

이미 풀린 (= 다시 안 해도 되는) 항목:

- ~~A4 (recon game-aware)~~ ✅ 완료 — 2026-05-07
- ~~A5 (`_TILE_030`)~~ ✅ 완료 — 2026-05-07
- ~~A3 (translation_dict.py game-aware + Hero4 zone prefill)~~ ✅ 완료 — 2026-05-07
- ~~Hero4 SCN 암호화 정체 파악~~ ✅ 완료 — 2026-05-07 (표준 DES, ECB 거의 확실)
- ~~DES key 자동 brute-force v1~~ ✅ 시도 완료 — ASCII (2,311) + sliding-window (59,556) 둘 다 키 미발견
- ~~DES key 자동 brute-force v2~~ ✅ 2026-05-14 — 전체 binary (511,006) + descriptor (736) + AID 파생 (24) + hash 가설 (MD5/SHA1) + sequential bytes + `JIWONLEE` 가설 + 흔한 weak keys — Phase 1 sentinel match 0건
- ~~ECB vs CBC 단정~~ ✅ 2026-05-14 — last-block ciphertext `3b7af9a427907dac` 가 350 중 38회 반복. CBC 라면 unique 해야 → ECB 100%
- ~~HDAT/_H_PS\* entry layout 추론~~ ✅ 2026-05-14 — PS000-007 = 10-byte 헤더 + 6×10-byte 레코드. [`convert_h4_hdat_ps.py`](../../tools/converter/convert_h4_hdat_ps.py) 작성, `work/h4/converted/HDAT/ps.json` 생성
- ~~Hero4 SCN plaintext signature 발굴~~ ✅ 2026-05-18 — e0184/e0185 plaintext SCN 발견 → `01 ?? 01 53 00 01 ?? ??` 5-byte known-plaintext signature 확립
- ~~CHARACTERS_H4 사전 prefill~~ ✅ 2026-05-18 — e0185 글로벌 catalog 87 string → 52 캐릭터/객체 prefill, system prompt 통합 검증
- ~~`_DAT_DES` 정밀 검증~~ ✅ 2026-05-18 — 824 byte 중 823 표준 DES 일치, **S1[58] 1 byte 만 다름** (`std=3 → got=2`). [verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py)
- ~~Hero4 custom DES 구현~~ ✅ 2026-05-18 — [custom_des_h4.py](../../tools/converter/custom_des_h4.py) (pure Python, 5,876 blk/s, roundtrip OK)
- ~~DES brute-force v3 (signature) + v4 (custom DES)~~ ✅ 2026-05-18 — v3 (표준 DES + Hero4 signature) Phase 2 0건, v4 (custom DES + 513,941 candidates × 5 ciphers) Phase 1 0건 → 키는 binary literal 아님
- ~~`_PAL` secondary RGB 통계~~ ✅ 2026-05-18 — A1/A2 = 0 padding (alpha 아님), identical 0%, scale-darken 11% 만. 가설 좁힘 (color cycling / two-tone / display profile). [analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py)
- ~~_EXD payload struct (count=1 케이스)~~ ✅ 2026-05-18 — subtype=2/3 의 4B head + 8B box(es) layout 확정. box = LE int16 dx,dy,w,h. 117 file 모두 파싱. [parse_h4_exd.py](../../tools/converter/parse_h4_exd.py) + `work/h4/converted/exd_parsed.json`
- ~~_MAP_M_ extras 영역 multi-section~~ ✅ 2026-05-18 — 4-8 sections × (1B count + N×8B record), 8B record = type+sub3+x+y. 97 file 모두 파싱, 13/97 완전 소비. [parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py)
- ~~v4 brute-force (custom DES, S1[58]=2)~~ ✅ 2026-05-18 — 513,941 candidates × 5 ciphers × 438s, **0 survivors** → 키는 binary literal 아님 100% 확정
- ~~HDAT Group B (P000-P005) layout~~ ✅ 2026-05-18 — `3B header + N×50B entries`, entry = 8 u16 LE + marker + 5B param + 14 nested u16. 6/6 파일 파싱. [parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py)
- ~~e0184_scn 완전 분해 + SCN bytecode 구조 추론~~ ✅ 2026-05-18 — 12B 헤더 + record-based bytecode (opcode 0x01 = string, 0x0c = immediate, 0xff = sep). [docs/h4/formats/scn.md](formats/scn.md)
- ~~HDAT Group A 암호화 키 공유 확인~~ ✅ 2026-05-18 — SCN sentinel block `3b7af9a427907dac` 가 Group A 에서 92회 반복 → SCN + HDAT Group A 8개 같은 DES 키. 키 발견 시 356 파일 동시 복호화
- ~~HDAT Group D (PDAT, SG)~~ ✅ 2026-05-18 — `_H_SG` = 10 슬롯 × 17B (2 모드 × 5 캐릭터), `_H_PDAT` = 17 var-length records (player init data)
- ~~OBJ/{000,001,002}/ 그룹 분포~~ ✅ 2026-05-18 — 000=100 16×16 icons / 001=100 variable 캐릭터 / 002=47 variable 아이템. 게임 매핑은 _MAP_M_ extras sub[3] cross-ref 후
- ~~_MAP_M_ extras 의 sub[2] = global OBJ id 매핑~~ ✅ 2026-05-18 후속4 — 16,358 records 100% in [0,246], 0 OOB. `0..99=g000, 100..199=g001, 200..246=g002`. x/y = 16-pixel 좌표. [analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py)
- ~~plaintext SCN disassembler + e0185 name_table 추출~~ ✅ 2026-05-18 후속4 — [disasm_h4_scn.py](../../tools/converter/disasm_h4_scn.py), 80 entries catalog 추출, opcode 통계 (op_0x01 462회 가장 흔함)
- ~~_MAP_M_ extras sec[4+] event block header~~ ✅ 2026-05-18 후속5 — 77/97 maps 가 `[count: 1B] [00 01: 2B] [type: 1B]` 매칭. count=3 (51) 또는 4 (26), type=0x03 (52) 또는 0x02 (34). Variable-length records 내부 schema 는 Ghidra 후
- ~~e0185 op_0x01 record 9-byte fixed schema~~ ✅ 2026-05-18 후속5 — 462 records 모두 `[01] [00 07 00 00 00 prefix] [2~4B middle] [2e terminator]`. 평균 6 refs/entity (= 80 catalog × 6 ≈ 480) → catalog index 참조 패턴 확정
- ~~OBJ id 매핑 정정~~ ✅ 2026-05-18 후속5 — filename = global id 그대로 (offset 빼지 않음). `OBJ/001/_OBJ_199` 형태. 파일 존재 검증 완료
- ~~CIF 117 파일 Hero3 parser 호환성 + stride 검증~~ ✅ 2026-05-18 후속6 — slot_count 1..8 모두 정상 파싱. hero=41B + enemy=4B stride. **Hero3 엔진 commonMain 이전 시 Hero4 자동 inherit**. [parse_h4_cif.py](../../tools/converter/parse_h4_cif.py), [cif.md](formats/cif.md)
- ~~CIF↔EXD 117/117 페어링~~ ✅ 2026-05-18 후속6 — 모든 entity 가 CIF+EXD pair. EXD subtype=3 (collision+body) 가 88/117 = 게임 캐릭터/NPC
- ~~Hero4 전체 DES 암호화 파일 풀 스캔~~ ✅ 2026-05-18 후속6 — 107 confirmed sentinel match + 141 likely high-entropy. **DES key 발견 시 ~400 파일 동시 복호화** (E/BSDAT/ESDAT, ITM/DAT, NPC/QUEST, FR/ 추가). [scan_h4_des_files.py](../../tools/recon/scan_h4_des_files.py)
- ~~Hero4 CIF 117 animation frame 완전 디코드~~ ✅ 2026-05-18 후속7 — Hero3 decoder 무수정 적용 (hero 41B + enemy 4B). _H_001~004 hero = 973~1879 frames each. 117/117 = 0 errors. [decode_h4_cif_frames.py](../../tools/converter/decode_h4_cif_frames.py), JSON: `cif_frames_decoded.json`
- ~~_EGDAT 167 enemies 100% 파싱~~ ✅ 2026-05-18 후속7 — type byte 0x1e + 32B paired record (16B stat + 16B extras). HP/ATK/DEF/4 stats. **Hero4 적 데이터 game wiring 즉시 사용 가능**. [parse_h4_npc_data.py](../../tools/converter/parse_h4_npc_data.py)
- ~~_NPCG_DAT + variant + FT HNF 폰트 + AI scripts 43~~ ✅ 2026-05-18 후속7 — NPCG 60 records (39 unique NPC IDs), 5 fonts (HNF magic, English + Korean), 43 AI bytecode scripts
- ~~CIF id ↔ e0185 catalog 매핑 (80/117 한국어 이름)~~ ✅ 2026-05-18 후속8 — CIF 3=브레스, CIF 4=브리안, CIF 76-79=상점 4종. Hero4 entity 한국어 라벨링 완성. 출력: `hero_entities_named.txt`, `e0185_catalog_named.txt`, `cif_with_catalog_names.json`
- ~~EGDAT 59 enemy types × 1-6 variants~~ ✅ 2026-05-18 후속8 — 167 entries 그룹화. extra byte 15 = variant id within type
- ~~_FT_HANINFO 2350 한글 음절 lookup~~ ✅ 2026-05-18 후속8 — KS X 1001 표준 정확 일치, EUC-KR 코드 → glyph 매핑. 즉시 텍스트 렌더링 사용 가능
- ~~ITM SD0/SD1 147 아이템 한국어 이름 추출~~ ✅ 2026-05-18 후속9 — 첫 byte=count, 이후 [length] [EUC-KR text] 반복. 소마주/파워러젬/백색마도 등. 출력: `itm_descriptions.{json,txt}`
- ~~GMenu/NPCUI/EVENT_POP 한국어 UI 텍스트 191개 추출~~ ✅ 2026-05-18 후속9 — 메뉴(82) + 서브액션(17) + NPC UI(70) + 이벤트팝업(11) + 12 orbs + 5 특수 오브. 출력: `gmenu_ui_texts.txt`, `event_pop_texts.txt`
- ~~AI script 43 files 통계 패턴~~ ✅ 2026-05-18 후속9 — byte 0=0x01 script start, 0x64 정확히 1회/파일 (END marker), 공통 4-byte 시퀀스 식별. opcode 의미는 Ghidra 후
- ~~_NPCG_DAT byte 2 = CIF id 직접 매핑~~ ✅ 2026-05-18 후속10 — 60 records, 39 unique NPC IDs 모두 CIF id 와 1:1. CIF 80/110-114 도 NPC 등록 확인 (별도 catalog source 존재 시사)
- ~~ITM/_ITEMDROP 9 records × 8B layout~~ ✅ 2026-05-18 후속10 — `[06 00 + 6 item_id slots]`, zone progressive drop pool
- ~~BSDAT 8B + ESDAT 16B 공유 cipher prefix 발굴~~ ✅ 2026-05-18 후속10 — DES key validation 핵심. 9 known-ciphertext sentinel 로 즉시 검증 가능

### 🎯 첫 응답 체크리스트 (사용자 메시지 분석)

```
사용자 메시지에 다음 단어 포함 여부 빠르게 확인:

□ "key", "키", "8 byte", "DES 키", "발견", "복호화" → 시나리오 1
□ "Ghidra", "ghidra", "xref", "_DAT_DES", "함수 추적" → 시나리오 2
□ "Phase C", "KMM", "iOS", "공통 모듈", "리팩터" → 시나리오 3
□ 단순 "이어서", "다음 진행" 만 → 시나리오 4 (정보 요청)
```

자동 진행 가능한 Hero4 항목은 더 이상 없음 — 위 4 시나리오 중 하나로 진입 필수.

---

## 🟢 즉시 자동 가능 (사용자 트리거만 필요)

### ⚡ DES key 발견 시 자동 파이프라인 (다음 세션 카피-페이스트)

```bash
# 0. 키 검증 — 키 = 8 bytes (16 hex / 8 ASCII / colon-sep)
KEY="<KEY_HERE>"   # 예: "0xa1b2c3d4e5f60718" 또는 "Hanbit01"

# 0.5. 1초 검증 (표준 DES + Hero4 custom DES 둘 다 시도)
python -c "
from Crypto.Cipher import DES
import sys; sys.path.insert(0, 'tools')
from converter.custom_des_h4 import decrypt as h4d

k = bytes.fromhex('$KEY')   # 또는 b'$KEY' if ASCII

# Test 1: 표준 DES, 가장 흔한 last block (38회 sentinel)
print('std-DES last:', DES.new(k, DES.MODE_ECB).decrypt(bytes.fromhex('3b7af9a427907dac')).hex())

# Test 2: Hero4 custom DES (S1[58]=2), 가장 흔한 first block (8회)
p = h4d(k, bytes.fromhex('4655b8f39c0fe0b2'))
sig_ok = p[0]==0x01 and p[2]==0x01 and p[3]==0x53 and p[4]==0x00 and p[5]==0x01
print('h4-DES first:', p.hex(), '  signature OK:', sig_ok)
"
# → low-entropy plaintext (예: 00*8) 이거나 signature OK 면 키 정답

# 1. SCN 일괄 복호화 → work/h4/decrypted/SC/*_scn (350 file)
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key "$KEY" --batch

# 1b. (NEW 2026-05-18) HDAT Group A 8 파일도 같은 키 → 복호화
#     SCN sentinel 3b7af9a427907dac 가 HDAT-A 8 파일에서 92회 반복 → 동일 DES 키 확정
for f in _H_BH _H_BS _H_SA _H_SS _H_S000 _H_S001 _H_S002 _H_S003; do
    python tools/converter/decrypt_h4_scn.py --key "$KEY" \
        work/h4/extracted/HDAT/$f work/h4/decrypted/HDAT/$f
done

# 2. 단일 파일로 1차 검증 — EUC-KR 한글이 보이면 성공
xxd work/h4/decrypted/SC/e0001_scn | head -10
#    또는 첫 8 byte 가 plaintext signature `01 ?? 01 53 00 01 ?? ??` 매치하는지

# 3. decrypted 를 extracted 로 백업-치환 (convert_all.py 가 extracted 만 봄)
cp -r work/h4/extracted/MAP/SC work/h4/extracted/MAP/SC.encrypted_backup
cp work/h4/decrypted/SC/* work/h4/extracted/MAP/SC/

# 4. 파이프라인 재실행
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/converter/prepare_android_assets.py work/h4/converted apps/hero4-android/app/src/main/assets

# 5. A1 — 영어 번역 (~30분, ~$0.30)
#     translate_dialogues.py 의 system prompt 는 이미 CHARACTERS_H4 52 entries prefill 됨 (2026-05-18)
export ANTHROPIC_API_KEY="..."
HERO_GAME=h4 python tools/i18n/translate_dialogues.py

# 6. (선택) corpus top characters 보강 — translation_dict.py 의 CHARACTERS_H4 dict 추가
#    이미 52 entries 있음. Top 텍스트로 누락 인명 보강 시 dialogue_top_texts.json 참조

# 7. (NEW) e0184/e0185 의 plaintext 와 decrypt 결과 일치 검증
#    → SCN bytecode 파서 작성 가능 (docs/h4/formats/scn.md 의 opcode 0x01/0x0c 가설로 시작)
```

### A1. ~~대사 영어 번역~~ ⛔ **DES key 발굴 후 가능**

```bash
export ANTHROPIC_API_KEY=...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

- 입력: `work/h4/converted/dialogue_corpus.json` (현재 garbage, key 발굴 후 재생성)
- 출력: `work/h4/converted/dialogue_translations_en.json`
- 이미 game-aware 사전 + system prompt 적용됨 (A3 완료)
- 추정 비용: ~$0.30 (Hero3 $0.66 보다 적음, 대사 수 1/6 수준)

> ⛔ **현재 차단**: Hero4 SCN 이 DES 암호화 되어 있어 corpus 가 garbage. Phase B 에서 DES key 8 bytes 발굴 → 위 §⚡ 자동 파이프라인 한 번 돌리면 됨. 자세한 내용은 [Phase B](#b-phase-b--ghidra-gui-분석) 참조.

### A2. ⭐ Hero4 Ghidra 프로젝트 셋업 — **현재 1순위**

`work/h3/ghidra_proj/*.lock` 파일이 잠겨 있어서 작업 중 work/ 이동 불가. Ghidra 가 열려있으면 닫고:

```bash
# 락 파일 정리 (Ghidra 닫은 후)
rm work/h3/ghidra_proj/*.lock work/h3/ghidra_proj/*.lock~
```

새 Hero4 Ghidra 프로젝트:
```
File > New Project > work/h4/ghidra_proj/Hero4
File > Import > work/h4/extracted/client.bin387872
Language: ARM:LE:32:Cortex (gcc)
```

**A2 직후 1순위 추적** (B-1):
- string `/DAT/_DAT_DES` @ 0x86ecc xref 검색
- 그 string 을 사용하는 함수 = `_DAT_DES` 파일 로더 = SCN decryption setup 진입점
- 그 함수 호출자 또는 인접 코드에서 8-byte 키 literal / 키 파생 input 추출
- 키 형태 후보: ASCII 8 bytes / 16 hex chars / binary 8 bytes / longer string의 prefix
- 발견 즉시 `tools/converter/decrypt_h4_scn.py --key <KEY> --batch` 로 검증

### ~~A3. Hero4 character 사전 보강~~ ✅ 완료 (2026-05-07)

[translation_dict.py](../../tools/i18n/translation_dict.py): `CHARACTERS_H3/H4`, `PLACES_H3/H4` 분리 + `for_game(id)` API 추가. Hero4 zone 12개 prefill (Murias/Findias/Falias/Gorias 켈트 4 보물 도시 + 수레바퀴섬/매도우힐/이름없는섬/아눈섬/검은바위섬/은바위섬/해적소굴/환영의검). 기존 `CHARACTERS/PLACES` 는 H3 alias 보존.

[translate_dialogues.py](../../tools/i18n/translate_dialogues.py): `build_system_prompt` 가 `_g.id` 기반 자동 게임 헤더 (`GAME_HEADERS`) + dict 선택. `--dry-run` 이 corpus 부재시에도 동작.

**검증 명령**:
```bash
HERO_GAME=h4 python tools/i18n/translate_dialogues.py --dry-run    # Hero4 system prompt 출력
HERO_GAME=h3 python tools/i18n/translate_dialogues.py --dry-run    # Hero3 회귀 없음 확인
```

CHARACTERS_H4 는 corpus 풀린 후 채울 placeholder. Hero3 회귀 0 (249 항목 그대로).

### ~~A4. `tools/recon/find_xrefs.py` Hero4 용 TARGETS 갱신~~ ✅ 완료 (2026-05-07)

[extract_strings.py](../../tools/recon/extract_strings.py) `--json` 옵션 + [_targets.py](../../tools/recon/_targets.py) 헬퍼로 풀림. 3 스크립트 모두 game-aware. 발견:
- code/data 경계 ≈ 0x77000
- 핵심 라벨 4개: `frameBuf is NULL`, `Alpha Palette Index Not Found`, `java/lang/NullPointerException`, `(null)`
- **Hero4 binary 는 LDR+ADD T1 인접 PIC 패턴이 거의 없음** → Phase B 에서 다른 추적 전략 (32-bit LDR.W 또는 Ghidra 자체 xref) 필요

### ~~A5. `_TILE_030` 분석~~ ✅ 완료 (2026-05-07)

컨테이너 prefix `01 00 00 00 <size LE32>` 감지. [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 의 `decode_h4_tile` 에서 prefix stripping 후 inner BM 으로 재진입. 결과: 16×16 dark blue placeholder. h4_tile=276→277.

---

## 🟡 사용자 결정 필요

### B. Phase B — Ghidra GUI 분석

상세: [`ghidra-guide.md`](ghidra-guide.md)

**선결**:
- JDK 21 + Ghidra 12.x 설치 (Hero3 와 동일 환경)
- A2 (Ghidra 프로젝트 생성) 완료
- A4 (Hero4 GOT base 추정) 완료 권장

**우선순위 함수** (string xref 기반):

| 풀리는 미해독 | 키 string |
|---|---|
| ⭐ **DES key (8 bytes)** | `/DAT/_DAT_DES` 로딩 함수 + 그 호출자 (SCN 복호화 진입점) — `J@IWO8N7L0E7E` @0x86edc 같이 추적 |
| _PAL secondary RGB 의미 | `/H4/PAL/_H_%03d_PAL`, `Alpha Palette Index Not Found` |
| _EXD payload entry struct | `/H4/EXD/_H_%03d_EXD` |
| _MAP_M_ extras 영역 (NPC/exit/event) | `/MAP/M/_MAP_M_%03d` |
| HDAT entry layout | (정확한 string 미확인 — file enum 으로 로드 가능) |

**예상 시간**: 1~2주 (Hero3 Ghidra 작업과 비슷한 수준).

> ⚠️ **2026-05-07 발견**: Hero4 SCN 파일은 **DES 암호화** (high-entropy 바이트). `work/h4/extracted/DAT/_DAT_DES` (824 bytes) 가 표준 DES 알고리즘 테이블 (PC-1, E-box, P-box, S1-S8) 을 그대로 담고 있음을 확인.
>
> ⚡ **2026-05-14 보강**: ECB 모드 단정 (last-block ciphertext `3b7af9a427907dac` ×38 반복). 확장 brute-force v2 (전체 binary + descriptor + hash + `JIWONLEE` 가설) **모두 실패** → 키는 binary 안 8-byte literal 이 아니라 **(a) 별도 위치 / (b) 스크램블 / (c) 런타임 derive** 셋 중 하나. Ghidra 에서 `_DAT_DES` 호출 함수 따라가서 키 source 직접 확인 필수. 검증용 known-ciphertext 표는 [PROGRESS.md `🔑 known-ciphertext leverage`](PROGRESS.md#-known-ciphertext-leverage-ghidra-키-발견-시-즉시-검증용) 참조.

### C. Phase C — Hero3 엔진 KMM 분리 + Hero4 콘텐츠 wiring

[Phase D 와 묶인 결정](#phase-d).

**작업 큰 그림**:
1. `android/` (Hero3 단일) → `apps/hero3-android/` + `shared/` (KMM commonMain)
2. `shared/commonMain/` 에 Hero3 의 Scene/UiKit/GameView/Settings/InputController 등 (~30 클래스)
3. `expect/actual` 추상화: Settings, AssetReader, Locale
4. `android.graphics.Canvas` → Compose Multiplatform `Canvas` 마이그레이션
5. Hero4 게임 콘텐츠를 같은 엔진 위에 마운트 — `games/hero4/` 안의 자산/시나리오를 `apps/hero4-android/MainActivity` 가 읽어 `GameView` 마운트

**예상 시간**: 2~4주 (가장 큰 리팩터링).

**위험**:
- Hero3 가 현재 사용자 검증된 빌드 — 분리 전 git tag 권장 (`v0.1-pre-kmm`)
- Canvas API 마이그레이션 시 게임 화면이 일시적으로 깨질 수 있음. 단계적 진행 (한 Scene씩 commonMain 으로 이전 + 검증)

### D. Phase D — iOS 출시 (Phase C 와 묶임)

**4 옵션 비교** (이전 답변 정리):

| | Compose Multiplatform | LibGDX | KMM+네이티브 | Godot |
|---|---|---|---|---|
| Hero3 코드 재활용 | **~90%** | ~30% | ~50% | 0% |
| 2D 픽셀 RPG 적합 | 양호 (Skia) | 우수 | 양호 | 우수 |
| 학습 곡선 | 낮음 (Kotlin only) | 중간 | 높음 (Kotlin+Swift) | 중간 |
| 시간 비용 | ~3주 | ~6주 | ~8주 | ~12주 |

**추천: Compose Multiplatform** — Hero3 의 Kotlin/Canvas 코드와 가장 잘 호환, 1 코드베이스, 2026 시점 iOS 안정화.

**선결**:
- Apple Silicon Mac (M1+) — iOS 빌드 / 시뮬레이터 / 실기 테스트 모두 필수
- Apple Developer 계정 ($99/년)
- Phase C 완료 (commonMain 엔진)

**작업**:
1. `apps/hero3-ios/`, `apps/hero4-ios/` Xcode 프로젝트 + Swift App entry + `ComposeUIViewController(GameRoot())` 마운트
2. iOS Simulator 검증 (가상 키패드, 한국어 한글 렌더, 사운드)
3. 실기 (TestFlight) 테스트
4. App Store 제출 (게임당 별도 Bundle ID `com.hanbit.hero3` / `com.hanbit.hero4`)

---

## 🔴 외부 도구 / 데이터 필요

### E. SMAF/MMF → OGG 변환

`work/h4/extracted/SND/*_MMF` 41개 (Hero3 와 동일 Yamaha SMAF 포맷). Android `MediaPlayer` 가 SMAF 직접 지원 안 함 → OGG/MP3 변환 필요.

옵션:
1. **Yamaha SMAF SDK** (공식) — 변환 도구 제공, 라이센스 검토
2. **MIDI 추출 → 사운드폰트로 OGG 렌더** — 무료, 음색이 다를 수 있음
3. **수동 재녹음** — 가장 충실하지만 시간 비용 큼

Hero3 도 동일 보류 상태. 두 게임 동시 진행하면 효율적.

### F. iOS 출시 인프라

- Apple Developer 가입
- App Store Connect 메타데이터 등록 (게임당)
  - 카테고리: Games > Role Playing
  - 등급: Apple 등급 심사 (12+ 또는 9+ 추정)
  - 한국어 + 영어 listing 텍스트 / 스크린샷
- TestFlight beta 테스터 모집

---

## 📋 권장 진행 순서 (2026-05-18 갱신)

| # | 작업 | 자동/수동 | 시간 | 상태 |
|---|---|---|---|---|
| 1 | A4 (recon game-aware) | 자동 | 30분 | ✅ 완료 (2026-05-07) |
| 2 | A5 (`_TILE_030`) | 자동 | 30분 | ✅ 완료 (2026-05-07) |
| 3 | A3 (translation_dict game-aware + Hero4 prefill) | 자동 | 15분 | ✅ 완료 (2026-05-07) |
| 4 | DES brute-force v1 | 자동 | 1시간 | ✅ 완료 (키 미발견) |
| 4b | DES brute-force v2 | 자동 | 1시간 | ✅ 완료 (2026-05-14, 미발견) |
| 4c | DES brute-force v3 (Hero4 signature) | 자동 | 1시간 | ✅ 완료 (2026-05-18, 0 hit) |
| 4d | DES brute-force v4 (custom DES, 513k cand) | 자동 | 8분 | ✅ 완료 (2026-05-18, 0 hit) |
| 4e | `_DAT_DES` 정밀 검증 (S1[58]=2 발견) | 자동 | 30분 | ✅ 완료 (2026-05-18) |
| 4f | plaintext SCN 분석 (e0184/e0185 + CHARACTERS_H4 prefill) | 자동 | 2시간 | ✅ 완료 (2026-05-18) |
| 4g | _EXD/MAP_M_/HDAT_B 파서 | 자동 | 2시간 | ✅ 완료 (2026-05-18) |
| 4h | HDAT Group A 키 공유 확인 + Group D + OBJ 분포 | 자동 | 1시간 | ✅ 완료 (2026-05-18) |
| 4i | _MAP_M_ extras OBJ id 매핑 + SCN disassembler | 자동 | 2시간 | ✅ 완료 (2026-05-18 후속4) |
| 4j | sec[4+] event block header + op_0x01 9-byte schema + OBJ 매핑 정정 | 자동 | 2시간 | ✅ 완료 (2026-05-18 후속5) |
| 4k | CIF 117 파싱 + stride 검증 + EXD pairing + DES file pool 확장 | 자동 | 2시간 | ✅ 완료 (2026-05-18 후속6) |
| 4l | CIF frame 완전 디코드 + EGDAT 167 enemies + NPC/FT/AI plaintext 분석 | 자동 | 2시간 | ✅ 완료 (2026-05-18 후속7) |
| 4m | CIF↔catalog 한국어 이름 매핑 + EGDAT 59 types + 한글 font lookup | 자동 | 2시간 | ✅ 완료 (2026-05-18 후속8) |
| 4n | ITM 147 + GMenu/NPCUI 169 + EVENT_POP 11 + AI 통계 (500+ 한국어 텍스트) | 자동 | 1시간 | ✅ 완료 (2026-05-18 후속9) |
| 4o | NPCG→CIF 매핑 + ITEMDROP + BSDAT/ESDAT cipher prefix (system cross-ref) | 자동 | 1시간 | ✅ 완료 (2026-05-18 후속10) |
| 5 | **A2** (Hero4 Ghidra 프로젝트 셋업) | 사용자 GUI | 30분 | ⏳ **현재 1순위 차단** |
| 6 | **B-1** (DES key 발굴) | 사용자 + Claude | 1~3시간 | ⏳ A2 다음 |
| 7 | B-2 (`_PAL` secondary / `_EXD` count>1 / `_MAP_M_` section labeling 등) | 사용자 + Claude | 1~2주 | ⏳ B-1 후 |
| 8 | **A1** (대사 번역) | 자동 (API 키) | 30분 | ⏳ B-1 (DES key) 후 자동 |
| 9 | C+D 결정 (Mac/KMM 시점) | 사용자 결정 | — | ⏳ 대기 |
| 10 | C (KMM 리팩터) | Claude | 2~4주 | ⏳ Hero3 와 묶임 |
| 11 | D (iOS 출시) | 사용자 + Claude | 1주 | ⏳ 출시 인프라 |
| 12 | E (SMAF→OGG 변환) | 외부 도구 | — | ⏳ Phase D 전까지 |

### Quick start — 다음 세션에서 가장 먼저

사용자 트리거: **A2 → B-1 (Ghidra)** 또는 키 발견 후 자동 파이프라인 (위 §⚡ 카피-페이스트).
Claude (자동만): **Hero4 자동 항목 완전 종결 — 더 자동으로 진행할 게 없음**. Hero3 잔여 / Hero5 트랙 / 사용자 결정 대기.

---

## 📦 다음 세션에서 참조할 신규 산출물 (2026-05-18 세션)

### 신규 도구 (tools/)

| 도구 | 용도 | 입력 → 출력 |
|---|---|---|
| [tools/converter/custom_des_h4.py](../../tools/converter/custom_des_h4.py) | Hero4 custom DES (S1[58]=2) | key, plaintext/ciphertext (8B blocks) |
| [tools/converter/parse_h4_exd.py](../../tools/converter/parse_h4_exd.py) | _EXD 117 파일 box layout 파싱 | EXD files → exd_parsed.json |
| [tools/converter/parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py) | _MAP_M_ 97 파일 multi-section parsing | MAP files → map_extras_parsed.json |
| [tools/converter/parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py) | HDAT P000-P005 progression table 파싱 | P files → hdat_p_parsed.json |
| [tools/recon/verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py) | _DAT_DES 표준 DES 테이블 byte-by-byte 검증 | _DAT_DES → S1[58] deviation report |
| [tools/recon/analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py) | _PAL secondary RGB 의미 통계 | PAL files → pal_secondary_stats.json |
| [tools/recon/find_h4_des_key_v3.py](../../tools/recon/find_h4_des_key_v3.py) | brute-force with Hero4 plaintext signature | binary + sources → survivors |
| [tools/recon/find_h4_des_key_v4.py](../../tools/recon/find_h4_des_key_v4.py) | brute-force with custom DES | binary (513k cand) → 0 hit |

### 신규 JSON / 데이터 (work/h4/converted/)

| 파일 | 내용 |
|---|---|
| `e0185_name_table.json` | e0185 글로벌 entity catalog 87 strings |
| `exd_parsed.json` | _EXD 117 파일 파싱 (box dx/dy/w/h) |
| `map_extras_parsed.json` | _MAP_M_ 97 파일 extras (sections × records) |
| `hdat_p_parsed.json` | HDAT P000-P005 6 파일 (entries × main_values) |
| `pal_secondary_stats.json` | _PAL 5,724 entries 통계 |

### 신규 문서

| 문서 | 내용 |
|---|---|
| [docs/h4/formats/scn.md](formats/scn.md) | SCN bytecode 구조 추론 (e0184/e0185 plaintext 기반) |
| `formats/exd.md` (갱신) | _EXD box layout count=1 케이스 완전 풀이 |
| `formats/map.md` (갱신) | extras multi-section 구조 |
| `formats/hdat.md` (갱신) | Group A 키 공유 + Group B layout + Group D 풀림 |
| `formats/bm-tile-obj.md` (갱신) | OBJ 그룹 분포 |

---

## 🚧 의도적으로 미해결로 둔 것

- `OBJ/{000,001,002}/` 247 single-frame BM 의 인덱스 의미 — PNG 변환은 됐으나 무엇을 가리키는지 (지역별? 이벤트별?) Phase B 에서 _MAP_M_ extras 와 같이 풀릴 가능성
- HDAT entry layout — 그룹 분류만. 게임 wiring 단계에서 정확한 의미 필요 시 Phase B 확장
- Hero5 별도 트랙 — `docs/h5/PROGRESS.md` 참조. Hero3+Hero4 안정화 후
