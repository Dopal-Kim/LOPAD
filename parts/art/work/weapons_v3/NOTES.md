# 무기 v3 — 53라운드 Q19·Q26~Q32 무기 재디자인 (칼 B · 대검 A · 단검 B · 활 B+화살 뽑기)

근거: `decisions/2026-10-03-round-53-playtest4.md` Q18~Q21(무기별 기본 자세·`player_attack` = 활 빠른 사격), Q26~Q32(무기 방향·빛·대검 휴대·색). 시안 `gemini/concept_weapons/raw_{katana_B2,greatsword_A2,dagger_B,bow_B}.jpg` 는 **참고만** — 도트는 전부 직접(Gemini 미사용).
재현: 칼 = `python3 parts/art/work/hero_v3/build.py`(칼 B 는 `katana3.py` 안) → 무기 = `python3 parts/art/work/weapons_v3/build.py [free] [greatsword] [dagger]` → 비교 = `python3 parts/art/work/weapons_v3/compare.py`. 전부 결정적(두 빌드 경로에서 같은 바이트 — `build2.py greatsword_draw` 재실행으로 md5 대조).

## 진행 상황

| 단계 | 상태 |
|---|---|
| 1 칼 B 전 오버레이(연격 1~3 · 휴대 4 · 뽑아 든 휴대 4 · 뽑기 · 넣기 · 특수) | **완료** — 몸 시트는 바이트 동일(무기만 바뀜), 넣기 불티 crc32 seed 로 재출력 |
| 2 무기별 기본 자세 몸 | **완료** — `player_{idle,walk,run}_free` (대쉬는 원래 왼손이 비어 `player_dash` 공용) |
| 3 대검 A 오버레이 | **완료** — 연격 1~3 · 대쉬베기 · 내리찍기 · 뽑기 · 넣기 · 특수 · 등 휴대 4 · 뽑아 든 휴대 4 |
| 4 단검 B 오버레이 | **완료** — 연격 1~3 · 특수 · 휴대 4 |
| 5 활 B 오버레이 + `player_bow_reload` 몸(몸에 꽂힌 화살 뽑기) | **남음** |
| 6 산출 미리보기 | 칼·대검·단검분 완료(2배 전 프레임 · 3배 gif · 1배 조명 합성 · 구↔새 비교). 4무기 나란히 합성은 활 뒤 |

## 1. 규격표

| 항목 | 값 |
|---|---|
| 무기 시트 | **192×192** · 피벗 **(96,186)** = 몸 피벗 (48,138) · `playerFrameOffset` (48,48) · `pixelScale` 0.5 · `depth` 항상 above + `occlusionBaked` |
| JSON (칼 v3 규약) | `gripAnchors`(쥔 손, 무기 시트 좌표) · `handAnchors` · `bladeLocal`(몸 기준 θ·elev, 프레임별) · `bladeTipAnchors`(무기 끝, 이펙트 위치용) · `carryHidden` · `bodySheet` · `bodySheetByWeapon` · `design`/`glowRule`/`colorBudget` · 동작 시트는 몸 JSON 의 판정 필드(`impactFrame`·`hitFrames`·`activeFrames`·`cancelFromFrame`·`timingMs`·`phases`·`oldTiming` …)를 그대로 옮김 + `timingCheck` |
| 색 | 칼 **16** · 대검 **14** · 단검 **14** (각 16 이하, **전부 주인공 30색 팔레트 안**, 백열 코어 X 미사용, 반투명 0) — build assert |
| 빛(Q30) | 평소: 칼 날선·칼집 금 / 대검 홈 혼불 1점 / 단검 균열 2줄 = 1px A21·A19, 끝 A23. **glow(판정) 프레임만** 칼 날선 A25·A26 + 날 몸 A21 / 대검 양 날 A25·A23 + 홈 불줄 A21 + 끝 A26 / 단검 균열 A23 + 끝 A26 |
| 치수(설계 ×1.5 = 도트) | 칼 날 37(55) + 손잡이 12(18) · 칼집 38(57) — 그대로 / 대검 날 44(66, 리카소 7 포함, 폭 7) + 손잡이 10(15) / 단검 조각 16(24, 폭 최대 6) + 붕대 손잡이 4.5(7) |

## 2. 이동 몸 시트 선택 규칙 (Q19 — 아트 제안, 시스템 확인 필요)

모든 휴대 오버레이 JSON 과 `player_*_free` JSON 에 `bodySheetByWeapon` 으로 같은 표를 넣었다.

