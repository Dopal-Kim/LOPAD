# 게임 시스템 파트 — 작업 기록

## 1단계 프로토타입 (2026-10-01)
기획서 11장 1단계 "사각형 캐릭터가 이동·공격하고 적 1종을 처치" 구현. 결정은 `parts/producer/decisions/2026-10-01-round-05/06-*.md`.

### 구성
| 경로 | 내용 |
|---|---|
| `src/main.ts` | 진입점. 창 크기에 맞는 정수 배율로 캔버스 확대 |
| `src/config.ts` | Phaser 설정 (960×540 — 32라운드, 처음엔 640×360; pixelArt, Arcade 물리) |
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

## 29라운드 반영 (3): 오디오 연동 · 보스 국면 프레임 · 2~7층 보스 시트 폴백 · 활 발사 프레임 (2026-10-01)
계약: `assets/audio/manifest.json`(음향↔시스템 계약 초안, 결정 로그 I). 임시값은 `decisions/2026-10-01-round-29-autonomous-demo.md` "K. 시스템 오디오 연동 임시값".
- **서빙** `vite.config.ts`: 파일 목록 매니페스트가 `audio/**` 를 이미 포함하므로 WAV MIME(`audio/wav`)만 추가. 요청은 `assets-game/audio/manifest.json` + 존재하는 WAV 48개.
- **로더** `src/scenes/Preloader.ts`: 파일 매니페스트에 `audio/manifest.json` 이 있으면 JSON 단계에서 읽고, 이미지 단계에서 entries 중 파일이 있는 것만 `load.audio(entry.id, url)`(캐시 키 = entry id, 예 `sfx/swing_katana`). 끝나면 `audio.register(manifest, 로드된 키)`. 라우팅이 타이틀·개성 선택이면 `audio.setState('title')`.
- **정의** `src/systems/audioDefs.ts`(Phaser 없음): 매니페스트 타입, `dbToGain`, 버스 음량(`sfxGain` = master + SFX 0 dB + gainDb, `bgmGain` = master + BGM -8 dB + gainDb, 보스전 -3 dB, 일시정지 -6 dB), `resolveBgm`(상태 > 층), `bossBgmState`(보스 id 가 `bgmByState` 키면 그 상태 — 황제 = `emperor`, 그 외 `boss`), `SfxDedupe`(20ms), 피치 변주 대상(`sfx/swing_*`, `sfx/hit_enemy*`, `sfx/enemy_hurt`) ±4%.
- **트리거 표** `src/systems/audioMap.ts`: EventBus 이벤트 → 효과음. 함수형 id(무기별 swing, 적 id 별 `_telegraph/_dash/_shot`), 조건(`when`), 지연(`delayMs`: 근접 = attack 2프레임 시작, 활 = 3프레임 시작), 루프(`loop`: 가드 유지), 정지(`stop`: 가드 해제, 조준 취소). 신설 이벤트(계약 밖, 시스템 내부): `PLAYER_SECONDARY`, `POTION_USED`, `ITEM_PICKED`, `ENEMY_TELEGRAPH`, `ENEMY_ATTACK`, `BOSS_TELEGRAPH`, `BOSS_ATTACK`, `EXIT_OPENED`, `RUN_ENDED`, `ENDING_CHOSEN`, `FATE_DECIDED`, `MENU_OPENED/SELECTED/CLOSED`. `ENEMY_DAMAGED` 는 `Mob.takeDamage(amount, { crit, tick })` 가 발행(치명 → hit_enemy_crit, 출혈·잔월 틱은 enemy_hurt 만).
- **재생** `src/systems/audio.ts` `audio`(게임 수명 싱글턴, `main.ts` 에서 `attach(game)`): 트리거 표 구독, 효과음 보이스 8개 상한(초과 시 가장 오래된 것 정지), 루프 효과음 맵, BGM 크로스페이드 1200ms(`game.events` STEP 으로 진행 — 씬 재시작과 무관), `STAGE_STARTED` → 층 곡·상태 해제, `BOSS_STARTED` → `boss`/`emperor`, `BOSS_DIED` → 층 곡 복귀, `PLAYER_DIED`·`ENDING_CHOSEN`·`RUN_ENDED` → 페이드아웃 + 루프 정지, 타이틀·개성 선택·`toTitle`·`startNewRun` → `title`. 일시정지(`host.pause/resume`) 덕킹. 첫 pointerdown/keydown 에서 컨텍스트 resume(Phaser unlock 과 중복 무해). 음소거 `M`(`KeyM`, input 포커스 중 제외) → `game.sound.mute`, `localStorage lopad.mute`. 디버그: `__lopad.audio()`(Game) / `window.__lopadAudio()`(`?debug=1`, 타이틀 등 Game 밖) — manager·contextState·entries·loaded·missing·bgm·bgmVolume·state·floor·loops·voices·recent(최근 12: id·시각·rate·delayMs)·mute.
- **보스 국면 프레임** (결정 로그 J): `SheetJson.phaseFrames { telegraph, dash, recover_or_fan }`. `EntityVisual.hold(action, dir, column, time, durationMs)`(프레임 고정, idle/walk 가 덮지 않음) · `loopFrames(action, dir, columns, frameMs)`(파생 애니 `<애니>#p1-2`, `spriteLibrary.phaseAnim`) · `release()` · `held`. `Boss`: 예고 = frame 0 유지, 돌진 = 1↔2 150ms 반복(돌진 방향), 벽 경직 = frame 3 을 `wallStunMs` 유지, 돌진 멈춤·부채꼴 = frame 3 을 그 프레임 길이(220ms)만큼. 유지 중에는 피격 hurt 애니·접촉 attack 애니를 재생하지 않는다(번쩍임만). `phaseFrames` 가 없으면 기존 attack 재생. 돌진 예고·실행·부채꼴에 `BOSS_TELEGRAPH`/`BOSS_ATTACK` 발행.
- **2~7층 보스 폴백**: `spriteLibrary.alias(name, target)` + `resolve()`. Preloader 가 `BOSSES` 중 자기 idle 시트가 없는 id 를 `SPRITES.BOSS_FALLBACK_SHEET`(`stage1`)로 별칭. 텍스처·애니 키는 대상 이름(`stage1_idle_down@f2`)이며 층 램프 스왑이 그대로 적용된다. 황제는 자기 시트. `EntityVisual.sheetName` = 실제 시트 이름.
- **활 발사 시점**: `PlayerAttackPayload.releaseDelayMs`(= attack 3프레임 시작 ÷ 배속, `EntityVisual.frameStartMs(2)`). `Game.fireArrow` 는 연사 판정만 즉시 하고 화살 생성(`spawnArrows`)은 그 시점에 플레이어 현재 위치로(정지·사망·씬 종료면 취소). bow_shot 효과음도 같은 지연.
- **메뉴**: `TextMenu` 가 `MENU_OPENED { id, reopen }`(같은 메뉴 다시 그리기는 reopen → 열림음 없음), `MENU_SELECTED`, `MENU_CLOSED { selected }`(선택 없이 닫힘만 menu_cancel) 발행. UI 계약(`MENU_OPEN/CLOSE`)은 그대로.
- 테스트 8개 추가(dB·경로·버스 음량·BGM 결정·중복 묶기·피치 변주·실제 매니페스트 대조(표의 id 전부 존재, 매니페스트의 효과음 전부 사용)·프레임 시작 시각). 전체 72개. prettier·tsc·eslint·build 통과.
- 검증(헤드리스 `vite preview --port 4174`, Chromium `--autoplay-policy=no-user-gesture-required`): 음향 매니페스트 + WAV 48 = 요청 49건 전부 200, WebAudio `running`, entries 48 = loaded 48, missing 0. 1층 진입 `level_enter` + `bgm/floor_low`(음량 0.376 = -8.5 dB). 클릭 → `swing_katana`(delay 94.6ms = 1프레임 100ms ÷ 1.057, rate 1.003/0.985), 쿨다운 중 2번째 클릭은 기록 없음, Space → `dash`. 보스 방 → `boss_start`, 상태 `boss`, `bgm/boss` 0.335(-9.5 dB), 보스 애니 `walk_left → attack_left#hold0 → attack_left#p1-2 → attack_left#hold3 → idle_right`(예고·돌진·벽 경직), `boss_telegraph`. 처치 → `boss_die`, 상태 null, `bgm/floor_low` 복귀, `pickup_gold`, 보상 메뉴 `menu_move`. 2층 전환 → `level_enter`·`save`, 2층 보스 `stage2` 의 애니 `stage1_attack_down@f2`, 별칭 stage2~7 → stage1(스크린샷: 녹색 램프). 8층 황제 → 상태 `emperor`, `bgm/emperor` 0.188(-14.5 dB). `M` → mute true / `lopad.mute`=1 → 다시 false / 0. 활: 화살이 클릭 뒤 약 162ms(3프레임 시작)에 생성, `bow_shot` delayMs 162, 우클릭 200ms 뒤 해제 → `bow_draw` 재생 후 정지(voices 0, bow_aimed 없음), 800ms 유지 → `bow_aimed`. 대검 우클릭 유지 → loops `guard_hold`, 해제 → loops 없음 + `guard_push`. 개성 100 → `menu_move`, [1] → `menu_select` + `evolve`. 시련 진입 `door_close`, hurtAll → `hit_enemy` + `enemy_hurt`, 처치 → `enemy_death`, 사수 → `archer_shot`. 타이틀 → `bgm/title` 0.447. 콘솔 오류·경고 0. 스크린샷: 스크래치 `r30audio/audio-*.png`.
- 후속(범위 밖): UI 메뉴 커서 이동음(`menu_move` 는 현재 열림음으로 사용) — UI 가 소리를 내려면 계약에 재생 명령 추가 필요. 엔딩 전용 효과음·휴식 방·상점 진입음은 자산 없음. OGG 전환은 복귀 후 인터뷰. `TRIAL_CLEARED` 발행 시점에 `bossUnlocked` 가 아직 false 라 Game 의 '본영 문 열림' 자막 분기가 닿지 않는 것으로 보임(기존 동작, 이번 범위 밖 — 확인 필요).

