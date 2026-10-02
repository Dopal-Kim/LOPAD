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
