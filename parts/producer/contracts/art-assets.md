# 계약: 아트 산출물 ↔ 게임 시스템 로드 형식 (29라운드 자율 승인, ~~도영 님 복귀 후 검토~~ → 31라운드 #8 일괄 승인)

아트 파트는 아래 형식으로 내보내고, 시스템 파트는 아래 형식만 믿고 로드한다. 변경은 양쪽 합의 후 이 문서부터 고친다.

## 1. 스프라이트 시트 (`assets/sprites/<분류>/<이름>_<동작>.png` + `.json`)
- 격자 시트, 패딩 0. **행 = 방향**(`directions` 순서: down, up, left, right), **열 = 프레임**. 프레임 번호 = `row * frames + column`. → **(57라운드 → §19) v3 아틀라스 시트는 `row * atlas.grid.columns + column`. 정수 `frames` 는 `framesPerDirection` 으로 바뀌고 `frames` 는 프레임 사전(객체)이다.**
- JSON 필드: `image, action, frameWidth, frameHeight, frames, directions[], fps, frameDurationsMs[], loop, pivot{x,y}`. (§19 적용 시트: 정수 `frames` → `framesPerDirection`, `frames{}`·`atlas{}`·`meta{}` 추가)
- 시스템은 ~~`this.load.spritesheet(key, png, { frameWidth, frameHeight })` 로 읽고~~ → **(57라운드 Q16·Q38 → §19) v3 시트(player·weapons·fx·enemies·bosses·structures)는 트림 아틀라스로 읽는다(`this.load.atlas`, 4096 초과는 `this.load.multiatlas`). 격자 `spritesheet` 로드는 §19 적용 밖 시트(타일셋 등)·옛 격자 JSON 에만 남는다.** 그 뒤 `anims.create({ key: '<이름>_<동작>_<방향>', frames: row 범위, frameRate: fps 또는 duration 배열, repeat: loop ? -1 : 0 })` 로 등록한다.
- 애니메이션 키 규칙: `player_walk_down`, `dummy_idle_left` 등 `<이름>_<동작>_<방향>`.
- 피벗: 스프라이트 원점은 `pivot`(발 위치). 물리 바디는 시스템이 별도로 정한다(현재 플레이어 바디 12×12 가 발밑에 오도록).
- 동작 목록: 주인공 idle/walk/attack/dash/hurt/death. 일반 적·보스 idle/walk/attack/death(+ 보스는 phase2 등 추가 가능, JSON 에 있으면 시스템이 선택적으로 사용).
- 크기: ~~주인공·일반 적 16×24(덩치 24×24 허용), 보스 32×48, 황제 48×64~~ → **현행: 주인공 96×144 도트(화면 48×72, §13·53라운드 Q1), 일반 적 주인공과 같은 크기·결사병 128×176(§14·53라운드 Q33·Q52), 1층 보스 192×240(§15·54라운드 Q14·Q22). 28라운드 크기는 50라운드 Q2로 대체.** 1프레임 동작도 같은 형식(frames: 1).

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
- 뽑기·넣기 (53라운드: 구 칼·구 주인공 시트 삭제 — 현행은 `sprites/player/v3/`·`sprites/weapons/v3/` 의 같은 이름, §13): 칼 `weapons/katana_draw`·`katana_sheathe` + 몸 `player/player_katana_draw`·`_sheathe`, 대검 `greatsword_draw`·`_sheathe`(두 손으로 등에서 끌어냄). 단검·활은 없음. 시스템은 공격 시작 시 draw, 일정 시간 비전투·무공격이면 sheathe.

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

## 8. 49라운드 Gemini 산출물 (테마 키아트·지도 일러스트·원경 배경)
결정: `decisions/2026-10-02-round-49-playtest2.md` Gemini Q1. 생성 원본·프롬프트는 `parts/art/work/gemini/` 에 보관하고, 게임에 들어가는 파일은 LOPAD 팔레트(lopad.json gray + 층 램프 + UI 세피아)로 색을 보정·감색한다. 키 값은 어디에도 남기지 않는다.
- **테마 키아트**: `assets/sprites/ui/keyart_<region>.png` (region = waste·gate·outer·brewery·hall, 2층은 후속) — 960×540, 노드 진입 배너·M 지도 위치 정보 패널·로딩 카드용(UI 사용, `assets/ui/` 로 복사).
- **펼친 지도 일러스트**: `assets/sprites/ui/map_bg_f1.png` — 960×540 이상, '잔' 외곽 황무지에서 심층부 연회장으로 이어지는 펼친 양피지 지도(노드가 놓일 자리는 비워 둔 원근 지형), UI 노드 지도 배경 레이어(`assets/ui/map_bg_<floor>.png` 로 복사).
- **원경 배경**: `assets/sprites/bg/<region>.png` — 전투장 바깥(void) 너머로 보이는 하늘·건물 실루엣, 가로 1920 이상 반복 가능, 시스템이 시차(parallax) 배경으로 사용(후속 연결).

## 9. 50라운드 쿼터뷰·2배 도트 (시범: 1층 외곽 거리)
결정: `decisions/2026-10-02-round-50-modern-view.md`. 시각 참조는 GDD + 최근 인기 로그라이크(Dungeon Survivors, 세피리아)만. 80·90·00년대 게임 참조 금지.
- **배율 표기**: 모든 시트·타일셋 JSON 에 `pixelScale`(정수) 필드. 새 2배 도트 = `1`, 기존 도트 = 없음/`2`(시스템이 2배로 그려 크기를 맞춘다). 게임 카메라 확대는 1배.
- **캐릭터**: 32×48, 피벗 (16,46) = 발. 행 = down/up/left/right(기존 규약). 시범 범위: 주인공 idle·walk·dash·hurt·death + 칼 3연격(combo1~3)·칼 휴대 오버레이(64×64 피벗 (32,62)), 적 결사병(charger) idle·walk·attack·hurt·death.
- **타일셋**: `tiles/v2/stage1_outer` — 타일 32×32. 인덱스 표 v3 의 의미(0~3 바닥, 4 복도, 7 void, 8~10 문, 11 출구, 12 상점, 13~20 소품, 21~22 벽 변형, 23~38 roomFloors)는 유지하되, **벽은 쿼터뷰 높이**: `walls.front` = 벽 앞면 세로 2칸(64px, 인덱스 5 = 아랫단, 24~ 이후 새 인덱스 `wallFrontUpper`), `walls.top` = 윗면(인덱스 6). JSON `wallHeightTiles: 2`. 시트 크기 자유(인덱스 표를 JSON 에 명시).
- **쿼터뷰 구조물·소품**: 높이가 있는 것은 `pivot` = 바닥 접점, `occludeAbove`(px) = 이 높이 위로는 캐릭터를 가림(Y 정렬).
- **조명**: JSON `light: { color, radius, intensity, flicker? }` 를 가진 소품·구조물·이펙트는 시스템이 광원으로 등록. 바닥·벽 색은 어둠 위에서 빛을 받아 살아나도록 중간 명도로(완전한 검정 금지).

## 10. 51·52라운드 추가 (갈래별 기본 공격 이펙트 · 활 속사/저격)
- 근거: 51라운드 §4(개성 발현 시 기본 공격 이펙트 차별화, 활 = 속사·저격), 52라운드 Q5(v2 전환 때 2배 일괄 · 2단 갈래 = 색 교체 + 겹침 · 저격 단계 1/3·2/3). 아트 기록 `parts/art/work/combos/NOTES.md` 10절.
- **근접 1단 갈래 시트**: `fx/<weapon>_combo<n>_<branch>` — katana `iai`·`batto`, greatsword `crush`·`weight`, dagger `twin`·`gale`. 크기·피벗·프레임·ms·anchor·spawn·impact/hit/cancel 프레임·`hitRadiusPx`·`arcDeg` 는 **기본 시트와 동일**(판정 불변). 추가 필드 `branch`·`branchLabel`·`baseSheet`·`replaces`. 시스템은 갈래가 있으면 이 키로 바꾸고, 파일이 없으면 기본 시트로 대체한다.
- **2단 갈래**: ~~시트 없음~~ → **55라운드 Q16: 2단 전용 시트** `fx/v3/<1단 시트>_<2단 id>`(1단보다 큰 틀·피벗 — JSON 값을 읽음, 판정 필드는 1단과 동일). 1단 JSON `secondarySheets`·`secondaryVariants[id].sheet` 로 연결, 2단 JSON `runtime`(overlay·flashOverride·holdLastFrameMs·shakeOverride·trailOverride 등) 실행, `colorSwap` 은 시트 파일이 없을 때만 대체. 활 2단 저격은 `tailSheets`. 아래 52라운드 문구는 대체 경로로만 유효: 1단 시트 JSON `secondaryVariants[<id>]` = `colorSwap`(from/to hex, `fromSlot`/`toSlot`, 동시 적용) + 선택 `overlays`(기존 `crit_burst`·`bleed`·`pierce`) + 타이밍·이펙트 덮어쓰기. 단검 가열 1~3단은 `heatVariants`(색 교체 + 기존 재생 속도 힌트). 색 교체는 바닥 팔레트와 같은 캔버스 재색칠 방식(정확 교체, `setTint` 아님).
- **활 속사**: `bow_arrow_rapid`·`bow_arrow_aimed_rapid`(투사체, 회전, loop_move), `bow_muzzle_rapid`(1회 재생, 새 spawn 지점 **`arrow_spawn`** = 화살 발사 위치). 조준선은 기존 `aim_line`.
- **활 저격**: `bow_arrow_snipe`·`bow_arrow_aimed_snipe`(JSON `tailSheets`), 꼬리 `bow_arrow_snipe_lv1/2/3`(화살 아래 깊이, 피벗 = 화살 중심, `tailLevel`). 단계 = 최대 사거리 **1/3 부터 lv2, 2/3 부터 lv3**(피해 배율도 같은 구간). 조준선 `aim_line_snipe` 16×3 타일 · 6프레임 · 진행도 구동(frame = min(4, floor(progress×5)), 충전 완료 = 5).
- 산탄 계열(`scatter`·`rain`·`seek`) 시트는 화기류 도입 때 재사용 — 삭제하지 않는다.
- 해상도: 현 사양으로 연결, 이펙트 v2(2배) 전환 때 같은 스크립트로 일괄 재출력.

## 11. 52라운드 도트 세분화 (2배 밀도)
- 근거: 52라운드 Q7·Q8. 내부 렌더 1920×1080, 논리 좌표·UI 배치는 960×540 기준 유지.
- `pixelScale` 의미 확장: 960×540 논리 px 하나에 들어가는 도트 수의 역수. 기존 v1 = 2(카메라 2배 시절 도트, 시스템이 1로 간주해 온 '구 시트'), v2 = 1(32×48 = 화면 32×48), **v3 = 0.5**(64×96 도트 = 화면 32×48 크기). 시스템은 `pixelScale` 로 길이 필드(hitRadius·thrust·light radius·occludeAbove·피벗)를 환산한다.
- 경로: `sprites/<category>/v3/…` — v3 → v2 → 구 시트 순으로 우선 로드(동작 단위 혼용 허용).
- **(57라운드 → §19)** v3 시트의 로드 형식은 격자 `spritesheet` 가 아니라 **트림 아틀라스**(§19.2·§19.3). 픽셀 크기·피벗·프레임 수·ms 등 이 절의 규격은 그대로이고, 저장 형식만 바뀐다.
- 주인공 v3: ~~64×96~~ **96×144(53라운드 Q1 → §13)**, 피벗 = 발 중앙(아트가 JSON `pivot` 으로 명시), 색 예산 30. 프레임: idle 6 · walk 8 · run 8 · 연격 타당 6~8 · dash 5 · hurt 3 · death 10(재로 무너지고 일기장만 남음).
- 보스 v3: ~~128×192(화면 64×96)~~ **1층 보스 192×240(화면 96×120), 피벗 (96,220)(54라운드 Q14·Q22 → §15)**. 이펙트 v3: 기존 크기 ×2, 같은 생성 스크립트로 재출력.
- ~~타일·구조물·세트는 32px(v2) 유지.~~ → **(60라운드 Q9 B안) 지역 바닥·엄폐 담·구조물도 64도트 = 1칸(`pixelScale 0.5`)으로 전환**. 아트가 2배 밀도 설계로 다시 만들어 넣는 시트부터 적용하고, 시스템은 타일셋·구조물 JSON 의 `pixelScale` 을 읽어 0.5(64도트 칸)를 처리한다. 인덱스 표·키는 그대로(§9·§12). **(60라운드 P1 반영)** 1층 5지역 타일셋(`tiles/v2/stage1_<region>`)이 `tileWidth`/`tileHeight` 64·`pixelScale 0.5` 가 됐고, 도트 단위 길이(`tileLights` radius·offset, `decals[].rect`, `props`·`bigProps` 의 rect·pivot·occludeAbove·light radius·offset)도 모두 2배다 — 시스템은 pixelScale 로 환산한다. 새로 그린 칸은 JSON `redrawn60`, 2배 확대 임시본은 `upscaled60`.
- **(60라운드 P1)** 1층 적 3종(dummy·archer·charger) attack 10프레임(분할 [3,1,3,3])·hurt 4프레임([70,30,30,30], flashFrame 0). 판정 시각·총 길이는 그대로. 시스템은 프레임 번호를 하드코딩하지 않고 JSON `phaseFrames`·`impactFrame`/`fireFrame`·앵커 배열·`frameDurationsMs` 를 읽는다. `elite_emblem.headTopByEnemy` dummy 119·archer 120·charger 139.

## 12. §9 쿼터뷰 타일셋 키 정리 (52라운드 Q9 · 시스템 질문 정리)
현재 아트 산출물(`tiles/v2/stage1_outer.json`)과 시스템 해석기가 맞춘 형태를 정식으로 한다.
- `walls.front` = `{ "lower": [..], "upper": [..] }`(가중치는 목록 중복). 숫자·배열 형태와 `walls.frontUpper`·`wallFrontUpper` 는 하위 호환으로만 읽는다.
- `walls.top` = v2 에서는 **벽 윗면**. 구 자동타일의 북쪽 벽 'top' 과 구분하려고 v2 타일셋은 `quarter: true` 또는 `wallHeightTiles` 가 있을 때 이 뜻으로 읽는다.
- `walls.stacking`·`topAboveFront`·`left/right/bottom/corner_*`(경계 가장자리)·`stoneSet`(엄폐 담)·`floorShadows`·`tileLights` 는 정식 키. `bigProps`·`emissiveColors` 는 예약(시스템 미사용).
- `light.flicker` = `{ "amp": 0~1, "hz": n }` (숫자면 amp 로 간주). `light.offset` = `[x, y]` 도트 단위, 정식.
- 새 인덱스는 **40번부터**(roomFloors 23~38 과 겹치지 않게).
- 신규 `roomFloorMix`: 0~1, 바탕 판석에 방 종류 바닥(`roomFloors.*`)을 섞는 비율. 없으면 0.06.
- 타일셋 소품 Y 정렬(`pivot`·`occludeAbove`) 여부는 미정 — 다음 인터뷰.
- (52라운드 Q10) 걷기·달리기 시트 JSON 에 `stride` = `{ "px": <한 주기 이동 도트>, "cycleMs": <한 주기 ms> }`. 시스템은 실제 이동 속도 / (px×pixelScale 환산 / cycleMs) 비율로 재생 속도를 조절한다(이동 속도는 바꾸지 않음).
- (52라운드 Q11) `bigProps` 정식화: 시스템이 전투장에 규칙 배치(벽 앞 가로등, 광장 화로 1~2, 구석 우물·좌판). 각 항목의 타일 인덱스 묶음·발자국(막힘 칸)·`pivot`·`occludeAbove`·`light` 를 따른다. 북쪽 벽 틈은 '골목 입구'로 그린다(전용 타일이 없으면 시스템이 어두운 벽 타일로 대체하고 아트에 요청).