## 32라운드 반영: 해상도 960×540 · 방 80×48 + 카메라 추종 · 리듬 점 · 조준 유지 (2026-10-02)
결정: `decisions/2026-10-02-round-31-return-review.md`(1·2), `2026-10-02-round-32-redesign-direction.md`(Q1·Q2·Q5). 임시값은 32라운드 로그 끝 "시스템 반영 기록 (임시값)".
- **해상도** `src/core/Constants.ts` `GAME` 960×540. `main.ts` 정수 배율 로직 그대로(1280×720 창 = 1배 + 레터박스, 1920×1080 = 2배). 시스템 임시 화면 수치는 `PLACEHOLDER_UI`(글꼴·획 예시 패널·결과 화면 간격·이름 입력 폭)로 모아 1.5배. `TextMenu`·`GameOver`·`Setup`·진화 배너가 사용. UI 코드는 손대지 않음.
- **맵** `src/systems/mapgen/types.ts` `CELL_W/CELL_H` 80×48, `ROOM_MARGIN` 3, `DOOR_MARGIN` 2. `tiles.ts` 래스터화 재작성: 방 내부는 셀 안 무작위 위치(중앙 축 포함 조건 삭제), 연결마다 `portOf`(문 위치 범위·복도 시작 좌표) → 문 2개(또는 복도 셀이면 1개)를 따로 고르고 Z 자 복도(`carveBox` 3구간). 보스 2×2 방의 문은 입구 셀 띠 안에만. `data/stages.json` 방·보스 방 크기, 웨이브, 스폰 거리 / `data/enemies.json` 사수·결사병 거리 / `src/world/tileskin.ts` `PROPS_RULES` 재조정. `layout.ts`(셀 배치)는 변경 없음.
- **카메라** `src/world/TileWorld.ts` `cellRect`·`cameraRegion(x, y)`(방 안 = 방 셀 사각형, 복도·문 위 = 현재 셀 ∪ 진행 방향 이웃 셀, 월드로 잘라냄). `src/scenes/Game.ts` `updateCamera(force, delta)`: 데드존 → 영역 클램프(`clampCenter`, 영역이 화면보다 작으면 가운데) → 프레임 보정 lerp → 반올림 스크롤. `startFollow/setBounds` 와 `CAMERA.CELL_OFFSET_Y`·`currentCellKey` 제거. 보스전도 같은 추종.
- **리듬 점** `src/scenes/Setup.ts`: 리듬 단계 진입 시 `showDot`, `update(time, delta)` 에서 `moveDot`(WASD 속도 = 플레이어 이동 속도, 스페이스 = 대쉬 거리 순간 이동 + 잔상 tween), 클릭 `flashDotRing`. 상수 `RHYTHM_DOT`. 집계(`RhythmSample`)는 그대로. 디버그 훅 `window.__lopadSetup()`(`?debug=1`: phase·dot·rhythm·clicks·rings·features).
- **조준 사격** `src/objects/Player.ts`: `aim` 상태에서 차지 완료 시 `aimReady` + `PLAYER_SECONDARY { phase: 'ready' }` + 번쩍, **떼면** 발사(차지 전이면 cancel). `isAimReady` getter, 디버그 `playerExtra().aimReady`. `EventBus` `PlayerSecondaryPayload.phase` 에 `'ready'`.
- **디버그** `__lopad.camera()` 에 `width/height/region`.
- 테스트: mapgen 2개 추가(방 내부가 셀 여백 안 / 문 양옆 벽 + 방끼리 직접 연결은 문이 4타일 이상 어긋남). 전체 74개 통과. prettier·tsc·eslint·build 통과.
- 검증(헤드리스 `vite preview --port 4174`, Chromium): 1920×1080 → 캔버스 960×540 CSS 1920×1080(배율 2), 1280×720 → CSS 960×540 중앙(배율 1). 시드 `lopad` 1층: 방 7개 전부 시작 방에서 바닥 BFS 도달, 시작 방 영역 1280×768, 1층 아트 타일셋(`tiles_stage1`, 소품 74). D 1.2초 → scrollX 1560→1600(영역 오른쪽 끝에서 클램프), 플레이어 화면 x 563/960. 시련 방 순간 이동 → 스크롤이 8프레임 샘플(120ms 간격)에 걸쳐 2410→919 로 수렴(튀지 않음), 영역 = 그 방 셀. 스폰 4마리 최소 거리 10.4타일, 문 닫힘(4). 남쪽 문 밖 복도에 서면 영역 세로 1536(현재 셀 + 아래 셀). 보스 방 영역 2560×1536, A 0.8초 → scrollX 3356→3313, 보스 HP 200. 1→8층 전환(2~8층은 플레이스홀더 타일셋, 영역 1280×768). 활: 우클릭 800ms 유지 → `aim`·aimReady true·조준 화살 없음 → 떼면 `sheet_bow_arrow_aimed_fx` 피해 11 + `bow_aimed`; 200ms 유지 후 떼면 취소(화살 0). 개성 선택: 3획 → 리듬 점 (480,270), D 0.5초 → x 528(+48 = 96px/s), 스페이스 → x 576(+48)·dashes 1, 클릭 → 원 1·attacks 1, 5초 후 운명. 콘솔 오류·경고 0. 스크린샷: 스크래치 `r32/r32-*.png`.
- 후속(범위 밖·인터뷰 대상): 적 수·거리 임시값 밸런스 패스, 2~8층 전용 타일셋(아트), 보스 방 크기 체감, 복도에 소품·조명(아트), HUD 가장자리 배치(UI).

