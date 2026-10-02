# 게임 UI 파트 — 작업 기록

## 45라운드 (2026-10-02) · Tab 워프 지도
결정: `decisions/2026-10-02-round-45-traversal-structures.md` Q3(비전투 중 어디서든 지도 열고 클리어한 방 선택)·Q9(Tab)·Q10(선택 중 정지). 계약: `contracts/ui-system-interface.md` **§8** (승인 #12) — `UiSnapshot.inCombat/sprinting/warp`, `UiRoom.warpable`, `uiCommands.warpTo`, `WARP_DONE`/`WARP_DENIED`. 그 외 시스템 코드 열람 없음.

### 동작
- **Tab** (HudScene `keydown-TAB`, `addCapture('TAB')` 로 브라우저 포커스 이동 차단, 길게 눌러 반복 입력은 무시)
  - 지도가 열려 있으면 닫고 `resume()`.
  - 메뉴·일시정지·결과 씬이 떠 있거나, 스냅샷 `menu`·`paused`·`warp.warping`·`warp.blocked==='busy'` 면 **조용히 무시**.
  - `inCombat` 또는 `warp.blocked==='combat'` 이면 열지 않고 자막 자리에 안내 1.8초(공지와 같은 `showCaption(kind:'notice')`).
  - 그 외(`warp.ready`)면 지도를 만든 뒤 `uiCommands.pause()`. HUD 의 `PAUSED` 처리기는 지도가 있을 때 일시정지 일기장을 띄우지 않는다.
- **Esc**: 지도가 열려 있으면 닫고 재개(일시정지 일기장으로 가지 않음). 아니면 기존대로 일시정지.
- **선택**: 마우스(방 위에 올리면 고름, **눌렀다 뗀** 뒤) 또는 Enter/Space(**지도가 열린 뒤 누른 키를 뗀** 뒤) → 한 프레임 늦게 `warpTo(roomId)`.
  `true` 면 지도를 닫는다(시스템이 재개 후 워프). `false` 면 `WARP_DENIED` 사유를 지도 안 오른쪽에 강조 글로 보인다(지도가 닫혀 있으면 자막 안내).
- **입력 새는 것 방지**: 선택을 뗄 때(pointerup/keyup) 받고 다음 프레임에 넘긴다 — 같은 프레임에 게임 씬이 재개되면 그 입력이 공격·대쉬로 들어갈 수 있어서. 게임 씬은 정지 중이라 누르는 입력을 받지 않는다. 어두운 바탕 사각형도 인터랙티브로 둬 페이지 밖 클릭을 막는다.
- `RESUMED`·`MENU_OPEN`·`RUN_ENDED`·`STAGE_STARTED` 가 오면 지도를 닫는다(재개 호출 없이).
- `WARP_DONE` → 자막 자리 '건너왔다 — {방 이름}' 1.8초 (기존 방 진입 자막이 없어 중복 아님).
- HUD 미니맵 아래 'M 음소거' 다음 줄에 **'Tab 워프'**(ink_faint, 오른쪽 정렬) — 비전투일 때만. `sprinting` 표시는 하지 않음.

### 화면 (`WarpMap.ts`, HUD 씬 위 depth 100~103)
- 화면 전체 G00 α0.55 → 일기장 한 페이지(`book`, seed 'warp'): 제목 '지나온 길'(Galmuri14, page_title) + `rule`.
- 왼쪽 지도: 격자 전체(7×7 기준 칸 40px, 최대 40·최소 16, 영역 최대 520×340), 틀 S2 1px. **방문한 방만** 그린다(미니맵과 같음). 연결선 S1 2px(양 끝 중 하나라도 방문).
  - 방 칸: 안쪽 여백 3px, 같은 방 이웃 칸은 이어 칠함. 종이가 S3 이라 방은 잉크처럼 어둡게.
  - 현재 방: S1 + 층 강조 22 테두리 2px + 글리프 22 틴트.
  - 워프 가능(`warpable`): S1 + S5 테두리 1px. 고른 방: 층 강조 20 테두리 2px + 깜빡이는 `cursor` 촉(방 왼쪽).
  - 그 외 방문한 방(마치지 않은 시련 등): S2, 글리프 α0.45.
  - 글리프 `mini_*` 8×8 을 2배(16×16)로 방 가운데.
- 오른쪽 칸(196px): 범례(글리프 4종 + 이름, 칸 표본 3종) → `rule` → 고른 방 이름(page_selected ×2) + '건너갈 곳을 고른다'(page_faint) + 거부 사유/빈 지도 안내.
- 아래: 조작 안내 한 줄(page_faint).
- 방 버튼은 Container → Graphics → 글리프(스킬 버튼 규약), 입력 판정은 방 칸 모양대로(L자 방도 칸 단위).
- 키보드 이동(`warpNav.ts`, 순수 함수 + 테스트 5개): 방향으로 정면 거리 + 옆 거리×2 가 가장 작은 워프 가능 방. 처음 고른 방 = 현재 방에서 가장 가까운 워프 가능 방.

### 같이 고친 것
- `GlowText.makeInteractive` 입력 사각형이 글자 상자의 **반 칸 왼쪽 위로 밀려** 있던 문제(Phaser Container 판정은 지역 좌표 + displayOrigin(폭·높이 절반)). 사각형을 (w/2, h/2) 에서 시작하도록 고쳤다 → 선택 목록 항목의 오른쪽 절반도 클릭·호버가 된다.

### 소유 코드 추가·변경
| 파일 | 내용 |
|---|---|
| `WarpMap.ts` (신규) | 워프 지도 오버레이 클래스, 방 이름·거부 사유 문구 매핑(`roomName`, `DENY_KEY`) |
| `warpNav.ts`, `warpNav.test.ts` (신규) | 키보드 방향 이동 계산 |
| `HudScene.ts` | Tab/Esc 처리, 지도 열기·닫기, `WARP_DONE`/`WARP_DENIED`/`RESUMED` 구독, 'Tab 워프' 힌트, `toast()` |
| `text.ts` | `WARP_TEXT`(임시 문구), `warpText()` — 텍스트 팩 `hud.<키>` 가 있으면 우선 |
| `theme.ts` | `WARP` 수치(임시값) |
| `glow.ts` | 입력 사각형 수정 |

### 검증 (헤드리스 Playwright 960×540, `vite preview --port 4176`, 스크립트 `scratchpad/r45ui.cjs`, 스크린샷 `scratchpad/r45ui/`)
Tab(대상 없음) 열림·빈 안내·게임 정지(PauseScene 없음) → Tab 닫힘·재개, Tab `defaultPrevented` true·포커스 BODY 유지 → 휴식·시련 방문 → 시련 전투 중 Tab 거부 자막 → 시련 클리어 → Tab 지도 → 방향키 이동 → Enter 워프(trial1→start, `WARP_DONE` 자막) → Tab → 마우스 클릭 워프(start→trial1) → Esc 로 닫힘(일시정지 없음) → 일시정지 중 Tab 무시 → evolve 메뉴 중 Tab 무시. 워프 선택 전후 `lastAttack` 변화 없음(대조: 평소 클릭은 변함). 일시정지 항목 오른쪽 끝 클릭 동작(입력 사각형 수정 확인). 콘솔 오류·경고 0, HTTP 4xx 0. tsc·eslint·vitest(113)·build 통과.

### 관찰 (요청 후보)
- 게임이 정지된 동안 `getUiSnapshot().paused` 가 false 로 남는다(일시정지 일기장이 떠 있어도). 스냅샷이 게임 씬 update 에서만 갱신되는 것으로 보인다. UI 는 씬 활성 여부로 보완했다.
- 텍스트 팩 조작법 한 줄(`controls`)에 Tab 워프·Shift 달리기가 없다(스토리 텍스트 팩 갱신 대상).

---

## 현재 상태 (2026-10-02, 41라운드 · UI 키트 전폭 적용)
결정: `decisions/2026-10-02-round-32-redesign-direction.md`(960×540, UI 전폭), `round-33-ui-kit-review.md`(HUD 하단 중앙), `round-34-font.md`·`round-39-font-final-hitfeel.md`(Galmuri 단일, 발광 할로), `round-41-ui-kit-approved.md`(적용 범위), `round-31-return-review.md`(채택 문구).
계약: `contracts/ui-system-interface.md`(스냅샷·이벤트, 코드 `src/contract/ui.ts`), **`contracts/ui-art-kit.md` v0.4**(키트·9-slice·발광 글자 규칙 표). 열람: #7(팔레트·텍스트 팩), #10(`assets/sprites/ui/**`).

### 소유 에셋 (`assets/ui/`)
| 경로 | 내용 |
|---|---|
| `kit/*.png`, `kit/*.json` | 아트 UI 키트 v0.4 **그대로 복사한 사본**(`assets/sprites/ui/*`). 수정 금지, 갱신 시 재복사. `kit/README.md` 참조 |
| `kit/palette.json` | `parts/art/palette/lopad.json` 사본. UI 는 `floors[].ramp`(층 강조 16~27) 만 읽는다. 세피아·무채는 `theme.ts` 에 고정값 |
| `weapons/<id>_icon.png` | HUD 무기 아이콘 (30라운드, 아트 사본) |
| `fonts/*.woff2` | Galmuri11/14/9/11-Bold (OFL). UI 는 11·14 만 쓴다 |

로드 경로는 전부 `assets-game/ui/...` (시스템 vite 플러그인).

### 소유 코드 (`src/ui/`)
| 파일 | 내용 |
|---|---|
| `index.ts`, `keys.ts` | 계약 §5 공개 지점 (`UI_SCENES`, `uiScenes`). 변경 없음 |
| `theme.ts` | 팔레트 고정값(`GRAY` G00~G15, `SEPIA` S0~S5, 1층 램프 폴백), 글꼴(`FONT`: Galmuri11 11px/12, Galmuri14 14px/15), **발광 글자 스타일 표 `TEXT_STYLES`**(page_body/page_title/page_selected/page_unsel/page_faint/ink_body/ink_faint/ink_accent — 계약 1.2절 그대로, `accentSlot` 은 현재 층 램프 슬롯), 레이아웃 수치 `LAYOUT` |
| `kit.ts` | 키트 로더 `preloadKit`(씬마다 호출, 있는 텍스처는 건너뜀)·`setupKit`(아이콘 프레임·커서 애니), 글꼴 로드 `fontsReady()`(Galmuri11 은 style.css, **Galmuri14 는 `FontFace` API 로 UI 가 직접 등록**), 층 강조색 `accentHex(scene, stageIndex, slot)`, **9-slice `NinePanel`**(Image 9장 Container — Phaser `NineSlice` 는 WebGL 전용이라 쓰지 않음), `inkPanel`, 페이지 `paperPage`(panel_paper + paper_tile + 얼룩 3~5 고정 seed), 책 `book`(틀 + 페이지 1·2장 + spine), `rule`, `icon`, `cursor`, 게이지 `Gauge`(frame/boss/gray, 1층은 그려진 amber 띠, 2층부터 gray 띠 × 램프 23 틴트) |
| `glow.ts` | **`GlowText`** = 발광 글자 (Container). 그늘 8개(맨해튼 2) → 할로 4개(4방향, 알파) → 본색 1개를 Text 로 복제해 겹친다 (계약 "정확한 방법"). `setText`(바뀔 때만), `setGlowStyle`, `setStageIndex`(강조색 재칠), `placeCenter/placeRight`(정수 위치), `makeInteractive`, `scale 2` 정수 확대. 헬퍼 `glowText()` |
| `widgets.ts` | `SelectList`: 숫자/W·S·방향키+Enter/마우스. 선택 `page_selected` + `cursor` 스프라이트(2프레임), 비선택 `page_unsel`, 비활성 `page_faint` α0.45 + '(불가)', detail `page_faint` 아래 줄(줄바꿈 가능). 잉크 바탕(`surface:'ink'`)은 `ink_body`/`ink_faint` + `cursor_light` |
| `text.ts` | 세계관 문구 `uiText`, `fill`, `controlsLine` (변경 없음) |
| `TitleScene.ts` | 어두운 바탕 + `title_diary` 2배 + 'LOPAD'(Galmuri14 ×2 ink_body) + 부제(ink_faint) + 메뉴(잉크 SelectList) + 조작법 줄 |
| `HudScene.ts` | 하단 중앙 `panel_ink` 480×64 (x 240, y 464): 1행 `icon_hp` + 체력 게이지 170 + 수치 + `icon_gold` 수치 + `icon_potion` 수치 + Q(ink_faint); 2행 무기 아이콘 + 이름·진화명(ink_body) + `icon_sense` + 개성 게이지(gray 100) + 수치(ink_faint) + '우클릭 ○○'(ink_faint, 우측 정렬). 보스 `gauge_boss` 360 은 묶음 위 8px + `icon_boss` + 이름·HP·페이즈(ink_accent). 자막(STORY)은 보스 이름 위(보스전 아니면 묶음 위), ink_body, 패널 없음. 상단 좌 층 제목·시련(ink_body), 상단 우 `minimap_frame` + 'M 음소거'(ink_faint) + `icon_sound`. 우하단 공지 작은 ink 패널 + `icon_exit`/`icon_boss` + ink_accent. 배너(층 시작·개성 변화) 가운데 ink_body ×2. Esc 는 `keydown-ESC` 이벤트 |
| `Minimap.ts` | `minimap_frame` 9-slice, 칸 12px, 방문한 방 G01 칸 + `mini_*` 글리프, 연결선 G02, 현재 방 층 강조 22 테두리 + 글리프 틴트, 클리어 시련 글리프 α0.45 |
| `MenuScene.ts` | 모든 메뉴 id 공용 **일기장 한 페이지**: 제목 page_title ×2(한자 가능 → Galmuri11) + `rule` + SelectList + footer(page_faint). 페이지 폭은 내용에 맞춤(최소 420, evolve/ending 520, 최대 W-64) |
| `PauseScene.ts` | 일기장 한 페이지 440×264 (책 472×296): 제목 '일기장'(Galmuri14), 이름·층·시련 / 능력치 / 무기(개성) / 패시브 / `icon_save` 세이브 남음 + 시드(page_faint) / `rule` / '[1] 더 쓴다 (Esc)' '[2] 일기장을 덮는다' → '[1] 적지 않은 것은 남지 않는다. 그래도 덮는다 — 예' '[2] 더 쓴다' / 조작법(page_faint) |
| `ResultScene.ts` | **두 페이지 펼침** 책 632×432 (페이지 292×400 ×2 + spine 16). 왼쪽: '한 생을 다 썼다'/'쓰러졌다'(Galmuri14) + `rule` + `diary_closed` + 이름·층(도달) + 처치 + `icon_gold`·`icon_sense`·`icon_souls` 수치 + 무기 + 시드. 오른쪽: 스토리 문장(`line`, 줄바꿈) + 엔딩 부제(page_title) + `rule` + '[1] 다시 태어난다 (영혼 → 개성 선택)' '[2] 일기장을 덮는다' + `stamp_clear`/`stamp_dead` α0.85 |

### 좌표 규칙
- 내부 해상도 960×540, 모든 좌표 정수, `scale.width/height` 기준. 1280×720 창 = 1배, 1920×1080 = 2배.
- 글자는 Galmuri11 11px(한자 포함 가능) 본문·HUD·메뉴·자막. 제목은 Galmuri14(한자 없는 고정 제목: 일기장·LOPAD·한 생을 다 썼다·쓰러졌다) 또는 Galmuri11 ×2(메뉴 제목·배너 — 한자 가능). Bold 없음. 줄 간격 = 글꼴 높이 + 4 이상(`lineSpacing 4`, 목록 줄 18).
- 종이 위 글자는 `TEXT_STYLES` 의 page_* 만, 잉크 위는 ink_* 만. 새 색 없음 (알파 0.5/0.55 만).

### 격리
- `src/ui/**` 는 `src/contract/ui.ts` 와 `phaser` 만 import (ESLint). 시스템은 `src/ui/index.ts` 만 import.

### 검증 (2026-10-02, 헤드리스 Playwright, `vite preview --port 4175`, 스크립트 `scratchpad/ui41.cjs`, 스크린샷 `scratchpad/ui41/`)
1280×720(1배)·1920×1080(2배): 타이틀 → HUD 1층(묶음·미니맵·음소거 힌트) → 휴식 방 자막 → evolve 메뉴(커서 이동) → 개성 배너 → 일시정지 → 확인 → 재개 → 2층 배너·일시정지(**선택 할로 녹색**) → 2층 보스(게이지 녹색·이름·자막) → 보상·패시브 메뉴 → '오르는 길 열림' 공지 → 사망 결과 → 8층 황제 → ending 메뉴 → 클리어 결과('다음 전장으로'). `document.fonts.check` Galmuri11·14 true. 콘솔 오류·경고 0, HTTP 4xx 0. tsc·eslint·vitest(88)·build 통과.

### 41라운드 자율 결정 (임시값, 도영 님 검토 대상)
1. 발광 글자 구현은 **Text 13장 Container** (계약 "정확한 방법"). RenderTexture 굽기는 WebGL(헤드리스 swiftshader)에서 Text 가 그려지지 않아 보류.
2. 9-slice 는 Phaser `NineSlice`(WebGL 전용) 대신 Image 9장 Container.
3. 글꼴: Galmuri9 미사용(detail 도 Galmuri11 page_faint). Galmuri14 는 UI 가 `FontFace` 로 직접 등록(style.css 추가 요청 병행).
4. 게이지 층 색: 1층은 아트가 그린 amber 띠 그대로, 2층부터 `gauge_fill_gray` × 램프 23 곱 틴트. 개성 게이지는 gray 띠 그대로.
5. HUD 수치 배치: 이름 옆 간격은 텍스트 폭에 따라 밀린다(전표 최소 x+282, 독주 최소 x+352, 감각 최소 x+200). 하단 여백 12px(권장 16 보다 작음 — 패널이 플레이 영역을 덜 가리게).
6. 보스 처치 뒤 스냅샷에 `boss.hp 0` 이 남는 동안 보스 게이지를 숨긴다.
7. 자막은 kind 와 무관하게 ink_body(보스 자막도). 공지 패널은 `exitOpen` 우선, 아니면 `bossUnlocked`.
8. 일시정지 '[1] 더 쓴다 (Esc)' 는 텍스트 팩 `pause.cancelQuit` + ' (Esc)' (팩의 `pause.resume` '계속하기 (Esc)' 대신 — 31라운드 채택 문구).
9. 결과 왼쪽 페이지의 재화·영혼·감각은 아이콘 + 수치(`UiResult` 에 `names` 가 없어 이름을 못 씀).
10. 미니맵 칸 12px, 격자 7×7 기본(틀 100×100). 클리어 시련 글리프 α0.45.
11. Esc 처리를 `JustDown` 폴링 → `keydown-ESC` 이벤트로 변경 (씬 전환 프레임에 Key 가 눌린 채 남아 재개가 안 되던 문제).

### 계약 추가 요청 (프로듀서 인터뷰 대기)
- `UiSnapshot.weapon.id` (아이콘 매핑), `UiSnapshot.mute` (음소거 상태 표시) — 30라운드 요청 유지.
- `UiResult.names`(또는 결과에 재화·영혼 이름) — 결과 페이지에 세계관 이름을 쓰기 위해.
- evolve 강화 항목 label 이 '더 깊게 — 현재 개성 피해·범위 +15% (1/3) — 사무라이 칼' 로 와서 detail 과 겹친다(계약 §7 "label 은 이름만"). 시스템 반영 요청.
- 보조 동작 진행도(가드·차지·쿨), 감각(feel) 토글 표시는 범위 밖(설정 토글은 41라운드 범위 밖).

### 시스템에 부탁할 것
- `public/style.css` 에 Galmuri14 `@font-face` 추가 (`assets-game/ui/fonts/Galmuri14.woff2`). 없어도 UI 가 FontFace 로 등록하지만 선언이 있으면 더 빨리 뜬다.

### 다음 인터뷰 후보
- 1배 창(1280×720)에서 11px 본문 가독성 확인 (도영 님 실기 체감)
- 개성 선택 화면(3획·리듬)의 정식 비주얼 (시스템 플레이스홀더 → 일기장 컨셉으로)
- 상점·보상 메뉴의 아이콘·설명 레이아웃
- 설정 화면(키 변경, 음량·음소거 상태)
- 데미지 숫자·피격 연출 등 전투 피드백 UI (현재 시스템 소관)

---

## 이전 기록

### 개시 (2026-10-01, 16라운드)
결정: `decisions/2026-10-01-round-16-ui-kickoff.md`. 교차 참조 승인: `decisions/cross-references.md` #1·#2. 계약: `contracts/ui-system-interface.md`.
검증(헤드리스): 타이틀 → 새 런 → 메타 메뉴 → 3획·리듬 → 게임(HUD) → 시련 → 보스 → 감각 보상 → 패시브 → 출구 열림 → Esc 일시정지 → 재개 → 사망 → 결과. 콘솔 오류 0.

### 스토리 반영 (2026-10-01, 26라운드 · 교차 참조 #4)
HUD `STORY` 자막(공지 1.8초/그 외 3.6초), 층 제목(`floorTitle`), 재화·물약 이름(`names`). 일시정지·결과에 이름·층 제목.

### 29라운드 (자율 진행 · 세계관 문구 · evolve 메뉴)
세계관 문구 적용(`getUiText`, 키 없으면 기본 문구), evolve 3지선다 detail 아래 줄·비활성 흐림·'(불가)', 라벨 끝 ' — 설명' 중복 제거 규칙. 검증 `scratchpad/ui29.cjs`.

### 30라운드 (자율 진행 · 엔딩 화면 · 무기 아이콘 · 음소거 힌트)
결과 엔딩 부제(`clearedDestroy`/`clearedUnderstand`), ending 메뉴, HUD 무기 아이콘(`assets/ui/weapons/`, 이름→id `WEAPON_ICON_IDS`), 'M 음소거' 힌트. 검증 `scratchpad/ui30.cjs`.
