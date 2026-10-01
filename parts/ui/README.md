# 게임 UI 파트 — 작업 기록

## 개시 (2026-10-01, 16라운드)
결정: `parts/producer/decisions/2026-10-01-round-16-ui-kickoff.md`. 교차 참조 승인: `decisions/cross-references.md` #1·#2. 계약: `contracts/ui-system-interface.md`.

### 소유 코드 (`src/ui/`)
| 파일 | 내용 |
|---|---|
| `index.ts` | 계약 §5 공개 지점: `UI_SCENES` 키, `uiScenes` 배열 (시스템은 이것만 import) |
| `keys.ts`, `theme.ts` | 씬 키, 플레이스홀더 테마(색·폰트). 아트 파트 산출물로 교체 대상 |
| `widgets.ts` | 패널(`panel`/`drawPanel` 재그리기), 게이지(Bar), 라벨, 선택 목록(SelectList: 숫자/방향키+Enter/마우스, 항목 아래 `detail` 작은 글씨, 비활성 흐림, `measure`/`maxWidth`/`setPosition`) |
| `text.ts` | 세계관 문구 조회 `uiText(section, key, fallback)`, `{key}` 치환 `fill`, 조작법 한 줄 `controlsLine(secondaryName)` (계약 §4 `getUiText`) |
| `TitleScene.ts` | 타이틀: 이어하기 / 새 런, 조작법 |
| `HudScene.ts` | 병렬 HUD: 체력바·골드·물약·층/시련·무기 아이콘+무기+개성 게이지·우클릭 보조 동작명·보스 체력바·미니맵·`M 음소거` 힌트, Esc 일시정지, 층 시작·개성 변화 배너 |
| `Minimap.ts` | 방 그래프 미니맵 (방문한 방만, 종류별 색, 현재 방 강조, 클리어한 시련 색 변경) |
| `MenuScene.ts` | 보상·패시브·상점·메타·개성 3지선다(evolve)·엔딩 2지선다(ending) 공용 오버레이 (계약 MENU_OPEN/CLOSE). 패널 폭은 항목·제목·푸터 폭에 맞춤(evolve·ending 최소 520, ending 제목 강조색) |
| `PauseScene.ts` | 일시정지: 능력치·패시브·감각·조작법, 계속/타이틀로(확인) |
| `ResultScene.ts` | 런 결과: 사망/클리어(+엔딩 부제 `result.clearedDestroy`/`clearedUnderstand`), 스토리 문장(사망·클리어), 이름·층, 기록, 영혼, 다시/타이틀 |

### 격리
- `src/ui/**` 는 `src/contract/ui.ts` 와 `phaser` 만 import (ESLint `no-restricted-imports` 로 강제).
- 시스템 코드는 `src/ui/index.ts` 만 import (ESLint 로 강제).

### 검증 (2026-10-01, 헤드리스)
타이틀 → 새 런 → 메타 메뉴(UI 렌더) → Enter → 3획·리듬 → 게임(HUD) → 시련 → 보스 → 감각 보상 메뉴 → 패시브 메뉴 → 출구 열림 → Esc 일시정지(이동 정지) → 재개 → 사망 → 결과 화면. 콘솔 오류 0.

### 스토리 반영 (2026-10-01, 26라운드 · 교차 참조 #4)
- HUD: `STORY` 이벤트 자막(하단 중앙, 보스 체력바 위, 공지 1.8초/그 외 3.6초), 층 제목(`floorTitle`), 재화·물약 이름(`names`)
- 일시정지: 이름·층 제목 표시. 결과: 첫 줄 스토리 문장(흐린 색), 이름·층 제목
- 검증(헤드리스): 1층 제목·전표·잔의 독주 표시, 휴식 방 자막, 보스 자막, 클리어 결과 화면. 콘솔 오류 0.

### 29라운드 (2026-10-01, 자율 진행 · 세계관 문구 · evolve 메뉴)
결정: `decisions/2026-10-01-round-29-autonomous-demo.md` 자율 결정 B(채택/보류 범위). 계약 §7 (`getUiText`, 메뉴 id `evolve`).
- 세계관 문구 적용 (`uiCommands.getUiText()`, 키 없으면 기본 문구): 타이틀 부제·메뉴 4종(`title.*`), HUD `hud.bossUnlocked`('본영 문 열림')·`hud.exitOpen`('오르는 길 열림')·`hud.evolvedBanner`(이름만), 결과 `result.retry`, 타이틀·일시정지 조작법 줄은 `controls` 템플릿의 `{secondary}` 를 스냅샷 `weapon.secondaryName` 으로 치환(타이틀은 무기 미정이라 '보조 동작').
- **보류(기본 문구 유지)**: '런 클리어', '타이틀로'(결과·일시정지), 일시정지 제목.
- evolve 3지선다: 선택지 `detail` 을 항목 아래 작은 글씨(9px, 흐림)로, 비활성 항목은 알파 0.45 + '(불가)', 푸터 표시. reward/passive/shop/meta 도 `detail` 이 오면 같은 방식.
- 시스템이 보내는 evolve 라벨 `이름 — 설명` 과 `detail`(= 설명)이 겹치므로, 라벨 끝의 ` — 설명` 을 떼고 설명은 아래 줄로만 보인다 (UI 표시 규칙, 되돌리기 쉬움).
- 타이틀 메뉴 패널 폭을 항목 폭에 맞춤 (세계관 문구가 길어 220px 고정 폭이 넘침).
- 검증(헤드리스, 콘솔 오류 0): 타이틀 부제·메뉴·조작법 → 사무라이 칼 evolve 1차(거합/발도술/더 깊게) → 2차 + 강화 3회 후 3번 비활성 → 잔월 선택 배너 → 시련 4/4 '본영 문 열림' → 일시정지 조작법 '우클릭 패링' → 보스 처치·보상·패시브 → '오르는 길 열림' → 사망 결과('다시 태어난다 (영혼 → 개성 선택)') → 대검 일시정지 '우클릭 가드'. 스크립트 `scratchpad/ui29.cjs`.