## 35라운드 반영 (1단계): 피격 피드백 — 히트스톱·흔들림·넉백·피격 이펙트·데미지 숫자 (2026-10-02)
결정: `decisions/2026-10-02-round-35-combat-dev.md`(Q1·Q2, 분담). 임시값은 그 로그 끝 "시스템 반영 기록 (임시값)". 글꼴 규칙은 `round-34-font.md`.
- **감각 계층** `src/systems/feel.ts`(Phaser 없음): `feelSettings`(shake/hitstop/knockback 배율, numbers 표시 — 게임 수명 싱글턴, 저장 안 함) + `setFeel(patch)`. `HitStop`(요청 → `until`, 마지막 시작 뒤 `MIN_GAP_MS` 80 안의 요청 무시, 더 긴 요청은 연장), `Shake`(활성 항목 중 가장 큰 진폭×남은 비율, 매 프레임 무작위 방향 **정수** 오프셋, `last` 기록), `knockSpeed(d, T)` = 2d/T(선형 감쇠 적분 = d), `knockFactor`. 수치는 `Constants.FEEL`.
- **히트스톱** `Game.update`: `hitStop.active(time)` 이면 `setHitStopped(true)` → 물리 `world.pause()`(`syncPhysicsPause` 가 `frozen` 과 합산), 플레이어·적 `anims.pause()`, `FxPool.setPaused(true)`; 그 프레임은 입력을 **읽지 않고**(큐 유지) 카메라(흔들림)·STATE 스냅샷만 진행. 끝나면 전부 재개. 씬 시계는 흐르므로 지연 호출(쌍격 2타·베기 이펙트)은 그대로 — 최대 40~90ms 어긋남은 허용. 플레이어 피격은 `onPlayerDamaged` 에서 90ms.
- **흔들림** `updateCamera`: 추종 보간·반올림이 끝난 스크롤에 `shake.sample()` 정수 오프셋을 **더하기만** 한다(보간 상태 `camCenter` 는 건드리지 않음 → 튀지 않음). 적중 2px/60ms, 치명 4/100, 플레이어 피격 5/140, 보스 벽 충돌 6/160(`Boss` 가 `BOSS_WALL_HIT` 발행 → `Game.onBossWallHit`), 대검 충격파(`mods.shockwave`) 4/100.
- **넉백** `Mob.shove(dirX, dirY, distPx, ms, additive, onEnd)`: 선형 감쇠 속도를 `update` 의 `delta` 로 중점 적분(히트스톱 동안 update 가 없으니 그만큼 멈춤, 프레임 속도와 무관하게 거리 ≈ distPx). 일반 적은 AI 대신(비틀거림, `isKnockedBack` true), 보스는 AI 속도에 **더하기만**(1/4 거리, 패턴 안 끊음). 벽은 Arcade 충돌이 막는다. `stun()` 은 shove 를 지운다. 끝나면 `onEnd` → `knock_dust`. `Player.takeHit(attack, time, source?)`: `source`(가해자→플레이어 방향) 가 있고 대쉬 중이 아니면 8px/100ms 조작 대신 밀림(`update(input, time, delta)` 에 delta 추가).
- **피격 공통 경로** `Game.hitMob(mob, dmg, { crit, dirX, dirY, tick?, knock? })`: 적중점 = 바디 중심에서 공격 방향 반대쪽 0.6×반폭, 피는 바디 중심(시트)/뒤쪽(플레이스홀더). 근접(`applyMeleeHit`)·화살(`onPlayerShotHit`, 방향 = 속도)·반사 투사체·대쉬 잔상·가드 반격(`knock: false` — 이미 `knockback` 중)·잔월·출혈 틱(`tick: true` → 작은 숫자만, 이펙트·정지·넉백 없음)이 전부 여기를 지난다. 디버그 `hurt/hurtAll(amount, crit?)` 도 같은 경로(방향 +x).
- **피격 이펙트** `src/systems/hitFx.ts` `HitFx`: 아트 시트(계약 §3, 35라운드 아트 커밋)가 있으면 `FxPool` 로 — `hit_spark` 16×16 any 적중점 깊이 `DEPTH.HIT_FX`(4.5, 개체 위); 치명타는 `crit_burst` 32×32 any 가 **대신**; `blood` 24×24 4방향(행 = 공격 진행 방향) 히트박스 중심에 **바닥 깊이**(`FX_GROUND`), 마지막 프레임(얼룩)을 `FEEL.BLOOD_STAIN_MS` 500 유지 후 페이드(`FxPool.play` 옵션 `holdLastMs` 추가); `knock_dust` 16×8 4방향(행 = 밀린 방향) 넉백 끝 발 접지점(`mob.x, body.bottom`) 바닥 깊이; `player_hit` 24×24 any 플레이어 중심(`getCenter`) 개체 위. 시트가 없으면 Graphics 생성 텍스처(흰 원 r3 → 2.2배 페이드 120ms, 층 램프 base 색 점 4개 180ms, 치명 링 6→18px 160ms, 회색 G7 먼지 점 3개 200ms) 플레이스홀더.
- **로드** `spriteDefs.HIT_FX_IDS`(5종) + `ENEMY_FX_IDS`(telegraph_line/circle/cone, enemy_bullet, boss_fan_shot, muzzle_flash — 2단계용, **로드만**) 를 `allFxSheetIds(WEAPONS)` 로 합쳐 Preloader 가 요청. `SheetJson` 에 `tailFrames?`·`tile?` 필드 추가(타입만). 층 램프 스왑(`@f<n>`)이 피격 시트에도 적용된다(2층 `blood_fx_right@f2` 확인).
- **데미지 숫자** `src/systems/damageNumbers.ts` `DamageNumberPool`: Text 풀 24(가득 차면 가장 오래된 것 재사용), 적중점 −10px 에서 위로 14px(600ms, Quad.Out), 끝 200ms 페이드, 가로 ±4px 흔들림, 깊이 `DEPTH.DAMAGE_TEXT` 5. 일반 흰 G13 `#d8d9db`, 치명 = 층 램프 **23(light1)** 색(1층 `#e2a33c`, 2층 `#52b97b`) + `!` + 1.5배, 플레이어 피격 G11 `#b2b4b8` + `-`, 틱 0.8배. **글꼴 Galmuri11 11px** — `public/style.css` `@font-face`(URL `assets-game/ui/fonts/Galmuri11.woff2`, UI 소유 파일을 URL 로만 참조; `vite.config.ts` MIME `font/woff2` 추가) + `src/systems/fonts.ts` `ensureFont()`(Preloader 에서 `document.fonts.load("11px 'Galmuri11'")`, 3초 초과·실패면 monospace, `fontFamilyOr`). HUD 가 아니라 월드 좌표에 시스템이 직접 그린다(결정 로그 분담).
- **이벤트**: 내부 `BOSS_WALL_HIT { id, x, y }` 신설. `PlayerDamagedPayload.source?` 추가(내부 넉백 방향) — UI 계약 `PLAYER_DAMAGED` 중계는 `{ hp, maxHp, amount }` 만 보낸다(계약 변경 없음).
- **디버그**: `__lopad.feel()`(settings·FEEL 상수·hitstop{active, remainingMs, count, physicsPaused}·shake{offset, active, count, last}·numbers[]·font{family, loaded}·hitFx{sheets, placeholders}), `setFeel({ shake: 0 })`, `shoved()`, `mobs()` 에 `shoved/frame/animPaused`, `playerExtra().shoved`, `hurt/hurtAll(amount, crit?)`, `moveMob(index, x, y)`(보스 벽 충돌 검증용).
- 테스트 7개 추가(`feel.test.ts`: 히트스톱 간격·배율 0, 흔들림 감쇠·최대값·정수·배율 0, 넉백 적분 ≈ d·배율·setFeel 검증). 전체 81개. prettier·tsc·eslint·build 통과.
- 검증(헤드리스 `vite preview --port 4174`, Chromium swiftshader 1920×1080 — 약 20~30fps 라 프레임 수는 실제보다 적다): 글꼴 `document.fonts.check("11px 'Galmuri11'")` true, woff2 200 `font/woff2`, 피격 시트 5종 + 2단계 6종 로드. `hurtAll(2)`: 히트스톱 프레임 동안 물리 `isPaused`·적 `animPaused`·위치 고정, 흔들림 오프셋 scrollY 914→916, 넉백 +6.8px(목표 6), 숫자 `2` `#d8d9db` Galmuri11, `hit_spark/blood/knock_dust_fx_right`. 치명 `hurtAll(3, true)`: 70ms(첫 프레임 뒤 남은 37ms), `3!` `#e2a33c` 1.5배, `crit_burst` 가 섬광 대신, 넉백 +11px(목표 10; 20fps 서브스텝 초과분). **실제 근접 적중**(징집병 옆 20px 에서 클릭): hp 10→5, 히트스톱 2프레임, 대상 x +8.6(공격 방향 0.997), 숫자 `5`, 섬광·피·먼지. 플레이어 투사체 피격(`fireAtPlayer`): 히트스톱 3프레임(90ms), 흔들림 최대 5px, `-7` `#b2b4b8`, 플레이어 −8.5px(투사체 진행 방향), `player_hit_fx`. 보스: 히트스톱 60ms, 넉백 +1.5px(= 6×1/4, `shoved` 4프레임 동안 AI 유지), 숫자 `10`. 보스를 왼쪽 벽 옆 4타일에 두고 플레이어를 1타일 옆에 → 돌진 → `#hold3` 과 함께 `shake.last {px 6, ms 160}` 3회(사이의 5px 는 접촉 피격). `setFeel({shake:0,hitstop:0,knockback:0})` → 정지 0프레임·오프셋 0·변위 0, 숫자는 유지; `numbers:false` → 숫자 없음. 2층: `9!` `#52b97b`, `crit_burst_fx_right@f2`. 콘솔 오류·경고 0. 스크린샷: 스크래치 `r35/r35-{b0,c0,e0,f0}-*-zoom(-x2).png`(2층 캡처는 600ms 창을 놓쳐 숫자 없음 — 수치는 샘플로 확인).
- 후속(범위 밖): 2단계 적·보스 양상(예고 마커 `telegraph_*`, `enemy_bullet`·`boss_fan_shot`·`muzzle_flash` 연결 — 시트는 이미 로드됨), 흔들림·히트스톱 강도 설정 UI(계약에 설정 명령 필요), 효과음 `BOSS_WALL_HIT` 매핑(음향 자산 없음), 지속 피해 틱 숫자 과다 시 묶기.

