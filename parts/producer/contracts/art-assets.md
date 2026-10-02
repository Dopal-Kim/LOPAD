# 계약: 아트 산출물 ↔ 게임 시스템 로드 형식 (29라운드 자율 승인, 도영 님 복귀 후 검토)

아트 파트는 아래 형식으로 내보내고, 시스템 파트는 아래 형식만 믿고 로드한다. 변경은 양쪽 합의 후 이 문서부터 고친다.

## 1. 스프라이트 시트 (`assets/sprites/<분류>/<이름>_<동작>.png` + `.json`)
- 격자 시트, 패딩 0. **행 = 방향**(`directions` 순서: down, up, left, right), **열 = 프레임**. 프레임 번호 = `row * frames + column`.
- JSON 필드: `image, action, frameWidth, frameHeight, frames, directions[], fps, frameDurationsMs[], loop, pivot{x,y}`.
- 시스템은 `this.load.spritesheet(key, png, { frameWidth, frameHeight })` 로 읽고, `anims.create({ key: '<이름>_<동작>_<방향>', frames: row 범위, frameRate: fps 또는 duration 배열, repeat: loop ? -1 : 0 })` 로 등록한다.
- 애니메이션 키 규칙: `player_walk_down`, `dummy_idle_left` 등 `<이름>_<동작>_<방향>`.
- 피벗: 스프라이트 원점은 `pivot`(발 위치). 물리 바디는 시스템이 별도로 정한다(현재 플레이어 바디 12×12 가 발밑에 오도록).
- 동작 목록: 주인공 idle/walk/attack/dash/hurt/death. 일반 적·보스 idle/walk/attack/death(+ 보스는 phase2 등 추가 가능, JSON 에 있으면 시스템이 선택적으로 사용).
- 크기: 주인공·일반 적 16×24(덩치 24×24 허용), 보스 32×48, 황제 48×64. 1프레임 동작도 같은 형식(frames: 1).

## 2. 타일셋 (`assets/tiles/stage<n>.png` + `stage<n>.json`)
- 16×16 격자 한 장. JSON 의 `tiles` 는 **게임 타일 ID → 시트 인덱스 목록**. 게임 타일 ID(시스템 `TileId`): `0 void, 1 floor, 2 wall, 3 door_open, 4 door_closed, 5 door_locked, 6 corridor, 7 exit, 8 shop`.
- 같은 ID 에 인덱스가 여러 개면 시스템이 좌표 해시로 변형을 고른다(바닥 변형, 벽 변형). 예: `"1": [0,1,2,3]`.
- 벽은 1차로 단일 타일(위·아래 구분 없음)이어도 된다. 자동타일(상/하/좌/우/모서리)을 넣으려면 JSON `walls: { top, bottom, left, right, corner_* }` 키로 추가하고, 시스템은 있으면 쓰고 없으면 단일 벽을 쓴다.
- 장식(소품)은 `props: [{ index, name, solid }]` 로 두고 시스템이 방 바닥에 무작위 배치한다(선택). 37라운드: 소품은 층당 6종까지(인덱스 13~18). **40라운드: 소품 8종(13~20), 항목에 `maxPerRoom?: number`(방당 최대 개수), `weight?: number`(배치 가중치, 기본 1) 허용.**
- 37라운드 추가: `roomFloors: { start: number[], trial: number[], rest: number[], boss: number[] }` — 방 종류별 바닥 인덱스 목록. 키가 없거나 비면 `tiles["1"]` 을 쓴다. 복도는 `tiles["6"]`. 벽 변형은 `tiles["2"]` 목록에 인덱스를 더 넣으면 좌표 해시로 섞인다. **40라운드 인덱스 표 v3: 8열×5행(128×80), 소품 13~20, 벽 변형 21~22, 방 종류별 바닥 각 4변형 23~38(`decisions/2026-10-02-round-40-tileset-final.md`). 시스템은 JSON 값만 읽으므로 인덱스 변경에 코드 수정이 없어야 한다.**
- 팔레트 교체: 층별 강조색은 시트 자체가 층별 파일이므로 런타임 치환 없음. 캐릭터는 1층 램프 색으로 그려지고, 시스템이 **런타임 팔레트 스왑**(강조 램프 12칸 → 현재 층 ramp)을 `parts/art/palette/lopad.json` 기준으로 수행한다(캔버스 텍스처 재채색).

