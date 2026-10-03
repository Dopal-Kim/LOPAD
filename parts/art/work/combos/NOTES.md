# combos — 근접 3연격 · 무기 든 특수 동작 (48라운드 Q2) + 49라운드 무기 휴대·동작 강화 (2026-10-02)

> **[53라운드 보관]** 이 기록의 산출물 중 `assets/sprites/player/player_*` 전부와 `weapons/katana_{combo1..3,special}` 는 삭제됨(도영 님 "옛 주인공은 거의 안 남도록", 시스템이 더 이상 로드하지 않음). `combos/build.py` 는 `--legacy` 없이는 실행되지 않는다. 대체: `player/v3`·`weapons/v3/katana_*`. 대검·단검·활 구 오버레이와 fx 는 남아 있음.

> **49라운드 개정은 아래 6~9절.** 대검 1~3타와 칼 1타는 6절 표가 2절 표를 대체한다(나머지 행은 그대로 유효).

빌드: `python3 parts/art/work/combos/build.py` (약 6초, 재실행 시 전부 재생성). 근거: `decisions/2026-10-02-round-48-playfeel-route.md` Q2, 계약 `contracts/art-assets.md` §6.1·§6.2(+§3·3.1·3.2), `fx-design.md`, `art-bible.md`.
리그 재사용(읽기만): `work/player/build.py`(몸) · `work/weapons/build.py`(칼날·활 어휘) · `work/fx_concept/build.py`(Canvas·호·광선·꼬리). 기존 `player_attack`·`weapons/<w>_attack`·`fx/<w>_slash` 는 건드리지 않았다.

## 1. 산출물 (35 시트 = PNG 35 + JSON 35)
- 3연격 × 3무기: `player/player_<w>_combo<n>` 16×24 · `weapons/<w>_combo<n>` 48(대검 64) · `fx/<w>_combo<n>` (칼 96 · 대검 128 · 단검 64). 4방향(down/up/left/right), 피벗 = 주인공 발.
- 특수 동작: `player/player_{katana,greatsword,dagger}_special` + `weapons/<w>_special`, `player/player_bow_aim` + `weapons/bow_aim`.
- 미리보기: `preview_{katana,greatsword,dagger}.png`(몸+무기 4배 · fx 2배), `preview_specials.png`(오른쪽 = 기존 보조 fx 겹침), `preview_mock_1x.png`(월드 480×270 실픽셀) · `preview_mock_2x.png`(카메라 2배 화면 960×540) · `preview_mock_2x_down.png`, `preview_strip_1x.png`, `gif/<w>_chain_right.gif`(가장 빠른 취소로 1→2→3타 시간축).

## 2. 규격 표 (시스템 전달용)
공통: 프레임 번호 기준 = 몸 시트. 무기 시트는 같은 프레임 번호·같은 ms, `depth` up = below, 나머지 above. 이펙트는 `anchor: player_pivot`, `spawn: attack_frame2`, `impactFrame: 1` — fx f0(예비 40ms)를 판정 40ms 전에 재생해 fx f1 시작 = 몸 f1 시작 = 판정. 판정 원점 = 몸 중심 = 발 위 10px. 각도는 right 기준 화면각(0 = 정면, + = 아래), down = +90°, up = −90°, left = 180−θ.

| 시트 | 몸 프레임 · ms | hitFrames | cancelFromFrame (ms) | 판정 메모 | 무기 | fx 크기 · 프레임 · ms · 피벗 | 트레일·섬광·흔들림 |
|---|---|---|---|---|---|---|---|
| ~~katana_combo1~~ → 6절 | 4 · 90/40/120/100 (350) | [1] (90ms) | 3 (250) | R33 · 140° (−70→70) | 48 (24,39) | 96 · 5 · 40/50/60/70/90 · (48,58) | W1 0.6/120 f2 |
| katana_combo2 | 3 · 40/40/90 (170) | [1] (40) | 2 (80) | R33 · 130° (65→−65 역방향) | 48 | 96 · 4 · 40/40/50/80 | W1 0.6/120 f2 |
| katana_combo3 | 4 · 40/40/100/140 (320) | [1] (40) | — (연격 끝) | R33 · 170° (−85→85) | 48 | 96 · 6 · 40/40/60/80/100/120 | W1 0.7/180 · 섬광 X1 0.12 f1 · 1px/50 |
| ~~greatsword_combo1~~ → 6절 | 4 · 160/60/120/140 (480) | [1] (160) | 3 (340) | R51 · 190° (−110→80) | 64 (32,47) | 128 · 6 · 40/60/70/80/100/120 · (64,74) | W1 0.6/160 · 2px/60 |
| ~~greatsword_combo2~~ → 6절 | 4 · 140/60/120/140 (460) | [1] (140) | 3 (320) | R51 · 200° (100→−100 역방향) | 64 | 128 · 6 · 같음 | W1 0.6/160 · 2px/60 |
| ~~greatsword_combo3~~ → 6절 | 5 · 200/60/70/140/180 (650) | [1] (200), active [1,2] | — | R51 · 270° (−150→120) | 64 | 128 · 7 · 40/50/70/90/110/130/160 | W1 0.7/220 · 섬광 W3 0.12 f1 · 3px/90 |
| dagger_combo1 | 3 · 50/40/70 (160) | [1] (50) | 2 (90) | 찌르기 L24 × W8, 각 −8° | 48 | 64 · 4 · 40/40/50/70 · (32,42) | — |
| dagger_combo2 | 3 · 40/40/70 (150) | [1] (40) | 2 (80) | 찌르기 L24 × W8, 각 +10° | 48 | 64 · 4 · 같음 | — |
| dagger_combo3 | 4 · 60/40/70/110 (280) | [1] (60) | — | 찌르기 L28 × W10, 각 0° | 48 | 64 · 5 · 40/40/50/60/90 | 1px/40 |