## 35라운드 반영 (2단계): 적·보스 공격 양상 — 예고 마커·적 투사체 시트·적 행동 3종·보스 패턴 4종·roomFloors (2026-10-02)
결정: `decisions/2026-10-02-round-35-combat-dev.md`(2단계), `round-37-tileset-review.md`(roomFloors), 39·40라운드 추가 지시. 임시값은 35라운드 로그 끝 "시스템 반영 기록 2단계 (임시값)". 계약 `art-assets.md` §2(roomFloors·소품 maxPerRoom/weight·벽 변형)·§3.1(projectile 앵커).
- **예고 마커** `src/systems/telegraph.ts` `TelegraphFx`: `line(x, y, angle, lengthPx, ms)`(telegraph_line 8×8 → TileSprite 로 x 타일링 + 회전, 피벗 (0,4) = 공격자) · `circle(x, y, r, ms)`(scale = r/15) · `cone(x, y, angle, halfAngle, r, ms)`(4방향 행 = 지배 축, 전체각 > 120° 면 원). 2프레임 깜빡임은 시트 `frameDurationsMs`(120ms) 로 `update()` 가 프레임을 바꾼다. 바닥 깊이, 만료·`end()` 시 제거, `aim(x, y, angle)` 로 예고 중 추적. 시트가 없으면 Graphics 점선/원/부채꼴 플레이스홀더. 히트스톱 시 `setPaused`. 디버그 `__lopad.telegraph()`.
- **MobContext 확장** (`src/objects/Mob.ts`): `telegraph`, `playFx`(총구 화염), `countMobs(id)`, `areaHit(x, y, r, attack)`(내리찍기: crush 시트/링 + 흔들림 + 반경 안 플레이어 피해), `summon(id, x, y)`(→ `RoomDirector.spawnExtra`, 처치 대기 목록에 포함), `pack`(`src/systems/packCharge.ts` — 방 공유 집단 돌격 상태, 테스트 2개). `ProjectileSpec.sprite` 로 탄 시트 지정. `Mob.guardReduction(dirX, dirY, time)`(기본 0) · `facingVector()`.
- **적** `src/objects/Enemy.ts`: 결사병 예고 중 돌진 경로선(길이 = 속도×시간, 플레이어 추적) → 돌진 시 제거; **방패 막기** `shield`(정면 전체각 안의 공격 피해 ×(1−reduction), 돌진 중 정면 = 돌진 방향); 사수 **조준선**(`ranged.telegraphMs/telegraphTiles`, 조준 중 정지) → attack 2프레임에 `muzzle_flash`(바디 중심 + 전방 8px·위 2px, 개체 위 깊이) + `enemy_bullet` 탄 → **재장전**(`ranged.reload`: n발 뒤 reloadMs 동안 후퇴·사격 없음); 징집병 **집단 돌격**(`pack`: 머릿수·거리 조건에 전원 speedMult 배 durationMs, 쿨타임). 상태는 `behaviorState`(디버그 `__lopad.behavior()`).
- **보스** `src/objects/Boss.ts`: 패턴 기계 — `phases[].patterns` 중 쿨타임·조건(fan 있음 / slam·volley 수치 있음 / summon 상한 미만)이 맞는 후보에서 시드 RNG(`floorSeed:boss:<id>`)로 선택, `patternIntervalMs ?? dash.intervalMs` 간격. 상태 `telegraph/dash/stun`(돌진, 경로선 추가) · `fanTelegraph`(cone 마커 → 부채꼴, 탄 `boss_fan_shot` 2프레임 루프) · `slamTelegraph`(플레이어 위치에 circle → `areaHit`) · `recover`(소환 뒤 frame 3 유지) · `volleyTelegraph/volley`(선 마커 → 일직선 n발 shotGapMs 간격, 황제). `fan.afterDash` 연계 유지. 패링 경직은 마커 제거 + 패턴 리셋. 디버그: `patternLog`·`summoned`·`patternState`, `__lopad.setBossHp(hp)`.
- **투사체** `src/objects/Projectile.ts`: `ProjectileVisual` 에 `originX/Y`(시트 pivot)·`anim`(루프 시트) 추가, `Game.fire` 가 `spec.sprite` 로 시트 JSON 의 `rotate`·`pivot`·`loop` 를 해석. `deactivate` 시 애니 정지, 히트스톱 시 `setAnimPaused`. 반사 시 텍스처 유지·회전 시트만 180°.
- **피격 경로** `Game.hitMob`: `mob.guardReduction` > 0 이면 피해 감소(최소 1) + `hit_spark` + 숫자 + 히트스톱 40ms + 흔들림 2px 만, 피·치명 버스트·넉백 생략. 지속 피해 틱은 막지 않음.
- **방 상태 머신** `RoomDirector.spawnExtra`(활성 방에 적 추가, 걸을 수 없는 자리면 방 안 무작위) · 보스 사망 시 남은 부하 즉시 정리(시체만).
- **roomFloors(37·40라운드)** `src/world/tileskin.ts`: `TilesetJson.roomFloors`, `TileSkin.roomFloors`(비어 있지 않은 것만, 역매핑 = 바닥), `indexFor(id, x, y, isOpen?, roomType?)` — 바닥은 방 종류 목록, 벽 자동타일 인덱스가 `tiles["2"][0]` 이면 그 목록을 좌표 해시로 섞음(정면 벽 변형). `roomTypeMap(layout)`(방 내부 타일 → 종류) 을 `TileWorld` 가 바닥 레이어 생성 시 사용(복도·방 밖은 undefined → `tiles["1"]`). 소품 `maxPerRoom`(방당 상한, 후보에서 제외) · `weight`(가중 선택 `pickWeighted`, 0 = 제외). 시트 크기·인덱스는 JSON 값만 사용(128×64·128×80 모두). 테스트 5개 추가(방 종류별 목록·옛 형식·빈 목록 / 벽 변형 / 128×80 재배치 인덱스 / maxPerRoom=1·weight 0 / roomTypeMap). 디버그 `__lopad.tileIndexAt`.
- **데이터**: `data/enemies.json`(archer `ranged.telegraphMs/telegraphTiles/sprite/muzzle/reload`, charger `shield`, dummy `pack`), `data/bosses.json`(모든 페이즈 `patterns`, fan `telegraphMs/telegraphTiles/sprite`, 보스별 `slam`·`summon`(황제 제외)·`volley`(황제)). `src/data/types.ts`·`index.ts` 검증(패턴 이름·필요 수치·소환 적 존재).
- **이벤트** (`src/core/EventBus.ts`): `ENEMY_TELEGRAPH.kind` 에 `'shot'`, 신설 `ENEMY_BEHAVIOR { id, kind: 'reload' | 'block' | 'pack' }`, `BossPattern = 'dash' | 'fan' | 'slam' | 'summon' | 'volley'`, `BOSS_TELEGRAPH.attack` 에 fan/slam/volley, `BOSS_ATTACK.attack` 에 slam/summon/volley. 음향 매핑(`audioMap.ts`)은 변경 없음(기존 dash/fan 만).
- **상수** `Constants.ENEMY_FX`(시트 이름·기준 반지름 15·원 대체 각 120°·플레이스홀더 점선·총구 오프셋 8/2·소환 간격 12). 39라운드: `FEEL.DAMAGE_TEXT.CRIT_SCALE` 1.5 → 2.
- **디버그 훅 추가**: `telegraph()`, `projectiles()`, `behavior()`, `lastSlam()`, `spawnEnemy(id, x, y)`, `setBossHp(hp)`, `killMob(i)`, `tileIndexAt(tx, ty)`.
- 테스트 88개(packCharge 2 + tileskin 5 추가). prettier·tsc·eslint·vitest·build 통과(작업 중 UI 파트가 `src/ui/theme.ts` 를 고치는 동안 한때 tsc·build 가 UI 쪽 오류로 실패해, 헤드리스 검증은 HEAD 의 `src/ui` 를 넣은 격리 사본 빌드로 진행. 종료 시점 작업 트리에서는 전부 통과).
- 검증(헤드리스 `vite preview --port 4174`, Chromium swiftshader 1920×1080, `?new=1&seed=lopad&debug=1&weapon=katana`, 처치로 개성 100 에 닿아 3지선다가 열리지 않도록 배치마다 `setPersonality(0)`): 시트 6종(telegraph 3·enemy_bullet·boss_fan_shot·muzzle_flash) 로드. **roomFloors**: 1층 아트 JSON(40라운드 128×80 재배치)로 시작 방 바닥 인덱스 {23..26}, 시련 {27..30}, 휴식 {31..34}, 보스 {35..38}, 소품 74. **집단 돌격**: 징집병 4마리, 발동 다음 프레임부터 4마리 전부 `pack`·속도 67.2(= 48 × 1.4), 평시 48, 약 2.06초 뒤 해제. **결사병**: `telegraph` 중 line 마커 길이 90(= 89.6)·각 π(플레이어 방향)·시트, 돌진 시작에 마커 0 → 속도 224(= 14칸). **방패**: 정면(플레이어가 −x, 공격 방향 +x) 10 → 5 피해·넉백 없음(`shoved` false), 뒤에서 10 → 10·넉백. **사수**: `move → aim`(line 48px, 0.3초) `→ move`(사격) ×3 → `reload`(2.2초, 속도 40 = 2.5칸, 플레이어 반대 방향 cos 1) `→ move`; 탄 `sheet_enemy_bullet_fx` 회전 = 속도 각(−0.245 / −1.133), 총구 화염 15프레임. **보스 1페이즈**: 패턴 기록 `dash, dash, dash, slam, dash, dash`, line 마커 154px(= 16칸 × 0.6초), 내리찍기 circle 반지름 40(2.5칸)·플레이어 피해 25(`lastSlam.hit`). **2페이즈**(HP 45%): `… slam, summon, slam, dash, fan, …` 4패턴 전부, 소환 2(보스 양옆 ±28px, 징집병 2), cone 마커 반지름 80(5칸), 탄 `sheet_boss_fan_shot_fx` + `boss_fan_shot_fx_down` 루프 최대 7. **황제**(8층, HP 60% → 2페이즈): `fan, slam, fan, fan, volley`, 선 마커 192px(12칸), 정렬 사격 5발이 같은 각(0.153 = 마커 각) 일직선, 탄 `@f8` 변형, 소환 없음. 콘솔 오류·경고 0. 스크린샷: 스크래치 `r35b/r35b-{b0 결사병 예고선, d0 사수 조준선, d1 사수 탄(어두워 잘 안 보임), e0 보스 돌진선, e1 내리찍기 원, e2 부채꼴 cone, e3 부채꼴 탄, e4 소환, e5 전체, f0 황제 정렬 선, f1 정렬 탄}.png`, 로그 `r35b/log.json`.
- 후속(범위 밖): 적 투사체가 벽을 통과함(기존 동작 — 투사체↔벽 충돌 없음, 황제가 벽가에서 쏘면 탄이 벽 너머로), `enemy_bullet` G01 구슬이 어두운 새 바닥에서 잘 안 보임(아트 피드백), 재장전 전용 애니 없음, 패링 반사 탄의 헤드리스 검증은 생략(코드 경로는 1단계와 동일), 집단 돌격 발동 프레임의 ≤1프레임 지연, 음향 자산 없음(새 attack·ENEMY_BEHAVIOR).

