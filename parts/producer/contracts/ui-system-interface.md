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
`secondaryName` 은 우클릭 보조 동작의 이름. ~~(현재 전 무기 "패링"). 무기별로 달라질 예정(16라운드 도영 님 지시).~~ → **무기별(27라운드 Q1·§7): 칼 '가드·패링'(56라운드 Q48·§13) / 대검 '가드' / 단검 '그림자 걸음' / 활 ~~'조준 사격'~~ '당겨 쏘기'(57라운드 Q7).**

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


## 7. 29라운드 추가분 (자율 승인, ~~도영 님 검토 대기~~ → 31라운드 #8 일괄 승인)
- 메뉴 id `evolve`: 개성 임계 도달 시 3지선다(변환 A / 변환 B / 강화). 시스템이 게임을 정지하고 UI 메뉴 씬이 그린다. 선택지 `label` 은 **이름만**, `detail` 은 설명(UI 가 아래 줄에 그린다). 강화 항목은 label '더 깊게 — …', detail 에 수치.
- `uiCommands.getUiText()` 추가. `weapon.secondaryName` 은 무기별(패링/가드/그림자 걸음/~~조준 사격~~). (칼은 56라운드 '가드·패링' — §13, 활은 57라운드 Q7 '당겨 쏘기')
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
- `interactable` 이 나오는 종류: `chest`·`grave`·`campfire`·`ledger`·`agingBarrel`·`counter`·`cardTable`·`exchange`·`dogRing`·`pawn` + (60라운드) `warFlag`·`clue`·`eventProp`·`mapSeller`. 타격·통과·자동형(`crate`·`cask`·`still`·`hiddenWall`·`stakeBell`·`roulette`)은 안내가 없고 이벤트(§9.6)로만 알린다.
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

## 10. 48라운드 추가 (노드 지도 진행·탄생 연출·워프 비활성, 승인 #17)
결정: `decisions/2026-10-02-round-48-playfeel-route.md`. 1~2층은 방+복도 대신 **노드 지도 + 노드마다 작은 전투장(약 40×24타일)** 으로 진행한다.

### 10.1 스냅샷 (`UiSnapshot.route`)
```ts
type UiNodeType = 'journey' | 'battle' | 'shop' | 'rest' | 'event' | 'boss';
type UiNodeState = 'locked' | 'available' | 'current' | 'cleared' | 'passed';
interface UiRouteNode {
  id: string; type: UiNodeType; name: string;  // name 은 자리표시
  col: number;            // 왼→오 진행 단계(0부터)
  row: number;            // 같은 단계 안 위치(0부터), 그리기용
  links: string[];        // 다음 단계로 이어지는 노드 id
  state: UiNodeState;
}
interface UiRoute {
  floor: number;
  nodes: UiRouteNode[];
  currentId: string | null;
  choosing: boolean;      // true = 다음 노드를 골라야 함(시스템이 입력 잠금)
}
// UiSnapshot.route: UiRoute | null  (노드 지도를 쓰지 않는 층이면 null)
```
- `available` = 지금 고를 수 있는 다음 노드(choosing 일 때만 의미), `passed` = 고르지 않고 지나친 갈래.

### 10.2 이벤트·명령
- `UI_EVENTS.ROUTE_CHOOSE_OPEN` ('ui:route-choose-open', 페이로드 `UiRoute`): 노드를 마치고 출구에 서면 발행. 시스템은 게임 입력을 잠근다. UI 는 노드 지도를 선택 모드로 연다.
- `uiCommands.chooseNode(id: string): boolean` — available 노드만 true. 시스템이 전환 연출 후 그 노드 전투장을 연다.
- `UI_EVENTS.ROUTE_NODE_ENTERED` ('ui:route-node-entered', `{ id, type, name }`): 노드 진입(자막·제목 표시용).
- Tab: 노드 지도 보기 전용(선택 불가, 게임 일시정지). 45라운드 워프는 비활성 — `warp.targets` 는 항상 빈 배열, `ready=false`. UI 는 워프 지도 대신 노드 지도를 띄운다.

### 10.3 탄생 연출
- `UI_EVENTS.BIRTH_STARTED` ('ui:birth-started') / `BIRTH_DONE` ('ui:birth-done'): 그 사이 UI 는 HUD 를 숨기고 "아무 키나 눌러 건너뛰기" 안내만 작게 표시(선택). 건너뛰기 입력은 시스템이 받는다.

### 10.4 카메라
- 게임 월드 카메라 zoom 2(탄생 연출 중 일시 확대). UI 씬은 영향 없음. `UiInteractable.screen` 등 화면 좌표는 계속 캔버스 픽셀(960×540)로 준다.

