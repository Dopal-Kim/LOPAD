# 무기 v3 — 53라운드 Q19·Q26~Q32·Q44~Q46 무기 재디자인 (칼 B · 대검 A · 단검 B · 활 B+화살 뽑기)

근거: `decisions/2026-10-03-round-53-playtest4.md` Q18~Q21(무기별 기본 자세·`player_attack` = 활 빠른 사격), Q26~Q32(무기 방향·빛·대검 휴대·색). 시안 `gemini/concept_weapons/raw_{katana_B2,greatsword_A2,dagger_B,bow_B}.jpg` 는 **참고만** — 도트는 전부 직접(Gemini 미사용).
재현: 칼 = `python3 parts/art/work/hero_v3/build.py`(칼 B 는 `katana3.py` 안) → 무기 = `python3 parts/art/work/weapons_v3/build.py [free] [greatsword] [dagger] [bow]` → 비교 = `python3 parts/art/work/weapons_v3/compare.py`. 전부 결정적(두 빌드 경로에서 같은 바이트 — `build2.py greatsword_draw` 재실행으로 md5 대조).

## 진행 상황 (2차 — Q44~Q46 반영)

| 단계 | 상태 |
|---|---|
| 1 칼 B | 완료 → **Q44 폭 +1(5차선)·날 몸 한 단 밝게(G6~G3)**, 넓은 날 래스터(`K.fill_blade`)로 바꿈. 몸 시트 바이트 동일 |
| 2 기본 자세 몸 | 완료 — `player_{idle,walk,run}_free` · 대쉬 `player_dash` 공용 (Q46 규칙 확정) |
| 3 대검 A | 완료 → **Q44 '몸만한 칼'**(날 90 + 손잡이 21 도트, 폭 9) · **Q45 대검만 확대 틀 248×272** |
| 4 단검 B | 완료 → **Q44 폭 +1(최대 7)·한 단 밝게(G7~G3)** |
| 5 활 B | **완료** — `bow_aim` · `bow_reload` · `bow_attack` · `bow_carry_{idle,walk,run,dash}` + `player_bow_reload` 몸 = 몸에 꽂힌 화살 뽑기 |
| 6 산출 | 완료 — 2배 전 프레임 · 3배 gif · 1배 조명 합성 4무기 · 구↔새 비교(4무기 8칸) |

## 1. 규격표

| 항목 | 값 |
|---|---|
| 무기 시트(칼·단검·활) | **192×192** · 피벗 **(96,186)** · `playerFrameOffset` (48,48) |
| 무기 시트(대검, Q45) | **240×272**(Q55 재출력, 이전 248) · 피벗 **(119,209)** · `playerFrameOffset` **(71,71)** — 448 캔버스에 그린 뒤 대검 전 시트(28장) 합집합 + 몸 사각형 + 여백 2 로 한 틀(8 배수)로 자름. 피벗 = 몸 피벗 (48,138) + 오프셋. 잘림 0 assert |
| 공통 | `pixelScale` 0.5 · `depth` 항상 above + `occlusionBaked` · 반투명 0 |
| JSON (칼 v3 규약) | `gripAnchors`(쥔 손, 활 = handL) · `handAnchors` · `bladeLocal`(활 휴대 `bowLocal`) · `bladeTipAnchors`(무기·화살 끝) · `carryHidden` · `bodySheet` · `bodySheetByWeapon` · `design`/`glowRule`/`colorBudget`(대검 `sizeNote`) · 동작 시트는 몸 JSON 판정 필드 그대로 + `timingCheck` |
| 색 | 칼 **16** · 대검 **14** · 단검 **14** · 활 **15** (각 16 이하, 전부 주인공 30색 팔레트 안, X 미사용) — build assert |
| 빛(Q30) | 평소 1px 은은(A21·A19, 끝 A23) · 판정/발사 프레임만 밝게(A25·A26). 활은 시위가 유일한 빛나는 선: 평소 A21 · 당김 A23 · 가득 A25 · 놓는 순간 A26 번쩍 |
| 치수(도트) | 칼 날 55 × 폭 5(+날선) · 칼집 57 / 대검 날 90 × 폭 9 + 손잡이 21, 코등이 21, 갈고리 15 / 단검 24 × 최대 7 / 활 60(활대 폭 4, 끝 갑옷 5) · 화살 51 |