가장 빠른 취소 기준 타격 간격: 칼 0 → 200 → 80ms("씽 · 씽씽"), 대검 0 → 320 → 380ms("훙 훙 훙"), 단검 0 → 80 → 100ms("슈슈슉").
JSON 필드: `comboIndex, comboLength, nextCombo, hitFrames, activeFrames, cancelFromFrame, timingMs{hitAt, cancelAt, total}, hitRadiusPx, arcDeg, arcFromDeg, arcToDeg` 또는 `thrust{lengthPx, widthPx, angleDeg, fromPx}` + 무기 `frameStates`.

| 특수 시트 | 프레임 · ms | 메모 (JSON) | 겹치는 기존 fx |
|---|---|---|---|
| katana_special (패링) | 5 · 50/90/120/70/110 | phases ready[0] window[1,2] riposte[3] recover[4], holdFrame 2 (창이 길면 유지), 성공 = f3·f4, 실패 = f4 | parry_flash (parry_success, 접점) |
| greatsword_special (가드) | 6 · 80/160/160/60/90/130 | enter[0] hold[1,2] **loopFrames [1,2]** (누르는 동안) release[3,4] recover[5] | guard_wave · ironwall (guard_release = f4) |
| dagger_special (그림자 걸음) | 5 · 50/60/70/80/140 | depart[0,1] arrive[2,3] primed[4], teleportAfterFrame 1, holdFrame 4 (primeMs 동안) | shadowstep_ghost (출발점, f2 시점) |
| bow_aim (조준) | 7 · 100×5/120/80 | progressDriven, progressFrames 0~5 `frame = min(5, floor(progress*5))`(aim_charge 와 같은 식), releaseFrame 6 (화살 생성 = f6 시작, 취소면 생략), drawPx 0~5 | aim_charge · aim_line |

## 3. 임시 결정 (도영 님 검수 대상)
1. **판정 반경 산출**: 단계 데이터(`data/**`)는 열람 금지라 공개 결정 로그(11b·14라운드)의 판정값으로 계산 — 먼 끝 = 리치 + 히트박스 짧은 변/2 (칼 14+8 = 22 · 대검 20+14 = 34 · 단검 10+6 = 16) × 1.5 = **칼 33 · 대검 51 · 단검 24(3타 28)**. 호의 바깥 가장자리 = `hitRadiusPx`(그림 = 판정). 시스템 실제값이 다르면 시스템 값이 우선이고, 알려 주면 반경만 바꿔 재빌드한다(상수 `HIT`).
2. **대검 범위 크기**: R51 = 카메라 2배에서 지름 204 화면 px(화면 높이의 약 38%). '크고 묵직함'에는 맞지만 큰 편. 대안: 리치만 1.5배(R30 안팎, 128 → 96 캔버스).
3. **이펙트 캔버스**: 칼 96 (피벗 48,58) · 대검 128 (64,74, §3.2 크기 표 밖) · 단검 64 (32,42). 반경이 커서 기존 48 에 들어가지 않는다.
4. **연격 리듬(ms)**·**cancelFromFrame**: 위 표. 칼은 1타 뒤 취소를 늦게(f3) 두어 '씽 · 씽씽' 간격을 만든다. 대검 3타 판정은 f1 시작 1회 + `activeFrames [1,2]`.
5. **단검 찌르기 판정 폭** W8(3타 W10)·각도 −8°/+10°/0°(세 줄기가 부채꼴로 갈라짐) — 폭은 1.5배 하지 않았다(찌르기 느낌 유지).
6. **3타 섬광·흔들림**: 칼 X1 0.12 + 1px/50ms, 대검 W3 0.12 + 3px/90ms(1·2타 2px/60ms), 단검 3타 1px/40ms. fx-design 의 기본 공격 '흔들림 없음' 규칙에서 연격 마지막 타만 예외.
7. **무기 상태 연출**: 1타 f0 = 실체화(호박 윤곽), 2·3타는 손에 든 채 시작, 1·2타 마지막(취소되면 안 보이는 복귀 프레임) = 흩어지는 호박 윤곽, 3타 마지막 = 불티. 정면·후면 복귀 프레임은 칼날을 아래로 60% 끌어내려 얼굴을 가리지 않게.
8. **대검 가드 자세**: 옆면 = 칼을 세워 벽, 정면·후면 = 허리 높이 가로(왼손은 날을 받침). 
9. **활 조준**: 활 위치는 기존 bow_attack 과 같은 방향별 고정점, 시위 손 0→5px. f0 화살은 호박 윤곽으로 실체화, f5 촉 글린트, f6 발사(시위 복귀 떨림).
10. **범위 밖(미제작)**: 진화 대쉬 계열(발도술·허보·질풍·잔상)의 '무기 든 대쉬' 몸 자세는 이번 지시 목록에 없어 만들지 않았다. 필요하면 `player_<w>_dash_armed` 같은 이름으로 추가 인터뷰.

## 4. 색 예산 (마지막 실행 35 시트 ALL OK)
- 몸: 기존 주인공 팔레트 그대로(무채 10 + 림 G04 + 강조 21·23), 새 색 없음.
- 무기: 무채 G00·G05·G08·G13 + 층 강조 ≤7(17·19·21·22·24·25·27), fx 블록 미사용.
- fx: 칼·단검 = 보조 4 + 코어 2 + 층 강조 22·24·27 = 9, 대검 = 보조 4 + 코어 2 + 재 G06·G09 + 층 24·27 = 10 (≤11). 고립 0 · 반투명 0.

## 5. see → critique → fix
1. 1회차: 정면·후면 복귀 프레임에서 칼날이 어깨 높이 가로로 얼굴을 가림(옆면 '내린 칼' θ90 이 정면에서는 가로) → 정면·후면의 fade/embers 프레임만 화면 아래로 60% 끌어내림. 단검 찌르기 줄기가 3px 바늘로 1배에서 약함 → 최대 폭 5→7(3타 6→8.5), 그림자 줄기 3→4 · 간격 4.5, 시작점 몸 중심 +4 → +7. 목업에서 대검 R51 이 미니 장면(90px 높이)을 넘음 → 판정과 같은 크기라 유지, 임시 결정 2 로 보고.
2. 2회차: 특수 동작 미리보기에서 guard_wave·shadowstep_ghost 가 불투명 칸 뒤에 묻힘(미리보기 버그) → 투명 합성. 아래 방향 목업에서 회전한 호·균열 정상, 단검 줄기 가독 OK.
3. 3회차(1배 실픽셀 띠): 은빛 초승달 · 용암 고리 · 보라 찌르기가 모양만으로 구분됨, 3타가 각 무기에서 가장 큼. 정면 찌르기가 다리 위를 지나는 것은 탑다운 정면 찌르기의 성질로 수용. SHIP.

