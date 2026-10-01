# 게임 시스템 파트 — 작업 기록

## 1단계 프로토타입 (2026-10-01)
기획서 11장 1단계 "사각형 캐릭터가 이동·공격하고 적 1종을 처치" 구현. 결정은 `parts/producer/decisions/2026-10-01-round-05/06-*.md`.

### 구성
| 경로 | 내용 |
|---|---|
| `src/main.ts` | 진입점. 창 크기에 맞는 정수 배율로 캔버스 확대 |
| `src/config.ts` | Phaser 설정 (640×360, pixelArt, Arcade 물리) |
| `src/core/Constants.ts` | 엔진·화면·연출 상수 (게임 수치는 data/) |
| `src/core/EventBus.ts` | 이벤트 버스 + 이벤트 상수 |
| `src/core/GameState.ts` | 런 상태 + `reset()` |
| `src/data/types.ts`, `src/data/index.ts` | `data/*.json` 타입과 로더(런타임 검증) |
| `src/systems/InputSystem.ts` | WASD 이동, 좌클릭 공격(커서 방향), R 재시작 → `InputState` 추상화 |
| `src/systems/Combat.ts` | 전투 수식 (방어력 평면 차감, 임시) |
| `src/objects/Player.ts`, `src/objects/Enemy.ts` | 사각형 플레이스홀더 엔티티 |
| `src/scenes/*` | Boot → Preloader → Game → GameOver(플레이스홀더) |
| `data/player.json`, `data/enemies.json` | 플레이어 스탯, 적 정의 |

### 실행
```
npm install
npm run dev        # http://localhost:8080
npm run typecheck  # tsc --noEmit
npm run build
```

### 검증 (2026-10-01)
- `tsc --noEmit` 통과, `vite build` 통과
- 헤드리스 Chromium(1280×720)에서 실행: 콘솔 오류 0, 2배 정수 확대, 이동·공격·처치·피격·HP 감소 확인

### 이 파트가 임시로 둔 것 (UI·아트 파트 산출물로 교체 예정, 교체는 승인 절차 후)
- `[DEBUG]` 텍스트 — HUD가 아님. HUD는 UI 파트
- `GameOver` 씬 — 결과 화면 플레이스홀더. 정식 화면은 UI 파트
- 사각형 색상 — 스프라이트는 아트 파트

### 다음 인터뷰 후보
- 테스트 러너(vitest) 도입 여부 (데이터 검증·전투 수식 단위 테스트)
- 2단계 "핵심 루프" 범위: 무작위 맵 1층 + 보스 + 사망/재시작
- 대쉬·패링 입력과 타이밍

## 2단계 핵심 루프 (2026-10-01)
기획서 11장 2단계 "무작위 맵 1층 + 보스 + 사망/재시작". 결정은 `decisions/2026-10-01-round-08/09-*.md`.

### 구성
| 경로 | 내용 |
|---|---|
| `src/systems/rng.ts` | 시드 난수 (mulberry32) |
| `src/systems/mapgen/` | 순수 TS 맵 생성기: `layout.ts`(셀 격자 배치) → `tiles.ts`(타일 래스터화·문) → `index.ts`(`generateFloor(seed, params)`) |
| `src/world/TileWorld.ts` | Phaser 타일맵 올리기, 벽 충돌, 문 상태(open/closed/locked), 좌표 변환 |
| `src/systems/RoomDirector.ts` | 방 상태 머신: 시련(잠금→웨이브→해제), 휴식(회복), 보스(해금→전투→클리어) |
| `src/objects/Mob.ts` | 적·보스 공통부 (접촉 공격 주기, 피격, 플래시) |
| `src/objects/Enemy.ts` | chase / ranged / charge 행동 |
| `src/objects/Boss.ts` | 페이즈·돌진·벽 경직·부채꼴 투사체 |
| `src/objects/Projectile.ts` | 적 투사체 풀 |
| `src/scenes/Preloader.ts` | 플레이스홀더 타일 텍스처를 코드로 생성 |
| `src/scenes/Game.ts` | 카메라(방 고정 / 보스 추적), 전투 배선, 디버그 텍스트 |
| `src/debug/index.ts` | `?debug=1` 검증 훅 (게임 로직 아님) |
| `data/stages.json`, `data/bosses.json`, `data/enemies.json` | 층 구성·보스·적 3종 |

