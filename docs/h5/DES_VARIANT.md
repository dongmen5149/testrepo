# Hero5 DES 변종 — 완전 해독 (2026-05-09)

원본 분석: `tools/h5_disasm_des.py`, `tools/h5_resolve_des_got.py` (capstone+lief).
구현: `tools/h5_des.py` (`mx_des_decrypt` / `mx_des_encrypt`).
적용: `tools/h5_decrypt_calc.py` 가 calc_pl/en/sk.dat 평문을 MD5 검증 통과로 dump.

---

## 1. 결론

**libHeroesLore5.so 의 DES 는 표준 DES 와 거의 동일** — 단 한 가지만 다름:

> **MAT_SBOX[0x3a]** (= S1 행 3, 열 10) 값이 **3 → 2** 로 수정됨.

이 한 비트의 차이만으로 표준 pycryptodome DES 가 calc_*.dat 를 풀지 못했다.

다른 모든 테이블은 표준 DES 와 100% 일치:
- IP, IP_inv (각 64)
- E expansion (48), P box (32)
- S2..S8 (각 64) + S1 의 나머지 63개 entry
- PC1 (56), PC2 (48)
- Shift schedule [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]

키: `'0EP@KO91'` (8 ASCII bytes, .rodata 0x001588b0).

---

## 2. .so 호출 규약 — 표준 DES encrypt/decrypt 의 swap

`MX_desInit` 직후 init flag (`KEY4ENCRYPT` = 1B at 0x1647d4) 가 1 로 설정.
`KEY4REAL` (768B at 0x174ae0) 에 16개 라운드 서브키가 K_1..K_16 순서로 저장.

| 함수 | flag 동작 | startDes 모드 | 효과 |
|---|---|---|---|
| `MX_desEncrypt` | flag != 0 → reversal SKIP | mode=1 (정상 split) | **표준 DES encrypt** |
| `MX_desDecrypt` | flag != 0 → reverse keys, set flag=0 | mode=0 (input swap) | **표준 DES decrypt** |

수학적 동치:
- `MX_desEncrypt(P) = STD_DES_encrypt(P, key)` (키 스케줄 K_1..K_16, 표준 split, 16 라운드)
- `MX_desDecrypt(C) = STD_DES_decrypt(C, key)`
  - 내부적으로 reversed_keys + swap_input + mode-1-style combine 으로 구현
  - Feistel 항등식 `R(K)^{-1} = SW ∘ R(rev_K) ∘ SW` 를 활용해 동일 함수로 양방향 처리

(이것이 `MX_desEncrypt = STD decrypt` 같은 직관 반대 결론에 빠질 만한 이유 — 순환 참조처럼 보이지만 결국 표준이다.)

---

## 3. 파일 포맷 (LoadResDecrypt)

calc_*.dat 와 그 외 보호 리소스의 와이어 포맷:
```
[16B md5(plain)][DES-encrypted body...]
```
- DES 모드: ECB
- body 길이: 8 의 배수 (DES block)
- 검증: MD5(decrypted_body) == 첫 16 byte

`tools/h5_des.py` 의 `mx_des_decrypt(body, key)` 가 평문 반환.

---

## 4. Formula VM 도출

평문 calc_*.dat 의 구조 (`Formula::calcByFormula` @ 0x77244 분석):

```
[u8 magic=0x02][u8 formula_count][u8 padding=0x00]
formulas[]:
  [u8 size = total_bytes - 2][u8 padding]
  [i32 lower_bound][i32 upper_bound]
  [u8 body_count]
  body[body_count]:
    operator (op & 0x10):  1 byte
    operand (op == 0):     5 byte (op=0 + i32 immediate value)
    operand (op == 0x0c):  5 byte (op=0xc + i32 var_id → Formula::getValFunc 로 fetch)
    그 외:                 5 byte (getNumberInStack 가 0 반환 — 무의미)
```

**opcode 맵** (실제 jumptable 기반, 기존 `BATTLE_FORMULA.md` 의 매핑은 역순이었음):

| op | mnemonic |
|---:|---|
| 0x11 | ADD |
| 0x12 | SUB |
| 0x13 | MUL |
| 0x14 | DIV |
| 0x15 | MOD |
| 0x16 | XOR |

스택 머신: operator 만나면 `b = pop(); a = pop(); push(op(a, b))`.
최종 결과를 `clamp(lower, upper)` 로 마무리.

**ID 분기** (`Formula::calc` @ 0x7749c):
- id 0..999     → calc_pl (39 formulas)
- id 1000..1999 → calc_en (19 formulas)
- id 2000..3007 → calc_sk (128 formulas)

총 186개 공식 모두 정상 파싱 (size mismatch 0 건).

---

## 5. 산출물

| 파일 | 설명 |
|---|---|
| `tools/h5_disasm_des.py` | DES 함수 disasm + 테이블 후보 dump |
| `tools/h5_resolve_des_got.py` | PC-relative GOT lookup → 테이블 주소 해석 |
| `tools/h5_des.py` | 표준 DES + S1 수정 변종 Python 구현 |
| `tools/h5_decrypt_calc.py` | calc_*.dat → 평문 (MD5 검증) |
| `tools/h5_formula_disasm.py` | Formula VM 디스어셈블러 → 사람이 읽을 공식 |
| `work/h5/analysis/calc_pl_plain.bin` | 평문 calc_pl (1584B) |
| `work/h5/analysis/calc_en_plain.bin` | 평문 calc_en (624B) |
| `work/h5/analysis/calc_sk_plain.bin` | 평문 calc_sk (4680B) |
| `work/h5/analysis/formulas_disasm.txt` | 186 공식 디스어셈블 (945줄) |

---

## 6. 활용

### battle_system.gd 정확화
지금까지 `dmg = max(1, atk + rand(0..7) - enemy_def/2)` 같은 **임시 공식**으로 동작.
이제 정확한 공식이 추출되었으므로:

예: `id=0` (player attack base damage):
```
clamp((V[2] + 32*V[58] + 10*V[153]) * (100 + V[20]) / 100, 1, 30000)
```
- V[2]: skill 의 base attack value
- V[58]: 전역 state (gv[0x1474] sub-struct, player.atk?)
- V[153]: 전역 state (player.weapon_atk?)
- V[20]: skill 의 multiplier %

배틀 코드에서 `Formula.calc(formula_id, attacker, defender, skill, item)` 으로 호출 가능.

### Formula 평가기 구현 — ✅ 완료 (2026-05-09)
GDScript 측에 동일한 스택 VM 을 만들어 calc_*.dat 평문을 그대로 평가:

- `apps/hero5-godot/scripts/core/formula_vm.gd` — autoload `FormulaVM` 신규
- `apps/hero5-godot/assets/data/formula/{formulas,var_dict}.json` — `tools/h5_export_formulas.py`
  가 생성 (186 공식 + 254 var_id 매핑, gv+0x1474 sub-struct 의 111 fields 포함)
- `tools/h5_test_formula_eval.py` 가 Python 으로 같은 알고리즘 실행 → 동일 결과 검증
  (id=0 = `(50+32*100+10*30)*(100+25)/100 = 4437` 정확)

`battle_system.gd` 의 player attack 은 Formula id=0, skill 은 2000+skill_id, enemy turn
은 1000 호출. var_lookup 미완 시 임시 공식 fallback 으로 동작 보장.