---

# 49라운드 개정 — 무기 휴대 · 동작 강화 (2026-10-02)

근거: `decisions/2026-10-02-round-49-playtest2.md` 4절(무기 휴대)·5절(무기 동작·자원), 계약 `contracts/art-assets.md` §7.1·§7.2 (+ §3·3.1·6.1·6.2).
빌드 2개 (각각 재실행 시 전부 재생성, 서로 독립):
- `python3 parts/art/work/combos/build.py` (약 14초) — 기존 48라운드 시트 + 대검 1~3타 재제작 · 칼 1타 발도 · 내리찍기 · 대쉬 베기 · 단검 가열 · 활 장전.
- `python3 parts/art/work/carry/build.py` (약 4초) — 휴대 오버레이 · 뽑아 든 상태(임시) · 칼/대검 뽑기·넣기.
- 공용 기하 `combos/gear.py`: 칼집·등 대검·역수 단검·손 활의 자리, 두 손 자세, **가림 굽기**(아래 6.0).
- 몸 리그(`work/player/build.py`)는 읽기만. player_idle/walk/dash 를 리그로 다시 그려 기존 PNG 와 **픽셀 단위로 같음**을 확인한 뒤, 그 자세표에서 손·허리·등 위치를 프레임마다 뽑았다.

## 6.0 공통 규약 (시스템 전달)
- 모든 49라운드 무기 시트: 행 = down/up/left/right, 열 = 몸 시트와 같은 프레임 번호·같은 ms, 피벗 48 (24,39) / 64 (32,47) = 주인공 (8,23), `anchor: player_pivot`, `playerFrameOffset` = 주인공 프레임 원점.
- **가림 굽기(`occlusionBaked: true`)**: 몸 뒤로 가야 하는 부분(먼 허리 칼집, 등의 대검 날, 어깨 너머로 젖힌 칼날, 몸 너머를 향한 칼날)은 그 프레임의 몸 실루엣으로 **이미 지워 두었다**. 그래서 한 시트에 앞·뒤가 섞여도 `depth` 하나로 겹칠 수 있다.
  - `depth` = 방향별 문자열(기존 형식 그대로) — 앞 층이 있는 방향은 `above`, 몸 뒤뿐인 방향은 `below`. `depthByFrame` = 방향별 프레임 목록(현재 방향 안에서 모두 같음).
  - 대검 1~3타·칼 1타의 `depth` 가 바뀌었다: 48라운드 `up = below` → 49라운드 **네 방향 모두 `above`(가림 굽기)**. 시스템이 JSON 의 depth 를 읽으면 코드 변경 없음.
- 몸 시트는 리그 색만(새 색 없음). 무기는 무채 G00·G05·G08·G13 + 층 강조(칼집 옻칠 17·19·20, 감개 21, 글린트 25·27 등). 이펙트는 fx 블록(백열 코어 + 무기 보조 램프).

## 6. 대검 1~3타 재제작 (두 손 큰 휘두름) · 칼 1타 발도 베기
대검: 두 손 잡기(옆면 = 먼 팔을 몸 뒤로 그려 두 번째 손을 자루머리 쪽 2px 에), 2단 예비(어깨 위로 끌어올림 → 최대 비틀림·뒷발에 무게·웅크림) → **훙(판정)** → 끝까지 휘둘러 앞발에 무게 → 칼끝을 땅에 박고 버팀(회복) → 자세 회복. 무기는 등에서 꺼낸 실물이라 실체화 윤곽·불티 소멸 상태를 없앴다(`frameStates` = steel/glow).
칼 1타: f0 = 허리 칼집 손잡이를 쥐고 낮게(칼은 칼집 안), f1 = 뽑으며 벰(판정, 칼집은 빈 채 허리에 남음). 프레임 수·ms·판정·취소는 48라운드와 같다.

| 시트 | 몸 프레임 · ms (합) | hitFrames (ms) | cancelFromFrame (ms) | recoverFrames | fx spawn · fxSpawnAtMs | 판정 메모 | 무기 |
|---|---|---|---|---|---|---|---|
| greatsword_combo1 | 6 · 90/100/60/110/140/130 (630) | **[2]** (190) | 4 (360) | [4,5] | `attack_frame3` · 150 | R51 · 190° (−110→80) 그대로 | 64 (32,47) |
| greatsword_combo2 | 6 · 80/90/60/110/140/120 (600) | **[2]** (170) | 4 (340) | [4,5] | `attack_frame3` · 130 | R51 · 200° (100→−100) 그대로 | 64 |
| greatsword_combo3 | 7 · 100/120/60/70/150/160/160 (820) | **[2]** (220), active [2,3] | — | [4,5,6] | `attack_frame3` · 180 | R51 · 270° (−150→120) 그대로 | 64 |
| katana_combo1 | 4 · 90/40/120/100 (350) | [1] (90) | 3 (250) | — | `attack_frame2` · 50 | R33 · 140° (−70→70) 그대로 | 48 (24,39) |

**바뀐 JSON 규격(시스템 확인 필요)**: 대검 판정 프레임 1 → **2**(예비 2프레임), 프레임 수 4/4/5 → 6/6/7, 총 길이 480/460/650 → 630/600/820ms, cancel 3 → 4. 새 필드 `recoverFrames`·`recoverNote`·`fxSpawnAtMs`(= hitAt − 40, 이펙트 f0 재생 시각)·`revision`. 이펙트 시트(`fx/greatsword_combo*`·`fx/katana_combo1`) PNG 는 **그대로**, JSON 의 `spawn` 이 대검만 `attack_frame2` → `attack_frame3`(= 3번째 프레임 = 판정 프레임) 으로 바뀌었다. `hitRadiusPx 51`·`arcDeg` 는 그대로.