### 검증 (2026-10-01)
- `npm run test` 12개 통과 (맵 생성: 방 구성·결정성·도달 가능성·거리 제약·보스 문·벽 밀폐 / 전투 수식 / 데이터 검증)
- `npm run lint`, `npm run typecheck`, `npm run build` 통과
- 헤드리스 Chromium + `?debug=1` 훅으로 전체 루프 확인: 시련 4개 진입 시 문 닫힘 → 웨이브 1·2 → 클리어 시 문 열림 → 4개 후 보스 문 해금 → 휴식 → 보스전(문 닫힘, 2페이즈 진입, 플레이어 피격) → 클리어 화면. 콘솔 오류 0.

### 다음 인터뷰 후보 (3단계)
- 대쉬·패링 입력·타이밍, 대쉬 공격
- 무기 개성 시스템과 기본 무기 1종 (현재 공격은 범용 히트박스)
- 스테이지 2 이후 확장, 스테이지 전환 세이브(최대 2회)
- 감각 수치 획득 규칙, 상점·골드
- 열린 구조 + 미니맵 → UI 파트 개시 필요 (교차 참조 승인 대상)

## 3단계-a 전투 행동 (2026-10-01)
결정: `decisions/2026-10-01-round-11-stage3-kickoff.md`.
- `src/objects/Player.ts`: 상태 머신 normal / dash / parry / recover. 대쉬(무적·고정 속도), 패링 창, 실패 후딜, 대쉬 공격 판정.
- `src/objects/Mob.ts`: `stun()` — 패링 성공 시 경직. 돌진병·보스는 경직 시 패턴 리셋.
- `src/objects/Projectile.ts`: `reflect()` — 패링된 투사체는 방향 반전 후 적에게 데미지.
- `src/systems/senses.ts`: 감각 적립 (처치 방식 3분류, 스테이지마다 초기화). 테스트 2개.
- 검증(헤드리스): 대쉬 48px 이동·dash 상태, 투사체 패링 시 피해 0, 실패 시 recover, 접촉 패링으로 적 경직, 대쉬 공격 8 데미지(5×1.5), 감각 +1. 콘솔 오류 0.

## 3단계-b 무기 개성 1차 (2026-10-01)
결정: 11라운드 Q4, 임시값은 `decisions/2026-10-01-round-11b-weapon-notes.md`.
- `data/weapons.json`, `src/systems/weapons.ts` (`WeaponState`: 개성 누적·진화·히트박스/데미지 배율, 테스트 3개)
- 처치 → `personalityValue` 누적 → 100 달성 시 진화, 베기 궤적 이펙트와 임시 알림 텍스트
- 검증(헤드리스): 14처치 후 '거합' 진화, 진화 후 1타 6 데미지(5×1.2). 콘솔 오류 0.

## 3단계-c 스테이지 확장 (2026-10-01)
결정·임시값: `decisions/2026-10-01-round-12-stage-expansion.md`.
- `data/stages.json`: `run.order` 7개 스테이지, `run.maxSaves`, 스테이지별 `enemyScale`·웨이브·시련 수. `data/bosses.json`: 보스 변형 6종 + `final`(3페이즈, 연속 돌진 `repeat`).
- `src/core/GameState.ts`: `startRun / nextStage / toSave / applySave`, 층 시드 = 런 시드 + 층 번호.
- `src/systems/save.ts`: `SaveSlot` (localStorage 추상화, 테스트 3개).
- `src/scenes/Game.ts`: `init(mode)` new/next/resume, 출구 타일 진입 시 `scene.restart({mode:'next'})`, 전환 세이브, 사망·클리어 시 삭제.
- 검증(헤드리스): 1→7층 전환, 세이브 2→1→0, 재진입 이어하기(2층 시작, HP 83), 2층 더미 HP 24, 최종 보스 3페이즈 진입, 런 클리어 후 세이브 null. 콘솔 오류 0.