## 11. 49라운드 추가 (무기 자원·위치 정보·음소거 이동·무기 시험장)
결정: `decisions/2026-10-02-round-49-playtest2.md`. 타입은 `src/contract/ui.ts` 에 커밋됨.

### 11.1 무기 자원 (`UiSnapshot.resource: UiWeaponResource | null`)
- 칼·대검 = `stamina`(기력), 활 = `ammo`(화살 탄창, 비면 장전 `reloading` + `progress`), 단검 = `heat`(과열: 연격이 이어질수록 가열·공격속도 상승, 최대에서 `overheat` 후 냉각 `progress`, `stage` = 가열 단계).
- UI 는 HUD 에 무기 아래 게이지로 그린다(종류별 모양 다르게: 기력 막대 · 화살 칸 · 열 게이지). 시스템은 값만 준다.

### 11.2 위치 정보
- `UiRouteNode.region`(지역 이름)·`desc`(설명 한두 줄, 자리표시) 추가. 1층 지역 흐름: 여정(황무지·전장) → 성문 → 외곽 거리 → 양조 구역 → 지배자의 연회장.

### 11.3 키 재배정
- **M = 지도 + 현재 위치·위치 정보** (UI 가 읽음). Tab 은 같은 지도(보조). 시스템은 M 을 더 이상 음소거로 쓰지 않는다.
- 음소거는 Esc(일시정지) 메뉴의 설정 항목 → `uiCommands.setMuted(bool)`, 상태는 `UiSnapshot.muted`.
- 노드 선택 확정 전 UI 가 "넘어가시겠습니까?" 확인을 띄우고, 예일 때만 `chooseNode` 를 부른다(시스템 변경 없음).

### 11.4 무기 시험장
- 타이틀에서 `uiCommands.startWeaponLab()` → 시스템 씬 `WeaponLab`. 무기·진화 갈래 고르기는 기존 메뉴 흐름(`MENU_OPEN` id `lab`·`labBranch` → `select`)으로, UI 는 일반 메뉴처럼 그린다. 시험장 안에서 `UiSnapshot.lab = true`(UI 는 노드 지도·층 표시 대신 '무기 시험장' 표시). 시험장 안 열기 키는 시스템이 정해 계약 README 에 적는다(임시 제안: L).