## 7. 새 시트 규격 표 (시스템 전달용)

### 7.1 휴대 오버레이 (`weapons/<w>_carry_<a>`, a = idle·walk·dash)
몸 `player_idle`(6f 220/220/220/180/220/220, loop) · `player_walk`(8f × 110, loop) · `player_dash`(3f 60/90/90) 와 **같은 프레임 수·ms·loop**. 몸과 같은 프레임 번호를 같은 시각에 겹친다.

| 무기 | 휴대 자리 | 캔버스 · 피벗 | depth (down/up/left/right) | 메모 |
|---|---|---|---|---|
| katana | 캐릭터 왼쪽 허리 칼집(손잡이 앞·칼집 뒤). down = 화면 오른쪽 허리(일기장 아래), up = 화면 왼쪽, 옆 = 먼 허리 | 48 (24,39) | above/above/below/below | 칼집 옻칠 = 층 강조 17·19·20(런타임 스왑) |
| greatsword | 등. 무기 손 쪽 어깨 위로 손잡이, 칼끝은 반대쪽 아래. 옆면 = 모자 위로 손잡이가 솟는 사선 | 64 (32,47) | above/above/below/below | down 은 가슴 사선 멜빵(19) |
| dagger | 무기 손에 역수(날이 팔뚝을 따라 위로) | 48 (24,39) | 모두 above | |
| bow | 무기 손에 쥠(정면·후면 = 모서리로 본 세로 활대, 옆 = 활 옆모습이 몸 앞) | 48 (24,39) | 모두 above | |

- 무기 손 = 48라운드 연격과 같은 손(down = 화면 오른쪽 팔, up = 화면 왼쪽 팔, 옆 = 가까운 팔). 걷기 팔 흔들림·대쉬 웅크림·몸 흔들림을 프레임마다 따라간다.
- hurt/death 중의 휴대 표시는 그리지 않았다(시스템 판단 — 제안: hurt 는 carry_idle f0 유지, death 는 숨김).

### 7.1-b 뽑아 든 상태 (임시 추가, `weapons/<w>_carry_drawn_<a>`, 칼·대검)
같은 몸 시트 규격. 칼 = 빈 칼집 + 무기 손에 칼(앞-아래로), 대검 = 등은 비고 무기 손으로 칼끝을 땅에 끌듯 든다. depth 모두 above. **계약 §7.1 목록에 없는 이름**이라 인터뷰 대상(아래 9절 1).

### 7.1-c 뽑기·넣기 (몸 + 무기, 4방향)
| 시트 | 프레임 · ms (합) | phases (JSON) | 시작/끝 자세 |
|---|---|---|---|
| player_katana_draw + weapons/katana_draw (48) | 3 · 70/70/90 (230) | grip[0] pull[1] drawn[2] | 시작 = carry_idle, 끝 f2 = katana_carry_drawn_idle f0 |
| player_katana_sheathe + weapons/katana_sheathe (48) | 4 · 90/90/90/120 (390) | chiburi[0] insert[1,2] click[3] (날밑 글린트) | 시작 = drawn, 끝 → katana_carry_idle |
| player_greatsword_draw + weapons/greatsword_draw (64) | 4 · 90/110/90/110 (400) | grab[0] lift[1] over[2] drawn[3] | 두 손으로 어깨 위 손잡이 → 머리 위 → 앞으로 → 한 손으로 끌어 듦(= greatsword_carry_drawn_idle f0) |
| player_greatsword_sheathe + weapons/greatsword_sheathe (64) | 4 · 100/110/110/120 (440) | lift[0] behind[1] seat[2] release[3] | 끝 f3 = greatsword_carry_idle f0 |

- 연격 1타는 draw 없이 바로 재생해도 이어진다: 칼 1타 f0 = 칼집 손잡이를 쥔 발도 자세, 대검 1타 f0~f1 = 어깨 위에서 끌어올림. draw 시트는 공격이 아닌 동작(패링·가드 등)으로 전투에 들어갈 때.

### 7.2 동작 강화
| 시트 | 프레임 · ms (합) | 핵심 필드 (JSON) | depth |
|---|---|---|---|
| player_greatsword_slam + weapons/greatsword_slam (64) | 8 · 90/110/90/60/90/160/120/130 (850) | `leapFrames [2,3]` (leapStart 200ms) · `impactFrame 4` (350ms) · `recoverFrames [5,6,7]` · `leapOffsetsPx {2:-3, 3:-2}`(제안, 몸 띄우기는 시스템) · `impactDistancePx 21` · `impactOffsetPx` right (23,0) left (−24,0) down (3,13) up (−4,−24) | 모두 above |
| fx/greatsword_slam | 96×96 · 6f 50/60/80/100/120/150 (560) · 피벗 (48,48) = 충격파 판정 원 중심 | `anchor hitbox_center` · `spawn greatsword_slam_impact`(= 몸 impactFrame 시작) · `depth floor` · `scale allowed`(그림 반경 ≈ 40 → 판정 R 이면 R/40, boss_slam 과 같은 규약) · `flash` X1 0.16/60ms f0 · `shake` 4px/120ms · 균열이 정면(방향 행)으로 쏠린 부채꼴 | — |
| player_greatsword_dashslash + weapons/greatsword_dashslash (64) | 7 · 70/90/60/90/120/160/140 (730) | `hitFrames [2]` (160ms) · `recoverFrames [4,5,6]` (310ms~) · `holdFrame 5`(대기를 늘리려면 유지) · R51 · 210° (110→−100) · `fxReuse greatsword_combo2 @ spawnAtMs 120` | 모두 above |
| fx/dagger_combo<n>_heat<k> (n,k = 1..3) | **80×80** · 피벗 (40,50) · 프레임·ms = dagger_combo<n> 과 같음 | `heatLevel k` · `heatOf` · `visualLengthPx` = thrust + 2k · 판정 `thrust` 그대로 · `playbackRateHint` 1.15/1.3/1.5(제안) · heat3 `shake` 1px/40 · anchor/spawn/impactFrame = 기본과 같음 | above |
| player_bow_reload + weapons/bow_reload (48) | 5 · 90/100/120/100/90 (500) | `refillFrame 3` (탄창 충전 = f3 시작, 310ms) · phases reach[0] materialize[1] bring[2] refill[3] settle[4] · `progressDriven: optional` (frame = min(4, floor(progress*5))) | 모두 above |