| 동작 | 칼 | 대검 | 단검 | 활 |
|---|---|---|---|---|
| idle | `player_idle` | `player_idle_free` | `player_idle_free` | `player_idle_free` |
| walk | `player_walk` | `player_walk_free` | `player_walk_free` | `player_walk_free` |
| run | `player_run` | `player_run_free` | `player_run_free` | `player_run_free` |
| dash | `player_dash` | `player_dash` | `player_dash` | `player_dash` |
| 오버레이(휴대) | `katana_carry_<동작>` | `greatsword_carry_<동작>`(등) | `dagger_carry_<동작>`(손 역수) | `bow_carry_<동작>`(5단계) |
| 오버레이(뽑아 든) | `katana_carry_drawn_<동작>` | `greatsword_carry_drawn_<동작>`(오른손으로 낮게 끎) | 없음 | 없음 |

- `_gs`(대검 전용 몸)·`_bow`(활 전용 몸)는 만들지 않았다 — 등에 멘 대검은 두 손이 비고, 뽑아 든 대검은 오른손 한 손으로 끌며, 활은 왼손이 내려 든 자세로 `_free` 위에서 읽힌다(활은 5단계에서 다시 확인).
- 대검 뽑기·넣기 몸 끝 프레임을 `player_idle_free 0` 으로 바꿨다(`gear3.GEAR[...].idleBody = "free"`). 등 손잡이를 쥔 키는 등에 멘 방향(-100°, -56°)·높이(z 65)에 맞춰 고쳤다 → `player_greatsword_draw/sheathe` 몸 PNG 만 바뀜. 나머지 2차 몸 PNG 는 바이트 동일, JSON 은 `weaponOverlayV3` 연결 + `oldWeapon: null`.

## 3. 타이밍 대응

- 칼: `hero_v3/export.py` assert 그대로(연격 hitAt·판정 끝·cancelAt·total = v2, 뽑기·넣기·패링 단계 시작 = 구 16×24) — 프레임 정의를 건드리지 않았다.
- 대검·단검: 오버레이 = 2차 몸 시트와 **같은 프레임 수·같은 ms**. `wv3.check_gear_timing` 이 몸 JSON ms 와 같음 + `export2.check_timing`(구 프레임 시작 ms·total·timingMs 항목·판정 끝)을 다시 assert → JSON `timingCheck`.

| 시트 | 프레임 | 확인 항목 |
|---|---|---|
| greatsword_combo1 / 2 / 3 | 12 / 12 / 14 | hitAt · cancelAt · total · 프레임 시작 · 판정 끝 |
| greatsword_dashslash / slam | 13 / 16 | hitAt · recoverFrom / impactAt · leapStart · total · 판정 끝 |
| greatsword_draw / sheathe / special | 7 / 7 / 12 | 프레임 시작 · total |
| dagger_combo1 / 2 / 3 | 6 / 6 / 8 | hitAt · cancelAt · total · 판정 끝 |
| dagger_special | 9 | 프레임 시작 · total |

## 4. 무기별 그림

- **칼 B 재 칼날** (`hero_v3/katana3.py`): 날 = 재 G5·G4·G3·G2(빛 쪽 → 등) + 날선 1px 호박(7칸마다 한 칸 어둡게 = 끊긴 균열) + 휨(최대 1.6 도트, 화면 길이에 비례) + 등 쪽 재 결손 3칸 + 하바키(쇠 깃). 코등이 = 흉갑 조각(IRON SL2·4·6, 한쪽 모서리 깨짐). 손잡이 = 사선 붕대(PL1·PL2) + 재 덩이 끝. 칼집 = 금 간 재·흙(G1~G4, 빛 테 G4) + 1px 호박 이음매 3곳 + 쇠 입구테 + 붕대 끈. 넣기 '딸깍' 반짝은 A26·A25·A23.
- **대검 A 녹슨 양손검** (`greatsword.py`): 7차선 날(빛 날 G8 · 빗면 G7 · 면 G6 · 홈 G5 · 면 G6 · 빗면 G5 · 그늘 날 G4) + 녹 얼룩 5곳(A18, 가장자리 A19 한 점) + 이 빠짐 7칸 + 가장 깊은 홈에 혼불 1점 + 갈고리(±5) + 가죽 리카소 + 긴 십자 코등이(±7, 끝이 날 쪽으로 굽음) + 박힌 화살촉(촉 2 · 부러진 대 5 · 깃 2) + 가죽 손잡이·쇠고리·둥근 폼멜. 등 휴대 = 가죽끈 고리 2개, 몸이 숙으면(측면) 같이 기움.
- **단검 B 재 껍데기 송곳니** (`dagger.py`): 붕대 밑동 → 불룩한 배(6) → 빛 쪽으로 치우친 끝. 빛 쪽 깨진 날 G6, 재 비늘 면 G4/G5·G3/G2, 그늘 쪽 셀아웃(역수로 팔뚝과 겹쳐도 떨어져 보임), 갈라지는 균열 2줄, 끝 4도트 A23→A25. 붕대 손잡이를 꿰뚫은 녹슨 못.
- 넓은 날(대검·단검)은 `wv3.fill_blade`(픽셀마다 축·법선 거리로 차선 선택)로 그린다 — 줄 긋기(stroke)는 기울어진 넓은 날에서 차선이 엇갈려 사다리·톱니 잔무늬가 생겼다.