## 2. 이동 몸 시트 선택 규칙 (Q19 제안 → Q46 확정, 계약 §13)

모든 휴대 오버레이 JSON 과 `player_*_free` JSON 에 `bodySheetByWeapon` 으로 같은 표를 넣었다.

| 동작 | 칼 | 대검 | 단검 | 활 |
|---|---|---|---|---|
| idle | `player_idle` | `player_idle_free` | `player_idle_free` | `player_idle_free` |
| walk | `player_walk` | `player_walk_free` | `player_walk_free` | `player_walk_free` |
| run | `player_run` | `player_run_free` | `player_run_free` | `player_run_free` |
| dash | `player_dash` | `player_dash` | `player_dash` | `player_dash` |
| 오버레이(휴대) | `katana_carry_<동작>` | `greatsword_carry_<동작>`(등) | `dagger_carry_<동작>`(손 역수) | `bow_carry_<동작>`(왼손에 내려 듦) |
| 오버레이(뽑아 든) | `katana_carry_drawn_<동작>` | `greatsword_carry_drawn_<동작>`(오른손으로 낮게 끎) | 없음 | 없음 |

- `_gs`·`_bow` 전용 몸은 만들지 않았다(Q46 확정) — 등에 멘 대검은 두 손이 비고, 뽑아 든 대검은 오른손으로 낮게 끌며, 활은 왼손에 내려 든 채 `_free` 위에서 읽힌다(1배 합성 확인).
- 대검 뽑기·넣기 몸 끝 프레임을 `player_idle_free 0` 으로 바꿨다(`gear3.GEAR[...].idleBody = "free"`). 등 손잡이를 쥔 키는 등에 멘 방향(-100°, -56°)·높이(z 65)에 맞춰 고쳤다 → `player_greatsword_draw/sheathe` 몸 PNG 만 바뀜. 나머지 2차 몸 PNG 는 바이트 동일, JSON 은 `weaponOverlayV3` 연결 + `oldWeapon: null`.

## 3. 타이밍 대응

- 칼: `hero_v3/export.py` assert 그대로(연격 hitAt·판정 끝·cancelAt·total = v2, 뽑기·넣기·패링 단계 시작 = 구 16×24).
- 대검·단검·활: 오버레이 = 2차 몸 시트와 같은 프레임 수·같은 ms. `wv3.check_gear_timing` = 몸 JSON ms 동일 + `export2.check_timing`(구 프레임 시작 ms·total·timingMs·판정 끝) → JSON `timingCheck`.

| 시트 | 프레임 | 확인 항목 |
|---|---|---|
| greatsword_combo1 / 2 / 3 | 12 / 12 / 14 | hitAt · cancelAt · total · 프레임 시작 · 판정 끝 |
| greatsword_dashslash / slam | 13 / 16 | hitAt · recoverFrom / impactAt · leapStart · total |
| greatsword_draw / sheathe / special | 7 / 7 / 12 | 프레임 시작 · total |
| dagger_combo1 / 2 / 3 · special | 6 / 6 / 8 · 9 | hitAt · cancelAt · total · 판정 끝 / 프레임 시작 · total |
| bow_aim | 8 | 프레임 시작 · total · release f6 (620ms) · 진행도 f0~5 |
| bow_reload | 10 | 프레임 시작 · total · refill f6 (310ms) · 진행도 식 min(9, floor(p×10)) 그대로 |
| bow_attack (= player_attack) | 7 | 프레임 시작 · total · release f3 (150ms) |

## 4. 무기별 그림