## 13. 53라운드 (주인공 1.5배 · 등 상흔 · Gemini 외벽 테두리)
- 근거: `decisions/2026-10-03-round-53-playtest4.md` Q1~Q4.
- **주인공 v3 크기 변경**: 96×144 도트, `pixelScale: 0.5` → 화면 48×72(논리 px). 경로는 `sprites/player/v3/` 그대로(64×96 판을 덮어씀). 피벗 = 발 중앙(JSON `pivot`). 판정(히트박스)·이동 수치는 시스템이 정하며 그림 크기와 별개.
- **등 상흔 기준점**: 주인공 v3 몸 JSON 에 프레임별 `scarAnchor` = `{x, y, w, h, rot, visible}`(도트 좌표, 등 중앙 사각형). 뒷모습(up)은 visible:true, 측면은 어깨 쪽 작은 사각형, 정면은 false. 시스템이 플레이어가 그은 획을 이 사각형에 맞춰 줄여 빛나는 균열로 겹쳐 그린다(몸 위, 조명 영향 없음).
- **Gemini 외벽 테두리**: `assets/tiles/border/<region>/` — 북(`north.png`, 가로 이음새 없는 띠)·남(`south.png`)·서(`west.png`)·동(`east.png`)·모서리(선택) 그림 + `border.json`(각 띠의 화면 높이/폭 논리 px, 바닥과 맞닿는 기준선 y, 반복 여부, 광원 자리 `lights[]`). 바닥·충돌은 기존 격자, 벽 칸 위에 테두리 그림을 덮는다. 세부 키는 시범(외곽 거리) 산출 뒤 확정.
- (53라운드, 시스템 61e326b 해석 확정) 테두리 `border.json` 키: `bands.{north,south,west,east}`(`image`·`emissive`·`width`·`height`·`baselineY`/`baselineX`·`repeat: "x"|"none"|"sides"`·`focusX`·`lights[]`), `bands.north.sides.left|right`(`image`·`emissive`·`width`·`repeat:"x"`·`lights[]`), `doors.{north,south,west,east}`(`file`·`w`·`h`·`baselineY`/`baselineX`·`openingX/Y/W/H`·`mirrorOf`), `ambient`(참고값, 시스템은 `lighting.json` 기준). 성문은 가운데 조각의 성문이 북쪽 가운데 출구.
- **(57라운드 → §19.4)** 외벽 그림 파일은 `.png` 가 아니라 **`.webp`**(PNG 삭제), 가로·세로 4096 초과 띠는 `pieces[]` 로 나뉜다. 위 키의 뜻은 그대로.
- (53라운드 Q42·Q43) **이펙트 v3**: `sprites/fx/v3/<이름>.png/.json`, `pixelScale: 0.5`. 우선순위 v3 → v2 → 구(시트 단위 대체). 크기는 구 fx(pixelScale 2 간주)와 화면 크기가 같게 도트 ×4, 주인공에 붙는 `dash_trail`·`dash_dust` 는 ×6(§11 의 '기존 크기 ×2' 문구 정정). 프레임·ms·loop·anchor·spawn·segments·directions 는 구 시트와 동일. 도트 단위 길이(pivot·hitRadiusPx·drift.pxPerSec·tilePeriodPx)는 시스템이 pixelScale 로 환산, `scale`·`shake.px` 는 환산하지 않음. `telegraph_line` 타일 주기 64도트. 색 시트당 14 이하, 주인공 재 램프 7색 공유 허용.
- (53라운드 Q44~Q46) **무기별 이동 몸 선택**: 칼 `player_<idle|walk|run>`(칼집 쥔 몸), 대검·단검·활 `player_<idle|walk|run>_free`, 대쉬 공통 `player_dash`. 휴대 `<weapon>_carry_<동작>`, 뽑아 든 상태 `<weapon>_carry_drawn_<동작>`. 무기 시트 크기는 무기마다 다를 수 있음(대검 확대 틀) — 시스템은 JSON `frameWidth/frameHeight`·`pivot`·`playerFrameOffset` 을 읽는다. 추가 필드 `bodySheet`·`bodySheetByWeapon`·`bladeTipAnchors`·`glowRule`·`design`.
- (53라운드 Q61~Q64) **무기 이펙트 v3**: `sprites/fx/v3/<weapon>_<동작>[_<갈래>]`, 색은 주인공 재·호박 램프만(무기별 강조색 없음) — **(60라운드 Q19) 이 제한은 런 시작 때 처음 받는 기본 무기와 그 기본 이펙트에만 남고, 갈래·강화·각성 무기·각성 fx 등 나머지는 고유색 허용**. fx JSON `paletteSwap: "none"` — 시스템은 지역 바닥 팔레트 교체에서 fx 를 제외한다. fx 는 조명(라이트맵) **위**에 그린다(어둠에 묻히지 않게). 칼·대검 연격 궤적은 칼끝 반경까지 메운다. 판정 밖 프레임(선딜·잔광)은 호박 A25(#eecc78) 이하 색(반투명 아님, Q66), 백열 X0/X1 은 판정 프레임만(Q65), 지속 버프 루프(giant·gale)는 예외(Q67). 공용 fx 도 팔레트 교체 제외(Q68). `shadowstep_ghost` 는 주인공 크기(×6).

## 14. 53라운드 바닥 소품 v3 · 4지역 쿼터뷰 바닥
- 소품 우선순위: 지역 타일셋 JSON 에 `propsSheet` 가 있으면 시스템은 그 v3 시트(`tiles/v3/stage1_<region>_props.json`, `pixelScale 0.5`)의 `props`·`bigProps` 를 타일셋 13~20 소품·v2 `bigProps` 보다 먼저 쓴다. 파일이 없으면 v2. 외곽도 v3 시트가 있으면 v3(`slot` 으로 v2 13~20 대응).
- v3 소품 형식: 모든 길이는 도트(논리 px = 도트 × pixelScale). 소품 `rect`(128×128)·`pivot` 은 칸의 논리 (16,30). bigProps 는 `rect`·`footprint`·`pivot`(발자국 맨 아래 줄 가운데, 바닥 위 2 논리 px)·`solid`·`occludeAbove`·`light`/`lights[]`·`placement`·`avoidNearBorder`. `depth:"floor"` = 바닥 데칼(통과, Y 정렬 없음). index 는 참고값, rect 우선.
- 지역 타일셋 `tiles/v2/stage1_<waste|gate|brewery|hall>` 은 §9·§12 키 그대로 + `decals[]`(바닥 위·소품 아래, 통과)·`border`(테두리 경로)·양조 `canal`.
- `canal`: `frames` 를 `frameMs` 로 순환, 다리(`bridge.left/right`)만 걷기 가능, 수로 칸은 걷기 막힘·**투사체 통과**(53라운드 Q51), 다리 좌우 `litNearBridge` 칸은 `framesLit`.
- 적 v3: `sprites/enemies/v3/<id>_<동작>`, `pixelScale 0.5`, 크기는 적마다 다를 수 있음(결사병 128×176, 피벗 (64,170)). 추가 필드 `phaseFrames`·`phaseStartMs`·`impactFrame`·`fireFrame`·`muzzleAnchors`·`hammerFaceAnchors`·`flashFrame`·`emissiveColors`(판정은 기존 data 기준, 참고용).

## 15. 54라운드 1층 보스 '만취' v3 시트 · 보스방 소품
- 근거: `decisions/2026-10-03-round-54-boss1-patterns.md`.
- 경로 `sprites/bosses/v3/stage1_<동작>.png/.json`, ~~128×192~~ → **192×240 도트, 피벗 (96,220)(54라운드 Q14·Q22 확정)**, `pixelScale: 0.5`(화면 96×120) — 시스템은 JSON `frameWidth/frameHeight/pivot` 을 읽는다, 피벗 = 발 중앙(JSON `pivot`), 4방향(기존 보스 시트 방향 규칙). 우선순위 v3 → 구 `bosses/stage1_*`(동작 단위 대체). 색: 주인공·적 v3 규칙(시트당 40색 이하 권장), 술은 호박 계열.
- 동작과 JSON 이벤트 키(시스템이 읽음, 없으면 시스템 임시 타이밍):
  - `idle`·`walk`·`hurt`·`death`(기존과 같은 의미)
  - `attack`(돌진 준비·돌진, `phaseFrames`), `slam`(`impactFrame`)
  - `drink`(큰 잔 들기→들이켜기 루프→다 마심, `phaseFrames: {lift, gulp, finish}`, 프레임별 `cupAnchors {x,y,w,h}` = 약점 잔 판정 사각형)
  - `drink_break`(잔이 깨지고 술을 뒤집어씀 → 비틀 경직 루프)
  - `stagger_dash`(비틀 돌진 몸 기울기, 예고·돌진 프레임 `phaseFrames`)
  - `fall`(넘어짐→누워 있음 루프→일어남, `phaseFrames: {fall, down, rise}`)
  - `kick`(술통 걷어차기, `impactFrame`, `footAnchors`)
  - `throw`(술 뿌리기, `releaseFrame`, `handAnchors`), `throw_torch`(횃불 던지기, `releaseFrame`, `handAnchors`) — Q16 분리
  - `phase_drink`(페이즈 전환 들이켜기, 선택 — 없으면 `drink` 재사용)
- 보스방 소품(연회장 `stage1_hall_props` v3 시트 확장 또는 별도 시트): 기둥(solid, 2×2 발자국 권장), 촛대 상태 `lit`/`fallen_unlit`/`relit`(쓰러지면 통과), 굴러가는 술통(회전 프레임), 횃불 투사체, 잔 파편·술 튀김 fx(`fx/v3`, `paletteSwap: "none"`).
- (54라운드 Q18·Q21) 보스 불타는 오버레이 `fx/v3/boss1_onfire`(루프, 보스 발 기준 피벗, `paletteSwap: "none"`, 광원 포함 권장), 굴러가는 술통 1.25배(지름 약 68도트, `circumferencePx` 갱신).
- (54라운드 Q23~Q27) `boss1_rolling_barrel` 의 `circumferencePx`·`diameterPx`·`lengthPx` 는 **논리 px** 단위. `boss1_onfire` 는 보스와 같은 프레임·피벗(192×240, (96,220)), 행 = 보스 방향, `phaseFrames {ignite, loop, out}`·`loopRange`·`light`·`lightByPhase`(도트 단위 반경). ~~누운 동작(fall·death)용 불길 행/시트 추가 예정(키는 아트가 제안, 시스템은 JSON 을 따름).~~ → **54라운드 Q28: `fx/v3/boss1_onfire_down` 으로 해결(아래 항목).**
- (54라운드 Q28) `fx/v3/boss1_onfire_down`: 1행(any) 16열, `useFor`/`standFor` 로 보스 동작 프레임별 누운/서 있는 불길 선택, `frameOffsets` [dx,dy] 도트(빛도 함께 이동), 두 시트 `phaseFrames`·타이밍 동일 — 전환 시 열 번호 이어 씀. 죽음은 마지막 프레임에서 out.

## 16. 55라운드 무기 이펙트 전면 디벨롭 (타격감·움직임·갈래)
- 근거: `decisions/2026-10-03-round-55-weapon-fx-overhaul.md`.
- 적중 스파크 `fx/v3/hit_<weapon>`·`hit_<weapon>_heavy`(막타 = 연격 마지막 타·대쉬 공격 마무리·치명타): `anchor: hitbox_center`, `rotate: true`·`drawnFacing`(공격/화살 진행 방향으로 회전), `flipY: "allowed"`, `glowFrames`, `holdFrame`(히트스톱 중 정지 프레임), `hitstopMs`(참고값 — 시스템 Q6 표가 기준), `shakeHint`(참고), `replaces: "hit_burst"`.
- 재 파편 입자 `fx/v3/particles_ash`: `kinds.<이름>{frames, frameMode loop|life, lifeMs, speedPxPerSec, gravityPxPerSec2, dragPerSec, frameMs, …}`, `recipes.<hit 시트>`(kind별 개수·`coneDeg`). 길이는 도트(pixelScale 0.5).
- 칼끝 잔상 리본 `fx/v3/ribbon_ash`·`ribbon_ash_thin`: 가로 x=0 꼬리(재)→끝 머리(호박), 프레임 = 나이 단계, `ribbon.uMode: "stretch"`, 반투명 대신 색 단계·디더.
- 움직임 fx(dash_trail·dash_dust·parry_flash·guard_wave·ironwall·shadowstep_ghost·aim_charge): 프레임 수·ms 변경 가능 — 시스템은 JSON `frameDurationsMs` 를 읽는다. `previous`(이전 값 기록), ironwall `depthByDirection {"up": "below"}`.
- 소유: `guard_wave`·`ironwall`·`shadowstep_ghost`·`aim_charge` 빌드는 `parts/art/work/fx_v3/build_feel.py`(작업 B).

## 17. 55라운드 칼·대검 새 연격 (아트·시스템 공용 규격)
- 근거: `decisions/2026-10-03-round-55-weapon-fx-overhaul.md` Q18~Q25, `decisions/research-2026-10-03-melee-combos.md`.
- **(56라운드 갱신)** 아래 항목 중 `(56라운드 → §18)` 표시가 붙은 부분은 §18 이 우선한다(템포·칼 반경·칼 3타·대검 8방향·차지·붓획·무기 틀).
- 각도 표기: 조준 방향 = 0°, 화면 기준 시계 방향 +. R = 현재 판정 반경(칼 ~~33~~ **38(56라운드 Q1 사거리 ×1.15 → §18)**·대검 51 월드 px), ×는 R 배율. 수치는 출발점(시스템 데이터로 조정).
- **칼 K-A 발도 초승달** — (56라운드 → §18: 3연격 템포 Q1, 1·2타 모양은 유지)
  - 1타 대각 올려베기: 비대칭 호 110°, +70°→−40°, ×1.0, 빠름, 내딛기 4~6px.
  - 2타 대각 내려베기: 비대칭 호 110°, −70°→+40°(1타 역방향, X자 교차), ×1.0, 빠름, 내딛기 4~6px.
  - 3타 수평 발도(마무리): 초승달 150°, ~~+75°→−75°~~ **−75°→+75°(왼 허리 칼집에서 뽑는 방향, Q26)**, ×1.25, 납도 자세 선딜(중간 템포), 내딛기 14~16px. **150ms 뒤 같은 호에 잔상 베기 2차 판정(피해 50%)** — 전용 잔상 fx. → **(56라운드 → §18) 3타는 '일섬'(4칸 돌진 일자 베기, Q2)으로 교체, 잔상 베기는 '그림자 분신'(검기 3단일 때만, Q3·Q28·Q29)으로 교체.** 이 3타 시트(`katana_crescent`·`katana_crescent_echo`)는 보관(Q35).
- **대검 G-C 관성 순환** — (56라운드 → §18: 8방향 그림 Q6, 무게 프레임 Q5, 3타 ~2.6초 템포 Q25)
  - 연격: H1 수평 시계 방향 150°(×1.0, 내딛기 4~6px) → V 정면 내려찍기(좁은 쐐기 40° ×1.3 + 끝점 충격원 반경 0.35R, 내딛기 ~12px, 무거운 히트스톱·흔들림) → H2 수평 반시계 150° → V → H1 … 입력이 이어지는 한 끊김 없이 교대.
  - 관성: 이어지는 타마다 공속 +5%, 최대 +20%, 1초 무입력·피격 시 초기화. 최대일 때 V 충격원 확대.
  - 홀드 차지(좌클릭 홀드): 3단 0.4 / 0.8 / 1.2초, 단계마다 호박 번쩍임, 떼면 차지 내려찍기 — 쐐기 길이 ×1.3 / 1.5 / 1.8, ~~3단은 충격파 링 추가~~ **(56라운드 Q10 → §18) 기본 차지는 충격파 없음(땅 균열만), 개성 발현 후에는 휘두르지 않는 '꽂아내리기' + 마우스 방향 충격파**. 차지 중 이동 ×0.35. 우클릭 가드 유지.
- **판정 모양 종류(시스템 데이터)**: `arc`(내반경 있는 호: 시작각·끝각·내반경), `wedge`(좁은 쐐기 + 선택 `impactCircle`), `rect`(찌르기), `ring`(충격파). 타마다 지정.
- **그림(아트)**: 몸 v3 `player_<weapon>_<동작>`·무기 v3 `<weapon>_<동작>`·fx v3 `<weapon>_<동작>` 를 새 동작 단위로. 이펙트는 원 전체가 아니라 판정 호를 따라 2~3프레임에 그려 나가는 ~~부분 초승달~~ **붓으로 그은 한 획(56라운드 Q11 → §18)**(내려찍기는 세로로 선 가는 호 + 바닥 균열·먼지 링). JSON 에 판정 프레임(`impactFrame`/`glowFrames`/`holdFrame`)·`bladeTipAnchors`(칼 포함 모든 근접)·`hitShape` 참고값. 동작 이름은 아트가 제안, 시스템은 JSON 을 따름(보고서 표로 공유).
- 갈래(1단·2단) 시트는 기본 연격 데모 확인 후 새 모양에 맞춰 다시 그린다(Q25).
- (55라운드 Q26~Q28) 새 연격 시트 이름: 몸 `player/v3/player_<동작>`·무기 `weapons/v3/<동작>`·fx `fx/v3/<동작>` — 동작 = `katana_rise`·`katana_fall`·`katana_crescent`(+fx `katana_crescent_echo`), `greatsword_sweep_cw`·`greatsword_cleave`(+fx `greatsword_cleave_impact`)·`greatsword_sweep_ccw`·`greatsword_charge`(fx `greatsword_charge_flash_lv1~3`)·`greatsword_charge_slam`(fx `greatsword_charge_slam_lv1~3`·`greatsword_charge_ring`). 대검 새 무기 틀 ~~240×264·피벗 (117,200)·offset (69,62)~~ **240×280·피벗 (117,207)·offset (69,69)(56라운드 작업 B → §18)**. 왼쪽 방향은 그림·판정 모두 180° 회전(`dirTransform: rotate`, 거울 아님) — **(56라운드 Q6 → §18) 대검은 8방향을 직접 그린 `dirTransform: drawn8`(회전·반전 없음), 칼·단검·활은 `rotate` 유지**. 56라운드 추가 동작: `katana_issen`(3타 일섬), `greatsword_charge_plunge`(꽂아내리기) — §18. 대검 차지 3단 번쩍임만 백열 허용(Q27). 타이밍 기준 = 아트 JSON(`timingMs`·`spawnAtMs`·`impactFrame`).

## 18. 56라운드 무기 피드백 (아트·시스템 공용 규격)
- 근거: `decisions/2026-10-04-round-56-weapon-feedback.md` Q1~Q55. 아트 산출: 커밋 2a943eb(작업 A — 붓획·칼 템포·일섬·분신·단검 fx), c2f2a91(작업 B — 대검 8방향 무게 프레임·땅 균열·충격파·단검 1.3배·활 당겨 떼기), 65bf004(작업 C — 공격 수단 키아트, 참고 그림), 07d3c00(작업 D·E1·E2 — 대검 fx 8행 정리·자원/상태 표시·약한 화살 / 칼·대검 새 기본기 / 단검·활 새 기본기), 5f7dae8(작업 F — Q51 JSON 정리·새 동작과 뽑기·넣기·보조 동작의 검기·울분 오버레이). 아래 수치는 아트 JSON 에서 옮긴 값이다. 판정·피해는 §17 원칙대로 **시스템 데이터가 기준**(JSON `hitShape` 등은 참고값). 인터뷰로 정한 값은 '결정'으로 따로 적는다(JSON 문구와 다르면 결정이 우선).
- 단위: JSON 의 `…Px`·`pivot`·anchor 는 **도트**(`pixelScale: 0.5`, 월드 px = 도트 / 4). `world` 표기는 월드 px. 판정 원점 = 피벗(발) 위 40 도트. 시간 ms, 0 = 몸 시트 재생 시작. 56라운드 시트 JSON 의 `version` 은 `"v3-r56"`(작업 A·B·E2·F), `"v3-r56-e1"`(작업 E1 칼·대검 새 기본기), `"v3-r56d"`(작업 D 자원·상태·약한 화살·검기/울분 오버레이) 중 하나, 설명 필드 `r56` 에 근거 Q 번호.

### 18.1 공통
- **fx 생성 시각 `spawnRule`**: `spawnAtMs = 몸 hitAt − sum(fx frameDurationsMs[:impactFrame])`(아트 빌드 때 현재 몸 JSON 으로 계산). 몸 타이밍을 데이터로 바꾸면 같은 식으로 다시 계산하면 그림이 맞는다. fx 필드 `spawn: "body_ms"`·`spawnAtMs`·`impactAtBodyMs`.
- **붓획 궤적(Q11)**: 연격 fx 는 채운 초승달 면 대신 붓 한 획 — 시작 가늘고·가운데 굵고·끝 갈라짐, 판정 호를 따라 2~3프레임에 그어 나가고 시작 쪽부터 재로 마름. JSON `brushStroke: true`, `drawnArc{fromDeg, toDeg, radiusDots, brushWidthDots, …}`(붓획 바깥 가장자리 ≈ 판정 반경), `frameRoles`(pre → draw → draw(끝까지) → decay…). 백열은 `glowFrames` 의 획 머리 몇 도트만. 55라운드 그림은 `previous` 경로(`parts/art/work/combo56_fx/prev55/`)에 보관.
- **히트스톱 정지 프레임(Q37)**: 붓획이 다 그어진 **다음 칸**에서 멈춘다(55라운드 Q14 규칙 대체). 56 연격 fx JSON 에는 전용 정지 프레임 키가 없다 — `frameRoles` 의 'draw(끝까지)' 다음 칸이 그 칸. **결정(Q51): 시스템이 `frameRoles` 로 계산, 키는 추가하지 않는다.** (일부 새 fx 는 `holdFrame` 을 따로 적어 둠 — `dagger_backstab`·`guard_perfect_fx`, 그 시트는 `holdFrame` 우선.)
- **무기 적중 번쩍임(Q12)**: 적중 순간 무기 그림이 크게·하얗게 번쩍 — 기준 그림은 무기 시트의 판정 프레임(`glowFrames`·`frameStates: "glow"`). **결정(Q50): 판정 첫 1프레임만 백열, 그다음 판정 프레임은 호박.**
- **행 규약(56라운드 추가)**: `dirTransform` = `rotate`(§17, 칼·단검·활) · `drawn8`(대검 8방향, §18.3) · `drawn4`(칼 새 기본기 fx `katana_counter`·`katana_iai` — JSON `directionNote`: 4행 = 칼 몸 행 순서, left 는 §17 180° 회전 규칙으로 그려 둠). 행이 방향이 아닌 시트는 `rowsAre` 로 표시 — `"sizes"`(s·m·l), `"stacks"`(1~5), `"kinds"`(guard·parry). 이 시트는 방향으로 행을 고르지 않는다.
- **이동형 동작 공통 필드**: `dash`·`dashPx`·`leapPx`·`sidestepPx` = `{world, dots, frames, startMs, endMs, easing, stopsAtWall}`(있는 키만). 그림은 제자리(피벗 고정), 이동은 시스템. 방향키와 무관하게 조준 방향(비켜섬은 `side`). 벽에 막히면 그 자리에서 멈추고 남은 프레임은 그대로 재생.
- **칼끝 리본(§16 `ribbon_ash`, Q38)**: 기본 연격에서는 끄고 돌진류(그림자 걸음·꽂아내리기 등 이동 궤적)에만.
- 적 피격 번쩍임 = 호박색 반투명 80ms, 히트스톱으로 늘어나지 않음(Q36) — 시스템 처리, 시트 변경 없음.

### 18.2 칼 (Q1·Q2·Q3·Q28·Q29·Q31·Q34·Q35·Q48·Q49)
- **판정 반경 R = 38 월드 px(152 도트)** — §17 의 33 대체(사거리 ×1.15, Q1). 몸 96×144·피벗 (48,138), 무기 192×192·피벗 (96,186)·`playerFrameOffset (48,48)`, 4행·`dirTransform: rotate`(§17 그대로).
- 연격(3연격 합 470 + 440 + 740 = 1650ms, 타마다 잔심 정지 — **결정(Q49): 1.65초 그대로**, 데모로 조정). 칼 가드 = 우클릭, 누른 직후 0.15초 안 피격 = 패링(**결정 Q48**, 11라운드 0.2초 대체 — §18.10 `guard_perfect_fx`):

| 동작 (몸·무기·fx 같은 이름) | 프레임 | frameDurationsMs | total / hitAt / activeEndAt / cancelAt | impactFrame (hitFrames) | 판정 참고 | 내딛기 (월드) | fx 틀 · 피벗 · spawnAtMs · fx impactFrame |
|---|---|---|---|---|---|---|---|
| `katana_rise` 1타 대각 올려베기 | 8 | 60, 60, 30, 40, 30, 60, 130, 60 | 470 / 150 / 190 / 410 | 3 ([3]) | `arc` +70°→−40°, ×1.0 | 5, 프레임 [1,2,3], 60ms~ | 320×328 · (156,223) · 120 · 1 |
| `katana_fall` 2타 대각 내려베기 | 7 | 70, 50, 40, 30, 60, 130, 60 | 440 / 120 / 160 / 380 | 2 ([2]) | `arc` −70°→+40°, ×1.0 | 5, 프레임 [1,2], 70ms~ | 312×336 · (156,224) · 70 · 1 |
| `katana_issen` 3타 일섬 | 12 | 60, 50, 110, 30, 40, 40, 40, 110, 70, 60, 90, 40 | 740 / 250 / 330 / 700 | 4 ([4,5]) | `rect`(아래) | 돌진 64(아래) | 선 시트 `katana_issen_line_*`(아래) |

- **일섬 `player_katana_issen`·`weapons/v3/katana_issen`(Q2·Q34)**: `phases` 납도 [0,1] → 거합 자세 [2] → 돌진 [3~6] → 잔심 [7] → 피 털기 [8] → 납도 [9,10] → 일어섬 [11]. 끝 = 칼집에 넣은 상태(`katana_carry_idle`, Q34), 다음 1타는 뽑기 후 베기.
  - 돌진 `dash`: `startMs 220`·`endMs 370`(150ms), `distancePx` 64 월드(256 도트) = 4칸, `easing: linear`, `stopsAtWall`, `invulnerable`(`invulnFrames` = `dashFrames` = [3,4,5,6]), `passesThroughEnemies`. 방향키와 무관하게 조준 방향(4행)으로. 그림은 제자리(피벗 고정), 이동은 시스템. 벽에 막히면 그 자리에서 멈추고 남은 프레임은 그대로 재생.
  - 판정 `hitShape: rect` — 원점 = 돌진 출발 시점의 판정 원점, 0° = 돌진 방향, `fromPx −24`·`lengthPx 320`·`widthPx 72` 도트(월드 −6 / 80 / 18: 출발 피벗 뒤 24 도트 ~ 도착 피벗 앞 40 도트). 벽에 막혀 짧게 멈추면 `lengthPx` = 실제 이동 거리 + 64 도트. 판정 프레임 [4,5](250~330ms).
- **일섬 선 `fx/v3/katana_issen_line_t1~t4` + `_solo`**:

| 시트 | 틀 | 피벗 | `tiles` · `travelPx` |
|---|---|---|---|
| `katana_issen_line_t1`(`_solo`) | 248×256 | (121,161) | 1칸 · 16 월드(64 도트) |
| `katana_issen_line_t2`(`_solo`) | 368×376 | (184,224) | 2칸 · 32(128) |
| `katana_issen_line_t3`(`_solo`) | 496×504 | (247,287) | 3칸 · 48(192) |
| `katana_issen_line_t4`(`_solo`) | 624×624 | (308,348) | 4칸 · 64(256) |

  - 공통: 12프레임 `[30, 40, 40, 40, 50, 50, 50, 50, 50, 60, 80, 80]`(620ms), 4행 = 돌진 방향, `impactFrame 1`, `burstFrame 8`(`burstAtLineMs 350` = 몸 570ms).
  - `anchor: "dash_start_pivot"` — 일섬 돌진을 시작한 순간의 주인공 발 위치(월드)에 고정, 주인공을 따라가지 않음. 선은 판정 원점 높이(피벗 위 40 도트)에서 돌진 방향으로 그어짐.
  - 생성: `spawnAtMs 220`(= `dash.startMs`), 출발 피벗에 1회. 고르기 `pickRule`: **실제 이동 칸 수**(벽에 막히면 줄어듦)를 내림해 t1~t4(4칸 = t4, 1칸 미만 = t1).
  - 깊이 `depth: "below_player"` — 바닥 바로 위, 주인공·적·그림자 분신 아래. 조명 위(fx 규칙)는 유지.
  - **분신 유무로 고르기(Q28)**: 검기 3단 소모 일섬(분신이 따라옴) = `katana_issen_line_tN`(`glowFrames [1,2,8]`, f5~f7 분신이 지나간 부분만 다시 밝아짐, f8 = 분신 도착 터짐). 그 밖의 일섬 = `katana_issen_line_tN_solo`(`glowFrames [1,2]`, `shadowSheet: null`). 짝은 각 JSON `soloVariant`·`withShadow`. 몸·무기 JSON `lineSheets` 는 8키 — `t1`~`t4`(분신 있음) + `t1_solo`~`t4_solo`(분신 없음)(작업 F).
  - `_solo` 의 f8 터짐은 **연출만, 추가 피해 없음**(Q31 — A25 이하 색).
- **그림자 분신 `fx/v3/katana_issen_shadow`(Q3 → Q28·Q29)**: 192×208, 피벗 (94,146) = 분신 발, 8프레임 `[50, 50, 50, 60, 50, 60, 70, 80]`, 4행 = 돌진 방향, 색 9.
  - **조건: 검기 3단을 소모한 일섬일 때만**(Q28 — Q3 '일섬마다'와 아트 메모 '일섬 0.2초 뒤' 대체). 몸·무기 JSON `shadow.condition: "ki3_spent"`(`conditionRef` Q28), fx JSON `condition` 도 같음(작업 F). `shadow.startAtMs 420`·`arriveAtMs 570`.
  - `anchor: "issen_shadow_path"` — `travelFrames [0,1,2]`(`travelMs 150`) 동안 출발 피벗 → 도착 피벗(주인공이 실제로 멈춘 자리) 선형 이동, `slashFrame 3`, `vanishFrames [4~7]` 은 도착 피벗에 고정. 생성 `spawnAtMs 420`(몸 기준, 돌진 시작 + 200ms).
  - **피해: 도착 순간 1회(몸 570ms = 선 `burstFrame`), 일섬 선(`hitShape` rect, 실제 이동 거리) 위 적 전부에 50%**(Q29). 몸·무기 JSON `shadow.damageScale 0.5`·`shadow.damageTiming {rule: "arrive_once", atBodyMs: 570, target: "issen_line_rect"}`(작업 F). fx JSON `hitTimingOptions` 는 검토 기록(A 채택).
  - 깊이: JSON `depth` = 주인공처럼 Y 정렬(일반 스프라이트 깊이 권장), `lit: false`.
- **`katana_crescent`(몸·무기·fx) + fx `katana_crescent_echo` 보관(Q35)**: 55라운드 3타 수평 발도·잔상 시트. 기본 연격에서는 쓰지 않고, 갈래·새 공격 수단 재사용 후보 — 삭제하지 않는다.

### 18.3 대검 (Q5·Q6·Q10·Q25·Q27·Q30·Q32·Q51)
- **8방향 `directionRows`(Q6)** — 몸·무기·연격 fx 공통 행 순서(기존 4행 뒤에 대각 4행):

| 행 | direction | 화면각 | 몸 |
|---|---|---|---|
| 0 | down | 90° | 정면 |
| 1 | up | −90° | 뒷면 |
| 2 | left | 180° | 측면 |
| 3 | right | 0° | 측면 |
| 4 | down-right | 45° | 정면 3/4 |
| 5 | down-left | 135° | 정면 3/4 |
| 6 | up-right | −45° | 뒷면 3/4 |
| 7 | up-left | −135° | 뒷면 3/4 |

  - `dirTransform: "drawn8"` — 8방향 모두 직접 그린 그림(회전·반전 없음). 행 = 조준각 8분할(−22.5°~22.5° = right, 시계 방향). 판정·fx 각도는 조준각 그대로(§17 회전 규칙).
  - 대각 몸은 정면/뒷면 몸에 3/4 단서(진짜 3/4 리그는 나중, Q27). 아래 대각 내려찍기는 칼 수평 성분을 ±38°, 기울기 −46° 까지 세움. 위 대각 내려찍기는 칼이 몸 너머로 가려지고 방향은 바닥 균열·붓획이 보여 줌(Q27).
- **무기 틀**: 240×280, 피벗 (117,207), `playerFrameOffset (69,69)`(§17 의 240×264·(117,200)·(69,62) 대체). `depth` 8방향 모두 `above`, `occlusionBaked`. 방향별 칼 방향 `bladeLocalByDirection`.
- **무게 필드(Q5)**: `frameRoles`(windup·hold·heave·strike·drag·catch·link, 내려찍기 planted, 꽂아내리기 turn·raise·plunge·pull·recover), `holdFrames`(머리 위/뒤에서 버팀 = 긴 선딜), `dragFrames`(칼 무게에 몸이 끌려감), `dragStepPx{world, dots, frames, startMs}`(끌림 이동 참고값, 방향키와 무관 — 시스템 판단), `stepPx`(내딛기 — 방향키를 누를 때만). 적을 크게 튕겨 내는 연출은 채택 안 함(Q5).
- **동작별 값**(몸 `player_<동작>`·무기 `weapons/v3/<동작>` 같은 프레임, 몸 96×144·피벗 (48,138)):

| 동작 | 프레임 | frameDurationsMs | total / hitAt / activeEndAt / cancelAt | impactFrame (hitFrames) | holdFrames / dragFrames | dragStepPx · stepPx (월드) | 판정 참고 |
|---|---|---|---|---|---|---|---|
| `greatsword_sweep_cw` H1 | 11 | 60, 80, 110, 70, 60, 40, 50, 70, 90, 90, 100 | 820 / 380 / 470 / 630 | 5 ([5,6]) | [2,3] / [7,8] | 6 (470ms~) · 5 [4,5] | `arc` −75°→+75°, 내반경 0.35R (150°, Q32 유지) |
| `greatsword_cleave` V | 12 | 60, 90, 120, 80, 50, 40, 40, 70, 100, 90, 80, 100 | 920 / 440 / 480 / 740 | 6 ([6]) | [2,3] / [7,8] | 4 (480ms~) · 12 [4,5,6] | `wedge` 40° ×1.3 + `impactCircle` 0.35R |
| `greatsword_sweep_ccw` H2 | 11 | sweep_cw 와 같음 | 820 / 380 / 470 / 630 | 5 ([5,6]) | [2,3] / [7,8] | 6 (470ms~) · 5 [4,5] | `arc` +75°→−75°, 내반경 0.35R |
| `greatsword_charge` 홀드 | 7 | 80, 100, 120, 100, 100, 100, 100 | — | — | `holdFrame 3` | — | 단계 0.4 / 0.8 / 1.2초 |
| `greatsword_charge_slam` 기본 차지 | 9 | 40, 60, 40, 40, 80, 110, 120, 100, 110 | 700 / 180 / 260 / — | 4 ([4]) | [0] / [5,6] | — · 12 [2,3,4] | `wedge` 40° ×1.3 / 1.5 / 1.8(단계) + `impactCircle` 0.35R |
| `greatsword_charge_plunge` 꽂아내리기 | 9 | 40, 70, 80, 90, 40, 90, 160, 110, 120 | 800 / 280 / 320 / — | 4 ([4]) | [0,3] / [5,6] | — | 꽂힌 자리 `ring` 0.45R(91.8 도트) + 충격파 fx |

  - 템포: H1 → V → H2 = 820 + 920 + 820 = 2560ms(Q25, 55라운드 Q29 '약 2초' 대체). 몸·무기 JSON `msNote` 근거도 Q25 로 정리됨(작업 F).
  - `greatsword_charge`: 들어 올림 [0,1,2] 1회 → 홀드 동안 `loopRange [3,6]` 반복(시트 `loop: false`, 시스템이 반복 재생). 단계 번쩍임 `greatsword_charge_flash_lv1~3`(55라운드 규격). `nextMove` = 기본 → `greatsword_charge_slam`, 개성 발현 후 → `greatsword_charge_plunge`(Q10).
  - **`greatsword_charge_slam`(Q10 기본 차지)**: 칼로 직접 강하게 내려침, **충격파 링 없음**(`greatsword_charge_ring` 은 쓰지 않음 — fx `charge_slam_lv1~3` JSON 의 `ringStage3`·`ringSheet` 필드는 제거됨, 몸 JSON `chargeBasicNote`, 작업 F). 땅 충격 = `greatsword_ground_crack`, 행 `rowByStage [m, m, l]`, impactFrame 시작에 쐐기 끝점.
  - **`greatsword_charge_plunge`(Q10 개성 발현 후 차지)**: 휘두르지 않고 칼을 땅에 수직으로 꽂아 마우스 방향 충격파. `plantFrames [4,5,6,7]`, `plantAnchors` = 칼이 바닥에 꽂힌 점(몸 시트 도트, 꽂힌 프레임만 값·나머지 null): down (45.0,143.8)·up (51.0,132.2)·left (31.5,136.9)·right (64.5,139.1)·down-right (50.6,143.8)·down-left (39.7,143.1)·up-right (56.3,132.9)·up-left (45.4,132.2). impactFrame 시작에 이 점을 피벗으로 `greatsword_plunge_wave`(마우스 방향) + `greatsword_ground_crack` 행 l. 땅속 칼 부분은 그리지 않음.
- **대검 fx**:

| fx | 틀 | 피벗 | 프레임 · ms | spawnAtMs (impactFrame) | 행 |
|---|---|---|---|---|---|
| `greatsword_sweep_cw` | 440×448 | (219,267) | 6 · 40, 45, 45, 40, 40, 40 | 340 (1) | 8행 `drawn8` |
| `greatsword_sweep_ccw` | 440×448 | (217,265) | 6 · 40, 45, 45, 40, 40, 40 | 340 (1) | 8행 `drawn8` |
| `greatsword_cleave` | 568×576 | (282,322) | 6 · 40 ×6 | 360 (2) | 8행 `drawn8` |
| `greatsword_charge_slam_lv1` | 568×576 | (282,322) | 6 · 40, 40, 40, 40, 40, 50 | 100 (2) | 8행 `drawn8` |
| `greatsword_charge_slam_lv2` | 648×656 | (324,364) | 6 · 40, 40, 40, 40, 50, 60 | 100 (2) | 8행 `drawn8` |
| `greatsword_charge_slam_lv3` | 776×784 | (387,427) | 6 · 40, 40, 40, 50, 60, 70 | 100 (2) | 8행 `drawn8` |
| `greatsword_ground_crack` | 424×352 | (217,179) | 8 · 40, 50, 60, 80, 110, 150, 200, 260 | 몸 impactFrame 시작 (0) | 3행 = 크기 |
| `greatsword_plunge_wave` | 416×112 | (−1,55) | 8 · 40, 40, 40, 50, 50, 60, 70, 90 | 몸 impactFrame 시작 (0) | 1행 `any` |

  - `greatsword_cleave`·`charge_slam_lv*` 의 끝점 충격 `greatsword_cleave_impact`(55라운드 규격, `impactSheetScale` cleave 관성 최대 1.3 · 차지 1.0 / 1.15 / 1.3 참고값).
  - **`greatsword_ground_crack`**: `directions` 칸에 크기 키 `s`·`m`·`l` — **`rowsAre: "sizes"`**, 방향으로 고르지 않음(`rotate: false`, 회전·반전 없음). `anchor: "hitbox_center"` = 내려찍은 자리(V·차지 = 쐐기 끝점 충격원 중심, 꽂아내리기 = `plantAnchors`). 크기 `s` 반경 102 도트(0.5R) = V 내려찍기(관성 최대면 `m`), `m` 143(0.7R) = 차지 1·2단, `l` 204(1.0R) = 차지 3단·꽂아내리기. 세로 압축 `groundKy 0.85`, `depth: "above"`, `shakeHint` s 4px·100ms / m 6·130 / l 8·170(참고). f4~f7 은 식은 금 — 오래 남기려면 마지막 프레임을 붙잡고 시스템이 끄는 시점을 정함(반투명 금지). `greatsword_cleave_impact` 와 함께 써도, 대신 써도 된다.
  - **`greatsword_plunge_wave`**: `anchor: "plant_point"`(꽂힌 자리), `rotate: true`·`drawnFacing: "right"`(마우스 방향 각도로 회전)·`flipY: "allowed"`, `depth: "above"`. 판정 참고 `hitShape: rect` `fromPx 0`·`lengthPx 408`(2.0R)·`halfWidthPx 52`, 앞머리 **`frontPxByFrame [70, 150, 230, 310, 380, 408, 408, 408]`**, 판정 프레임 [0~4] — 앞머리가 지나간 칸만 맞히거나 판정 프레임 동안 전체 사각형(시스템 데이터 기준). `shakeHint` 7px·160ms.
  - **대검 fx 8행(Q30·Q51)**: 대검 방향성 이펙트는 몸·무기 시트와 같은 `directionRows` 순서의 8행 `dirTransform: "drawn8"` 시트 — 연격 3종(`greatsword_sweep_cw`·`greatsword_cleave`·`greatsword_sweep_ccw`)·`greatsword_charge_slam_lv1~3`(각 JSON `directionRows`·`directionRowsNote`)과 새 기본기 fx(§18.8). 몸 시트에서 고른 행 번호를 fx 에도 그대로 쓴다. 대각 전용 `_diag` 시트는 **없다**(만들지 않음). 둥글거나 작은 fx `greatsword_cleave_impact`(1행)·`greatsword_charge_flash_lv1~3`(4행)·`greatsword_charge_ring`(1행, 기본 차지에는 안 씀)은 8행 통일에서 빼고 55라운드 `rotate` 규격 유지(**결정 Q51**). `greatsword_ground_crack`·`greatsword_plunge_wave` 는 방향 무관(위).

### 18.4 단검 (Q4)
- **무기 그림 1.3배**: `weapons/v3/dagger_combo1~3`·`dagger_special`·`dagger_carry_idle/walk/run/dash` — 같은 디자인을 새 치수로 다시 래스터(최근접 확대 아님): 조각 길이 16.0→20.8·폭 최대 7→9 도트·손잡이 4.5→5.8(JSON `scale56`). 틀 192×192·피벗 (96,186)·`playerFrameOffset (48,48)` 은 그대로.
- **판정 참고(몸·무기·fx `dagger_combo1~3` JSON)**: 찌르기 직사각 판정의 수평 길이 ×1.5, 폭·시작점·각도는 그대로. **몸·무기 JSON 최상위 `thrust` 가 56값**(작업 F 정리 — Q51), 이전 값은 `previousThrust`(최상위와 `hitReference56` 안). 최상위 `thrust` = `hitReference56.thrust` = fx `thrust`. 피해 ×1.4 는 시스템 데이터. 타이밍(빠른 템포)은 그대로.

| 타 | lengthPx (도트) `previousThrust` → `thrust` | widthPx | angleDeg | fromPx | total / hitAt | fx 틀 · 피벗 |
|---|---|---|---|---|---|---|
| `dagger_combo1` | 96 → 144 | 32 | −8 | 16 | 160 / 50 | 328×344 · (164,204) |
| `dagger_combo2` | 96 → 144 | 32 | +10 | 16 | 150 / 40 | 336×336 · (165,205) |
| `dagger_combo3` | 112 → 168 | 40 | 0 | 16 | 280 / 60 | 400×400 · (199,236) |

### 18.5 활 (Q9·Q20·Q26·Q27·Q55)
- **`player_bow_draw_hold` + `weapons/v3/bow_draw_hold`**(`bow_aim` 대체): 우클릭을 누르는 동안 당김, **자동 발사 없음**. 14프레임 `[90 ×10, 70 ×4]`, 4행, 무기 192×192·피벗 (96,186)·offset (48,48).
  - f0~f5 = 진행도 구동(`progressDriven`): `frame = min(5, floor(p × 5))`, **`fullFrame 5`**(가득). 진행 속도(가득까지 시간)는 시스템 데이터.
  - `holdLoop [6,9]` — 가득 뒤 계속 누름(시위 1px 떨림).
  - `strainLoop [10,13]` — 너무 오래 쥠: 조준선 흔들림·위력 감소(Q20 · Q27 채택, JSON `strainLoopNote` 도 채택 표기로 정리됨 — 작업 F). 시작 시점·감소량은 시스템 데이터.
  - 당기는 중 이동 50%(Q20).
- **`player_bow_release` + `weapons/v3/bow_release`**: 4프레임 `[40, 60, 80, 100]`(release → follow → recover → ready), **`releaseFrame 0`** = 놓는 순간 화살 생성. 일찍 놓은 약한 화살도 같은 몸 시트(구분은 화살 그림). 끝 = 계속 우클릭이면 바로 `bow_draw_hold`, 아니면 `bow_carry_idle`.
- **`arrowSpawnAnchors`**(무기 `bow_release` JSON, f0 만 값): 무기 시트 좌표 down (102.8,115.3)·up (89.2,86.9)·left (55.5,103.2)·right (136.5,98.4). 화살 생성 점이자 `bow_perfect_release`·`bow_muzzle_rapid` 의 피벗(몸 좌표 = 무기 좌표 − (48,48)).
- **`fx/v3/bow_perfect_release`**: 112×104, 피벗 (36,56) = 화살 생성 점, 5프레임 `[30, 40, 50, 60, 80]`, 1행 `any`, `rotate: true`·`drawnFacing: "right"`(발사 각도), `anchor: "projectile"`, `depth: "above"`, `glowFrames [0,1]`(백열 허용). **완벽 놓기 = 가득(f5 도달) 직후 0.15초 안에 뗌**(Q9)일 때만 `bow_release` f0 시작에 1회. 일반 놓기는 없음(또는 `bow_muzzle_rapid`).
- **`fx/v3/bow_arrow_weak`(Q26)**: 일찍 뗀 약한 화살 전용 그림 — 촉이 어둡고 짧게 흔들리는 연기 꼬리. 64×24, 피벗 (40,12), 4프레임 `[60 ×4]` 루프(`anim: "loop_move"`), 1행 `any`, `anchor: "projectile"`, `rotate: true`·`drawnFacing: "right"`·`flipY: "allowed"`, `depth: "above"`. 기존 `bow_arrow`(48×24, 피벗 (24,12))와 같은 축 — 화살 픽셀은 피벗 기준 같은 자리, 꼬리 쪽으로 16 도트 넓힘. 가득(f5) 전에 놓으면 `bow_arrow` 대신 이 시트(`spawn: "early_release"`). **결정(Q55): 한 시트를 갈래 공용으로** — 속사·저격 갈래 화살(`_rapid`·`_snipe`) 상태에서도 일찍 놓으면 이 시트(JSON `replacesWhen` 의 '질문 사항'은 이 결정으로 정리). 피해·속도는 시스템 데이터.

### 18.6 새 기본기 요약 (Q21~Q24 키아트 → Q40~Q43 입력 · Q48·Q52~Q55 결정)
- 시트 이름: 몸 `player/v3/player_<키>`·무기 `weapons/v3/<키>`·fx `fx/v3/<키>`(+ 표의 보조 fx). 상세 규격은 §18.7~§18.9.

| 무기 | 키 | 동작 | 입력·조건 (Q40~Q43, 수치는 임시값) | 결정 |
|---|---|---|---|---|
| 칼 | `katana_counter` | 간파 반격 | 기본기 — 패링 성공 직후 0.4초 안 좌클릭. 패링 = 우클릭 가드를 누른 직후 0.15초 안 피격(Q48) | 비켜섬 = 조준 방향의 해부 왼쪽 6 월드 px, 호 130° ×1.1(Q55) |
| 칼 | `katana_iai`(+fx `katana_iai_ready`) | 대치 일격 | 기본기 — F 로 넣은 채 좌클릭을 누르고 있다가 떼면 발도 일격(넣기 첫 타 치명과 연결) | **언제 떼도 같은 일격, 최소 유지 시간 없음**(Q53 — 넣기 첫 타 치명은 그대로). 납도 딸깍 터짐은 연출만·칼집에 넣은 채 끝(Q55) |
| 대검 | `greatsword_tackle` | 어깨 태클 | 기본기 — 대쉬 중 좌클릭(대쉬 공격 `greatsword_dashslash` 교체) | 적을 밀고 감, 돌진 40 월드 px, fx 는 첫 접촉 순간(Q55) |
| 대검 | `greatsword_brace_upswing`(+fx `_ember`·`greatsword_brace_absorb`) | 버티기 올려베기 | 기본기 — 가드 중 좌클릭(맞아도 안 끊김, 울분 소모 시 강화) | **피해는 그대로 받음(맞은 피해는 울분으로 쌓임), 버티기 0.27초 고정**(Q54) |
| 대검 | `greatsword_leap_slam`(+fx `_land`) | 공중제비 도약 찍기 | 기본기 — 차지 중 스페이스(차지 단계 유지) | 공중 무적 없음, 착지 링 0.6R, 벽에 막히면 나선 fx 생략, 공중제비 칸(몸이 무기 오버레이에 그려짐) 색 예외 허용(Q55) |
| 대검 | `greatsword_guard_rush` | 막다가 떼면 돌진 | 기본기 — 퍼펙트 가드 직후 우클릭을 떼면 밀쳐내기 대신 돌진 | 적을 밀고 감, 돌진 56 월드 px(Q55) |
| 단검 | `dagger_backstab` | 등 뒤 치명 찌르기 | 기본기 — 그림자 걸음 직후 좌클릭(기존 확정 치명을 전용 동작으로) | 560ms, 전용 섬광만 — 공용 치명 fx 를 겹치지 않음(Q55) |
| 단검 | `dagger_flurry`(+fx `_heat2`·`_heat3`) | 고속 난타 | 기본기 — 좌클릭 홀드(과열 빠르게 상승) | 과열 3단(경계 40·80%), 초당 약 11타(Q55) |
| 활 | `bow_arrow_rain`(+fx `bow_arrow_rain_rise`·`_fall`·`_mark`) | 화살비 | 기본기 — 우클릭으로 당긴 채 좌클릭, 하늘로 3발, 커서 원 범위 낙하, 탄창 3 소모 | **3발 연속 발사(640ms), 떨어지는 자리마다 작은 판정 — 원 안 무작위 9곳, 40ms 간격**(Q52). 예고 원 m(32 월드 px)·좌클릭 순간 표시, 낙하 화살 12° 고정 + 좌우 뒤집기(Q55) |

- 갈래로 열리는 수단(칼 회전 베기 = 거합 1단·가드 불가 내려베기 = 발도술 1단, 단검 부채꼴 투척 = 질풍 1단·그림자 분신 교차 베기 = 쌍격 1단, 활 속사 연사 = 속사 갈래·관통 화살 = 저격 갈래)의 시트 키는 미정. 키아트(참고 그림)는 `parts/art/work/gemini/weapon_moves/sheet_<weapon>.png`·`list_<weapon>.md`(Q39 확정).

### 18.7 칼 새 기본기 (Q21·Q40·Q48·Q53·Q55)
- 몸 96×144·피벗 (48,138), 무기 192×192·피벗 (96,186)·`playerFrameOffset (48,48)`, 4행 down·up·left·right. fx `dirTransform: "drawn4"`(§18.1 행 규약). 판정 반경 R = 38 월드 px(152 도트, §18.2).

| 동작 (몸·무기 같은 이름) | 프레임 | frameDurationsMs | total / hitAt / activeEndAt / cancelAt | impactFrame (hitFrames) | 판정 참고 | 이동 (월드) | fx 틀 · 피벗 · 생성 · fx impactFrame |
|---|---|---|---|---|---|---|---|
| `katana_counter` 간파 반격 | 8 | 30, 40, 40, 30, 40, 120, 60, 60 | 420 / 110 / 140 / 300 | 3 ([3]) | `arc` −80°→+50°(130°) ×1.1, 내반경 0 | 비켜섬 6 [1,2] 30ms~ · 내딛기 6 [3,4] 110ms~ | 344×368 · (171,251) · `spawnAtMs` 80 · 1 |
| `katana_iai` 대치 일격 | 15 | 50, 60, 80, 120, 120, 120, 120, 30, 30, 40, 160, 70, 60, 90, 50 | 1200 / 700 / 770 / 1150 (유지 루프 1회 기준) | 8 ([8,9]) | `rect` `fromPx 22.8`·`lengthPx 231`·`widthPx 273.6`(0.15R~1.52R, 폭 1.8R) | 내딛기 16 [7,8,9] | 504×504 · (249,291) · 뗀 순간 · 1 |

- **`katana_counter`**: `phases` catch [0] → slip [1] → cock [2] → cut [3,4] → zanshin [5,6] → recover [7]. `startsFrom` = `katana_special` 패링 창 f3~f4(받은 자세), `endsWith` = 뽑아 든 낮은 겨눔(`katana_carry_drawn_idle`), `nextMove` = `katana_rise`(이어서 좌클릭 시 1타).
  - `sidestepPx {world 6, dots 24, frames [1,2], startMs 30, side: "anatomicalLeft"}` — 조준 방향의 해부 왼쪽(화면 반시계 90°)으로 반 발 비켜섬. `stepPx` 6 [3,4] 은 방향키를 누를 때만.
  - fx `katana_counter`: 6프레임 `[30, 20, 30, 70, 80, 90]`, `anchor: player_pivot`, `glowFrames [1,2]` — 1·2타보다 가늘고 짧은 붓 한 획(`drawnArc` 반경 167.2 도트).
- **`katana_iai`**: `phases` enter [0,1,2] → hold [3~6] → release [7~14](draw 7 · strike 8,9 · zanshin 10 · chiburi 11 · noto 12,13 · recover 14). 시트 `loop: false`.
  - 유지: `holdFrames` = `loopFrames` [3,4,5,6](`loopRange [3,6]`, `holdFrame 3`) — 좌클릭을 누르는 동안 시스템이 반복.
  - 뗌: **`releaseFrame 7`** — 떼는 순간 f7 로 건너뛰어 끝까지. 들어감(f0~f2) 중에 떼도 f7 로 바로(최소 유지 없음 — Q53). `releaseTimingMs {hitAfterRelease 30, activeEndAfterRelease 100, clickAfterRelease 390, totalAfterRelease 530}` — 판정·딸깍·끝은 **뗀 시각 기준**으로 계산(`timingMs` 는 유지 루프 1회 = 480ms 기준 시트 시각).
  - **`clickFrame 13`** = 납도 딸깍(선 터짐). `burst {atFrame 13, afterReleaseMs 390}` — **연출만, 추가 피해 없음**(Q55).
  - `startsFrom` = `katana_carry_idle`(F 로 넣은 상태), `endsWith` = `katana_carry_idle`(칼집에 넣은 채, Q55), `nextMove` = `katana_rise`(칼집 상태 1타 = 뽑기 후 베기 — 넣기 첫 타 치명).
  - **`koiguchiAnchors`** = 프레임별 칼집 입구(몸 시트 도트, 15프레임 모두 값). 무기 시트 좌표 = + `playerFrameOffset (48,48)`.
  - fx `katana_iai`: 11프레임 `[30, 30, 40, 80, 80, 70, 60, 60, 70, 80, 90]`, **`anchor: "release_pivot"`**(뗀 순간의 주인공 발에 고정, 따라가지 않음), `spawn: "release"`·`spawnAtReleaseMs 0`(JSON `spawnAtMs 670` 은 루프 1회 기준), `impactFrame 1`, `glowFrames [1,2]`, `burstFrame 7`(`burstAtLineMs 390` = 몸 `clickFrame`), `depth: "below_player"`. JSON `burstNote` 의 'glowFrames 에 7 추가 가능'은 쓰지 않음(Q55).
  - fx `katana_iai_ready`: 48×56, 피벗 (21,8), 5프레임 `[30, 40, 50, 60, 70]`, 1행 `any`, `anchor: "koiguchi"`, `depth: "above"`, 백열 없음. JSON: 유지 `readyAfterHoldMs` 500(임시)에 1회(`spawn: "hold_ready"`). **Q53(언제 떼도 같은 일격)에 따라 JSON `readyNote` 의 '완성 일격(치명 등)'은 쓰지 않는다** — ~~반짝임을 연출로만 남길지는 미정.~~ → **연출만 남김, 위력 변화 없음(56라운드 Q60).**

### 18.8 대검 새 기본기 (Q22·Q40·Q54·Q55)
- 몸 96×144·피벗 (48,138), 8행 `directionRows`·`drawn8`(§18.3). **무기 틀 280×296·피벗 (139,206)·`playerFrameOffset (91,68)`** — 새 4동작 합집합 틀(결정 Q55: 별도 틀). §18.3 연격 틀(240×280·(117,207)·(69,69))과 다르므로 JSON `frameWidth/frameHeight`·`pivot`·`playerFrameOffset` 을 읽는다. 무게 필드(`frameRoles`·`holdFrames`·`dragFrames`·`dragStepPx`·`stepPx`)는 §18.3 규칙.

| 동작 | 프레임 | frameDurationsMs | total / hitAt / activeEndAt / cancelAt | impactFrame (hitFrames) | holdFrames / dragFrames | 이동 (월드) | 판정 참고 |
|---|---|---|---|---|---|---|---|
| `greatsword_tackle` 어깨 태클 | 9 | 60, 90, 40, 40, 40, 70, 90, 90, 100 | 620 / 190 / 270 / 430 | 3 ([3,4]) | [1] / [6] | `dashPx` 40 [2,3,4] 150~270ms easeOut · 끌림 6 (340ms~) | `rect` 앞 0~0.6R·폭 0.8R, `travelsWithPlayer` |
| `greatsword_brace_upswing` 버티기 올려베기 | 11 | 40, 70, 100, 100, 60, 40, 50, 80, 100, 90, 100 | 830 / 370 / 460 / 640 | 5 ([5,6]) | [] / [7,8] | `stepPx` 6 [4,5] 310ms~ | `wedge` 50° ×1.2 + `impactCircle` 중심 0.9R·반경 0.3R, `launch` |
| `greatsword_leap_slam` 공중제비 도약 찍기 | 13 | 40, 80, 50, 50, 50, 50, 50, 40, 60, 110, 120, 100, 110 | 910 / 410 / 470 / — | 8 ([8]) | [0] / [9,10] | `leapPx` 48 [2~7] 120~410ms linear | `wedge` 40° ×1.3 / 1.5 / 1.8(차지 단계) + 쐐기 끝 `impactCircle` 0.45R + `landingRing` 0.6R |
| `greatsword_guard_rush` 막다가 떼면 돌진 | 9 | 40, 50, 40, 40, 40, 60, 90, 90, 100 | 550 / 130 / 270 / 360 | 3 ([3,4,5]) | [] / [6] | `dashPx` 56 [2,3,4,5] 90~270ms easeOut · 끌림 6 (270ms~) | `rect` 앞 0~0.75R·폭 0.9R, `travelsWithPlayer`·`carry` |

- **`greatsword_tackle`**: `startsFrom` = 대쉬 중 좌클릭(`greatsword_dashslash` 대신), `endsWith` = `greatsword_carry_drawn_idle`. `dashPx {world 40, dots 160, frames [2,3,4], startMs 150, endMs 270, easing easeOut, stopsAtWall}` — 벽·큰 적에 막히면 멈춤. 판정은 돌진 동안 몸과 함께 이동, 적마다 1회, **적을 밀고 감**(Q55).
- **`greatsword_brace_upswing`**: `startsFrom` = 가드 자세(`greatsword_special`) 중 좌클릭, `endsWith` = LINK_C, `nextMove` = `greatsword_cleave` | `greatsword_sweep_cw`.
  - **`superArmorFrames [0~6]`·`superArmorMs [0,460]`** — 이 구간에 맞아도 동작이 끊기지 않음. **피해는 그대로 받고 울분으로 쌓임(결정 Q54)**. 맞을 때마다 fx `greatsword_brace_absorb` 1회.
  - `braceFrames [1,2,3]`(40~310ms = 270ms) — **버티기 0.27초 고정(결정 Q54)**.
  - `rageVariant`: 울분 소모 시 판정 ×1.5·60°, fx 를 `greatsword_brace_upswing_ember` 로(몸·무기 그림은 같음).
- **`greatsword_leap_slam`**: `startsFrom` = `greatsword_charge` 루프 f3~f6 중 스페이스(f0 = 루프 f3 자세), cancel 없음, `endsWith` = `greatsword_carry_drawn_idle`.
  - **차지 단계 유지(`chargeStageKept`)**: 뛰기 직전 차지 단계로 착지 쐐기(`hitShape.lengthPxByStage [265.2, 306.0, 367.2]`)와 균열(`groundCrack.rowByStage [m, m, l]`, 착지 impactFrame 시작에 쐐기 끝점)을 고른다.
  - **`leapPx {world 48, dots 192, frames [2~7], startMs 120, endMs 410, easing linear, stopsAtWall}`** — 벽에 막히면 그 자리에 착지. `airborneFrames [2~7]`, `landAtMs 410`. **공중 무적 없음(결정 Q55)**.
  - **`airOffsetPx.byFrame [0, 0, 18, 58, 76, 64, 34, 12, 0, 0, 0, 0, 0]`**(도트, 위 +) — 시스템이 몸·무기(오버레이 포함) 시트를 이만큼 위로 올려 그린다. 그림자·피벗·판정 원점은 바닥, 프레임 사이 보간 가능.
  - **`flipFrames [3,4,5]`**(`flipAngles` 90° / 180° / 270°)·**`bodyInOverlayFrames [3,4,5]`** — 이 칸은 몸 시트 칸이 비어 있고 몸이 무기 오버레이 안에 함께 그려져 있다(회전 그림이 몸 틀보다 큼). 몸·무기 두 시트를 늘 겹쳐 그리면 맞는다. 이 칸의 몸 색은 무기 색 예산 예외(결정 Q55). `flipRender` 는 행별 회전 원본·각도·중심(제작 기록).
- **`greatsword_guard_rush`**: `startsFrom` = 퍼펙트 가드 직후 우클릭 뗌(밀쳐내기 `greatsword_special` 대신), `endsWith` = `greatsword_carry_drawn_idle`. `dashPx {world 56, dots 224, frames [2,3,4,5], startMs 90, endMs 270, easing easeOut, stopsAtWall}`. 판정 `carry: true` — **적을 앞으로 밀고 감**(크게 튕기지 않음, Q5·Q55), 적마다 1회, f5 퍼 올림에서 놓음.
- **대검 새 기본기 fx**(모두 `brushStroke`, 8행 `drawn8` 은 몸 행 번호 그대로):

| fx | 틀 | 피벗 | 프레임 · ms | 생성 (fx impactFrame) | anchor · 깊이 | 행 |
|---|---|---|---|---|---|---|
| `greatsword_tackle` | 296×296 | (148,230) | 6 · 40, 40, 50, 60, 70, 80 | **첫 접촉 순간**(0) — 결정 Q55(JSON `spawnAlt`), 빗나가면 생략. JSON `spawnAtMs 190` 은 몸 hitAt | `player_pivot`, `followPlayer` | 8행 |
| `greatsword_brace_upswing` | 360×424 | (181,265) | 6 · 40, 40, 50, 60, 70, 80 | 330 (1) | `player_pivot` | 8행 · `variant: "base"` |
| `greatsword_brace_upswing_ember` | 416×496 | (210,304) | 6 · 40, 40, 50, 60, 70, 80 | 330 (1) | `player_pivot` | 8행 · `variant: "rage"`(울분 소모) |
| `greatsword_brace_absorb` | 80×88 | (42,81) | 5 · 30, 40, 50, 60, 70 | `superArmorFrames` 중 피격마다 1회 | `player_pivot`, `followPlayer`, above | 1행 `any` |
| `greatsword_leap_slam`(나선) | 592×664 | (292,398) | 8 · 50, 50, 50, 50, 40, 60, 70, 80 | 170 (—) | **`leap_start_pivot`**, above · `bakedTravelDots 192`·`airBaked` | 8행 |
| `greatsword_leap_slam_land` | 568×576 | (284,324) | 5 · 40, 50, 60, 70, 90 | 370 (1) = 착지 410ms | `player_pivot`, `followPlayer` | 8행 |
| `greatsword_guard_rush`(땅 홈) | 696×672 | (345,338) | 8 · 40, 40, 40, 60, 90, 90, 100, 120 | 90 (—) | **`dash_start_pivot`**, `below_player` · `bakedTravelDots 224` | 8행 |

  - 나선(`greatsword_leap_slam`)은 도약 48 월드 px 기준으로 이동이 그려져 있음 — **벽에 막혀 짧게 뛰면 생략**(결정 Q55). `glowFrames` 없음.
  - 땅 홈(`greatsword_guard_rush`)은 돌진 56 월드 px(224 도트) 기준으로 그려져 있음.
  - `greatsword_leap_slam_land` 와 함께 `greatsword_ground_crack`(위 `rowByStage`).

### 18.9 단검·활 새 기본기 (Q23·Q24·Q40~Q43·Q52·Q55)
- 단검: 몸 96×144·피벗 (48,138), 무기 192×192·피벗 (96,186)·`playerFrameOffset (48,48)`, 4행, 무기 그림 1.3배(`scale56`, 역수 `reverseGrip`).

| 동작 | 프레임 | frameDurationsMs | total / hitAt / activeEndAt / cancelAt | impactFrame (hitFrames) | 판정 참고 `thrust` (도트) | fx 틀 · 피벗 · spawnAtMs · fx impactFrame |
|---|---|---|---|---|---|---|
| `dagger_backstab` 등 뒤 치명 찌르기 | 10 | 40, 50, 70, 30, 50, 60, 70, 50, 60, 80 | 560 / 190 / 240 / 420 | 4 ([4]) | `lengthPx 150`·`widthPx 56`·`fromPx 24`·0° | 200×152 · (101,137) · 160 · 1 |
| `dagger_flurry` 고속 난타 | 10 | 40, 40, 45, 45, 45, 45, 45, 45, 60, 80 | 490 / 80 / 305 / — (`hitsAt` 80·170·260, `loopMs 270`) | 2 ([2,4,6]) | `lengthPx 144`·`widthPx 48`·`fromPx 16`·0° | 336×344 · (168,208) · 0 · 2 |

- **`dagger_backstab`**: `startsFrom` = `dagger_special` 끝 프레임(f8 확정 치명 자세), `endsWith` = READY_DG → `dagger_carry_idle`, `cancelFromFrame 8`. 판정은 기본 3타(168)보다 짧고 넓은 정면 직사각(바로 앞 적의 등).
  - fx `dagger_backstab`: 6프레임 `[30, 50, 60, 70, 60, 80]`, `anchor: player_pivot`, `holdFrame 1`, `hitstopHint 90ms`, `shakeHint` 3px·110ms, `flash`(화면 가장자리 호박 60ms, 선택 — 시스템). **`critAnchors`**(치명 섬광 중심 = 칼날 70% 박힌 자리, 몸 시트 도트): down (47.7,90.2)·up (48.3,60.9)·left (6.2,75.2)·right (89.8,75.4), 몸 피벗 기준 = (x−48, y−138).
  - **결정(Q55): 전용 섬광만 — 공용 치명 fx(`hit_dagger_heavy`·`crit_burst`)를 겹치지 않는다**(JSON `critAnchorNote` 의 '겹친다면' 경우는 쓰지 않음).
- **`dagger_flurry`**: 좌클릭 홀드 — **`startFrames [0,1]`** 1회 → 홀드 동안 **`loopFrames [2~7]`**(`loopRange [2,7]`, f7 → f2) 반복 → 떼면 지금 찌르기의 당김 프레임까지 마치고 **`endFrames [8,9]`**. 시트 `loop: false`(시스템이 반복). `stabAngles {2: −10°, 4: +12°, 6: 0°}` 는 그림 각(판정은 0° 하나).
  - fx: 몸과 같은 10프레임·같은 ms, 몸 f0 시작에 같이 시작하고 같은 프레임 번호를 같은 시각에 표시(`spawnAtMs 0`).
  - **과열 단계 `heatRule`**: 과열 0~39% = `dagger_flurry`, 40~79% = `dagger_flurry_heat2`(360×368·(180,220)), 80~100% = `dagger_flurry_heat3`(376×376·(185,225)). 단계가 바뀌면 같은 프레임 번호로 fx 시트만 바꿔 이어 재생(`heatVariants`·`heatLevel`·`heatOf`, 세 시트 프레임·ms 동일). 몸·무기 그림은 같음. **결정(Q55): 과열 3단 경계 40·80%, 초당 약 11타.** 100% 자동 폭발은 §18.10 `dagger_overheat_burst`.
- **활 `bow_arrow_rain`**(몸·무기): 12프레임 `[50, 60, 40, 40, 40, 40, 40, 40, 40, 70, 80, 100]`, 4행, 무기 192×192·피벗 (96,186)·offset (48,48). `timingMs {total 640, releasesAt [110, 230, 350], cancelAt 390}`, `cancelFromFrame 9`.
  - `phases` raise [0,1] → volley [2~8] → recover [9,10,11]. **`releaseFrames [2,5,8]`**(`arrowCount 3`) — 각 프레임 시작에 화살 1발 생성(하늘로). renock 프레임은 시위 위에서 재가 뭉쳐 새 화살이 맺힘(몸에서 뽑지 않음, 탄창 3 소모는 시스템).
  - `startsFrom` = `bow_draw_hold` 가득(f5) 또는 유지 루프(f6~f9) 중 좌클릭, `endsWith` = 우클릭을 계속 누르고 있으면 `bow_draw_hold`, 아니면 `bow_carry_idle`. `skyAngleDeg`(프레임별 하늘 각) 참고.
  - **`arrowSpawnAnchors`**(무기 JSON, 무기 시트 좌표, `releaseFrames`·f9 만 값): `bow_arrow_rain_rise` 의 피벗.
- **화살비 fx**:

| fx | 틀 | 피벗 | 프레임 · ms | 행 | anchor · 깊이 | 생성 |
|---|---|---|---|---|---|---|
| `bow_arrow_rain_rise` | 200×184 | (105,179) | 4 · 40, 40, 40, 50 | 4행(방향), `rotate: false` | **`arrow_spawn`**, above | 몸 `releaseFrames` 시작마다 1회(110·230·350ms). 솟는 이동은 시트 안에 그려짐(`screenAngleDeg`·`riseDistancePx`) |
| `bow_arrow_rain_mark` | 440×440 | (219,219) | 10 · 50, 60, 90, 90, 90, 90, 60, 60, 70, 90 | 3행 = 크기 s·m·l(`rowsAre: "sizes"`) | `hitbox_center`(커서 원 중심), below | 좌클릭 순간 appear [0,1] 1회 → 첫 화살이 떨어질 때까지 wait `loopRange [2,5]` → 낙하 동안 rain [6,7](마지막 칸 유지 가능) → out [8,9] |
| `bow_arrow_rain_fall` | 72×232 | (49,219) | 7 · 40, 40, 40, 40, 60, 80, 100 | 1행 `any`, `rotate: false`, `flipX: "allowed"` | `hitbox_center`(낙하점), above | 낙하점마다 1회, `impactFrame 3`(시트 120ms) 시작 = 그 점의 판정 |

  - 예고 원 `sizeInfo`: s 96 도트(24 월드)·m 128(32)·l 176(44). `scaleRule` = 판정 반경에 가장 가까운 행을 고르고 scale = R / `radiusPx`(0.85~1.2 권장). **결정(Q55): m(32 월드 px), 좌클릭 순간 표시.**
  - 낙하 화살: `fallHeightPx 150`, `fallSlantDeg 12`, `flipX` 로 좌우 섞기. **결정(Q52): 떨어지는 자리마다 작은 판정 — 원 안 무작위 9곳, 40ms 간격**(JSON `spawnNote` 의 '9~12곳·30~50ms·큰 원 1회 판정 선택'은 이 결정으로 대체). **결정(Q55): 12° 고정 + 좌우 뒤집기.** 작은 판정 반경·첫 낙하 시각은 시스템 데이터.

### 18.10 자원·상태 표시 (Q7·Q8·Q13~Q20·Q48·Q51·Q55)
- **검기·울분 오버레이(무기 위 덧그림, Q14·Q15)**:
  - 이름: `weapons/v3/<칼 무기 시트>_ki1`~`_ki3`(검기 1~3단), `weapons/v3/<대검 무기 시트>_grudge1`~`_grudge3`(울분 단계).
  - 그리는 법(`drawRule`): 대상 무기 시트(`overlayOf`)를 그린 **바로 위**(`depth: "above_weapon"`)에 **같은 프레임 번호(row*frames+col — 57라운드 아틀라스는 row*`atlas.grid.columns`+col, §19.2)·같은 시각·같은 피벗**(주인공 피벗 + `playerFrameOffset`)으로 겹친다. 틀·피벗·offset·프레임 수·`frameDurationsMs`·행 = 대상 시트와 같음(`bodySheet`·`level` 표시). 단계가 바뀌면 같은 프레임 번호로 오버레이만 바꿔 낀다. **0단이거나 대상 시트의 오버레이 파일이 없으면 생략**.
  - 3단 `glowFrames` = 대상 시트의 판정 프레임(검기 3단 판정 날선 흰 픽셀 허용, Q55). 칼집 안(칼끝 null) 칸·칼집 휴대 시트는 칼집 금을 단계 색으로 달굼(1단 연기 / 2·3단 작은 불, `sheathNote`).
  - **결정(Q55)**: 오버레이 시트 방식, 새 칼·대검 동작에도 적용. 울분 단계 = 게이지 구간 1~33 / 34~66 / 67~100%(값은 시스템 데이터) — 차지 내려찍기로 전부 소모하면 오버레이 없음.
  - `greatsword_leap_slam_grudge1~3` 도 `bodyInOverlayFrames [3,4,5]`(§18.8) · 위로 올려 그리기(`airOffsetPx`)는 무기와 같이.
  - 대상 시트(07d3c00 + 5f7dae8 + 56라운드 작업 G):

| 자원 | 대상 무기 시트 (`weapons/v3/`, 각 `_ki1~3` / `_grudge1~3`) |
|---|---|
| 검기 (16시트 × 3) | `katana_carry_idle`·`katana_carry_walk`·`katana_carry_run`·`katana_carry_dash`, `katana_carry_drawn_idle`·`katana_carry_drawn_walk`·`katana_carry_drawn_run`·`katana_carry_drawn_dash`, `katana_rise`·`katana_fall`·`katana_issen`, `katana_counter`·`katana_iai`, `katana_draw`·`katana_sheathe`·`katana_special` |
| 울분 (21시트 × 3) | `greatsword_special`·`greatsword_draw`·`greatsword_sheathe`(Q62 추가), `greatsword_carry_idle`·`greatsword_carry_walk`·`greatsword_carry_run`·`greatsword_carry_dash`, `greatsword_carry_drawn_idle`·`greatsword_carry_drawn_walk`·`greatsword_carry_drawn_run`·`greatsword_carry_drawn_dash`, `greatsword_sweep_cw`·`greatsword_cleave`·`greatsword_sweep_ccw`, `greatsword_charge`·`greatsword_charge_slam`·`greatsword_charge_plunge`, `greatsword_tackle`·`greatsword_brace_upswing`·`greatsword_leap_slam`·`greatsword_guard_rush` |

  - 오버레이가 없는 무기 시트(재생 중 생략): 칼 `katana_crescent`(보관)·`katana_combo1~3`·`katana_carry_groggy`, 대검 `greatsword_dashslash`(태클로 교체)·`greatsword_slam`·`greatsword_combo1~3`·`greatsword_carry_groggy`.
- **낙인 표식 `fx/v3/dagger_brand_mark`(Q16)**: 44×40, 피벗 (17,34), 6프레임 `[40, 70, 120, 120, 120, 120]`, **행 = 스택 `"1"`~`"5"`**(`rowsAre: "stacks"`, 방향으로 고르지 않음·회전 없음), **`anchor: "enemy_head"`**, `followTarget`, `depth: "above"`, `glowFrames [0]`. 스택이 오를 때마다 그 행의 stamp [0,1] 1회 → `loopRange [2,5]` 반복, 스택이 그대로면 루프만. 기폭·과열 폭발·대상 사망 때 지움. **결정(Q55): 셈 획은 적 머리 위.**
- **낙인 기폭 `fx/v3/dagger_brand_burst`(Q16·Q18)**: 152×136, 피벗 (76,68), 8프레임 `[40, 40, 50, 60, 70, 80, 100, 120]`, **행 = 크기 s·m·l**(`rowsAre: "sizes"`) — 스택 1~2 = s(반경 34 도트)·3~4 = m(46)·5 = l(60)(**결정 Q55: 스택 → s/m/l**). `anchor: "hitbox_center"`, `impactFrame 1`, `glowFrames [1,2]`, `shakeHint` s 2px·80ms / m 3·100 / l 5·130, `light`. 생성: 그림자 걸음으로 낙인 적 등 뒤에 선 순간 1회 + 과열 100% 일괄 폭발 때 낙인 적마다 1회(가까운 적부터 40ms 간격 권장).
- **과열 폭발 `fx/v3/dagger_overheat_burst`(Q19 · Q51 전용 fx)**: 224×144, 피벗 (110,78), 8프레임 `[40, 40, 50, 60, 70, 80, 90, 110]`, 1행 `any`, `anchor: player_pivot`, `impactFrame 0`, `radiusPx 92`, `glowFrames [0,1]`, `light`, `shakeHint` 4px·140ms. 과열 100% 순간 1회 — 주변 낙인 적의 기폭은 이 시트 f1 시작부터 가까운 순서로 `dagger_brand_burst`.
  - 식힘 `fx/v3/dagger_overheat_cool`: 72×128, 피벗 (35,117), 6프레임 ×110ms 루프, `anchor: player_pivot`·`followTarget`. 식는 동안(잠깐 느려짐) 루프, 끝나면 마지막 칸에서 끔(반투명 금지).
- **퍼펙트 가드·패링 `fx/v3/guard_perfect_fx`(Q7·Q8·Q48)**: 88×104, 피벗 (44,52), 7프레임 `[30, 40, 50, 60, 70, 80, 90]`, **행 = 종류 `guard`·`parry`**(`rowsAre: "kinds"`) — guard = 퍼펙트 가드(피해 0, 튕기지 않음), parry = 패링 성공. **`anchor: "guard_contact"`**, `rotate: true`·`drawnFacing: "right"`(그림 오른쪽 = 공격이 들어온 쪽, 주인공 → 공격자·투사체 각도)·`flipY: "allowed"`, `depth: "above"`, `impactFrame 0`, `glowFrames [0,1]`(f0 틈 흰 픽셀 허용, Q55), `holdFrame 1`, `light`, `shakeHint` guard 2px·70ms / parry 3·90.
  - **결정(Q55·Q62): 퍼펙트 가드·패링 순간에만 기존 `parry_flash`·`guard_wave`(§16)를 대체**한다. 일반 가드의 `guard_wave` 는 유지(Q62)(JSON `pairsWith` 의 '함께 또는 대신'은 이 결정으로 정리). 문구 'PERFECT GUARD'·'PARRY'(Q8)는 UI·시스템 텍스트.
  - 판정 창: 가드를 누른 직후 0.15초 안 피격 — 칼 패링·대검 퍼펙트 가드 공통(Q7·Q48).
- **그로기 `player/v3/player_groggy`(Q7·Q13·Q19)**: 96×144, 피벗 (48,138), 10프레임 ×150ms = 1500ms 루프(한 주기 = 그로기 1.5초), 4행. **결정(Q55): 칼·대검이 같은 몸을 공유(왼손 빈 몸), 루프만(전환 프레임 없음), 그로기 중 가드 몸은 현행** — 가드를 누르면 현행 가드 몸으로 바꾸고, 떼면 이 시트의 같은 시각 프레임으로 돌아온다(권장). `phases` swayRight [0~4]·swayLeft [5~9], `eyeOffFrames [6,7]`.
  - 휴대 무기 `carryOverlay`(같은 프레임 번호로 겹침): `weapons/v3/katana_carry_groggy`(192×192·피벗 (96,186)·offset (48,48), 왼허리 칼집, `sheathMouthAnchors`) / `weapons/v3/greatsword_carry_groggy`(240×272·피벗 (119,209)·offset (71,71), 등 가죽끈, 4행).
  - 소용돌이 `fx/v3/player_groggy_swirl`: 40×20, 피벗 (20,10), 6프레임 ×125ms 루프(1.5초에 2바퀴), 1행 `any`, `anchor: "player_head_top"`, `followTarget`, `depth: "above"`. 피벗 = 몸 **`headTopAnchors[방향][프레임]`**(머리 꼭대기, 몸 시트 도트) + **`swirlOffsetY −14`**(도트, 위로 14). 그로기가 끝나면 끔.
- 약한 화살 `bow_arrow_weak` 은 §18.5.
- 흰 픽셀 허용처(결정 Q55): 검기 3단 판정 날선 · 낙인 새 획 · 퍼펙트 가드 f0 틈 · 기폭 핵. 그 밖은 기존 규칙(백열은 판정 순간 획 머리 몇 도트만).

### 18.11 56라운드 앵커 이름
- `anchor` 값(fx 를 어디에 붙이는가):

| anchor | 종류 | 뜻 | 쓰는 시트 |
|---|---|---|---|
| `player_pivot` | 따라감(기존) | 주인공 발(몸 피벗). `followPlayer: true` 면 매 프레임 따라감 | 대부분의 몸 기준 fx |
| `dash_start_pivot` | world 고정 | 돌진을 시작한 순간의 주인공 발 | `katana_issen_line_t1~t4`(`_solo`), `greatsword_guard_rush` fx |
| `issen_shadow_path` | 이동 | `travelFrames` 동안 출발 피벗 → 도착 피벗(실제로 멈춘 자리) 선형 이동, 이후 도착 피벗 고정 | `katana_issen_shadow` |
| `release_pivot` | world 고정 | 좌클릭을 뗀 순간(몸 `releaseFrame` 시작)의 주인공 발 | `katana_iai` fx |
| `leap_start_pivot` | world 고정 | 도약 출발(`leapPx.startMs`) 순간의 주인공 발 | `greatsword_leap_slam` fx(나선) |
| `koiguchi` | 몸 앵커 | 칼집 입구 — 몸 `koiguchiAnchors[방향][프레임]` | `katana_iai_ready` |
| `arrow_spawn` | 무기 앵커 | 화살 생성 점 — 무기 `arrowSpawnAnchors[방향][프레임]` | `bow_arrow_rain_rise` |
| `projectile` | 투사체(기존) | 투사체 위치·진행 각도 | `bow_perfect_release`, `bow_arrow_weak` |
| `plant_point` | 몸 앵커 | 칼이 바닥에 꽂힌 점 — 몸 `plantAnchors`(§18.3) | `greatsword_plunge_wave`(꽂아내리기 `greatsword_ground_crack` 도 이 점) |
| `player_head_top` | 몸 앵커 | 머리 꼭대기 — 몸 `headTopAnchors` + `swirlOffsetY` | `player_groggy_swirl` |
| `enemy_head` | 적 | 적 머리 위(적을 따라감, `followTarget`) | `dagger_brand_mark` |
| `hitbox_center` | 판정(기존 §16) | 판정 중심 — 적 히트박스 중심 / 내려찍은 자리 / 커서 원 중심 / 낙하점 | `hit_*`, `greatsword_ground_crack`, `dagger_brand_burst`, `bow_arrow_rain_mark`·`bow_arrow_rain_fall` |
| `guard_contact` | 판정 | 가드 맞닿음 점(주인공과 들어온 공격 사이), 각도 = 주인공 → 공격자·투사체 | `guard_perfect_fx` |

- 앵커 좌표 필드(프레임별 점 — 값이 없는 프레임은 `null`):

| 필드 | 들어 있는 JSON | 좌표계 | 값 있는 프레임 |
|---|---|---|---|
| `plantAnchors` | 몸 `player_greatsword_charge_plunge` | 몸 시트 도트 | `plantFrames [4,5,6,7]` |
| `arrowSpawnAnchors` | 무기 `bow_release`(§18.5) · 무기 `bow_arrow_rain` | 무기 시트 좌표(몸 좌표 = − (48,48)) | `bow_release` f0 · `bow_arrow_rain` f2·f5·f8·f9 |
| `koiguchiAnchors` | 몸·무기 `katana_iai` | 몸 시트 도트(무기 좌표 = + (48,48)) | 15프레임 모두 |
| `headTopAnchors` | 몸 `player_groggy` | 몸 시트 도트 | 10프레임 모두 |
| `critAnchors` | fx `dagger_backstab` | 몸 시트 도트(방향당 1점) | — |
| `sheathMouthAnchors` | 무기 `katana_carry_groggy` | 몸 시트 도트 | 10프레임 모두 |

## 19. 57라운드 트림 아틀라스·외벽 WebP (저장 형식 변경)
- 근거: `decisions/2026-10-04-round-57-systems-review.md` Q16~Q19(고른 무기만 런 시작 때 로드 · 빈 공간을 잘라낸 아틀라스 · 외벽 WebP 손실 압축과 4096px 초과 분할), Q38(아틀라스 JSON 형식은 아트안으로 통일 — 정수 `frames` → `framesPerDirection`, `frames{}` hash, `atlas.grid.columns` / 프레임 여백 2px / 외벽 albedo q90·발광 무손실 / 반복 타일·리본 5종 트림 안 함 / assets 교체 + 원 격자 PNG·외벽 PNG 삭제 / 적·보스·구조물 v3 도 같은 변환), 점검 보고 `decisions/research-2026-10-04-optimization-audit.md` A1~A4. 산출: 아트 866d609(변환 도구·스테이징), 시스템 a5d89fc(아틀라스 로더 — 격자·아틀라스 양쪽 지원).
- **바뀌는 것은 저장 형식뿐이다.** §1~§18 의 크기(원 프레임 `frameWidth`×`frameHeight`)·피벗·앵커·프레임 수·`frameDurationsMs`·행 규약·추가 필드의 뜻은 그대로다.

### 19.1 적용 범위
| 대상 | 경로 | 형식 |
|---|---|---|
| 주인공 몸 | `sprites/player/v3/` | 트림 아틀라스 |
| 무기 (휴대·연격·오버레이 `_ki1~3`·`_grudge1~3` 포함) | `sprites/weapons/v3/` | 트림 아틀라스 |
| 이펙트 | `sprites/fx/v3/` | 트림 아틀라스 (아래 '트림 안 함' 제외) |
| 적 | `sprites/enemies/v3/` | 트림 아틀라스 (57 Q38 범위 확장) |
| 보스 | `sprites/bosses/v3/` | 트림 아틀라스 (57 Q38 범위 확장) |
| 구조물 | 구조물 v3 시트 | 트림 아틀라스 (57 Q38 범위 확장) |
| 월드 아이템(소모품 드롭) | `sprites/items/v3/` | 트림 아틀라스 (60라운드, 폴더 위치는 인터뷰 대기) |
| 외벽 테두리 | `tiles/border/<region>/` | WebP (§19.4) |
| 타일셋·소품 시트 (`tiles/**` 의 격자 타일셋) | §2·§9·§12·§14 | 격자 유지. 60라운드 B안부터 64도트 칸(`pixelScale 0.5`) 시트가 섞일 수 있음(§11) |

- **트림 안 함(`atlas.noTrim: true`)**: 반복 타일 계열 fx(`telegraph_line` 처럼 타일 주기로 이어 그리는 시트)와 칼끝 리본(`ribbon_ash`·`ribbon_ash_thin` 등) — **5종**(57 Q38). 이 시트도 아틀라스 JSON 형식은 같고 프레임 사각형만 원 프레임 크기 그대로다. 5종의 정확한 목록은 아트 변환 도구 설정이 기준이다.
- 무기 시트 로드 시점(Q16): 고른 무기의 시트만 런 시작 때 로드하고, 시험장 등에서 무기를 바꾸면 이전 무기 시트를 해제한다(Q38 시스템 — 시스템 처리, 시트 변경 없음).

### 19.2 아틀라스 JSON (`<이름>.json` + 페이지 PNG)
기존 시트 JSON 의 필드를 유지하고 아래만 바뀌거나 더해진다.

| 필드 | 형태 | 뜻 |
|---|---|---|
| `framesPerDirection` | number | **옛 정수 `frames`**(방향 한 행의 프레임 수). 이름만 바뀜 |
| `frameWidth`·`frameHeight` | number | 원 프레임(트림 전) 크기 — 그대로. = 각 프레임의 `sourceSize` |
| `frames` | object | **TexturePacker JSON Hash** 형식의 프레임 사전. 키 = `String(row * columns + column)`(`columns` = `atlas.grid.columns`), 값 = `{ frame{x,y,w,h}, rotated: false, trimmed, spriteSourceSize{x,y,w,h}, sourceSize{w,h} }` |
| `atlas.version` | `"atlas57-1"` | 아틀라스 형식 판 |
| `atlas.grid` | `{ columns, rows, frameWidth, frameHeight, frameCount }` | 원 격자 정보 — 열 수·행 수(방향 수)·원 프레임 크기·전체 프레임 수 |
| `atlas.padding` | `2` | 페이지 안 프레임 사이 여백(px) |
| `atlas.noTrim` | boolean | 트림하지 않은 시트(§19.1 '트림 안 함') |
| `atlas.emptyFrames` | 목록 | 완전히 빈 프레임 — 1×1 투명 사각형으로 저장, 키·번호는 유지 |
| `atlas.dedupedFrames` | 목록·사전 | 그림이 같은 프레임을 한 사각형으로 합친 기록 — 여러 키가 같은 `frame` 사각형을 가리킨다 |
| `atlas.pages` | number | 페이지 수 (1 = 단일 PNG) |
| `meta` | `{ image, size{w,h}, … }` | TexturePacker 메타. `meta.size` = 페이지 크기 |
| `image` | string \| `null` | 단일 페이지면 페이지 PNG. **4096px 를 넘어 나눈 시트는 `null` + `textures[]`** |
| `textures[]` | 배열 | **multiatlas**: 페이지마다 `{ image, size, frames }`. 키 규칙은 `frames` 와 같다 |

- **좌표 원칙**: `pivot` 과 §3~§18 의 모든 도트 좌표(앵커·`bladeTipAnchors`·`scarAnchor`·`plantAnchors`·`koiguchiAnchors`·`cupAnchors`·`arrowSpawnAnchors`·`headTopAnchors` 등)는 **원 프레임(`sourceSize`) 좌표**다. 트림 오프셋(`spriteSourceSize`)은 로더가 처리하므로 좌표를 다시 계산하지 않는다.
- **프레임 번호**: 애니메이션은 `String(row * atlas.grid.columns + column)` 키로 만든다. §1 `row * frames + column`, §18.10 오버레이 '같은 프레임 번호' 규칙도 이 번호로 읽는다(값은 같다 — 열 수가 같으므로).
- **빈 프레임**: 몸 칸이 비어 있는 `bodyInOverlayFrames`(§18.8) 같은 칸도 키를 지우지 않고 1×1 로 둔다 — 프레임 수·시각이 어긋나지 않게.
- 페이지 한 변 최대 **4096px**. 넘으면 multiatlas 로 나눈다.

### 19.3 로드 (시스템)
- §19.1 범위 시트는 아틀라스로 로드한다(`this.load.atlas` — `textures[]` 가 있으면 `this.load.multiatlas`). 애니메이션 키 규칙(`<이름>_<동작>_<방향>`)은 §1 그대로.
- 시스템 로더는 격자·아틀라스 양쪽을 읽는다(a5d89fc). 어느 쪽인지 고르는 기준(`atlas` 블록 유무 / `frames` 가 객체인지)은 시스템 구현을 따른다.
- Canvas 렌더러 폴백에서 트림 위치 1px 차는 허용한다(57 Q38 시스템).

### 19.4 외벽 테두리 WebP (`tiles/border/<region>/`)
- 그림 파일: `.png` → **`.webp`**. 그림(albedo) = **손실 WebP q90**, 알파 = **무손실**, 발광(`emissive`) = **무손실 WebP**. 옛 외벽 PNG 는 삭제(57 Q38).
- `border.json`(§13) 추가 키: **`imageFormat`**(그림 형식 표시, `"webp"`), 띠 한 변이 **4096px 를 넘으면 `pieces[]`** = `[{ image, emissive, x, y, width, height }]` — 한 띠를 여러 조각으로 나누고, 조각마다 그림·발광 파일과 띠 안 위치·크기를 적는다. 시스템은 조각을 그 위치에 이어 그린다. 그 밖의 §13 키(`width`·`height`·`baselineY`/`baselineX`·`repeat`·`lights[]`·`doors`·`sides` 등)의 뜻은 그대로.

### 19.5 새 시트 제작 규칙
- §19.1 범위의 **새 시트·고친 시트는 모두 atlas57 파이프라인**(아트 오프라인 Python 변환 도구, 866d609)을 거쳐 아틀라스로 내보낸다. 원 격자 PNG 는 `assets/` 에 두지 않는다(작업 원본 보관은 아트 파트 폴더).
- 새 외벽 그림도 §19.4 규칙(WebP·4096 분할)으로 내보낸다.
- 형식을 바꿀 때는 이 절부터 고친다(문서 머리말 규칙).
- (57 Q38) **`framesPerDirection` 은 `atlas.grid.columns` 와 같아야 한다** — 다르면 로더가 그 시트를 오류로 건너뛴다(플레이스홀더). Chromium 은 OGG 디코딩 버퍼가 `samples` 보다 8~25ms 길 수 있어 시스템이 `loopEndSample` 로 잘라 쓴다(음향 참고).

## 20. 58라운드 무기 피드백 2 시트 (58 Q1~Q11)
- 세부 규격(프레임 크기·피벗·anchor·타이밍)은 **각 시트 JSON 이 기준**이다. 저장 형식은 §19.
- 칼: `katana_thrust`(3타 찌르기, 무기·몸) + fx `katana_thrust_ki1~3`(검기 단계) + 무기 오버레이 `katana_thrust_ki1~3`(§18.10 검기 오버레이 규칙) / `katana_issen_dash`(일섬 = 대쉬 공격 전용).
- 대검: `greatsword_charge_swing`(차지 = 항상 휘둘러 내리찍기) + fx `greatsword_charge_crack_line_t1~t5`(내리찍은 지점부터 커서 쪽 3/4/5칸, 58 Q5) / 진짜 3/4 대각 리그로 다시 그린 대검 10시트(연격 240×296 피벗 (117,217), 새 동작 280×312 피벗 (139,218), 차지 휘두르기 248×288 피벗 (121,220)).
- 꽂아내리기 시트는 **보관만**(58 Q11, 로드하지 않음).
- 갈래 1단 수단(branch57): `katana_spin`, `katana_guardbreak`, `greatsword_shatter_crack_t1~5`, `greatsword_quake_ring`, `dagger_fan_throw`, `dagger_thrown`, `dagger_cross_clone`, `bow_rapid_loop`, `bow_arrow_pierce`.

## 21. 57라운드 빌드 축 시트 (fx·각성 오버레이·상태·저주)
- 경로: fx `assets/sprites/fx/v3/`, 각성 오버레이 `assets/sprites/weapons/v3/<무기 시트>_awaken`. 세부 규격·타이밍(`spawnAtMs` 또는 생성 규칙)·`glowFrames`·`frameRoles`·판정 제안값은 **각 JSON 이 기준**(판정 수치의 기준은 시스템 데이터).
- **1단 연격 변화**: `katana_fall_wide`, `status_stagger`, `greatsword_cleave_crack`, `dagger_combo3_double`, `dagger_gale_wind`, `aim_charge_quick`, `bow_snipe_full`.
- **2단 갈래 fx(16갈래)**: `katana_whirl_loop`·`katana_whirl_reflect` / `katana_moon_trail` / `katana_cleave_crack`·`katana_execute` / `katana_mirror_ki`·`katana_mirror_parry` / `greatsword_quake_fork` / `greatsword_echo_counter` / `greatsword_giant_ring`·`greatsword_charge_flash_lv4` / `greatsword_congest_aura`·`greatsword_congest_burst` / `dagger_frenzy_clone_in`·`_out` / `dagger_brand_bleed`·`dagger_brand_hop` / `dagger_stuck_blade` / `dagger_hotwind_trail`·`dagger_hotwind_burst` / `bow_arrow_split` / `bow_arrow_stuck`·`bow_arrow_recall` / `bow_deadeye_scope` / `bow_link_stack`·`bow_skypierce_line`.
- **최종 각성**: 시그니처 fx `katana_fullmoon`, `greatsword_landslide`(8방향, `drawn8` 행 순서), `dagger_hundred_ghosts`, `bow_meteor_arrow`. 무기 외형은 오버레이 60장(칼 20·대검 20·단검 11·활 9).
- **상태·세트**: `status_mark`, `status_burn`, `status_boil`, `set_stasis_wave`, `status_slowed`, `pool_liquor`, `pool_liquor_fire`, `status_drunk`, `drunk_sway`, `endure_last_stand`, `chain_bloodlust`, `set_flash`, `dual_trait_get`, `perfect_dodge`. 저주 표시 `curse_mark`(7행 = 저주 7종).
- **갈래 런 교체 규칙**: `katana_fall_wide`↔`katana_fall`, `dagger_combo3_double`↔`dagger_combo3`, `aim_charge_quick`↔`aim_charge`, `dagger_hotwind_burst`↔`dagger_overheat_burst`(같은 규격·1:1 교체).
- **각성 오버레이 규칙**: 검기·울분 오버레이와 같은 규칙(같은 프레임 번호·시각·피벗). 그리는 순서 무기 → `_awaken` → `_ki`/`_grudge`. 각성 런에서만.
  - **(60라운드 Q15~Q21 재디자인)** 각성 외형을 다시 만든다: 칼 = 월인(K-A), 대검 = 핏빛 거암검(G-A 바탕, 피가 균열에서 터짐), 단검 = 귀화(D-A), 활 = 혜성 날개(B-A). **각성 시트만 틀 확대**(칼·단검·활 256 안팎, 대검 320×336 안팎) — 프레임 번호·시각은 같고 틀·피벗은 각 JSON 이 기준(시스템이 원 무기 시트와의 피벗 차이를 보정). 각성 무기 색 상한 24. 각성 궤적은 기존 연격 fx 와 별개인 **각성 전용 fx**. 각성 순간 색 전환 ≈ 420ms(8×60ms), 각성 상태 순환 6~12프레임.
  - **(60라운드 제작 결과)** 각성 오버레이 JSON 에 `pivot`·`playerFrameOffset`·`weaponSheetPivot`(원 무기 피벗)·`pivotDelta` 가 있다. 각성 오버레이는 `pivot` 을 주인공 피벗에 맞춰 그린다(= 원 무기 피벗 + `pivotDelta`). 틀: 칼 192 → 264×264(Δ 36,32) / 단검·활 192 → 256×256(Δ 32,32) / 대검 가로 +80·세로 +64(Δ 40,32; 240×272 → 320×336, 240×296 → 320×360, 280×312 → 360×376, 248×288 → 328×352). 프레임 번호·시각은 원 시트와 같다.
  - **각성 순간 fx** `<무기>_awaken_in`(katana·greatsword·dagger·bow) 12프레임 — 각성을 얻은 순간 1회(followPlayer, anchor `player_pivot`), 같은 순간부터 `_awaken` 오버레이를 켠다.
  - **각성 전용 궤적** `<기본 fx>_awaken` 19종 — 각성 런에서 기본 fx 대신 1:1 교체(JSON `swapRule`, 틀·ms·피벗·행 동일): 칼 `katana_rise`·`katana_fall`·`katana_spin`·`katana_thrust`·`katana_issen_line_t1~t4` / 대검 `greatsword_sweep_cw`·`_ccw`·`greatsword_cleave`·`greatsword_charge_swing` / 단검 `dagger_combo1~3`·`dagger_flurry` / 활 `bow_arrow`·`bow_arrow_rapid`·`bow_arrow_snipe`(화살 3종은 꼬리 때문에 틀이 길다: 120×24 피벗 (96,12) / 128×24 (112,12) / 186×24 (162,12), rotate·drawnFacing 동일).
  - 시그니처 4종(`katana_fullmoon`·`greatsword_landslide`·`dagger_hundred_ghosts`·`bow_meteor_arrow`)은 이름·행·프레임·ms·앵커가 같고 그림·틀·피벗만 바뀜(JSON 기준).
- **새 앵커 이름(§18.11 추가)**: `path_point`, `crack_end`, `player_pivot_ground`, `clone_pivot`, `ground_point`, `aim_cursor`, `line_start`, `dodge_start_pivot`. 머리 꼭대기 앵커가 없는 동작은 주인공 피벗 위 124 도트 × 렌더 배율(1.25).
- **행 규약 `rowsAre`**: `stacks`(`katana_mirror_ki`·`bow_link_stack`·`status_mark`), `stages`(`set_flash` 2/4/6, `greatsword_giant_ring` lv4), `kinds`(`curse_mark`).
- **반복 타일**: `bow_skypierce_line`(`tile: true`, 주기 64 도트, 트림 안 함).
- **그림자 색**: `shadowPalette` 필드(주인공 색 → 분신 색). 난무 상주 분신은 단검 몸·무기 시트를 런타임 색 교체.
- **재사용 매핑**: 명경 분신 일섬 = `katana_issen_shadow` ×2(+90ms, ±24 도트) / 지진 착지 = `greatsword_shatter_crack_t2` / 비도 투척 = `dagger_thrown` ×5 / 연궁 분열 화살 = `bow_arrow_rapid` / 잔불 심장 = `fire_pool` / 거인 피격 흡수 = `greatsword_brace_absorb` / 비도 도착 = `shadowstep_ghost`.
- 아트 제안 길이·반경(설계안에 없던 값, 인터뷰 대기): 일도양단 균열 4칸, 지진 갈래 각 2칸, 울혈 폭발 반경 2.25칸, 정적 파동 반경 약 5.6칸.

## 22. 60라운드 2차 묶음 월드 아트 (57 Q38 확정안)
- 공통: `pixelScale 0.5`(64도트 = 1칸), 트림 아틀라스(§19). JSON 마다 `usage`·`pivot`·`anchor`(또는 `anchorRule`)·`states`, 발광 시트는 `emissiveColors`·`light`/`lightByState`. 상호작용 표지 = 램프 25 한 점 + 23 받침, 사용 후 꺼짐. 세부는 **각 JSON 이 기준**.
- **엘리트**: `enemies/v3/{dummy,archer,charger}_{idle,walk,attack,hurt,death}_elite`(15) — 호박 외곽선 오버레이. 적 **바로 아래**에 같은 프레임 번호·피벗·flip, scale ×1.15 로 그림(`pulse` 제안 필드). 적 시트를 다시 그리면 아트가 재생성.
- `fx/v3/elite_emblem` 52×60, 6행 × 2열(`rowsAre: kinds` — 접두어 6종 임시 id drunkard·burning·barrel_armor·enraged·ringleader·guzzler; 0열 평소, 1열 발동·변형). pivot (26,58), `anchor: enemy_head` = 적 pivot 위 `headTopByEnemy`(dummy 117·archer 120·charger 131) + 10도트.
- `fx/v3/elite_nameplate` 192×30, 가로 `nineSlice` 26/26, `textArea`, 권장 글자색 #eecc78. 글자는 시스템/UI 가 그림. pivot (96,28), 문장 위(2단 배치는 인터뷰 대기).
- **구조물** `structures/v3/`: `challenge_banner`(C4 도전 성소, idle → raise 5 → active 6 루프 → cleared, 광원 220, `paletteSwap`), `still`(1-2 증류 화로 v3, v1 대체 우선 로드, `fireBox`, 광원 300), `event_last_cup`(E2), `event_tasting_tray`(E5), `event_peddler_mat`(E1·숨은 노드 행상, `slotAnchors` 3), `event_cache`(E7·숨은 보물방, idle/open/used), `event_offering_cup`(E8, pray 4 루프), `event_dropped_ledger`(E9, `depth: floor`), `clue_drain`·`clue_cracked_cask`(숨은 노드 단서, found 상태 발광).
- **아이템** `items/v3/consumable_f1` 64×72, 3행 × 8(행 = 1층 소모품 3종 임시 id fire_bottle·strong_swig·cold_water), `anchor: ground`.
- 재사용(새로 그리지 않음): E3 징집병 사망, E4 UI 일기장, E6 독주 술통 + `fire_pool`, E2·E5 카운터, E8 묘, E7 숨은 벽. 성과 등급(완·양)은 UI 몫(설계 f.2).

### 22.1 2차 묶음 2단계 fx (60라운드 Q13)
- 모두 `fx/v3/`, `pixelScale 0.5`, 트림 아틀라스, `drawOver: lightmap`. 엘리트 fx 는 `paletteSwap: true`(층 강조색, Q12), 화염 술병 fx 는 `paletteSwap: "none"`. 세부는 각 JSON 이 기준.
- `elite_barrel_armor` 128×112, 2행(`back` = 적 아래·외곽선 위 / `front` = 적 위) × 3열(0 평소, 1·2 막아낸 맞음). `anchor: enemy_body`, scale = `bodyBoxByEnemy[적].scale` × 1.15, flipX 는 적과 같이. 첫 강공 적중 → 이 시트 끄고 `elite_barrel_armor_break`(208×176, 9프레임 1회, `flashFrame 0`, `shake`) 재생 → `elite_emblem` barrel_armor 행을 1열로.
- `elite_drunk_vapor` 112×80, 8프레임 루프, `enemy_head`(headTop − 8, 문장 아래). 몸 흔들림·휘는 궤적은 코드 연출.
- `elite_ringleader_link` 64×24, 6프레임 루프, 반복 타일(`tile: true`, 주기 64, 트림 안 함, `rotate`, 쐐기가 +x 로 흐름) — 두목 pivot 위 60 → 강화 대상 pivot 위 60. `elite_ringleader_aura` 136×56 루프, 강화 대상 발밑(`depth: floor`). 두목 사망 시 둘 다 끄고 주변 적에 `status_stagger`.
- `elite_guzzle_trail` 72×28, 4프레임 루프 투사체(죽은 적 → 엘리트 머리, 0.35초·호 30도트 제안) → `elite_guzzle_drink` 128×128, 9프레임 1회(`healFrame 4` 에 HP·크기 증가 적용 제안).
- `fire_bottle_thrown` 56×56, 8프레임 루프(회전은 그림에 포함, 왼쪽이면 flipX, 광원 70, 포물선·그림자 원은 시스템) → 착지 `fire_bottle_burst` 240×184, 10프레임 1회(`radiusPx 96` = 1.5칸, 광원 260, `lightByPhase`, `shake`) → `fire_pool` 로 넘김. 플레이어 소모품·독주 행상 공용(`sharedWith`).