## 3. 무기·이펙트 (`assets/sprites/weapons/<무기id>_<동작>.png`, `assets/sprites/fx/<이름>.png`)
- 무기 아이콘 `weapons/<id>_icon.png` 16×16 1프레임(메뉴·HUD). 공격 이펙트 `fx/<id>_<동작>.png` 는 1절 형식(방향 4행, 프레임 N열). 1차 진화 이펙트는 `fx/<진화id>.png`.
- 무기 id: katana, greatsword, dagger, bow. 진화 id 는 `data/weapons.json` 의 트리 id 와 같게(스토리·시스템이 정한 id 를 아트가 따른다).

### 3.1 29라운드 보강 (아트 4단계)
- 손에 든 무기 `weapons/<id>_attack` 은 **48×48**, 4방향×4프레임, 피벗 (24,39) = 주인공 피벗 (8,23). 플레이어 `attack` 과 같은 프레임 번호를 같은 시각에 표시. JSON `depth`: `"below"`(up 방향) / `"above"`.
- 이펙트 JSON 추가 필드: `anchor` = `player_pivot`(피벗을 플레이어 발 피벗에) / `hitbox_center`(히트박스 중심) / `projectile`(투사체 중심, `rotate: true` 면 진행 각도로 회전, `drawnFacing: "right"`) / `ui`. `directions: ["any"]` 면 1행. `spawn` = 재생 시점 메모(`attack_frame2`, `hit`, `dash_start`, `loop_move`).
- 재생 시점: slash/iai/twin = attack 2프레임 시작, crush/weight = 적중 판정 시작, batto = 대쉬 시작, gale = 이동·대쉬 중 루프, pierce = 화살에 루프, scatter = 발사점 1회.

### 3.2 42·43라운드 보강 (인페르노 기반 재디자인 양산)
- 팔레트 예외: 이펙트는 `lopad.json` `fx` 블록(백열 코어 X0/X1 + 무기별 보조 램프 4칸)을 쓸 수 있다. 캐릭터·타일·UI 금지. 적·보스 예고·공통 피격은 보조색 없이 층 램프 + 코어.
- 크기: 기본 공격 48, 1차 64, 2차 궤적형 96(적중형 64). 기존 id·행열·anchor·spawn 규약 유지.
- JSON 추가 필드(있으면 시스템이 사용): `weapon`, `secondary`, `trail {color, alpha, ms, fromFrame}`, `flash {color, alpha, ms, atFrame}`, `shake {px, ms}`, `progressDriven`, `followsTarget`, `followsPlayer`, `tailFrames`, `tile`, `scale`, `depth`, `pivotNote`.
- 신규 시트: `telegraph_aura`(수렴 오라 루프), `hit_burst`(적중 광선, hit_spark 대체).
- 46라운드 신규: `boss_slam` 96×96 · 6f(40/50/60/80/110/140ms) · 피벗 (48,48) = 슬램 지점 = 판정 원 중심 · `anchor: hitbox_center` · `spawn: boss_slam_impact` · 바닥 깊이 · 층 램프 + 코어 + 무채만(보조색 없음). `flash`·`shake` 필드 포함, `scale: "allowed"`(판정 반경 R 이면 R/40, 정수 배율 권장). 보스 내리찍기에서 `crush` 대신 사용.

## 4. 로드 책임
- 시스템 `Preloader` 가 `assets/` 를 로드하고, 파일이 없으면 기존 플레이스홀더(단색 사각형)로 폴백한다. 아트가 파일을 추가하면 자동으로 쓰인다.

## 5. 상호작용 구조물 시트 (47라운드)
- 경로: `assets/sprites/structures/<id>.png` + `<id>.json`. 시스템 Preloader 가 manifest 로 자동 로드, 없으면 플레이스홀더 도형으로 폴백.
- id(초안 번호): `crate_f1`·`crate_f2`(C1 층별 외형), `chest`(C2), `grave`(C3), `bonfire`(C5), `barrel`(1-1), `still`(1-2), `ledger`(1-3), `cask`(1-4), `counter`(1-5), `cellar_wall`(1-6), `card_table`(2-1), `chip_exchange`(2-2), `dog_ring`(2-3), `bet_bell`(2-4), `roulette`(2-5), `pawn`(2-6). 추가 fx: `fire_pool`(1-1 불붙은 웅덩이 루프, `assets/sprites/fx/`, §3 규약).
- 크기: 타일 단위 16×16 ~ 48×32 (dog_ring·roulette 처럼 바닥에 까는 것은 최대 64×48 허용). JSON 필드:
  - `frameWidth`, `frameHeight`, `frames`, `directions: ["any"]`(1행), `frameDurationsMs`
  - `footprint: [tw, th]` 타일 수(단단한 영역), `solid: true|false`, `pivot` = 발판 아래 가운데
  - `states: { "<이름>": [frame, …] }` — 최소 `idle`. 쓰는 이름: `idle`, `used`(소모됨), `broken`(부서지는 애니, 마지막 프레임 유지), `active`(루프: 불·회전), `hit`(맞음 1프레임). 시스템은 없는 상태면 `idle` 첫 프레임을 쓴다.
  - `depth`: `floor`(바닥에 깔림) / `y`(Y 정렬, 기본)