- **칼 B 재 칼날** (`hero_v3/katana3.py`): 날 = 재 G5·G4·G3·G2(빛 쪽 → 등) + 날선 1px 호박(7칸마다 한 칸 어둡게 = 끊긴 균열) + 휨(최대 1.6 도트, 화면 길이에 비례) + 등 쪽 재 결손 3칸 + 하바키(쇠 깃). 코등이 = 흉갑 조각(IRON SL2·4·6, 한쪽 모서리 깨짐). 손잡이 = 사선 붕대(PL1·PL2) + 재 덩이 끝. 칼집 = 금 간 재·흙(G1~G4, 빛 테 G4) + 1px 호박 이음매 3곳 + 쇠 입구테 + 붕대 끈. 넣기 '딸깍' 반짝은 A26·A25·A23.
- **대검 A 녹슨 양손검** (`greatsword.py`): 9차선 날(빛 날 G8 · 빗면 G7 · 면 G6 ×2 · 홈 G5 · 면 G6 ×2 · 빗면 G5 · 그늘 날 G4, Q44) + 녹 얼룩 5곳(A18, 가장자리 A19 한 점) + 이 빠짐 7칸 + 가장 깊은 홈에 혼불 1점 + 갈고리(±5) + 가죽 리카소 + 긴 십자 코등이(±7, 끝이 날 쪽으로 굽음) + 박힌 화살촉(촉 2 · 부러진 대 5 · 깃 2) + 가죽 손잡이·쇠고리·둥근 폼멜. 등 휴대 = 가죽끈 고리 2개, 몸이 숙으면(측면) 같이 기움.
- **단검 B 재 껍데기 송곳니** (`dagger.py`): 붕대 밑동 → 불룩한 배(6) → 빛 쪽으로 치우친 끝. 빛 쪽 깨진 날 G6, 재 비늘 면 G4/G5·G3/G2, 그늘 쪽 셀아웃(역수로 팔뚝과 겹쳐도 떨어져 보임), 갈라지는 균열 2줄, 끝 4도트 A23→A25. 붕대 손잡이를 꿰뚫은 녹슨 못.
- **활 B** (`bow.py`): 활대 = 재·흙(빛 쪽 G6 · G5 · 흙 WD2/G4 · 그늘 G3) + 호박 균열 4점, 양 끝 갑옷 조각(SL6·SL4·SL2), 줌통 붕대. 시위 1px 혼불(위 빛 규칙). 재 화살 = 대 G5/G3 · 깃 G6/G5 · 촉 A21→A25(가득이면 끝 A26). 조준 방향 = 시위 손 → 줌통 손(화살이 줌통을 지남), 당긴 만큼 활 끝이 더 휨. 조준 초반(p < 0.2)은 화살이 재로 맺히는 중(점선).
- **활 장전 = 몸에 꽂힌 화살 뽑기** (`gear3.GEAR["bow_reload"]`, `hero.pose(arrowOut)`): f0·1 오른손이 오른어깨 뒤로 → f2 꽂힌 화살을 쥠 → f3 위·바깥으로 뽑음(몸의 그 화살 사라짐) → f4·5 앞으로 가져오며 촉이 달아오름 → **f6 refill**: 시위에 대면 재로 부서져 시위에 스밈(시위 A25) → f7 부서짐 끝 → f8 시위 A23 → f9 뽑힌 자리에서 재가 메워 화살이 다시 돋음(불티). 뽑힌 자리 불티는 등 쪽에서 보임. `hero.py` `arrowOut`(기본 False = 다른 시트 바이트 동일).
- 넓은 날(칼·대검·단검)은 `K.fill_blade`(katana3, 칼은 휨 `off_fn` 포함)(픽셀마다 축·법선 거리로 차선 선택)로 그린다 — 줄 긋기(stroke)는 기울어진 넓은 날에서 차선이 엇갈려 사다리·톱니 잔무늬가 생겼다.

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

