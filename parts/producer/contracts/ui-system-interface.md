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

## 9. 47라운드 추가 (상호작용 구조물, 승인 #14)
결정: `decisions/2026-10-02-round-47-structures-impl.md` (초안 `parts/system/structures-draft.md` 5.3 Q5~Q18 추천안 적용, 전부 임시값). 시스템은 규칙·판정·키 입력·문자열을, UI 는 안내·메뉴·HUD 상태·미니맵 점을 맡는다.
코드: `src/contract/ui.ts` (아래 타입 이름 그대로). 모든 새 필드는 시스템이 채우기 전까지 빈 기본값(`null` / `[]` / `false`)이다.

### 9.1 스냅샷 — 상호작용 안내 `UiSnapshot.interactable: UiInteractable | null`
플레이어에게서 **1.5칸(24px) 안의 가장 가까운 E형 구조물** 하나. 없으면 `null`. 다 쓴 구조물(더 할 수 있는 행동이 없는 것)은 빠진다. 일시적으로 못 쓰면 `usable=false` 와 사유로 내려준다.
```ts
type UiStructureKind =            // 초안 id
  | 'crate'       // C1 부서지는 짐 (타격형)
  | 'chest'       // C2 종군 상인의 궤짝 (E)
  | 'grave'       // C3 무명 전사의 묘 (E 2초)
  | 'campfire'    // C5 모닥불 (E)
  | 'cask'        // 1-1 독주 술통 (타격·굴림)
  | 'still'       // 1-2 증류 화로 (통과)
  | 'ledger'      // 1-3 외상 장부대 (E)
  | 'agingBarrel' // 1-4 숙성 통 (E)
  | 'counter'     // 1-5 선술집 카운터 (E)
  | 'hiddenWall'  // 1-6 밀주 저장고 숨은 벽 (타격)
  | 'cardTable'   // 2-1 패 탁자 (E + 선택)
  | 'exchange'    // 2-2 목숨 칩 환전대 (E)
  | 'dogRing'     // 2-3 투견 링 (E)
  | 'stakeBell'   // 2-4 판돈 종 (타격)
  | 'roulette'    // 2-5 룰렛 바닥 (자동)
  | 'pawn';       // 2-6 전당포 창구 (E)

interface UiCost {
  kind: 'gold' | 'hp' | 'maxHp' | 'potion' | 'passive' | 'none';
  amount: number;       // 수치 (표시 불필요면 0)
  label: string;        // 그대로 그릴 문자열 (예 '35전표'). none 이면 ''
  affordable: boolean;  // 지금 낼 수 있는가
}

type UiInteractBlockReason = 'combat' | 'busy' | 'gold' | 'hp' | 'potion' | 'notReady' | 'full' | 'limit';
// combat 전투 중 · busy 메뉴·연출·워프 중 · gold/hp/potion 부족 · notReady 아직 때가 아님(숙성 중 등) · full 더 받을 수 없음 · limit 횟수 소진

interface UiInteractable {
  id: string;            // 구조물 인스턴스 id (층 안에서 유일)
  kind: UiStructureKind;
  name: string;          // 표시 이름 (자리표시)
  roomId: string;        // map.rooms[].id
  key: string;           // 누를 키 이름 (현재 'E')
  actionKey: string;     // 행동 문구 키 (예 'chest.open')
  action: string;        // 행동 문구 값 (자리표시, 예 '연다')
  cost: UiCost | null;   // 비용 없으면 null
  hold: { durationMs: number; progress: number } | null; // C3 묘: durationMs 2000, progress 0..1 (이동하면 0). 그 외 null
  usable: boolean;       // = reason === null
  reason: UiInteractBlockReason | null;
  reasonText: string;    // 불가 사유 문구 (자리표시). usable 이면 ''
  screen: { x: number; y: number }; // 구조물 윗변 중앙의 화면 좌표 (게임 캔버스 픽셀, 카메라 반영)
}
```
- `interactable` 이 나오는 종류: `chest`·`grave`·`campfire`·`ledger`·`agingBarrel`·`counter`·`cardTable`·`exchange`·`dogRing`·`pawn`. 타격·통과·자동형(`crate`·`cask`·`still`·`hiddenWall`·`stakeBell`·`roulette`)은 안내가 없고 이벤트(§9.6)로만 알린다.
- E 를 누르면 바로 실행되는 종류: `chest`(지불·개봉) · `campfire`(불씨 전부 사용) · `agingBarrel`(넣기 / 꺼내기) · `dogRing`(판돈 걸고 도전 시작). 비용은 `cost` 로 미리 보여 준다.
- E 를 누르면 메뉴(§9.4)가 열리는 종류: `cardTable`·`exchange`·`pawn`·`ledger`·`counter`, 그리고 `grave`(2초 누르기가 끝나면).