### 다음 인터뷰 후보
- 감각 → 스테이지 클리어 능력치 보상 규칙 (BLANK)
- 골드·상점·소모품·패시브 (기획 6장)
- 개성 선택 연출(런 시작 시 무기 결정), 무기 추가
- 메타 진행: 무기 도감, 영혼 토큰 (기획 3장)
- 경쟁 모드

## 3단계-d 경제 (2026-10-01)
결정·임시값: `decisions/2026-10-01-round-13-economy.md`.
- `data/economy.json`(골드·드랍·희귀도·상점·능력치 보상·치명타 배율), 적·보스 `gold`
- `src/systems/economy.ts`(골드 굴림, 상점 가격, 보상 적용, 치명타 판정, 테스트 4개), `src/objects/Pickup.ts`(바닥 드랍 풀), `src/systems/TextMenu.ts`(임시 숫자 키 메뉴)
- `Game.ts`: 처치 드랍 → 접촉 획득, 시련 +15 / 보스 +50, Q 물약, 보스 처치 후 감각 포인트 선택 → 출구·상점 타일, 상점 구매, 세이브 v2
- 검증(헤드리스): 드랍 4개 획득(골드 10, 물약 1), 시련 보너스, 물약 사용(HP 50→80), 보상 선택(최대 HP 110), 상점 회복·물약·감각 구매와 포인트 선택, 타일 이탈 시 닫힘, 2층 전환 시 골드·물약·보너스 유지 및 세이브 v2. 콘솔 오류 0.

### 남은 시스템 파트 후보
- 개성 선택 연출(런 시작 시 무기 결정), 무기 추가, 패시브
- 메타 진행: 무기 도감, 영혼 토큰 (기획 3장)
- 경쟁 모드, 치명타 데미지 스탯 연결, 장비 구매

## 3단계-e 무기 4종·개성 선택 (2026-10-01)
결정·임시값: `decisions/2026-10-01-round-14-weapons-personality-meta.md`.
- `data/weapons.json`(대검·단검·활 추가, 성향 벡터), `data/personality.json`, `src/systems/personality.ts`(획·리듬 특징 추출, 가중 거리 선택, 테스트 6개)
- `src/scenes/Setup.ts`: 3획 → 5초 리듬 → '운명' 표시 → Game(new, weapon). Preloader 가 세이브/`?weapon=` 여부로 분기, 사망 후 재시작은 Setup 으로
- `Game.ts`: 활 투사체(`playerShots`, 연사 감쇠, 관통), 무기 치명타 보너스, 공격 중 감속, 진화 이펙트(충격파·쌍격·관통)
- 검증(헤드리스): 큰 직선 획 + 공격 위주 리듬 → 대검 선택, 무기별 피해 5/11/3/5, 활 연사 2발째 4, 관통 진화. 콘솔 오류 0.

## 3단계-f 메타 진행 (2026-10-01)
- `data/meta.json`, `src/systems/meta.ts`(영혼 산식, 도감 누적, 강화 구매·비용, 보너스 환산, 저장소; 테스트 5개)
- 런 종료(사망·클리어) 시 `settleRun` 1회 정산 → 결과 화면에 영혼 표시. 런 시작 시 `gameState.meta` 보너스(최대 HP·공격·방어·대쉬 쿨·물약 소지) 적용
- Setup 씬 첫 단계: 영혼·강화 구매·도감 요약 메뉴, Enter 로 개성 선택
- 검증(헤드리스): 2층 도달·15처치·진화 1 후 사망 → 영혼 55, 도감 기록; 재시작 메뉴에서 최대 HP 구매(30) → 다음 런 최대 HP 105, 영혼 25. 콘솔 오류 0.

## 3단계-g 패시브 (2026-10-01)
결정: `decisions/2026-10-01-round-15-passives.md`.
- `data/passives.json`, `src/systems/passives.ts`(레벨 누적 효과 합계, 희귀도 가중 3지선다, 복원; 테스트 5개)
- 효과 연결: 방어력·이동 속도·공격 배율·저체력 배율·패링 창·반사 배율·대쉬 쿨·대쉬 공격·개성 획득·처치 회복
- 보스 보상 체인: 감각 포인트 선택 → 패시브 3지선다 → 출구·상점. 세이브 v3 에 패시브 포함
- 검증(헤드리스): 강철 피부로 방어 5, 흡혈로 3처치 후 HP +6, 보스 후 체인 동작, 2층 전환 시 패시브 유지·세이브 v3. 콘솔 오류 0.