- 색: 무채 16 + 층 강조 램프(16~27, 런타임 층 스왑) — 공통(C2·C3·C5·crate)은 스왑 대상, 층 테마 구조물은 그 층 램프로 그리고 `floor: "stage1"|"stage2"` 메모. UI 세피아·무기 보조 램프 금지. 불·발광은 백열 코어 X0/X1 허용(이펙트 규약과 동일).
- 이름·서사는 자리표시(스토리 확정 전). 외형 메모는 `parts/system/structures-draft.md` 각 항목의 "외형(아트 요청)".

## 6. 48라운드 추가 (연격·무기 든 특수 동작·탄생·바닥 v4·노드 아이콘)
범위는 **1~2층 한정**(48라운드). 기존 규약(행=방향 down/up/left/right, 열=프레임, 피벗, 층 램프 스왑)을 그대로 따른다. 카메라 2배 확대는 시스템이 처리하므로 시트 크기 규격은 바뀌지 않는다.

### 6.1 무기별 3연격 (근접 3종)
- 주인공 몸: `player/player_<weapon>_combo<n>` (weapon = katana·greatsword·dagger, n = 1·2·3), 16×24, 4방향, 프레임 3~5.
- 손에 든 무기: `weapons/<weapon>_combo<n>`, 48×48(대검은 64×64 허용), 피벗 = 주인공 피벗에 맞춤(48: (24,39), 64: (32,47)), 몸 시트와 같은 프레임 번호·같은 `frameDurationsMs`. JSON `depth` 규칙은 §3.1과 같음.
- 베기 이펙트: `fx/<weapon>_combo<n>`, §3·3.2 규약(anchor `player_pivot`, spawn `attack_frame2` 또는 `impactFrame` 명시). 판정 범위 1.5배에 맞춰 호 반경을 키운다(시스템이 판정 반경을 JSON `hitRadiusPx`·`arcDeg`로 읽는다 — 메모 필드로 넣을 것).
- 느낌: 대검 = "훙 훙 훙" 크게 휘두르는 3연격(묵직, 3타가 가장 큼) · 칼 = "씽 씽씽"(1타 뒤 빠른 2연속) · 단검 = "슈슈슉" **찌르기** 연타(호가 아니라 앞으로 뻗는 찌르기 줄기 3개).
- JSON 메모 필드(있으면 시스템이 사용): `comboIndex`, `hitFrames`, `cancelFromFrame`(다음 타로 넘어갈 수 있는 프레임), `hitRadiusPx`, `arcDeg`(찌르기는 `thrust: {lengthPx, widthPx}`).

### 6.2 무기를 들고 하는 특수 동작
- 주인공이 무기를 든 채 보조 동작·진화 특수 효과를 실행하는 모습: `player/player_<weapon>_special` (4방향, 4~6프레임) + `weapons/<weapon>_special`(위 6.1과 같은 겹침 규칙). 활은 `player/player_bow_aim`·`weapons/bow_aim`(시위 당긴 자세, 차지 진행도 프레임).
- 기존 fx(패링 섬광·밀쳐내기·허보 분신·조준 등)는 그대로 쓰고, 이 시트는 그 순간의 **몸과 무기 자세**만 담당.

### 6.3 탄생 연출
- `player/player_birth`: 32×32, 방향 `["down"]` 1행, 피벗 (16,31) = 주인공 발. 프레임 14~20: 흙이 모여 둥글게 소용돌이 → 사람 형체로 굳음 → 무릎 꿇은 자세 → 일어섬(마지막 프레임 = player_idle down 0 과 이어짐). `frameDurationsMs` 합 약 3.5~4초. JSON 메모 `burstFrame`(잔불이 터지는 프레임).
- `fx/birth_dust`(바닥 흙 소용돌이 루프·흩어짐, 64×32 안팎, §3 규약, 층 램프).