### 9.2 스냅샷 — HUD 상태 `UiSnapshot.statuses: UiStatus[]`
층 안에서 이어지는 구조물 상태. 시스템이 그릴 순서로 정렬해 내려주며, 없으면 `[]`. UI 는 `label`·`value` 를 그대로 그린다.
```ts
type UiStatusId = 'debt' | 'drunk' | 'stakes' | 'embers' | 'fireWeapon' | 'ring' | 'roulette' | 'aging' | 'pawn';
interface UiStatus {
  id: UiStatusId;
  kind: 'buff' | 'debuff' | 'resource' | 'timer' | 'rule' | 'progress';
  label: string;        // 이름 (자리표시)
  value: string;        // 그대로 그릴 값
  amount?: number; max?: number;            // 게이지용 (선택)
  remainMs?: number; durationMs?: number;   // 타이머 상태만
  detail?: string;      // 효과 설명 한 줄 (자리표시)
}
```
| id | 출처 | kind | value 예 | 타이머 | 사라지는 때 |
|---|---|---|---|---|---|
| `debt` | 1-3 외상 장부대 | debuff | '90G' (amount=남은 빚) | — | 다 갚음 / 보스 처치 정산 |
| `drunk` | 1-5 선술집 카운터 | buff | '2단' (amount 1~3, max 3) | — | 다음 시련 클리어·보스 처치 |
| `stakes` | 2-4 판돈 종 | debuff | '×1.6' (amount=울린 횟수, max 2) | — | 층 끝 |
| `embers` | C5 모닥불 | resource | '2' (amount, max 4) | — | 모닥불 사용(0이면 항목 없음) |
| `fireWeapon` | 1-2 증류 화로 | buff | '불' | remainMs/durationMs 6000 | 시간 끝 |
| `ring` | 2-3 투견 링 | timer | '2/3' (amount=쓰러뜨린 수, max) | remainMs/durationMs 20000 | 도전 종료 |
| `roulette` | 2-5 룰렛 바닥 | rule | 규칙 이름 | — | 그 시련 클리어 |
| `aging` | 1-4 숙성 통 | progress | '1/2' (amount=지난 시련 수, max 2) / 다 익으면 '다 익음' | — | 꺼냄 |
| `pawn` | 2-6 전당포 창구 | resource | 맡긴 개수 | — | 되찾음 / 층 끝 |

적에게 걸린 화상은 HUD 상태가 아니다(시스템이 월드에 그린다).

### 9.3 키
- **E 는 시스템이 읽는다** (상호작용, 2초 누르기 포함). UI 는 키를 등록하지 않고 `interactable` 로 안내만 그린다(예: "[E] 연다 · 35전표", 누르기 진행 원·막대, 불가 시 회색 + `reasonText`).
- E 형 구조물은 **비전투 중에만** 동작한다 (`inCombat === true` 이면 `reason: 'combat'`).
- 메뉴 조작은 기존 메뉴와 같다 (`select(menuId, key)`). 구조물 메뉴가 열려 있는 동안 시스템이 플레이어 입력(이동·공격·E)을 잠근다. 게임 씬은 멈추지 않는다.

### 9.4 메뉴 — 구조물 메뉴 id 와 선택지
기존 `MENU_OPEN(UiMenu)` → `uiCommands.select(menuId, key)` → `MENU_CLOSE` 흐름을 그대로 쓴다. `UiMenuId` 에 아래 6개가 추가된다.
```ts
type UiStructureMenuId = 'cards' | 'exchange' | 'pawn' | 'grave' | 'ledger' | 'counter';
type UiMenuId = 'reward' | 'passive' | 'shop' | 'meta' | 'evolve' | 'ending' | UiStructureMenuId;
interface UiMenu {
  // ...기존 id, title, footer?, lines
  cancelKey?: string;    // 그만두기 줄의 key. 구조물 메뉴는 항상 '0'. 있으면 UI 는 ESC·닫기 버튼을 select(id, cancelKey) 로 보낸다
  structureId?: string;  // 이 메뉴를 연 구조물 인스턴스 id (= UiInteractable.id). 구조물 메뉴만
}
```
- 모든 구조물 메뉴의 **마지막 줄은 그만두기**(`key: '0'`, `enabled: true`)이고 `cancelKey: '0'` 이다. 나머지 선택지 key 는 `'1'`, `'2'`, … 순서.
- 선택지의 `label` 은 이름(비용 포함 가능), `detail` 은 효과·조건 설명, 못 고르면 `enabled: false`(이유는 `detail` 에).
- 한 선택 뒤 같은 메뉴를 다시 그려야 하면(전당포처럼 여러 번) 시스템이 같은 id 로 `MENU_OPEN` 을 다시 보낸다(기존 상점과 같음). 끝나면 `MENU_CLOSE`.