## 42·43라운드 반영 (3단계): 인페르노 이펙트 — 2차·보조 연결 · 잔상 리본 · 화면 섬광 · 굵은 예고 · 아트 A·B 규격 (2026-10-02)
결정: `decisions/2026-10-02-round-42-infernum-fx.md`(Q1~Q3, 43라운드 검수), 계약 `art-assets.md` §3.1·§3.2, 설계 `parts/art/fx-design.md` §4~6(공개·승인 열람), 아트 B 전달 요점 `parts/art/work/fx_prod/NOTES-b.md`. 임시값은 42라운드 로그 끝 "시스템 반영 기록 (임시값)".
- **시트 필드** `src/systems/spriteDefs.ts` `SheetJson`: `trail{color,alpha,ms,fromFrame,widthRatio}` · `flash{color,alpha,ms,atFrame}` · `shake{px,ms}` · `secondStage{frame,atMs,flash,shake}` · `hitFrames` · `stateFrames` · `tint{when,color,method}` · `alias` · `spawnNote` · `scale: number | string` 등. 순수 함수 `sheetScale`(문자열 → 1) · `fxImpactFrame`(`impactFrame` 우선, `spawn: attack_frame2` 면 1 = f0 예비) · `hitFrameOffsets(def, hits)` · `progressFrame(p, frames, divisor)`. 크기·피벗·프레임 수·ms 는 JSON 에서 자동(코드 수정 없음).
- **색 해석** `palette.resolveFxColor(palette, ref)`: `#rrggbb`(A 묶음) · `fx.weapons.<무기>.ramp[i]` · `fx.core[i]`(B 묶음) → 정수, 모르면 null. `data/palette.json` fx 블록(대검 W2 `#d8441c`).
- **FxPool** `src/systems/fx.ts`: §3.2 훅 — `flash` 는 atFrame 시작, `shake` 는 섬광 프레임(없으면 타격 프레임), `secondStage` 는 그 프레임에서 한 번 더, `trail` 은 fromFrame 부터(`opts.trailSource` 궤적, 없으면 스프라이트 위치 — player_pivot 이면 몸 중심). 예약 이벤트는 **이펙트 재생 경과**(update 사이 시간, 히트스톱 중 정지)로 잰다(`schedule`). `leadMs(id)` = 타격 프레임 시작 ms, `sheet(id)`, `framesOf(id)`, 옵션 `tintFill`(setTintFill) · `staticFrame`/`setFrame`(진행도) · `followOffset` · `hooks: false`(보스가 crush 를 빌릴 때) · `stop(h, holdMs, fade)`.
- **잔상 리본** `src/systems/trail.ts` `TrailRenderer`(Graphics 하나 = 리본 하나, 16ms 샘플 정수 폴리라인, 두께 최신 → 1px, 색 코어 → 층 강조 → 몸통, 히트스톱 시 샘플 시각 이동) + `trailMath.ts`(`segmentStyle`·`arcPoint`·`flashAlphaAt`, 테스트). JSON `trail` 이 있는 휘두름 시트는 플레이어 중심 호를 훑는 궤적으로, 발도술·허보는 플레이어 몸 중심으로. 시트 trail 이 없거나 시트가 없으면 기본 호 리본(`FEEL.TRAIL.SLASH`). 화살·일반 대쉬 리본 없음(fx-design §6.1). `feelSettings.trail`.
- **화면 섬광** `src/systems/screenFx.ts` `ScreenFx`: 월드 최상(`DEPTH.SCREEN_FX` 50, scrollFactor 0) 사각형 하나, 큰 알파 유지(합산 없음), update 로 선형 감쇠. 보스 페이즈(X0 0.35/120ms + 채도 감소), 진화 선택(층 light1), 사망 암전. 채도 감소는 WebGL 카메라 `postFX.addColorMatrix()` 를 **필요할 때만** 붙였다 뗀다(캔버스는 SATURATION 회색 사각형). 치명 섬광·히트스톱 채도 감소는 상수 0(꺼짐). `feelSettings.flash`.
- **연결(Game)**: 휘두름 `pathFx('wide','iai','dance','twin') ?? <무기>_slash` 를 `swingDelayMs − leadMs` 에 재생 · 쌍격·난무 추가 타격 간격 = `hitFrameOffsets`(`FEEL.SYNC_HIT_FRAMES`) · 잔월 `zangetsu` 루프(틱 동기) · 지진 `quake`(1단에서 1회, secondStage) · 분쇄 `pulverize` · 철벽 `ironwall` + `guard_wave` · 거인 `giant`(공격 동안 루프) · 허보 `longinvuln`/발도술 `batto`(따라감, 리본) · 급소 `dashcrit`/암살 `assassin`(대상 히트박스 중심, crit_burst 대신) · 출혈 `bleed`(적에 붙어 루프, 틱과 위상 맞춤) · 잔상 `afterimage`(출발점) · 섬광 `flash`/추적 `seek`/관통 `pierce` 화살 꼬리 · 폭우 `rain`/산탄 `scatter` 발사점 · 중시 `heavyarrow` 화살 + `heavyarrow_hit`(적중) · `parry_flash`(접점 + 히트스톱 60ms) · `shadowstep_ghost` · `aim_charge`(진행도 `min(5, floor(p×5))`) + `aim_line`(`stateFrames` 차지 f0/완료 f1, `src/systems/aimFx.ts`) · `dash_dust` · `dash_trail`(45ms 간격, 발도술·허보·잔상 노드면 무기 W1 setTintFill) · `hit_spark` → `alias` `hit_burst`.
- **굵은 예고** `src/systems/telegraph.ts`: 선 시트(16×16, 4px) TileSprite + **화살촉**(층 램프 22/18 삼각형) · 원/부채꼴 **진행도 6프레임**(scale R/22·R/27, `progressDriven` 없는 옛 시트는 루프 애니) · **수렴 오라** `telegraph_aura`(`TelegraphOptions.aura` — 결사병 돌진·보스 돌진·부채꼴·정렬 사격, 공격자 중심 추적) · 마감 직전 160ms 깜빡임 3배 · 플레이스홀더(4px 점선·원 + 닫히는 안쪽 원·오라 원). `setFloor(floor)` 로 층 램프.
- **상수** `FEEL.TRAIL`(BAND_PX 4·WIDTH_RATIO 0.6·W1) · `FEEL.SCREEN`(DEFAULT_FLASH·CRIT 0·BOSS_PHASE 0.35·HITSTOP_DESAT 0) · `FEEL.SECONDARY`(AIM_CHARGE_DIVISOR 5·DASH_TRAIL_TINT_NODES) · `FEEL.SYNC_HIT_FRAMES` · `ENEMY_FX.BOLD`(LINE_SCALE_Y 1·TIP·CIRCLE/CONE_BASE_RADIUS 22/27·PROGRESS_DIVISOR 6·AURA_SCALE 1·FINAL_MS 160). `DEPTH.TRAIL`·`DEPTH.SCREEN_FX`.
- **디버그**: `__lopad.trails()`(kind·샘플·몸통 색·폭·수명·점), `screen()`(flash·flashCount·lastFlash·death·desaturation·mode), `aimFx()`, `evolveTo(id)`, `telegraph()` 에 frame·scale·tip·aura·alpha·sheets.aura, `fx()` 에 texture·scale·tint, `setFeel({ trail, flash })`.
- 테스트 +4(`resolveFxColor` hex/팔레트 경로, 양산 필드 함수, 섬광 감쇠, 기존 차지 프레임 테스트는 `progressFrame` 으로 대체). 전체 96개. prettier·tsc·eslint·vitest·vite build 통과.
- 검증(헤드리스 `vite preview --port 4175`, Chromium swiftshader 960×540 — 1920×1080 은 너무 느려 샘플 창을 놓침): 시트 85개 로드, 누락 0. 만월: `wide_fx` + 리본 `sheet` 몸통 `#6f7e97`·폭 2·수명 220, 섬광 X1 0.22/40ms. 쌍격: 리본 몸통 `#3e2a62`(팔레트 경로 해석), 섬광 0.18. 지진: `quake` 1장이 f1~f7 재생(동시 1), 섬광 2회(f1·secondStage), 흔들림 4px/120ms. 분쇄·철벽(+guard_wave 바닥 0.95, ironwall 위)·거인(공격 동안 루프)·난무(f1~3 + 적중 3회)·출혈(적 중심 추적, hp 17→14 틱)·암살(shadowstep_ghost 출발점 → assassin)·섬광 화살 꼬리·폭우(5발 + rain)·추적(seek, 회전)·중시 조준(aim_charge 프레임 0→5, aim_line 시트, 취소 시 즉시 제거)·패링(parry_flash + 히트스톱). 대쉬: 허보 경로 `dash_dust`·`batto`·`longinvuln`·`dash_trail` 틴트 `6f7e97`·리본 1줄, 잔상 경로 `afterimage` + 틴트 `3e2a62`, 대검(노드 없음) 틴트 없음. 보스 페이즈: 섬광 0.35 → 감쇠, 채도 0.96 → 0. 예고: 선 시트 + 화살촉 + 오라(`sheet_telegraph_aura_fx`), 원 scale 1.818(= 40/22)·진행도 프레임·마감 160ms `final`, 부채꼴 scale 2.963(= 80/27) + 오라. 사망 암전. `setFeel({trail:false, flash:false})` → 리본 0·섬광 0. 콘솔 오류는 favicon 404 하나뿐. 스크린샷: 스크래치 `r43/r42-{b0 만월 리본, b1 잔월, c0 지진, c1 철벽, d0 출혈, d1 암살, e1 조준, e2 폭우, f0 패링, f2 보스 페이즈, g0 굵은 선, g1 원, g2 부채꼴+오라}.png`, `r43/dash-*.png`, 로그 `r43/log.json`.
- 미지원(안전하게 무시): 휘두름 시트의 `tailFrames`(메모 — 꼬리 루프는 잔월·피만 호출 쪽 옵션), `spawnNote`·`pivotNote`·`weapon`·`secondary`·`directionMeaning`·`trail.note`(메모), `followsPlayer`/`followsTarget`(호출 코드가 같은 동작을 명시하므로 필드로 분기하지 않음), 이펙트 `depth` 문자열(호출 코드가 같은 깊이를 명시, `fxDepthHint` 유틸만), `tint.when/color` 문장(노드 목록·색은 상수와 팔레트에서), `secondStage.atMs`(frame 시작 ms 를 씀 — 지금 둘이 같다).
- 후속(범위 밖): 보스 내리찍기가 대검 보조색 `crush` 를 빌려 씀(보스 전용 충격파 시트 필요 여부), 보스 페이즈 타이틀 카드(UI 파트), 플레이어 공격 시트가 없을 때 f0 앞당김 불가(40ms 늦음).

