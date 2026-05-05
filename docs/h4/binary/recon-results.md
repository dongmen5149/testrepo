# `client.bin387872` 정찰 결과 (Hero4)

566,408 byte ARM Thumb native binary. Hero3 의 `client.bin64000` (735 KB) 동일 아키텍처지만 다른 빌드.

## 자동 정찰 (이미 완료)

```bash
HERO_GAME=h4 python tools/recon/extract_strings.py     # ASCII/EUC-KR 8,167개
HERO_GAME=h4 python tools/recon/find_f81f.py           # 0xf81f literal 10 위치
HERO_GAME=h4 python tools/recon/disasm_thumb.py        # 첫 256 byte + LDR PC-rel 인덱스
HERO_GAME=h4 python tools/recon/find_base.py           # GOT base 후보 (Hero3 TARGETS 라 noise)
```

GUI 분석 가이드: [`../ghidra-guide.md`](../ghidra-guide.md).

## 발견 1: 자산 로더 path strings

게임의 모든 자산 path 가 string constant 로 binary 안에 명시되어 있어 **디스어셈블 없이도 자산 로딩 흐름을 파악** 가능. 각 string 은 자산 로더 함수의 sprintf 인자.

```
/H4/CIF/_H_%03d_CIF             /H4/PAL/_H_%03d_PAL
/MAP/M/_MAP_M_%03d              /MAP/SC/e%04d_scn  /MAP/SC/n%04d_scn
/MAP/EFFECT/_EVT_EFF_%d_CIF     /MAP/EFFECT/_EVT_EFF_BM
/CM/_MMENU_CHAR_%d_BM           /CM/_MMENU_CHAR_%d_CIF
/CM/_MMENU_BM                   /CM/ENDING_%d_BM
/CM/GRADE_BM                    /CM/GRADE_V_BM
/SND/BGM_%02d_MMF               /SND/EFF_%02d_MMF
/ITM/DAT/_ITM_%02d_DAT          /ITM/BASIC_SM_DAT
/NPC/_QUEST_%d_DAT              /NPC/PROBABILITY_DAT
/NPC/_NPCG_DAT                  /NPC/NAME_DAT
/NPC/FACE_0_BM                  /NPC/FACE_0_CIF
/NPC/NPCUI_ARMSSHOP_DAT_%d      /NPC/NPCUI_GUARDIANSHOP_DAT
/NPC/_NPCUI_SHOP_DAT_%d         /NPC/_NPCUI_COMBINE_DAT_%d
/OBJ/SPR/_OBJ_SPR_%03d_BM       /OBJ/SPR/_OBJ_SPR_%03d_CIF
/GMenu/_GMENU_TXT               /GMenu/_GMENU_SUB_TXT
/GMenu/_GMENU_COMM_BM           /GMenu/_GMENU_ONLY_BM
/GMenu/_NPCUI_TXT
/tdf/_tdf_MENU_TXT              /tdf/TITLE_BM
/DAT/_DAT_DES                   /l/_LOGO
/NPC/_EVENT_POP_TXT
```

## 발견 2: 세이브 파일 (RecordStore 4개)

```
./Hero4OptionSave              # 옵션 (BGM 볼륨, 언어 등)
./Hero4GameSave                # 메인 게임 진행
./Hero4SlotSave                # 슬롯 메타 (1/2/3 슬롯)
./Hero4SmsAgree                # SMS 약관 동의 (한국 통신사 요구)
```

Hero3 의 `P/` 폴더 세이브와 다른 이름 → Hero4 가 새 세이브 시스템. 어차피 리메이크에서 세이브 호환 X 결정이라 무관.

## 발견 3: 키 에러 메시지

```
====> frameBuf is NULL                  ← Hero3 와 동일 메시지 (같은 한빛 엔진)
====> Alpha Palette Index Not Found     ← _PAL 의 alpha 처리 분기 단서
NOTREADY / READY
```