| id | 구조물 | 선택지 (key: 내용, 전부 자리표시·임시값) |
|---|---|---|
| `cards` | 2-1 패 탁자 | '1'·'2'·'3': 엎어진 패 3장 중 하나 (판돈은 `title`/`footer` 에). 고르면 결과는 `STRUCTURE_RESULT`, 흉패면 `CHALLENGE_STARTED` |
| `exchange` | 2-2 목숨 칩 환전대 | '1': 피를 판다 (HP 25% → 50G, 층당 3회) · '2': 목숨을 건다 (최대 HP -15 → 능력치 포인트 1, 층당 1회) |
| `pawn` | 2-6 전당포 창구 | 맡기기: 보유 패시브마다 한 줄 + 물약 한 줄 · 되찾기: 맡긴 것마다 한 줄 (label 에 '맡긴다'/'되찾는다' 와 금액). 선택마다 다시 그림 |
| `grave` | C3 무명 전사의 묘 | '1': 기록한다 (영혼 +10) · '2': 받아들인다 (개성 +25) |
| `ledger` | 1-3 외상 장부대 | '1': 외상을 긋는다 (+60G, 빚 90G, 층당 1회) · '2': 갚는다 (가진 골드로 빚 상환, 빚 있을 때만) |
| `counter` | 1-5 선술집 카운터 | '1'~'3': 잔 고르기 (잔당 10G, 취기 +1단, 누적 최대 3 — 이미 마신 잔은 `enabled: false`) |

### 9.5 미니맵 — `UiRoom.structureDot: boolean`
사용 가능한 E형 구조물(§9.1 의 `interactable` 대상 종류 중 다 쓰지 않은 것)이 남은 방이면 `true`. 미니맵은 그 방에 점 1개를 그린다. 미방문 방의 표시 여부는 기존 미니맵 규칙(방문 방만 그림 등)을 따른다(UI 판단).

### 9.6 이벤트 (시스템 → UI)
| 이벤트 | 페이로드 | 시점 |
|---|---|---|
| `STRUCTURE_USED` | `UiStructureUsed = { id; kind: UiStructureKind; roomId; actionKey }` | E형 구조물 행동 완료 (E 즉시 실행 또는 메뉴 선택 확정) |
| `STRUCTURE_BROKEN` | `UiStructureBroken = { id; kind; roomId }` | 타격형 구조물 부서짐 (`crate`·`cask`·`hiddenWall`). 연출·음향용, UI 구독은 선택 |
| `STRUCTURE_RESULT` | `UiStructureResult` (아래) | 결과 알림 한 줄 — 획득·손실·경고. UI 가 토스트·하단 알림으로 그린다 |
| `CHALLENGE_STARTED` | `UiChallengeStarted` (아래) | 투견 링 시작 · 흉패 소환 (전투 시작 → `inCombat` true) |
| `CHALLENGE_CLEARED` | `UiChallengeCleared` (아래) | 위 도전 종료 (`inCombat` false 로 돌아옴) |
```ts
interface UiStructureResult {
  id: string; kind: UiStructureKind;
  tone: 'gain' | 'loss' | 'mixed' | 'warn' | 'info'; // warn = 판돈 종 첫 타격(두 번째 타격에서 확정) 등
  text: string;                                      // 그대로 그릴 한 줄 (자리표시)
  deltas: { gold?: number; hp?: number; maxHp?: number; potions?: number; souls?: number; personality?: number; points?: number };
}
interface UiChallengeStarted {
  id: string; kind: 'dogRing' | 'cardTable'; roomId: string;
  label: string;               // 도전 이름 (자리표시)
  goal: string;                // 목표 문구 (자리표시, 예 '20초 안에 개 3마리')
  timeLimitMs: number | null;  // 투견 링 20000, 흉패 null
}
interface UiChallengeCleared {
  id: string; kind: 'dogRing' | 'cardTable'; roomId: string;
  outcome: 'clear' | 'flawless' | 'timeout'; // timeout = 시간 초과(판돈 몰수, 사망 아님)
  text: string;                              // 결과 문구 (자리표시)
}
```
- 골드·HP·물약 변화는 기존 `GOLD_CHANGED`·`PLAYER_DAMAGED`/`PLAYER_HEALED` 도 평소처럼 발행된다. `STRUCTURE_RESULT` 는 그 위에 얹는 설명 문구다.
- 모닥불을 쓰면 기존 `STORY`(kind `'rest'`) 로 휴식 메모가 다시 올 수 있다.

### 9.7 명령
새 명령은 없다. 구조물 메뉴는 기존 `uiCommands.select(menuId, key)` 로 답한다(그만두기 = `select(id, menu.cancelKey)`).

### 9.8 텍스트
구조물 이름·행동 문구·사유·결과·메뉴 문장은 전부 **자리표시**이며 시스템이 문자열로 내려준다(Q17). 스토리 파트 확정 후 `contracts/story-text.md` 로 바뀌어도 필드 형태는 그대로다. UI 는 문구를 직접 만들지 않는다(키 이름 'E' 같은 조작 안내 틀은 UI 가 그려도 된다).
