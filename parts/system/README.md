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
