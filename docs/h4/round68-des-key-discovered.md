# Hero4 Round 68 — DES key 발견, 350+8 파일 일괄 복호화 완료 (자동)

> **세션**: 2026-05-18 Round 68 (Hero4 자동 트랙)
> **이전 상태**: 자동 영역 47건 종결, DES key 만 차단 (Phase B Ghidra 필요)
> **돌파**: Hero3 R57 의 `0EP@KO91` 발견 + Hero5 `mx_des_decrypt` 변종 포팅 자료 cross-game 분석으로 **Ghidra 없이 키 발견**

## TL;DR

**Hero4 DES key = `J@IWO8N7`** (8-byte ASCII = `4a 40 49 57 4f 38 4e 37`)
**Cipher = Hero5 `mx_des_decrypt`** (S1[58]=2 + startDes mode=0 swap halves + reversed subkey)

검증:
- SCN sentinel `3b7af9a427907dac` → `0000000000000000` (8-byte zero, 38회 sentinel 전부 일치)
- `e0001_scn` 복호화 → `수레바퀴섬 / 주둔지 / 티르 / 깨워주러 왔더니 아직까지 자고 있으면...`
- `e0100_scn` 복호화 → `이름없는섬 / 비밀통로 / 크래드의 / 보스룸에서는 / 세이브를`
- SCN 348 + HDAT-A 8 + 2 plaintext = **358 파일 한 번에 복호화**
- dialogue corpus: 4,078 garbage → **35,752 entries (15,127 unique)** — 8.76x 증가

## 결정적 분석 경로

### 1. Hero3 R57 (`docs/h3/ghidra-des-system-and-dat-paths-2026-05-18.md`)

```
binary 0xac584: "/dat/des_dat"  (path string)
binary 0xac594: "0EP@KO91"      (8-byte DES key ASCII, 위치 = string + 0x10)
```

→ 한빛소프트는 binary 안에 DES path string + 8-byte key 평문을 path 직후에 배치.

### 2. Hero4 등가 패턴 (이미 발견되어 있던 단서)

```
binary 0x86ecc: "/DAT/_DAT_DES"
binary 0x86edc: "J@IWO8N7L0E7E"  (13 char ASCII, 위치 = string + 0x10)
```

→ 한빛 패턴 동일. 13 char 중 **첫 8 byte = key**.

### 3. Hero5 `tools/h5_des.py` (libHeroesLore5.so 포팅)

```python
def mx_des_decrypt(data: bytes, key: bytes = b"0EP@KO91") -> bytes:
    subkeys = key_schedule(key)
    subkeys_rev = list(reversed(subkeys))   # ← Hero4 v4 누락 부분
    n = len(data) // 8
    out = bytearray()
    for i in range(n):
        out += start_des_block(data[i*8:(i+1)*8], subkeys_rev, mode=0)
        # mode=0 = "swap halves" before Feistel rounds
    return bytes(out)
```

→ S1[58]=2 만 수정한 v4 `custom_des_h4.py` 는 **swap + reversed subkey 누락** → 0 hit.
→ Hero5 의 `mx_des_decrypt` 가 정확한 한빛 변종.

### 4. v5 brute-force (`tools/recon/find_h4_des_key_v5.py`)

curated 키 후보 + Hero3 binary sliding window 로 mx_des_decrypt 검증. 결과:

| key 후보 | 검증 ciphertext | 결과 | 결론 |
|---|---|---|---|
| `0EP@KO91` (Hero3/Hero5) | scn_last_x38 | 랜덤 | Hero4 는 다른 키 |
| **`J@IWO8N7`** | scn_last_x38 | `0000000000000000` ★ | **HIT** |
| **`J@IWO8N7`** | scn_last_x11 | `2100000000000000` ★ | sentinel + opcode |
| **`J@IWO8N7`** | scn_first_x8 | `010101560000ffff` | SCN signature 3/5 매칭 |
| `@IWO8N7L` (offset 1) | 모두 | 랜덤 | 첫 8 byte 만 유효 |
| `IWO8N7L0` (offset 2) | 모두 | 랜덤 | |

→ **`J@IWO8N7` 단독 sentinel block 100% NULL** → 키 결정.

## 자동 파이프라인 결과

```bash
# 1. SCN 350 + HDAT-A 8 = 358 파일 복호화 (~30초)
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key 'J@IWO8N7' --batch

# 2. e0184/e0185 plaintext 복원
cp work/h4/extracted/MAP/SC/e0184_scn work/h4/decrypted/SC/
cp work/h4/extracted/MAP/SC/e0185_scn work/h4/decrypted/SC/

# 3. 복호화 결과를 extracted 로 swap (convert_all.py 가 extracted 만 봄)
cp -r work/h4/extracted/MAP/SC work/h4/extracted/MAP/SC.encrypted_backup
cp work/h4/decrypted/SC/* work/h4/extracted/MAP/SC/

# 4. 자산 재변환 + corpus 빌드
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/converter/prepare_android_assets.py \
    work/h4/converted apps/hero4-android/app/src/main/assets
```