### 2차 (Q44 굵고 크게 · Q45 대검 틀)
1. (칼) 폭 +1 을 줄 긋기로 하니 기울어진 날에 잔무늬 → `fill_blade` 에 휨(`off_fn`)을 넣어 칼도 픽셀 단위 래스터. 칼끝 기울기를 차선별로(끝으로 갈수록 등 쪽부터 잘림). 한 단 밝게 하며 G6 추가 → 칼집 그늘 G1 을 G2 로 올려 16색 유지.
2. (대검) 66 → 90 도트, 폭 9, 코등이 21 로 키우니 등 휴대가 종아리까지 내려와 '몸만한 칼'로 읽힘. 192 틀 대신 캔버스 448 에 그려 합집합으로 자름 → 248×272, 잘림 0(이전 최대 33 도트 넘침 해소).
3. (활 1) 화살(24)이 가득 당김(32)보다 짧아 촉이 활 뒤에 묻히고 어두운 대가 몸에 사라짐 → 화살 34, 대 한 단 밝게. 활대 3차선은 1배에서 실선 → 4차선 + 한 단 밝게. 휴대 활이 정면에서 옆면만 보여 막대로 읽힘 → 조준축을 바깥·앞(-60°)으로 돌려 곡선이 보이게.
4. (활 2) 가득 당김에서 촉이 활 앞으로 나와 호박 점으로 읽힘, 장전 f4 에 뽑은 화살(깃·촉)이 가슴 앞을 가로지름 — 1배 합성에서 활 곡선·시위가 읽힘.

## 6. 남은 약점

1. ~~대검 연격 마지막 키(45°, -40°) 칼끝이 바닥 아래~~ → **53라운드 Q55 해결(3차)**: 회복 키 elev -40° → -30°~-33°, 끝 키 = 휴대 각 (58°, -30°) `gear3.GS_END`·`DRAWN_GS`. build assert 2개 — ① 대검 시트 전 프레임 칼끝 높이 ≥ 0(내리찍기 박힘 f4·f5 제외, `gear3.gs_tip_z`) ② 연격 1·3타·대쉬 베기·내리찍기·가드 끝 프레임 칼끝 ↔ `greatsword_carry_drawn_idle` 0 칼끝 거리 ≤ 11 도트(측정 최대 10.5, 이전 최대 40). 판정 시점(timingCheck) 그대로. 대검 틀이 248 → **240×272**, `playerFrameOffset` (71,71), 피벗 (119,209) 로 1~2 도트 바뀜(합집합 자동 맞춤 — JSON 을 읽으면 됨). 몸 PNG 재출력: `player_greatsword_{combo1,combo3,dashslash,slam,special}`.
2. 대검 뽑기 2~3 프레임 뒷면에서 날이 카메라를 향해 짧은 덩어리(원근상 맞음). 대검 판정 glow 는 1배에서 줄무늬처럼 보임(양 날 + 홈 불줄).
3. 단검·대검: 정면·뒷면 찌르기·앞 베기는 원근상 짧음(2차 약점 그대로). 단검 그림자 걸음 f8 측면은 먼 손이라 몸에 가림.
4. 활: 오른쪽 보기 휴대는 왼손이 먼 쪽이라 활이 몸에 가려 일부만 보임. 가득 당김의 화살대는 팔 위를 지나 어두운 팔과 겹침(촉·시위로 읽힘). 장전 f9 화살이 '다시 돋음'은 해석(재가 메움) — 시트에서 화살이 한 프레임에 돌아옴.
5. 칼 넣기 '딸깍'(f6) 반짝은 손에 일부 가려짐. 1배에서 칼집은 여전히 어두운 편.
6. 이펙트(기본 공격·갈래)는 `parts/art/work/fx_weapons_v3/` 에서 v3 로 다시 그림(53라운드 Q5).

미리보기(이 폴더): `preview_<시트>_x2.png`(전 프레임 2배, 노란 테 = 판정) · `preview_<시트>_x3.gif` · `preview_mock_lit.png`(1배 조명 합성 4무기: 칼 휴대·1타 / 대검 등·1타 / 단검 역수·1타 / 활 휴대·가득) · `preview_compare_old.png`(구 ↔ 새). 칼 미리보기는 `hero_v3/preview_katana_*`·`preview_carry_*`.
