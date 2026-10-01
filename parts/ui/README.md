# 게임 UI 파트 — 작업 기록

## 개시 (2026-10-01, 16라운드)
결정: `parts/producer/decisions/2026-10-01-round-16-ui-kickoff.md`. 교차 참조 승인: `decisions/cross-references.md` #1·#2. 계약: `contracts/ui-system-interface.md`.

### 소유 코드 (`src/ui/`)
| 파일 | 내용 |
|---|---|
| `index.ts` | 계약 §5 공개 지점: `UI_SCENES` 키, `uiScenes` 배열 (시스템은 이것만 import) |
| `keys.ts`, `theme.ts` | 씬 키, 플레이스홀더 테마(색·폰트). 아트 파트 산출물로 교체 대상 |
| `widgets.ts` | 패널, 게이지(Bar), 라벨, 선택 목록(SelectList: 숫자/방향키+Enter/마우스) |
| `TitleScene.ts` | 타이틀: 이어하기 / 새 런, 조작법 |
| `HudScene.ts` | 병렬 HUD: 체력바·골드·물약·층/시련·무기+개성 게이지·우클릭 보조 동작명·보스 체력바·미니맵, Esc 일시정지, 층 시작·개성 변화 배너 |
| `Minimap.ts` | 방 그래프 미니맵 (방문한 방만, 종류별 색, 현재 방 강조, 클리어한 시련 색 변경) |
| `MenuScene.ts` | 보상·패시브·상점·메타 공용 오버레이 (계약 MENU_OPEN/CLOSE) |
| `PauseScene.ts` | 일시정지: 능력치·패시브·감각·조작법, 계속/타이틀로(확인) |
| `ResultScene.ts` | 런 결과: 사망/클리어, 기록, 영혼, 다시/타이틀 |

### 격리
- `src/ui/**` 는 `src/contract/ui.ts` 와 `phaser` 만 import (ESLint `no-restricted-imports` 로 강제).
- 시스템 코드는 `src/ui/index.ts` 만 import (ESLint 로 강제).

### 검증 (2026-10-01, 헤드리스)
타이틀 → 새 런 → 메타 메뉴(UI 렌더) → Enter → 3획·리듬 → 게임(HUD) → 시련 → 보스 → 감각 보상 메뉴 → 패시브 메뉴 → 출구 열림 → Esc 일시정지(이동 정지) → 재개 → 사망 → 결과 화면. 콘솔 오류 0.

### 다음 인터뷰 후보
- 개성 선택 화면(3획·리듬)의 정식 비주얼 (현재 시스템 플레이스홀더)
- 상점·보상 메뉴의 아이콘·설명 레이아웃 (아트 파트 개시 후)
- 설정 화면(키 변경, 음량 — 음향 파트 개시 후)
- 데미지 숫자·피격 연출 등 전투 피드백 UI