### 시스템 파트 현황 (2026-10-01 기준)
완료: 프로토타입, 핵심 루프(7층), 전투 행동, 무기 4종·개성 선택, 경제(골드·상점·물약), 감각 보상, 메타 진행, 패시브.
남은 후보: 경쟁 모드, 치명타 데미지 스탯 연결, 장비 구매, 스토리 개연성 방·개성 조회 방(스토리·UI 파트 개시 필요), 밸런스 패스.

## UI 계약 어댑터 (2026-10-01, 16라운드)
- `src/contract/ui.ts`(계약 공개면: 이벤트·스냅샷 타입·`uiCommands`·시스템 전용 `__system`), `src/contract/snapshot.ts`(스냅샷 생성, 테스트 1개), `src/contract/host.ts`(씬 제어·세이브 명령 구현)
- `TextMenu` 는 브로커가 됨: UI 렌더러 등록 시 MENU_OPEN/CLOSE 이벤트 + UI 메뉴 씬 실행, 아니면 임시 텍스트
- Game: 매 프레임 STATE 스냅샷 발행, HUD 병렬 실행, 피격·회복·골드·진화·보스·방 진입 이벤트 중계, 결과 화면을 UI 결과 씬으로. Setup: 메타 메뉴를 계약 메뉴로
- 시스템 디버그 텍스트는 `?debugtext=1` 일 때만 표시

## 스토리 반영 (2026-10-01, 26라운드)
교차 참조 승인 #3: `parts/producer/contracts/story-text.md` 만 참조.
- `data/story.json`(계약 JSON 복사), `src/data/types.ts` `StoryData`, `src/data/index.ts` `STORY` 검증, `src/systems/story.ts`(`fill`·`floorText`·`evolutionLine`·`deathLine`, 테스트 3개)
- 8층 구조: `data/stages.json` `stage8`(황제의 수도) 추가, `data/bosses.json` `emperor`(구 `final`)·`stage7` 변형, 보스 이름을 계약 이름으로
- 일기장 이름 입력: `Setup` 씬 메타 메뉴 → `name` 단계(DOM input 12자) → 3획 → 운명. `GameState.playerName`, 세이브 v4
- 자막: `UI_EVENTS.STORY` 로 층 진입·휴식 방 첫 진입·시련 시작/클리어·본영 해금·보스 개시·개성 변화·세이브 알림 발행. HUD 층 제목·재화 이름은 스냅샷 `floorTitle`·`names` 로 전달. 상점 제목·품목 이름도 계약 이름 사용
- `public/style.css`: 가운데 정렬을 Phaser autoCenter 로 (DOM 컨테이너 정렬)
- 검증(헤드리스): 이름 입력 → 운명 → 1층 제목·전표·잔의 독주 표시 → 휴식 방 자막 → 1~8층 전환(보스 이름 7종) → 세이브 v4 playerName → 황제 '평(平)' 800 → 클리어 결과 문장. 콘솔 오류 0.

### 시스템 파트 현황 (갱신)
완료: 위 전부 + 8층·스토리 텍스트 연결·이름 입력.
남은 후보: 엔딩 분기 2종(없앤다/이해한다), 개성 분기 트리·강화 선택지(25라운드), 무기별 우클릭 보조 동작, 경쟁 모드, 밸런스 패스.

