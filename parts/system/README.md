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

## 46라운드 반영 (Q2·Q3) + 45라운드 Q11: 보스 충격파 `boss_slam` · 보스 예고 전부에 수렴 오라 · 달리기 먼지 (2026-10-02)
결정: `decisions/2026-10-02-round-46-fx-stage3-review.md` Q2·Q3, `decisions/2026-10-02-round-45-traversal-structures.md` Q11, 계약 `art-assets.md` §3.2 46라운드 줄, 시트 `assets/sprites/fx/boss_slam.json`(승인 #8 읽기).
- **보스 내리찍기** `Game.areaHit`: 대검 `crush` 차용 중단 → `ENEMY_FX.SLAM_ID = 'boss_slam'`(96×96, 피벗 48,48 = 슬램 지점, 바닥 깊이 `DEPTH.FX_GROUND`). 보조색이 없으므로 **JSON flash·shake 훅을 켠다**(X1 0.2/40ms f0, 4px/120ms) — 시트가 재생되면 `BOSS_WALL` 흔들림(6px/160ms)은 생략해 흔들림은 하나. 시트가 없으면 기존 링 + `BOSS_WALL`. 배율 = `radiusFitScale(R, hitRadiusPx ?? ENEMY_FX.SLAM_BASE_RADIUS_PX 40)` — 비율이 정수일 때만 그 값, 아니면 1(지금 R = 2.5칸 = 40 → 1). `ENEMY_FX_IDS` 에 `boss_slam` 추가(Preloader 로드·층 램프 `@f<n>` 변형 자동). `SheetJson.hitRadiusPx` 추가.
- **수렴 오라** `telegraph.ts`: `circle()` 도 `TelegraphOptions` 를 받고, `auraAt` 이 있으면 오라를 마커와 떨어진 공격자 위치에 두며 `aim()` 이 옮기지 않는다. 보스 내리찍기 원(착지점) + 오라(보스 히트박스 중심) 추가 → 보스의 예고(돌진·연속 돌진·부채꼴·정렬 사격·내리찍기) 전부 오라. 광각 부채꼴이 원으로 바뀔 때도 오라 유지. 일반 적은 결사병 돌진만(사수 조준선은 오라 없음 — 기존 그대로). 소환은 예고 마커가 없는 즉시 패턴이라 해당 없음.
- **달리기 먼지** `TRAVERSAL.SPRINT_DUST`: `SCALE_MULT 0.5 → 0.75`, `ALPHA 0.6 → 0.85`.
- **디버그**: `__lopad.lastSlam()` 에 `fx`(텍스처 키 또는 `'ring'`)·`fxScale`.
- 테스트: 기존 케이스에 `radiusFitScale`·`allFxSheetIds` 의 `boss_slam` 단언 추가(새 케이스 없음). 전체 113개(UI 파트 동시 작업분 포함). tsc·eslint·vitest·vite build 통과.
- 검증(헤드리스 `vite preview --port 4177`, 960×540, seed lopad, 플레이어를 판정 원 밖으로 옮겨 피격 흔들림 배제): 1층 `sheet_boss_slam_fx`(anim `boss_slam_fx_down`, 깊이 0.95, 배율 1), 섬광 `#fff4dc` 0.2/40ms, 흔들림 4px/120ms **1회**. 2층 `sheet_boss_slam_fx@f2`(녹색 램프). 오라: 보스 돌진 선·부채꼴·내리찍기 원 모두 `sheet_telegraph_aura_fx`(2층 `@f2`). 정렬 사격(황제)은 헤드리스 미확인(같은 `line + aura` 코드 경로). 콘솔 오류는 favicon 404 하나. 스크린샷 스크래치 `r46/r46-{f1,f2}-boss-slam-{a,b}.png`, 로그 `r46/r46.json`.

## 47라운드 반영: 상호작용 구조물 16종 (공통 C1·C2·C3·C5 · 1층 1-1~1-6 · 2층 2-1~2-6) (2026-10-02)
결정: `decisions/2026-10-02-round-47-structures-impl.md`(초안 5.3 Q5~Q18 추천안 적용, 전부 임시값), 설계 `parts/system/structures-draft.md`(구현 상태 표는 그 문서 6장), 계약 `ui-system-interface.md` §9(승인 #14), `art-assets.md` §5(승인 #13, 시트 `assets/sprites/structures/*.json` 17종 + `fx/fire_pool` 읽기).
- **데이터** `data/structures.json`(초안 5.1 형식): `rules`(E 키·24px·예산·문/시작점/보스 여유·타격 간격) · `text.reasons`(불가 사유 자리표시) · `structures[16]`(`id` = 계약 `UiStructureKind`, `kind` = hit/interact/pass/auto, `group` = filler/common/theme, `floors`, `roomTypes` 가중치, `chance`, `perFloor`/`perRoom`, `maxPerRoom`, `size` = 아트 footprint × `spriteScale`, `solid`, `place` = wall/wallPrefer/any/center/cellar, **`sprite` = 아트 시트 id 대응표**(crate → `{stage1: crate_f1, stage2: crate_f2, default: crate_f1}`, campfire → bonfire, cask(1-1) → barrel, agingBarrel → cask, hiddenWall → cellar_wall, cardTable → card_table, exchange → chip_exchange, dogRing → dog_ring, stakeBell → bet_bell, 나머지 같은 이름), `placeholder`(시트 없을 때 색·글자), `params`(수치), `text`(문구 자리표시)). 로더·검증 `src/systems/structures/data.ts`.
- **배치** `src/systems/structures/placement.ts` `planStructures(layout, stageId, seed, { forceAll })` — 시드 결정적(`<층 시드>:structures`), **소품보다 먼저**(그 칸은 `planProps(…, exclude)` 에서 제외). 1층 = 공통 + 1층 테마, 2층 = 공통 + 2층 테마, 3층 이상 = 공통만(짐 외형은 `crate_f1` 재사용). 예산: common·theme 각 3~4 **종류**(`countBy: "kind"`, filler = 짐·술통은 방마다 따로), 방당 E형 최대 2, 문 반경 4·시작점 반경 5·보스 출구/상점 여유, 구조물끼리 1칸. 중앙·저장고 자리를 먼저, 그다음 놓일 방이 적은 것부터. 숨은 벽은 문이 없는 벽면 바깥 여백(≥6칸)에 5×4 저장고가 전부 빈 공간일 때만(`planCellar`). 단단한 칸은 `TileWorld.setBlocked` 로 걸을 수 없는 칸이 되어 적 생성·워프 착지가 피한다. **URL `?structures=all`** = 그 층에 나올 수 있는 종류 전부(데모·검증용, 예산·확률 무시).
- **런타임** `src/systems/structures/StructureSystem.ts`(Game 이 host 로 필요한 것만 넘김), 그림 `src/world/StructureView.ts`(시트 상태 `idle/used/broken/active/hit/ready` + 시트별 `used1·used2`(카운터), `damaged1·2`·`*_top`(숨은 벽: 북쪽 벽 외엔 윗면), `idle_f2·used_f2`(2층 묘), `stateLoop`, 술통 구르기 회전(`rollDrawnFacing: down`), 룰렛 `stopFrames`, 링 `stakes`(말뚝만 단단)·`flagpost`(E 기준점), 화로 `fireBox`, 정수 배율 2(링·룰렛). 시트가 없으면 플레이스홀더 사각형 + 글자, 숨은 벽은 호박색 1px 금). 층 램프 스왑은 기존 `@f<n>` 변형. 단단한 구조물 = 정적 존(플레이어·적 충돌).
  - 타격형: 근접 판정(`meleeSwing` 사각형 — 일반·대쉬 공격·충격파·쌍격), 화살(`tickShots`, 관통 규칙 그대로), 가드 해제 밀쳐내기(술통만 굴림). 같은 구조물 300ms 간격.
  - E형: `KEYS.INTERACT = 'E'`, 플레이어 몸 중심에서 발판(링은 판돈 깃대)까지 24px 안 최근접 1개, 비전투만(`reason: 'combat'`), 메뉴·연출·워프·보상·도전 중 `busy`. 묘는 E 2초 누르기(이동하면 0). 구조물 메뉴(`cancelKey '0'`, `structureId`)가 열려 있는 동안 플레이어 입력 잠금(`neutralInput`), 게임은 계속 진행. 선택지는 '1'~'8' + '0'(UI 요청, 넘치면 8개까지).
  - 도전(투견 링·흉패): `RoomDirector.startChallenge(roomId, spawns, onDone, at?)` 가 클리어한 방을 다시 `active` 로(문 잠금) → 45라운드 비전투 판정(달리기·워프)과 자동 일관. 전멸 시 `cleared`·문 열림. 투견 링 시간 초과는 `abortChallenge()`(남은 개 사라짐).
  - 시련 웨이브 배율 `RoomDirectorHost.waveMods(room)` (판돈 종 HP·+n, 룰렛 적 수 ×1.5) — `rules.scaleWave`.
- **전투 훅(Game)**: `rollDamage(mult, forceCrit, kind)` 에 구조물 피해 배율(취기 공격·3단 대쉬 공격, 룰렛 치명만/선 넘으면 끝)·치명 가산(룰렛), 처치 보상 배율(판돈 종·룰렛 배수 판), 근접·화살 적중 후 화상, 주운 골드 빚 상환, 대쉬 경로 점화, `GameState.structureDefense`(취기 방어 −1/단, 층 전환 시 0).
- **감각**: `KillKind` 에 `'environment'`(술통 충돌·불바다 처치) → 층당 최대 4. `KILL_KINDS` 상수. 정산(`gainedThisStage`)은 집합 크기라 자동 반영.
- **계약 §9 채움**: 스냅샷 `interactable`(screen = 게임 캔버스 픽셀, 카메라 스크롤·배율 반영) · `statuses`(debt·drunk·stakes·embers·fireWeapon·ring·roulette·aging·pawn 순) · `map.rooms[].structureDot`(사용 가능한 E형이 남은 방) · 메뉴 6종(`cards`·`exchange`·`pawn`·`grave`·`ledger`·`counter`) · 이벤트 `STRUCTURE_USED`·`STRUCTURE_BROKEN`·`STRUCTURE_RESULT`·`CHALLENGE_STARTED`·`CHALLENGE_CLEARED` + 기존 `GOLD_CHANGED`·`PLAYER_DAMAGED`(피 판매·최대 HP 감소)·`PLAYER_HEALED`·`STORY`(모닥불 휴식 메모). `TextMenu.open(…, footer, { cancelKey, structureId })`.
- **내부 이벤트**(음향 훅) `STRUCTURE_HIT/BROKEN/USED/FIRE/BELL/ROULETTE`, `CHALLENGE_STARTED/CLEARED`, `PLAYER_SECONDARY` phase `'block'`(가드로 받아냄). `audioMap.ts` 는 **새 효과음 없이 기존 효과음에 임시 연결**(짐 hit_enemy, 술통 guard_push, 숨은 벽 door_open, 궤짝·장부·환전·전당 shop_buy, 묘 save, 모닥불·카운터 potion_use, 숙성 통 pickup_potion, 불 dash/boss_fan, 종 boss_telegraph/boss_phase, 룰렛 menu_move, 도전 door_close/trial_clear/menu_cancel).
- **기타 변경**: `Mob.speedMult`(웅덩이 감속, 일반 적만) · `Player.envSpeedMult` · `Projectile.fire` · `PassiveSet.remove/setLevel`(전당포) · `GameState.bonusSouls`(묘 '기록한다' 영혼은 즉시 메타 적립, 결과 화면에 합산 — 세이브 형식 그대로) · `GameState.gotoStage`(디버그 층 이동) · Preloader 가 `sprites/structures/<id>.json` 을 로드(`normalizeStructureSheet`: fps·loop·directions·pivot 생략 허용) · `fire_pool` fx · `STRUCTURE_FX` 상수.
- **디버그**: `__lopad.structures()`(id·종류·방·중심·타일·상태·그림 상태·아트 여부·다 씀) · `structureState()`(빚·취기·판돈·불씨·불붙은 무기·전당·링·룰렛·웅덩이·최근 결과 20) · `gotoStructure(id 또는 종류)` · `pressE()` · `hitStructure(id 또는 종류)` · `interactable()` · `statuses()` · `gotoFloor(n)`.
- 테스트 +23(`placement.test.ts` 10: 결정성·층별 종류·예산·방당 E형·겹침·문/시작점 회피·짐/술통·층별 시트·forceAll·소품 제외 / `rules.test.ts` 11: 데이터 대응표·검증·가격·빚·취기·판돈·웨이브·패·전당·환전·불씨/숙성/링 / `senses.test.ts` +1). 전체 144개. prettier·tsc·eslint·vitest·vite build 통과.
- 검증(헤드리스 `vite preview --port 4178`, 960×540, seed r47, katana): 아래 "구현 상태" 표의 확인 항목 전부. 스크린샷·로그 스크래치 `r47/`(f1-*, f2-*, n-*, c-*, log.json, logb.json). 콘솔 오류 0(AudioContext 자동재생 경고만).

## 48라운드 반영 (Q7·Q8): 개성 선택 — 획 찢기 연출 · 15초 회피 시험 (2026-10-02)
결정: `decisions/2026-10-02-round-48-playfeel-route.md` Q7·Q8 (14라운드 Q3 의 5초 리듬을 대체, 30라운드 획 예시 패널·`strokeFeatures` 유지).
- **획 연출** `src/systems/strokeFx.ts` + 순수 계산 `strokeFxMath.ts`(`STROKE_FX` 임시값): 절차 생성 어두운 결 표면 → 지나간 자리를 RenderTexture 에 즉시 '찢긴 틈(검정) + 들뜬 가장자리(G06·층 램프 3) + 식은 잔불(램프 4·7)'로 굽고(필기처럼 남음), 위에 ADD Graphics 로 최근 조각만 백열(fx.core X0/X1) → 1층 강조(램프 9·10) 순으로 `COOL_MS` 2.6초 동안 식힘. 획을 떼면 그 획 전체가 `FLARE` 로 한 번 더 번쩍. 불티 파티클(진행 반대쪽 ±65°, 중력), 펜 끝 빛 번짐, 650px/s 이상이면 미세 흔들림(90ms 간격). 속도 → 틈 폭 2~9px·빛 세기 0.55~1. 마지막 획 뒤 0.9초 보여 주고 0.65초 사라짐.
- **회피 시험** `src/systems/dodgeTrial.ts`(수치 `DODGE_TRIAL`·난이도 `trialStep`·측정 분류·평가 `evaluateDodge`, Phaser 없음) + `dodgeTrialRunner.ts`(화면). 메인 카메라 2배(경기장 중심), 글자는 확대 없는 UI 카메라(`ADDED_TO_SCENE` 로 새 오브젝트를 UI 카메라에서 숨김). 원 반지름 6.5타일, 투사체는 +1.6타일 고리에서. player 시트(걷기·대쉬·피격), `player.json` 속도·대쉬(거리·시간·쿨·무적). 패턴: 조준탄(선 예고) 0초~, 부채꼴(boss_fan_shot, 부채꼴 예고) 2.5초~, 교차(수직 두 지점 연발) 5.5초~, 원형 확산(원 밖 한 점에서 안쪽 반원, 원 예고) 8.5초~. 간격 1150→470ms·속도 6.5→10.5타일/s·예고 520→300ms(지수 1.4), 마지막 3초 420ms·×1.25·230ms·동시 2패턴. 맞으면 player_hit + 흰 칠 + 흔들림 + 진행 방향 2.2타일 밀려남(180ms) + 650ms 무적. 걸어서는 못 나가고 밀려서 원 밖이면 **즉시 종료**(`FALL_MODE: 'end'`, `'return'` 도 구현). 체력 없음.
- **측정·평가**: 투사체별 최근접 틈(판정 원 가장자리 사이) → 3타일 안만 회피로 셈, ≤0.6타일 직전 / ≥1.8타일 멀찍이. 최근접 직전 280ms 안에 대쉬 시작 + 틈 ≤1.2타일 = 대쉬 직전 회피. 축: far·close(비율), dashDodge(4회 포화), endure(=(피격−2)/7, 떨어지면 1), clean(무피격 끝까지 1, 1회 0.5), survival. 리듬 3축 자리 = keyMove(이동 프레임 비율)·keyAttack(0.5 + 0.4(close−far) + 0.3 endure)·keyDash(대쉬/8). 무기 가산: 활 0.5far+0.25clean · 단검 0.2close+0.3dashDodge+0.25clean · 칼 0.35close+0.15dashDodge · 대검 0.5endure. `chooseWeapon(features, weapons, P, bias)` = 거리 − 가산 최소(가산 없으면 기존과 동일, `scores` 반환 추가). 희귀 = clean×survival×(0.5+0.5max(far,dashDodge)) ≥0.75 → 기록만(무기 결정 미반영).
- **화면 흐름**: 획 3/3 → 자국 사라짐 → 안내 2.2초("원 안에서 15초를 버텨라", 이동 가능) → 15초(라벨에 남은 시간·피격, 원 테두리 호가 줄고 마지막 3초 맥동) → 결과 한 줄 1.9초(자리표시 6종) → 경기장 흐림 + 기존 운명 문구 → Game.
- **디버그**(`?debug=1`) `window.__lopadSetup()` = { phase, strokes, strokeFx 요약, trial 스냅샷, camera, evaluation, features, weapon } + `.skipToStrokes(name)` · `.autoStrokes('fast'|'slow'|'round')`(같은 포인터 경로) · `.skipTrial(프리셋 'far'|'close'|'dash'|'tank'|'fell'|'clean' 또는 DodgeSample 일부)`.
- 테스트: `dodgeTrial.test.ts` 12 · `strokeFxMath.test.ts` 4 · `personality.test.ts` +7(가산·중립 획 + 회피 결과 → 활/단검/칼/대검/희귀).
- 임시 위치: 이번 작업 범위상 `Constants.ts`·`data/personality.json` 을 고치지 않아 수치를 `DODGE_TRIAL`·`STROKE_FX` 에 둠 → 정리 때 옮길 것. `personality.json rhythm.durationMs/attackSaturation` 은 더 쓰지 않음(`dashSaturation` 만 사용), `RHYTHM_DOT` 상수 미사용.

## 48라운드 반영 (Q1~Q6·Q9~Q11): 카메라 2배 · 근접 1.5배 3연격 · 노드 지도(1~2층) · 탄생 연출 · 구조물 재배치 · 워프 비활성 (2026-10-02)
결정: `decisions/2026-10-02-round-48-playfeel-route.md`, 계약 `ui-system-interface.md` §10(승인 #17), `art-assets.md` §6(승인 #8 시트 JSON 읽기), `parts/story/world-bible.md` §1~2-0 열람(승인 #16, 노드 자리표시 이름용). **범위 1~2층.** `Setup.ts`·`personality.ts`(Q7·Q8, 다른 에이전트)·`src/ui/**` 는 건드리지 않음.
- **카메라 2배** `CAMERA.ZOOM = 2`(게임 월드 카메라만, UI 씬 무관). `updateCamera` 는 보이는 반폭(`width/(2·zoom)`)으로 클램프하고 스크롤 = 중심 − 캔버스 반폭, 데드존·스냅·흔들림은 화면 px → 월드 px(÷zoom, 흔들림 체감 유지). 구조물 `screen` 은 기존 식이 zoom 반영(캔버스 픽셀 그대로). 디버그 글자·임시 진화 배너는 역배율. 데미지 숫자는 월드와 함께 2배(치명 44px 상당 — 검수 후보). 적 사거리 임시 보정: 사수 `keepMin/MaxTiles 8/14 → 6/10`, 결사병 `triggerTiles 10 → 8`(2배 화면 세로 약 17타일 안에서 보이게).
- **근접 1.5배 + 3연격** `data/weapons.json`: 칼·대검·단검 `hitbox` width/height/reach ×1.5(활 유지) + `combo`(모양·버퍼·리셋·마지막 타 회복·타별 피해·크기·길이·다음 타 허용·판정 시간). 상태 머신 `src/systems/combo.ts` `ComboTracker`(press → poll: 버퍼 안 입력을 다음 타 허용 시각에 시작, 마지막 타 뒤 회복, 끝난 뒤 resetMs 지나면 1타, 대쉬·멈춤에서 reset). 판정 = **몸 중심(발 위 10px)** 부채꼴(칼·대검) / 찌르기 직사각형(단검) — 물리 영역은 외접 사각형, 겹친 적을 모양으로 다시 거름. 판정 시작 = 몸 시트 `hitFrames[0]` 시작(연격만, 기존 단일 공격은 즉시), 판정 길이 = max(data activeMs, 시트 `activeFrames` 구간). 아트 JSON 메모가 있으면 데이터 대신: `hitRadiusPx`·`arcDeg`·`arcFromDeg/arcToDeg`(비대칭 호·휘두름 방향, left 는 좌우 반전) · `thrust{lengthPx,widthPx,angleDeg,fromPx}` · `cancelFromFrame`(다음 타 허용) · `hitFrames`. 아트 메모로 그린 모양에는 타 크기 배율을 빼고 대쉬 배율(1.5)·진화·강화 배율만 곱한다. 몸 `player_<w>_combo<n>` · 무기 `weapons/<w>_combo<n>`(없으면 `<w>_attack`) · 이펙트 `fx/<w>_combo<n>`(없으면 `<w>_slash`).
  - 진화와의 관계(임시): 연격 시트가 있으면 진화 베기(거합·만월·쌍격·난무)는 **마지막 타**에, 없으면 기존처럼 매 타. 대검 충격파(파쇄·지진·분쇄의 링·흔들림·지진 2단·분쇄 탄 지우기)는 **마지막 타만**. 쌍격·난무 추가 타·출혈·잔월·중압·거인·대쉬 공격·그림자 걸음 확정 치명은 매 타 그대로.
  - 무기를 든 특수 자세 `player_<w>_special`(+`weapons/<w>_special`) 구간은 JSON `phases`: 패링 ready+window(창 길이에 맞춤) → 성공 riposte+recover / 실패 recover(후딜 길이), 가드 enter → 누르는 동안 `loopFrames` 반복 → 떼면 release+recover, 그림자 걸음 arrive+primed(순간이동 뒤). 활 조준 `player_bow_aim` = 진행도 프레임 `min(5, floor(p×5))` 유지, 발사 = `releaseFrame`. 오버레이는 텍스처 프레임 번호에서 열을 꺼내 구간 재생·유지(`#hold`)에도 같은 열.
- **노드 지도** `data/route.json` + `src/systems/route.ts`: 1층 = 여정 3(황폐한 탄생지 → 버려진 길(쉬운 전투: 징집병 3) → 국경 초소(휴식)) + 두 갈래 × 3단계(전투 3·상점 1·휴식 1·이벤트 1을 층 시드로 섞음, 같은 갈래 다음 단계로 항상 + 확률 0.35 로 옆 갈래 교차, 어느 길이든 전투 ≥1 이 될 때까지 다시 섞음) + 보스. 2층 = 갈래 6 + 보스(진입 두 갈래). 노드 id `c<단계>r<줄>`, 이름은 자리표시(route.json `names`). 3층 이상은 기존 방+복도.
  - 전투장 `src/systems/mapgen/arena.ts`: 내부 40×24(보스 44×26) + 벽 1칸 + 빈 여백 8칸(숨은 저장고 자리), 복도·문 없음. 시작점 왼쪽 3칸(탄생지는 가운데), 출구 오른쪽 2×2, 상점 노드는 위쪽 가운데 2×2 상점 타일. 카메라 경계 = 내부 + 벽(저장고가 있으면 넓힘). 바닥 `roomFloors` 키: 여정 = start, 전투 = trial, 휴식 = rest, 보스 = boss, **상점 = rest, 이벤트 = start**. 방 상태 머신 종류: 탄생지·상점·이벤트 = start(들어서면 클리어), 버려진 길·전투 = trial, 국경 초소·휴식 = rest(입장 회복), 보스 = boss.
  - 진행: 노드마다 `scene.restart({ mode: 'node' })`(층 상태 유지, `STAGE_STARTED`·층 자막은 층 시작만) → 밝아짐 320ms·입력/전투 시작 잠금 450ms → `ROUTE_NODE_ENTERED` → 노드 클리어 500ms 뒤 출구 → 출구에 서면 입력 잠금 + `ROUTE_CHOOSE_OPEN` → `uiCommands.chooseNode(id)`(available 만 true) → 암전 280ms → 다음 전투장. 보스 노드는 기존 보상 → 가운데 출구·상점 → 다음 층(층 진입 갈림이면 빈 전투장에서 바로 선택). UI 렌더러가 없으면 숫자 키 1·2 로 고른다.
  - 재해석(임시): 시련 총수 `trialsTotal` = 어느 길로 가도 거치는 최소 전투 수, `trialsCleared` = 깬 전투(버려진 길 포함), `bossUnlocked` = 다음이 보스, 시련 보너스·불씨는 전투마다, 휴식 회복 = 휴식 노드·국경 초소 입장 50%, 상점 = 상점 노드(들어서면 바로) + 보스 뒤(기존), 세이브 = 층 전환 때(기존, 노드 진행은 저장 안 함 — 이어하기는 그 층 처음부터).
  - 구조물(Q11) `route.json kinds.*.structures` + `planStructures(…, { node: { kinds, budget, reserve } })`: 전투 = 짐·독주 술통·증류 화로·판돈 종·룰렛·투견 링, 휴식 = 모닥불·숙성 통·무명 전사의 묘·선술집 카운터, 상점 = 외상 장부대·전당포·환전대·궤짝·패 탁자, 이벤트 = 숨은 벽·궤짝·짐, 국경 초소 = 모닥불·묘, 버려진 길 = 짐·술통(filler만), 보스 = 술통. 층 테마 제한 유지(1층 전투 = 화로(+짐·술통), 2층 전투 = 판돈 종·룰렛·투견 링). 노드 예산 = filler 밖 종류 수(전투 1~2·휴식 2~3·상점 2~3·이벤트 1~2), 방 종류 가중치·방당 E형 상한·투견 링 최소 폭은 노드에서 무시, 시작점·출구·상점 둘레 3칸 비움. `?structures=all`·`VITE_DEMO_STRUCTURES=all` = 그 노드에 허용된 종류 전부.
  - 층 상태 이어받기 `StructureSystem.exportFloorState/importFloorState`(빚·취기·판돈 종·불씨·불붙은 무기·전당·궤짝 수·숙성) — `GameState.structureCarry`. 노드 지도에서는 불씨가 모닥불 없는 노드에서도 쌓이고, 앞 노드 숙성 통의 물약은 익으면 자동으로 받으며, 빚 정산은 장부대 정의로 보스 처치 때. 전당포에 맡긴 물건은 상점 노드를 떠나면 되찾을 수 없음(후속 검토).
- **워프 비활성**: `warp = { ready: false, blocked: 'busy'|'combat', targets: [], warping: false }`, `warpTo` 는 항상 거부(전 층). 달리기는 그대로(비전투).
- **탄생 연출** `src/systems/birth.ts`(`BIRTH` 상수): 흐름 = **개성 선택(Setup) → 황폐한 탄생지 노드 시작 시 탄생**(Setup 수정 없음 — 씬 전환 지점 `mode: 'new'` 에서 `GameState.birthPending`). 카메라 2→4배 450ms → `player_birth` 재생(별도 스프라이트, 피벗 16,31) + `fx/birth_dust` `segments.swirl` 루프 → `burstFrame` 프레임 진입 시 `segments.scatter` 1회 + 잔불 섬광(0xffb050·0.35·160ms) + 흔들림 2px·180ms → 애니 끝(= idle down 0)에 플레이어로 교체 → 150ms → 4→2배 750ms(합 ≈ 5초). 단계 전환은 애니 이벤트 기준(느린 프레임에서도 그림과 맞음, 안전장치 3배). 아무 키·클릭 = 건너뛰기(진입 250ms 뒤부터). `BIRTH_STARTED`/`BIRTH_DONE` 발행, 그동안 조작·전투 잠금, 그림자도 숨김. 시트가 없으면 흙 알갱이 소용돌이 + 플레이어 알파 0→1 + 불티 폴백. `?nobirth` 로 생략(검증용).
- **발밑 그림자**: 시트가 있는 플레이어·적은 기존대로 타원 그림자(`SPRITES.SHADOW_ALPHA 0.35`)를 그린다(탄생 연출 중 숨김).
- **디버그**(`?debug=1`): `__lopad.route()`(계약 UiRoute + 종류·클리어·출구·경로·선택지·전투장·잠금) · `openRouteChooser()` · `chooseNode(id)` · `gotoNode(id)`(링크 무시, 층 상태 유지) · `gotoExit()` · `combo()`(마지막 타·허용 시각·다음 타·마지막 판정 모양/원점/맞은 수·오버레이) · `birth()`·`skipBirth()` · `camera().camZoom`.
- 테스트 +18(새 17 + `spriteDefs` 1): `route.test.ts` 9(층 범위·결정성·1층/2층 구성·연결성(모든 노드 도달·다음 단계만·전투 ≥1)·상태 표기·전투장 모양·노드 구조물 허용/테마/forceAll/예산·비움 칸) · `combo.test.ts` 8(1→2→3→회복→1·버퍼·리셋·cancelFromFrame·부채꼴·찌르기·데이터 1.5배·아트 메모 우선/반전) · `spriteDefs.test.ts` 갱신(+오버레이 동작·애니 키 해석). 전체 191개. tsc·eslint·vitest·vite build 통과.
- 검증(헤드리스 `vite preview --port 4181`, 960×540): 탄생(4배 → 잔불 → 2배, 건너뛰기) · 노드 선택(UI 지도 Enter) · 칼/대검/단검 3연격(판정 모양·맞은 수) · 가드 유지·패링·활 조준 자세(무기 오버레이) · 노드별 구조물(`structures=all`) · 보스 → 2층 진입 갈림 선택 → 2층 전투(룰렛·판돈 종). 스크린샷 스크래치 `r48/`. 헤드리스는 프레임이 느려 씬 시계(delayedCall)가 실제 시간보다 늦다 — 연격 타이밍 체감은 실기 확인 필요.
- 임시값(전부 검수 대상): 연격 수치(칼 350/170/220ms·피해 1.0/0.6/0.8·허용 250/80ms, 대검 480/460/650ms·0.75/0.75/1.1·허용 340/320ms, 단검 160/150/280ms·0.9/0.9/1.2·허용 90/80ms, 버퍼 220/300/200ms, 리셋 380/450/300ms, 마지막 타 회복 160/260/120ms), 판정(칼 R33 140°/130°/170°, 대검 R51 190°/200°/270°, 단검 찌르기 24×8(−8°)·24×8(+10°)·28×10 — 아트 메모 값, data 기본값도 같게), 노드 수치(교차 0.35·출구 지연 500ms·암전 280/320ms·진입 잠금 450ms·예산), 탄생 수치, 적 사거리 보정, 노드 이름.

## 49라운드 반영 (1·2절): 획 부스러기·빛 터짐 · 회피 시험 → 시작 감각 등급 (2026-10-02)
결정: `decisions/2026-10-02-round-49-playtest2.md` 1절(획 연출)·2절(회피 시험 → 체급 보상). 작업 파일: `Setup.ts`·`personality.ts`(+test)·`strokeFx*.ts`·`dodgeTrial*.ts` 만.
- **부스러기** `StrokeFx` 2번째 파티클(보통 혼합): 긁힌 화면 조각(gray 5~8)·검은 재·잔불 조각(1층 램프 4)이 위로 튀었다가 중력(540)으로 떨어짐. 이동 px 당 0.1 × (0.5 + 빛 세기), 한 번에 최대 8, 누를 때 6·뗄 때 그 획을 따라 16.
- **빛 터짐** `StrokeFx.burst(onPeak, onDone)` (`STROKE_FX.BURST`, 타임라인 `burstAt`): 마지막 획 0.45초 뒤 → 흔들림(620ms, 0.0045) + 획 전체 맥동·달아오름 + 부스러기 → 백열 섬광이 각 획 경로를 따라 달림(420ms, 머리 불티) → 획 위 28점에서 무게중심 바깥으로 광선(쐐기 3겹, 길이 180~560px)·중심 빛 번짐 → 화면 하얗게(190ms) → **가장 하얀 순간 = 회피 시험 시작**(긁힌 화면 걷어냄) → 유지 110ms → 760ms 동안 걷힘. 무기는 3획 직후(빛 터짐 전)에 정해 둔다. Setup 단계 `'burst'` 추가.
- **무기 = 3획만** `chooseWeapon(features: StrokeFeatures, weapons, P)` — 획 3축(`STROKE_KEYS`)만으로 가중 거리, `bias`·`scores` 제거. 회피 시험은 무기 결정에서 완전히 제외. `FATE_DECIDED`(UI) `features` 는 이제 획 3축만.
- **회피 시험 → 등급** `gradeTrial(sample)`: 점수 = 버틴 비율×100 − 피격×6 − 떨어짐 15 → S ≥90(+3) · A ≥70(+2) · B ≥45(+1) · C(+0). 결과 화면(자리표시): 한 줄 + "등급 X · 시작 감각 +N (버틴 시간 · 피격)", 운명 문구에 "시작 감각 +N (시험 등급 X)". 기존 회피 축·무기 가산(`evaluateDodge`·`WEAPON_BIAS`·희귀)은 삭제, 회피 거리 분류·대쉬 직전 회피는 기록만.
- **보상 전달**: Game 시작 데이터 `{ mode: 'new', weapon, playerName, senseBonus }` (`senseBonus` 0~3 추가, 기존 형식 유지). 감각 가산은 Game 쪽(다른 에이전트).
- **경기장** `buildArena(shape, rnd)`: 4px 칸 격자(±176×±108 px), 모양 무작위 — 원(일렁임 4.5%) · 타원(가로/세로 1.3~1.7, 기울기 ±0.45rad) · 불규칙 다각형(6~10 꼭짓점, 반지름 0.7~1.22, 가로 1.15) · 여러 섬(가운데 0.56R + 둘레 2~4섬, 다리 폭 8px). 투사체 고리 = 바닥 외곽 타원 + 1.6타일(세로 ≤132px), 남은 시간 호도 외곽 타원.
- **갉아먹힘**: 칸마다 (가장자리 BFS 깊이 + 잡음 0~2.6칸) 순위 → 본 시험 1.5초부터 끝까지 무너진 비율 = 0.7 × 진행^1.1 (끝에 30% 남음, 다리가 먼저 끊김). 무너지기 700ms 전부터 균열(어두워짐·검은 금·잔불 점, 마지막 35% 떨림), 무너지면 칸이 사라지고 부스러기가 바닥 뒤로 떨어짐. 아래쪽이 빈 칸 밑에 절벽 면(5px). 걸어서·대쉬로는 못 나감(발 둘레 2px 4점, 여유가 나빠지지 않는 쪽으로만·축별 미끄러짐). 발밑이 무너지거나 밀려나 바닥 밖이면 떨어짐(바닥 뒤로 가라앉음) → 즉시 종료.
- **난이도 상향**: 간격 950→380ms · 속도 7.5→12타일/s · 예고 460→250ms(지수 1.3) · 마지막 3초 340ms·×1.25·200ms·동시 2패턴 · 부채꼴 2초/교차 4.5초/원형 7초부터 · 부채꼴 4~8발 · 교차 3~7연발 · 원형 14~24발 · 밀려남 2.6타일 · 무적 600ms.
- **디버그**(`?debug=1`) `__lopadSetup()` += `result`·`senseBonus`·`startData`·`forcedShape`, `strokeFx` 요약 += `debrisAlive/Emitted`·`burst{t,trace,rays,white,peaked}`, trial 스냅샷 += `elapsedMs`·`onFloor`·`god`·`arena{shape,cells,alive,aliveFrac,warn,bounds,spawn}`. `.skipTrial('S'|'A'|'B'|'C'|'fell' 또는 DodgeSample 일부)`(빛 터짐 중에도) · `.trialShape(shape?)` · `.trialWarp(ms)` · `.trialGod(on)` · `.holdBurst(ms|null)`.
- 테스트: `dodgeTrial.test.ts` 17(등급 3·모양/갉아먹힘 7·난이도 상향 1 포함) · `strokeFxMath.test.ts` 7(+빛 터짐 타임라인·경로 자르기·광선) · `personality.test.ts` 10(3획만·key* 무시).
- 검증(헤드리스 `vite preview --port 4191`, 960×540): 실제 마우스 3획(부스러기) → 빛 터짐 단계별(holdBurst) → 시험(4모양 × warp 7/12/15초, 남은 비율 0.74→0.49→0.30) → 봇 플레이(떨어짐 → C/+0) → 운명·시작 데이터, 등급 프리셋 5종(senseBonus 3/2/1/0/1). 스크린샷 스크래치 `r49setup/`. 콘솔 오류 0.
- 임시값(전부 검수 대상): 등급 기준(감점 6/15, 90/70/45), 갉아먹힘(1.5초·30%·^1.1·잡음 2.6·경고 700ms), 모양 수치, 난이도 상향 수치, 빛 터짐 시간·광선 수치, 부스러기 수치, 결과·안내 문구.

## 49라운드 반영 (3·4-2·6·7): 지역 흐름 · 실내 느낌 제거 · 세트 배치 · 탄생 전장 조작 안내 (2026-10-02)
결정: `decisions/2026-10-02-round-49-playtest2.md` 3·4-2·6(특수 노드 기능은 중앙)·7, 계약 `art-assets.md` §7.3(지역 타일·세트 소품·전장 소품), `ui-system-interface.md` §11.2(UiRouteNode.region·desc). **Game.ts·Preloader.ts·spriteDefs.ts 는 이 작업에서 고치지 않았다.** 연결 코드는 메인 세션이 붙인다(아래 "연결"). 연결 전에는 새 코드가 동작에 영향을 주지 않는다.
- **지역 흐름** `data/route.json floors.*.regionByCol` + `regions`: 1층 단계 0~6 → 황무지(waste)·황무지·성문(gate)·외곽 거리(outer)·외곽 거리·양조 구역(brewery)·지배자의 연회장(hall). 2층은 임시 지역 2개(도박 골목 alley·도박장 안채 den, 지역 타일셋 없음 → stage2). `route.ts` `regionIdOf/regionOf/regionDesc/regionEdge/regionTilesets/regionIds`, `RouteState.toUi()` 가 노드마다 `region`(지역 이름)·`desc`(노드 종류별 → 지역 기본, 자리표시)를 채운다(계약 §11.2).
- **지역 타일셋** `tileskin.ts` `regionSkins`(이름 → TileSkin) · `namedTilesetJsonPath/TextureKey` · `skinFor(floor, tileset)` = 지역 타일셋(로드됐으면) → 층 타일셋 → 플레이스홀더. 파일은 `tiles/stage1_<region>.json`(인덱스 표 v3 그대로).
- **실내 느낌 제거** `mapgen/arena.ts` `ArenaEdge`(route.json `arena.edge` + 지역 `edge` 덮어쓰기): 네 변마다 깊이 0..maxInset 계단 프로필(run 칸마다 ±1~2)로 안쪽을 깎아 담·잔해·건물 앞면 경계(벽 타일 = 지역 타일셋 5·6)를 만든다. 모서리에서 떨어져 나간 조각은 비우고(중앙 기준 연결 보장), 위·아래 벽 일부는 열린 틈(원경 void)으로 남긴다. 시작점·출구 둘레(keepClearTiles)는 깎지 않음. 방 내부 사각형·카메라 경계는 그대로. 열린 틈은 `TileWorld` 가 칸 단위 충돌(`edgeVoidTiles`)로 막는다. `spawnExactCenter`(탄생 전장 = 정확히 중앙), `shopCenter`(상점 2×2 중앙), `ArenaInfo.center` 추가. 48라운드 `spawnCenter`(중앙 왼쪽 4칸, 무기 시험장이 씀)는 그대로.
- **세트 배치** `structures/setpiece.ts` `planSetPiece` + route.json `setPieces`(노드 종류 → `kinds.*.setPiece`): 휴식·국경 초소 = 중앙 모닥불 광장(광장 문양·둘레 돌 8·벤치, 반지름 6에 숙성 통·묘·카운터) · 상점 = 중앙 노점 거리(상인 = 중앙 상점 타일, 길 ±1줄은 구조물 금지, 길 양옆에 장부대/전당포·환전대/궤짝·궤짝/패 탁자·패 탁자 + 노점 천막·등불) · 이벤트 = 중앙 사건 장소(잔해 + 궤짝 + 파편 고리) · 전투·버려진 길 = 엄폐 담(벽 섬 2~3, 바닥 연결을 깨면 되돌림) 둘레에 짐·술통(`fillerNear`) + 앵커 옆 증류 화로/판돈 종 · 보스 = 연회 탁자·깃발 · 탄생 전장 = 아래 튜토리얼. 결과 `fixed` 를 `planStructures(node.fixed)` 가 먼저 정확한 자리에 놓고, 놓인 종류는 예산에서 빼서 나머지만 무작위로(세트 우선, 무작위는 보조). 벽가 구조물은 깎인 가장자리에서 안쪽으로 밀어 넣는다(`slideToWall`). 소품 시트 `structures/set_<region>_<name>`(전장은 `battlefield_*`)은 `allStructureSprites()` 기본값에 포함(매니페스트에 있으면 로드). 그림 `src/world/SetPieceView.ts`: 시트가 있으면 시트, 없으면 옅은 도형.
- **탄생 전장 조작 안내** `tutorial.ts`(단계 머신, Phaser 없음) + `tutorialDirector.ts`(EventBus 연결): 표식 5개 = 이동(도착) → 공격(허수아비 근처 2번, 활은 조준 원뿔 14칸·25°) → 대쉬 → 보조 동작(패링 성공·실패·가드·그림자 걸음·조준) → 약한 적(징집병 2, 체력·공격 ×0.5, `RoomDirector.startChallenge`) → 끝(그때 출구). 표식에 다가가면 안내 문구(STORY notice), 켜지자마자 문구는 `promptOnStart`. 지금 단계 행동은 표식에 닿기 전에 해도 센다. 허수아비 3은 그림(맞으면 흔들림)이고 물리 개체는 아니다. 혼불 6개는 탄생 자리 둘레 2.5칸(`fx/soul_wisp` 있으면 시트 루프, 없으면 빛 점). 전장 소품: 부러진 무기 7·찢긴 깃발 3·쓰러진 병사 흔적 5·잔해 담 2.
- **설계도 묶음** `routeArena.ts` `planNodeArena(node, stageId, floorSeed)` → { layout, region, tileset, setPiece, reserve, structureNode, tutorial } · `setPieceTiles`(타일셋 소품 제외 칸).
- **연결**(메인 세션): Game.ts — 노드 전투장을 `planNodeArena` 로 만들기, 구조물 `node: structureNode`, 타일셋 `skinFor`, `SetPieceView`, `TutorialDirector`(출구 조건 `tutorial.done`), shutdown 정리, 디버그 `route().region/setPiece/tutorial`, `?notutorial`. Preloader.ts — 지역 타일셋 로드(`regionTilesets()` → `regionSkins`). spriteDefs.ts — `STRUCTURE_FX_IDS` 에 `soul_wisp`.
- 테스트 +23: `mapgen/arena.test.ts` 7(결정성·사각형 아님·연결·틈·중앙 시작점·사각 벽 호환·프로필) · `routeArena.test.ts` 14(지역 매핑·스냅샷 region/desc·지역 타일셋·소품 시트 이름·결정성·휴식/상점/이벤트 중앙·전투 엄폐·소품 바닥/겹침·예산·튜토리얼 자리·진입 대기) · `tutorial.test.ts` 8(단계 순서·문구·허수아비·원거리·순서 밖 행동·전투·건너뛰기) · `rules.test.ts` 갱신.
- 임시값(검수 대상): 단계 → 지역 표(외곽 거리 2단계·양조 구역 1단계), 2층 지역 2개, 지역·노드 설명 문구, 가장자리(기본 깊이 3·run 2~5·틈 1~2개 폭 2~4, 황무지 4·틈 2~3 / 성문 2·0~1 / 외곽 3·1~2 / 양조 3·0~1 / 연회장 2·0), 템플릿 좌표·반지름·각도 흔들림 20°, 엄폐 개수·모양, 소품 이름(stones·bench·plaza·street·stall·lantern·scene·wreck·debris·barrels·crates·table·banner·rubble·weapon·flag·fallen — 아트가 이 이름으로 그리면 자동 사용), 튜토리얼 좌표·문구·횟수·약한 적 수치, 그림 수치(route.json `view`), 튜토리얼은 매 런 탄생 노드에서 진행(행동을 먼저 하면 빨리 지나감).

## 49라운드 반영 (4·5절): 무기 휴대 · 무기 자원(기력·탄창·과열) · 대검 무게감·내리찍기·대쉬 공격 · 무기 시험장 (2026-10-02)
결정: `decisions/2026-10-02-round-49-playtest2.md` 4절(휴대)·5절(동작·자원·시험장) + 2절 보상 연결(senseBonus) + 6절 M 키. 계약: `ui-system-interface.md` §11.1·11.3·11.4, `art-assets.md` §7.1·7.2. 작업 파일: `Game.ts`(유일 편집자)·`WeaponLab.ts`(새)·`Player.ts`·`WeaponOverlay.ts`·`LabDummy.ts`(새)·`weaponResource.ts`(새)·`weaponLab.ts`(새)·`combo.ts`·`spriteDefs.ts`·`InputSystem.ts`·`audio.ts`·`Constants.ts`·`EventBus.ts`·`data/types.ts`·`data/index.ts`·`data/weapons.json`·`contract/host.ts`·`debug/index.ts`·`config.ts`·`Preloader.ts`(?lab 라우팅 한 줄).
- **무기 자원** `WeaponResource`(Phaser 없음, 시간 주입) → `UiSnapshot.resource`(계약 §11.1). 데이터 `weapons.json <무기>.resource`.
  - 기력(칼·대검): 연격 타별·대쉬·대쉬 공격·내리찍기 소모, 마지막 소모 뒤 지연이 지나면 회복. 0 → `exhausted`(max×recoverRatio 까지 차야 풀림): 이동 감속(exhaustedMoveMult), 강한 타 불가 = 마지막 타는 1타로 돌아감(`ComboTracker.poll(…, allowFinisher)`)·대쉬 공격은 일반 타·내리찍기 없음. 대쉬는 바닥나도 됨(회피 수단 유지, 임시). 비전투 달리기·걷기는 소모 없음.
  - 화살 탄창(활): 한 발(조준 사격 포함)마다 1, 비면 자동 장전(`reloading` + progress), **R = 수동 장전**(게임 중 R 은 다른 용도 없음 — 재시작 R 은 결과 화면 전용, 같은 키를 InputSystem 이 한 번만 읽는다). 장전 중 발사·조준 불가. 장전 동작 `player_bow_reload`(장전 시간에 맞춤).
  - 과열(단검): 연격 타마다 가열 → 단계 0..3(경계 30/60/90) → 공격 속도 ×1/1.15/1.3/1.45(`ComboTracker.setSpeed`, 타 시작 시 고정, 애니·다음 타 허용·리셋 모두 나눔). 최대 열을 1.5초 유지하면 `overheat` → 1.6초 냉각(공격 불가, 열 선형 감소, progress). 단계별 이펙트 `fx/dagger_combo<n>_heat<k>` 있으면 그것, 없으면 기본 연격 이펙트 ×(1+0.12k)·잔상 리본 폭 ×(1+0.35k).
  - 내부 이벤트 `weapon:resource`(exhausted·recovered·reloadStart·reloadDone·overheat·cooled·heatStage) — 음향 훅 후보(매핑 없음).
- **무기 휴대** (`weapons.json <무기>.carry`): 칼 sheath(1타 = 발도, drawMs 0) · 대검 back(아래 아트 맞춤: 별도 뽑기 없이 1타) · 단검·활 hand. 마지막 공격 2.5초 뒤 넣기(`<무기>_sheathe` 몸·무기 시트, 칼 = 납도). `WeaponOverlay`: 무기 드는 동작(attack·combo·special·aim·draw·sheathe·slam·dashslash·reload)은 같은 열 무기 시트, 그 밖(대기·걷기·대쉬·피격)은 `weapons/<무기>_carry_<idle|walk|dash>` 같은 열(깊이 JSON — 방향별 문자열 또는 방향·프레임별 배열). 뽑아 든 동안(칼·대검, 넣기 전)과 휴대 시트가 없을 때는 attack 무기 시트 0프레임 폴백(Constants `CARRY` 위치·각도·배율). 내부 이벤트 `player:weapon-drawn`·`player:weapon-sheathed`.
- **대검 무게감** (`weapons.json greatsword.weight`): 타마다 반 걸음(8px/110ms) 전진, 휘두른 뒤 감속 유지(타 길이 + 220ms), 3타는 타격 순간부터 0.3초 정지(대쉬·공격도 불가).
- **내리찍기** (`greatsword.slam`, 충격파 계열 = 경로에 파쇄·지진·분쇄 → `mods.shockwave`): 3타가 마우스 방향 도약(8~40px) → 착지 → 원형 판정(반경 44px × 진화·강화 배율, 피해 3타 × 1.3) + 기존 충격파 이펙트(지진 2단·분쇄 탄 지우기 그대로). 시간은 `player_greatsword_slam` 메모(leapFrames·impactFrame) 우선, 없으면 260ms 도약 + 320ms 회복으로 3타 시트를 늘임. `fx/greatsword_slam` 은 impactFrame 이 착지에 오게 앞당겨 재생.
- **대쉬 공격** (`greatsword.dashSlash`): 대쉬 직후 공격 = 달려들며(24px/140ms) 크게 한 번(부채꼴 220°, 대쉬 공격 배율) → 멈춤. 시트 `player_greatsword_dashslash` 우선, 없으면 3타 시트 420ms + 350ms 멈춤. 충격파 없음.
- **무기 시험장** 씬 `WeaponLab`(= `Game` lab 모드, 계약 §11.4): 22×14 아레나(카메라 2배), 중앙 허수아비(무한 체력·누적 피해 표시·넉백 없음), 사수 허수아비(중심 +7,−4칸에서 왼쪽으로 1.4초마다 탄, 공격 8). **L(확정, 49라운드 UI §11 커밋 기준)** = 메뉴 `lab`(무기 4종 '1'~'4' · '9' 개성 갈래 · '0' 닫기) → 무기를 바꾸면 씬 재시작 후 `labBranch`. `labBranch` = '1' 기본 · '2'~'7' 1차·2차(트리 순서, 2차는 부모 1차 포함) · '8' 강화 +1(최대 뒤 0) · '9' 무기 바꾸기 · '0' 닫기 — 즉시 적용. 라벨 앞 갈래 깊이 표기(깊이 d → 공백 2칸 × (d−1) + '└ ', 1차 '└ 파쇄', 2차 '  └ 지진' — UI 가 들여쓰기에 씀). 메뉴 동안 정지. 시험장 나가기는 UI 가 `toTitle()` 을 부르는 경로가 기본(시스템 Esc 처리는 보조). **Esc** = 타이틀(메뉴가 열려 있으면 닫기만, UI 가 메뉴를 닫은 직후 200ms 는 무시, UI 일시정지 화면이 뜨더라도 2 스텝 뒤 `toTitle` 이 정리). 세이브·노드 지도·탄생 없음, HP 50% 아래면 가득(죽지 않음), 개성·골드 없음. `UiSnapshot.lab = true`. host: 시험장 씬도 정리 대상에 추가. `?lab[&weapon=]` 로 바로 진입(검증용).
- **senseBonus**: Game 시작 데이터 `senseBonus`(0~3, 범위 밖은 잘라냄)를 새 런(`mode: 'new'`)에서 감각에 더한다.
- **M 키**: 오디오의 M 음소거 토글 제거(`AUDIO.MUTE_KEY_CODE` 삭제). 음소거는 `uiCommands.setMuted`, `UiSnapshot.muted = audio.isMuted`.
- **디버그**: `weaponState()`(자원·휴대·오버레이 방식·내딛기·정지·sinceDashMs·마지막 이벤트) · `setResource(v)` · `lab()`(허수아비 누적 피해·맞은 수·쏜 수·메뉴) · `openLabMenu('lab'|'labBranch')` · `ui().select(id, key)`·`ui().startWeaponLab()`·`ui().setMuted(b)`.
- 테스트 +23: `weaponResource.test.ts` 13(기력 소모·지연 회복·바닥/회복 경계·low · 탄창 자동/수동 장전·진행도 · 과열 단계·속도·식음·유지 → 과열 → 냉각·유지 초기화 · 데이터 종류·대검 > 칼 소모·휴대 위치) · `weaponLab.test.ts` 3 · `combo.test.ts` +2(속도·마지막 타 막기) · `spriteDefs.test.ts` +4(휴대 동작·오버레이 폴백·깊이 배열·heat/slam 이펙트 id) + 로드 목록 갱신.
- 검증(헤드리스 `vite preview --port 4192`, 960×540, 별도 outDir): 대검 휴대(등, 시트) → 뽑기(draw) → 3연격(기력 100→68, 반 걸음·정지) → 기력 0 exhausted → 갈래 메뉴로 파쇄 → 내리찍기(시트 메모: 도약 200~350ms·착지 350ms·전체 850ms, 원형 판정 R57) → 대쉬 공격(시트 730ms, 220°) → 2.5초 뒤 넣기 → Esc 타이틀 · 활 8발 → 자동 장전(progress) → R 수동 장전 · 단검 가열 0→1→2→3 → 최대 유지 → overheat → 냉각 끝 0 · 칼 1타 발도 → 뽑아 든 폴백 → 납도 · L 메뉴(UI) · Esc 로 메뉴만 닫힘 · M 무반응·setMuted 스냅샷 · 일반 게임 기력 스냅샷·계약 startWeaponLab. 스크린샷 스크래치 `r49combat/`. 콘솔 오류: `sheet_greatsword_combo1_fx` 시트 처리 실패 1건(아트 산출물 쪽, 시스템 무관).
- 임시값(전부 검수 대상): 기력(칼 max 100·회복 38/s·지연 500ms·타 7/6/12·대쉬 12·대쉬 공격 16 / 대검 회복 26/s·지연 700ms·타 16/16/26·대쉬 15·대쉬 공격 26·내리찍기 32, low 30%, 회복 경계 35%, 감속 칼 0.65·대검 0.55), 탄창(8발·장전 1.3초·low 2), 과열(타 9/9/13·식음 45/s·지연 450ms·경계 30/60/90·속도 1/1.15/1.3/1.5·유지 1.5초·냉각 1.6초), 휴대(넣기 2.5초·폴백 위치), 대검(반 걸음 8px/110ms·감속 연장 220ms·시트 없을 때 정지 300ms·도약 8~40px·시트 없을 때 260+320ms·반경 40·×1.3·대쉬 공격 24px/140ms·시트 없을 때 420+350ms·220°), 시험장(아레나 크기·허수아비 위치·탄 간격/속도/공격·HP 50%), 키(R 장전 — L 시험장 메뉴는 확정), 대쉬는 기력 바닥에도 가능.
- **아트 전달(49라운드 무기 시트) 맞춤** (메인 세션 전달 + `parts/art/work/combos/NOTES.md` 49라운드 절, 해당 시트 JSON 열람): 휴대 시트에 더해 칼·대검 **`<w>_carry_drawn_{idle,walk,dash}`**(뽑아 든 채)를 쓴다(없으면 attack 0프레임 폴백), 피격 등은 carry_idle 0열. 대검 1~3타 데이터 시간을 시트와 같게(630/600/820ms, 취소 360/340ms) — 이동 정지는 몸 시트 **`recoverFrames` 구간**(1·2타 = 이동만, 3타 = 공격·대쉬도), 메모가 없을 때만 3타 finisherStopMs. 연격 이펙트는 몸 시트 `fxSpawnAtMs`(재생 배속 반영) 우선. **대검 뽑기는 없음**(drawMs 0: 1타 f0~f1 이 곧 등에서 끌어올림), 가드·패링 시작도 뽑은 상태로. 내리찍기 착지점 = 시트 `impactOffsetPx`(방향별, 없으면 impactDistancePx), 반경 40(그림 반경)·`fx/greatsword_slam` 은 착지 순간 착지점에 바닥 깊이·배율 R/40(정수일 때만)으로, 이때 파쇄 이펙트·기본 흔들림 대신(지진·분쇄 2차 이펙트는 그대로). `leapOffsetsPx`(몸 띄우기 제안)는 **미적용**. 대쉬 공격 판정·이펙트 = 몸 시트 메모(R51·210°, `fxReuse` greatsword_combo2 @120ms, 없으면 데이터 fxCombo·fxSpawnAtMs). 단검 과열 4단 속도 1.5(아트 playbackRateHint 와 같게), 가열 이펙트도 같은 배속. 활 장전 동작은 `refillFrame` 시작이 장전 완료(1.3초)에 오도록 늘임.
- **지역·세트·튜토리얼 연결 적용** (다른 시스템 에이전트의 `r49world/connection.diff` 그대로 — 노드 전투장 `planNodeArena`·지역 스킨 `skinFor`·`SetPieceView`·`TutorialDirector`(출구 조건 tutorial.done, `?notutorial`)·Preloader 지역 타일셋·`soul_wisp`). 디버그 `route().setPiece` 에 center·signs·dummies·decor(시트 후보) 추가.
- **세트 소품 시트 매핑** (아트 이름이 `set_<region>_<name>` 가정과 다름 → `data/route.json` 의 sprite 후보 목록, `{region}` = 지역 id, 튜토리얼 표식 `{step}` = 단계 signName): 휴식 plaza → `set_{region}_plaza`·`set_{region}_fire_ring`(황무지 = set_waste_fire_ring)·`set_outer_plaza` / 상점 stall → `set_{region}_stall`·`set_outer_stall`, lantern → `set_{region}_lantern`·`_lamppost`·`_brazier`(성문 = set_gate_brazier)·`set_outer_lamppost` / 전투 crates·엄폐 barrels → `set_{region}_crates|barrels`·`set_{region}_barrel_stack`(양조 구역) / 보스 table → `set_{region}_table`·`_long_table`·`set_hall_long_table`, banner → `set_{region}_banner`·`battlefield_banner`, **rug 새 소품**(중앙 4×3 바닥) → `set_{region}_rug`·`set_hall_rug` / 전장 flag → `battlefield_flag`·`battlefield_banner` / 표식 → `tutorial_sign_{move,attack,dash,skill(보조 동작 단계 signName),fight}` → `tutorial_sign`. 미사용: `set_outer_stall_side`(측면 노점 자리 없음). 그림 없는 이름(stones·bench·street·scene·wreck·debris·rubble·flag 등)은 도형 폴백.
- **혼불 탄생**: `player_birth` JSON `fx.ambient` + `underOptional` 이면 흙 소용돌이(birth_dust)를 끄고 혼불(세트 그림 soul_wisp 6개)만.
- 통합 검증(헤드리스 4192): 탄생 전장(황무지 타일셋, 소품 25 중 시트 23, 혼불 6 시트) → 표식 이동 → 허수아비 2타 → 대쉬 → 패링 → 표식 5 에서 징집병 2(체력 10) → 처치 → 튜토리얼 끝 → 클리어·출구 열림 · 휴식 노드(양조 구역): 모닥불 중앙(−1,0)·숙성 통/묘/카운터 반지름 6 · 상점 노드(외곽 거리): 노점 거리 중앙, 장부대·궤짝 (∓5,−3), 노점·가로등 시트 · 지도 안 void 칸 1054개 전부 시트 인덱스 7(−1 은 지도 밖). 콘솔 오류 0.

## 50라운드 1단계: 최적화 — 책임별 분리 · 죽은 코드 제거 (2026-10-02)
운영 규칙(루트 CLAUDE.md 6-1 "복잡해지면 최적화 선행"). **기능 변경 없음** — 분리 전 빌드와 분리 후 빌드를 같은 헤드리스 시나리오(탄생·튜토리얼 5단계·연격·노드 선택·시험장 대검 연격/갈래 메뉴/내리찍기 + 구조물 E·상점·활·3층 방+복도·워프 거부)로 돌려 결과가 같음을 확인(시험장 허수아비 맞은 수만 헤드리스 프레임 타이밍에 따라 4/5 — 분리 전 빌드도 같은 흔들림).

### 구조 지도 (파일별 책임)
| 파일 | 책임 |
|---|---|
| `src/scenes/Game.ts` (3195 → 약 650줄) | 씬 생애주기만: create 순서(모듈 생성 → 런 준비 → 노드 진입 → 월드 → 플레이어 → 개체·연출 풀 → 물리 배선 → 방 상태 머신 → 튜토리얼 → 구조물 → 계약 연결 → 디버그 → 이벤트 표) · 매 프레임 순서(탄생 / 정지 / 히트스톱 / 진행) · 정지(frozen·히트스톱 물리 정지) · shutdown 정리. 공유 상태(player·mobs·world·fx…)는 모듈이 읽도록 공개 필드 |
| `scenes/game/shared.ts` | 씬 시작 데이터 `GameInitData` · 판정 원점(발 위 10px) · 연격 마지막 타 판정 · 개성 경로 이펙트 고르기(`pathFx`·`evolutionFxId`) · 주소 옵션(`urlParams`, 5곳 중복 제거) |
| `scenes/game/GameCamera.ts` | 플레이어 추종(데드존·lerp·스냅)·영역 클램프·흔들림 오프셋 |
| `scenes/game/GameCombat.ts` | 피해 계산(`rollDamage`) · 적 피격 공통 경로(`hitMob`: 숫자·섬광·피·히트스톱·흔들림·넉백·방패) · 접촉·투사체·반사·플레이어 화살 겹침 콜백 · 패링 섬광 · 플레이어 피격 연출 · 적이 요청하는 탄·내리찍기·소환 · 플레이스홀더 충격파 |
| `scenes/game/PlayerStrikes.ts` | PLAYER_ATTACKED: 연격 판정 모양(아트 메모 우선)·휘두름 이펙트·잔상 리본·대검 내리찍기 충격파·쌍격/지진 2단·활(연사·산탄·관통·추적·중시)·잔월·출혈·거인 · 매 프레임 추적 화살·잔월·출혈 |
| `scenes/game/MotionFx.ts` | 가드 밀쳐내기·그림자 걸음·대쉬 시작(먼지·발도술·허보·잔상·잔상 피해) · 유지형 연출(질풍·조준 점선·차지·대쉬 잔상·달리기 먼지) |
| `scenes/game/Progression.ts` | 런 시작 모드(새 런·다음 층·이어하기·다음 노드)·세이브 · 처치 → 개성 → 3지선다(변환·강화)·진화 배너 · 스테이지 보상(능력치·패시브) · 엔딩 · 사망·정산·결과 화면 |
| `scenes/game/Economy.ts` | 드랍·줍기·골드·물약·상점 타일 메뉴·구매 |
| `scenes/game/RouteFlow.ts` | 노드 진입(밝아짐·잠금)·클리어 → 출구 → 노드 선택(UI·숫자 키)·전환 · 층 출구 · 디버그 gotoNode |
| `scenes/game/BirthFlow.ts` | 탄생 연출 연결(입력 잠금·카메라 배율·건너뛰기·HUD 알림) |
| `scenes/game/LabMode.ts` | 무기 시험장(연습 런·아레나·허수아비·L/Esc 메뉴·죽지 않음) |
| `scenes/game/UiRelay.ts` | 스냅샷 · 스토리 자막 · 내부 이벤트 → UI 중계 · 워프 요청 거부 |
| `scenes/game/DebugHooks.ts` | `?debug=1` 훅 연결 (`route()` 정보 포함) |
| `src/objects/Player.ts` (1038 → 약 730줄) | 상태 머신: 이동·달리기·대쉬·보조 동작·연격 입력·대검 무게(내딛기·정지)·피격 |
| `objects/player/PlayerGear.ts` | 무기 자원(기력·탄창·과열) 진행·이벤트 · 장전 동작 · 휴대(뽑기·넣기·납도) |
| `objects/player/PlayerPoses.ts` | 무기를 든 자세(특수 자세 구간·가드 반복·조준 진행도·발사 프레임)·이동 애니·판정 구간 길이 |
| `objects/player/heavyMoves.ts` | 대검 내리찍기·대쉬 공격 (조준 벡터 공용) |
| `src/systems/structures/StructureSystem.ts` (2232 → 약 430줄) | Game 이 보는 창구: 전투 훅·배율·이벤트 구독·스냅샷·디버그·노드 사이 층 상태 |
| `structures/core.ts` | 인스턴스·물리 바디·층 상태(빚·취기·판돈·불씨·불붙은 무기·전당·숙성) · 생성·그림 상태·바디 · 결과/사용/부서짐/도전 이벤트 · 메뉴 공통 · 물약 지급·최대 HP 감소 · 룰렛 규칙 |
| `structures/kinds/strikeKinds.ts` | 타격형·통과형: 짐·독주 술통(구르기·웅덩이·불바다)·증류 화로(불붙은 무기·불화살·화상)·숨은 벽(저장고)·판돈 종 |
| `structures/kinds/serviceKinds.ts` | 공통·1층 E형: 궤짝·묘·모닥불·장부대·숙성 통·선술집 카운터(취기) |
| `structures/kinds/gambleKinds.ts` | 2층: 패 탁자·환전대·투견 링·룰렛·전당포 |
| `structures/interact.ts` | E 안내: 가장 가까운 것·막힌 사유·비용·행동 이름·실행 분기·묘 길게 누르기·화면 위치 |
| `structures/status.ts` | HUD 상태 줄 |

중복 제거: 주소 옵션 파싱 5곳 → `urlParams()`, 플레이어 시트 조회 헬퍼 → `EntityVisual.sheet()`, 구조물 단단한 발판 생성 2곳 → `core.addSolid`, 숙성 상태 줄 2곳 → `agingStatus`, EventBus 구독/해제 15쌍 → 표 하나(`subs`), 지연 콜백 '진행 중' 확인 → `PlayerStrikes.live`, 잔월 남는 궤적 → `leaveTrailDot`.
**죽은 코드 제거**: 45라운드 워프 실행 경로(48라운드 §10.2 로 전 층 비활성 — `warpDeny` 가 늘 거부라 도달 불가): `startWarp`·`finishWarp`·워프 연출 상태, `TRAVERSAL.WARP`, `Events.WARP_STARTED/ARRIVED`·`WarpPayload`, `warpTargets`·`warpDenyReason`·`findSafeTile`(+테스트 7), `TileWorld.safePointInRoom`. 계약 `uiCommands.warpTo` 는 그대로(늘 거부 사유만). 짐 부서짐의 쓰이지 않던 `deltas` 변수.

## 50라운드 2단계: 렌더링 기반 — 2배 도트·쿼터뷰 벽·동적 조명 (외곽 거리 시범) (2026-10-02)
결정: `decisions/2026-10-02-round-50-modern-view.md`. 계약: `art-assets.md` §9.

### 설계 판단 1 — 카메라 '1배' 를 렌더 배율로 (월드 좌표는 그대로)
- 결정 Q2 의 뜻 = 새 도트 1px 가 화면 1px, 화면상 크기는 지금과 비슷. 두 길 중 **렌더 배율만 바꾸는 쪽**을 택했다: 월드 1단위 = 화면 2px(`RENDER.WORLD_TO_SCREEN`, 게임 카메라 배율 `CAMERA.ZOOM` 이 이 값), 타일 = 월드 16(`TILE`) 그대로.
  - 새 2배 도트(`pixelScale: 1`)는 스프라이트를 0.5 배로 그린다 → 도트 1px = 화면 1px(= '카메라 1배' 화면). 기존 도트(`pixelScale` 없음 = 2)는 1배(화면 2px) → 섞여 있어도 같은 화면 크기. `artScale(def) = pixelScale / 2`.
  - 월드 좌표를 2배로 옮기는 길(TILE 32·카메라 1)은 데이터 px(이동·판정·넉백·사거리·바디 크기·아트 메모)를 전부 2배로 바꾸고 Arcade 바디 배율까지 손대야 해 회귀 위험이 커서 버렸다. 지금 길은 **판정·속도·데이터 수치가 한 줄도 안 바뀐다**(체감 동일).
  - 새 도트 시트 JSON 의 월드 길이 메모(`hitRadiusPx`·`thrust`·`impactOffsetPx`·`impactDistancePx`·`light.radius/offsetY`·`occludeAbove`)는 로드 때 월드 단위로 바꾼다(`sheetToWorldUnits`). 프레임·피벗·프레임 좌표(fireBox·stakes·flagpost)는 텍스처 좌표라 그대로.
  - 적용: 주인공·적(`EntityVisual` — 동작마다 그 시트의 배율·피벗으로 원점·배율을 맞추고, Arcade 바디는 프레임 단위 × 배율이라 배율로 나눠 넣어 **월드 바디 크기 그대로**), 무기 오버레이, 이펙트 풀, 구조물·세트 그림, 혼불, 탄생 시트. 판정 박스는 데이터 그대로(화면 크기 기준 유지). 데미지 숫자·디버그 글자는 변화 없음.
- 로드: `sprites/<분류>/v2/<파일>`·`tiles/v2/<이름>.json` 이 매니페스트에 있으면 기존 경로보다 먼저(동작 단위 — v2 가 없는 동작은 기존 시트, 섞여도 같은 크기). 지금 들어온 v2: 주인공 idle·walk·dash·hurt·death·칼 연격, 결사병 5동작, `tiles/v2/stage1_outer`.

### 설계 판단 2 — 쿼터뷰 벽 (`world/QuarterView.ts`)
- 타일셋 JSON 에 `wallHeightTiles` 가 있으면 쿼터뷰. 충돌·출입·판정은 **기존 16 격자 타일맵**(보이지 않게)이 그대로 맡고, 그림만 새로: 바닥 = 32px 타일맵을 0.5 배로(벽 칸은 원경), 벽 칸마다 **윗면**(위로 wallHeightTiles 칸 올림) + 남쪽이 벽이 아니면 **앞면**(아랫단 = `walls.front`/`tiles["2"]` 변형, 윗단 = `walls.frontUpper`·`wallFrontUpper`·`walls.front` 배열 둘째, 윗면 = `walls.top`, 없으면 인덱스 5·6).
- 깊이 = 벽 칸 아래변 y (개체와 같은 Y 정렬) → 벽 남쪽 캐릭터는 앞, 북쪽(뒤) 캐릭터는 가려진다. 가려진 주인공 둘레 벽 그림은 반투명(`QUARTER.OCCLUDE_ALPHA 0.55`, 임시). 위쪽 벽 앞면이 보이도록 노드 전투장 카메라 경계를 wallHeightTiles 칸 위로 넓혔다. 출구·상점·저장고처럼 칸이 바뀌면 바닥·벽 그림을 다시 만든다.
- 구조물·소품 `occludeAbove`: 피벗에서 그 높이까지(받침)는 바닥 깊이(`STRUCTURE_FX.OCCLUDE_BASE_DEPTH`), 그 위는 Y 정렬 — 그 위로만 캐릭터를 가린다(같은 프레임 두 장, 자르기). 없으면 기존처럼 통째로 Y 정렬.

### 설계 판단 3 — 동적 조명 + 어둠: 라이트맵 RenderTexture (`systems/lighting/`)
- 매 프레임 화면 × `lightmapScale 0.5`(480×270, 선형 필터) 라이트맵을 지역 주변광 색으로 채우고 → 보이는 광원을 방사형 그라데이션으로 **가산** 스탬프 → 비네팅을 같은 라이트맵에 굽고 → `DEPTH.LIGHTMAP 2` 에 **곱하기**로 덮는다. 그 위에 광원마다 가산 그라데이션(빛 번짐, 월드 좌표).
- 라이트맵 아래(어둠에 잠김): 바닥·벽·개체·구조물·개체 위 이펙트. 위(그대로 읽힘): 드랍·투사체·공격 판정·잔상·피격 이펙트·데미지 숫자·화면 섬광. 바닥 깊이의 적 예고 마커는 붉은 경고광을 달아 어둠에서도 읽힌다.
- **Light2D(노멀맵 없이) 대신 고른 이유**: Light2D 는 모든 개체(타일맵·Graphics·텍스트)에 파이프라인을 따로 걸어야 하고 광원 수가 셰이더 상수(maxLights)에 묶이며 빛 번짐·비네팅을 따로 만들어야 한다. 라이트맵은 개체 코드를 안 건드리고, 광원 1개 = 1/4 해상도 쿼드 1장 + 번짐 1장, 화면 전체 합성은 1장(곱하기)뿐이라 비용이 예측 가능하다. 광원 상한 `maxLights 24`(주인공 빛 고정 + 화면 중심 가까운 순, 화면에 걸치는 것만).
- 광원: 주인공 주변 빛(늘) · JSON `light` 를 가진 소품(타일셋 props)·구조물·세트 그림·이펙트 · JSON 이 없으면 `data/lighting.json fallback`(시트 id → 임시 광원: bonfire·still·fire_pool·soul_wisp·set_outer_lamppost/stall/plaza·set_waste_fire_ring·set_gate_brazier) · 무기 이펙트(`weapon` 필드 시트) 순간광(이펙트 길이 동안 감쇠) · 예고 경고광. 깜빡임 = 광원마다 다른 두 사인 합(`flickerFactor`). 부서진·다 쓴 구조물은 꺼진다.
- **켜는 곳**: `data/lighting.json regions` 에 있는 지역의 노드 전투장만(Q4 시범 = 외곽 거리). `?light=0` 끔, `?light=1` 이면 다른 전투장·시험장에도 default(검증용).
- 성능(헤드리스 소프트웨어 GL, 참고치): 조명 갱신 CPU 0.4~0.7ms/프레임(광원 11개 상점 노드 포함). GPU 비용은 1/4 해상도 채우기 + 광원 쿼드 + 전체 화면 곱하기 1장 — 실기 60fps 확인 필요(헤드리스는 조명 없이도 15~25fps).

### `?slice=outer` (시범 확인)
`?slice=<지역 id>`(+`&weapon=`) = 새 런으로 그 지역의 전투 노드에 바로(탄생 생략, 그 뒤 진행은 정상). 디버그 `__lopad.lighting()`(켜짐·주변광·등록/후보/그린 광원·라이트맵·CPU ms) · `__lopad.quarter()`(벽 그림 수·비친 수·타일 px·벽 높이).

### 테스트 · 검증
- 테스트 +14: `lighting/lighting.test.ts` 6(색·깜빡임 범위·광원 고르기·광원 목록 따라가기/만료/끔·시트 광원 우선순위·데이터 검증) · `world/quarter.test.ts` 5(쿼터뷰 인덱스 표기 3가지·충돌 인덱스·기존 타일셋 호환) · `systems/spriteScale.test.ts` 3(도트 배율·메모 단위 변환·v2 경로).
- tsc·eslint·vitest(41파일 288개)·vite build 통과(작업 중 다른 에이전트의 회피 시험·획 연출 편집이 한때 tsc/빌드를 깨뜨려, 그동안은 그 파일만 HEAD 판으로 되돌린 사본에서 확인 — 지금은 실제 작업 트리 그대로 통과).
- 헤드리스(`vite preview --port 4196`, 960×540): 1단계 회귀 시나리오 결과 분리 전과 같음(v2 주인공 시트로도) · `?slice=outer` 외곽 거리 전투(실제 v2 타일셋: 2칸 건물 앞면·윗면, 엄폐 담 앞면, 결사병 v2, 화로 불빛, 주인공 빛, 공격 순간광) · 아래쪽 벽 뒤 가림 비침 · 외곽 상점(가로등 4·노점) / 휴식(모닥불) 광원 · `?light=0`. 콘솔 오류 0. 스크린샷: 스크래치 `r50sys/`(outer_lit_*·outer_shop_*·outer_rest_*·v2_*·s2r_*).

### 임시값 (전부 검수 대상)
주변광(외곽 #4a4e6e, default #55586e) · 주인공 빛(반경 104·세기 0.72·색 #ffe6c2·깜빡임 0.03) · 광원 상한 24 · 라이트맵 0.5 · 그라데이션 falloff 0.6 · 깜빡임 4~9Hz · 빛 번짐(알파 0.22·반경 ×0.55) · 비네팅(0.5·안쪽 0.5) · 무기 순간광(반경 56·0.55) · 예고 경고광(반경 36·0.45·#ff5a3c) · fallback 광원 표 · 가림 비침 알파 0.55 · occludeAbove 받침 깊이 0.7 · 라이트맵 깊이 2(무엇을 어둠 위로 둘지).

### 남은 일 · 확인 필요
- 적 탄·화살 시트가 `pixelScale 1` 로 오면 투사체 배율(바디 보정 포함)이 아직 없다(지금 v2 범위 밖).
- 다른 지역은 시범 검수 뒤 `lighting.json regions` 에 넣으면 켜진다(타일셋은 `tiles/v2/` 가 오면 자동 쿼터뷰).
- 아래쪽 경계 벽이 바닥 두 줄을 덮는 것(원근상 맞음)·가림 비침 방식은 체감 검수 대상.

### 50라운드 2단계 보정: v2 외곽 거리를 아트 목업에 맞춤 (2026-10-02)
코디네이터 비교(헤드리스 `?slice=outer` vs `parts/art/work/v2_outer/preview_mock_lit.png`)로 찾은 원인과 수정. 읽은 아트 파일(허가): `assets/tiles/v2/stage1_outer.json`, `parts/art/work/v2_outer/NOTES.md`·`scene.py`(쌓기 규칙 확인).
- **바닥**: 전투 노드 바닥이 `roomFloors.trial`(27 배수구·28 금·29·30)로만 깔려 칸마다 배수구가 찍혔다. 목업 바닥은 `tiles["1"]`(0~3 판석)뿐 → 쿼터뷰(v2) 타일셋은 판석이 바탕, 방 종류 바닥은 `QUARTER.ROOM_FLOOR_PERCENT`(6%, 임시) 칸만. 기존 타일셋은 그대로.
- **벽 쌓기**: 아트 JSON 은 `walls.front = { lower: [...], upper: [...] }`(중복 = 가중치) 객체였는데 숫자·배열만 읽어 윗단이 40 하나로 고정됐고, 모든 벽 칸에 윗면을 2칸 올려 그려 서·동·남 경계와 두꺼운 벽이 조각났다. → `walls.stacking` 규칙대로: 남쪽이 바닥인 벽 = 아랫단(제자리) → 윗단 → 처마 `topAboveFront`(47), 그 밖의 벽 = 제자리 윗면 + 경계 가장자리(`left 48`·`right 49`·`bottom 50`·`corner_bl/br 51/52`), 나머지 `top 6`. 엄폐 담(바깥 빈 칸에 닿지 않는 벽 덩어리)은 `stoneSet`(43·46 / 44 / 45). 바닥 그늘 `floorShadows`(53~57)를 벽 발치에 겹침. 앞면 창·문 `tileLights`(21·22) 광원. 소품 light 의 `flicker {amp,hz}`·`offset`(칸 안 좌표) 지원.
- 비교 이미지: 스크래치 `r50sys/compare_outer_fix.png`. 남은 차이: 북쪽 경계가 49라운드 들쭉날쭉 가장자리(외곽 maxInset 3)라 목업처럼 일직선이 아니고, 전체 밝기가 목업보다 어둡다(주변광·주인공 빛 임시값) — 인터뷰 대상.