## 12. 50라운드 (Gemini 키아트·지도 배경 적용)
- UI 는 `assets/sprites/ui/keyart_<region>.png`(960×540)·`map_bg_f1.png` 를 `assets/ui/` 로 복사해 쓴다(승인 #18 연장). 키아트: 노드 진입 시 지역이 바뀌면 짧은 지역 카드(키아트 + 지역 이름), M 지도 위치 패널 배경. 지도 배경: 1층 노드 지도 배경(`MAP_BG_FLOORS`), 노드 배치는 지도 그림의 길(왼쪽 황무지 → 오른쪽 위 연회장)에 맞춘다.
- 시스템 변경 없음(`UiRouteNode.region` 사용).

## 53라운드 추가 (1920 렌더 · F 넣기/뽑기)
- **화면(52라운드 Q8)**: 실제 캔버스 1920×1080, 논리 화면 960×540. UI 씬의 main 카메라는 시스템이 씬 시작(READY) 때 zoom 2·원점 (0,0)으로 맞추므로 UI는 960×540 좌표로 그린다. 씬의 `this.scale.width/height`는 960×540으로 보인다(호환 층, 임시 — UI가 `UI_SCREEN` 상수로 옮긴 뒤 제거). `pointer.x/y`는 실제 캔버스 px — 논리 좌표는 `pointer.worldX/worldY`. `UiInteractable.screen` 등 화면 좌표는 논리 960×540 px. UI 씬은 main 카메라 zoom·origin·centerOn을 바꾸지 않는다. 코드 상수 `UI_SCREEN = { WIDTH: 960, HEIGHT: 540, RESOLUTION: 2 }`(`src/contract/ui.ts`).
- **넣기/뽑기(51라운드 Q4)**: `UiSnapshot.carry: { drawn: boolean; firstStrike: string | null; key: 'F' } | null` — 칼·대검처럼 넣고 뽑는 무기일 때만, 손에 드는 무기(단검·활)는 null. `firstStrike` = 넣은 상태에서 준비된 첫 타 보너스 이름(예: '발도', '끌어내기'), 뽑았거나 없으면 null. 조작 안내에 F(넣기/뽑기) 추가.
- **(53라운드 Q47~Q50, 시스템 구현)** `UI_EVENTS.ENEMY_INCOMING` `{ roomId, delayMs, count? }` — 모든 적 소환 delayMs 전에 발행(0이면 동시, 튜토리얼 900ms). UI 경고는 튜토리얼에서만. `UI_EVENTS.TUTORIAL_STEP` `{ index, total, text, keys: string[] }` — 튜토리얼 안내 문구가 뜰 때. `uiCommands.cancelChoose(): boolean` — 노드 고르기 중 Esc, 지도를 닫고 출구에서 물러남(고르는 중이 아니면 false). `cancelKey` 는 Esc로 닫을 수 있는 메뉴(상점 '0', 구조물 '0', 시험장 lab '0', labBranch '9')에만, 필수 메뉴(보상·패시브·개성·엔딩)에는 없음. 시험장에서 메뉴가 없을 때의 Esc는 UI 일시정지(pause()가 시험장에도 적용)가 받는다.

## 13. 56라운드 추가 (무기 고유 자원·그로기 HUD, 승인 #20)
- 근거: 56라운드 Q13~Q20(자원 구조), Q7·Q19(그로기 1.5초), Q48(칼 우클릭 가드·패링), Q58(HUD 표시 결정).
- **`UiSnapshot.gauge: UiWeaponGauge | null`** — 무기 고유 자원. 칼 `kenki`(검기, 3단), 대검 `grudge`(울분), 단검 `brand`(낙인 — 값은 현재 가장 많이 쌓인 적의 스택 0~5, 과열은 기존 `resource`), 활 `breath`(숨, 0~3).
  - `{ kind: 'kenki' | 'grudge' | 'brand' | 'breath'; label: string; value: number; max: number; stage?: number; focusing?: boolean }` — `stage` 는 단계형(검기 0~3, 울분 0~3 구간 1~33/34~66/67~100%), `focusing` 은 숨 감속 정밀 조준 중.
- **`UiSnapshot.groggy: { active: boolean; leftMs: number } | null`** — 칼·대검만(기력 0 → 1.5초, 시간으로만 회복). 그 밖의 무기는 null. 기존 `resource.state: 'exhausted'` 는 유지.
- **이름 변경**: 칼 `weapon.secondaryName` '패링' → '가드·패링'(조작 안내 `{secondary}` 문구에 그대로 반영).
- 월드 문구 "PERFECT GUARD"·"PARRY" 는 시스템이 월드 공간 텍스트로 그린다(UI 아님).
- UI 표시(56라운드 Q58): 무기명 옆 고유 자원 게이지(단계 눈금), 그로기 중 남은 시간 표시. 세부 모양은 UI 파트 인터뷰.

## 14. 57라운드 빌드 축·2차 묶음 — **초안 (57 Q38 일괄 진행 지시에 따라 적용 예정)**
> **초안이다.** 계약 변경은 원래 재인터뷰 사항(승인 #12·#14·#17·#20 조건)이다. 57라운드 Q38 "방금 다뤘던 최적화랑 설계 요소들 모두 진행하자"(남은 항목 추천안 확정·구현 진행)에 따라 이 형태로 **적용 예정**이며, 승인 기록은 `decisions/cross-references.md` #21. 아래 타입·필드·이벤트·메뉴 id 이름은 프로듀서 제안이다 — 시스템·UI 구현 중 바꿀 필요가 생기면 이 절부터 고친다.
> 근거: 57라운드 Q22~Q37(빌드 축 1차), Q38(취기·2차 묶음 추천안 확정), 설계안 `decisions/design-2026-10-04-build-axis.md`(1.4 세트·1.6 패시브·1.7 이중 개성·2.6 개성 3지선다 칸·4.2 저주), `design-2026-10-04-build-axis-chwigi.md`(QC-0 취기 상태 합침), `design-2026-10-04-second-bundle.md`(a 보상 미리보기 · b 위험 노드 · d 숨은 노드·지도 정보 · e 상점 진열 · f 성소·성과 등급 · g 엘리트 · i 소모품).
> 공통: 새 필드는 시스템이 채우기 전까지 빈 기본값(`null` / `[]` / `false`)이다. 이름·문장·설명은 전부 **자리표시**(스토리 확정 전, §9.8 과 같은 원칙) — UI 는 받은 문자열을 그대로 그린다. 1층 단계(57 Q23): 2단 갈래·각성은 무기 시험장에서만 실제로 나온다(실제 런에서는 해당 값이 비거나 잠김).

### 14.1 태그·세트 (`UiSnapshot.build`)
```ts
type UiTagId =                 // 10태그 (57 Q24). 이름(name)은 자리표시
  | 'insight'   // 간파 — 완벽 성공(패링·퍼펙트 가드·완벽 놓기·완벽 회피)
  | 'breach'    // 돌파 — 이동기
  | 'vital'     // 급소 — 치명
  | 'scar'      // 상흔 — 출혈·화상
  | 'chain'     // 연쇄 — 처치
  | 'ranged'    // 원격 — 투사체·충격파
  | 'weight'    // 중량 — 강공
  | 'mark'      // 표식 — 표식·낙인
  | 'endure'    // 버팀 — 위기·피해 감소
  | 'drunk';    // 취기 — 1층 '잔' 테마 태그 (2층부터 층 테마 태그가 이 유니온에 추가된다)

interface UiTagState {
  id: UiTagId;
  name: string;              // '간파' 등
  score: number;             // 태그 점수 = 패시브 종류당 1 + Lv3 +1 + 갈래 노드 1(강화 시 최대 3) + 저주 이득 (57 Q25)
  stage: 0 | 2 | 4 | 6;      // 지금 켜진 세트 단계 (임계 2/4/6)
  next: number | null;       // 다음 임계 (6 달성이면 null)
  effects: { threshold: 2 | 4 | 6; name: string; description: string; active: boolean }[]; // 세트 효과 3칸
}
interface UiBuildState {
  tags: UiTagState[];        // score > 0 인 태그만, 점수 높은 순 (시스템 정렬)
  dualTraits: UiDualTrait[]; // 얻은 이중 개성 (14.2)
  curse: UiCurse | null;     // 지금 걸린 저주 (14.3, 동시 1개)
}
// UiSnapshot.build: UiBuildState
```
- **패시브 목록에 태그**: 기존 `UiSnapshot.passives[]` 항목에 `tags: UiTagId[]`(1~2개)·`maxLevel: number`(현행 3)를 더한다. 이중 개성은 태그 점수를 주지 않으므로 `passives` 가 아니라 `build.dualTraits` 에 둔다.
- 세트 단계가 바뀌면 이벤트 `TAG_SET_CHANGED`(14.11).

### 14.2 이중 개성 (`UiDualTrait`)
```ts
interface UiDualTrait {
  id: string; name: string; description: string;
  branchName: string;        // 짝 갈래 이름 (예 '선풍')
  tag: UiTagId;              // 짝 태그 (취기 짝 4종은 'drunk')
  tier: 1 | 2;               // 1단 짝(태그 2점) / 2단 짝(태그 4점)
}
```
- 조건을 채우면 다음 보상 3지선다 1칸에 확정 등장(57 Q27) — 그 칸은 메뉴 줄 `kind: 'dual'`(14.4).

### 14.3 저주 (`UiCurse`)
```ts
interface UiCurse {
  id: string; name: string;  // 1층 7종 (만취 서약·외상·깨진 잔·불붙은 혀·맨손 맹세·저주 궤짝·피멍), 자리표시
  benefit: string;           // 이득 한 줄
  penalty: string;           // 저주 한 줄
  nodesLeft: number | null;  // 남은 노드 수 (층을 넘어도 유지). 처치 수 기준 저주면 null
  killsLeft: number | null;  // 처치 수 기준 저주(저주 궤짝 '다음 12처치')만, 그 외 null
}
```
- 정화 없음·동시 1개(57 Q37). 노드 지도·HUD 노드 띠에 남은 노드 표시는 UI 판단.
- 저주를 받을 때(위험 노드 '저주 길' 2택, 이벤트, 구조물, 개성 '피의 계약' 칸)는 기존 메뉴 흐름 — 저주 2택은 새 메뉴 id `curse`(14.7).

### 14.4 메뉴 줄 종류 — 개성 3지선다 칸·보상 칸 (`UiMenu.lines[]` 확장)
```ts
type UiChoiceKind =
  | 'branchA' | 'branchB'    // 갈래 A / B (1단 임계 100, 2단 임계 200)
  | 'reinforce'              // 강화 (+15%, 갈래 태그 +1 최대 3. 각성 후 상한 5)
  | 'bloodPact'              // 피의 계약 (2단 이후 임계 200마다 셋째 칸 — 저주 1개, 이득 1.5배·지속 +1노드)
  | 'awaken'                 // 최종 각성 (조건 미충족이면 잠김)
  | 'dual'                   // 이중 개성 확정 칸 (보상 3지선다)
  | 'passive'                // 일반 패시브 선택
  | 'curse';                 // 저주 선택 (저주 2택)
interface UiMenuLine {
  // ...기존 key, label, enabled, detail?
  kind?: UiChoiceKind;
  tags?: UiTagId[];          // 이 선택이 주는 태그 (패시브·갈래 노드)
  rarity?: 'common' | 'rare' | 'epic' | 'legendary'; // 패시브 희귀도 (일반·희귀·영웅·전설)
  locked?: { condition: string } | null; // 잠긴 칸 — 각성 조건 안내 (예 '2단 + 그 2단 태그 6점 + 5층 보스 이후'). locked 면 enabled=false
}
```
- `evolve` 메뉴 칸 구성(27 Q4 · 57 Q37 · 설계안 2.6): 1단 임계 = [`branchA` / `branchB` / `reinforce`], 2단 임계 = [`branchA` / `branchB` / `reinforce`], 2단 이후 임계마다 = [`reinforce` / `bloodPact` / `awaken`](잠김이면 `locked`).
- 보상 3지선다(`reward`·`passive`)에 이중 개성이 대기 중이면 한 칸이 `kind: 'dual'`.

### 14.5 노드 지도 (`UiRouteNode` 확장 · `UiRoute` 확장)
```ts
type UiNodeRewardKind =      // 보상 미리보기 아이콘 7종 (설계안 a.1)
  | 'gold' | 'passive' | 'personality' | 'consumable' | 'statPoint' | 'curse' | 'unknown';
type UiNodeGrade = 'perfect' | 'good';   // 완(完) · 양(良)
interface UiRouteNode {
  // ...기존 id, type, name, col, row, links, state, region?, desc?
  reward: UiNodeRewardKind | null; // 공개된 보상. null = 아직 비공개(다음 단만 공개)·상점·휴식. 'unknown' = '?'(이벤트·숨김)
  risk: 'elite' | 'curse' | null;  // 위험 노드 (엘리트 길 / 저주 길, 1층 1개)
  riskText: string;                // 진입 확인('넘어가시겠습니까?')에 붙일 위험 한 줄. 위험 노드 아니면 ''
  prefixes: string[] | null;       // 엘리트 접두어 이름 (지도 정보로 공개된 경우만, 아니면 null)
  eventName: string | null;        // 이벤트 내용 이름 (지도 정보로 공개된 경우만)
  hidden: 'smudge' | 'located' | 'found' | null; // 숨은 노드: 얼룩만 / 위치 표시(지도 정보) / 조사로 길 열림. 일반 노드는 null
  grade: UiNodeGrade | null;       // 지나온 노드의 성과 도장
}
interface UiRoute {
  // ...기존 floor, nodes, currentId, choosing
  intel: { nextTier: boolean; fullFloor: boolean; hiddenLocated: boolean }; // 산 지도 정보 3품목
}
```
- 숨은 노드는 `hidden: 'smudge'` 동안 이어지는 노드의 `links` 에 들어가지 않는다(UI 는 얼룩만 그림). `found` 가 되면 `links` 에 들어가고 고를 수 있다.
- 지도 정보 구매: 국경 초소 '지도 장수' = 새 메뉴 id `mapInfo`(14.7), 상점 노드 = `shop` 메뉴 줄(`group: 'mapInfo'`, 14.6).

### 14.6 상점 진열 (`shop` 메뉴 줄 확장)
```ts
interface UiMenuLine {
  // ...14.4 확장 포함
  group?: 'fixed' | 'display' | 'reroll' | 'chest' | 'mapInfo'; // 고정 4칸 / 진열 3칸(패시브 2·소모품 1) / 리롤 / 궤짝 덤 / 지도 정보
  price?: UiCost;            // 가격 (§9.1 UiCost). 리롤은 15 → 25 → 35
  soldOut?: boolean;         // 팔림 (enabled=false)
}
```
- 리롤 줄은 상점 안 전표 리롤만(토큰 아님 — 57 Q38 충돌 처리). 리롤 뒤 같은 id 로 `MENU_OPEN` 을 다시 보낸다(§9.4 규칙).

### 14.7 새 메뉴 id
| id | 여는 때 | 줄 | `cancelKey` |
|---|---|---|---|
| `curse` | 저주 길 진입·이벤트 등 저주 2택 | `kind: 'curse'` 2줄 (`detail` = 이득·저주·지속) | 없음(필수) — 저주 길은 진입 확인에서 이미 동의 |
| `event` | 이벤트 노드 (1층 9종) · 저주 길 클리어 보상 2택(60라운드) | 선택지 + 마지막 줄 '지나간다'(`'0'`) — §9.4 구조물 메뉴 틀 | `'0'` |
| `mapInfo` | 국경 초소 지도 장수 | 3품목(`price`) + 그만두기 | `'0'` |
| `consumableSwap` | 소모품 칸이 찬 상태에서 다른 종류 획득 | '바꾼다' / '그대로 둔다' | 없음(필수) |
- `UiMenuId` 유니온에 위 4개를 더한다.

### 14.8 소모품 칸 (`UiSnapshot.consumable`)
```ts
interface UiConsumableSlot {
  key: string;               // 사용 키 이름 (시스템이 읽음 — 60라운드 Q27 확정 'C', 독주 Q 와 별개)
  item: { id: string; name: string; description: string; kind: 'throw' | 'drink'; count: number; max: number } | null; // 같은 종류 최대 2. 빈 칸이면 null
}
// UiSnapshot.consumable: UiConsumableSlot | null   (소모품 칸이 없는 모드면 null)
```
- 소모품 키는 시스템이 읽는다(§9.3 의 E 와 같은 방식). 투척은 누르면 커서 방향 즉시. UI 는 HUD 칸·키 안내만.

### 14.9 엘리트 이름표 (`UiSnapshot.elites`)
```ts
interface UiElite {
  id: string;
  name: string;              // 이름표 문구 (예 '불붙은 결사병', 자리표시)
  prefixes: string[];        // 접두어 (1층 1개)
  hp: number; maxHp: number;
  screen: { x: number; y: number }; // 머리 위 화면 좌표 (논리 960×540 px, 카메라 반영 — §9.1 screen 과 같은 규칙)
}
// UiSnapshot.elites: UiElite[]   (화면 안의 살아 있는 엘리트만)
```
- 외곽선·머리 위 문장 아이콘·접두어 fx 는 월드 그림(시스템·아트). 이 필드는 UI 가 이름표를 그릴 때 쓴다.

### 14.10 노드 성과 등급 · 진행 표시
```ts
interface UiNodeTrial {      // 잔 구간 전투·위험 노드 진행 중에만
  timeLimitMs: number;       // 1층 50000 (데이터 값)
  elapsedMs: number;
  hitTaken: boolean;         // 피격 있었음
}
// UiSnapshot.nodeTrial: UiNodeTrial | null
interface UiNodeGraded {
  nodeId: string;
  grade: UiNodeGrade | null; // null = 등급 없음
  noHit: boolean; inTime: boolean;
  deltas: { gold?: number; personality?: number }; // 받은 보상 (위험 노드 ×2 반영)
  text: string;              // 결과 문구 (자리표시)
}
```
- 노드 종료 시 `NODE_GRADED`(14.11) — UI 가 일기장 도장 연출. 지도에는 `UiRouteNode.grade` 로 남는다. 보상은 메뉴 없이 자동 지급(설계안 0.3-3).
- 도전 성소(C4 전장 깃발): `UiStructureKind` 에 `'warFlag'` 추가(E, 첫 웨이브 전 비전투에만), 시작·종료는 기존 `CHALLENGE_STARTED`·`CHALLENGE_CLEARED`(kind 에 `'warFlag'` 추가).
- **(60라운드 Q32)** `UiStructureKind` 에 `'clue'`(숨은 노드 단서 — E 로 살펴보기 → 지도에 길 공개), `'eventProp'`(이벤트 노드 소품 — E 로 이벤트 메뉴), `'mapSeller'`(국경 초소 지도 장수 — E 로 `mapInfo` 메뉴) 추가. 안내는 다른 E형 구조물과 같이 `UiSnapshot.interactable` 로 간다.
- **(60라운드 시스템 구현 메모)** UI 가 처리할 메뉴 id: `curse`(저주 2택, 저주 길 진입·피의 계약), `event`(이벤트 선택지, '0' 지나가기 / 저주 길 클리어 보상 2택도 이 id), `mapInfo`(지도 정보 3품목, '0' 닫기), `consumableSwap`(소모품 교체 '바꾼다/그대로 둔다', 필수 선택). 숨은 노드는 처음부터 지도에 있고 같은 단의 아래 줄에 `state: 'locked'`, `hidden: 'smudge'` 로 오며, 길이 열리면 갈라지는 노드의 `links` 에 들어간다. 엘리트 이름표는 UI 가 `UiSnapshot.elites` 로 그린다(아트 `elite_nameplate` 시트 사용, §14.9). 보스 파훼 결정타는 UI 이벤트가 아니라 시스템 내부 `BOSS_BREAK{kind:'finisher'}`.
- **(60라운드 시스템 구현 메모)** `UiRouteNode` 의 reward·risk·riskText·prefixes·eventName·hidden·grade 와 `UiRoute.intel` 은 이 절에서 필수지만, 기존 UI 코드·테스트가 이 필드 없이 노드를 만들어 코드(`src/contract/ui.ts`)에서는 임시로 선택(`?`)이다. 시스템은 늘 채운다. UI 가 테스트를 고친 뒤 필수로 되돌린다.

### 14.11 이벤트 (시스템 → UI)
| 이벤트 | 값 | 페이로드 | 시점 |
|---|---|---|---|
| `TAG_SET_CHANGED` | `'ui:tag-set-changed'` | `{ tag: UiTagId; name: string; stage: 0 \| 2 \| 4 \| 6; effectName: string }` | 세트 단계가 오르거나 내림 |
| `DUAL_TRAIT_GAINED` | `'ui:dual-trait-gained'` | `UiDualTrait` | 이중 개성 획득 |
| `CURSE_GAINED` | `'ui:curse-gained'` | `UiCurse` | 저주 받음 |
| `CURSE_ENDED` | `'ui:curse-ended'` | `{ id: string; name: string }` | 저주 기간 끝 |
| `NODE_GRADED` | `'ui:node-graded'` | `UiNodeGraded` | 성과 등급 노드 종료 |
| `HIDDEN_NODE_FOUND` | `'ui:hidden-node-found'` | `{ nodeId: string }` | 단서 조사로 숨은 길 열림 |
| `PERFECT_SUCCESS` | `'ui:perfect-success'` | `{ kind: 'parry' \| 'perfectGuard' \| 'perfectRelease' \| 'perfectEvade' }` | 완벽 성공 사건 (완벽 회피 = 적 공격 판정 직전 0.15초 안 대쉬·그림자 걸음, 57 Q28) |
| `CONSUMABLE_USED` | `'ui:consumable-used'` | `{ id: string; name: string; left: number }` | 소모품 사용 |
- 월드 문구: '완벽 회피' 표시는 §13 'PERFECT GUARD'·'PARRY' 와 같은 방식(시스템 월드 텍스트)을 제안. UI 는 `PERFECT_SUCCESS` 를 HUD 연출(예: 간파 세트 진행)에만 쓴다.
- 기존 `STATE` 스냅샷으로 모든 값이 매 프레임 오므로 위 이벤트는 연출용이다(구독 선택).

### 14.12 그 밖 (이번 초안 범위 밖 — 다음 인터뷰 후보)
- 취기 상태(QC-0 합침): HUD 상태 `drunk`(§9.2)를 그대로 쓰고, 세트 2 '한 잔'의 취기 상태 5초는 `remainMs`/`durationMs` 를 채우는 안 — 형태만 메모, 확정은 시스템 구현 때.
- 보스 파훼 결정타 이벤트·결과 표시, 이벤트 E4 '일기장의 빈 쪽'의 갈래 트리 미리보기 데이터, 저주 남은 노드의 노드 띠 표시 방식 — 별도.

- **(60라운드 Q39)** §14.9 `UiElite.screen` 은 엘리트 **머리 꼭대기** 화면 좌표. UI 는 그 37px 위(문장 pivot + 64도트)에 이름표를 둔다.

## 15. 설정 (61라운드 P10)
```ts
interface UiSettings {
  shake: number;          // 화면 흔들림 배율 0~1 (기본 1)
  flash: boolean;         // 섬광(피격·결정타 화면 번쩍임) 켜기 (기본 true)
  tilt: boolean;          // 보스 '세상이 돈다' 화면 기울기 켜기 (기본 true)
  damageNumbers: boolean; // 피해 숫자 표시 (기본 true)
  master: number;         // 전체 음량 0~1
  bgm: number;            // 배경음 0~1
  sfx: number;            // 효과음 0~1
}
```
- UI 가 설정 화면(일시정지 메뉴의 한 항목, 타이틀에서도 열림)을 그리고 값을 바꾼다. 시스템 명령 `setSettings(s: UiSettings)` 로 넘기고, 시스템은 즉시 적용(카메라 흔들림 배율·섬광·기울기·피해 숫자·음량 버스)한다. 저장은 시스템 세이브(메타 영역)에, 부팅 때 `UiSnapshot.settings` 로 UI 에 알려 준다.
- 기존 §11.3 `setMuted` 는 유지(`master` 0 과 별개의 빠른 음소거).

## 16. 무기 4동사 (61라운드 P1)
- 스냅샷 `weaponVerbs: UiWeaponVerbs` — 현재 무기의 4칸(`UiVerbSlot`: 좌 연격 · 우 시그니처 · Space 대쉬(+대쉬 공격) · 좌 홀드 고유 기술)마다 `UiWeaponVerb`(키 이름·동작 이름·한 줄 설명). 1단 갈래는 동작을 **더하지 않고 같은 칸의 기본 동작을 대신**하므로 갈래를 얻으면 해당 칸 이름이 바뀐다. 정확한 필드는 `src/contract/ui.ts` 가 기준.
- 함께 바뀐 표시: `carry` 는 늘 null(F 넣기/뽑기 삭제), 단검 `resource` 는 null(가속은 숨김, 보이는 자원은 낙인), 활 `gauge`(숨)는 저격 갈래일 때만. 튜토리얼에 '좌클릭 길게' 단계(`PLAYER_HOLD_VERB` 로 완료).
- **(61 시스템 구현)** 기본값 상수 `UI_DEFAULT_SETTINGS`, `UiSnapshot.settings` 는 필수(타이틀 등 게임 씬이 없을 때도 저장값). 메타 세이브 키 `lopad.meta.settings`.
- **(61 시스템 구현) 메뉴 줄 표기 규칙**: `UiMenuLine.label` 에는 가격·희귀도·내부 id 를 넣지 않는다. 가격은 `line.price`(`label` 포함), 희귀도는 `line.rarity`, 선택 값 `line.key`(`d1`·`reroll`·`m:<id>` 등)는 그리지 않고 UI 가 번호 단축키로 보여 준다. 등급 노드의 보상 메뉴는 평가 카드 뒤 1.6초(`GRADE_CARD_HOLD_MS`)에 열린다. 튜토리얼 패널은 기존 `pause()`/`resume()` 사용.

## 17. 서사 표시·보스 UI (61라운드 단계 2·3)
- `STORY.kind`: `voice`(원한의 한마디 — `weapon`, 화자 이름 없음), `speech`(군주 대사 — `speaker`), `clue`(조사 기록 — `lines` 여러 줄, Enter·Esc·클릭으로 닫음, 게임 멈추지 않음), `event`(이벤트 문장). 선택 필드 `holdMs`·`scene`·`title`. UI 는 STORY 를 큐로 한 차례씩 띄운다(보스 앞 '한마디 → 등장 자막 → 군주 대사').
- `UiResult.smudgeLine`: 사망 결과 화면의 이름 번짐 문구.
- 이벤트 `UI_EVENTS.BOSS_BREAK` = `'ui:boss-break'` `{ kind: 'cup'|'pillar'|'cask'|'stumble'|'finisher'; label?; text? }`, `UI_EVENTS.ENEMY_INTRO` = `'ui:enemy-intro'` `{ id?; name; desc? }`, `BOSS_DIED.finisher?: boolean`.
- 스냅샷 `boss` 선택 필드: `phaseName`·`phaseNames`·`phaseMarks`(체력 비율 눈금), `broken`(boolean 또는 `{leftMs,totalMs}`), `candles: {x,y,lit}[]`(논리 960×540 화면 좌표), `dark`.
- (확인, 61 단계 2·3 C1) `ENEMY_INTRO` 페이로드 = `{ id, name, desc }` — 위 `UI_EVENTS.ENEMY_INTRO` 와 같은 이벤트(C1 에서 추가). `id`·`desc` 는 선택 필드로 유지.
- (확인) 상점 상인의 E 상호작용 안내는 당분간 기존 kind `'mapSeller'` 를 재사용한다(상점 전용 kind 는 아직 없음 — 추가하면 이 줄을 고친다).
- 보스 처치: UI 는 처치 카드·처치 대사가 끝날 때까지(최대 4.5초) 보상 메뉴를 기다린다. 시스템이 연출 뒤 메뉴를 열면 그 순서를 따른다.

### 17.1 (61 단계 4) 보스 포효·UI 색 고정
- 이벤트 `UI_EVENTS.BOSS_ROAR` = `'ui:boss-roar'` `{ name }` — 등장 연출의 포효 프레임(현재 3.8초)에 한 번. UI 는 보스 이름 카드를 이 순간 띄운다(BOSS_STARTED 즉시 띄우지 않음). `introMs` 가 0 이면 시스템이 BOSS_STARTED 직후 바로 낸다.
- UI 색: 체력 막대는 항상 붉은색, HUD·메뉴 테두리·글자색은 기본 팔레트 하나로 고정 — 층 테마(`theme`·지역 색)로 바꾸지 않는다. 스냅샷에 테마 값이 와도 UI 는 색에 쓰지 않는다.