## 45라운드 반영: 비전투 이동 — 달리기(Shift 1.8배) · 워프(클리어한 방, 계약 §8) (2026-10-02)
결정: `decisions/2026-10-02-round-45-traversal-structures.md` Q1~Q3, 승인 #12 (계약 `ui-system-interface.md` §8 만 추가).
- **비전투 판정 (단일 기준)**: `RoomDirector.inCombat` = 방 상태 머신에 `active`(시련 웨이브·보스전 진행 중) 방이 있으면 전투. 순수 규칙은 `src/systems/traversal.ts` (`isInCombat`·`warpTargets`·`warpDenyReason`·`sprintStep`·`findSafeTile`).
- **달리기**: `KEYS.SPRINT = 'SHIFT'`, 배율·가속은 `data/player.json` `sprint { speedMult 1.8, accelMs 150, decelMs 120 }`. 일반 상태로 이동 중일 때만 목표 1.8배(가드·조준·패링 후딜·넉백 중엔 1로 감속). 전투가 시작되면 decelMs 에 걸쳐 1배로. **대쉬**는 거리·속도 그대로(배율 미적용)이고 대쉬 동안 달리기 배율을 유지해 끝나면 이어서 달린다. 공격 감속(`attackSlowMult`)은 곱해진다.
- **발밑 먼지**: 달리는 동안 140ms 마다 `dash_dust` 를 0.5배·알파 0.6 으로 (훅 끔). 시트가 없으면 작은 회색 점. 새 아트 요청 없음. `FxPlayOptions` 에 `scaleMult`·`alpha` 추가.
- **워프**: `uiCommands.warpTo(roomId)` → `host.ts` 가 판정(`check`) → 게임이 `pause()` 상태면 재개(`RESUMED`) → `Game.startWarp`. 조건 = 비전투 · 메뉴/개성 선택/보상/층 전환/워프 중 아님(상점 메뉴는 허용, 워프 시 닫음) · 방문 · 시스템 기준 클리어(시작 방 처음부터, 휴식 방 진입 즉시, 시련 클리어, 보스 처치) · 현재 방 아님.
  연출: 퇴장 섬광(X1 0.55/160ms) + 출발 먼지 → 140ms 뒤 착지점으로 `body.reset`·카메라 즉시(`updateCamera(true)`)·도착 섬광(0.4/220ms)·먼지 → `director.update()` 로 `ROOM_ENTERED` 즉시 → `WARP_DONE`. 입력 잠금 300ms(`neutralInput`), 무적 600ms, 진행 중 동작·넉백·조준·질풍 루프를 끊는다. 착지점 = `TileWorld.safePointInRoom`: 중앙에서 가까운 순, 3×3 바닥, 출구·상점 타일에서 3칸 초과(보스 방은 출구가 중앙이라 비켜 선다). 내부 이벤트 `WARP_STARTED`·`WARP_ARRIVED`(음향 매핑 없음).
