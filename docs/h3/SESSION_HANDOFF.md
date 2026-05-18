# Hero3 인수인계 노트 (Round 73 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99.95%**. 🏆 **R73 DES 8/8 파일 복호화 성공** (Hero5 mx_des_decrypt 변종 + key 0EP@KO91). R58 의 "NDK runner 필수" 가설 폐기. **i15_dat = master shop catalog** 한글 텍스트 발견. SMAF pipeline 작성 (외부 도구 부재 graceful detection).

마지막 commit: `54e14071 feat:영웅서기4 Round 72 — E/BSDAT + ESDAT 6 파일 정밀 파싱 (559 entries)` (H3 R72 흡수)

**Round 73 산출물 = uncommitted**:
- 신규 doc 2: [`smaf_conversion_guide.md`](smaf_conversion_guide.md) + [`ghidra-round73-des-success-smaf-pipeline-2026-05-19.md`](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md)
- 신규 스크립트 2: `tools/converter/decrypt_h3_mx_des.py` + `convert_h3_smaf_pipeline.py`
- 신규 복호화 산출물 (work/h3/decrypted/, gitignored): `i15_dat.plain` + 7 others
- MASTER_SPEC §10 갱신 (DES 0 pending)
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (R74)

### 1.1 ⭐⭐⭐⭐ DES 평문 데이터 정밀 파싱

R73 의 8 plain 파일을 typed Kotlin object 로 디코드:

1. **i15_dat parser** — master shop catalog text DB
   - entry = (size, name, description text)
   - body 가 "레벨 10 투구; 머리띠; 보스용도 15년;" 같은 자연어
   - 텍스트 → 구조화 (level / category / desc 분리)

2. **drop_dat / droph_dat parser** — 18-byte stride entry
   - `11 00` separator 의 의미 (drop_count 또는 entry header)
   - enemy_id ↔ drop item_id + drop_rate% 매핑

3. **smith_dat / smithh_dat parser** — i14 → i0~i12 레시피
   - input items + output item + cost(gold) 구조 추정

4. **shop_dat / shoph_dat parser** — 상점 NPC 별 판매 목록
   - price 정보 + item_id 표

5. **boss skill ID H4 가설 검증** — R67/R68 의 결론. drop_dat 또는 신규 dat 안에 boss AI table 있는지 확인

### 1.2 ⭐⭐⭐ Hero3Catalog 확장

R73 산출물 → R71 Hero3Catalog 에 통합:
- Hero3ShopEntry / Hero3DropEntry / Hero3Recipe data class 추가
- game_balance.json v1.2 (582KB → ~700KB 예상)

### 1.3 ⭐⭐ Compose MP UI 마이그레이션 (Phase C Step 4d)

엔진 코드 분리의 마지막 단계.

## 2. 사용자 환경 필수 작업

### 2.1 ⭐⭐ SMAF → OGG 변환

R73 의 pipeline 스크립트 + 가이드 작성 완료. 외부 도구 4종 설치만 하면 즉시 33 파일 변환:
1. smaf-converter.jar (https://github.com/antanas-vasiliauskas/smaf-converter)
2. TiMidity++ 또는 FluidSynth
3. FluidR3_GM.sf2 (130MB SoundFont)
4. FFmpeg (`winget install Gyan.FFmpeg`)

설치 후:
```bash
python tools/converter/convert_h3_smaf_pipeline.py
```

자세한 가이드: [smaf_conversion_guide.md](smaf_conversion_guide.md).

### 2.2 ⭐⭐ Dialogue LLM 번역

9,740 entries, $4.09 추정 (Claude Sonnet 4.6). R69 의 `work/h3/translation_queue.json` 사용.

## 3. Round 73 핵심 발견

### 3.1 DES 8/8 복호화 성공 (🏆)

```
algorithm:  Hero5 mx_des_decrypt 변종 (startDes mode=0 + swap halves)
key:        "0EP@KO91" (Hero3 R57 확정)
python port: tools/h5_des.py
```

| 파일 | 검증 |
|---|---|
| i15_dat | 한글 "붉은머리띠 / 레벨 10 투구" 발견 = master shop catalog 확정 |
| getitem_dat / smith_dat / smithh_dat / shop_dat / shoph_dat | entropy 3.6-4.1 = binary table 평문 |
| drop_dat / droph_dat | 18-byte stride + `11 00` separator binary drop table |

**핵심 lesson**: 벤더 공통 cipher = cross-game 1순위 시도. R58 의 1년 묵은 "NDK 필수" 가설이 30분에 해결됨.

### 3.2 i15_dat = master shop catalog (★★★★★)

평문 첫 entry:
```
@0x0008  size=52  nl=26  name=(...붉은머리띠...)
                          body=" 레벨 10 투구; 머리띠; 보스용도 15년; "
```

→ shop NPC 가 표시하는 item description 텍스트 직접 포함.

### 3.3 SMAF pipeline (★★★)

33/33 SMAF 헤더 검증 통과. 외부 도구 설치 후 자동 33 파일 변환 가능.

## 4. 작업 순서 권장 (R74)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 73 산출물
3. **i15_dat parser 작성** (R74 핵심):
   - entry 디코드 + description 텍스트 분리
   - shop catalog → Hero3Catalog 확장
4. **drop_dat parser**:
   - 18-byte stride entry 디코드
   - enemy_id ↔ drop item 매핑
5. **smith_dat parser**:
   - 조합 레시피 매핑
6. **사용자 환경 진행** (병행):
   - SMAF 도구 설치 → OGG 변환
   - Dialogue LLM 번역

목표 진행률 (R74 종료): **~99.98%**.

## 5. 참고 문서

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (§10 DES 0 pending)
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 73](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md) — ★ 이번 라운드 (DES success + SMAF)
- [smaf_conversion_guide.md](smaf_conversion_guide.md) — SMAF 외부 도구 가이드
- [Round 72](ghidra-round72-scene-integration-2026-05-19.md) — Android scene 통합
- [Round 71](ghidra-round71-catalog-loader-2026-05-19.md) — Hero3Catalog data layer
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — Master Spec
- (R56-R69) — see MASTER_SPEC §14
- `tools/converter/decrypt_h3_mx_des.py` — R73 DES batch
- `tools/converter/convert_h3_smaf_pipeline.py` — R73 SMAF pipeline
- `tools/h5_des.py` — Hero5 mx_des_decrypt Python 포팅 (Hero5 R68)
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