### 30라운드 (2026-10-01, 자율 진행 · 엔딩 화면 · 무기 아이콘 · 음소거 힌트)
계약: `src/contract/ui.ts` 의 `UiMenuId` `'ending'`, `UiResult.ending` (23라운드 엔딩, 시스템 추가분·승인 대기).
- **결과 화면**: `ending === 'destroy'` 면 `result.clearedDestroy`('다음 전장으로'), `'understand'` 면 `result.clearedUnderstand`('처음으로 내일을 적었다') 를 '런 클리어' 아래 강조색 부제로. 첫 줄 `line`(엔딩 문장) 은 그대로. 부제가 있으면 본문 줄을 8px 내림. '런 클리어' 문구 자체는 보류 유지(29라운드 자율 결정 B).
- **ending 메뉴**: 패널 최소 폭 520, 제목 강조색(`#fff0a0`), 두 항목(없앤다/이해한다)의 `detail` 을 evolve 와 같이 아래 줄 작은 글씨로.
- **무기 아이콘**: `assets/ui/weapons/<id>_icon.png`(아트 산출물 16×16 사본, README 참조) 를 HUD 무기 패널 이름 왼쪽에 표시. `preload()` 에서 `assets-game/ui/weapons/<id>_icon.png` 로 `load.image`(assets-game 플러그인). 이름→id 매핑은 `HudScene.ts` `WEAPON_ICON_IDS`(사무라이 칼=katana, 대검=greatsword, 단검=dagger, 활=bow). 텍스처가 없으면 아이콘 없이 이름만(오프셋 0).
- **무기 패널 폭**: 아이콘(+20px) 때문에 `우클릭: 패링` 이 190px 패널 밖으로 넘치던 것(원래부터 넘침)을, 텍스트 폭에 맞춰 패널을 다시 그리도록(`drawPanel`, 최소 190) 고침. 패널 높이 30 → 34.
- **음소거 힌트**: 미니맵 아래 우상단에 `M 음소거`(작은 글씨, 흐린 색). 토글 자체는 시스템(M 키) 소관, UI 는 힌트만. 스냅샷에 음소거 상태가 없어 on/off 표시는 못 함(계약 요청).
- 검증(헤드리스, 콘솔·HTTP 오류 0): 무기 4종 HUD 아이콘 → 8층 황제 처치 → ending 메뉴(제목·detail 2줄) → `1`/`2` → 결과 2종(부제 '다음 전장으로' / '처음으로 내일을 적었다'). 스크립트 `scratchpad/ui30.cjs`, 스크린샷 `scratchpad/ui30/`.

### 계약 추가 요청 (프로듀서 인터뷰 대기)
- `UiSnapshot.weapon.id`(`'katana' | 'greatsword' | 'dagger' | 'bow'`): 현재 이름 문자열로 아이콘을 매핑하므로 이름이 바뀌면 아이콘이 사라진다.
- `UiSnapshot.mute: boolean`(또는 `MUTE_CHANGED` 이벤트): 힌트를 '음소거 중' 상태 표시로 바꾸기 위해 필요.

### 다음 인터뷰 후보
- 보류 문구 3건('한 생을 다 썼다' / '일기장을 덮는다' / 일시정지 제목 '일기장') 채택 여부
- 가드·조준 진행도 표시 (스냅샷에 보조 동작 진행 값이 없음 — 계약 추가 필요)
- 시스템 evolve 라벨을 `이름` 만으로, 설명은 `detail` 로 분리할지 (현재 UI 가 접미사를 떼서 표시)
- 개성 선택 화면(3획·리듬)의 정식 비주얼 (현재 시스템 플레이스홀더)
- 상점·보상 메뉴의 아이콘·설명 레이아웃 (아트 파트 개시 후)
- 설정 화면(키 변경, 음량 — 음향 파트 개시 후)
- 데미지 숫자·피격 연출 등 전투 피드백 UI