- 대쉬 베기 전용 이펙트는 범위 밖 → `fx/greatsword_combo2`(같은 방향 호) 재사용 제안을 JSON `fxReuse` 에 적었다.
- 단검 가열: k1 = 보라 몸체 + 코어 확장 + 백열 촉, k2 = 보라→백열 몸체 + 뒤로 한 겹 잔상, k3 = 백열 몸체 + 보라는 가장자리만 + 광선 5. 캔버스는 기본 64 에서 잘려 **80** (§3.2 크기 표 밖 — 9절 4).

## 8. 미리보기 · 검수
- `combos/preview_greatsword.png`·`preview_katana.png`(재생성: 판정 프레임 기준 fx 겹침), `preview_r49_actions.png`(내리찍기 + fx 4방향 · 대쉬 베기 · 활 장전), `preview_dagger_heat.png`(heat0~3 × 1~3타), `preview_mock_r49_1x.png`/`_2x.png`(월드 480×270 · 카메라 2배), `gif/greatsword_slam_right.gif`(도약 오프셋·이동 흉내 포함)·`greatsword_dashslash_right.gif`·`bow_reload_down.gif`·`greatsword_chain_right.gif`·`katana_chain_right.gif`.
- `carry/preview_carry_sword.png`·`preview_carry_hand.png`·`preview_carry_drawn.png`·`preview_drawsheathe.png`, `carry/preview_mock_1x.png`/`_2x.png`(4무기 × idle/walk/dash × 4방향), `carry/gif/carry_walk_<dir>.gif`(4무기 걷기 나란히), `carry/gif/<w>_draw_sheathe_right.gif`(휴대 → 뽑기 → 든 채 걷기 → 넣기 → 휴대).
- 색 예산: combos 51 시트 · carry 26 시트 **ALL OK**(고립 0 · 반투명 0 · 무기 무채 {0,5,8,13} · 무기 강조 ≤7 · fx 합 ≤11).
- see → critique → fix:
  1. 칼집이 정면에서 거의 안 보임 → 칼집을 바깥으로 눕히고 손잡이 4px. 대검이 옆면에서 세운 판자처럼 보임 → 모자 위로 손잡이가 솟는 사선(−0.28). 정면 대검 손잡이가 머리에 가림 → 어깨 바깥으로. 멜빵 G05 가 외투에 묻힘 → 옻칠 19. 가림 뒤 1px 조각 → 굽기 단계에서 제거.
  2. 단검 옆면 가로 막대가 허리띠 장식처럼 보임 → 팔뚝을 따라 세움. 옆면 활이 다리 회색과 섞임 → 기울이기 2회 실패(체커 무늬) → 세로 활대를 손보다 2px 앞(몸 앞)으로.
  3. 칼 1타 발도 호(right −70→70)가 정면·후면에서 화면 오른쪽/왼쪽에서 시작 → 칼집을 그쪽(캐릭터 왼쪽 허리)으로 옮겨 호와 일치.
  4. 대검 예비 자세의 칼날이 옆면에서 얼굴을 가로지름 → '등 쪽 위로 젖힌 칼날 = 머리·등 뒤' 규칙(gear.blade_layer). 내리찍기·뽑기의 '머리 위' 프레임이 정면·후면에서 지면 회전 때문에 옆으로 누움 → 화면각 직접 지정. 후면 충격점이 31px 로 튐 → 멀어지는 칼날 원근 단축(17 → 10px).
  5. 활 장전 화살 묶음이 흰 덩어리 → f1 호박 부채 3개, f2·f3 나란한 화살 2개(사이 1px). 단검 가열 heat1 이 기본과 구분 안 됨 + 64 캔버스에서 광선 잘림 → 램프 재배치 + 80 캔버스.

## 9. 임시 결정 (도영 님 검수 대상)
1. **뽑아 든 상태 시트 `<w>_carry_drawn_{idle,walk,dash}` 추가(칼·대검)** — 계약 §7.1 은 "공격 시작 시 draw, 비전투면 sheathe" 라 그 사이 이동 중 모습이 필요해 만들었다. 이름·사용 여부는 인터뷰.
2. **칼 1타 = 항상 발도**: 납도 전(뽑아 든 상태)에 다시 1타를 치면 f0 이 '칼집 손잡이를 쥔' 그림이 된다. 제안: 연격이 끝나면(3타 끝 또는 취소 창 경과) 짧게 납도(katana_sheathe) — 발도술 느낌. 대안: 뽑아 든 상태에선 1타 f0 을 건너뛰고 f1 부터.
3. **대검 판정 프레임 1 → 2, 총 길이 증가(630/600/820ms)** — '두 손 크게 휘두르고 잠시 이동 제약'을 그림으로 만들기 위한 2단 예비 + 회복 프레임. 이동 제약·기력 소모 시간은 시스템 값, 아트는 `recoverFrames` 로 구간만 표시.
4. **단검 가열 캔버스 80**·`playbackRateHint 1.15/1.3/1.5`(가열 단계별 재생 배속 제안 — 실제 공속 배율은 시스템).
5. **내리찍기 수치**: 도약 [2,3] · 충격 f4(350ms) · `impactDistancePx 21` · 충격파 그림 반경 ≈ 40(scale R/40) · 흔들림 4px/120ms · 섬광 X1 0.16. 도약 거리·몸 띄우기(제안 −3/−2px)는 시스템.
6. **대쉬 베기**: 전용 fx 없이 2타 fx 재사용, f5 '공격하기 위해 대기' 자세(holdFrame).
7. **칼집 자리 = 캐릭터 왼쪽 허리**(발도 호 시작 쪽). 정면에선 화면 오른쪽 허리라 일기장 바로 아래에 겹쳐 보인다. 옆면은 먼 허리라 손잡이·칼집 끝만 보인다.
8. **활 장전에 화살통 없음** — 다른 손이 어깨 뒤에서 호박빛 화살 3개를 실체화(무기 실체화 언어 유지). 화살통을 몸에 그리려면 몸 시트 변경이 필요.
9. **범위 밖(미변경)**: 칼 2·3타·패링(katana_special) 무기 시트에는 빈 칼집이 없고, 48라운드 '흩어짐(fade/embers)' 상태가 남아 있다(무기가 실물 휴대로 바뀐 49라운드와 어긋남). 대검 가드(greatsword_special)도 한 손 그림. 다음 라운드 개정 후보.