## 27라운드 반영: 우클릭 보조 동작 4종 · 개성 분기 트리 2×2 · 강화 선택지 (2026-10-01)
결정: `decisions/2026-10-01-round-27-secondary-and-branches.md` (임시값은 그 파일 끝 "시스템 반영 기록").
- `data/weapons.json`: `{ rules: { reinforceBonus, reinforceMax }, weapons: {...} }` 로 재구성. 무기마다 `secondary: { kind, name, ... }`(parry / guard / shadowstep / aimedshot) 와 `personality: { thresholds: [100, 200], branches: [A, B] }`, 각 1차 노드는 `next: [A1, A2]`. 노드 = `{ id, name, description, damageMult, hitboxMult, mods }`. `mods` 는 효과 키 묶음(`src/data/types.ts` `WeaponMods`)이며 경로를 따라 병합(뒤 노드가 덮어씀), `damageMult`·`hitboxMult` 는 곱.
- `src/systems/weapons.ts` `WeaponState`: `path`(선택 id 경로)·`reinforce`·`choicePending`. 임계 도달 → `choicePending`(게이지 정지) → `choose(id)` / `reinforceNow()`. 강화 = 피해·범위 ×(1 + 0.15 × 횟수), 최대 3. 2차 완료 + 강화 3회면 `canEvolve` false 로 게이지 정지. 테스트 5개.
- `src/systems/InputSystem.ts`: 우클릭 `secondaryPressed / secondaryHeld / secondaryReleased`.
- `src/objects/Player.ts`: 상태 `guard`(유지, 피해 감소·감속, 떼면 `PLAYER_GUARD_RELEASED`) · `aim`(유지, 차지 완료 시 `aimed` 공격 자동 발사, 먼저 떼면 취소) · 그림자 걸음(`PLAYER_SHADOW_STEP` → Game 이 목적지 결정, `primeMs` 안의 다음 공격 1회 확정 치명). 공격 페이로드에 `forceCrit`. 무기 mods 로 대쉬 쿨·무적 연장·대쉬 공격 배율·확정 치명·이동 속도 반영.
- `src/objects/Mob.ts`: `knockback()`(AI 정지, 속도 유지), `stun(…, source)` 로 패링 경직과 타격 경직 구분(`isParryStunned` 가 감각 '패링 처치' 분류). `src/objects/Projectile.ts`: `homingTurn`·`steerToward`, `hitStunMs`, 무한 관통(`Infinity`).
- `src/scenes/Game.ts`: 3지선다 메뉴 `evolve`(변환 A / 변환 B / 강화)를 `update` 에서 `choicePending && !menu.isOpen` 일 때 연다(보스 보상 체인 뒤로 자연 순연). 열려 있는 동안 `frozen` + `physics.world.pause()`. 효과 연결: 타격 횟수(쌍격·난무), 충격파 2단(지진), 투사체 소멸(분쇄), 적중 경직(중압), 출혈·잔월(update 에서 틱 처리 — 정지와 함께 멈춤), 잔상(대쉬 경로 판정), 가드 반격(철벽), 슈퍼아머 근사(거인), 산탄·폭우 부채꼴, 섬광 속도·무한 관통, 중시 조준 사격 배율·경직, 추적 유도.
- 세이브 v5: `weapon: { id, personality, path, reinforce, choicePending }`. 도감 `maxStage` = 경로 길이(0~2), `evolutions` = 경로 노드 이름 (의미 유지).
- 계약: `src/contract/ui.ts` `UiMenuId` 에 `'evolve'` 추가(승인 필요). 스냅샷 `weapon.secondaryName` 은 무기별 이름, `threshold` 는 현 단계 임계.
- 디버그 훅: `setPersonality(v)`, `weapon()`, `playerExtra()`, `ui().continueRun()/hasSave()`.
- 검증: 테스트 48개(기존 44 + 변경 반영), lint·typecheck·prettier·build 통과. 헤드리스(`?debug=1&new=1&weapon=`): 패링 상태 진입 / 가드 중 피해 20→5(70% 감소, 비가드 17), 가드 이동 11px vs 29px, 해제 시 적 19px 밀려남 / 그림자 걸음으로 가장 가까운 적 뒤로 이동·다음 타격 5(확정 치명, 비치명 3)·2초 쿨 / 조준 사격 0.6초 차지 후 11 피해·무한 관통, 조기 해제 취소 / 개성 100 → `evolve` 메뉴(정지, 이동 불가) → 거합 → 200 → 잔월 → 강화 ×2(피해 1.56, 범위 43.68) → 잔월 지속 피해 3틱 → 보스 보상 체인 후 2층 세이브 v5(path·reinforce) → 이어하기 복원 → 강화 3회 후 게이지 정지. 폭우 5발, 난무 3타, 중압 경직. 콘솔 오류 0.

