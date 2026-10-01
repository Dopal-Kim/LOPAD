---
name: phaser
description: >
  LOPAD용 Phaser 3 + TypeScript 게임 개발 규약. 2D 탑다운 로그라이크의 씬 구조, EventBus,
  GameState, Constants, 데이터 주도 설계, 물리·입력·성능 패턴을 다룬다. 게임 시스템 파트와
  UI 파트만 사용한다 (루트 CLAUDE.md의 스킬 접근 규칙 참조).
license: MIT
metadata:
  origin: OpusGameLabs/game-creator skills/phaser v1.3.0 (MIT) 에서 발췌·개작
  adapted-for: LOPAD (PC 웹, 키보드+마우스, 픽셀아트)
  tags: [game, 2d, phaser, typescript, scenes, arcade-physics, topdown, roguelike]
---

# Phaser 3 Game Development (LOPAD 개작판)

원본은 OpusGameLabs/game-creator 플러그인의 `phaser` 스킬(MIT)이다. LOPAD에 맞춰 다음을 제거했다:
수익화(Play.fun) 안전 영역, 모바일 60/40 입력 규칙, 스펙터클 이벤트 강제, 뮤트 버튼 규칙,
플러그인 자체 템플릿 의존. 나머지 아키텍처 규약은 그대로 따른다.

## Core Principles

1. **Core loop first** — boot → preload → create → update 의 최소 루프를 먼저 만든다.
   승패 조건을 비주얼·오디오·연출보다 먼저 넣는다. 초기 범위는 작게: 1 씬, 1 메커닉, 1 실패 조건.
2. **TypeScript-first** — 항상 TypeScript. `strict: true`.
3. **Scene-based architecture** — 화면 하나가 씬 하나. 씬은 좁게 유지.
4. **Vite bundling** — 공식 `phaserjs/template-vite-ts` 템플릿에서 시작.
5. **Composition over inheritance** — 깊은 클래스 계층 대신 행동 조합.
6. **Data-driven design** — 적·아이템·무기·스테이지 수치는 코드가 아니라 데이터 파일(JSON)에.
7. **Event-driven communication** — 씬·시스템 간 통신은 전부 EventBus.
8. **Restart-safe** — `GameState.reset()` 이후 깨끗한 상태. 로그라이크의 "런 재시작"이 이 규칙에 직결된다.
   남은 타이머, 리스너, 참조가 없어야 한다.

## Mandatory Conventions

모든 코드는 [conventions.md](conventions.md)를 따른다:

- **`core/` 디렉터리** — EventBus, GameState, Constants
- **EventBus 싱글턴** — `domain:action` 이벤트 이름, 씬 간 직접 참조 금지
- **GameState 싱글턴** — `reset()`으로 런 초기화
- **Constants 파일** — 모든 매직 넘버·색·속도·설정값. 하드코딩 0
- **Scene cleanup** — `shutdown()`에서 EventBus 리스너 제거

## Project Setup

```bash
npx degit phaserjs/template-vite-ts <dir>
cd <dir> && npm install
```

### 기준 디렉터리 구조

```
src/
├── core/
│   ├── EventBus.ts        # 싱글턴 이벤트 버스 + 이벤트 상수
│   ├── GameState.ts       # 중앙 상태 + reset()
│   └── Constants.ts       # 모든 설정값
├── scenes/
│   ├── Boot.ts            # 최소 설정 후 Preloader로
│   ├── Preloader.ts       # 모든 에셋 로드, 진행바
│   ├── Game.ts            # 메인 플레이
│   └── GameOver.ts        # 결과 화면 + 재시작
├── objects/               # 엔티티 (Player, Enemy, Projectile ...)
├── systems/               # 매니저·서브시스템 (전투, 맵 생성, 무기 개성 ...)
├── ui/                    # UI 컴포넌트 (UI 파트 소유 — 루트 CLAUDE.md 참조)
├── audio/                 # 오디오 매니저
├── config.ts              # Phaser.Types.Core.GameConfig
└── main.ts                # 진입점
```

> LOPAD의 실제 폴더 배치(해상도, data/ 위치 등)는 게임 시스템 파트 개시 인터뷰에서 확정한다.
> 확정 전까지 이 구조는 기본값일 뿐이다.

자세한 설정은 [project-setup.md](project-setup.md).

## Scene Architecture

- **Lifecycle**: `init()` → `preload()` → `create()` → `update(time, delta)`
- 씬 전환 데이터는 `init()`으로 받는다
- 에셋은 `Preloader` 씬에서만 로드
- `update()`는 얇게 — 서브시스템과 게임 오브젝트에 위임
- 타이틀·일시정지 등 화면 목록은 UI 파트 결정에 따른다. 시스템 파트는 임의로 화면을 추가하지 않는다
- UI 오버레이(HUD, 일시정지)는 병렬 씬으로 분리하는 것을 기본으로 하되, 확정은 UI 파트 인터뷰에서
- 씬 간 통신은 EventBus만

[scenes-and-lifecycle.md](scenes-and-lifecycle.md) 참조.

## Game Objects

- 커스텀 오브젝트는 `Phaser.GameObjects.Sprite` 등 기반 클래스 확장
- 풀링은 `Phaser.GameObjects.Group` (투사체, 적, 드랍)
- 복합 오브젝트는 `Container`, 단 깊은 중첩 금지
- `GameObjectFactory`에 등록해 씬 레벨 접근

[game-objects.md](game-objects.md) 참조.

## Physics