---

# 10. 51라운드 — 개성 갈래별 기본 공격 이펙트 · 활 속사/저격 (2026-10-02)

근거: `decisions/2026-10-02-round-51-playtest3.md` 4절 (원문 "개성 발현이 됨으로써 기본 공격에서부터 뭔가 이펙트가 개성이 두드러지도록" · 활 산탄 삭제 → 속사/저격), `fx-design.md`, 계약 `art-assets.md` §3·3.1·3.2·6.1. 시각 참조 = GDD·기존 LOPAD fx 언어만(옛 기기 팔레트·패턴 자료 미사용, 루트 4-1).
빌드: `python3 parts/art/work/combos/branches.py` (약 6초). `build.py` 를 **모듈로 읽기만** 한다(COMBOS·HIT·Canvas·저장·검사 재사용) — 기존 시트는 다시 쓰지 않는다. 저장 전 `guard()` 가 같은 이름의 기존 파일을 발견하면, 그 JSON `source` 가 branches.py 가 아닌 한 중단한다. 만든 파일 목록 = `combos/branches_created.txt`.

## 10.1 산출물 (27 시트 = PNG 27 + JSON 27, 전부 새 파일)
- 근접 1차 갈래 × 3타 = 18: `fx/<w>_combo<n>_<branch>` — katana: `iai`(거합)·`batto`(발도술) / greatsword: `crush`(파쇄)·`weight`(중압) / dagger: `twin`(쌍격)·`gale`(질풍).
- 활 9: `fx/bow_arrow_rapid` · `bow_arrow_aimed_rapid` · `bow_muzzle_rapid` · `bow_arrow_snipe` · `bow_arrow_aimed_snipe` · `bow_arrow_snipe_lv1~3` · `aim_line_snipe`.
- 2차 갈래 16종(만월·잔월·허보·급소·지진·분쇄·철벽·거인·난무·출혈·잔상·암살·연궁·무한통·관통·필중): **시트 없음** — 1차 시트 JSON `secondaryVariants` 에 색 치환·겹침 지시.
- 미리보기: `preview_branch_{katana,greatsword,dagger}.png`(타마다 기본/A/B 3행 × 전 프레임 2배, f1 에 몸·무기 겹침, 오른쪽 f1 4방향 1배) · `preview_branch_bow.png`(6배, 회색 이름 = 기존 비교용) · `preview_branch_strip_1x.png`(1배 실픽셀 f2) · `preview_branch_mock_1x.png`/`_2x.png`(월드 480×270 → 카메라 2배 960×540) · `gif/branch_<w>_combo<n>_right.gif`(기본·A·B 나란히, 실제 ms).

## 10.2 규격 표 (시스템 전달용)
**근접 갈래 시트 = 기본 시트와 규격이 같다.** 크기·피벗·프레임 수·`frameDurationsMs`·`anchor`·`spawn`·`impactFrame`·`hitFrames`·`cancelFromFrame`·`timingMs`·`hitRadiusPx`·`arcDeg/From/To`·`thrust`·`fxSpawnAtMs`·`recoverFrames`·`shake`·`flash` 를 기본 시트 JSON 에서 그대로 복사했다. **판정은 바뀌지 않는다**(그림 = 같은 판정 가장자리). 시스템은 갈래가 확정되면 `fx/<w>_combo<n>` 대신 `fx/<w>_combo<n>_<branch>` 를 재생하면 된다(파일이 없으면 기본으로 폴백).

| 시트 | 크기 | 프레임 · ms | 피벗 | anchor · spawn | hitFrames | 바뀐 필드 |
|---|---|---|---|---|---|---|
| katana_combo1_{iai,batto} | 96 | 5 · 40/50/60/70/90 | (48,58) | player_pivot · attack_frame2 | [1] | iai `trail.color` W2 · batto `trail: null` |
| katana_combo2_{iai,batto} | 96 | 4 · 40/40/50/80 | (48,58) | 〃 | [1] | 〃 |
| katana_combo3_{iai,batto} | 96 | 6 · 40/40/60/80/100/120 | (48,58) | 〃 | [1] | 〃 (flash·shake 기본과 같음) |
| greatsword_combo{1,2}_{crush,weight} | 128 | 6 · 40/60/70/80/100/120 | (64,74) | player_pivot · attack_frame3 | [2] | weight `trail.color` W0 |
| greatsword_combo3_{crush,weight} | 128 | 7 · 40/50/70/90/110/130/160 | (64,74) | 〃 | [2] (active [2,3]) | 〃 |
| dagger_combo{1,2}_{twin,gale} | 64 | 4 · 40/40/50/70 | (32,42) | player_pivot · attack_frame2 | [1] | `heatVariants` 추가 |
| dagger_combo3_{twin,gale} | 64 | 5 · 40/40/50/60/90 | (32,42) | 〃 | [1] | 〃 |