## 5. 자기 비평 (see → critique → fix)

### 칼 B
1. 날 몸을 G2~G4 로 하니 어두운 바닥·몸 위에서 날 폭이 사라지고 호박 날선 한 줄만 남아 '빛나는 막대'로 읽힘 → 날 몸을 한 단 밝게(G5/G4/G3, 등 G2), 셀아웃 차선 대신 등 그늘.
2. 판정 프레임이 평소와 거의 같아 Q30(타격 때 밝게)이 안 보임 → glow 에서 날선 A25(끝 쪽 A26) + 날 몸 A21/A19 + 다음 차선 G4 → 2배·1배 모두 판정 프레임이 뚜렷.
3. (확인) 칼집은 어둡지만 빛 테 G4·호박 이음매가 1배에서 허리 선으로 읽힘. 색 16/16.

### 대검 A
1. 날 폭 5 로는 '보통 칼' — 츠바이헨더 무게가 안 읽힘. 정면 등 휴대에서 코등이가 어깨에 가림, 녹 A19 점이 불티처럼 보임 → 폭 7(빗면 2단), 갈고리 ±5, 코등이 ±7, 등 코등이를 어깨 위로(z +3), 녹을 A18 위주로.
2. 녹을 흩뿌린 점이 체크무늬가 되어 톱·사슬처럼 보이고, glow 가 줄무늬 '사다리' → 녹을 얼룩 5곳으로 뭉침, glow 를 양 날 + 홈 불줄 한 줄로 단순화.
3. 그래도 기울어진 넓은 날에 사다리 잔무늬 → 줄 긋기 대신 `fill_blade`(픽셀 단위) → 깨끗한 띠.

### 단검 B
1. 19 도트 바늘로는 1배에서 안 보임, 대기 휴대(θ 165°)는 정면에서 몸 뒤로 숨음 → 24 도트·폭 6 송곳니(시안 비율), 휴대 각도 (140°, -60°)로 엉덩이 바깥에 늘어뜨림.
2. 역수라 팔뚝(붕대)과 겹칠 때 묻힘 → 그늘 쪽 셀아웃 차선 + 빛 쪽 G6 날. 판정 프레임은 균열·끝이 밝아져 찌르기가 읽힘.

## 6. 남은 약점

1. **대검 칼끝이 192 틀 아래로 넘어감**(최대 33 도트, 정면 내리찍기 판정 f8~f11 · 측면 1·3타 회복) — 틀 아래 여백이 발밑 6 도트뿐인데, 정면에서 앞쪽 땅으로 향한 날은 화면상 발보다 아래로 내려온다. 2차 몸의 `weaponLocal` 각도를 지켜서 생김 → 질문 1. (뽑아 든 휴대는 각도를 바꿔 해결)
2. 대검 뽑기 2~3 프레임 뒷면(up)에서 날이 카메라를 향해 짧은 덩어리로 보임(원근상 맞음).
3. 단검: 정면·뒷면 찌르기는 원근상 짧음(2차 약점 그대로). 그림자 걸음 끝(f8) 측면에서 먼 손 단검이 몸에 가려 안 보임.
4. 대검 연격 마지막 키(45°, -40°)와 뽑아 든 대기(58°, -30°)가 달라 연격 → 휴대 전환 때 날이 살짝 튐(틀 여백 때문에 휴대 각을 올렸음).
5. 칼 넣기 '딸깍'(f6) 반짝은 손에 일부 가려짐(이전과 같음). 1배에서 칼집은 어두운 편.
6. 이펙트(기본 공격·갈래)는 이번 범위 밖 — `bladeTipAnchors`·`glowRule` 을 다음 단계 기준으로 씀.

미리보기(이 폴더): `preview_<시트>_x2.png`(전 프레임 2배, 노란 테 = 판정) · `preview_<시트>_x3.gif` · `preview_mock_lit.png`(1배 조명 합성: 칼 휴대·1타 / 대검 등·1타·끎 / 단검 역수·1타) · `preview_compare_old.png`(구 ↔ 새). 칼 미리보기는 `hero_v3/preview_katana_*`·`preview_carry_*`.
