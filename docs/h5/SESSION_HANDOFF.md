# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-10 (Round 36 — 4 element 시스템 구조 식별. **V[136..143] = 4 elements × 2 (atk/def) 8 fields**. V[144]/V[145] = current element bonus (V[89]/V[93] 으로 선택, +30%/level). V[151]/V[152] = magic stat pair (skill slot 별).)

---

## 🚀 다음 세션 빠른 시작 (한 줄)

**"Round 37 시작 — 한글 비트맵 폰트 매핑 (P5)"** 으로 진행 (capstone+lief 로 581 glyph index ↔ Unicode 추출).
또는 다른 미해결 항목 (Mission 시스템, scn opcode 미구현 cross-check 등).

새 클론 환경이라면 먼저 [§ 빠른 재개](#빠른-재개-1-커맨드--환경-복원) 의 단일 커맨드로
환경 복원 (`python tools/h5_extract_pipeline.py`).

---

## 30초 요약 (Round 36 시점, 2026-05-10)

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 P1~P4 + DES 해독 + Formula VM 통합 + Item struct 분석** 완료.
Title → ClassSelect → Demo 흐름 동작하는 Godot 4 프로젝트 (`apps/hero5-godot/`).

**verify_godot_project.py: 0 errors / 0 warnings.**

### Round 6~36 누적 발견 (요약)

| 영역 | 핵심 결과 |
|---|---|
| Formula VM stat field | V[58]=level, V[60..63]=str/dex/**con/int** (R11 정정), V[69]=SP, V[70]=CP |
| V[111..116] secondary | atk_growth_coef + 5 secondary stat = **근접명중/장거리명중/회피/방패방어/크리티컬** (R11 buildup csv 매핑) |
| V[118..133] buff/temp bonus | str/dex/con/int bonus + 5 buff slot (EXP%/SP감소%/CP충전/쿨타임/포션효과 — R12) + def_red% + atk%bonus + 5 secondary bonus |
| V[134..148] equipment | element bonus 영역, calc_sk[2003]/[2004] 가 EquipItem stat 합산 → cache |
| V[151..155] derived | V[151,152]=magic stat (둘 다 INT, R12 정정), V[153]=con, V[154]=str, V[155]=max_sp |
| V[168..182] ItemBase | V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor (R13) |
| EquipItemInfo struct | +0x14=item_subtype, +0x155=class subtype code, +0x15d=level_limit, +0x15f & 0x1f = 5-class mask (W/R/G/K/S, R16), +0x165..+0x167=refine_count/sub/locked (R17), +0x168..+0x16d=6 socket slots |
| LoadItemTable csv layout | 모든 카테고리 공통 base (item_id u32 + sub_record + sub_record_data 256B memcpy). EquipItem 만 sb-area (struct +0x150..+0x167) 추가 (R14/18) |
| cat 12-16 추가 fields | BattleUseItem +0x134..+0x137 (4 byte ✓ csv 매칭), OrbItem +0x134..+0x135, MixBookItem +0x134..+0x140 (R19) |
| slot_16/17 SkillBookItem | **+0x134=class_id**, +0x135=skill_index, **+0x136=skill_level** (LV1..7 정확 매칭 ✓), +0x137=required_level. slot_16 = Warrior(0)+Rogue(1), slot_17 = Gunslinger(2)+Knight(3). HERO::IfLearnSkill 의 (class_id/2)+16 공식 (R21) |
| slot_18 CashItem | jumptable case 18 → **0xa3b38 별도 path** (R19 가설 정정), 2 byte ext +0x134/+0x135 (R20) |
| 소서러 (class_id=4) 미구현 stub | c_csv_skill_04 부재 / SORCERER class object 없음 / class_stats unk1..14=1 placeholder. 출시 빌드 = 4 클래스 only. cat 18 매핑은 dead code (R22) |
| slot_11 BattleUseItem 4 byte 의미 | +0x134=effect_type (91=HP/90=SP/87=buff/92=마석/19=test/0=무효), +0x135=success_rate%, +0x136=effect_value (HERO+0x300 u16), +0x137=duration (HERO+0x302 s16). HERO::BattleUseItem 분석 (R23) |
| SLOT_META 전면 정정 | slot_12=orb (이전 scroll), slot_13=mix material (이전 orb), slot_15=mix_book recipe (이전 material_2). record 이름 + ext 길이 cross-check 결과 (R23) |
| val_15f csv vs runtime 용도 분리 | csv: lower 5 bit = class_mask + upper 3 bit = tier_flags. runtime: SetItemOption (0xa0ff8) 가 option_type code 로 overwrite. GetRelieveLevelLimit (0xa835c) 의 cmp #0x6c='l' 는 runtime option (R24) |
| val_15f upper 3 bit 실증적 의미 | upper=0 (170, legendary 보스/named) / =1 (248, rare 중급) / =3 (9, gem 보석 헤어핀/서클릿) / =7 (362, common 상점 기본) (R24) |
| slot_15 mix_book recipe 13 byte 구조 | 1~3 ingredients (cat/idx/count) + result (cat/idx) + success_rate%. 쿠킹/포션 합성/재료 정제/무기 제작 카테고리. 116 records 모두 검증 (R25) |
| **강화 stat 보너스 식 (Formula VM)** | **id=35: clamp((V[184]+V[187]),0,9999)**, **id=36: clamp((V[185]+V[187]),0,9999)**. V[184]=item+0x156=stat_a, V[185]=item+0x158=stat_b, V[187]=item+0x166=sub_count. **refined_stat = base + sub_count** (R26) |
| **EquipItem stat 의미 (slot 별)** | weapon (slot 0-3): atk_min/atk_max (a<b), shield (slot 9): phys/mag def (a≈b), helmet/boots/accessory: primary/secondary def (a>b), spirit (slot 10): 별도 mechanism (a,b ≤1) (R26) |
| **ApplyItemRefine 5-case jumptable 의미** | case 0=큰성공 (refine_count++, sub+=2), case 1=성공 (refine_count++, sub+=1), case 2=재료소비 (no change), case 3=lock (+0x167=1 영구 잠금), case 4=destroy (item 파괴). refine_count cap 10 (R26) |
| **ApplyOrbCombine orb socket mechanism** | item +0x168 = orb_count (V[188]), +0x169..+0x16d = 5 socket bytes. 39 orb 종 (3 그룹 × 13). sub_orbs=9 면 강도 multiplier 2x. Mission::CheckOrbCombine 호출로 mission 진척 (R26) |
| **NewDropItem signature + +0x15f arg position** | `NewDropItem(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 12 args. 7번째 arg (5번째 s8) = +0x15f tier_flags. cat ≤ 10 (EquipItem) 만 strb 발생 (R27) |
| **Monster drop_table 13-byte entry** | Monster::SetDropItem 내 drop pool 이 13 byte/entry. 4 가지 drop type (idx ∈ [0..3]) × 13. byte 데이터에서 NewDropItem 의 +0x15f arg 직접 전달 — csv 의 tier_flags 분포를 따름 (R27) |
| **+0x15f tier_flags csv↔drop 일관성** | csv val_15f = (class_mask | tier_flags<<5). drop_table 이 csv 분포 그대로 전달. 즉 Round 24 의 실증적 라벨 (legendary/rare/gem/common) 이 보스/일반 monster drop 로직에서도 의미 있게 사용됨 (R27) |
| **ApplyNormalMix (NPC blacksmith)** | MixSmithTableInfo* 별개 데이터 (csv slot_15 와 다름). struct layout col-major: +0x11c (option_grade), +0x11d-1f (cat[3]), +0x120-22 (idx[3]), +0x123-25 (count[3]), +0x126-128 (result_cat/idx/sr) (R28) |
| **ApplySpecialMix (csv slot_15 recipe)** | GetItemTableInfo 로 csv slot_15 데이터 직접 사용 + Mission::CheckMissionMix. struct +0x135-140 col-major (csv 13 byte transpose 후) (R28) |
| **mix_book recipe csv↔struct layout** | csv 파일 = row-major (per-ing: cat,idx,count) = 사용자 관점 정확 (R25). struct memory = col-major (cat[3], idx[3], count[3]) — LoadItemTable transpose. 두 해석 모두 정당, parse_mix_book_extra row-major 객체 그대로 유지 (R28) |
| **ApplyItemCompose (option 결합)** | 두 EquipItem (둘 다 grade ≤ 2 만) → option pair (+0x15f/+0x162, +0x160/+0x163) 결합. gv+0x1444+0x198+fp*6 = 결합 prob 테이블 (R28) |
| **ApplyItemDecompose (분해)** | option_grade-based prob (gv+0x1444+0x1b8+grade*10, 4 s16 thresholds × 5 grade). 5-way: money refund (default) / mix material / potion / 기타 (R28) |
| **gv+0x1444 sub-struct prob 테이블 영역** | +0x130-198 강화 prob (R17), +0x198-1b8 결합 prob (R28), +0x1b8-1f4 분해 prob (R28), +0x1f4-208 orb prob (R26) (R28) |
| **droptable.dat 식별** | VFS index 18, 3278B = 252 entries × 13B = 63 monsters × 4 drop tiers. byte 0=0x0b cat (potion only), byte 1=0, byte 2=monster_idx, byte 3=drop_tier (0x0e..0x11). LoadItemDropTable → ItemTable+0x214 (R29) |
| **drop_table = potion drop pool only** | ❌ Round 30 정정: 사실은 EquipItem drop pool (R30) |
| **droptable.dat = EquipItem drop pool (정정)** | byte 11 = NewDropItem cat arg (5/6/7/8/0xff). 0xff = default → generic EquipItem (376B alloc). Monster progression: 저급 monster=default, 강함=specific cat (helmet/boots/accessory) (R30) |
| **byte 0 = constant marker** | 0x0b 일관 (format version 추정), cat 아님. byte 11 가 진짜 cat (R30) |
| **register propagation: byte 0xb → r3** | 0xbcb0c ldrb r8 [r3,ip] → 0xbcc08 sp+0x40 → 0xbcc20 ldr ip → 0xbcc38 asr r3 (signed s8). NewDropItem r3 = signed byte 0xb (R30) |
| **droptable.dat multi-tier drop 시스템** | Monster +0x254..+0x26c 의 5단계 threshold + Rand(0,0xffff) 으로 cat 결정 path 선택. byte 7 = default path cat (0..9 모든 EquipItem), byte 11 = highest tier path cat (helmet/boots/accessory). mid paths = Rand(0,9). cat 4=armor 누락 = Sorcerer stub cross-confirm (R31) |
| **Monster progression 검증** | Monster 0=accessory only, Monster 62=weapon/shield/boots common + rare accessory bonus. 게임 difficulty 와 정확 일치 (R31) |
| **MixSmithTable 데이터원 식별** | /c/csv/smith_0/1/2.dat (각 96 entries × 300B/entry = 288 NPC blacksmith recipes). smith_0=accessory craft, smith_1/2=weapon craft. 모두 75% success rate. HERO+0x1d00 = MixSmithTable_ptr (R32) |
| **mix_book vs smith_table 비교** | 둘 다 13-byte recipe layout 공유. mix_book (slot_15, 116) = ApplySpecialMix + Mission, smith_table (288) = ApplyNormalMix (NPC blacksmith UI). success rate 다름 (mix_book 90-100% vs smith 75%) (R32) |
| **enemy_g.dat layout 정밀 분석** | Per-enemy 240B (Map+0x1f0+idx*0xf0). file +4..0xf (12B u8 markers), +0x10..0x1b (6 u16 = HP/MP/ATK/DEF/EXP/Gold), +0x1c..0x2a (15B u8 drop/level), +0x2b 이후 (4 skill blocks × 16B). 121B file 읽음 per enemy (R33) |
| **Monster struct +0x254..+0x275 가 별도 source** | enemy_g 와 직접 매핑 X. Monster constructor 또는 game-state init 에서 set. drop chance thresholds (+0x254..+0x26c) + drop count/type/marker (+0x270..+0x275) (R33) |
| **drop 시스템의 3 데이터원** | (1) enemy_g.dat → Map+0x1f0 (HP/skills), (2) droptable.dat → ItemTable+0x214 (drop pool), (3) Monster init → Monster+0x254..+0x275 (drop thresholds) (R33) |
| **Monster::setEnemyData 발견** | 0xc1a94, 1532B. LoadRes("/c/csv/enemy_%d.dat", arg) → Monster +0x218 (name) ..+0x275 (drop). +0x254..+0x275 의 모든 writer 가 이 함수에 (R34) |
| **enemy_%d.dat 3 files (difficulty)** | enemy_0/1/2.dat 각 23190B × 166 records. 첫 record size 140B (variable). byte 0x10 만 다름 (0x16/0x2d/0x46) → 3 difficulty levels 추정 (R34) |
| **Monster 시스템의 4 데이터원 정리** | enemy_g (Map HP/skills), enemy_*.dat (Monster stat+drop), droptable.dat (drop pool), smith_*.dat (craft recipes) — 모든 Monster/Item 시스템 데이터원 식별 (R34) |
| **enemy_*.dat record byte → Monster field 정밀 매핑** | byte 0..3 → +0x22c..+0x22f (markers), byte 39..66 → +0x254..+0x26c (7 u32 drop thresholds), byte 67..72 → +0x270..+0x275 (drop count/markers), byte 73..79 → +0x276..+0x27c, byte 80+ → BATTLER stats (R35) |
| **Monster decoder + 498 records JSON** | 3 difficulty × 166 records 정확 parse. Easy drop_count=0, Normal=17-19, Hard=26-27 (게임 difficulty 시스템 검증) (R35) |
| **4 element 시스템 구조 식별** | V[136..143] = 4 elements × 2 (atk/def). id=7/8 calc_pl 의 magic atk/def total 식 = sum_elements + V[153]/2 + V[144/145]*(100+30*V[89/93])/100. V[89]/V[93] = current element index. V[151]/V[152] = magic stat pair (skill slot 별 magic damage bonus) (R36) |

### Phase 2/3 인프라 완료
- ✅ DES 변종 해독 (S1[3][10]=2), calc_*.dat MD5 검증 평문 dump
- ✅ Formula VM 186 공식 (39+19+128) 디스어셈블 + GDScript 평가기 + battle_system 통합
- ✅ gv+0x1474 sub-struct 111 fields 정확 매핑
- ✅ ItemTable / EquipItemInfo / ItemBase 구조체 layout 추출 (R13~R19)
- ✅ items.json 에 named fields 부여 (subtype, class_mask, class_label, level_limit, item_id, sub_record, val_150..val_160, refine fields)

### 직전 작업 (이어서 진행 시 시작점)
- Round 36 종료. 다음 라운드 시작점은 아래 "다음 세션 시작점" 섹션 참조.
- 가장 직접적 옵션: **한글 비트맵 폰트 매핑 (P5)** — capstone+lief 로 _midas_funcFntInvalidate
  분석으로 581 glyph index ↔ Unicode 매핑 추출. 시스템 폰트 (Noto Sans CJK KR) 로 우회 중,
  폰트 충실도 향상 only.
- 또는 Mission 시스템 분석 (Round 28 의 Mission::CheckMissionMix 호출 추적).
- ✅ **Round 6**: gv_sub 핵심 필드 정확화 (writer 분석으로 V[58]=level, V[60..63]=base_str/dex/int/con,
  V[69]=SP, V[70]=CP, V[118..121]=bonus_str/dex/int/con 확정)
- ✅ **Round 6**: visual 효과 hookup — screen_shake tween, map_tile_change highlight, narration text lookup
- ✅ **Round 7**: V[111]=atk_growth_coef, V[112..116]=secondary stat base, V[153]=stat_con, V[154]=stat_str, V[155]=max_sp 확정
- ✅ **Round 8**: V[127]=def_reduction%, V[128]=atk%bonus, V[129..133]=secondary stat bonus, V[134..148]=element/magic bonus 식별. Round 7 의 0x294/0x296 (buff descriptor) 가 Formula VM var 가 아닌 gameplay 전용 필드임을 정정 (V[125]=0x2a6, V[126]=0x2a8 별개)
- ✅ **Round 9**: ApplyBuildupEffect jumptable 자동 추출 도구 (`tools/h5_apply_buildup_disasm.py`).
  V[122..126] = 5 buff stat slot 확정 (entry type 30/31/32/34/36).
  V[125]/V[126] (0x2a6/0x2a8) 의 store target 확정.
  c_csv_class.json 의 5 클래스 V[112..116] base 패턴 추출 (워리어/로그/건슬링어/나이트/소서러).
  battle_system.gd + formula_vm.gd 에 클래스별 정확 lookup 적용.
- ✅ **Round 10**: 한글 stat label 의 .so 직접 reference 0건 확인 — 모두 VFS text/*.json 에 분산.
  `00017_488ab1c6.json` 에 status menu 의 20-stat 라벨 sequence (방어력/공격력/물리방어력/.../크리티컬저항) 발견.
  `StateInGameMenu::DrawPropertyMenu` 가 register-indirect dynamic dispatch — 정적 분석으로 stat↔cache offset 매핑 어려움 확인.
  `HERO::CalcStatusComputation` 의 24 calc 호출이 모두 `calc_sk[2003] (V[41])` + `calc_sk[2004] (V[156])` 두 공식만 사용 — 7 EquipItem slot × 2 stat + 4 spirit slot × 2 stat. V[136..148] (element bonus) 영역에 cache.
  V[112..116] 5 stat 의 한국어 라벨은 미확정 — 후보 (명중률/회피율/크리티컬/정확도/마법적중) 식별.
- ✅ **Round 11**: c_csv_buildup.json (`tools/h5_decode_buildup.py`) 의 entry type ↔ ApplyBuildupEffect type 매핑으로 **V[112..116] 5 secondary stat 라벨 확정**:
  - V[112] = 근접명중 (csv 0x14 → ABE 11 → V[129] bonus)
  - V[113] = 장거리명중 (csv 0x15 → ABE 12 → V[130] bonus)
  - V[114] = 회피 (csv 0x16 → ABE 13 → V[131] bonus)
  - V[115] = 방패방어 (csv 0x18 → ABE 14 → V[132] bonus)
  - V[116] = 크리티컬 (csv 0x19 → ABE 15 → V[133] bonus)
  5 클래스 base 패턴이 모두 합리적으로 일치 (워리어=근접명중 24, 건슬링어=장거리명중 24, 워리어=방패방어 5).
  **V[62]/V[63] = base_con/base_int 정정** (이전 int/con 매핑 오류) — buildup csv "건강+#1" → ABE 4 → V[120] = bonus_con, "정신+#1" → ABE 5 → V[121] = bonus_int.
  decode_h5_class.py / class_stats.json / class_select.gd / battle_system.gd / formula_vm.gd 일괄 정정.
- ✅ **Round 25**: slot_15 (mix_book recipe) 13 byte ext 구조 RE 완료:
  - layout: byte 0 (separator) + 3×3 byte ingredients (cat/idx/count, 0xff=unused) +
    2 byte result (cat/idx) + 1 byte success_rate %.
  - 116 records 모두 정확히 parse (이름 cross-check 검증).
  - 쿠킹 (살코기+황혼버섯 → 황혼수프가루 100%), 포션 합성 (포션 ×2 → 미들포션 100%),
    재료 정제 (엑토플라즘 ×10 → 에테르 90%), 무기 제작 (보통칼날+가죽+강철 →
    투란기어 90%) 등 카테고리화.
  - success_rate 분포 = 게임 밸런스 검증 (legendary 무기 20-22%, 일반 100%).
  - parse_mix_book_extra 가 의미있는 'recipe' 객체 부여 (이전 raw sb_extra_hex 대체).
- ✅ **Round 24**: val_15f upper 3 bit (tier_flags) 의 실증적 의미 식별:
  - **csv-time vs runtime val_15f 용도 분리** 발견 — csv 는 (class_mask + tier_flags),
    runtime 은 SetItemOption (0xa0ff8) 가 option_type code 로 완전 overwrite.
    GetRelieveLevelLimit (0xa835c) 의 `cmp #0x6c` ('l') 는 runtime option_type 비교.
    MakeItemOption (0xa10e8) 가 val_15c (option_grade) 로 SetItemOption 호출 여부 결정.
  - **items.json 789 EquipItem records 분포 분석** 으로 upper 3 bit 의 의미 추정:
    - upper=0 (170): **legendary** — 실가라스/투란기어/디바인세이버 보스 무기
    - upper=1 (248, bit5): **rare** — 중급 무기/방어구
    - upper=3 (9, bit5+6): **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔)
    - upper=7 (362, bit5+6+7): **common** — 일반 상점 (롱소드/단검 등)
  - 가설: bit5="obtainable" / bit6="gem-accessory" / bit7="common-tier".
  - parse_equip_extra 가 tier_flags + tier_label 부여 (legendary/rare/gem/common).
  - slot_4 "스태프" 1 record 가 tier=legendary + class_mask=0 (Sorcerer 전용 staff)
    Round 22 미구현 stub 사실과 cross-confirm.
- ✅ **Round 23**: HERO::BattleUseItem (0x8fd20, 536B) 디스어셈블 + SLOT_META 전면 정정:
  - slot_11 의 +0x134..+0x137 의미 확정:
    - +0x134 = effect_type → HERO[0x2fe] → CalcStatusComputation 분기
      (91=HP heal, 90=SP heal, 87=buff 보호, 92=마석, 19=test, 0=무효)
    - +0x135 = success_rate % → random(0,99) 와 cmp (모두 100 = 100% 성공)
    - +0x136 = effect_value → HERO[0x300] (u16, 회복량/buff 강도)
    - +0x137 = duration → HERO[0x302] (s16, 지속 turn)
    - SetPotionCoolTime(100) — cooldown 100 frame.
  - SLOT_META 전면 정정 (record 이름 + ext_after_sb 길이 cross-check):
    - slot_12 = orb (이전 scroll 잘못, 2 byte ext, 뇌제의오브 등)
    - slot_13 = mix material (이전 orb 잘못, 0 ext, 살코기/재료2..9)
    - slot_15 = mix_book recipe (이전 material_2 잘못, 13 byte ext, 황혼수프/포션)
  - parse_battle_use_extra 라벨 정정 (val_134→effect_type 등 의미있는 이름).
- ✅ **Round 22**: Sorcerer (class_id=4) 미구현 stub 확정 분석:
  - .so 클래스 심볼 검색 → WARRIOR / ROGUE / GUNNER / KNIGHT 4개만 존재.
    SORCERER class object 없음.
  - skill csv 검색 → c_csv_skill_00..03 (player) + c_csv_skill_05 (16 monster
    skills: 암흑탄/지옥소환/얼음폭풍/완전면역 등). c_csv_skill_04 완전 부재.
  - class_stats.json 검토 → 소서러 unk1..unk14 모두 1 (다른 클래스 6/12/18/24).
    unk0=320 (다른 1000) — 명백한 placeholder.
  - IfLearnSkill 의 (class/2)+16=18 매핑은 dead code path. slot_18 (CashItem)
    의 records 49 모두 class_id=4 없음.
  - class_select.gd UI 정정 — "소서러" → "소서러 (미구현)" 라벨 표시.
  결론: 영웅서기5 출시 빌드 = 4 클래스 only. 소서러는 향후 확장 클래스로
  계획됐으나 미구현 채로 출시.
- ✅ **Round 21**: HERO::IfLearnSkill (0x95d08, 316B) 디스어셈블 → SkillBook
  +0x134..+0x137 의 의미 정확 식별:
  - +0x134 = **class_id** (HERO 클래스 0..4)
  - +0x135 = **skill_index** (HERO::skills[] 배열 인덱스)
  - +0x136 = **skill_level** (LV 매칭 ✓ Round 20)
  - +0x137 = **required_level** (HERO+0x22d 와 cmp)
  - 공식 `(class_id/2)+16` → Warrior/Rogue=cat 16 (slot_16), Gunslinger/Knight=cat 17
    (slot_17), Sorcerer=cat 18 (slot_18 — 충돌, 별도 path 추정).
  - slot_16 도 실제 SkillBook 임이 확인 (양손베기/돌진/내려찍기 등 Warrior 스킬)
    — SLOT_META 정정 (이전 'mix_book' 잘못).
  - parse_skill_book_extra 의 라벨 정정 (val_134→class_id, val_135→skill_index,
    val_137→required_level).
  - 검증: slot_16 95 records (Warrior 48 + Rogue 47), slot_17 98 records
    (Gunslinger 49 + Knight 49). 각 클래스 정확히 10 skills × 1..7 levels.
- ✅ **Round 20**: LoadItemTable 함수 끝 영역 (0xa479c..0xa49c0) 추가 disasm —
  `tools/h5_dump_loaditem_tail.py` (`capstone.skipdata=True` 로 literal pool 통과).
  - **slot_17 (SkillBookItem) 4 byte ext** @ 0xa47c0 (jumptable case 16/17 공유).
    +0x134=skill_class (2/3), +0x135=skill_id (0..9), **+0x136=skill_level**
    (V[1..7] 이름과 정확 매칭 ✓), +0x137=required_level (monotonic).
    검증: '연속사격LV1..LV4' = (2, 0, 1..4, [1, 4, 10, 22]) — 4 byte 모두 일치.
  - **slot_18 (CashItem) 2 byte ext** @ **0xa3b38** (jumptable case 18 별도 path —
    Round 19 의 0xa47c0 가설 정정). hardcoded type 0x12=18 at +0x14, 2 byte:
    +0x134 (cash_category 0..3), +0x135 (stack/type, 255=passive 추정).
  - `decode_h5_item.py` 에 `parse_skill_book_extra` (4 byte) + `parse_cash_extra`
    (2 byte) 추가, SLOT_META[18] = "cash" 로 정정 (이전 "skill_book" 잘못).
  - items.json 검증: slot_17 98 records, slot_18 49 records 모두 추가 fields populated.
- ✅ **Round 19**: LoadItemTable 의 cat 12+ jumptable case 별 추가 fields disasm:
  - cat 12 (BattleUseItem, 0xa4060): +0x134/0x135/0x136/0x137 (4 byte u8) — csv 에서 매칭 ✓
  - cat 13 (OrbItem, 0xa423c): +0x134/0x135 (2 byte, csv 에 보통 없음)
  - cat 14, 15 (MixItem, 0xa43f4): 추가 fields 없음 (record_size = base 만)
  - cat 16 (MixBookItem, 0xa4578): sub-loop +0x135..+0x140 (12+ byte, csv 에 4 만)
  - cat 17, 18 (SkillBook/Cash, 0xa47c0): 다음 라운드
  decode_h5_item.py 에 `parse_battle_use_extra` / `parse_orb_extra` /
  `parse_mix_book_extra` 추가 + dispatch wire-up. items.json 의 slot_11 포션이
  정확한 4 byte (val_134=91, val_135=100, val_136=4, val_137=50) 추출 — disasm
  매핑이 csv 와 정확 일치 검증.
- ✅ **Round 18**: ItemTable::SetItemOption (240B, @0xa0ff8) 디스어셈블 →
  `+0x15f` 가 random option_type byte 임 확인. SetItemOption 가 호출 시 random
  option 픽 → +0x15f = option_type, +0x162 = option_value (level*param*rand).
  csv 의 val_15f 는 init default — runtime 변경 가능. items.json 의 class_label
  통계가 default 값 (Round 16 의 5-class mask 해석은 csv 시점에는 유효).
  LoadItemTable 의 cat 12+ jumptable 분석 — 모든 카테고리가 공통 base layout
  (item_id u32 + sub_record_len + sub_record bytes) 공유. EquipItem (cat 1-11)
  만 sb-area 추가. `decode_h5_item.py` 에 `parse_common_extra` 함수 추가 →
  모든 19 슬롯에 item_id + sub_record_hex 부여.
- ✅ **Round 17**: `RefineItem::ApplyItemRefine` (956B) 디스어셈블 → 강화 시
  변경되는 EquipItemInfo struct field 식별:
  - `+0x165` = refine_count (강화 횟수 u8)
  - `+0x166` = refine_sub_count (보조 강화 u8)
  - `+0x167` = refine_locked (1=영구 잠금)
  ApplyItemRefine 의 r7 jumptable: r7=0/1=success +N, r7=3=lock, r7=4=실패(아이템 destroy).
  CopyData (0xa8884) 가 +0x165..+0x168 모두 복사 → runtime 변경 saved.
  val_15f upper 3 bit 통계: upper=7 (224, "common") 362 records, upper=1 (32, "강화")
  248 records, upper=0 ("중급") 170, upper=3 ("보석 액세서리") 9 (slot_5 헤어핀/서클릿).
  정확 의미 식별 미완 — bit6 (64)=gem accessory, bit7 (128)=common flag 가설.
- ✅ **Round 16**: items.json 정정 — `+0x155` 가 class_restriction 이 아니라
  **subtype code** 임을 IsEquipPossible / IsEquipPossibleSpirit cross-check 로
  확인 (slot_10 spirit 의 cls=5/7 분포 + IsEquipPossibleSpirit 가 0x155==7 만 허용).
  진짜 class restriction 은 **`val_15f & 0x1f`** = **5-class 비트 마스크**
  (bit0=W, bit1=R, bit2=G, bit3=K, bit4=S):
  - val=31 (WRGKS, 모든 클래스) 385 records (가장 많음)
  - val=9 (WK), val=17 (WS), val=14 (RGK), val=18 (RS) 등 다양
  - spirit 검증: 데몬의뿔 W only / 고렘의인장 RS / 팬텀의부적 WS / 기사의징표 RGK
  - decode_h5_item.py 가 `subtype` (이전 class_restriction 정정) + `class_mask`
    + `class_label` (W/R/G/K/S 조합 string) 부여.
  - val_15f upper 3 bit (32, 64, 128) 의 추가 의미 (career/tier/cash) 는 다음 라운드.
- ✅ **Round 15**: `decode_h5_item.py` 에 `parse_equip_extra` 함수 추가 — Round 14
  의 csv layout 활용해 EquipItem (cat 1-11) extra body 가변 parse + items.json
  에 named fields (`class_restriction`, `level_limit`, `item_id`,
  `sub_record_hex`, `val_150..val_160`, `triplet_162`) 부여.
  검증: 롱소드 cls=0/lv=1, 나이트롱소드 lv=5, 버클러(방패) cls=3 (워리어/나이트),
  서클릿(헬멧) cls=5/lv=1 — 모두 합리적 매핑.
  cls 가 비트 마스크로 추정 (1=warrior, 2=rogue, 4=gunslinger, 8=knight, 16=sorcerer)
  — 다음 라운드 IsEquipPossible cross-check 필요.
- ✅ **Round 14**: ItemTable::LoadItemTable (4320B) 의 EquipItem 처리 영역
  (0xa3cf0~0xa4060) 디스어셈블 분석 → csv record body → in-memory EquipItemInfo
  struct field 매핑 layout 추출:
  - csv +2..3 (u16 read but discarded — struct +0x14 = function arg category)
  - csv +4..5 (u16) → struct +0x16 (refine_value)
  - csv +6 (u8 name_len `nl`) → name string memcpy → struct +0x18
  - csv +7+nl..(+4 byte) (u32) → struct +0x30
  - csv +11+nl (u8 sub_record_len `sblen`) → 256B sub-record memcpy → struct +0x34..+0x134
  - 그 후 sb 시작 위치에서 u16/u8 sequence → struct +0x150..+0x162 영역
  - LoadItemTable 안에서 Formula::calc(0x7f3=2035) 호출 — load 시점 base stat 계산
  - `tools/h5_extract_loaditem_layout.py` 도구 작성 (register tracking 한계로
    부분 추출 — 수동 disasm 분석으로 보완).
- ✅ **Round 13**: EquipItemInfo struct 핵심 field + ItemBase formula 영역 식별.
  - EquipItemInfo +0x14 = item_category/slot_type (s8) — IsEquipPossible jumptable 의 조건
  - EquipItemInfo +0x155 = class_restriction (s8) — HERO+0x22c (class_id) 와 비교
  - EquipItemInfo +0x15d = level_limit (s8) — GetLevelLimit 가 fetch
  - EquipItemInfo +0x168..+0x16d = 6 socket slot (orb/refine ID, 0xff=빈슬롯)
  - V[168..182] = ItemBase (Formula::calc 5번째 인수) 의 struct field:
    - V[168] (item +0xe) = base SP cost (`V[168]*(100-V[123])/100`)
    - V[170] (item +0x16) = base cooldown (`V[170]*(100-V[125])/100`)
    - V[174] (item +0x44) = damage growth multiplier (`V[56]+V[57]*V[174]`)
    - V[181] (item +0x4e) = speed/weight divisor
  - csv extra (33..80B) ≠ in-memory EquipItemInfo (376B) — `LoadItemTable` 가 csv→struct
    매핑 처리. csv stat order ↔ struct offset 매핑은 다음 라운드 RE 필요.
- ✅ **Round 12**: V[122..126] 5 buff slot 정확 라벨 + V[151,152] magic stat 정정.
  - V[122] = EXP %bonus (`(100+V[122])/100` multiplier, csv 0x1d 경험치LV)
  - V[123] = SP소모% 감소 (`V[168]*(100-V[123])/100`, csv 0x1e)
  - V[124] = CP충전LV (`(V[124]/100)*150+300`, csv 0x1f)
  - V[125] = 쿨타임 감소% (`V[170]*(100-V[125])/100`, csv 0x21)
  - V[126] = 포션효과 %bonus (`V[56]*V[183]*(100+V[126])/100`, csv 0x23)
  - V[151], V[152] 둘 다 magic stat (INT 보정) — 이전 V[152]=DEX 추정 정정.
  formula 공식의 `(100±V[xxx])/100` 패턴 + csv 라벨 cross-check 로 일관 확정.

**이번 세션 (2026-05-09 Round 6) 완료 항목**:
- **gv_sub writer 분석 도구** — `tools/h5_find_gv_writers.py` (3568 함수 스캔, 547 stores 추적).
  산출 `gv_substruct_writers.tsv` + `gv_substruct_writers_summary.txt` (135 unique offsets).
- **gv_sub 필드 의미 식별** — calc_pl id=18 `(104*V[58]^2)+711+(level-1)*600` ⇒ V[58]=level 확정,
  HERO::IncreaseSP/IncreaseCP writer ⇒ 0x248=SP / 0x24a=CP, calc_pl id=20..23 패턴 ⇒ 0x236..0x23c=base, 0x298..0x29e=bonus.
  자세히 [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md).
- **`battle_system._player_ctx()` 정확화** — 12 확정 + 6 강한 추정 매핑 적용 (이전 추정 6 → 18).
  Python sanity test (`h5_test_formula_eval.py`) id=0 → 4437 통과.
- **`formula_vm._player_default()` 정확화** — defender side fallback 도 동일 매핑 적용.
- **시각 효과 hookup** — demo.gd 의 toast trace → 실제 visual 적용:
  - `screen_shake`: Demo Node2D position Tween 으로 8-step decay oscillation
  - `map_tile_change`: MapRenderer.highlight_tile 노란 사각형 1.5초 표시
  - `narration`: GameData.ingame_text(string_idx) lookup → DialogBox

---

## 빠른 재개 (1 커맨드 = 환경 복원)

**가장 흔한 케이스 — assets/ 비어있는 새 클론**:
```bash
# APK 가 있는지 확인 후 (Hero5/영웅서기5(최신폰전용).apk)
# 한 번에 모든 자산 처리 (~6s, incremental — 이미 있는 단계는 스킵):
python tools/h5_extract_pipeline.py
#   --force        : sentinel 무시하고 전체 재실행
#   --only NAME ...: 특정 단계만 (apk/vfs/names/sprite/text/converters/disasm/godot/verify)
#   --skip NAME ...: 특정 단계 제외
# 단계별 수동:
python tools/h5_vfs_unpack.py            # 1. VFS unpack (2189 entries)
python tools/h5_recover_names.py         # 2. 이름 복원 (99.7%)
python tools/h5_batch_sprite.py          # 3. sprite 421 + palette 588
python tools/h5_extract_text.py          # 4. 한글 코퍼스
for f in tools/converter/{convert,decode}_h5_*.py; do python $f; done   # 5. 디코더 일괄
python tools/import_to_godot.py          # 6. assets/ 채우기 (opcode_table 자동 포함)
python tools/verify_godot_project.py     # 7. 검증 → 0 errors / 0 warnings 기대

# 마지막: Godot 4.2+ Editor 에서 apps/hero5-godot/ 열고 F5
```

**단순 검증만 (assets/ 이미 있음)**:
```bash
python tools/verify_godot_project.py
```

---

## 다음 세션 시작점 (Round 37 후보, 우선순위 순)

### 1. 한글 비트맵 폰트 매핑 (P5, LOW PRIORITY but 자율 가능)

`_midas_funcFntInvalidate` 디스어셈블로 581 glyph index ↔ Unicode 매핑 추출.
시스템 폰트 (Noto Sans CJK KR) 로 우회 중이므로 게임 동작에 영향 없음 —
폰트 충실도 향상 only.

### 2. Mission 시스템 분석

Round 28 에서 ApplyNormalMix 가 csv slot_15 와 별개로 MixSmithTableInfo* 사용 확인.
HERO::GetMixSmithTableInfoPtr (0x890f4) 의 implementation 분석으로:
- MixSmithTableInfo 데이터의 위치 (VFS entry, .so .rodata 또는 별도 csv 파일)
- 데이터 entry 갯수 + 각 entry 의 의미 (NPC blacksmith UI 와 cross-check)
- struct layout (Round 28: +0x11c..+0x128) 의 csv layout 매핑

### 3. val_15f bit5/bit6/bit7 의 정확 게임 의미 (Round 24/27 가설 추가 검증)

Round 24 에서 items.json 분포 기반 실증적 라벨 (legendary/rare/gem/common) 부여.
정확 의미 확정을 위해:
- `MapItem::NewDropItem` (0xa7884) 의 11 args 중 +0x15f 에 사용되는 arg 추적
- `DropTable::GetRandomItem` 또는 `ShopInventory::GetRandomItem` 의 호출 패턴
- bit5/bit6/bit7 각각의 의미 (현재 가설: obtainable/gem-accessory/common-tier)

### 3. Save 데이터 구조 검증 (선택, V[112..116] 라벨 재검증)

save 파일 dump → HERO+0x278..0x282 (V[111..116] 영역) 의 game-saved 값을
game UI 표시값과 매칭. Round 11 의 secondary stat 라벨 (근접명중/장거리명중/
회피/방패방어/크리티컬) 재검증 가능.

### 4. 한글 비트맵 폰트 매핑 (LOW PRIORITY — 게임 영향 없음)

`_midas_funcFntInvalidate` 디스어셈블로 581 glyph index ↔ Unicode 매핑 추출.
시스템 폰트 (Noto Sans CJK KR) 로 우회 중이므로 게임 동작에 영향 없음 —
폰트 충실도 향상 only.

### 5. P6: Android APK 실 빌드 검증 (USER TASK — 자동화 불가)

Godot Editor 4.2+ + Build Template + Export Templates (~1GB) + JDK 17 + Android
SDK 필수. 사용자가 GUI 로 진행 필요. `apps/hero5-godot/export_presets.cfg.template`
참조.

---

## 과거 우선순위 작업 (모두 완료)

| 영역 | 상태 | 산출 |
|---|---|---|
| P1: OPCODE_TABLE 77개 | ✅ EventProc::onFunction jumptable 자동 추출 | `work/h5/analysis/opcode_table.tsv`, capstone+lief |
| P2: enemy_g 121B layout | ✅ HP/MP/ATK/DEF/EXP/Gold + 5 skill slot | .so disasm 검증 |
| P3: Hero/CHAR 시스템 | ✅ 4방향 이동 + walk_frames | `character.gd` |
| P4: 전투/퀘스트/UI | ✅ 골격 + 실제 데이터 통합 | battle_system, quest_system |
| P5: 한글 폰트 | ✅ table.dat=Unicode (시스템 폰트로 우회) | `P5_FONT_MAPPING.md` |
| Damage formula 심층 | ✅ Event_PlayerDamage + BATTLER offset 확정 | `BATTLE_FORMULA.md` |
| Formula VM 식별 | ✅ 6 opcode 스택 머신 (calc_pl/en/sk.dat) | `BATTLE_FORMULA.md` §6 |
| Event_* 102개 매핑 | ✅ 1:1 mapping reference | `EVENT_OPCODE_REFERENCE.md` |
| ItemTable 19-카테고리 | ✅ runtime_size dispatch | `ITEM_STRUCT.md` |
| Formula VM 변수 사전 | ✅ 254 var_id → struct/offset | `FORMULA_VAR_DICT.md` |
| GOT gv 식별 | ✅ var_id 58-160 → gv[0x1474] sub-struct | Round 3 |
| interpreter.gd signal | ✅ 13 signal (map/camera/narration/...) | Round 3 |
| DES 변종 해독 | ✅ 표준 DES + S1[3][10]=2 단일 수정 | `DES_VARIANT.md`, Round 4 |
| calc_*.dat 평문 | ✅ 3 파일 MD5 검증 통과 | `work/h5/analysis/calc_*_plain.bin` |
| Formula VM 186 공식 | ✅ infix 표현 dump | `work/h5/analysis/formulas_disasm.txt` |
| gv_sub 111 fields | ✅ var_id 58-167+249 offset/type 매핑 | `gv_substruct_layout.tsv`, Round 5 |
| GDScript Formula VM | ✅ FormulaVM autoload + battle 통합 | `formula_vm.gd`, Round 5 |
| gv_sub 핵심 의미 식별 | ✅ writer 분석으로 V[58]=level / 0x248=SP / 0x24a=CP 등 18 fields 매핑 | `gv_substruct_writers.tsv`, [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md), Round 6 |
| 시각 효과 hookup | ✅ screen_shake tween + map highlight + narration text lookup | `demo.gd`, `map_renderer.gd`, Round 6 |
| V[111..116] 의미 | ✅ Round 7: V[111]=atk_growth coef, V[112..116]=class secondary stat base | LoadResClassInfo disasm + id=24..29 cross-check |
| 0x294/0x295/0x296 buff descriptor | ✅ Round 8: gameplay 전용 (Formula VM var 아님) | HERO::ApplyBuildupEffect + Round 7 정정 |
| V[127..148] buff/element bonus | ✅ Round 8: V[127]=def_red%, V[128]=atk%bonus, V[129..133]=stat bonus, V[134..148]=element | calc_pl 공식 패턴 + AddBuffArray disasm |
| V[151..155] formula 의존 stat | ✅ Round 7: V[153]=con, V[154]=str, V[155]=max_sp 확정 | id=0 / id=24 공식 + ApplyBuildupEffect entry 32 |
| V[122..126] 5 buff stat slot | ✅ Round 9: ApplyBuildupEffect entry type 30/31/32/34/36 자동 추출 | `applybuildup_table.tsv`, `tools/h5_apply_buildup_disasm.py` |
| V[112..116] 클래스 base 패턴 | ✅ Round 9: 5 클래스 secondary stat base 추출 | `class_stats_table.txt`, `tools/h5_extract_class_stats.py` |
| 한글 stat label 의 .so 위치 | ✅ Round 10: .so 0건, VFS text/*.json 에 분산 확인 | `tools/h5_find_kr_stat_strings.py` |
| 00017 status menu 20-stat sequence | ✅ Round 10: 라벨 순서 추출 | `tools/h5_find_kr_text_idx.py`, `kr_stat_text_locations.tsv` |
| CalcStatusComputation 의 calc_sk 매핑 | ✅ Round 10: calc_sk[3]=V[41], calc_sk[4]=V[156] (EquipItem stat) | `calc_status_cache_map.tsv`, `tools/h5_calc_status_table.py` |
| V[112..116] 5 secondary stat 라벨 | ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 확정 | `tools/h5_decode_buildup.py`, `buildup_decoded.tsv` |
| V[62]/V[63] = base_con/base_int 정정 | ✅ Round 11: buildup csv "건강"/"정신" 매핑 검증 | 동일 |
| V[122..126] 5 buff slot 라벨 | ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% | formula `(100±V[xxx])/100` 패턴 |
| V[151,152] magic stat 정정 | ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못) | `formulas_disasm.txt` 사용 패턴 |
| EquipItemInfo struct 핵심 5 field | ✅ Round 13: +0x14/+0x155/+0x15d/+0x168..0x16d | `tools/h5_dump_caller.py _ZN13EquipItemInfo*` |
| V[168..182] ItemBase formula 영역 | ✅ Round 13: V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor | `formulas_disasm.txt` cross-check |
| csv → EquipItemInfo struct layout 매핑 | ✅ Round 14: 가변길이 (name + sub_record) + u8/u16 mixed sequence | `tools/h5_extract_loaditem_layout.py`, ITEM_STRUCT.md "CSV → EquipItemInfo struct 매핑" 섹션 |
| items.json EquipItem named fields | ✅ Round 15: class_restriction/level_limit/item_id/sub_record/val_150..val_160 부여 | `tools/converter/decode_h5_item.py::parse_equip_extra` |
| +0x155 = subtype (class_restriction 정정) | ✅ Round 16: IsEquipPossibleSpirit cross-check | items.json `subtype` 필드 |
| 진짜 class_mask (val_15f & 0x1f) | ✅ Round 16: 5-class 비트 마스크 확정 (W/R/G/K/S) | items.json `class_mask` + `class_label` 필드 |
| EquipItemInfo refine fields | ✅ Round 17: +0x165=count, +0x166=sub_count, +0x167=locked | `applyitemrefine_disasm.txt` |
| val_15f upper 3 bit 분포 | ✅ Round 17: upper=0/1/3/7 만 등장 (170/248/9/362), 정확 의미 미완 | `tools/h5_check_items.py` |
| SetItemOption: +0x15f=option_type / +0x162=option_value | ✅ Round 18 | `_ZN9ItemTable13SetItemOptionEP8ItemInfoa` disasm |
| 모든 카테고리 (cat 1-18) common base | ✅ Round 18: item_id + sub_record_hex | `decode_h5_item.py::parse_common_extra` |
| cat 12-16 카테고리별 추가 fields layout | ✅ Round 19: BattleUseItem 4 byte / OrbItem 2 byte / MixItem 0 / MixBookItem 12 byte | `parse_battle_use_extra` / `parse_orb_extra` / `parse_mix_book_extra` |
| BattleUseItem (cat 12) +0x134..+0x137 csv 매칭 검증 | ✅ Round 19: slot_11 포션 4 byte 정확 추출 | items.json |
| slot_17 (SkillBookItem) 4 byte ext + skill_level 식별 | ✅ Round 20: 0xa47c0 disasm, 98 records 모두 v134/v135/skill_level/v137 추출 | `parse_skill_book_extra`, items.json |
| slot_18 (CashItem) 2 byte ext + 별도 jumptable case | ✅ Round 20: 0xa3b38 (Round 19 가설 정정), 49 records 모두 추출 | `parse_cash_extra`, items.json |
| SkillBook 4 byte fields 의미 (class_id/skill_index/skill_level/required_level) | ✅ Round 21: HERO::IfLearnSkill 분석, (class_id/2)+16 공식 확인 | `iflearnskill_disasm.txt` |
| slot_16 = SkillBook 정정 (이전 mix_book 잘못) | ✅ Round 21: Warrior 48 + Rogue 47, 양손베기/돌진/내려찍기 등 | items.json, SLOT_META |
| 소서러 (class_id=4) 미구현 stub 확정 | ✅ Round 22: skill_04.dat 부재 + SORCERER class 없음 + class_stats unk1..14=1 | class_stats.json, c_csv_skill_*, class_select.gd "(미구현)" |
| class_stats.json STR/DEX/CON/INT 순서 정정 | ✅ Round 11: decode_h5_class.py 정정 + 재생성 | `tools/converter/decode_h5_class.py` |
| 강화 stat 보너스 식 (Formula VM id=35/36) | ✅ Round 26: refined_stat = base + sub_count (V[187]) | `formulas_disasm.txt`, `formula_var_dict.tsv` |
| V[184]/V[185] = item +0x156/+0x158 stat | ✅ Round 26: weapon=atk_min/max, shield=phys/mag def, helmet/boots/acc=primary/secondary | items.json stat_a/stat_b 분포, `decode_h5_item.py::parse_equip_extra` |
| ApplyItemRefine 5-case jumptable 의미 | ✅ Round 26: 큰성공/성공/stay/lock/destroy + refine_count cap=10 | `applyitemrefine_disasm.txt` |
| ApplyOrbCombine orb socket mechanism | ✅ Round 26: 39 orb 종 (3×13), +0x168 orb_count, +0x169..+0x16d 5 socket | `applyorbcombine_disasm.txt` |
| NewDropItem signature 12 args + +0x15f position | ✅ Round 27: `(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 7번째 arg = tier_flags | `newdropitem_disasm.txt` |
| Monster drop_table 13-byte entry | ✅ Round 27: SetDropItem 안에 13B/entry × 4 drop type. NewDropItem 의 +0x15f arg 가 entry byte 에서 직접 전달 | `setdropitem_disasm.txt` |
| +0x15f tier_flags csv↔drop 일관성 | ✅ Round 27: csv val_15f = drop_table 의 byte data 와 동일 의미. Round 24 의 legendary/rare/gem/common 라벨이 게임 drop 로직에서 사용 검증 | 동일 |
| ApplyNormalMix (NPC blacksmith) mechanism | ✅ Round 28: MixSmithTableInfo* 별개 데이터, struct +0x11c..+0x128 col-major | `applynormalmix_disasm.txt` |
| ApplySpecialMix (csv slot_15 recipe) mechanism | ✅ Round 28: GetItemTableInfo 로 csv 직접 사용 + Mission 진척, struct +0x134..+0x140 col-major | `applyspecialmix_disasm.txt` |
| ApplyItemCompose (option 결합) | ✅ Round 28: 두 EquipItem grade≤2 결합 → option set 합성, gv+0x1444+0x198 prob 테이블 | `applyitemcompose_disasm.txt` |
| ApplyItemDecompose (분해) | ✅ Round 28: option_grade-based 5-way prob, gv+0x1444+0x1b8 테이블, money refund / mix material / potion 분기 | `applyitemdecompose_disasm.txt` |
| mix_book recipe csv↔struct layout | ✅ Round 28: csv = row-major (사용자 의미), struct memory = col-major (LoadItemTable transpose). parse_mix_book_extra row-major 객체 그대로 유효 | `applyspecialmix_disasm.txt` |

---

## 게임 흐름

```
Title (로고 + Continue/New Game + 슬롯 메타: Lv/cls/G/inv/시간)
  ├─ New Game → ClassSelect (5 클래스 + STR/DEX/INT/CON 미리보기)
  │             → Demo
  └─ Continue / Slot 클릭 → Demo (저장 자동 로드)

Demo:
  WASD 이동 (충돌, 자동 인카운터 25step+10%/step)
  M/N 맵/씬 (BGM 페이드 + 캐릭터 자동 배치 + 맵 이름 표시)
  P NPC 스폰 (4색 분류) → E 가까운 NPC 와 대화 (한글 + 선택지 → 퀘스트)
  S 상점, Q 퀘스트, I 상태(ATK/DEF 합산), X 설정, H 도움말, B 전투
  자동 저장: slot 7, 60초 간격
  씬 전환 시 0.3s 검정 페이드
```

---

## 새 도구 (Ghidra-free .so 분석 + 통합 파이프라인)

| 도구 | 역할 | 추가 |
|---|---|---|
| `tools/h5_dump_loaditem_tail.py` | LoadItemTable 의 cat 17/18 영역 (0xa479c..0xa49c0) 추가 disasm — `capstone.skipdata=True` 로 literal pool 통과 (Round 20) | 2026-05-10 |
| `tools/h5_decode_buildup.py` | c_csv_buildup.json → ABE entry type 매핑 + V slot 라벨 자동 추출 (Round 11) | 2026-05-09 |
| `tools/h5_find_kr_stat_strings.py` | .so .rodata 에서 한글 stat label 검색 (Round 10) | 2026-05-09 |
| `tools/h5_find_kr_text_idx.py` | VFS text JSON 의 한글 stat label 위치 추출 (Round 10) | 2026-05-09 |
| `tools/h5_calc_status_table.py` | CalcStatusComputation 의 calc_sk → cache offset 매핑 (Round 10) | 2026-05-09 |
| `tools/h5_disasm_property_menu.py` | DrawPropertyMenu cache offset reads 추적 (Round 10) | 2026-05-09 |
| `tools/h5_apply_buildup_disasm.py` | HERO/BATTLER ApplyBuildupEffect jumptable 자동 추출 (Round 9) | 2026-05-09 |
| `tools/h5_extract_class_stats.py` | c_csv_class.json → 5 클래스 V[111..116] base 패턴 (Round 9) | 2026-05-09 |
| `tools/h5_find_battle_check_funcs.py` | 전투 함수 immediate calc id 호출자 추적 (Round 9) | 2026-05-09 |
| `tools/h5_find_formula_callers.py` | Formula::calc 전체 caller 분석 (r0/r1 reg propagation) (Round 9) | 2026-05-09 |
| `tools/h5_list_stat_methods.py` | HERO/CHAR/BATTLER stat 메서드 이름 분류 (Round 9) | 2026-05-09 |
| `tools/h5_dump_caller.py` | 단일 함수 disasm wrapper (Round 9) | 2026-05-09 |
| `tools/h5_find_func.py` | 심볼 substring 탐색 helper (Round 9) | 2026-05-09 |
| `tools/h5_find_gv_writers.py` | gv+0x1474 sub-struct offset 별 writer 함수 추적 (Round 6) | 2026-05-09 |
| `tools/h5_des.py` | 표준 DES + S1[3][10]=2 변종 (mx_des_encrypt/decrypt) | 2026-05-09 |
| `tools/h5_disasm_des.py` | DES 함수 disasm + 테이블 후보 dump | 2026-05-09 |
| `tools/h5_resolve_des_got.py` | PC-relative GOT lookup 해석 | 2026-05-09 |
| `tools/h5_decrypt_calc.py` | calc_pl/en/sk.dat → 평문 (MD5 검증) | 2026-05-09 |
| `tools/h5_formula_disasm.py` | Formula VM 186 공식 → infix 표현 dump | 2026-05-09 |
| `tools/h5_extract_gv_subStruct.py` | var_id 58-160 의 gv+0x1474 sub-struct offset 추출 | 2026-05-09 |
| `tools/h5_export_formulas.py` | 186 공식 + 254 var_dict → GDScript JSON | 2026-05-09 |
| `tools/h5_test_formula_eval.py` | Formula VM 정합성 테스트 (id=0 → 4437 검증) | 2026-05-09 |
| `tools/h5_extract_pipeline.py` | 9-step 통합 파이프라인 (incremental + --force/--only) | 2026-05-09 |
| `tools/h5_scn_body_stats.py` | 258 scn body 정적 trace + opcode 빈도 TSV | 2026-05-09 |
| `tools/h5_extract_battle_funcs.py` | 11 BATTLER/HERO/Monster 함수 ARM disasm + callee | 2026-05-09 |
| `tools/h5_smaf_audit.py` | 42 SMAF ↔ 42 OGG 1:1 매칭 검증 + 청크 dump | 2026-05-09 |
| `tools/h5_disasm_newhiteffect.py` | NewHitEffect / HeroSkillAtkHardCode disasm | 2026-05-09 |
| `tools/h5_find_damage_callers.py` | IncreaseHP/AddEffectDamage caller 추적 | 2026-05-09 |
| `tools/h5_disasm_formula.py` | Formula VM 4 함수 (dataLoad/calc/calcByFormula/getNumberInStack) | 2026-05-09 |
| `tools/h5_disasm_skill_hardcode.py` | HeroSkillAtkHardCode 단독 disasm | 2026-05-09 |
| `tools/h5_extract_event_funcs.py` | EventProc::Event_* 102개 일괄 disasm | 2026-05-09 |
| `tools/h5_disasm_item_funcs.py` | EquipItemInfo CopyData 등 7개 함수 → struct offset 추출 | 2026-05-09 |
| `tools/h5_extract_formula_vars.py` | Formula::getValFunc 254-entry switch → var_id 사전 | 2026-05-09 |
| `tools/h5_extract_opcode_disasm.py` | EventProc::onFunction jumptable → opcode_table.json 77 entries | 2026-05-08 |
| `tools/h5_event_arg_sizes.py` | Itanium ABI mangle parser → 105 Event_* arg_size | 2026-05-08 |
| `tools/h5_extract_enemy_layout.py` | Map::MapEnemyG_set → 121B record layout 검증 | 2026-05-08 |
| `tools/h5_inspect_enemy_record.py` | 디버그용 raw record dump | 2026-05-08 |
| `tools/h5_batch_sprite.py` | sprite/palette single-argv converter wrapper | 2026-05-08 |

의존: `pip install lief capstone`. import_to_godot.py 가 둘 다 있으면 opcode_table.json
자동 생성 (없으면 graceful skip — BASE_TABLE 38 fallback).

---

## 파일 위치 빠른 참조

### Phase 2 산출물 (`work/h5/` — gitignored)
- `extracted/` — APK unzip (assets/data.vfs.mp3, lib/armeabi/libHeroesLore5.so)
- `vfs_entries/` — 2,189 unpacked records
- `vfs_catalog.tsv` — index/hash/length/type
- `analysis/asset_names.tsv` — 99.7% 이름 복원
- `analysis/opcode_table.tsv` — 77/77 (자동 추출)
- `analysis/event_arg_sizes.tsv` — 105 Event_* arg sizes
- `analysis/enemy_g_layout.tsv` — record byte → struct field 매핑
- `analysis/scn_headers.tsv` — 258 scene 헤더
- `analysis/formula_var_dict.tsv` — 254 var_id → struct/offset (Round 3)
- `analysis/gv_substruct_layout.tsv` — 111 gv+0x1474 sub-struct fields (Round 5)
- `analysis/calc_pl/en/sk_plain.bin` — DES 복호 평문 (Round 4)
- `analysis/formulas_disasm.txt` — 186 공식 infix dump (Round 4, 945 줄)
- `analysis/des_disasm.txt`, `des_got_resolved.json`, `des_tables.json` — DES RE 산출
- `converted/sprites/<idx>/frame_NN_*.png`
- `converted/text/_corpus.txt` — 18,837 unique 한글

### Phase 3 (`apps/hero5-godot/`)
```
project.godot           # autoload 6: GameState/AssetLoader/GameData/Audio/Quest/FormulaVM
scenes/                 # 14 씬
scripts/core/           # 11 싱글톤/게임 로직
  game_state.gd, asset_loader.gd, game_data.gd, audio_manager.gd, quest_system.gd
  map_renderer.gd, character.gd, interpreter.gd, battle_system.gd, save_manager.gd
  formula_vm.gd            # ← Round 5: Formula VM 평가기 (calc_*.dat 186 공식)
scripts/ui/             # 17 UI 스크립트 (scene_fader.gd 추가)
assets/                 # gitignore — import_to_godot.py 가 채움
  sprites/, gbm/, palettes/, text/, sounds/, fonts/, gamedata/, maps/, scenes/
  scenes/opcode_table.json   # ← P1 산출물 (capstone+lief 있으면 자동 생성)
  scenes/bodies/<idx>.bin    # ← P1 scene body 자동 실행용
  data/formula/formulas.json # ← Round 5: 186 공식 (id → body)
  data/formula/var_dict.json # ← Round 5: 254 var_id → struct/offset
```

### 도구 (`tools/`)
- `h5_vfs_unpack.py`, `h5_recover_names.py`, `h5_extract_text.py` — Phase 2 추출
- `h5_batch_sprite.py` — single-argv converter wrapper
- `h5_extract_opcode_disasm.py`, `h5_event_arg_sizes.py`, `h5_extract_enemy_layout.py`
  — capstone+lief 분석 (P1, P2)
- `import_to_godot.py` — 모든 자산 → Godot
- `verify_godot_project.py` — tscn/gd reference 검증
- `converter/*` — 자산 디코더 (sprite/pa/gbm/scn/csv/skill/item/quest/enemy)

---

## 디버그 / 테스트 키 (Demo 씬)

| 키 | 기능 |
|---|---|
| WASD | 이동 |
| M / N | mapID / scene 전환 |
| P | NPC 마커 스폰 (4색) |
| E | 가까운 NPC 와 대화 |
| T | dialog 테스트 (트리거) |
| S | 상점 |
| Q | 퀘스트 패널 |
| I / ESC | 상태창 (ATK/DEF 합산 + hover 비교) |
| X | Settings |
| H | 도움말 |
| B | 즉시 전투 (테스트) |
| C / V | collision / tile attribute 디버그 |
| 1-8 | 슬롯 N 저장 |
| Shift+1-8 | 슬롯 N 로드 |
| F5 / F9 | slot 0 빠른 저장 / 로드 |

---

## 알려진 제한

- [x] ~~Interpreter opcode dispatch (22/77 만 구현)~~ — ✅ 77/77 (2026-05-08)
- [x] ~~enemy ATK/DEF offset 일부 부정확~~ — ✅ .so disasm 검증 완료 (2026-05-08)
- [x] ~~DES 복호화 차단~~ — ✅ 표준 DES + S1[3][10]=2 변종 해독 (2026-05-09)
- [x] ~~calc_*.dat 평문 미확보~~ — ✅ MD5 검증 통과 (2026-05-09)
- [x] ~~Formula VM 공식 추출 미완~~ — ✅ 186 공식 infix dump (2026-05-09)
- [x] ~~battle_system.gd 의 Formula VM 평가기 미구현~~ — ✅ FormulaVM autoload + battle 통합 (2026-05-09)
- [x] ~~gv+0x1474 sub-struct offset 추출~~ — ✅ 111 fields 정확 매핑 (2026-05-09)
- [x] ~~gv_sub 핵심 필드명 정확화~~ — ✅ Round 6 writer 분석으로 18 fields 의미 확정 (V[58]=level, V[60..63]=base, V[69]=SP, V[70]=CP, V[118..121]=bonus)
- [x] ~~V[111..116] (클래스 base 계수) 의미~~ — ✅ Round 7: V[111]=atk_growth, V[112..116]=secondary stat base
- [x] ~~V[155]=max_sp~~ — ✅ Round 7: ApplyBuildupEffect SP clamp 상한
- [x] ~~V[127..148] 다중 buff/element bonus~~ — ✅ Round 8: V[127]=def_red%, V[128]=atk%, V[129..133]=stat bonus, V[134..148]=element
- [x] ~~Round 7 0x294/0x296 mapping~~ — ✅ Round 8 정정: gameplay 전용 (Formula VM var 아님)
- [x] ~~V[125,126] (0x2a6, 0x2a8) buff slot 의미 식별~~ — ✅ Round 9: ApplyBuildupEffect entry type 34/36 으로 5-slot 시스템 일부임 확정
- [x] ~~V[112..116] 5 stat 의 한국어 라벨~~ — ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 (buildup csv 매핑)
- [x] ~~V[62]/V[63] 매핑 정정~~ — ✅ Round 11: int/con → con/int (이전 매핑 오류, buildup csv 로 검증)
- [x] ~~V[122..126] 5 buff slot 의미~~ — ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% 확정
- [x] ~~V[151,152] magic stat~~ — ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못)
- [x] ~~RefineItem::ApplyItemRefine 강화 stat 보너스 mechanism~~ — ✅ Round 26: V[184]+V[187] / V[185]+V[187] (id=35/36), 5-case jumptable
- [x] ~~ApplyOrbCombine orb 결합 mechanism~~ — ✅ Round 26: 39 orb 종, +0x168 count, +0x169..+0x16d 5 socket
- [ ] V[151] vs V[152] 의 element 짝 (fire/ice/lightning/dark 어느 것)
- [ ] 한글 비트맵 폰트 (시스템 폰트로 우회 중) — P5, capstone+lief 로 가능
- [ ] SMAF (.mmf) 변환 (OGG 42개로 충당)
- [ ] 자산 이름 7개 / 0.3% 미복원 (게임 영향 없음)
- [ ] Android APK 실 빌드 미검증 — P6, Godot Editor 환경 필수
- [ ] Godot Editor 에서 실제 실행 검증 — verify 는 reference 만, GDScript compile 미검증

---

## 환경 의존성

**필수**:
- Python 3.10+
- Pillow (sprite 변환)

**.so disasm 작업 시 (P1/P2/P5)**:
- `pip install lief capstone`

**Godot 빌드/실행**:
- Godot 4.2+ Editor
- (Android export) JDK 17 + Android SDK + NDK + build template

---

## 참조 문서

- [`PROGRESS.md`](PROGRESS.md) — 전체 진행 상세 (Phase 2 분석 단계별 + Phase 3 시스템별)
- [`PHASE3_ENGINE.md`](PHASE3_ENGINE.md) — Godot 4 엔진 결정 근거
- [`DES_VARIANT.md`](DES_VARIANT.md) — DES 변종 해독 + calc_*.dat 평문 + Formula VM 디스어셈블러
- [`BATTLE_FORMULA.md`](BATTLE_FORMULA.md) — BATTLER damage 함수 disasm + Event_PlayerDamage 공식 + Formula VM/DES 키
- [`FORMULA_VAR_DICT.md`](FORMULA_VAR_DICT.md) — Formula VM 변수 사전 (254 var_id → struct/offset)
- [`EVENT_OPCODE_REFERENCE.md`](EVENT_OPCODE_REFERENCE.md) — 102개 Event_* opcode 의미 매핑 reference
- [`ITEM_STRUCT.md`](ITEM_STRUCT.md) — EquipItemInfo struct 부분 layout + 19-카테고리 dispatch
- [`P5_FONT_MAPPING.md`](P5_FONT_MAPPING.md) — table.dat=Unicode (EUC-KR 아님) 정정 + 매핑 위치
- [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md) — Round 6: HERO 객체 (=gv+0x1474) offset 별 의미 매핑 (writer 분석)
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 템플릿