- **계약 §8**: `UiSnapshot.inCombat`·`sprinting`·`warp { ready, blocked, targets, warping }`, `UiRoom.warpable`, `uiCommands.warpTo(roomId): boolean`, 이벤트 `WARP_DONE { fromRoomId, roomId, type }`·`WARP_DENIED { roomId, reason }`, 사유 `'combat' | 'busy' | 'unknown-room' | 'not-cleared' | 'current-room'`. 워프 선택 화면 키는 UI 가 읽는다(임시 제안 Tab).
- **디버그**: `__lopad.warp(id)` → `{ ok, reason }`(계약 경로), `warpInfo()`(ready·blocked·targets·warping·inCombat·currentRoomId·lockedMs·last), `sprintInfo()`(allowed·sprinting·mult·speedPx·vx·vy·dust).
- 테스트 +12(비전투 판정, 워프 목록·거부 사유·실제 층 그래프, 달리기 데이터·가감속, 착지점 3종, 스냅샷 warpable). 전체 108개. prettier·tsc·eslint·vitest·vite build 통과.
- 검증(헤드리스 `vite preview --port 4175`, 960×540, seed lopad): 시작 방 걷기 vx 96 → Shift 172.8(1.8배, 먼지 7회), 떼면 1배. 시작 방에서 `warp('start')` current-room, 미방문 휴식 방 not-cleared, 없는 id unknown-room. 휴식 방 진입 → targets [start] → 워프 ok: 중간 warping·busy·잠금 267ms·섬광 → 도착 (2040,2680)=시작 방 중앙, currentRoomId start, 카메라 즉시. 시련 방: inCombat true · blocked combat · Shift 눌러도 96 · warp combat 거부. 시련 클리어 후 pause() 상태에서 warp(rest1) → 자동 재개(UiPause 닫힘)·도착. 클리어한 시련 방으로 워프 후 다시 172.8. 콘솔 오류는 favicon 404 하나. 스크린샷 스크래치 `r45/`.
- 임시값·후속: 1층 어두운 바닥에서 먼지(0.5배·0.6)가 잘 안 보임(수치 조정 후보). 현재 방에는 워프 불가(복도 한가운데서 마지막 방으로 돌아가는 용도 없음). 보스 방 출구로 워프하면 출구 옆(3칸 밖)에 선다. 달리기 중 걷기 애니 속도는 그대로.