## 산출물

### 도구 수정

| 파일 | 변경 |
|---|---|
| `tools/converter/decrypt_h4_scn.py` | mx-des (default) / std-ecb / std-cbc 3 mode. `--input_dir` 옵션 추가. plaintext SCN auto-skip |

### 신규 도구

| 도구 | 용도 |
|---|---|
| `tools/recon/find_h4_des_key_v5.py` | mx_des_decrypt 변종 + curated 키 + Hero3 binary cross-game brute-force |

### 데이터

| 파일 | 내용 |
|---|---|
| `work/h4/decrypted/SC/*_scn` | 350 파일 (348 decrypt + 2 plaintext) |
| `work/h4/decrypted/HDAT/_H_{BH,BS,SA,SS,S000-S003}` | 8 HDAT-A 파일 |
| `work/h4/converted/dialogue_corpus.json` | **35,752 lines / 15,127 unique** (이전 4,078 garbage 대비 8.76x) |
| `work/h4/converted/dialogue_top_texts.json` | top 200 빈도순 |
| `apps/hero4-android/app/src/main/assets/` | 496 PNG + JSON 재배포 |

### Top dialogue 빈도 검증

```
[x347] '퀘스트'  [x176] '있는'   [x175] '입수'   [x171] '완료'
[x127] '무슨'    [x122] '어떻게' [x110] '내가'   [x102] '하지만'
[x101] '그런'    [x94 ] '티르'   [x86 ] '그리고' [x84 ] '그럼'
```

티르 (Tír) = 주인공 이름 (켈트 신화 Tír na nÓg 의 Tír), 퀘스트/입수/완료 = 게임 시스템 동사.

## 영향

### 즉시 해제된 차단

- ⛔ A1 (대사 영어 번역) → ✅ 가능 (Claude Haiku, ~$0.30, ~30분)
- ⛔ HDAT-A 8 파일 (BS/BH/SA/SS/S000-S003) entry layout 분석
- ⛔ ITM/DAT, E/BSDAT, E/ESDAT, NPC scripts, FR/ 등 ~ 50+ 파일 추가 복호화 가능

### 보존된 미해결

- ITM/DAT 16 + E/BSDAT 3 + E/ESDAT 3 + NPC ~7 + FR ~5 ≈ **30~40 파일은 같은 키 cross-ref 미검증**.
  cipher prefix 통계 (PROGRESS.md known-ciphertext leverage) 로는 SCN/HDAT-A 와 sentinel 공유 → 같은 키 거의 확실.
  `tools/recon/scan_h4_des_files.py` 결과 **107 confirmed + 141 likely**. Round 69 작업.

## Round 69 권장

1. ⭐ **남은 DES 파일 일괄 복호화** (E/, ITM/DAT/, NPC/ 등) — `--input_dir` 으로 `tools/converter/decrypt_h4_scn.py` 재사용
2. ⭐ **HDAT Group A 8 파일 entry layout 분석** — battle skill (BH/BS), shop (SA/SS), zone scripts (S000-S003)
3. **A1 영어 번역** — translate_dialogues.py (system prompt 이미 game-aware)
4. SCN bytecode 완전 정밀화 — opcode 0x01/0x0c/0xff sep 외 32+ 신규 byte 패턴 분석 (해독 후 새 SCN 자료로)
5. Phase C (KMM 분리) 또는 Hero3/Hero5 트랙 결정

## 메타 — 왜 v1-v4 가 실패했는가

- v1 (ASCII brute force): 8-byte ASCII window 인 `J@IWO8N7` 는 candidate set 에 있었지만, **표준 DES** 검증 → 0 hit
- v2 (전체 binary sliding): 같은 후보 들어있었지만 **표준 DES**
- v3 (signature + 표준 DES): 같은 후보, 같은 검증
- v4 (custom DES S1[58]=2): S1 변형은 적용됐지만 **swap+reversed subkey 누락** → 같은 후보가 또 0 hit

**근본 원인**: Hero4 v1-v4 가 cipher 변종을 **부분만** 모델링 (S1 1 byte). Hero5 의 풀 변종 (mx_des_decrypt) 적용 후 즉시 발견.

**lesson**: Hero3+Hero4+Hero5 같은 vendor 인 경우, **암호 변종은 반드시 공유 확인 1순위**. Hero5 분석 결과를 Hero4 에 적용하는 cross-game 분석이 Ghidra 없이도 키 발견을 가능하게 함.
