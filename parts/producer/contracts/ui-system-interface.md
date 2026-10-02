# 계약: UI ↔ 게임 시스템 인터페이스 (16라운드 승인)

두 파트는 아래 두 파일만 서로 참조한다. 변경은 프로듀서 인터뷰 후 이 문서부터 고친다.

| 제공 | 파일 | 사용 |
|---|---|---|
| 시스템 → UI | `src/contract/ui.ts` | UI 파트 코드는 이 파일과 `phaser` 만 import |
| UI → 시스템 | `src/ui/index.ts` | 시스템은 `uiScenes`(씬 클래스 배열)와 `UI_SCENES`(키) 만 import |

## 1. 이벤트 (시스템 → UI) — `uiBus.on(UI_EVENTS.X, handler)`
| 이벤트 | 페이로드 | 시점 |
|---|---|---|
| `STATE` | `UiSnapshot` | 매 프레임 끝 (HUD 갱신용). 값은 복사본, 수정 금지 |
| `STAGE_STARTED` | `{ stageIndex, stageName }` | 층 시작 |
| `ROOM_ENTERED` | `{ roomId, type }` | 방 진입 |
| `PLAYER_DAMAGED` | `{ hp, maxHp, amount }` | 피격 |
| `PLAYER_HEALED` | `{ hp, maxHp, amount }` | 회복 |
| `GOLD_CHANGED` | `{ gold, delta }` | |
| `WEAPON_EVOLVED` | `{ name }` | 개성 변화 (연출용) |
| `BOSS_STARTED` / `BOSS_PHASE` / `BOSS_DIED` | `{ name, hp, maxHp, phase }` | 보스전 |
| `MENU_OPEN` | `UiMenu` | 시스템이 선택지를 요구할 때 (보상·상점·패시브·메타). UI 가 그리고 `select()` 로 답한다 |
| `MENU_CLOSE` | `{ id }` | |
| `RUN_ENDED` | `UiResult` | 사망·클리어. UI 결과 화면이 그린다 |
| `FATE_DECIDED` | `{ weaponName, features }` | 개성 선택 결과 (연출용) |
| `STORY` | `UiStoryLine = { kind: 'floor' \| 'boss' \| 'rest' \| 'notice' \| 'evolution' \| 'death'; text: string }` | 스토리 자막 한 줄 (26라운드). 층 진입·보스 개시·휴식 방 첫 진입·공지·개성 변화. UI 가 하단 자막으로 그린다 |
| `PAUSED` / `RESUMED` | `{}` | |

## 2. 스냅샷 — `UiSnapshot` (`getUiSnapshot()` 또는 `STATE` 이벤트)
```ts
interface UiSnapshot {
  hp: number; maxHp: number; gold: number; potions: number; potionMax: number;
  stageIndex: number; stageName: string; trialsCleared: number; trialsTotal: number; bossUnlocked: boolean; exitOpen: boolean;
  weapon: { name: string; evolutionName: string | null; personality: number; threshold: number; secondaryName: string };
  boss: { name: string; hp: number; maxHp: number; phase: number } | null;
  stats: { attack: number; defense: number; crit: number; sense: number };
  passives: { name: string; level: number; description: string }[];
  savesLeft: number; seed: string;
  map: { rooms: { id: string; type: 'start' | 'trial' | 'rest' | 'boss'; cells: { cx: number; cy: number }[]; visited: boolean; cleared: boolean }[];
         connections: { a: { cx: number; cy: number }; b: { cx: number; cy: number } }[]; currentRoomId: string; gridW: number; gridH: number };
  paused: boolean; menu: UiMenu | null;
  // 26라운드 추가 (스토리 계약 story-text.md 의 이름을 시스템이 채운다)
  playerName: string;                       // 일기장에 적은 이름. 비면 ''
  floorTitle: string;                       // 층 제목 (예: "1층 · 술독 제국 '잔(盞)'"). 비면 stageName 사용
  names: { potion: string; gold: string; shop: string; souls: string }; // 재화·물약·상점·영혼의 세계관 이름
}
```
`UiResult` 에도 `playerName` 과 `line`(사망·클리어 문장)이 추가된다 (26라운드). `STAGE_STARTED.stageName` 은 층 제목으로 채워진다.
`secondaryName` 은 우클릭 보조 동작의 이름(현재 전 무기 "패링"). 무기별로 달라질 예정(16라운드 도영 님 지시).