| 활 시트 | 크기 | 프레임 · ms · loop | 피벗 | anchor · spawn · depth | 메모 |
|---|---|---|---|---|---|
| bow_arrow_rapid | 16×6 | 2 · 40/40 · loop | (12,3) 화살 몸 중심 | projectile(rotate, drawnFacing right) · loop_move · above | `bow_arrow` 대체(속사) |
| bow_arrow_aimed_rapid | 20×6 | 2 · 40/40 · loop | (16,3) | 〃 | `bow_arrow_aimed` 대체(속사) |
| bow_muzzle_rapid | 16×16 | 2 · 30/40 · 1회 | (4,8) 화살 생성점 | projectile(rotate) · **`arrow_spawn`(새 spawn 이름)** · above | 발사마다 처음부터 재생 |
| bow_arrow_snipe | 24×5 | 2 · 50/50 · loop | (18,2) 무게 중심 | projectile · loop_move · above | `bow_arrow` 대체(저격). `tailSheets` |
| bow_arrow_aimed_snipe | 32×5 | 2 · 50/50 · loop | (24,2) | 〃 | `bow_arrow_aimed` 대체(저격) |
| bow_arrow_snipe_lv1 / lv2 / lv3 | 24×3 / 40×5 / 56×7 | 3 · 50×3 · loop | (22,1) / (38,2) / (54,3) = 화살 중심 | projectile · loop_move · **below** | `tailLevel`, `levelRuleSuggestion`: 비행 거리/최대 사거리 < 1/3 → lv1, < 2/3 → lv2, 이상 → lv3 |
| aim_line_snipe | 16×3 tile | 6 · 진행도 | (0,1) 선 시작 | player_pivot(rotate, tile) · aim_charge · below | `progressDriven`, frame = min(4, floor(progress*5)), 완료 = 5. `aim_line` 대체(저격) |

## 10.3 갈래별 디자인 (같은 규격에 성격만)
51라운드 1절("획이 너무 두껍고 부드럽지 않다")은 **같은 해상도 안에서** 반영했다. 획을 기본보다 가늘게 했고(칼 띠 6→5·4, 단검 줄기 7→3.6~4.4), 끝은 바늘처럼 모이게, 곡선은 표본 거리장으로 그려 계단을 줄였다. 2배 해상도 판은 10.7 임시 결정 1(인터뷰).
- **거합 iai = 초승달 잔광**: 바깥 가장자리 = 판정 반경의 완전한 원호. 안쪽만 부풀었다가 양 끝이 바늘로 모이는 '달' 모양에 1px 백열 선이 가장자리를 따라간다. 1px 잔광 호(R+2, 3타는 R+4 겹)는 **점선이 아니라 이어진 선**으로 꼬리 프레임까지 남는다. 끝에서 접선으로 새는 바늘 광.
- **발도 batto = 직선 섬광**: 호 대신 판정 가장자리 안쪽의 곧은 섬광 선(1타 세로 · 2타 아래→위 비스듬히 · 3타 X 두 줄). 판정 범위는 1px W0 점선 호로만 표시. 가운데 가로 섬광 별, 몸 쪽 메아리 선. 호 트레일 없음.
- **파쇄 crush = 균열 파편**: 기본보다 얇은 호를 비스듬한 틈 5곳으로 끊어 '깨진 띠'로 만든다. 판정 가장자리 밖으로 균열 4줄(백열 → 용암 → 식음 → 점선), 돌 파편 6개(G09 삼각, 앞 모서리 27/W3)가 바깥으로 튀며 떨어진다. 3타는 앞-아래 바닥 균열과 바닥 파편을 더한다.
- **중압 weight = 무거운 압력 파동**: 어둡고 두꺼운 띠(W0·W1) 가운데에 1px 녹은 선(W3) + 띠 안쪽 짓누름 선. 판정 밖으로 2px 파동 2겹(밝은 안선 + 어두운 바깥선)이 호보다 넓게 퍼지며 밀려난다. 3타는 바닥 눌림 납작 고리(세로 0.45).
- **쌍격 twin = 이중 궤적**: 나란한 가는 찌르기 두 줄(±2.5px). 둘째 줄은 1프레임 늦게 끝까지 뻗는다. 3타는 두 줄이 촉에서 만나는 가위 찌르기 + 교차 섬광.
- **질풍 gale = 바람 줄기**: 가는 본 줄기 + 몸 옆에서 출발해 촉 쪽으로 모여드는 1px 바람 줄기(완만한 활 모양, 뒤 W1 → 앞 W3). 다음 프레임에서 앞으로 밀려나고, 촉 너머로 바람 한 줄이 이어진다. 3타는 바람 3→4줄.
- **속사 rapid**: 8px 짧은 화살 + 뒤로 끊긴 1px 속도선 잔상 2(조준 3)개가 2프레임으로 엇갈려 깜빡인다. 발사점 섬광은 쐐기 + 위아래 광선 → 고리 조각, 70ms.
- **저격 snipe**: 몸 전체를 관통하는 1px 백열 코어 빛줄기(앞쪽에만 짧은 결)에 꼬리 3단계(가는 쪽 어둡고 화살 쪽 굵고 밝게, lv3 은 W0 가장자리 + X0 맥동 + 불티 27/25). 조준 레이저는 진행도에 따라 점 → 긴 점선 → 실선(W1 → W2 → W3 → X1)으로 차고, 완료 = X0 실선 + 양옆 실선.