## 29라운드 반영: 아트 산출물 연동 (스프라이트·타일셋·팔레트 스왑) (2026-10-01)
계약: `parts/producer/contracts/art-assets.md`. 임시값은 `decisions/2026-10-01-round-29-autonomous-demo.md` "C. 시스템 스프라이트 연동 임시값".
- **서빙**: `vite.config.ts` 플러그인 `lopad-game-assets` — dev 는 `/assets-game/<경로>` → `assets/<경로>`, build 는 `assets/**` → `dist/assets-game/**` 복사. 양쪽 다 `assets-game/manifest.json`(존재하는 파일 목록)을 제공해 로더가 **404 없이** 있는 파일만 요청한다. 해시 번들 `dist/assets/` 와 분리, base `./` 유지(상대 경로). `@types/node` devDependency 추가(플러그인 타입).
- **로더** `src/scenes/Preloader.ts`: manifest → 시트·타일셋 JSON → PNG(`load.spritesheet` / `load.image`) → `anims.create`. 로드 대상은 `src/systems/spriteDefs.ts`(주인공 6동작, 적·보스 id 별 5동작 — id 는 `data/enemies.json`·`bosses.json` 키). 없는 파일은 건너뛰고 `loaderror` 는 무시. 애니 키 `<이름>_<동작>_<방향>`, 프레임별 `frameDurationsMs` 를 Phaser 프레임 `duration` 으로 그대로 사용, `repeat: loop ? -1 : 0`.
- **엔티티** `src/objects/EntityVisual.ts`(조합): 시트가 있으면 원점 = 피벗(발), 바디는 발밑(가로 중앙·아래 끝 = 피벗 행), 발밑 타원 그림자(알파 0.35, 깊이 0.9), 깊이 = `entityDepth(y)`; 없으면 흰 사각형 텍스처 + 틴트(기존 플레이스홀더). `Player`·`Mob` 은 `Phaser.GameObjects.Sprite` 로 전환(`Rectangle` API 제거: `setFillStyle` → `visual.paint/flash/restore`).
  - 플레이어: 정지 idle(마우스 조준 방향) / 이동 walk(이동 방향) / 공격 attack(조준 방향, 무기 `cooldownMs` 에 맞춰 재생) / 대쉬 dash(`durationMs` 에 맞춤) / 피격 hurt(2프레임 뒤 복귀) / 사망 death(끝 프레임 유지, `deathAnimMs + 400ms` 뒤 결과 화면).
  - 적·보스: `Mob.update` 가 `think()` 뒤 속도로 idle/walk·방향을 정한다. 접촉 공격·사수 발사·결사병 예고·보스 예고/부채꼴에 attack. 사수는 attack 시트 2번째 프레임(총구 화염)에 맞춰 투사체 생성(`impactDelayMs`). 사망 시 시체 스프라이트가 death 재생 → 0.5초 유지 → 0.6초 페이드.
- **팔레트 스왑** `src/systems/palette.ts` + `data/palette.json`(아트 팔레트 사본): 층 진입 시 `spriteLibrary.activate(scene, floor)` 가 1층 램프 12색 → 현재 층 램프로 치환한 캔버스 텍스처(`sheet_<id>@f<n>`)와 애니(`<키>@f<n>`)를 만든다. 1층은 치환 없음.
- **타일셋** `src/world/tileskin.ts`: `tiles`(ID → 인덱스, 변형은 좌표 해시), `walls`(아래가 열려 있으면 top, 그 외 bottom/left/right/corner), `props`(방당 2~5개, 시드 결정적, 문 반경 2·시작 지점 반경 2·보스 방 출구/상점 자리 제외, 단단한 소품은 벽가 테두리에만) → `TileWorld` 가 바닥 레이어 + 소품 오버레이 레이어(깊이 0.5, 단단한 소품 충돌·스폰 회피). 타일셋이 없는 층은 플레이스홀더 항등 매핑.
- **디버그**: `__lopad.sprites()`(시트·애니 키·변형), `player()` 에 `anim`·`dir`·`animated`, `mobs()` 에 `anim`, `world()`(타일셋·소품 수), `propAt`, `nextStage()`.
- 테스트 13개 추가(팔레트 치환, 시트 키·프레임·길이, 타일 변형·자동타일·역매핑, 소품 결정성·제외 규칙). 전체 61개.
- 검증(헤드리스, `vite preview`): 21시트·84애니 로드, 매니페스트로 요청 45건 전부 200. idle 이 조준 방향(left/up), walk 가 이동 방향(right/down), attack_right, dash_left, hurt → idle 복귀, 1층 아트 타일셋(벽 정면/윗면, 소품 27개, 바닥 ID 1·벽 ID 2), 더미 walk/hurt 애니·시체, 2층 변형 `@f2`(플레이어 크롭 픽셀: 1층 호박 4·녹색 0 → 2층 호박 0·녹색 4), death_right@f2 후 결과 화면. 콘솔 오류·경고 0.