- **Arcade Physics** — 탑다운·단순 충돌에 사용. LOPAD 기본값
- **Matter.js** — 현실적 충돌·제약이 필요할 때만
- 두 엔진을 섞지 않는다
- 캐릭터 이동은 **상태 패턴** (idle, move, dash, attack, parry, hurt ...)

[physics-and-movement.md](physics-and-movement.md) 참조.

## Input (PC 웹 기준)

- 키보드 + 마우스가 1차 입력. 기획서 9장 조작키 표가 기준이며, 확정은 UI 파트 인터뷰에서
- 입력은 `inputState` 객체로 추상화해 게임 로직이 입력 소스를 모르게 한다
- 포인터 이벤트(pointerdown/move/up)는 마우스·터치 공통이므로 항상 포인터 이벤트로 처리
- 게임패드는 범위 밖 (요청 시 인터뷰)

## Performance (Critical Rules)

- **텍스처 아틀라스** — 개별 이미지 대량 로드 금지
- **오브젝트 풀링** — `maxSize` 있는 Group, `setActive(false)`/`setVisible(false)`로 재활용
- **update 최소화** — 활성 객체만 순회
- **카메라 컬링** — 큰 월드에서 활성화
- **배치 렌더링** — 프레임당 고유 텍스처 수를 줄인다
- **`pixelArt: true`** — 픽셀아트 게임이므로 게임 설정에 필수 (nearest-neighbor)
- `roundPixels: true` 도 함께 검토

[assets-and-performance.md](assets-and-performance.md) 참조.

## Advanced Patterns

- **State machines** — 엔티티·보스 페이즈 관리
- **Singleton managers** — 오디오, 세이브, 메타 진행(무기 도감)
- **Event bus** — 시스템 디커플링
- **Data-driven content** — JSON 로더 + 타입 정의
- **Tiled integration** — 타일맵 에디터 연동 (방+복도 생성 방식 확정 후 검토)

[patterns.md](patterns.md) 참조.

## Anti-Patterns (Avoid These)

- **비대한 `update()`** — 거대한 조건문 덩어리 금지. 오브젝트·시스템에 위임
- **Scene 주입 속성 덮어쓰기** — `world`, `input`, `cameras`, `add`, `make`, `scene`, `sys`, `game`,
  `cache`, `registry`, `sound`, `textures`, `events`, `physics`, `matter`, `time`, `tweens`, `lights`,
  `data`, `load`, `anims`, `renderer`, `plugins` 를 속성 이름으로 쓰지 않는다
- **풀링 없이 `update()`에서 객체 생성** — GC 스파이크. 프레임당 할당 최소화
- **개별 스프라이트 로드** — 아틀라스로
- **씬 간 직접 참조** — EventBus로
- **`delta` 무시** — 모든 이동은 시간 기반
- **깊은 Container 중첩** — 배치 렌더링이 깨진다
- **정리 누락** — `shutdown()`에서 리스너·타이머 제거. 런 재시작 안전성의 핵심
- **하드코딩 값** — 모든 수치는 `Constants.ts` 또는 데이터 파일
- **배선 안 된 콜라이더** — `physics.add.existing(obj, true)`만으로는 충돌이 없다. 반드시 `collider`/`overlap` 호출
- **보이지 않는 버튼 요소** — 버튼은 Container → Graphics → Text 순서로 구성하고 Container를 인터랙티브로

## Examples

- [Simple Game](examples/simple-game.md) — 최소 완성 게임
- [Complex Game](examples/complex-game.md) — 다중 씬, 상태 머신, 풀링, EventBus, 모든 규약 적용

## Pre-Ship Validation Checklist

- [ ] **Core loop** — 시작 → 플레이 → 승패 → 결과 확인
- [ ] **Restart** — `GameState.reset()` 후 잔존 리스너·타이머 없음
- [ ] **Input** — 키보드·마우스 동작 (기획서 9장 기준)
- [ ] **Responsive canvas** — `Scale.FIT` + `CENTER_BOTH`, 노트북 화면 기준 선명함 (해상도는 시스템 파트 인터뷰로 확정)
- [ ] **All values in Constants/data** — 매직 넘버 0
- [ ] **EventBus only** — 모듈 간 직접 import 통신 없음
- [ ] **Scene cleanup** — `shutdown()`에서 리스너 제거
- [ ] **Physics wired** — 모든 정적 바디에 `collider()`/`overlap()`
- [ ] **Object pooling** — 빈번 생성·파괴 객체는 Group
- [ ] **Delta-based movement**
- [ ] **Build passes** — `npm run build` 오류 없음
- [ ] **No console errors**

## Reference Files

| File | Topic |
|------|-------|
| [conventions.md](conventions.md) | 필수 아키텍처 규약 |
| [project-setup.md](project-setup.md) | 스캐폴딩, Vite, TypeScript 설정, 반응형 캔버스 |
| [scenes-and-lifecycle.md](scenes-and-lifecycle.md) | 씬 시스템 |
| [game-objects.md](game-objects.md) | 커스텀 오브젝트, 그룹, 컨테이너, 버튼 패턴 |
| [physics-and-movement.md](physics-and-movement.md) | 물리 엔진, 이동 패턴 |
| [assets-and-performance.md](assets-and-performance.md) | 에셋, 최적화 |
| [patterns.md](patterns.md) | ECS, 상태 머신, 싱글턴 |
| [no-asset-design.md](no-asset-design.md) | 절차적 비주얼 (프로토타입 단계 플레이스홀더용) |