## 10.4 2차 갈래 (JSON `secondaryVariants` — 시스템 전달 요점)
- 형식: `{ <2차 id>: { label, colorSwap: [{from, to, fromSlot, toSlot, role}], overlay?: {sheet, atFrame|loop, at, onHit|onlyOnCrit|minLevel}, holdLastFrameMs?, flashOverride?, shakeOverride?, trailOverride?, scaleHint?, note } }`.
- `colorSwap` 은 **정확한 색 치환**(층 팔레트 스왑과 같은 캔버스 재채색)이다. **여러 항목은 동시에 적용**한다(순차로 하면 W1 → W2 → W3 로 번진다). C16~C27 칸은 층마다 바뀌므로 `fromSlot/toSlot` 으로 현재 층 색을 찾을 것(hex 는 1층 기준). 어렵다면 Phaser `setTint(to)` 근사도 가능하다(정확도 낮음).
- overlay 는 **기존 시트만** 쓴다(`fx/crit_burst`·`fx/bleed`·`fx/pierce`).
- 표: 만월(W1→W2, 22→25, 1·2타도 X1 0.14 섬광) · 잔월(22→W1, 마지막 프레임 +160ms) · 허보(X0→X1, W3→W2) · 급소(24→27 + 치명 시 crit_burst) · 지진(W1→W2, 흔들림 3px/90) · 분쇄(파편 G09→27) · 철벽(W2·W3→G09 쇳빛) · 거인(W3→X1 + scaleHint) · 난무(W1→W2, 24→27) · 출혈(24→18, 22→17 + 적중 시 bleed) · 잔상(X0→W3 + 단검 트레일 W1 0.6/160) · 암살(24→25, W3→25) · 연궁(W1→W2) · 무한통(W3→25) · 관통(pierce 루프 겹침) · 필중(W2→W3, W3→X1 + lv3 적중 시 crit_burst).
- 단검 가열(heat1~3)을 갈래 시트에 쓸 때는 별도 시트 없이 JSON `heatVariants.colorSwap[k]` + 기존 `playbackRateHint` 1.15/1.3/1.5.

## 10.5 색 예산 · 검사 (마지막 실행 27 시트 ALL OK)
- 칼·단검 갈래: 보조 4 + 코어 2 + 층 강조 ≤3(22·24·27) = 6~9. 대검: 보조 4 + 코어 ≤2 + 재 G06·G09 + 층 ≤2 = 9. 활: 보조 ≤4 + 코어 ≤2 + 층 ≤2(25·27) = 3~7. 모두 ≤11.
- 고립 0 · 반투명 0 · 무기색 섞임 0. **캔버스 가장자리 닿음 0**(새 `edge_touch` 검사 — 잘림 방지).

## 10.6 see → critique → fix
1. 1회차: 발도 예비 1px 선이 반 픽셀 좌표(47.5+29)라 점 2개만 남음 → 선 좌표 정수화. 거합 2타 잔광이 안 보임 → W3/X1 로 한 단 밝게. 파쇄 f1 이 기본과 거의 같음 → **띠를 비스듬한 틈으로 끊는 '깨진 호'** 추가. 중압 파동 e+12 가 128 캔버스 가장자리에서 잘림 → 최대 e+10. 질풍 바람 줄기가 사선에서 2px 로 두꺼워지고 말림 갈고리가 덩어리 → 반폭 0.62, 몸 옆에서 촉으로 모이는 활 모양 줄기. 속사 화살이 가운데 깃 때문에 '+' 로 읽힘 → 깃을 뒤 V 로, 잔상을 1px 속도선으로. 저격 꼬리의 가는 끝이 밝음 → 가는 끝 W1, 굵은 끝 X0/X1. 미리보기 한글 라벨 깨짐 → ASCII.
2. 2회차: 질풍 촉 너머 바람·말림이 64 캔버스 밖(s1+9)으로 잘림 → 바람 끝 s ≤ 29.5, 말림 제거(1배에서 '[' 괄호로 읽힘). 파쇄 파편·균열이 반경 63 을 넘음 → 단계표 PHASE(최대 +8), 균열 길이 7~8. 쌍격 3타 촉 광선이 가장자리에 닿음 → 길이 2. 목업 칸 높이가 호를 자름 → 줄 높이 76/112/42/40. 저격 화살이 굵은 캡슐처럼 보임 → 결을 앞 35% 로 줄여 1px 빛줄기 위주로.
3. 3회차(1배 실픽셀 띠): 같은 무기 안에서 기본과 두 갈래가 모양만으로 구분된다. 칼 = 겹 초승달 / 단일 바늘 달 + 잔광 / 직선 섬광. 대검 = 이어진 호 / 깨진 호 + 파편 / 어두운 띠 + 압력 고리. 단검 = 굵은 방추 / 두 줄 / 바람 부채. 단검은 64 캔버스라 1배에서 작다(기본과 같은 규격이라 수용). SHIP.

## 10.7 임시 결정 (도영 님 검수 대상)
1. **해상도**: 지시대로 기존 연격 fx 와 같은 규격(1배 도트, `pixelScale` 없음 = 시스템 2배)으로 만들었다. 51라운드 1절(픽셀 세분화)과 50라운드 2배 도트(`pixelScale: 1`)를 따르려면 같은 스크립트를 캔버스·반경 2배로 다시 렌더한 v2 판이 필요하다(획 모듈은 해상도 무관). → 인터뷰.
2. **2차 갈래 = 시트 없이 colorSwap/overlay 메모**: 색 치환 구현은 시스템 몫이다. 불가하면 setTint 근사, 또는 2차 시트 별도 제작(+48 시트)을 재인터뷰.
3. **갈래 id**: iai·batto·crush·weight·twin·gale(기존 1차 진화 id), 활 rapid·snipe, 2차 volley·quiver·pierce·deadeye 는 메인 세션이 전달한 자리표시 그대로. 시스템 id 가 다르면 파일명만 바꿔 재빌드(상수 `BRANCHES`).
4. **저격 꼬리 단계 기준**(거리 1/3·2/3)과 피해 배율은 제안이다. 시스템 값이 우선이고, 아트는 시트만 교체한다.
5. **`bow_muzzle_rapid` spawn = `arrow_spawn`**: 새 spawn 이름이다(계약 §3.1 목록에 없음). 시스템이 화살 생성 시점에 같은 각도로 1회 재생.
6. **발도 갈래 트레일 없음**(`trail: null`), 거합 트레일 W2, 중압 트레일 W0 — 기본 트레일 색만 바꿈. 잔상(2차)만 단검 트레일을 새로 켬.
7. **속사 조준 레이저는 만들지 않음**: 속사는 기존 `aim_line` 을 그대로 쓴다고 가정.
8. **기존 산탄 시트(`scatter`·`rain`·`seek`)는 그대로 둠**: 51라운드 결정이 '화기류 도입 시 재사용'이므로 삭제·수정하지 않았다.