## 3. 메뉴 — `UiMenu`
```ts
interface UiMenu { id: 'reward' | 'passive' | 'shop' | 'meta' | 'evolve'; title: string; footer?: string;
  lines: { key: string; label: string; enabled: boolean; detail?: string }[] }
```
UI 는 `uiCommands.select(menuId, key)` 로 답한다. 시스템은 UI 렌더러가 등록되기 전까지 임시 텍스트 메뉴로 그린다 (`uiCommands.registerRenderer()` 호출 시 임시 메뉴 비활성).

## 4. 명령 (UI → 시스템) — `uiCommands`
| 함수 | 동작 |
|---|---|
| `registerRenderer()` | UI 가 메뉴·결과·일시정지를 그린다고 선언 (시스템 임시 화면 끔) |
| `select(menuId, key)` | 열린 메뉴에 선택 전달 |
| `pause()` / `resume()` | 게임 씬 일시정지·재개 (시스템이 `PAUSED`/`RESUMED` 발행) |
| `startNewRun()` | 개성 선택 씬으로 (세이브 삭제) |
| `continueRun()` | 세이브가 있으면 이어하기, 없으면 `startNewRun()` |
| `hasSave()` | 세이브 존재 여부 |
| `toTitle()` | 타이틀 씬으로 (런 중이면 세이브 없이 종료되므로 UI 가 확인창을 띄운다) |
| `getUiSnapshot()` | 현재 스냅샷 |
| `getUiText()` | 세계관 문구 `UiText { title, evolveMenu, result, pause, hud, controls }` (스토리 텍스트 팩 2차, 29라운드). UI 는 키가 있으면 그 문구를, 없으면 기본 문구를 쓴다 |

## 5. 씬 (UI → 시스템) — `src/ui/index.ts`
```ts
export const UI_SCENES = { TITLE: 'UiTitle', HUD: 'UiHud', PAUSE: 'UiPause', MENU: 'UiMenu', RESULT: 'UiResult' } as const;
export const uiScenes: Phaser.Types.Scenes.SceneType[];
```
시스템 규칙: Preloader 는 `UI_SCENES.TITLE` 이 등록돼 있으면 타이틀로, 아니면 기존 분기. Game 씬은 `create()` 에서 `UI_SCENES.HUD` 를 병렬 실행(`scene.launch`)하고 `shutdown` 에서 멈춘다. 사망·클리어 시 `RUN_ENDED` 를 발행하고 `UI_SCENES.RESULT` 를 시작한다(UI 가 등록돼 있을 때). 개성 선택 씬(`Setup`)은 시스템 소유로 유지하되 메타 메뉴는 `MENU_OPEN(meta)` 로 UI 가 그린다.

## 6. 금지
- UI 는 `gameState`·`EventBus`·씬 내부에 접근하지 않는다. 스냅샷은 복사본이며 바꿔도 시스템에 영향 없다.
- 시스템은 UI 씬의 내부 객체에 접근하지 않는다. 씬 키와 배열만 쓴다.


## 7. 29라운드 추가분 (자율 승인, 도영 님 검토 대기)
- 메뉴 id `evolve`: 개성 임계 도달 시 3지선다(변환 A / 변환 B / 강화). 시스템이 게임을 정지하고 UI 메뉴 씬이 그린다. 선택지 `label` 은 **이름만**, `detail` 은 설명(UI 가 아래 줄에 그린다). 강화 항목은 label '더 깊게 — …', detail 에 수치.
- `uiCommands.getUiText()` 추가. `weapon.secondaryName` 은 무기별(패링/가드/그림자 걸음/조준 사격).
- 아트 연동: UI 는 스프라이트를 직접 다루지 않는다. HUD 아이콘이 필요하면 `assets/ui/**`(UI 소유)에 둔다.
- 메뉴 id `ending`: 황제 처치 후 2지선다(없앤다/이해한다). `UiResult.ending?: 'destroy' | 'understand'`, `line` 은 고른 엔딩 문장. (29라운드 자율 승인)
- 요청 대기: `UiSnapshot.weapon.id`, `UiSnapshot.mute`.

## 8. 45라운드 추가 (비전투 이동: 달리기·워프, 승인 #12)
결정: `decisions/2026-10-02-round-45-traversal-structures.md` Q2·Q3. 달리기는 시스템이 전부 처리하고(UI 는 표시만), 워프는 **UI 가 선택 화면**, **시스템이 상태·명령·실행**을 맡는다.

