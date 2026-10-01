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