## 29라운드 반영 (2): 무기 오버레이·공격 이펙트·엔딩 2종 (2026-10-01)
계약: `parts/producer/contracts/art-assets.md` §3·§3.1. 임시값은 `decisions/2026-10-01-round-29-autonomous-demo.md` "H. 시스템 무기 이펙트·엔딩 임시값".
- **로더** `src/systems/spriteDefs.ts`: 분류 `weapons`(무기 id 별 `attack`) · `fx`(`sprites/fx/<이름>.json`, 내부 동작 이름 `fx` 로 고정 → sheetId `<이름>_fx`, 애니 키 `<이름>_fx_<방향>`). `fxSheetIds(WEAPONS)` 가 데이터에서 이펙트 목록을 유도(근접 `<id>_slash`, 원거리 `<id>_arrow`·`<id>_arrow_aimed`, 1차 진화 노드 id 전부). `directions: ["any"]` 는 1행이며 네 방향 키가 모두 0행을 가리킨다. Preloader 는 요청 쪽 동작 이름을 쓴다(JSON `action` 이 파일 이름과 달라도 무관). 팔레트 스왑(`@f<n>`)은 무기·이펙트 시트에도 그대로 적용.
- **무기 오버레이** `src/objects/WeaponOverlay.ts`: 플레이어가 `player_attack_<방향>` 재생 중일 때만 `weapons/<무기id>_attack` 의 **같은 열(프레임 번호)** 을 플레이어 피벗에 겹친다(별도 Sprite, 매 preUpdate 동기화). 깊이 = 플레이어 깊이 ± `DEPTH.OVERLAY_STEP`(JSON `depth`: up 은 below). 시트가 없으면 숨김.
- **이펙트 풀** `src/systems/fx.ts` `FxPool`: Group 풀(48), `play(id, x, y, { dir | angle, depth | depthOffset, follow, followRotation, durationMs, tailFrames })`. 일회성은 `animationcomplete` 에 비활성, 루프는 시간 만료·따라가는 대상 비활성 시 페이드(150ms) 후 비활성. 잔월은 거합 시트의 **마지막 3프레임만 반복**하는 파생 애니(`<키>#tail3`).
- **재생 시점** (`src/scenes/Game.ts`): `PlayerAttackPayload.swingDelayMs`(= attack 1프레임 길이 ÷ 재생 배속, `EntityVisual.lastImpactMs`) 뒤에 slash/iai/twin 을 발 피벗에 재생(플레이어 따라감, 깊이 +2단). crush(바닥 깊이 `DEPTH.FX_GROUND`)·weight(히트박스 중심 아래 6px, `DEPTH.ATTACK`) 는 적중 판정 시작(`meleeSwing`). batto 는 대쉬 시작(`PLAYER_DASHED`, 플레이어 아래·따라감). gale 은 `update` 에서 이동·대쉬 중 루프(방향 갱신, 멈추거나 정지 상태면 끔). pierce 는 화살에 루프 부착(`follow` + 회전 추종, 화살 소멸 시 함께). scatter 는 발사점 1회(발사 각도 회전, 산탄·폭우 공통). 2차 진화는 경로 첫 노드 id 의 1차 이펙트 재사용(지진 = 2단 판정마다 crush, 폭우 = scatter, 잔월 = iai 꼬리 반복).
- **플레이스홀더 전환**: 베기 시트가 있으면 공격 판정 사각형은 투명(판정만), 궤적 Graphics 는 iai 시트가 있으면, 충격파 Graphics 는 crush 시트가 있으면 끈다. 시트가 없으면 전부 기존 연출 유지.
- **투사체** `src/objects/Projectile.ts`: `Rectangle` → `Sprite`. `launch(..., { texture, rotate })` 로 화살 텍스처(`bow_arrow` / 조준 `bow_arrow_aimed`)와 진행 각도 회전(유도 중에도 매 틱 갱신, 반사 시 180°). 텍스처가 없으면 크기별 플레이스홀더 + 틴트(적 투사체 포함, 기존 외형 동일). 판정 바디는 외형과 무관하게 `spec.size` 정사각형 중심 정렬.
- **엔딩 2종** (23라운드): 황제 처치 → `RoomDirector.onRunCleared` → `beginEnding()`: `setFrozen(true)`(evolve 와 같은 정지) + `TextMenu.open('ending', STORY.endings.title, [없앤다, 이해한다])`(detail 에 결과 문장). 선택 → `gameState.ending`, 세이브 삭제, `settleRun(true)`, '이해한다' 면 `metaStore` 에 `understood: true`(`markUnderstood`), STORY 자막(kind `death`) 로 선택 문장, 1.2초 뒤 결과 화면. `UiResult.line` = 고른 엔딩 문장, `UiResult.ending` = `'destroy' | 'understand'`. 정지 상태로 씬이 끝날 때 물리 world 가 먼저 정리되므로 `cleanup` 은 world 유무를 확인한다.
- **데이터**: `data/story.json` `endings.title`(임시 제목) 추가, `StoryData.endings.title`.
- **계약 추가분(승인 필요)**: `src/contract/ui.ts` `UiMenuId` 에 `'ending'`, `UiResult.ending?: 'destroy' | 'understand'`.
- **디버그**: `__lopad.fx()`(활성 이펙트 애니·프레임·위치·회전), `player().overlayFrame / moving`, `shots()` 에 `texture / rotation`, `lastResult()`(마지막 RUN_ENDED 페이로드).
- 테스트 3개 추가(로드 대상 분류·경로, 이펙트 목록 유도, 오버레이 프레임 번호·any 행), meta 1개(`markUnderstood`). 전체 64개.
- 검증(헤드리스, `vite preview`, 1280×720): 시트 48(무기 4·이펙트 13 포함)·애니 192, 요청 전부 200. 4무기 공격 시 오버레이 프레임 12→15(right 행)와 attack 1프레임(100ms) 뒤 `<무기>_slash_fx_right` 재생. 활 화살 `sheet_bow_arrow_fx` 회전 0.79rad(대각), 조준 사격 `sheet_bow_arrow_aimed_fx`·무한 관통. 거합 선택 후 iai 재생(프레임 1→4), 잔월 `iai_fx_right#tail3` 반복 후 소멸, 발도술 대쉬 중 `batto_fx_right` 가 플레이어를 따라감(1026→1078), 파쇄 즉시 crush(바닥) + 베기, 지진 2회, 중압 weight, 쌍격 twin, 질풍 이동 중 `gale_fx_left` 루프 → 위로 돌면 `gale_fx_up` → 멈추면 0, 산탄 발사 시 scatter 1회 + 화살 3, 관통 화살에 pierce 부착 → 소멸 시 0. 2층 변형 `@f2` 가 오버레이·베기에 적용. 8층 황제 처치 → `ending` 메뉴(제목·2항목, 정지·이동 불가) → [1] `ending: destroy` / [2] `ending: understand` + 메타 `understood: true`, 세이브 null, 결과 화면 line 이 선택 문장. 콘솔 오류·경고 0. 스크린샷: 스크래치 `r29fx/fx-*.png`.
- 후속(이 작업 범위 밖): 보스 attack `phaseFrames`(J) 매핑, 2~7층 보스의 stage1 시트 폴백(J), 활 화살 생성 시점을 attack 3프레임에 맞추기(아트 권장), 지진 2단 크기 반영(현재 crush 원본 크기), 무기 아이콘(`<id>_icon`) 은 UI 쪽 로드.