### 8.1 스냅샷 추가 필드 (`UiSnapshot`)
```ts
interface UiSnapshot {
  // ...기존 필드
  inCombat: boolean;    // 활성 전투 방(시련 웨이브·보스전 진행 중)이 있으면 true. 달리기·워프는 false 일 때만
  sprinting: boolean;   // 지금 달리는 중 (비전투 + Shift 누름 + 이동 입력). HUD 표시용, 없어도 됨
  warp: UiWarpState;
}
interface UiWarpState {
  ready: boolean;                       // 지금 warpTo 를 받을 수 있는지 (blocked === null)
  blocked: 'combat' | 'busy' | null;    // ready=false 의 이유. combat = 전투 중, busy = 메뉴·개성 선택·보상·층 전환·워프 연출·사망
  targets: string[];                    // 워프 가능한 방 id (map.rooms[].id 와 같은 값, 방 정의 순서). ready 와 무관하게 방 조건만으로 채운다
  warping: boolean;                     // 워프 연출 중 (입력 잠금)
}
interface UiRoom {
  // ...기존 필드 (id, type, cells, visited, cleared)
  warpable: boolean;                    // = warp.targets.includes(id). 미니맵이 방마다 바로 쓰도록 같은 값을 중복 제공
}
```
- **워프 가능 방 조건** (`targets`·`warpable`): 방문했고(`visited`) 시스템 기준 클리어 상태이며 현재 방(`map.currentRoomId`)이 아님.
  시스템 기준 클리어 = 시작 방(처음부터) · 휴식 방(진입 즉시) · 시련 방(웨이브 클리어) · 보스 방(처치 후). 기존 `UiRoom.cleared` 는 시련 클리어 표시용 그대로이므로, 워프 판정에는 `warpable` 을 쓴다.
- **현재 방**: 기존 `map.currentRoomId` (마지막으로 내부에 들어간 방, 복도에 있어도 유지). `targets` 에서 빠진다.

### 8.2 명령 (UI → 시스템) — `uiCommands.warpTo(roomId: string): boolean`
- 판정이 통과하면 워프를 시작하고 `true`, 아니면 `false` 를 돌려주고 `WARP_DENIED` 를 발행한다.
- 게임이 `pause()` 로 멈춰 있으면, 판정이 통과할 때 시스템이 먼저 재개(`RESUMED` 발행)한 뒤 워프한다. 선택 화면 동안 멈출지는 UI 가 정한다 (멈추는 것을 권장 — 선택 클릭이 게임 씬의 공격 입력으로도 들어가지 않게).
- 실행: 섬광(퇴장) → 약 140ms 뒤 대상 방의 안전한 바닥(중앙에서 가장 가깝고 출구·상점 타일에서 3칸 이상 떨어진 곳)으로 이동, 카메라 즉시 이동, 섬광(도착). 시작부터 약 300ms 입력 잠금, 600ms 무적 (임시값).
- 도착하면 기존 `ROOM_ENTERED` 가 평소처럼 발행된 뒤 `WARP_DONE` 이 온다.

### 8.3 이벤트 (시스템 → UI)
| 이벤트 | 페이로드 | 시점 |
|---|---|---|
| `WARP_DONE` | `UiWarpDone = { fromRoomId: string; roomId: string; type: RoomType }` | 워프 도착 (위치·카메라 이동 완료) |
| `WARP_DENIED` | `UiWarpDenied = { roomId: string; reason: UiWarpDenyReason }` | `warpTo` 거부 |

`UiWarpDenyReason = 'combat' | 'busy' | 'unknown-room' | 'not-cleared' | 'current-room'` — 전투 중 / 메뉴·연출 중(또는 게임 씬 없음) / 없는 방 id / 미방문·미클리어 / 이미 그 방.

### 8.4 키 (UI 가 처리)
- **워프 선택 화면을 여는 키는 UI 가 직접 읽는다.** 시스템은 키를 등록하지 않는다. 임시 제안: **Tab** (브라우저 포커스 이동을 막으려면 키 캡처 필요). 기존 배정과 겹치지 않음: W/A/S/D 이동, Space 대쉬, Q 물약, R 재시작, M 음소거(시스템 오디오), Shift 달리기(시스템), 좌·우클릭 공격·보조. ESC 등 UI 가 이미 쓰는 키와의 관계는 UI 가 정한다.
- 달리기 키 **Shift** 는 시스템이 읽는다 (`KEYS.SPRINT`).
- 선택 화면은 `inCombat` 이 true 이거나 `warp.ready` 가 false 면 열지 않거나 회색으로 그리는 것을 권장 (열어도 `warpTo` 가 거부한다).