`frameBuf is NULL` 가 Hero3 와 정확히 같다는 것은 **두 게임이 같은 한빛 내부 엔진의 진화형** 임을 증명. Hero4 의 디코더 함수 분석 결과가 Hero3 에 그대로 적용 가능 (이미 0x0c BM 디코더에서 검증됨).

## 발견 4: WIPI/JLet API 임베드

```
org/kwis/msp/lcdui/JletEventListener
org/kwis/msp/lcdui/EventQueue
(III)V+notifyEvent
(Lorg/kwis/msp/lcdui/JletEventListener;)V+addJletEventListener
p()Lorg/kwis/msp/lcdui/EventQueue;+getEventQueue
(III)V+notifyPluginEvent
```

`org/kwis/msp/lcdui` = **WIPI** (한국 무선 인터넷 플랫폼) 의 JLet API. Hero4 ADF 메타에는 `MClass:Clet` 으로 표기되어 있지만, 바이너리는 **Clet (SKT GVM) + WIPI (KTF) 모두 호환** 되도록 빌드. 한 번의 게임 코드로 양 통신사 출시.

## 발견 5: 0xf81f magenta 상수 (10 위치)

```
0x002390  0x0400f81f      0x004d94  0x1c04f81f
0x00a5c0  0x0000f81f      0x016a94  0xf81ff7fd
0x02ce10  0x2201f81f      0x0442e0  0x1c04f81f
0x05c8e4  0x1c30f81f      0x062124  0x9a0af81f
0x07ff1c  0x2800f81f      0x0853d0  0xfffff81f
```

0x0a5c0 의 `0x0000f81f` 가 가장 자연스러운 단독 magenta constant. 모든 0xf81f 사용은 LDR PC-relative literal pool 통해 (MOVW Rn, #0xf81f 인스턴스 0개).

## 발견 6: 게임 텍스트 키워드

```
Skill / |SkillPoint        Menu / NPC
NOTREADY / READY
```

UI 어휘. Hero3 i18n 인프라 (`tools/i18n/translation_dict.py`) 와 같은 방식으로 영어 매핑 가능.

## GOT base 식별 (사용자 GUI 작업 필요)

`tools/recon/find_base.py` 는 Hero3 string offset 을 TARGETS 로 사용하므로 Hero4 에는 noise. Hero4 GOT base 추정에 필요한 작업:

1. extract_strings 결과에서 위 path string 들의 file offset 메모 (예: `0x086d6c: '/H4/PAL/_H_%03d_PAL'`)
2. `tools/recon/find_base.py` 의 `TARGETS` 를 Hero4 offset 으로 교체
3. 또는 Ghidra GUI 에서 frameBuf is NULL string xref 추적

자세한 내용: [`../ghidra-guide.md`](../ghidra-guide.md).

## 자산 로더 함수 식별 우선순위

Phase B Ghidra 분석 시 다음 string xref 부터:

| String | 풀리는 미해독 |
|---|---|
| `/H4/PAL/_H_%03d_PAL` | _PAL 의 secondary RGB 의미 (alpha mask vs 그림자) |
| `/H4/EXD/_H_%03d_EXD` | _EXD payload entry struct |
| `/MAP/M/_MAP_M_%03d` | _MAP_M_ extras 영역 (NPC/exit/event) |
| `'frameBuf is NULL'` | BM 디코더 진입점 (이미 0x0c 풀림, 추가 검증) |
| `'Alpha Palette Index Not Found'` | _PAL alpha 분기 (위와 연결) |
| `/HDAT/_H_P*`, `/HDAT/_H_PS*` | HDAT entry struct |

## 추가 자동 정찰 (옵션)

`tools/recon/find_xrefs.py`, `find_pic_xrefs.py` 는 Hero3 string offset 을 TARGETS 로 사용. Hero4 에 의미 있게 돌리려면:

1. extract_strings 결과 JSON 출력 추가
2. 파일 path string 들의 offset 추출
3. `find_xrefs.py` 의 TARGETS 를 그 offset 으로 교체
4. xref 위치 → 자산 로더 함수 진입점 후보

이건 Phase B 시작 전 사용자 시간 여유 있을 때 자동화 가능.
