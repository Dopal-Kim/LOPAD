# combos — 근접 3연격 · 무기 든 특수 동작 (48라운드 Q2, 2026-10-02)

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
| katana_combo1 | 4 · 90/40/120/100 (350) | [1] (90ms) | 3 (250) | R33 · 140° (−70→70) | 48 (24,39) | 96 · 5 · 40/50/60/70/90 · (48,58) | W1 0.6/120 f2 |
| katana_combo2 | 3 · 40/40/90 (170) | [1] (40) | 2 (80) | R33 · 130° (65→−65 역방향) | 48 | 96 · 4 · 40/40/50/80 | W1 0.6/120 f2 |
| katana_combo3 | 4 · 40/40/100/140 (320) | [1] (40) | — (연격 끝) | R33 · 170° (−85→85) | 48 | 96 · 6 · 40/40/60/80/100/120 | W1 0.7/180 · 섬광 X1 0.12 f1 · 1px/50 |
| greatsword_combo1 | 4 · 160/60/120/140 (480) | [1] (160) | 3 (340) | R51 · 190° (−110→80) | 64 (32,47) | 128 · 6 · 40/60/70/80/100/120 · (64,74) | W1 0.6/160 · 2px/60 |
| greatsword_combo2 | 4 · 140/60/120/140 (460) | [1] (140) | 3 (320) | R51 · 200° (100→−100 역방향) | 64 | 128 · 6 · 같음 | W1 0.6/160 · 2px/60 |
| greatsword_combo3 | 5 · 200/60/70/140/180 (650) | [1] (200), active [1,2] | — | R51 · 270° (−150→120) | 64 | 128 · 7 · 40/50/70/90/110/130/160 | W1 0.7/220 · 섬광 W3 0.12 f1 · 3px/90 |
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