### 6.4 바닥 타일 v4 (1·2층)
- `tiles/stage1`·`tiles/stage2` 를 **인덱스 표 v3(128×80, 8열×5행) 그대로** 다시 그린다(시스템 변경 없음).
- 방향: **깨진 포장도로 뒷골목** — 큰 판석·보도블록을 어둡고 평평하게, 금·빠진 블록·배수구·흙더미는 드물게, 잡점 제거, 잔불 강조색은 금 사이 일부만. 눈의 피로가 적어야 한다(2배 확대 상태에서 판단).
- `roomFloors.start` 4변형(1층)은 **황폐한 평화지역**(흙·잔해·탄 자국) — 여정 노드(탄생지·버려진 길·국경 초소)에 쓰인다.

### 6.5 노드 지도 아이콘 (UI 가 사용, 승인 #18)
- `ui/node_icons.png/json`: 아이콘 32×32, 1행 프레임 순서 고정 = `journey, battle, shop, rest, event, boss`(6), 상태는 별도 행 2개 추가(행 0 = 기본, 행 1 = 지나옴(식음), 행 2 = 잠김(흐림)). 색은 UI 세피아 + 현재 층 강조 1점(UI 키트 규칙). JSON 메모 `order`.

## 7. 49라운드 추가 (무기 휴대·동작 강화·전장 탄생·지역 타일·세트 배치)
범위 1층 우선(2층은 같은 틀을 이어서). 기존 규약(행 = down/up/left/right, 피벗 (8,23), 무기 오버레이 겹침 §3.1·§6.1)을 따른다.

### 7.1 무기 휴대 (상시 표시)
- 휴대 위치: **칼 = 허리 칼집 · 대검 = 등 · 단검 = 손(역수) · 활 = 손**.
- 시트: `weapons/<w>_carry_<action>` (action = idle·walk·dash, 몸 시트 `player_<action>` 과 같은 프레임 수·ms, 4방향, 48×48 피벗 (24,39) / 대검 64×64 (32,47)). JSON `depth` 를 방향·프레임별로(`below`/`above`).
- 뽑기·넣기: 칼 `weapons/katana_draw`·`katana_sheathe` + 몸 `player/player_katana_draw`·`_sheathe`, 대검 `greatsword_draw`·`_sheathe`(두 손으로 등에서 끌어냄). 단검·활은 없음. 시스템은 공격 시작 시 draw, 일정 시간 비전투·무공격이면 sheathe.

### 7.2 동작 강화
- 대검: 두 손 큰 휘두름으로 `greatsword_combo1~3` 재제작(몸이 크게 비틀리고 무게 중심 이동, 휘두른 뒤 자세 회복 프레임 포함). **내리찍기** `player_greatsword_slam` + `weapons/greatsword_slam` + `fx/greatsword_slam`(머리 위로 들어 → 짧은 도약 → 내려찍음, JSON `leapFrames`·`impactFrame`). **대쉬 공격** `player_greatsword_dashslash`(달려들며 크게 한 번 휘두르고 멈춰 자세 잡음, `recoverFrames`).
- 칼: 발도(칼집에서 뽑으며 베기) 동작을 1타에, 납도 동작 추가.
- 단검: 가열 단계별 이펙트 변형 `fx/dagger_combo<n>_heat<k>`(k = 1·2·3, 더 밝고 길게) 또는 JSON 메모로 틴트 지시.
- 활: 장전 동작 `player_bow_reload`·`weapons/bow_reload`.

### 7.3 지역 타일 (1층) · 세트 배치
- `tiles/stage1_<region>` (region = `waste`(황무지·전장) · `gate`(성문) · `outer`(외곽 거리) · `brewery`(양조 구역) · `hall`(지배자의 연회장)), **인덱스 표 v3 그대로**. 기존 `tiles/stage1` 은 폴백.
- 실내 느낌 금지: 하늘이 트인 거리. 인덱스 5·6(벽 정면·윗면)은 지역에 맞게 담·잔해 더미·건물 앞면·술통 더미 등으로, 7(void)는 바깥 원경 색.
- 세트 배치 소품: `structures/set_<region>_<name>` (§5 규약) — 구조물을 감싸는 주변 장식(노점 천막·광장 바닥 문양·모닥불 둘레 돌·술통 더미 등). 시스템이 노드 중앙 세트 배치에 사용.
- 전장 탄생: `player/player_birth` 를 **혼불(영혼)이 모여 형체가 되는** 버전으로 재제작(같은 규격 §6.3), `fx/soul_wisp`(떠다니는 혼불 루프), 전장 소품 `structures/battlefield_*`(부러진 무기 꽂힘·찢긴 깃발·쓰러진 병사 흔적·허수아비 `dummy`·튜토리얼 표식 `tutorial_sign`).
- 노드 아이콘: `ui/node_icons` 의 journey 열을 "앞으로 나아가는 길"(계단 아님)로 교체.
