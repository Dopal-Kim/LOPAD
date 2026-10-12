# 게임 UI 파트 — 작업 기록

## 62라운드 (2026-10-12) · 루프 3 UI G — 지도로 먼저 고르고 키아트는 작은 미리보기 · 짧은 먹 번짐 암전 (도영 님 추가 지시)
도영 님 원문: "키아트 넘어가는 과정이 조금 불필요하다고 느껴지네 차라리 어느 장소로 가는지 맵으로 먼저 고르고 그 장소 미리보기 효과로 키아트를 작게 띄워주는 방식이 더 좋을 것 같다." 판단: `decisions/2026-10-12-round-62-full-delegation.md` '루프 3 착수 중 추가 지시'. 계약: `src/contract/ui.ts` '62 시스템 H' 절(`UiRouteNode.previewKey`·`previewRegion`, `UiMenuLine.previewKey`·`previewRegion`, `UiTransitionMode` 'fade', `UiTransitionBegin.durationMs`). 계약 필드는 이름으로 읽어(`readPreviewKey`·`readPreviewRegion`) 커밋 순서와 무관하게 동작.

### 지도 미리보기 카드 (새 `RoutePreview.ts`, 순수 `previewView.ts`)
- 노드 지도(고르기·M 보기)에서 가리킨 곳(방향키·마우스 올림)의 그림을 작은 액자 카드로: 옻칠 테 S1·바랜 금 선 S5·그늘 3 · 그림 아래 먹 띠(위로 4계단 번짐) 안에 [종류 아이콘 16] 이름 · 종류 / 고유 한 줄(공개된 이벤트 내용 이름, 없으면 설명 첫 문장) / 보상·위험 한 줄(강조) / 위험 노드면 `riskText`(강조). 숨은 노드 얼룩은 카드 없음.
- 그림: ① 시스템 `previewKey` 텍스처가 이미 있으면 그것(`paint/door_*` — 시스템이 고른 키만, 이름 규칙으로 찾지 않음) ② 없으면 `previewRegion`(없으면 지역 표시 이름 낱말) 키아트 ③ 종이 + 종류 아이콘 크게. previewKey 를 받았는데 아직 로드 전이면 키아트로 띄워 두고 `addtexture-<키>` 가 오면 같은 자리에서 그 그림으로 교차 페이드.
- 크기: 노드 지도 그림 256×144(액자 포함 264×152) — 지도 칸 565×317 어디를 가리켜도 그 곳 아이콘·이름표를 가리지 않는 옆자리가 남는 크기(지시의 '약 300×170' 에서 줄임, 테스트로 전 구간 확인). 수련장 지도는 288×162. 렌더 2배 텍스처(576×324, LINEAR)를 1/2 로 그려 1920 렌더에서 1:1.
- 자리(`placePreview`): 가리킨 곳 오른쪽·왼쪽(기본)·위·아래 × 맞춤 세 자리 + 칸 위/아래 끝 후보 중 겹친 넓이 × 무게 합이 가장 작은 곳(가리킨 곳·그 이름표 1000, 지금 곳·다른 고를 곳·그 이름표·주인공 표시 40, 그 밖 노드 3, 이름표 1). 같으면 넓은 쪽(가리킨 곳이 왼쪽 절반이면 오른쪽)·가까운 쪽. 카드는 입력을 받지 않아 아래 노드를 가리켜도 마우스 올림이 그대로 닿는다.
- 가리킨 곳이 바뀌면 0.15초 교차 페이드(들어오던 카드는 지금 밝기에서 사라짐), 그림은 아주 느린 켄번스(1 → 1.03 → 1, 한쪽 9초, 좌우 치우침은 id 마다) — 자르기(setCrop)로 칸 크기는 그대로.
- 외길이어도 시스템이 지도를 열므로 첫 고를 곳을 가리킨 채 시작 → 카드가 바로 보인다.
- **확인 창 폐지**: Enter·Space(뗀 뒤)·좌클릭(같은 곳에서 눌렀다 뗀 것) 한 번으로 간다. UI D 무장 게이트(armMs·열기 전 누르던 키) 그대로. `RouteConfirm.ts` 삭제(`hasDepth` → `displayOrder.ts`), HUD Esc 의 확인 창 분기 삭제, 안내 줄 '←→↑↓ 가리키기 · Enter · 클릭 그리로 간다 · Esc 물러나기'.

### 수련장 지도 (`TrainingMap.ts`)
- 같은 카드: 고름 자리 방(키·마우스)의 `previewKey`(`paint/door_training_training`·`_boss`, 없으면 `doorKey`) → 없으면 지도 그림(`paint/map_training`)에서 방 자리 둘레 16:9 조각(그림 폭 30%) → 종이 + 작은 입구 그림. 이름 · '수련장 방' / 방 한 줄 / 도장 받은 방은 '도장을 받았다 — 다시 들어갈 수 있다'. 방·이름표 모두 고를 곳 무게.

### 짧은 먹 번짐 암전 `mode: 'fade'` (`TransitionScene`·`transitionView`)
- 캡처·그림·액자·흔들림·섬광 없이 가장자리에서 먹(G00 + 얼룩·섬유 결)이 번져 덮음(기본 0.38초, 시스템 `durationMs` 를 0.25~0.6초로 잘라 씀) → `covered` → READY 뒤 가운데부터 0.3초에 걷힘 → `end`. 번짐 순서 = 사각 가장자리 거리(제곱근) × 0.72 + 먹 얼룩 잡음 × 0.28(`inkEdgeOrder`, 변주 3장 캐시). 지도는 덮일 때까지 그대로 보인다(기존 `RouteControl.leave`).
- READY 가 덮기 전에 와도(시스템 안전장치) 덮인 즉시 걷힌다. 건너뛰기: 덮는 중 키 → 바로 덮음, 걷히는 중 → 짧게.
- 로딩 카드: 기존 규칙 그대로(덮인 뒤 READY 가 0.55초 넘게 늦을 때만 — 'fade' 에서 확인). floor·타이틀 파고들기·enterNode·exitRoom·training 모드는 손대지 않음.

### 지역 카드 (`HudBanners.ts`)
- 지도 미리보기로 그림을 이미 보고 'fade' 로 들어온 노드(5초 안의 마지막 전환이 'fade', `transitionState.recentTransitionMode`)에서 지역이 바뀌면 화면 가득 키아트 카드 대신 위 가운데 알림 줄 띠 하나: 노드 이름(2배) / '지역 · 지역 한 줄'(강조). 바로 뒤 같은 이름의 노드 배너는 삼킨다. 탄생·층 이동·이어하기는 그대로 큰 카드.

### 검증
- `npx tsc --noEmit` 0 · `npx eslint src/ui` 0 · prettier(바뀐 파일) · `npx vitest run src/ui` 36 파일 312(새 `previewView.test.ts` 12 — 자리·지도 칸 전 구간 무가림·글·그림 고르기·켄번스·교차 페이드·수련장 조각, `fadeTransition.test.ts` 5 — 페이로드·단계·번짐 순서·덮개 알파·마지막 전환).
- 헤드리스 Playwright 1920×1080(작업 트리 `vite build` 정적 서버, `scratchpad/u62g/` — `run.cjs` 가짜 갈림길·`run2.cjs` 실제 런·`run3.cjs` 실제 수련장): 첫 곳 자동 가리킴 + 카드(위험 노드 경고 줄) → → 다음 곳 교차 페이드 → 늦게 온 previewKey 그림으로 바꿔 끼움 → 마우스 올림 → 클릭 한 번 `chooseNode`(확인 창 없음) → 먹 번짐 암전 중간(지도 위로 가장자리부터) → 덮임 → 걷힘 → 끝, 'fade' 로딩 카드(READY 1.7초 지연), 실제 런 외길 지도 → Enter → 시스템 'fade' → 새 방 + 합친 지역 띠, 실제 수련장 지도(그림 메타 자리) 1·4·8번 방 카드(`door_training_training`·`door_training_boss`) → Enter → 'fade' → 방. 페이지 오류 0(404 1건은 바뀌기 전 빌드에서도 같음).
- 스크린샷: `g_01_first`·`g_03_second`·`g_04_swapped`·`g_05_hover`·`g_06_fade_mid`·`g_09_fade_loading`·`r_01_real_map`·`r_02_real_fade_mid`·`r_03_real_after`·`t_01_training_map`·`t_03_training_map8`·`t_04_training_fade`.

## 62라운드 (2026-10-12) · 루프 2 UI E — 시스템 C 계약 2차 패스 (유품 카드 · 결산 일기장 · 기억 장 · 출구 화살표 · 사망 걷기 · 첫 개성 발현 4~5장)
결정: `decisions/2026-10-12-round-62-full-delegation.md`, 계획 `2026-10-12-P16-loop2.md` §1~4. 계약: `src/contract/ui.ts` '62 루프 2 시스템 C' 절(지금 `uiLoop2.ts` 재수출), 스토리 63 팩(relics·floorEnd·deathSummary·memory), 용어집, 아트 §31(ui_relics·ui_portraits·map_marker_ghost). 입력 규칙은 UI D 공통 헬퍼(`choiceGate`·`choiceArm` — 열린 뒤 무장·열기 전 눌린 키는 뗀 뒤만·클릭은 눌렀다 뗀 것만)를 새 화면 모두에 썼다.

### 유품 카드 (P1-5 — `choiceCardView.relicCard`·`MenuChoiceCards`·새 `cardZoom.ts`)
- 메뉴 줄에 `line.relic` 이 있으면 머리표 '유품' · 그림 `relic.iconKey`(128 → 64, 세피아 테) · 이름 · '{n}단계 · 태그' · 한 문장(수치 없음) · 지닌 유품이면 '지닌 유품 — 한 단계 깊어진다'.
- **상세 보기**: 수치(`relic.detail`)와 흐린 한 줄(`flavor`)은 카드 앞면이 아니라 깔개 안 카드 줄 아래 '상세 칸'에 고름 자리 카드 것만(고름 자리를 옮기면 바뀐다). 계약의 'D 키'는 카드 줄에서 D 가 이미 오른쪽 이동(WASD)이라 키를 붙이지 않았다 — 입력은 UI D 몫이라 그리기만.
- Tab 빌드·일시정지 빌드 쪽: `snapshot.relics` 가 오면 이름 · 단계 · 태그(수치 없음), 없으면 옛 `passives`.

### 결산 일기장 (P1-6·P1-7 — `ResultScene` 재구성, 새 `ResultPages.ts`·`ResultMap.ts`·`resultView.ts`)
- 두 쪽 펼침 372×468. 사망: '이 생의 기록' · 이름(61 번짐 유지) · 쓰러진 곳 · 마지막 상대(초상 `ui_portraits` 96 UI 1배 — 없으면 '?') · 이름 · 한 줄 · 시간·처치·받은 피해 · 지닌 것 아이콘 줄(32, 그림 없으면 이름 한 자, 마우스 올리면 이름) / 오른쪽: 지나온 길 미니맵(지도 길 흐림 · 지난 길 강조 · 쓰러진 곳 × + 먹 붓 망령 `map_marker_ghost` 6칸 반복, 종이빛 번짐) · 이야기 한 줄 · 영혼 +n · `soulsLine`(열 수 있으면 강조).
- 층 끝: '1층 끝' · 층 제목 · 일기장 문장 · 칸(시간·처치·받은 피해·단서·영혼) · 지닌 것 / 오른쪽: 지나온 길 · **빈 괘선 장 가운데에 맺음 문장이 2배 글씨로 한 문장씩 적히고 붓 한 획** → footer·다음 기억 한 줄 → 버튼·완(完) 도장(일기장 마지막 장 연출).
- 버튼 [1] 다시 태어난다 · [2] 기억을 떠올린다(기억 장 덧그림 — 장을 열 수 있을 때만) · [3] 일기장을 덮는다 → `uiCommands.endChoice`(없으면 startNewRun·toTitle). Esc = 덮는다. 층 끝 버튼·무장은 맺음이 다 적힌 뒤. 옛 감각(눈 아이콘)·전표 줄 삭제, 옛 팩 `result.retry`('영혼 → 유산' 꼬리) 대신 63 팩 문구.

### 기억 장 (P1-8 — 새 `MemoryBook.ts`·`memoryView.ts`)
- 두 쪽: 왼쪽 '기억' · 머리 문장 · 지닌 영혼 · 다음 기억 한 줄 · 고름 자리 기억(그림 64 · 장 이름·무기 · 이름 · 단계 · 한 문장 · 수치 · 흐린 한 줄 · 상태 · [Enter] 떠올린다/지니고 태어난다/내려놓는다) / 오른쪽 다섯 칸(소품 · 손이 기억한 모양 · 떠올릴 개성 · 장터에 놓일 것 · 몸의 기억) — 칸 44(그림 32, 없으면 이름 한 자 — 몸의 기억은 첫 낱말) · 떠올림 ✓ · 지닌 소품 테 · 떠올릴 수 있으면 점 · 몸의 기억 단계 마름모.
- 떠올리기 연출: 칸에서 먹 고리가 번지고 칸이 한 번 튀어 오름 + 왼쪽 아래 '떠올렸다 — {이름}. 다음 생부터 함께한다.' (메뉴가 다시 열려도 1.5초 안이면 이어서).
- 쓰는 곳: 메뉴 'meta'(의식 덧쓰기 F2 — 떠올리기 'm:<id>', 덮기 '0', Esc 는 MenuScene) · 타이틀 새 항목 '기억'(지난 생·영혼이 있을 때, 수련장 다음) · 결과 화면 [2]. 타이틀·결과는 `memory.book()`·`unlock`·`setKeepsake` 와 MEMORY_CHANGED 로 다시 그린다. `metaAutoEnter` 는 줄에 `line.memory` 가 있으면 건너뛰지 않는다(볼 것이 있는 장).
- 소리: 이동·고르기·덮기 `uiSound`(시스템 F — 렌더러 메뉴 소리는 UI 몫). 결과 버튼 목록도 `sounds`.

### 운명 공개 뒤 고르기 (`MemoryPickCards.ts`, `RitualFate`)
- 메뉴 'aspect'·'keepsake' 를 카드로(1~5장, 4·5장은 좁힘): 머리표(손이 기억한 모양 / 기억의 소품 / 빈손) · 그림 `line.memory.iconKey`(처음 모양은 무기 아이콘 4배, 빈손은 점선 빈 칸) · 이름 · 한 문장 · 상세 칸(수치 · 흐린 한 줄). 고르기는 CardRow(UI D).
- 운명 공개 장: 회피 시험 결과는 `ritual.giftNote`(없을 때만 옛 gift) · 아래 '손이 기억한 모양 · {이름}' / '지니고 태어난다 · {이름}' 그림 줄(`ritual.memory`, 고를 때마다 갱신). 고르는 동안 Enter 는 페이지가 받지 않는다.

### HUD (`HudLoop2E.ts` — HudScene 은 연결만)
- `DEATH_STARTED`: 알림·자막·쪽지·토스트·Tab 빌드·지도를 거두고 HUD 카메라를 0.26초(슬로모 앞 절반 안)에 걷는다 → 먹 번짐 위에 아무것도 남지 않음. STAGE_STARTED·BIRTH_STARTED·노드 진입·씬 재시작에 되돌림.
- `exitHint`: 출구가 화면 밖이면 그 방향 가장자리에 강조색 화살(그늘 테 · 출렁임) + 안쪽에 '오르는 길'. 메뉴·지도·탄생·사망·문 걸어 나가기(door walkOut·inside·walkIn) 중엔 숨김.

### 첫 개성 발현 4~5장 (`growthView`·`GrowthCards` 배치만)
- `isGrowthMenu` 2~5장. 폭 4장 188·간격 14 / 5장 150·간격 12(이름 1배), 좁은 카드는 '[키] … 바뀜' 을 키 아래 줄로. 입력은 UI D 몫 그대로.

### 검증
- tsc 0 · eslint src/ui 0 · prettier(바뀐 파일) · vitest src/ui 34 파일 295(새 `loop2e.test.ts` 17 — 유품 카드·빌드 쪽·4~5장 폭·기억 장 격자·동작·다음 줄·메뉴 판별·떠올리기 대상·타이틀 항목·결산 미니맵·칸·문장·버튼·옛 결과).
- 헤드리스 Playwright 1920×1080(작업 트리 `vite build` 미리보기, `scratchpad/u62e/` — death·boss·memory·ui·title 드라이버): 사망 → HUD 걷힘 → 결산 → [2] 기억 장 → 떠올리기 연출 → Esc 로 결산 / 보스 군주의 유품 3장(상세 칸) → 층 끝 일기장 / 의식 F2 기억 장(메뉴) 떠올리기 → 모양·소품 카드 → 운명 공개 줄 / 개성 4·5장(가짜 메뉴) / 타이틀 '기억'. 페이지 오류 0.
- 메모: `page.clock` 가짜 시계에서는 키 이벤트 `timeStamp`(실제)와 `performance.now()`(가짜)가 어긋나 무장 게이트가 키를 버린다 — 입력 확인은 가짜 시계 없이 했다.

## 62라운드 (2026-10-12) · 루프 2 UI F — 시스템 D 계약 2차 패스: 사연 메뉴 · 결과 컷 · 숨은 보상 · 장터 노점 카드 · 상인 말하기 · 팻말 · 무리 방향 (P1-12·13·17, P2-10)
결정: `decisions/2026-10-12-P16-loop2.md` §5·§8, 전권 위임. 계약: `src/contract/ui.ts` '62 루프 2 시스템 D' 절(이후 `uiLoop2.ts` 재수출) · `snapshotLoop2D.ts`. 문구 = 스토리 63 팩 `events`·`shop`(시스템이 내려 줌, `textLoop2F.ts` 는 대체). 그림 = 아트 §31(`events/cut_*`·`ui_relics/*`·NPC·드랍 시트 — 시스템이 로드한 키만 씀).

### 사연 메뉴 · 상인과 말하기 (새 `MenuEvent.ts`, 순수 `eventView.ts`)
- `event` 메뉴에 `UiMenu.event` 가 있으면(또는 `shopTalk`) 일기장 한 쪽: 제목(2배) · 괘선 · [말하는 이 초상 72×84 — NPC 시트 0프레임 1배 상반신, 잘린 아틀라스 trim 맞춤(`portraitFit`)] 이름(흐림) / 첫 마디(말이면 「」, 지문이면 그대로) / 설명 문단(읽는 글 — 글자 크기 설정 따름) / footer 에만 있는 줄(다음 각성 미리보기 등) → 괘선 → '하나를 고른다 · 내준다 · 얻는다' 머리 → 선택지 표(줄마다 `[키] 이름 | 대가 아이콘 | 보상 아이콘`, 숨은 보상은 '?' 그림만).
- 아이콘을 그린 줄은 detail 글을 숨긴다 — 못 고르는 줄만 까닭(흐림). 상인 줄의 값(`price`)은 대가 칸 전표 아이콘으로 옮기고 라벨 끝 ' · 전표 15' 는 뗀다. 상인 메뉴(event 없음)는 제목 = 상인, 첫 마디 = footer.
- 고르기 = `CardRow`(UI D 무장 게이트 · 눌렀다 뗀 클릭만) + 새 `nav` 인자 `listFocusMove`(↑↓·W·S 세로, 끝에서 돌아감). '0' 지나간다/그만 본다도 표의 한 줄. 화면을 넘으면 옛 목록으로.
- 소리(시스템 F 메모): 이동 ui_move · 그만두기 ui_back · 상인 고르기 ui_select. 사연 고르기는 시스템이 event_choice 를 내므로 ui_select 생략.
- 아이콘 시트 새로 `assets/ui/kit/event_icons.png`(+json, 생성기 `parts/ui/tools/event_icons.py`): 키트 icons.png 결 16×16 손도트 8종 — 최대 체력(심장) · 각성(불꽃) · 유품(끈 달린 패) · 저주(먹 봉인) · 값 깎기(꼬리표) · 무리(창날 둘) · 일기장 · '?'. 전표·독주·체력은 키트 그대로. 'sense' 는 1층 화면에 없는 말이라 '?'.

### 결과 컷 · 숨은 보상 (새 `EventCut.ts`)
- `ui:event-result`: 화면 가운데 위쪽 종이 패널 — 컷 그림 320×180(1배) · 한 줄(읽는 글) · '내준다 [아이콘] · 얻는다 [아이콘]' · '[E] 계속'(설정의 상호작용 키). 3.2초 머문 뒤 사라짐, E·클릭으로 바로 닫힘. 그림이 없으면 글만.
- 이어지는 보상 메뉴(유품 고르기 등)는 컷이 보이도록 최대 1.4초 기다린다(uiSequence 'eventCut'). 이를 위해 `MenuScene.onOpen`: 앞 메뉴를 닫은 같은 순간 다음 메뉴가 열리면(성장 메뉴 제외) 앞 쪽을 걷고 `menuWaitMs()` 만큼 기다린 뒤 그린다(기다리는 동안 Esc 무시).
- `ui:hidden-reward`: 위 가운데 알림 줄 '개성' 급(growth 30): 잉크 띠 위 '다음에 받는다'·'받았다'(흐림) / [아이콘] 한 줄.

### 장터 노점 카드 · 산 연출 (새 `ShopOfferCard.ts`, `HudLoop2F.ts`)
- `snapshot.shopOffer`: 물건 윗변 위 작은 종이 카드(폭 168, 물건 쪽 꼬리, 화면 밖이면 아래로) — [그림] 이름 / (유품이면 희귀도 마름모 · '{n}단계 · 태그') — 한 줄 — [전표] 값 · '[E] 산다'(못 사면 값 줄 아래 까닭, 팔렸으면 '팔렸다'). 그림: 유품 = `relic.iconKey` 64(UI E 와 같은 `traitIconBox`), 물건 = 드랍 시트 잘린 그림 칸 맞춤(1배가 들면 1배). 카드가 떠 있으면 같은 노점의 E 말풍선은 숨김. 나타나기는 실제 시각 페이드(씬 트윈이 멈춰도).
- `ui:shop-purchased`: 물건 자리에서 주인공 쪽(화면 가운데 — 시스템 요청 참고)으로 빨려 드는 반짝임 7점 + 전투 묶음 전표 숫자 옆 '−n' 떠오름(`CombatHud.goldAt`).

### 팻말 · 무리 방향 (새 `WorldSigns.ts`, `WaveArrows.ts`)
- `snapshot.signs`: 허수아비 머리 위 나무 판자(S1 · 나뭇결 · 못 · 말뚝) — 이름(흐림) / 값(밝게), Galmuri, id 별로 지키고 글이 바뀔 때만 다시 그림.
- `UiEnemyIncoming.side`: 화면 가장자리 화살촉(바깥을 가리킴, 강조 22 + 먹 외곽) 몇 번 깜빡이고 사라짐. 위쪽은 y 24(알림 줄 위 끝 40 보다 위), flank = 양옆, around = 사방.

### 확인만
- P1-14 보스 국면 '???': UI C 가 `phaseStrip(…, '???')` 로 처리함(국면 띠의 오지 않은 국면 = '???', 국면 카드 이름은 BOSS_PHASE 때).

### 검증
- `npx tsc --noEmit` 0 · `npx eslint src/ui` 0 · `npx vitest run src/ui`(34 파일 295 — 새 `eventView.test.ts` 17) · prettier 통과. 헤드리스 Playwright 1920×1080(작업 트리 `vite build` 미리보기, `scratchpad/u62f/run1.cjs`·`run2.cjs` · 캡처 f01~f11): 시음회 메뉴(초상·아이콘 표) → 1 → 결과 컷 → 유품 고르기, 장터 노점 6칸 카드 · 사기 반짝임 · 상인 말하기·외상 목록, 유품 카드(전표 모자람), 숨은 보상 알림, 무리 화살촉, 팻말, 지문/못 고르는 줄 사연. 콘솔·페이지 오류 0.

## 62라운드 (2026-10-12) · 루프 2 UI D — 메뉴가 뜨기 전 렉 · 원치 않는 선택 막기 (도영 님 피드백, 전권 위임)

도영 님 원문: "인터페이스 뜨기 전에 렉 걸리는 거 좀 고치고 렉 걸려서 뭐 원하지 않은 개성 발현 눌려서 답답하니까 이런 것도 개선해봐".

### 렉 원인과 고친 것
- **원인 (측정으로 확인)**: 발광 글자 `GlowText` 하나가 Phaser Text 13개(그늘 8·할로 4·본색 1)였다. Text 하나마다 만들 때 글꼴 높이 측정(캔버스에 그려 픽셀 훑기) + 빈 글·글·색으로 세 번 다시 그리기 + 그때마다 GPU 업로드 → 카드 3장 메뉴 하나에 Text 300~400개·업로드 1,000번 이상이 한 프레임에 몰렸다 (노드 지도는 Text 950개).
- **한 장에 굽기** (`glow.ts` · 새 `glowRaster.ts`): 게임마다 공유 래스터 Text 하나(표시 목록 밖·GPU 업로드 없음)가 흰 글자를 한 번 그리고, 2D 캔버스 하나에 색을 입혀 그늘 → 할로 → 본색 순서·알파로 찍어 Image 하나로 그린다. 글꼴 높이는 글꼴·크기마다 한 번만 잰다. 화면은 예전과 픽셀 단위로 같다(헤드리스 비교: 다른 픽셀은 움직이는 커서뿐).
- **재사용 풀** (새 `glyphCache.ts`): 같은 글·글꼴·줄바꿈·색 겹이면 이미 구워 올린 텍스처를 빌려 쓴다 — 메뉴 다시 열기·고름 자리 옮기기(선택/비선택 스타일 오가기)·카드 키 [1]·머리표·안내 줄은 굽지도 올리지도 않는다. 320장 넘으면 쓰지 않는 것부터 지운다.
- **미리 데우기** (새 `uiWarm.ts`, HUD 가 뜨고 글꼴이 다 읽힌 뒤 0.6초): 두 글꼴 높이 측정 + 늘 나오는 글(카드 키·머리표·안내·닫기·지도 제목 등)을 한 프레임 4개씩 구워 둔다.
- 함정 하나: CanvasTexture 를 큰 캔버스로 바로 만들면 Phaser 가 `getImageData` 로 전체를 되읽는다(가속 캔버스면 GPU 되읽기 — 헤드리스에서 글 37개에 6.3초). 1×1 로 만들고 크기만 맞춘 뒤 그려 한 번 올린다.
- 성장 메뉴는 성과 카드를 기다리지 않는다 (시스템 E 요청 — 시스템이 이미 미뤄 둔다).
- 프레임 분할 생성은 넣지 않았다: 위 셋 뒤 카드 메뉴가 헤드리스(소프트웨어 GPU·과부하)에서도 10~55ms 라 나눌 만한 덩어리가 남지 않았다. 카드는 대신 실제 시각으로 천천히 들어온다(아래).

### 측정 (헤드리스 swiftshader 1920×1080, `uidebug=1` 의 `view.drawLog` — 그리는 JS 시간 ms. 같은 기계·같은 순서, `scratchpad/u62d/fin_*.txt`)
| 화면 | 전 (Text×13) | 후 처음 | 후 다시 |
|---|---|---|---|
| 개성 발현 처음 안내 카드 | 98 / 96 | 9 | 10 |
| 개성 발현 카드 3장 | 326~410 | 33 (새로 구움 16·빌림 10) | 10~28 |
| 1차 각성 카드 | — | 55 (21·37) | — |
| 보상(패시브) 목록 | 45~70 | 17 | 2~3 |
| 노드 고르기 지도 | 424~615 | 76 (38·9) | 9 |
| 사연 목록 12줄 (가짜 메뉴, 6번 열기) | 185~5,186 (보통 ~250) | 43 | 5~12 |
그다음 프레임 그리기(GPU 업로드 포함)는 전후 모두 2~11ms. 실제 PC 는 이보다 훨씬 빠르지만 비율은 같다(약 10배·다시 열기 30~50배).

### 원치 않는 선택 막기 (새 `choiceGate.ts` 순수 규칙 + `choiceArm.ts` 그림·Phaser + `inputHeld.ts` 눌린 키 추적)
- **무장**: 메뉴를 실제로 그린 순간부터 armMs(계약 `UiMenu.armMs`·`UiRoute.armMs`, 없으면 400) + 30ms 여유 동안 클릭·숫자·Enter·Space·그만두기 키·Esc 닫기를 받지 않는다. 그린 순간 `uiCommands.menuShown(id | 'route')` 를 불러 시스템 가드도 같은 때부터 센다 (UI 가 30ms 늦게 풀려 시스템이 버리는 선택을 보내지 않는다).
- 입력 시각은 처리 시각이 아니라 **이벤트 시각**(`timeStamp`) — 렉으로 늦게 처리된 키도 눌린 때로 판정. 그리기 전에 눌린 키는 버린다.
- **연타 막기**: 무장 중 고르기 입력이 오면 무장 끝을 `입력 + 220ms` 까지 민다(상한 그린 뒤 1.1초) — 전투하던 손이 두드리는 동안엔 풀리지 않는다.
- **열기 전부터 눌려 있던 키·마우스 왼쪽 버튼**은 한 번 뗀 뒤의 입력만 인정 (브라우저 이벤트로 직접 추적 — Phaser 큐가 밀려도 실제 상태).
- **좌클릭은 같은 카드(줄·버튼) 위에서 눌렀다 뗀 경우만** — 누름도 무장 뒤 새로 누른 것이어야. 끌어서 밖에서 떼면 고르지 않는다. 가운데·오른쪽 버튼은 고르지 않는다.
- 고름 자리 옮기기(←→·A·D·W·S·마우스 올림)는 막지 않는다.
- **보이기**: 카드는 아래 10px 에서 투명 → 제자리로 0.26초에 차례로(0.06초 간격) 들어오고, 테두리를 따라 강조색 2px 선이 왼쪽 위부터 시계 방향으로 차올라 한 바퀴가 닫히면 무장(선은 사라진다). 목록 메뉴·결산은 제목 아래 괘선 위로 선이 왼쪽 → 오른쪽 차오른다. 들어오기는 게임 시간이 아니라 실제 시각이라 렉이어도 무장이 끝날 때쯤 다 들어와 있다.
- **적용**: 성장 카드(개성 발현·1·2차 각성·단련)·처음 안내 카드·보상/패시브/유품 3지선다·패 탁자·수련장 지도/갈래·모든 목록 메뉴(사연·장터·구조물·저주…)·메타 Enter·닫기 버튼·Esc 닫기 (`MenuScene` 이 게이트 하나를 `CardRow`·`SelectList` 에 넘기고, 마지막 안전망으로 `send` 도 무장 전이면 버린다) · 노드 고르기 지도(Enter·Space·클릭 — 갈 길이 하나라 바로 가는 경우 포함) · 결산 버튼·Esc.
- 같은 메뉴를 다시 그리면(상점 갱신) 무장을 다시 하지 않는다. 닫혔다 같은 id 로 다시 열리거나(개성 발현 두 번 연속) 시스템 `openedAt` 이 바뀌면 새로 무장.
- 시스템 E 요청: 문으로 걸어 나가고·문 안·걸어 들어오는 동안(`door.phase` walkOut/inside/walkIn) HUD 키 막대·상호작용 말풍선·새 튜토리얼 안내를 숨긴다.

### 검증
- tsc(src/ui) · eslint(src/ui) · prettier · vitest(src/ui 32 파일 261 — 새 `choiceGate.test.ts` 14: 무장·이벤트 시각·연타 밀기와 상한·눌려 있던 키/버튼·눌렀다 떼기·문 걸음).
- 헤드리스(가짜 3장 카드 메뉴, `scratchpad/u62d/gate.cjs`): 열기 전부터 누른 '1' 고르지 않음 → 떼고 누르면 고름 · Space 연타 중 고르지 않음 → 멈춘 뒤 Enter 고름 · 무장 중 숫자·클릭 무시 → 무장 뒤 고름 · 열기 전부터 누른 마우스를 카드 위에서 떼도 고르지 않음 → 클릭 고름 · 카드에서 눌러 밖에서 떼면 고르지 않음 (10/10).
- 실제 흐름(`real.cjs`): 개성 발현 카드가 뜬 뒤 60~200ms 의 '1' 연타 3번 → 메뉴 그대로, 무장 뒤 '1' → 개성 얻음. Enter 를 누른 채 노드 고르기 지도를 열고 1.2초 뒤 떼도 길을 고르지 않음.
- 스크린샷 `scratchpad/u62d/`: `a_cards_mid.png`(무장 중 테두리 선), `r_2_cards_arming.png`·`r_5_route_held.png`, `new_list_crop.png`/`old_list_crop.png`(글자 전후 같음).

## 62라운드 (2026-10-12) · 루프 2 UI C — 설정·접근성(P1-16) · 일시정지(P2-5) · 로딩(P2-6) · 루프 1 시스템 A 요청 · 보스 '???'(P1-14) · 시련 보상(P2-3) · 용어집(P1-18)
결정: `decisions/2026-10-12-P16-loop2.md` §7·§8, 점검 `review-2026-10-12-stage1-competitive-audit.md`. 계약: §15 + 시스템 D 절(작업 트리 — `keys`·`hitstop`·`textScale`·`setFullscreen`·`abandonRun`·`saveAndQuit`·`ui:loading`·`UiNodeTrial.reward/broken`·`UiBossSnapshot.phaseRevealed`) — UI 는 이 값들을 형식 캐스트로 읽어 계약 코드가 없어도 돈다. 용어집 계약 `contracts/story-glossary.md`.

### 설정 (P1-16 — `SettingsPanel.ts`·새 `SettingsRows.ts`·`settingsView.ts`·`keyBindView.ts`·`uiPrefs.ts`·`fullscreen.ts`)
- 일기장 한 쪽(폭 432) 위 **탭 넷**: 화면(전체화면 F11 · 피해 숫자) / 소리(전체·배경음·효과음 · 소리 끄기 — 일시정지에서 옮김) / 조작(위·아래·왼·오른 · 대쉬 · 상호작용 · 독주 키 + 기본 키로) / 접근성(글자 크기 보통·크게 · 화면 흔들림 · 섬광 · 화면 기울기 · 타격 멈춤). 공통 끝줄 '처음 값으로 되돌린다 · 덮는다'. 탭은 Container → Graphics → 글(버튼 규약), 커서 0번 = 탭 줄(←→ 탭 바꾸기).
- 키 재설정: 키 줄 Enter·클릭 → 쪽 가운데 잉크 상자 '「대쉬」 쓸 키를 누른다 · Esc 그만둔다' → 다음 키의 `KeyboardEvent.code`(한글 입력기 무관) → Phaser 키 이름. 다른 동작이 쓰던 키면 맞바꿈(한 줄 알림), Esc·Tab·M·Enter·F11·Shift·R·C 는 막힘(한 줄 알림). 값은 `settings.keys {up,down,left,right,dash,interact,potion}` 로 `setSettings`. 키를 바꾸면 일시정지 조작 줄이 바뀐 키로 적힌다(`boundControlsLine`).
- 글자 크기: UI 의 **읽는 글**(`GlowText` `readable` — 자막·대사·한마디·이벤트 문장·조사 쪽지·로딩 팁·설정 미리보기)만 크게 = **1.5배**(실제 화면 3px 도트 = 선명). 칸이 정해진 라벨·카드·버튼은 그대로(넘침 방지). 값은 UI 저장소 `lopad.ui.prefs` + 시스템 `textScale`(1 | 1.25 — 시스템 월드 글자용)에 같이 싣는다.
- 전체화면: 시스템 `setFullscreen`(F11 은 시스템이 읽음) → 없거나 거절되면 브라우저 API 직접. 쓸 수 없는 창이면 '이 창에서는 쓸 수 없다'.
- Esc 는 부른 화면(일시정지·타이틀)이 `SettingsPanel.back()` 으로 넘긴다 — 키 기다리는 중이면 그만두기만.

### 일시정지 일기장 (P2-5 — `PauseScene.ts`)
- 항목: [1] 이어서 하기 (Esc) · [2] 싸우는 법 · [3] 설정 · [4] 수련장 · [5] 일기장 덮기('여기까지 적어 두고 타이틀로 — 이어 쓸 수 있다', 확인 없음 → `saveAndQuit`, 없으면 `toTitle`) · [6] 이번 생을 포기한다(확인 '이번 생을 여기서 끝낸다 — 예 / 아니, 더 쓴다' → `abandonRun`; 명령이 없으면 줄을 숨김, uidebug 는 보임). 시험장은 [5] 시험장을 나간다.
- '세이브 남음 n' 삭제(시드만 흐리게), 능력치·감각 줄 삭제(P16 §1·용어집). 조작 목록 대비: 키캡 이름 `page_unsel`(밝게), 조작 줄 흐림 → 본문.

### 로딩 (P2-6 — 새 `LoadingCard.ts`·`loadingView.ts`, `TransitionScene`)
- 지역 키아트 480×270(세피아 액자) · 위 '다음 장을 펼치는 중'(흐림) · 아래 단서 팁 한 줄(읽는 글 배율) · 진행 막대 320×4(1층 강조 22).
- 그림 속 입구 전환이 덮인 뒤 READY 가 0.55초 넘게 늦으면 뜨고(빠른 전환에는 안 보임), READY 에 막대를 채우고 걷힌다. 옛 '…' 붓 점은 카드가 없을 때만.
- 시스템 `ui:loading {phase, progress, done}` 가 오면 그 값(뒤로 가지 않음), 오기 전에는 시간 어림(90% 앞에서 멈춤). 전환 밖에서 진행이 오면 화면을 덮는 카드를 혼자 띄움(`done`·10초 소식 없음이면 걷음). `prefetch` 는 무시.
- 팁: 스토리 63 팩 `loadingTips` 중 requires 없는 14줄(`textR62.ts`), 팩 `hud.loadingTips` 가 오면 그것. 로딩마다 돌아가며.

### 루프 1 시스템 A 요청
- 레인 비우기: 전환 시작(기존) + **노드 진입(ROUTE_NODE_ENTERED)** 때 그 프레임 앞에 들어온 알림·자막·쪽지만 거둔다(`HudAlerts.clearBefore`·`StoryHud.clearBefore` — 같은 프레임에 먼저 온 새 방 층 자막은 남김), 토스트도.
- 새 군주 대사(speech)는 떠 있는·쌓인 앞 대사를 바꾸고 새 줄의 `holdMs` 를 지킨다.
- 보스 이름 카드: BOSS_STARTED `introMs` 로 싸움 시작 시각을 재서 그 무렵 다 걷히게 머묾을 줄임(최소 0.9초, `bossView.nameCardTiming`), 그 전에 보스가 맞으면 바로 접음.
- 확인창(P2-1): 갈 길이 하나뿐이면 묻지 않고 간다. 문구 '이 길로 간다 · 간다 · 아직'(용어집 고침표).
- 엘리트 이름표 여백: 시스템 `screen` = 문장 위 끝(없으면 머리 꼭대기) — `aboveHead` 3 유지(문장이 없을 때도 머리 바로 위). 일반 적 HP 막대는 UI 가 그리지 않음 확인(시스템 `MobReadability` 가 정예 제외로 그림 — 겹침 없음). 완벽 성공 가장자리 섬광(시스템 `screenFx.edge`, 가운데 투명 타원)과 UI '완벽 회피' 문구(화면 가운데 아래, 전투 묶음 위 30px)는 겹치지 않음.

### 그 밖
- P1-14: 국면 띠의 아직 오지 않은 국면 이름은 '???'. 계약 D `phaseNames` 빈 칸('')도 자리를 지킨다(`phaseNamesFor`).
- P2-3: 성과 칩 끝 '→ [전표 아이콘] +25 · 각성 20'(계약 D `UiNodeTrial.reward` 아이콘 — 전표는 아이콘+수치, 나머지는 label). 정보가 없으면 아이콘만, 맞았거나 시간이 지나면(`broken`) 흐리게.
- 메뉴 소리: `uiSound.playUiSound` — 음향 `sfx/ui_move`·`ui_select`·`ui_back`(없으면 조용히). 타이틀 메뉴·일기장 목록(`SelectList` `sounds` 옵션)·설정 쪽에서만(시스템 메뉴는 시스템 오디오).
- 'Enter · 클릭' 표기 통일: 워프·구조물 카드·튜토리얼 닫기·3지선다·조사 쪽지·확인창·설정 안내.
- **용어집(P1-18)**: 고침표의 src/ui 문구 반영 — Q 독주, 본영 → 군주의 방, 상점 → 장터, 이벤트 → 사연, '다음 눈금까지 {n}', 패시브 → 유품, Lv → 단계, 엘리트 길 → 정예 길, 노드 → 곳, 결과 '다시 태어난다', 연회장 설명의 지배자 → 군주. 새 `glossary.test.ts` — `src/ui/*.ts` 문자열 리터럴(TypeScript 구문 트리, 주석·import 제외, 한글 든 것)을 팩 `glossary.bannedWords`·`bannedPatterns.run`·`tone.patterns` 로 검사.

### 검증
- `npx tsc --noEmit` 0 · `npx eslint src/ui` · `npx vitest run src/ui`(31 파일 247) · prettier 통과. 헤드리스 Playwright 1920×1080(작업 트리 `vite build` 스냅숏 미리보기 — 개발 서버는 다른 파트 편집으로 HMR 새로고침이 나서 안 씀, 스크립트·캡처 `scratchpad/u62c/`).

## 62라운드 (2026-10-12) · 루프 1 UI B — 알림 큐 하나(P0-6) · HUD 다이어트(P1-15) · 적 가독성 UI 몫(P1-4) · P2-7·P2-8·P1-10·P1-20·P2-9 · 첫 생 의식 UI(P0-2, 계약 §20) · 타이틀 로고 쓰기·성문(art §30)

### 위 가운데 알림 줄 하나 (P0-6 — `alertPlan.ts` 순수 규칙 + `HudAlerts.ts` 그리기, `alertCards.ts`, `themeAlerts.ts`)
- 동시 2장, 위에서부터 중요도 순(보스 국면·이름 60 > 파훼 50 > 적 소개·주의 40 > 개성 30 > 방 이름 20 > 안내 10). 자리가 없으면 더 중요한 것이 가장 낮은 것을 접고, 아니면 줄을 선다. 줄에서 오래 기다린 낮은 것은 버린다(ttl). 같은 key 는 합친다.
- 합치기: '주의 · 적이 다가온다'(ENEMY_INCOMING) + '문이 닫혔다'(STORY notice, 계약 story-text `notices.trialStart`) → 한 장. 같은 웨이브의 처음 보는 적 여럿 → 한 장. 같은 개성의 옛 진화 배너(WEAPON_EVOLVED) + 개성 칩(TRAIT_GAINED) → 칩 하나.
- 보스: 이름 카드(포효)는 자잘한 알림을 걷고, 국면 카드는 같은 자리 카드를 바꾸며 파훼 카드를 접는다(겹침 없음). 처치 카드·각성 배너는 큰 순간이라 따로 — 뜰 때 줄을 비운다.
- 하데스식 배너: 글 폭에 맞춘 잉크 띠(양 끝 3단 흐림) + 위·아래 1px 강조선. 위 끝은 튜토리얼 단계 카드·도전 판 아래로 비킨다.
- 성과 진행 칩('59초 무피격')은 줄에서 빼 왼쪽 위(층 제목·상태 칩 아래)로. 수련장 과제 알림·빌드 안내도 같은 줄.
- P1-11: 전환 시작(TRANSITION_BEGIN) 때 알림·자막·쪽지·토스트를 비운다. 보스 국면이 바뀌면 지난 대사를 거둔다.

### HUD 다이어트 (P1-15 — `HudDiet.ts`)
- 각성 게이지 줄 → 체력 막대 밑 3px 띠(눈금만, 숫자·'n까지' 문구 없음). 옛 `GrowthGauge`·`GROWTH_HUD` 삭제.
- 보조 자원(기력) 줄 → 무기 줄 오른쪽 작은 원(부채꼴, 바닥이면 테 깜빡임).
- 왼쪽 위 태그 칩('갈 1') → Tab 빌드로(띠에는 저주·[Tab] 빌드만).

### 적 가독성 UI 몫 (P1-4)
- 엘리트 이름표 `aboveHead` 37 → 3 (실기에서 `screen` 이 이미 문장 위 끝이라 몸에서 ~100px 떠 있었다).
- 엘리트 체력 선은 맞았을 때만 2.6초(+0.4초 사라짐), 방금 잃은 부분 흰 꼬리.
- 일반 적 체력 막대·피해 숫자는 월드(시스템) 그림이라 이번 UI 범위 밖 — 시스템 요청으로 넘김.

### 그 밖
- P2-7 개성 카드 태그: 흐린 글 → 잉크 칩(강조 글) + '공명까지 n장'(`growthView.tagNeedAfterPick`).
- P2-8 처음 개성 안내: 빈 마름모 → 이번 메뉴의 개성 카드 그림 3장 + 각성 띠 눈금 도해.
- P1-10: 튜토리얼 단계 카드 20초 상한 삭제(다음 단계·노드 이동까지 유지), `UiSnapshot.keyBar` 이면 아래 4동사 키 막대, BIRTH `firstLife: false` 면 '싸우는 법' 패널 안 띄움.
- P1-20: 첫 생 선택 카드 그림 = `UiMenuLine.doorKey` 입구 그림, 안내 'Enter · 클릭' 통일.
- P2-9: 결과 화면 시드 → '세부 보기 (D)' 접기.

### 첫 생 의식 UI (P0-2, 계약 §20 — 새 씬 `UiRitual`)
- `RitualScene` (Setup 이 `UI_SCENES.RITUAL` 로 띄움, 부팅 때 렌더러 등록) · `RitualName`(name·rewrite) · `RitualStrokes`(+`ritualBrush` 먹 화폭) · `RitualFate`(fate·trial) · `ritualArt`(그림 읽기·안내 줄·붓 이름) · `ritualView`(순수) · `themeRitual`·`textRitual`.
- 이름: art §30 `ritual/diary_first_page` json 자리대로. 숨은 `<input>`(투명, 이름 칸 위 — IME 후보 창 자리)이 한글 조합을 받고, 화면엔 Galmuri 글자 모양을 `ink_brush` tip_d2 스탬프로 찍어 붓글씨로(새 글자는 열 차례로 찍힘). 덧쓰기: 지난 이름 흐리게 + 마른 붓 가로 획 + 그 위 새 이름, [Tab](redraw.key) 획 다시 · [F2](meta.key) 영혼 강화 귀퉁이(단추도 있음).
- 3획: `ritual/back_canvas`(+glow ADD 숨) 화면 가득, 640×360 도트 RenderTexture 에 press/tip/dry/flick/splat 스탬프(긋는 중 #141516, 판정 난 획 #e8b858 + #d67a11 빛무리), strokeClip 밖은 안 찍음. 점은 논리 좌표로 `ritual.stroke`. 오른쪽 종이 = 획 ↔ 무기 규칙(legend), 그 아래 '세 획' 낙관 칸, 3획 끝 큰 낙관. Esc = back.
- 회피 시험: 오른쪽 위 과제 목록(체크·지금 과제 강조·키캡), 과제 이름 카드(누르면 next), Enter 건너뛰기 · Esc 3획부터.
- 운명: `ritual/fate_frame` 9-slice 264 안에 `looks/<무기>_base`(lookKey 없으면 UI 가 읽음), 불씨 테 한 번 밝힘, 아래 무기 이름·첫 한마디·'왜'·시험 결과. Enter = next.
- 키트 동시 읽기 충돌('Texture key already in use') 방지: 다른 씬이 읽는 중이면 끝나길 기다린다.

### 타이틀 (art §30)
- `title_logo_reveal` 마스크로 로고를 획 순서대로 써 내려감(2600ms, 붓 머리 빛 띠, 불씨는 0.96 뒤). 모션 줄이기·파고들기면 바로 끝. `TitleLogoReveal.ts`.
- 파고들기 중심 = title.json `gate`(far 층 기준). 귀퉁이 메타 메모 = `UiSnapshot.meta`.

### 검증
- tsc · eslint(src/ui) · prettier(바뀐 파일) · vitest(src/ui 28 파일 231) 통과. 헤드리스 1920×1080 스크린샷 `scratchpad/u62b/` (r01~r14 의식, h_* HUD·알림, t0* 타이틀, b01 보스).

## 62라운드 (2026-10-12) · 타이틀 화면 전면 재구성 (전권 위임 · 아트 §29 · 경쟁력 점검 T1~T8)
결정: `decisions/2026-10-12-round-62-full-delegation.md`, 점검 `decisions/review-2026-10-12-stage1-competitive-audit.md` ③. 그림·수치 기준 = 아트 `assets/sprites/title/title.json`(+ embers·fog·menu_frame JSON — UI 가 직접 읽고, 없으면 `themeTitle.ts` 기본값). 시스템 코드 열람 없음.
- **층** (`TitleArt.ts`): far → 먼 안개 → 도시 불티 → mid → 들판 안개 → near(주인공 호흡 덧그림·등 발광·무기 목소리 4·불티) → 발목 안개 → 로고. 층마다 Container(가운데 원점, 배율 0.5×1.03) — 패럴랙스 far 0.15·mid 0.4·near 1.0(안개 0.25/0.7/1.0, 도시 불티 0.25), 최대 x28·y10 아트 px, lerp 0.035(프레임 길이 보정), 입력 = 포인터 + 24초 표류(진폭 0.35). 오프셋은 1화면 px 단위.
- **움직임**: 호흡 4.2초(scaleY 1→1.008, 발 기준) + 빛무리 알파 0.55↔1 같은 위상. 무기 목소리 9.6초 한 바퀴 칼→대검→단검→활 2.4초 간격(켜진 1.7초 사인 종, 꺼져도 0.25). 켜진 무기에서 그 색 불티, 로고 불씨 4개도 같은 세기로. 안개 3겹 TileSprite 흐름(−4·9·16 px/s). 달 정지.
- **불티** (`TitleEmbers.ts`): JSON 방출기 4(mound·back_crack·voices·city) — Image 풀, 상한 84(도시 12), 사인 흔들림·0.3초 나타남·1.2초 사라짐·10fps 프레임 루프, 한 프레임 방출 시간 상한 100ms.
- **등장**: 그림·글꼴·붓 마스크를 받는 동안 검은 화면 → 0.15초 뒤 `paint/brush_reveal_2` 먹 붓질 1.4초(480×270 덮개) → 로고 글자 0.85초부터 1.1초 · 부제 1.45초부터 · 무기 불씨 1.9초부터 0.14초 간격 점등 → 1.9초에 (첫 방문) '아무 키나 누른다' / (돌아옴) 메뉴. 아무 키·클릭이면 그 자리에서 끝까지 넘기고 메뉴.
- **'아무 키나 누른다'** (점검 T3): 첫 입력에서 오디오 컨텍스트 resume·사운드 매니저 unlock 후 메뉴. 같은 페이지에서 타이틀로 돌아오면 다시 묻지 않는다.
- **메뉴** (`TitleMenu.ts`): 왼쪽 아래 족자 9-slice(아트 `title_menu_frame`, 여백 48, 0.5배 — 틀 아래 끝 = 아트 영역 아래 끝, 높이는 줄 수에 맞춤). 줄 = Container → Graphics(호박 할로 띠) → GlowText, 글자 Galmuri14. 기본 S5(1px S4) · 선택 #faeec0(할로 #d67a11 α0.5 + 그늘 S2, 오른쪽 3px 비켜 섬) · 비활성 S4. 선택 줄 왼쪽 호박 m 불씨 커서(10fps). ↑↓·W/S·Enter·스페이스·숫자 1~n·마우스 올리기/누르기. 틀 아래 한 줄 = 고른 줄 덧말('일기장을 찢는다') 또는 2.6초 알림(수련장 거부 사유).
- **항목** (점검 T4·T5, 4개 이하): 이어 쓴다(세이브 있을 때만 — 없으면 **숨김**) · 다시 태어난다 · 수련장 · 설정 · 끝내기(Electron·Tauri 에서만). 무기 시험장은 주소 `#lab`·uidebug 일 때만(시스템 `?lab` 주소는 그대로). 괄호 덧말은 안내 줄로.
- **첫 생으로** (점검 T8): 다시 태어난다·이어 쓴다 → 그림 속 성문(아트 px (902,684), 미리보기에서 잼)으로 0.9초 파고들기(가까운 층일수록 빨리 커짐, 성문이 화면 가운데로) + 가장자리부터 먹(붓 마스크 거꾸로) + 성문 빛 번짐 → 다 덮이면 시스템 명령. 시스템 전환 흐름(`ui:transition-begin`)은 시스템이 시작하는 것이라 타이틀이 같은 문법으로 스스로 그린다. 수련장은 기존대로 시스템 전환.
- **영혼 메뉴 건너뛰기** (점검 ⑦, `MenuScene` + `titleView.metaAutoEnter`): 메뉴 `meta` 에 시작('enter') 말고 고를 줄이 없으면 그리지 않고 40ms 뒤 `select('meta','enter')` — 앞 메뉴(첫 생 선택) 그림은 지운다(고른 키가 이름 칸에 들어가지 않게 한 박자).
- **모션 줄이기**: 설정 '화면 흔들림 0' 또는 브라우저 `prefers-reduced-motion` → 패럴랙스·표류·안개 흐름·붓질·파고들기 끔(등장·떠남은 0.6초 페이드), 호흡·불티·목소리 빛만. 설정을 닫는 순간 다시 읽는다.
- **정리**: 옛 타이틀(일기장 그림·작은 'LOPAD'·조작 줄) 삭제 — `assets/ui/kit/title_diary.{png,json}` 지움, `KIT.titleDiary` 삭제. 조작 줄의 낡은 'Tab 워프'(점검 T6) — `controlsLine` 은 Tab 을 어디서나 'Tab 빌드'로(팩 줄의 'Tab 워프'도 바꿈), `routeMode` 인자 삭제(일시정지만 씀). 버전 'v0.62 데모' 오른쪽 아래(G09). 귀퉁이 메타 메모(T7)는 그릴 준비만(`metaMemo` — 계약에 값이 없어 숨김, 교차 참조 요청).
- **성능**: 타이틀 그림 13장·JSON 4개는 타이틀이 열릴 때만 읽고(지연 로드), 떠날 때 텍스처를 내려놓는다(돌아오면 다시 읽음). JS 매 프레임 비용은 프로파일상 무시할 수준(5초에 수 ms). 헤드리스 swiftshader WebGL 은 화면 가득 층 때문에 3fps(GPU 대체 한계), Canvas 렌더러 40fps — 실기 FPS 미측정.
- 글자 스타일 추가(`theme.ts`): `title_item`·`title_selected`·`title_disabled`·`title_scene`·`title_notice`·`title_version`·`title_prompt`(아트 §29 색 = 팔레트 S·G·1층 램프 안).
- 소유 코드: 신규 `TitleArt.ts`·`TitleEmbers.ts`·`TitleMenu.ts`·`themeTitle.ts`·`titleView.ts`(+테스트 22), 변경 `TitleScene.ts`(전면)·`MenuScene.ts`·`PauseScene.ts`·`text.ts`·`theme.ts`·`kit.ts`.
- 검증: HEAD + UI 변경분 깨끗한 사본에서 tsc 0 · eslint `src/ui src/contract` 0 · vitest `src/ui` 26 파일 213 · prettier(바뀐 파일). 헤드리스 Playwright 1920×1080(`vite preview`, Canvas 렌더러로 단계 캡처 + WebGL 최종 메뉴 1장, 스크립트·캡처 세션 scratchpad `title62/`): 검은 화면 → 붓질 3단 → 로고 → 불씨 → '아무 키' → 메뉴 → ↓ · 마우스 올리기 · 패럴랙스 양끝 · 설정(흔들림 0 → 모션 줄이기 켜짐 → 되돌림) · prefers-reduced-motion 페이드 · 새로 태어나기 파고들기 → 첫 생 선택(첫 생) / 두 번째 생은 영혼 메뉴 건너뛰고 이름 의식. 페이지 오류 0.
- 남은 것: 메타 요약 계약(T7), 메뉴 이동·선택 효과음(T8 — 음향 계약 필요), 로고 붓 획 써지기 애니메이션(T2 — 아트 획 순서 마스크 필요), 메뉴 아이콘(T4).


## 61라운드 (2026-10-06) · 단계 6 — 그림 속 입구 전환 · 수련장 UI · 무기 색 (P14, 계약 §19 · 아트 §28)
결정: `decisions/2026-10-06-P14-tutorial-color-transition.md`(자율 모드). 계약: `contracts/ui-system-interface.md` §19 + `src/contract/ui.ts`(시스템이 넣은 `UiTransitionBegin`(+`nodeId`)·`TRANSITION_*`·`UiTraining`(+`line`·`mapKey`)·`TRAINING_TASK`·`TRAINING_STAMP`·메뉴 `training`/`trainingChoice`·`startTraining`/`leaveTraining`). 그림은 아트 §28 마지막 줄 규격. 시스템 코드 열람 없음.

### 그림 속 입구 전환 (`TransitionScene.ts` 새 UI 씬 `UiTransition`, 모든 UI 씬 위)
- HUD·타이틀 create 에서 `ensureTransitionScene` 으로 띄워 둔다(`uiScenes` 에도 넣음, 등록이 없으면 직접 add). `ui:transition-begin` 때 맨 위로.
- 시작: 렌더 직후 게임 캔버스를 논리 960×540 캔버스로 캡처(빈 버퍼면 `renderer.snapshot`) → 그림 준비 → 단계 진행. 셰이더 없음(캔버스 처리 + 선형 필터).
- **enterNode·training**: 캡처한 지도 위 고른 노드(방) 자리에서 입구 그림이 작은 액자로 피어남(0.16초) → 입구 사각형으로 지수 줌 파고들기(0.72초, 목표가 제자리에서 화면 가운데로) → 마지막 38% 에 입구 안 어둠(G01 + 가운데 `light` 번짐)이 짙어져 덮임 → `ui:transition-covered` → READY 뒤 먹 붓질(아트 마스크 2 = 가운데에서 바깥)로 0.62초 걷힘 → `ui:transition-end`. 파고들 자리 = UI 가 고를 때 적어 둔 노드·방 화면 좌표(`transitionState`, id 확인) → 시스템 `from` → 화면 가운데.
- **exitRoom**: 방 화면 캡처 → 출구(`from`)에서부터 붓 그림으로 굳음(0.38초: 밝기만 단계 줄임 + 채도 줄임 + 먹 윤곽 + 종이 결 + 가장자리 종이 번짐, 480×270 처리) → 액자(아트 `frame` 9-slice 0.5배, 좁으면 코드 액자)·종이/지도 바탕이 둘러짐(0.2초) → 줌 아웃 0.3배(0.56초) = 덮임 → READY 뒤 바탕이 붓질(마스크 0·1·3 돌려 씀)로 걷히고 액자 그림이 작아지며 사라짐.
- **floor**: 종이 바탕 위 다음 지역 키아트 큰 액자(붓 그림 처리)가 떠오름 → 가운데로 파고듦(키아트 doorRect 는 아직 없음 — 아트 §28) → 같은 걷힘. `doorKey` 가 오면 그 그림.
- 입구 그림: `doorKey` 텍스처(+ 같은 키 JSON `doorRect`·`light`) — 없으면 UI 가 `ui:paint/...` 사본 키로 직접 읽어 보고(최대 0.9초), 그래도 없으면 지역 키아트 + 코드로 그린 입구(아치·성문·문·동굴, 노드 종류별) 대체. 줌 끝 배율 = 1.25 × max(960/w, 540/h). 붓 마스크·액자도 시스템 키가 없으면 UI 사본 키(`paintArt.ts` — 같은 키를 두 곳에서 읽어 생기는 'key already in use' 방지).
- 건너뛰기: 아무 키·클릭(시작 0.16초 뒤부터, `skippable`) — 덮기 전이면 바로 덮고, 덮였고 READY 면 0.14초에 걷음. 설정: 흔들림 배율(입구에 닿을 때 3px×배율), 섬광 끔이면 덮일 때 빛 번쩍임 없음.
- READY 를 2초 넘게 못 받으면 오른쪽 아래 붓 점 '…'(덮개 유지), 10초 안전망 뒤 스스로 걷음(console.warn).
- 노드 지도(`HudRoute.ts` — HudScene 에서 지도 다루기를 떼어 냄)·수련장 지도(MenuScene)는 고른 뒤 입력 없이 남아 있다가 덮이면 치움(전환이 오지 않으면 0.4초/0.3초 뒤). HUD 배너·지역 카드·자막은 전환 중 미루고 끝나면 이어 간다.

### 수련장 UI
- **과제 목록** (`TrainingHud.ts`, 오른쪽 미니맵·지도 안내 아래, 폭 232): '수련장 · 방 이름' + 진행 n/m(도장이면 작은 인주 도장) · 방 안내 한 줄(`line`) · 과제 줄 = 체크 칸 + 키캡(verb → 지금 무기 4동사 키, 없으면 기본 키) + 이름, 끝난 줄은 흐림 + 가운데 줄. 마당(`room` hall)·메뉴·지도 중 숨김.
- `ui:training-task` → 그 줄 흰 반짝 + 위 가운데 칩 '과제 · 이름'(2.2초). `ui:training-stamp` → 가운데 인주 도장 '수련'(2.2배 → 1배, 흔들림 설정) + '방 · 도장' / '여덟 방 모두 도장'.
- **수련장 지도** (`TrainingMap.ts`, 메뉴 `training`): 아트 `map_training`(+ rooms 메타, 방 id 는 index 순서로 대응) 두루마리 864×486 + 양끝 축, 방 자리 = 고리(그림이 있으면) / 작은 액자 입구(코드 두루마리) + 번호 + 이름 + 도장. 1~8·←→·Enter·클릭, Esc·0 = 나가기. 그림이 아직 안 읽혔으면 0.7초 뒤 UI 가 읽어 다시 그림.
- **첫 생 선택** (메뉴 `trainingChoice`): 일기장 한 쪽 위 카드 2장(수련장 = 작은 입구 / 바로 벽 밖으로 = 열린 길).
- 타이틀 '[3] 수련장'(무기 시험장 4·설정 5로 밀림), 일기장 '[5] 수련장'(수련장 안에서는 '수련장을 나간다' → `leaveTraining`, 덮기는 6). `startTraining` 거부(combat·boss·busy)면 사유 한 줄.

### 무기 색 (`themeWeapon.ts`, 아트 §28 색표)
칼 서리 #8fe3ff · 대검 용암 #ff5a2a · 단검 독 #c060ff · 활 비취 #40e0a0(보조는 팔레트 안). 원한의 한마디 세로 줄(+ 칼·대검·활 할로), 개성 카드·알림·성장도 그림 테두리, 성장 카드 키 밑줄·길 점·단련 눈금, Tab 성장도 지나온 길, HUD 각성 게이지 채움·지난 눈금·아이콘, 각성 배너 띠 위아래 1px, 고유 자원 칸(검기 서리·울분 2단 용암·낙인 독·숨 비취). HUD·메뉴 테두리·글자 기본색은 그대로(§17.1). `SwatchRef` 에 `{ hex }` 추가.

### 소유 코드
- 신규: `TransitionScene.ts`, `transitionView.ts`(+테스트 11), `transitionState.ts`, `paintFx.ts`, `paintArt.ts`, `themeTransition.ts`, `HudRoute.ts`, `TrainingHud.ts`, `TrainingMap.ts`, `trainingView.ts`(+테스트 5), `textTraining.ts`, `themeWeapon.ts`.
- 변경: `HudScene.ts`(노드 지도 → RouteControl, 전환·수련장 배선, 835 → 약 790줄), `MenuScene.ts`, `RouteMap.ts`(`nodePos`·`freeze`), `TitleScene.ts`, `PauseScene.ts`, `keys.ts`·`index.ts`, `debug.ts`(`hasTexture`·`tune.transitionSlow`), `theme.ts`·`themeStory.ts`·`themeGrowth.ts`·`StructureHud.ts`·`growthArt.ts`·`GrowthCards.ts`·`GrowthTree.ts`·`GrowthHud.ts`·`GaugeHud.ts`(무기 색), `text.ts`.

### 검증
`npx tsc --noEmit` 0 · `npx eslint src/ui src/contract` · `npx vitest run src/ui`(25 파일 191) · prettier(바뀐 파일) 통과. 헤드리스 Playwright(1920×1080, 작업 트리 빌드 `vite preview`, 스크립트·캡처 `scratchpad/p14/`): 실제 흐름 타이틀 [3] → 수련장 지도(아트 그림·rooms 자리) → '막고 받아치기' → 전환(입구 그림 피어남 → 파고듦 → 덮임 → 붓질 걷힘, 이벤트 begin → covered → ready → end 순서) → 과제 목록·과제 알림 → 가짜 도장 → 일기장 '[5] 수련장을 나간다'. 시험장에서 가짜 exitRoom·enterNode(가짜 노드 지도에서 고른 자리)·floor·건너뛰기(덮기 전 키 → 바로 덮음, READY 뒤 키 → 짧게 걷음), 첫 생 선택 카드, 네 무기 한마디 줄·게이지·Tab 성장도 색. 페이지 오류 0.

### 후속 (시스템 e6789e9 뒤)
- 수련장 안에서는 런 정보(층 제목·시련·미니맵·'M 지도'·'Tab 워프')를 숨기고 왼쪽 위 '수련장 · 방 · Esc 일기장', 아래 4동사 키캡 안내, 과제 목록은 오른쪽 맨 위(12). Tab = 빌드 보기, M = 무시. 일기장 첫 줄 '이름 · 수련장 · 방', 세이브·시드 줄 숨김. 과제 목록 머리는 방 이름만.
- 계약 §19 확정분 점검: `trainingChoice` 키 '1'/'2'(옛 'training'/'run' 도 읽음), `training` 취소 '0'(cancelKey 가 없어도 '0' 줄을 나가기로), `nodeId`·`line`·`mapKey`·`TRAINING_STAMP`·`startTraining` 결과 4종·`leaveTraining`·수련장 lab=false — 맞음.
- 헤드리스(실제 빌드): 수련장 방이 보이고 과제 목록·도장·일기장 '[5] 수련장을 나간다' → 타이틀. 실제 런의 enterNode·exitRoom 은 첫 생 → 이름 → 개성 획 → 탄생 시련 5과제(피하기)를 헤드리스로 통과하지 못해 못 찍었다(가짜 이벤트 확인만).

### 남은 것 / 확인 요청
- (해결 — 시스템 Training 씬 카메라) 헤드리스에서 수련장 방·마당의 게임 화면이 검게 나온다(HUD 는 정상, 시험장 방은 정상) — 시스템 쪽 조명·카메라 확인 필요(UI 전환 씬이 덮는 것이 아님: 전환 끝에 덮개·캡처를 지우고, 시험장에서는 방이 보인다).
- 층 키아트 입구 자리(doorRect)가 생기면 그쪽으로 파고들게 바로 바뀐다(지금은 가운데).
- 전환 단계 길이·붓 그림 처리 세기·과제 목록 자리는 임시값(`themeTransition.ts`).

## 61라운드 (2026-10-06) · 단계 5 — 개성 그림 · 공명 표시 · 1층 꺼진 태그 (P13, 계약 §18.1)
결정: `decisions/2026-10-06-P13-combat-variety.md`(자율 모드). 계약: `contracts/ui-system-interface.md` §18.1 + `src/contract/ui.ts`(`UiGrowthTrait.iconKey`·`UiResonance.iconKey`·`UiGrowth.resonance`·`UiMenuLine.trait/resonance`·`UI_EVENTS.RESONANCE`). 그림은 아트 65장(`ui_traits/<무기>_<개성>`·`ui_traits/res_<무기>_<태그>`, 시스템 로드). 시스템 코드 열람 없음.
- **개성 카드 그림**: 개성 카드 위 = 그림 64(128 도트 → 0.5배) · G01 바탕 · 무기 빛 테두리 2px(원한의 한마디 세로 줄 색 `VOICE_LOOK.bar` — 칼 G13·대검 21·단검 G10·활 S5) · G00 한 줄, 그 아래 [키] '{동작} 바뀜'. 그림이 없거나 텍스처가 없으면 예전 큰 키캡. 테두리 무기는 그림 키의 무기 → 스냅샷 무기 이름.
- **공명 힌트**(`line.resonance`): 카드 안 옅은 띠 — [◆◆] '이 카드로 「이름」 공명' / '돌파 짝 카드'(태그 줄 대신, 조인 단계에서도 남김).
- **알림**: 개성 알림 = 그림이 있으면 [그림 64] + '개성 발현 · 이름' / [키] 동작 / 한 문장. 공명 알림(`ui:resonance`) = 같은 틀 — 그림(없으면 ◆◆) · '공명 · 이름' · '돌파 개성 두 장이 엮였다' · 한 문장, 같은 순간 개성 알림이 있으면 그 아래에 붙는다.
- **Tab 성장도**: 얻은 개성 — 그림이 있으면 두 칸 격자(그림 32 · 이름 · [키]), 없으면 키캡 줄. '공명' 칸 — 켜진 것 먼저(그림 32 또는 ◆◆ 채움 · 이름 강조 · '켜짐' · 한 문장), 꺼진 것은 짝 마름모 진행 + '간파 0/2'(얻은 같은 태그 개성 수). 높이가 넘치면 접는다(1 공명 한 문장 → 2 공명 그림 → 3 개성 그림). 일기장 무기 줄 아래 '개성: …(셋까지)' · '공명: 켜진 것'.
- **'1층 꺼진 원격 태그' 원인**: UI 가 스냅샷 `build.tags` 를 그대로 그렸다. 시험장은 노드 지도가 없어(시스템 floor 값 비어 있음) 갈래 선풍의 원격 1점이 꺼진 태그 그대로 내려온다(실제 런은 시스템이 거름). → UI 가 층 표(`LIVE_TAGS_BY_FLOOR`, 키를 `stageIndex` → 층 번호로 바꿈 — stageIndex 는 지역마다 바뀌는 값)로 HUD 칩·Tab·일기장 태그·패시브 태그·세트 토스트를 거른다. 층 = `route.floor`, 지도가 없으면 1층(`buildView.tagFloor`).
- 디버그: `__lopadUi.addTexture(key, canvas)`(임시 그림 확인용).
- 검증: tsc 0 · eslint · vitest `src/ui` 23 파일 175 · prettier(바뀐 파일). 헤드리스 시험장(칼, L → 9 → n 눈금 → 개성·1차 각성 선풍·개성 공명 카드 → Tab · 일기장, 가짜 메뉴·이벤트로 그림 없는 모양) 페이지 오류 0.

## 61라운드 (2026-10-05) · 단계 4 — 무기 성장 UI 실제 빌드 점검 (시스템 G 03f4783 뒤)
작업 트리 실제 빌드 헤드리스(시험장 `?lab&weapon=<무기>` → L → 9 '각성 갈래 · 게이지' → n '다음 눈금까지', 스크립트·캡처 `scratchpad/r61h/`). 시스템이 보내는 메뉴 값은 계약 §18 그대로였다(kind trait/awaken1/awaken2/temper, 2~3장, branch·path·verb·lookKey).
- **원인 1 — 메뉴가 사라짐**: labBranch 를 닫고 같은 순간 evolve 를 열면 메뉴 씬이 닫히는 중이라 시스템이 다시 띄우지 않았다(스냅샷 menu = evolve 인데 씬 없음). → HudScene 메뉴 씬 안전망을 구조물 메뉴에서 **모든 메뉴**로 넓혔다(`ensureMenuScene`, 60ms 뒤 씬이 없고 스냅샷 메뉴 id 가 같으면 UI 가 띄움).
- **원인 2 — 1차 각성이 옛 목록으로**: 실제 길 한 줄이 길어 카드 높이(353)가 페이지 상한(카드 306)을 넘어 목록으로 떨어졌다. → 카드 폭 212 → 256(간격 18), 화면에 들 때까지 조이는 단계(0 그대로 / 1 그림 칸 40·괘선·'2차 각성 길' 머리글 뺌 / 2 길 한 줄·태그 뺌, 그래도 넘치면 목록). 네 무기 1차 각성 모두 1단계(303)로 카드.
- **원인 3 — 처음 안내가 바로 사라짐**: 같은 메뉴가 두 번 그려지며(씬 재시작·재전송) 첫 그리기에서 안내를 '본 것'으로 쳐 두 번째에 카드로 덮었다. → 안내가 떠 있는 동안 같은 메뉴가 오면 안내를 지키고, '본 것'은 닫을 때 기록.
- '1차 각성 카드가 선택 없이 닫힘'은 실제 빌드에서 재현되지 않음(안내 클릭 닫기 → 3초 대기·마우스 이동·→ 키, 메뉴 유지·선택 0).
- 용어: 노드 보상 'personality' 이름 '개성' → '각성 게이지'(글리프 '개' → '각'). `weapon.personality`·`threshold` 는 UI 가 이미 쓰지 않는다.
- 확인: 30 개성 안내 → 카드 → 개성 알림, 90 1차 안내 → 카드(그림 3) → 각성 배너, 150 개성, 220 2차 안내 → 카드 2장(길 그림), HUD 게이지, Tab 성장도(선풍 · 회오리 강조, 얻은 개성 2), 일기장 무기 줄. 페이지 오류 0.

## 61라운드 (2026-10-05) · 단계 4 — 무기 성장 UI (P12, 계약 §18)
결정: `decisions/2026-10-05-P12-weapon-growth.md`(자율 모드 — 세부는 UI 판단). 계약: `contracts/ui-system-interface.md` §18 + 시스템 G 가 작업 트리에 넣은 `UiGrowth*`·`UiSnapshot.growth`·메뉴 줄 `kind`/`branch`/`path`/`verb`·`GROWTH_GAIN`/`AWAKEN`/`TRAIT_GAINED`. 시스템 코드 열람 없음.

### 화면
- **HUD 각성 게이지** (`GrowthHud.GrowthGauge`, 전투 묶음의 무기·자원 줄 아래 한 줄 — 옛 2px 개성 진행선 대체): 아이콘 칸 마름모 · 게이지 숫자 · 막대 120px + 눈금(작은 ◇ = 개성 발현·단련, 큰 ◆ = 1차·2차 각성; 지난 것 채움, 다음 것 밝은 테) · '1차 각성까지 40'(없으면 '모든 눈금'). `ui:growth-gain` → 찬 부분 흰 반짝(0.32초) + 숫자 강조색(0.42초). 마름모는 글꼴 대신 Graphics(Galmuri 에 ◇◆ 가 없을 수 있음).
- **선택 카드** (`GrowthCards.ts`, `evolve` 메뉴의 줄이 모두 성장 칸이고 2~3장일 때):
  - 개성 발현: 바뀌는 키 그림 2배 + 강조 밑줄 + 그 칸의 지금 동작 이름(스냅샷 4동사) · 이름 2배 · 괘선 · 한 문장 · 이 층에서 켜진 태그만(1층 6태그 표 `LIVE_TAGS_BY_STAGE`).
  - 1차 각성: 무기 1차 모양 그림(`branch.lookKey`, 없으면 무기 이름 글자) · 이름 2배 · [키] '{동작} 바뀜' · 한 줄 양상 · '2차 각성 길' 두 줄(이름 · 한 줄).
  - 2차 각성(2장, 카드 252px): 길 그림(`path.lookKey`, 없으면 내 갈래 그림) · 이름 · (길이 바꾸는 칸이 있으면 키) · 한 줄.
  - 단련 눈금 메뉴 [단련 / 개성 / 개성]: 단련 카드는 이름 · 설명 · 단련 눈금 마름모(n/최대, 숫자 없음).
  - 고르기·들림·흔들림은 3지선다 카드와 같은 껍데기(`cardShell.ts` — 60 Q38 카드에서 떼어 내 두 화면이 같이 쓴다), 페이지 틀도 `cardPage` 하나.
- **처음 안내 카드** (`growth.firstTime.trait/awaken1/awaken2` 가 true 인 메뉴 앞에 한 장): 어둠 + 종이 · 제목 · 그림(1차 = 무기 기본 모양, 2차 = 내 갈래 모양, 없으면 큰 마름모) · 두 줄 · 'Enter · 클릭 — 고르러 간다'. 닫으면 카드가 그려진다(같은 실행에서 같은 종류는 한 번). 본 기록은 시스템 메타.
- **각성 배너** (`ui:awaken`): 어둠 띠 + '1차 각성'(흐림) · 모양 그림 · 이름 2배(강조) · 한 줄, 위 118, 2.5초. **개성 알림** (`ui:trait-gained`): 위 가운데 잉크 칩 — 키 그림 · '개성 발현 · 이름' · 한 문장, 2.7초.
- **Tab 성장도** (`GrowthTree.ts`, 빌드 보기 왼쪽 장 — 폭 236 → 288): '성장도' · '각성 게이지 n · 다음 눈금까지' · 나무(기본 → 갈래 3 → 길 6; 지나온 길 강조 2px · 다음에 고를 것 또렷 · 닫힌 것 흐림) · '얻은 개성'(키 그림 + 이름, 6줄 넘으면 '외 n'). 제목은 '무기 · 갈래 · 길'. 나무가 길어 전투 묶음에 닿으면 조작 키캡 칸을 뺀다(화면 아래 키캡 띠에 같은 안내). 옛 '개성 n/m' 막대 삭제.
- **겹치는 말 정리**: 일기장 무기 줄 '(개성 n/max)' → '무기: 이름 · 갈래 · 길 (각성 게이지 n)', 결과 화면 '영혼 → 개성 선택' → '영혼 → 유산', 성과 보상 '+n 개성' → '+n 각성', 3지선다 머리표 '개성' → '개성 발현'. 이중 개성 표시(일기장 빌드 쪽·배너·DUAL_TRAIT_GAINED 구독) 삭제(61 G 폐지).

### 소유 코드
- 신규: `growthView.ts`(순수 — 게이지 눈금 자리·남은 수, 키 칸, 켜진 태그, 카드 데이터, 안내 종류, 나무 상태·자리, 이벤트 읽기 + 테스트 15), `GrowthHud.ts`, `GrowthCards.ts`, `GrowthTree.ts`, `growthArt.ts`(마름모·모양 그림·키 배율), `cardShell.ts`, `textGrowth.ts`(`growthText`), `themeGrowth.ts`.
- 변경: `CombatHud.ts`·`combatView.ts`(각성 게이지 줄, 개성 진행선·`personalityRatio` 삭제), `MenuChoiceCards.ts`(cardShell·cardPage 로 줄임), `MenuScene.ts`, `HudScene.ts`(GrowthLayer), `BuildPeek.ts`, `PauseScene.ts`, `ResultScene.ts`, `buildView.ts`·`BuildLayer.ts`·`textBuild.ts`(이중 개성 삭제·성장 칸 이름).

### 검증
`npx tsc --noEmit` UI 오류 0(남은 104건은 시스템 G 진행 중 파일), `npx eslint src/ui`·`npx vitest run src/ui`(23 파일 170개)·prettier 통과. 헤드리스(HEAD 시스템 + 작업 트리 UI·계약 사본, `?debug=1&uidebug=1&lab&weapon=katana`, 가짜 growth·메뉴·이벤트, 스크립트·캡처 `scratchpad/r61g/`): HUD 게이지(0·1·2단계, 반짝), Tab 성장도(1·2단계), 개성 안내 → 카드, 1차 각성 안내(클릭) → 카드 · → 이동, 2차 각성 2장, 단련 메뉴, 각성 배너, 개성 알림. 페이지 오류 0. 실제 런 연결은 시스템 G 완료 후.

### 남은 것
- 안내 카드 '일기장에 다시 보기'(P12 문서) — 일기장 쪽 자리·조작은 다음에.
- 시스템이 각성 때 옛 `WEAPON_EVOLVED` 도 보내면 배너가 둘(각성 배너 + 진화 이름) — 보내지 않으면 문제 없음.
- 색에 안 쓰는 `stageIndex` 배선 정리(약 40 파일)는 이번에도 못 했다.

## 61라운드 (2026-10-05) · 단계 4 — UI 색 고정 · 보스 이름 카드를 포효에 (계약 §17.1)
결정: `decisions/2026-10-05-round-61-autonomous-stage1.md`(자율 모드), 도영 님 데모 피드백 '체력·인터페이스 색이 지역마다 바뀐다'. 계약: `contracts/ui-system-interface.md` §17.1. 시스템 코드 열람 없음.

### 화면
- **UI 색 고정**: 원인 = 강조 램프 슬롯(16~27)을 스냅샷 `stageIndex` 로 팔레트 `floors[i]` 에서 골랐다(글자 할로·강조 글·테두리·커서·노드 아이콘·게이지 띠 전부). `kit.accentHex` 가 이제 층과 무관하게 **기본 램프 하나**(팔레트 1층 '잔', 폴백 `FLOOR1_RAMP`)만 돌려준다 — `stageIndex` 인자는 옛 호출 모양으로만 남고 색에 쓰지 않는다. 노드 아이콘 층 사본(`nodeIconKey`) 삭제, `Gauge.setStage` 삭제.
- **체력 막대는 늘 붉은색** (`themeR61.HEALTH_BAR`, 팔레트 '적' 램프 값만 — 새 색 없음): 플레이어·보스 막대 = 새 게이지 종류 `health`(보스 틀 14px) — 잃은 부분(어두운 적, 슬롯 19) 위에 **피격 잔상**(밝은 적, 26)과 채움(적, 23). 잔상은 맞은 뒤 0.45초 머물고 0.4초 동안 줄어든다, 줄어드는 중 또 맞으면 보이는 자리에서 다시 머문다, 회복은 바로 따라간다(`combatView.hpTrailStep` + 테스트). 엘리트 이름표 2px 체력 선도 적/어두운 적.
- **보스 이름 카드 = 포효 순간**: `UI_EVENTS.BOSS_ROAR`(`{ name }`) 에 이름 카드. `BOSS_STARTED` 는 지난 카드만 치우고 카드를 띄우지 않는다. 국면 띠의 '지금' 은 페이로드 `phase` 가 없으면 스냅샷 `boss.phase`.

### 소유 코드
- 변경: `kit.ts`(accentHex 고정 · Gauge `health` 종류/잔상 · nodeIconKey 삭제), `combatView.ts`(+`hpTrailStep`), `themeR61.ts`(+`HEALTH_BAR`), `CombatHud.ts`·`BossHud.ts`(health 게이지, setStage 제거 · `started`/`roared`), `HudNarrative.ts`(BOSS_ROAR 구독), `EliteHud.ts`·`themeBuild.ts`(hpSlot 제거), `RouteMap.ts`·`RouteSide.ts`(노드 아이콘 원본 키), `theme.ts`(주석).
- 남은 정리(다음 기회): 색에 더는 안 쓰는 `stageIndex` 배선(GlowText·각 HUD 의 `setStageIndex`, 약 40 파일)은 무기 성장 화면 재설계와 겹쳐 이번엔 두었다. 보스 국면 이름·어둠 국면 표(`themeStory *_BY_FLOOR`)는 색이 아니라 그대로 `stageIndex` 로 찾는다.

### 검증
`npx tsc --noEmit` — UI 오류는 `HudNarrative.ts` 의 `UI_EVENTS.BOSS_ROAR` 1건뿐(시스템이 계약 코드에 상수를 넣으면 사라짐; 상수를 넣은 사본 트리에서는 0). `npx eslint .` 통과, `npx vitest run` 848/849(실패 1 = `src/systems/audio/audioDefs.test.ts`, 시스템·음향 몫), prettier 통과. 헤드리스 Playwright(1920×1080, 사본 트리 + 계약 상수, `?debug=1&uidebug=1&lab&weapon=katana`, 스크립트·캡처 `scratchpad/r61s4/`): 다섯 지역(황무지·외곽 거리·성문·양조 구역·연회장)에 `stageIndex` 를 0~4 로 일부러 바꿔도 HUD 묶음·메뉴 패널·오른쪽 위 띠 픽셀이 모두 같음(차이 0), 보스방(stageIndex 5)도 같은 색. 전/후 비교 `compare_before_after.png`. BOSS_STARTED 뒤 카드 없음 → BOSS_ROAR 에 이름 카드. 페이지 오류 0. (잔상 캡처는 헤드리스 스크린샷이 1초 넘게 걸려 사본에서만 머묾을 6초로 늘려 찍었다.)

## 61라운드 (2026-10-05) · 단계 2·3 — 서사 표시(P8) · 보스 UI(P10) · 노드 지도 늦은 그림 버그 · 신규 적 소개
결정: `decisions/2026-10-05-round-61-autonomous-stage1.md` P6·P8·P10(자율 모드 — 세부는 UI 판단, 이유를 아래에 적는다). 계약: `contracts/ui-system-interface.md` §1(`BOSS_STARTED`·`BOSS_PHASE`·`BOSS_DIED`·`STORY`) + 시스템이 작업 트리에 넣은 `UiStoryLine.kind` 4종(`voice`·`speech`·`clue`·`event`)·`speaker`·`weapon`·`lines`·`holdMs`, `UiResult.smudgeLine`(계약 문서 갱신 대상). 문장 톤: `parts/story/text-pack-61-stage1.md`(읽기 — 서사 문장은 시스템이 STORY 로 내려주고 UI 는 틀 낱말만). 시스템 코드 열람 없음(`src/contract/ui.ts` 읽기만).

### 화면
- **STORY 자막 차례** (`StoryHud.ts`, HudScene 자막을 옮김): 텍스트 팩 B1 '겹치면 큐에 넣어 뒤에' — 한 번에 한 줄, 쌓아 두는 상한 6(넘치면 오래된 기존 자막부터 버림). 글꼴 전·탄생 연출 중에는 쌓아 두었다가 그 뒤에(예전: 마지막 한 줄만). 공지(notice)는 차례를 앞지르고 떠 있던 서사 줄은 맨 앞으로 되돌아가 다시 뜬다. 머묾 = 시스템 `holdMs` 가 있으면 그것, 없으면 종류별 길이 비례(`storyHoldMs`).
  - **원한의 한마디** (`voice`): 전투 묶음 바로 위, 무기 줄 왼쪽에서 시작하는 한 줄 — 무기 빛 세로 줄 2px + 따옴표 글. 화자 이름 없음. 무기마다(`weapon` id, 없으면 스냅샷 무기 이름):
    - 칼 = 서늘한 회백(G13 + 무채 할로) · 왼쪽에서 한 번에 베어 들어옴 · 떨림 없음
    - 대검 = 잉걸 주황(강조 21 + 강조 18 할로) · 위에서 내려앉음 · 처음 0.6초 세로로 묵직하게 흔들림
    - 단검 = 흐린 회색(G10, 할로 없음 — 속삭임) · 한 글자씩 · 내내 가로로 잘게 떨림
    - 활 = 세피아 S5 · 낱말 하나씩(센다) · 떨림 없음
    - 머묾 2.0~3.2초(위기 장면 1.5초 — 시스템 `holdMs`).
  - **군주 대사** (`speech`): 하단 가운데 대사(ink_body) + 왼쪽 위 화자 이름표(잉크 패널 + 강조색 '만취'). 시스템 주석의 '만취: …' 한 줄 대신 이름표로 나눴다(대사가 두 줄로 접혀도 화자가 한 번만 보이게). 2.4~4.6초.
  - **이벤트 문장** (`event`): 하단 가운데 종이 띠(page_body, 지문체 — 일기장 기록처럼). 메뉴가 떠 있으면 닫힌 뒤에(텍스트 팩 §0.1). 3~6초.
  - **조사 기록** (`clue`): 가운데 위 일기장 쪽지(종이 380 폭) — 제목 '조사 기록' · 괘선 · 줄이 0.52초마다 하나씩 적힘 · 다 적히면 'Enter · Esc 덮는다'. **Enter·Esc·누르기로 덮는다**(E 는 시스템 상호작용 키라 쓰지 않음). 게임은 멈추지 않는다(줄이 시간차로 와도 막히지 않게 — 조사는 비전투에서만). 같은 단서 줄이 1.5초 안에 따로 오면 같은 쪽지에 잇는다. 전투 시작·메뉴·런 끝·층 전환·30초에 저절로 덮임.
  - 기존 자막(층·보스·휴식·개성 변화·사망)·공지는 예전 모양·시간 그대로.
- **신규 적 첫 등장 소개** (`StoryHud.enemyIntro`): 화면 위쪽(y 58 — 성과 칩 34·도장 카드 92 사이) '처음 보는 적' + 양옆 괘선 이름(강조) + 설명 한 줄(있으면). 2.2초, 이어서 오면 차례로(상한 3).
- **보스 UI** (`BossHud.ts` — CombatHud 에서 보스 막대를 옮겨 한 곳에):
  - 보스 막대: 아래 가운데 그대로. 이름 줄 '만취 · 얼큰'(국면 이름 — 예전 '페이즈 n'), **국면 눈금**(1층 65%·30% — 막대 위로 3px 튀어나온 1px 선, 아직 = 강조 22, 지남 = G06), 무너진 동안 이름 줄 오른쪽 '무너짐' 깜빡임(받는 피해 증가 — P6).
  - 이름 카드(`BOSS_STARTED`): 층 제목(흐림) · 보스 이름 2배(강조) · 괘선 · 국면 띠 '얼큰 → 만취 → 인사불성'(지금 = 강조, 지남 = 흐림, 화살은 픽셀 — Galmuri 에 '→' 가 없다). 뒤에 어둠 띠(G00 α0.5). 2.6초, 위 96(주인공 머리 줄 위).
  - 국면 카드(`BOSS_PHASE` 2·3): 'n국면' · 국면 이름 2배 · 국면 띠 · (3국면 '인사불성'이면) '어둠 — 쓰러진 촛대를 [E] 로 다시 켠다'. 2.05초.
  - 파훼·결정타 문구(`BOSS_BREAK`): 위 84에 '파훼' 2배 + 파훼 이름(잔 깨기·기둥 충돌·술통 되치기·취권 넘어짐) + '무너진 동안 더 아프다' / '결정타' + '무너진 틈을 끝냈다'. 찍힌 직후 0.24초 좌우 2px 흔들림. 시스템이 `label`·`text` 를 주면 그 문장.
  - 촛대 안내(어둠 국면 + 스냅샷 `boss.candles`): 화면 안 꺼진 촛대 위 까딱이는 세모 표지(강조 22 + 불씨 점), 화면 밖이면 가장자리(여백 22)에서 그쪽을 가리키는 세모 화살. 켜진 촛대는 빼고 가까운 것부터.
  - **처치 카드**(`BOSS_DIED`): 어둠 띠 + 이름 2배 + 괘선 + '쓰러졌다'(결정타를 보았으면 '결정타로 쓰러졌다'). 2.95초. **보상 메뉴는 이 카드가 끝날 때까지 기다리고**, 처치 뒤 대사(`speech` defeat)·한마디(`voice` bossKill)가 이어지면 그 줄이 끝날 때까지 늘인다 — 처치에서 최대 4.5초(`uiSequence` 일반화). 시스템이 연출 뒤에 메뉴를 열면 기다림은 0(시스템 이벤트 순서 그대로).
- **노드 지도 늦은 그림 버그** (`displayOrder.ts`·`RouteMap.late`): 원인 = Phaser `moveAbove` 가 '이미 위에 있으면 옮기지 않음' — 새로 만든 그림은 표시 목록 맨 끝이라 그대로 남아 노드·길·글을 덮었다. 늘 '빼고 → 기준 바로 위/아래에 넣기'(`insertNextTo`) + 깊이 정렬 요청. 그림을 1.5초 늦게 준 헤드리스에서 그림 = 바탕 바로 위(index 63 / 바탕 62), 노드·길·이름표가 그 위.
- **결과 화면 이름 번짐** (계약 `UiResult.smudgeLine`, P7): 사망이면 문장 아래 0.9초 뒤 '이름이 번진다.'(흐림)가 나타나고 왼쪽 이름이 흐려지며(α0.55) 오른쪽 아래로 흐린 사본 3장이 겹쳐 번진다(흐림 필터 금지라 겹친 사본).

### 소유 코드 (6-1 정리 먼저)
- **분리**: HudScene 자막(`showCaption`·미뤄 둔 자막·튜토리얼 겹침)을 `StoryHud` 로, 보스 막대를 CombatHud → `BossHud` 로, 서사·보스 이벤트 배선·가운데 아래 자리 계산을 `HudNarrative.ts` 로. HudScene 851 → 843줄(기능 추가 후), CombatHud 304 → 273줄.
- **신규**: `StoryHud.ts`, `BossHud.ts`, `HudNarrative.ts`, `timedCard.ts`(잠깐 떴다 사라지는 카드 공용), `eventsR61.ts`(계약 이벤트 이름 조회 — 없으면 UI 가 기다리는 이름), 순수 계산 `storyView.ts`·`bossView.ts`·`displayOrder.ts`(+테스트 3개), 수치 `themeStory.ts`, 문구 `textStory.ts`(`storyText`), `uiSequence.test.ts`.
- **변경**: `uiSequence.ts`(도장 카드 전용 → 연출 여럿 일반화: `sequenceShown`·`sequenceExtend`·`sequenceGone`·`menuWaitMs`, 도장 카드 API 유지), `theme.ts`(목소리 글자 스타일 4종 `voice_*` — 팔레트 색·허용 알파만), `CombatHud.ts`(보스 막대 뺌, `weaponRowLeft`), `RouteMap.ts`(늦은 그림 끼우기), `MenuScene.ts`(기다림 디버그 기록), `ResultScene.ts`(이름 번짐), `debug.ts`(`emitRaw`·`launch`), `text.ts`(`storyText`), `themeR61.ts`(보스 막대 수치 이동).

### 계약 요청 (시스템 C1·D — 아직 계약 코드에 없음, 오면 그대로 연결)
UI 는 아래가 **있으면 쓰고 없으면 기본값**으로 동작한다(지금은 기본값·가짜 값으로만 확인).
- 이벤트 `UI_EVENTS.BOSS_BREAK`(UI 가 기다리는 값 `'ui:boss-break'`) `{ kind: 'cup'|'pillar'|'cask'|'stumble'|'finisher', label?, text? }` — 파훼·결정타 문구. 계약 키가 생기면 `eventsR61.ts` 가 그 값을 쓴다.
- 이벤트 `UI_EVENTS.ENEMY_INTRO`(`'ui:enemy-intro'`) `{ id?, name, desc? }` — 신규 적 첫 등장.
- 스냅샷 `boss` 선택 필드: `phaseName`·`phaseNames`(없으면 1층 얼큰·만취·인사불성), `phaseMarks`(체력 비율, 없으면 1층 0.65·0.3), `broken: boolean | { leftMs, totalMs }`, `candles: { x, y, lit }[]`(논리 960×540 화면 좌표), `dark`(없으면 1층 3국면부터 어둠). `BOSS_DIED` 의 `finisher?: boolean`.
- `STORY` 선택 필드: `scene`(한마디 장면 키 — 지금은 디버그 기록만), `title`(조사 쪽지 제목, 없으면 '조사 기록').

### 검증
`npx tsc --noEmit`(UI 오류 0 — 작업 트리의 시스템 진행 중 파일 오류 1건 `src/objects/boss/patterns.test.ts` 는 시스템 몫)·`npx eslint src/ui`·`npx vitest run src/ui`(22 파일 155개)·`npx prettier --check src/ui` 통과, `npx vite build` 통과(HEAD 트리 + 작업 트리 `src/ui` + 작업 트리 `src/contract/ui.ts`). 헤드리스 Playwright(1920×1080, `vite preview`, `?debug=1&uidebug=1&lab&weapon=katana`, 스크립트·캡처 `scratchpad/r61s2/`): 한마디 4무기(색·등장·떨림), 차례(한마디 → 보스 자막 → 만취 대사, 공지 끼어들기 후 되돌림), 대사 이름표, 이벤트 문장(메뉴 중 대기 → 닫힌 뒤), 조사 쪽지(한 번에 3줄 · 따로 온 2줄 잇기 · Enter·Esc 덮기 — 일시정지 없음), 신규 적 소개, 보스 이름·2국면·파훼(잔 깨기)·3국면 어둠 + 촛대(화면 안 1 · 밖 2)·결정타·처치 카드 + 같은 틱 보상 메뉴(기다림 3.6초 = 카드 + 대사), 노드 지도 그림 1.5초 지연(그림이 노드 아래), 결과 화면 이름 번짐. 페이지 오류 0.

### 임시값·판단 (도영 님 검토 대상)
- 수치 전부(`themeStory.ts`), 틀 문구 전부(`textStory.ts`), 목소리 색 배정(`theme.ts voice_*`).
- 판단: ① 서사 줄은 한 차례로(한마디·자막·대사가 순서대로 — 보스 앞 '한마디 → 등장 자막 → 대사' 순서 보장), 공지만 앞지름. ② 한마디 자리 = 전투 묶음 바로 위(묶음 오른쪽은 보스 막대 자리라 겹침). ③ 대사 = 이름표 + 하단 자막. ④ 조사 쪽지는 게임을 멈추지 않고 직접 덮는다(시스템이 줄을 시간차로 보내도 막히지 않게). ⑤ 처치 뒤 메뉴 기다림 최대 4.5초. ⑥ 이름·국면 카드 뒤 어둠 띠(전투장 그림 위에서도 읽히게), 파훼 문구는 띠 없음(싸우는 중). ⑦ 촛대 안내는 시스템 좌표가 올 때만(없으면 국면 카드 안내 한 줄만).

---

## 61라운드 (2026-10-05) · P10 단계 1 — 설정 화면(§15) · 전투 HUD 다이어트 · 4동사 키캡 안내 · 플레이 점검 UI 항목
결정: `decisions/2026-10-05-round-61-autonomous-stage1.md` P1·P10(자율 모드 — 세부는 UI 판단, 이유를 아래에 적는다). 계약: `contracts/ui-system-interface.md` **§15**(설정) + 시스템이 작업 트리에 넣은 `UiSettings`·`UI_DEFAULT_SETTINGS`·`uiCommands.setSettings`·`UiSnapshot.settings`, 4동사 `UiWeaponVerbs`·`UiSnapshot.weaponVerbs`(계약 문서 갱신 대상). 플레이 점검 `decisions/review-2026-10-05-stage1-playtest.md` UI 항목(#2·#4·#10·#11·#13). 시스템 코드 열람 없음(`src/contract/ui.ts` 읽기만).

### 화면
- **설정 화면** (`SettingsPanel.ts`, 일기장 한 쪽 400px): 일시정지 일기장 `[4] 설정`(덮기·나가기는 `[5]` 로 밀림)과 타이틀 `[4] 설정` 에서 연다. 화면(화면 흔들림 막대 · 섬광 · 화면 기울기 · 피해 숫자) / 소리(전체 · 배경음 · 효과음 막대) / 처음 값으로 되돌린다 · 덮는다. 막대 = 10칸(10%씩) + 양옆 픽셀 화살표 + '70%'. 켜고 끄기 = '켬 끔' 두 낱말, 고른 쪽 밑줄. 고른 줄은 층 강조 22, 나머지 세피아.
  - 조작: ↑↓(W·S) 고르기 · ←→(A·D) 바꾸기(켜고 끄기는 ← 켬 · → 끔) · Enter·스페이스 켜고 끄기·실행 · 마우스(올리면 고름, 막대 누르고 끌기, 화살표·켬/끔 누르기) · Esc 덮기(한 단계 뒤로 — 일기장/타이틀 목록으로).
  - 값이 바뀌는 즉시 `uiCommands.setSettings`(같은 값이면 보내지 않음). 처음 열 때 값 = 이번 실행에서 보낸 값 → 스냅샷 `settings` → 계약 기본값(일시정지 중 스냅샷이 늦게 바뀌는 문제 방지). 빠른 소리 끄기(§11.3)는 그대로 둔다.
- **전투 HUD 다이어트** (`CombatHud.ts`): 하단 가운데 480 묶음 → **왼쪽 아래 전투 묶음**(데드셀·세피리아처럼 한 구석에). 크게 보이는 것은 넷뿐:
  - 1행 체력: 굵은 막대(보스 틀 14px·200) + 'n / m', 30% 이하면 강조색 깜빡임.
  - 2행 무기 아이콘 + **고유 자원 하나**(라벨 + 눈금 2배 정수 확대). 고유 자원(`gauge`)이 없으면 무기 자원(`resource` 기력·화살·열기 막대). 시스템이 둘 다 보내면(칼·대검 기력) 무기 자원은 작은 보조 줄(그로기 남은 시간선 포함 — 싸움에 바로 걸리는 상태라 감추지 않음).
  - 아래 행: 독주 '2/3' [Q] · 소모품 병 '2/2' [C](키캡) · 전표.
  - 맨 아래 2px 개성 진행선(글 없음).
  - 뺀 것: 무기 이름·갈래·개성 수치·'우클릭 …'(Tab·일기장·키캡 안내로). 아이콘 없는 무기만 이름을 흐리게. 보스 막대는 아래 가운데(묶음과 겹치면 비킴), 이름 · 페이즈만(수치 뺌). 자막·완벽 성공 문구는 `centerBottom`(보스 이름·묶음 위). 층 제목은 흐림(ink_faint).
  - 좌상단 빌드 칩(저주 1 + 태그 4 세로 목록) → **한 줄 띠**: 손실 띠 + '저주 3노드' · 태그 글리프 + 점수(세트 켜지면 강조) · [Tab] 빌드.
- **Tab 빌드 보기** (`BuildPeek.ts`, 노드 지도 층·무기 시험장): Tab 을 누르고 있는 동안 왼쪽 위 종이 두 장(게임은 안 멈춤). 왼쪽 = 무기 · 갈래 / 개성 n/m 막대 / 조작 키캡(2단) / '떼면 닫힌다', 오른쪽 = 일기장과 같은 빌드 글(`buildPage` 제목 없이). 전투 묶음 위에서 끝난다. 다른 화면이 뜨거나 창이 포커스를 잃으면 닫힘. 노드 지도 층의 Tab 은 더 이상 지도가 아님(M 만 지도) — 그 밖의 층(워프 층)은 Tab = 워프 지도 그대로. 조작 안내 줄에 'Tab 빌드'.
- **키캡 안내** (`keyGuide.ts` `keyGlyph`·`KeyHint`·`KeyGuide`, `keyGuideView.ts`): 키 그림(키캡 / 마우스 11×16 — 눌리는 단추 층 강조, 홀드는 아래 길게 누르기 막대) + 동작 이름 한 줄. 가로(`row`)·세로(`column`, `cols` 단). 키 이름 해석: '좌클릭'·'lmb'·'mouse:left' / '우클릭' / '좌클릭 길게'·'lmbHold'·'hold:lmb' / 'Space'·'스페이스' / 한 글자 키. **4동사 연결(`weaponVerbs`)**: 튜토리얼 '싸우는 법' 패널(이동 + 동사 4줄 '이름 — 설명'), 튜토리얼 단계 카드(키 그림 2배 — '좌클릭 길게' 도 마우스 그림), 일시정지 일기장 왼쪽(2단), 무기 시험장 아래 가운데 한 줄, Tab 빌드 보기. 동사가 없으면 예전 조작(좌 공격 · 우 보조 · Space 대쉬).
- **플레이 점검 UI 항목**
  - #2 '싸우는 법' 패널: **런마다 한 번**(노드마다가 아니라 — 첫 전투 노드 '버려진 길'도 여정 노드라 다시 떴다), 떠 있는 동안 **게임을 멈춘다**(`uiCommands.pause()` — 일시정지 일기장은 띄우지 않음, 닫으면 키를 뗀 뒤 `resume`). 저절로 닫히지 않는다. 시스템이 패널 전용 일시정지 명령을 계약에 넣으면 그것으로 바꾼다.
  - #4 내부 표지: 라벨 앞 영문 대괄호(`[common]`·`[epic]`·`[reroll]`…)를 뗀다(`cleanLabel` — 목록·카드). 시스템 키가 'd1'·'reroll'·'m:nextTier'·'give' 처럼 길면 화면 단축키는 쓰지 않은 숫자(그다음 글자, W·A·S·D 제외)를 준다(`menuHotkeys` — 선택은 시스템 키로). 가격은 띄어쓰기만 달라도 다시 붙이지 않는다('40 전표 · 40전표' 제거). 희귀도는 목록 라벨 오른쪽 마름모 4칸(켜짐 층 강조 22, 전설 25)으로 — 카드는 기존 마름모.
  - #10 노드 지도 이름표: 오른쪽 → 왼쪽 → 아래 → 위 → 오른쪽 아래·위 중 다른 아이콘·표지(보상·위험·도장)·주인공 표시·먼저 놓은 이름표와 겹치지 않는 자리(`routeLabels.ts`, 지금·갈 수 있는 곳 먼저). 보상 범례는 한 항목 안에서 줄을 바꾸지 않게(NBSP).
  - #11 성과 도장 카드와 보상 메뉴: 카드가 떠 있을 때 메뉴가 열리면 메뉴가 최대 1.2초 기다리고 카드는 그때 사라진다, 메뉴가 떠 있을 때 등급이 오면 카드는 메뉴가 닫힌 뒤(`uiSequence.ts`).
  - #13 메뉴 설명 대비: 설명 줄 page_faint(α0.55) → page_body, 못 고르는 줄 알파 0.45 → 0.55(허용 알파).
  - #9 피해 숫자 겹침은 시스템 월드 글자라 UI 범위 밖(시스템 몫).

### 소유 코드 (6-1 정리 먼저)
- **분리**: `HudScene.ts` 986 → 851줄 — 하단 묶음·보스 막대·그로기 계산을 `CombatHud.ts` 로.
- **신규**: `CombatHud.ts`, `BuildPeek.ts`, `SettingsPanel.ts`, `settingsStore.ts`, `keyGuide.ts`, `uiSequence.ts`, `themeR61.ts`(수치), `textR61.ts`(문구), 순수 계산 `combatView.ts`·`settingsView.ts`·`keyGuideView.ts`·`routeLabels.ts`(+테스트 4개).
- **변경**: `BuildHud.ts`(빌드 띠), `BuildLayer.ts`(Tab 안내·도장 대기열), `CarryHud.ts`·`ConsumableHud.ts`(왼쪽 기준·키캡), `GaugeHud.ts`(`gaugeLabelText`), `ResourceHud.ts`(`right`·`moveToY`), `keycap.ts`(`setMinWidth`), `PauseBuild.ts`(`objects`·제목 생략), `PauseScene.ts`·`TitleScene.ts`(설정·키캡 안내), `TutorialHud.ts`·`tutorialView.ts`(런마다 한 번·일시정지·4동사), `menuView.ts`·`widgets.ts`·`choiceCardView.ts`·`MenuChoiceCards.ts`·`MenuCards.ts`(표지·단축키·희귀도·대비), `MenuScene.ts`·`TrialHud.ts`(차례), `RouteMap.ts`(이름표 자리), `bundleView.ts`(범례), `text.ts`(`r61Text`, 'Tab 빌드', F 넣기/뽑기 안내 삭제), `theme.ts`(비활성 알파), `debug.ts`(`setSettingsCmd`·`settings` 기록), `buildView.ts`(쓰지 않는 `stagePips` 삭제).
- **버그**: Phaser `Transform.setPosition(x, y)` 가 게임 오브젝트의 `w`(4번째 좌표)를 0 으로 되돌린다 — Container 하위 클래스의 폭 필드 `w` 를 `boxW` 로 바꿨다(소모품 칸·고유 자원 눈금·넣기/뽑기 칩·키캡 안내). 새 Container 에 `w`/`z` 이름을 쓰지 말 것.

### 검증
`npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(103 파일 764개, UI 21 파일 128개)·`npx vite build` 작업 트리 통과. 헤드리스 Playwright(1920×1080, `vite preview`, `?debug=1&uidebug=1&lab&weapon=<무기>`, 스크립트·캡처 `scratchpad/r61ui/`): 칼·대검·단검·활 실제 스냅샷(4동사·자원 하나), 가짜 빌드·보스·저체력·그로기, Tab 누름/뗌, 설정(키보드 ←←·↓→·↓Enter, 마우스 클릭·끌기·켬/끔 → `setSettings` 기록과 스냅샷 `settings` 0.8 왕복 확인, Esc 로 일기장 → 게임, 다시 열면 값 유지), 타이틀 설정, 가짜 상점·패시브 카드·이벤트(표지 제거·단축키 '3' 비활성 무시·'2' 선택), 도장 → 메뉴 차례, 노드 지도 이름표, 튜토리얼 패널(PAUSED 뒤 일기장 없음, Enter → RESUMED, 같은 런 다른 여정 노드에서 다시 안 뜸), 단계 카드 '좌클릭 길게'. 페이지 오류 0.

### 임시값·판단 (도영 님 검토 대상)
- 수치 전부(`themeR61.ts`), 문구 전부(`textR61.ts`).
- 판단: ① 전투 묶음을 왼쪽 아래로 옮김(가운데 아래는 보스 막대·자막·시험장 안내 자리). ② 자원은 고유 자원 우선, 둘 다 오면 무기 자원은 보조 줄 — 시스템이 하나로 줄이면 자동으로 한 줄. ③ Tab = 누르고 있는 동안 빌드 보기(노드 지도 층·시험장), M = 지도. ④ 설정 막대 10% 칸, 켜고 끄기 ← 켬 · → 끔, 바깥 누르기로는 안 닫힘(끌다 놓쳐도 그대로). ⑤ '싸우는 법' 패널은 일시정지 + 저절로 안 닫힘. ⑥ 도장 카드가 있을 때 메뉴 대기 최대 1.2초. ⑦ 긴 시스템 키의 화면 단축키는 빈 숫자부터.
- 관찰(이번 범위 밖): 노드 지도를 지도 그림이 읽히기 전에 열면 늦게 온 그림이 노드·길을 덮는다(헤드리스, HEAD 에서도 같음). 노드 지도 층에 들어갈 때 HUD 가 그림을 미리 읽으므로 실제 플레이에서는 드물다 — 다음 작업에서 `late` 끼우기 순서를 고친다. → **61 단계 2에서 고침**(`displayOrder.ts`, 원인 = `moveAbove` 가 이미 위에 있으면 옮기지 않음).

---

## 60라운드 후속 (2026-10-05) · Q36~Q39 — 3지선다 카드 3장 · 이름표 새 바탕(글자 칸 24도트) · 완벽 문구 확인
결정: `decisions/2026-10-05-round-60-parallel-production.md` Q36(이름표 글자 칸 확대 — 아트 1103aba 반영)·Q37(완벽 성공 HUD 문구 회피·놓기만)·Q38(개성 3지선다 카드 3장)·Q39(UI 세부 유지, `screen` = 머리 꼭대기). 계약 §14.4·§14.9, 교차 참조 #24. 시스템 코드 열람 없음.

### 화면
- **3지선다 카드 3장** (`MenuChoiceCards.ts`): `evolve`·`reward`·`passive` 메뉴에서 그만두기를 뺀 칸이 **정확히 3**이면 카드(그 밖 칸 수·다른 메뉴는 목록 그대로, 화면을 넘으면 목록으로 물러남). 일기장 한 페이지(제목·괘선·footer) 위에 잉크 탁자 깔개(`panel_ink`) + 종이 카드(`panel_paper` + `paper_tile`) 3장(212×208 이상, 간격 22, 그림자 S0 α0.55).
  - 카드: 위 가운데 머리표 탭(잉크 + 종류 띠 — 갈래 21·강화 22·피의 계약 19·각성 25·이중 개성 23·패시브 22·저주 19, `kind` 가 없으면 메뉴 이름 '개성'·'보상'·'패시브') · 왼쪽 위 `[1]` · 이름(2배) · 희귀도 마름모 4칸(전설은 슬롯 25) · '희귀도 · 태그' · 괘선 · 설명 · 아래 '잠김 — 조건'(자물쇠) 또는 '(불가)'·'(팔림)'. 이름·괘선·설명 줄은 세 장이 같은 높이.
  - 고름 자리: 카드가 6px 들리고 그림자 3→7px, 층 강조 20 테 2px, 이름 `page_selected`. 못 고르는 카드는 흐림(테는 또렷), 고르면 좌우 2px 흔들림.
  - 조작: 1·2·3 / ←→(A·D) / Enter·스페이스 / 마우스(올리면 고름 자리, 누르면 선택). 그만두기 줄이 있으면 카드 아래 `[0] …` + ↓·0·Esc·'Esc 닫기' 버튼, 없으면 Esc 머무름 안내(기존). 아래 안내 '1·2·3 또는 ←→ 고르기 · Enter 고른다( · 0·Esc 그만두기)'.
- **엘리트 이름표 새 바탕** (Q36, 아트 1103aba): `assets/ui/elite/` 사본을 192×40 판(pivot 96,38 · `textArea` 26,7 140×24 · `textCenterY` 19)으로 교체. 코드가 JSON 을 읽는다 — 가로 = `textArea` 가운데(가운데 조각을 늘린 만큼 칸도 넓힘, 칸이 가운데보다 좁으면 그만큼 더 넓힘), 세로 = `textCenterY`(없으면 칸 가운데), 아래 끝 = `pivot.y`. 글자(Galmuri11 1배 12px)가 바느질 테 안 띠에 들어간다. 위치는 `screen`(머리 꼭대기, Q39 확정) 37px 위 그대로.
- **완벽 성공 문구** (Q37): 이미 회피·놓기만(`themeBuild.PERFECT.hudKinds = ['perfectRelease', 'perfectEvade']`) — 변경 없음, 확인만.

### 소유 코드·에셋 (6-1 정리 먼저)
- **분리**: `MenuScene.ts` 434 → 229줄 — 카드 고르기(`CardRow`)·닫기 버튼·패 탁자 화면을 `MenuCards.ts` 로.
- **신규**: `MenuChoiceCards.ts`(카드 3장 화면), `choiceCardView.ts`(+테스트 5개 — 카드 판정·글·안내, 순수 계산).
- **변경**: `menuView.ts`(`splitLabel` 공용), `eliteView.ts`(`textArea` 읽기·`plateTextCenter`, `plateMidW` 글자 칸 반영)·`EliteHud.ts`·`eliteView.test.ts`(새 판 수치), `textBuild.ts`(`choiceHint`·`choiceHintCancel`·`CHOICE_MENU_HEAD`), `themeBuild.ts`(`CHOICE_CARD`, `ELITE_PLATE` 주석).
- **에셋**: `assets/ui/elite/elite_nameplate.png/.json`(새 판 사본) + README.

### 검증
`npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(90 파일 691개)·`npx vite build` 통과. 헤드리스 Playwright(1920×1080, `vite preview`, `?debug=1&uidebug=1&lab&weapon=katana`, 스크립트·캡처 `scratchpad/r60cards/`): 가짜 evolve(강화·피의 계약·잠긴 각성, footer)·reward(패시브 희귀·이중 개성·패시브 전설, '0' 건너뛴다) → 카드 3장·→ 이동·'3'(잠긴 각성은 선택 안 감, reward '3' 은 감)·마우스 클릭(evolve '1'), 엘리트 이름표 2개(새 바탕). 페이지 오류 0.

### 임시값 (도영 님 검토 대상)
- 카드 수치 전부(`themeBuild.CHOICE_CARD`), 종류 띠 색 배정, 안내 문구, `kind` 없을 때 머리표 이름.
- 판단: ① 개성 1·2단 임계의 [갈래 A / 갈래 B / 강화]도 3칸이라 카드로 그린다. ② 카드로 그리는 메뉴 = evolve·reward·passive(저주 2택·이벤트·상점 등은 목록). ③ 탁자 깔개 = 잉크 패널.

---

## 60라운드 (2026-10-05) · 계약 §14 전체 — 빌드 축(태그·세트·이중 개성·저주·3지선다 칸) · 2차 묶음(노드 지도·상점·소모품·엘리트 이름표·성과 등급)
결정: 57라운드 Q38 '모두 진행', 60라운드 Q12(이름표 문장 위 2단)·Q27(소모품 C)·Q32(E 조사 kind). 계약: `contracts/ui-system-interface.md` **§14**(승인 #21) + `src/contract/ui.ts`(시스템 추가분만 import). 아트: `art-assets.md` §22 `fx/v3/elite_nameplate` → `assets/ui/elite/` 사본(수정 금지). 시스템 코드 열람 없음.

### 화면
- **HUD 빌드 칩** (좌상단, 구조물 상태 칩 아래): 저주 칩(손실 띠 슬롯 19 · '저주' · 이름(강조) · '3노드 남음'/'12처치 남음') → 태그 칩 최대 4개(점수 높은 순, 시스템 정렬) = 임시 글리프(이름 첫 글자 상자, 세트가 켜지면 테 강조) · 이름 · '점수 · n단' · 세트 임계 2·4·6 마름모 3칸.
- **완벽 성공 (§14.11)**: 간파 칩이 한 번 깜빡. 하단 묶음 위 가운데 'PERFECT EVADE'·'PERFECT RELEASE'(ink_accent, 0.52초 뒤 떠오르며 사라짐). 패링·퍼펙트 가드는 시스템 월드 문구(§13)가 있어 HUD 문구는 기본 끔(`PERFECT.hudKinds`).
- **소모품 칸 (§14.8)**: 1행 독주 Q 오른쪽 — 병 그림(투척은 불씨 마개) + 'n/m' + 키(`consumable.key`, C). 빈 칸이면 병 윤곽 + '빈 칸'(자리가 모자라면 윤곽 + 키만). 칸이 없는 모드(null)는 숨김.
- **엘리트 이름표 (§14.9)**: `elites[]` 마다 아트 바탕(가로 3조각 캡 26 · 가운데 반복 · 캡 26, scale 0.5 = 도트 밀도 그대로) + 이름(새 글자 스타일 `plate_name` = 슬롯 25 + 그늘 G00) + 아래 체력 선(슬롯 23). 머리 위 점에서 37px 위가 이름표 아래 끝(문장 위 2단). 오버레이 중 숨김, id 로 재사용.
- **성과 진행 칩 (§14.10 `nodeTrial`)**: 상단 가운데(도전 판이 있으면 그 아래) '32초 · 무피격'/'피격' + 시간 선(남은 25% 이하 강조). 시험장에서는 숨김.
- **성과 도장 (`NODE_GRADED`)**: 상단 가운데 종이 쪽지 — 왼쪽 도장 完·良(2배, 바랜 잉크 α0.85, 위에서 6px 내려와 찍힘) / 결과 문구 · '무피격 ○ · 제한 시간 ×' · '+20 전표 +15 개성'. 2.4초.
- **§14.11 알림 → 우하단 토스트**(구조물 결과와 같은 자리): 세트 단계 오름(획득)·내림/꺼짐(손실), 저주 받음(+저주 한 줄)·풀림, 숨은 길 드러남, 소모품 사용('이름 — 남은 n'). 이중 개성 획득은 가운데 배너.
- **메뉴 (§14.4·§14.6·§14.7, `menuView.ts`)**: 칸 종류가 섞인 메뉴(개성 3지선다·이중 개성 칸이 낀 보상)는 라벨 앞 〔갈래 A〕〔강화〕〔피의 계약〕〔각성〕〔이중 개성〕 등, 아래 줄 희귀도·태그, 잠긴 칸은 '잠김 — 조건' + '(잠김)'. 상점은 묶음이 바뀌는 줄 위에 머리글(늘 파는 것·오늘의 진열·진열 바꾸기·덤·지도 정보), 가격(`price.label`)이 라벨에 없으면 덧붙임, 팔린 줄 '(팔림)'. 페이지가 화면을 넘으면 설명을 접고 커서 줄 설명만 목록 아래 한 칸. 새 id `curse`(필수 — Esc 머무름)·`event`('0')·`mapInfo`('0')·`consumableSwap`(필수)은 같은 목록으로, 구조물 메뉴 안전망에도 넣음.
- **노드 지도 (§14.5)**: 보상 미리보기 표(아이콘 오른쪽 아래, 임시 글자 전·패·개·병·점·저·?), 위험 노드 = 바깥 마름모 테(슬롯 21) + 왼쪽 위 표(투·잔), 성과 도장 完·良(아이콘 오른쪽 위), 숨은 노드 `smudge` = 발광 잉크 얼룩(고를 수 없음, 이름 없음, 보기 모드에서 살펴보기만) / `located` = 얼룩 + 점선 고리 + '?'. 오른쪽 칸 '살펴보는 곳' 아래 보상·위험(+위험 한 줄)·접두어·이벤트 내용·도장 줄(범례 위를 넘으면 '…'), 범례 위에 보상 글자 범례·'산 지도 정보 · 다음 단 …'. '넘어가시겠습니까?' 창에 `riskText`(강조). HUD 노드 띠는 숨은 노드를 흐린 점 하나로.
- **E 안내 (§14.10 Q32)**: 말풍선은 시스템 `name`·`action` 그대로, 비었을 때만 종류별 기본 문구(`warFlag` 전장 깃발/깃발을 세운다, `clue` 수상한 자국/살펴본다, `eventProp` 눈길 가는 것/다가간다, `mapSeller` 지도 장수/지도를 본다). kind 를 문자열로 찾으므로 `clue`·`eventProp`·`mapSeller` 가 계약 코드에 생기면 바로 쓰인다.
- **일기장 (Esc)**: 두 쪽 펼침 — 오른쪽 '빌드' 쪽(태그·세트(점수·단계·다음 임계·켜진/꺼진 효과) / 이중 개성(짝 갈래·태그·단, 설명) / 저주(남은 기간·이득·저주) / 패시브(Lv/최대·태그) / 소모품). 넘치면 꺼진 효과·설명 → 효과·저주 줄 순으로 접고, 그래도 넘치면 '…'. 패시브 줄은 왼쪽 쪽에서 옮김.

### 소유 코드·에셋 추가·변경 (6-1 정리 먼저)
- **분리**: `RouteMap.ts` 1045 → 596줄(`routeGlyph.ts` 글리프·마름모·주인공, `RouteConfirm.ts` 확인 창, `RouteSide.ts` 오른쪽 칸, `routeSheet.ts` 양피지·일러스트), `HudScene.ts` 1085 → 986줄(`HudBanners.ts` 배너 차례·지역 카드, `HudBirth.ts` 탄생 연출), `MenuScene` 줄 만들기 → `menuView.ts`, `fill` → `fmt.ts`(순수 모듈이 Phaser 없이 쓰게).
- **신규**: `BuildLayer.ts`(§14 HUD 묶음·이벤트), `BuildHud.ts`(빌드 칩·완벽 성공), `ConsumableHud.ts`, `EliteHud.ts`, `TrialHud.ts`(성과 칩·도장 카드), `PauseBuild.ts`, `routeMarks.ts`, 순수 계산 `buildView.ts`·`bundleView.ts`·`eliteView.ts`·`menuView.ts`(+테스트 4개, 24개), `textBuild.ts`(R60 문구·이름 표, 데이터만), `themeBuild.ts`(§14 수치), `fixtures.ts`(테스트용 노드 — §14.5 필드를 모두 채움).
- **변경**: `widgets.ts`(SelectList 머리글·꼬리 글·커서 알림), `StructureHud.ts`(E 기본 문구, 토스트 tone·text 만), `kit.ts`(이름표 읽기), `theme.ts`(`plate_name`), `text.ts`(`r60Text`), `structView.ts`(`interactWords`), `RouteStrip.ts`, `PauseScene.ts`, 테스트 4개(routeView·regionView·resourceView·tutorialView → `fixtures`).
- **에셋**: `assets/ui/elite/elite_nameplate.png/.json`(+README).

### 검증
`npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(89 파일 682개, UI 13 파일 95개)·`npx vite build` 통과. 계약 코드의 §14.5 선택 필드 8개를 필수로 바꾼 사본(UI + `contract/ui.ts` 만)에서도 tsc 통과. 헤드리스 Playwright(1920×1080, `vite preview`, `?debug=1&uidebug=1&lab&weapon=katana`, 스크립트·캡처 `scratchpad/r60/`): 가짜 build·consumable·elites·nodeTrial·interactable(warFlag) → HUD 칩·이름표·소모품·PERFECT EVADE·세트 토스트, NODE_GRADED·CURSE_GAINED, 메뉴 6종(evolve·shop·curse·event·mapInfo·consumableSwap), Esc 일기장 두 쪽, 가짜 route(보상·위험·도장·smudge·intel) M 지도·고르기·위험 확인 창. 페이지 오류 0(WebGL 드라이버 경고만). 실제 런 탄생 경로는 헤드리스로 들어가지 못해(개성 획 그리기) 타입·논리 동일로만 확인.

### 임시값 (도영 님 검토 대상)
- 문구 전부(`textBuild.ts` R60_TEXT·이름 표), 임시 글자 글리프(보상 7·위험 2·태그 첫 글자·병 그림), 수치 전부(`themeBuild.ts`).
- 판단: ① 이름표 scale 0.5(아트 도트 밀도) — 글자(Galmuri11 1배)가 바탕 글자 칸(8px)보다 커서 테를 조금 덮는다. ② `screen` 을 머리 꼭대기로 읽고 37px 위에 이름표. ③ HUD 완벽 성공 문구는 회피·놓기만. ④ 일기장 두 쪽 펼침(928px)·패시브를 오른쪽으로. ⑤ 숨은 노드 얼룩 = 발광 잉크 얼룩(`stain_blot`, 손때 얼룩은 그림 위에서 안 보였다). ⑥ 성과 칩·이름표는 오버레이 중 숨김, 성과 칩은 시험장에서 숨김. ⑦ 저주 남은 기간은 HUD 칩·일기장에만(노드 띠 표시는 §14.12 범위 밖).

---

## 56라운드 (2026-10-04) · 무기 고유 자원·그로기 HUD
결정: `decisions/2026-10-04-round-56-weapon-feedback.md` Q13~Q20·Q48·Q58. 계약: `contracts/ui-system-interface.md` **§13**(승인 #20) — `UiSnapshot.gauge`(`UiWeaponGauge`)·`groggy`(`UiGroggy`), 칼 `secondaryName` '가드·패링'. 타입은 `src/contract/ui.ts`(시스템 추가분)만 import, UI 쪽 복제 정의 없음. 시스템 코드 열람 없음.

### 화면
- **고유 자원 눈금** (HUD 2행, 무기 이름 바로 오른쪽 10px): 라벨 `gauge.label`(ink_faint, 비면 기본 이름) + 칸. 개성 아이콘·게이지는 그 뒤로 비킨다(최소 px+200 그대로).
  - 검기 `kenki`: 칼날 마름모 7×8 × 3칸(간격 2), 아래에서 위로 차오름. 칸 색 재 G11 → 호박 22 → 백열 27. `stage` = 찬 단 수, 다음 칸은 비율 나머지만큼(시스템 실제 값 max 300).
  - 울분 `grudge`: 이어진 3칸 막대 14×6(간격 1), 왼쪽부터 연속 채움. 색 = 구간(`stage` 1·2·3 → 강조 20·22·25, 없으면 비율 1~33/34~66/67~100%).
  - 낙인 `brand`: 셈 획 2×8 × max(기본 5)칸, 정수 스택만. 최대면 전부 강조 25.
  - 숨 `breath`: 방울 7×7 × max(기본 3)칸, 소수면 부분 채움. 켜짐 G12, `focusing` 이면 강조 25 + '집중'(ink_accent 깜빡임).
  - 꺼진 칸은 G06 테두리 + G03 안쪽(열기 단계 눈금과 같은 문체). 가득이면 라벨 ink_accent.
  - 긴 무기·갈래 이름으로 '우클릭 …' 과 겹치면(간격 8 미만) 눈금 라벨을 빼고, 그래도 겹치면 '우클릭 …' 을 숨긴다(조작 안내·일기장에 같은 글).
- **그로기** (`groggy.active`, 칼·대검): 3행 기력 막대 아래 2px 남은 시간선(G03 바탕 + 강조 22, 오른쪽부터 줄어듦), 상태 글 '지침' 대신 **'그로기 1.2초'**(0.1초 올림, ink_accent 깜빡임), 2행 무기 아이콘·이름·눈금이 1px 떨림(60ms 계단 0·+1·0·−1). 전체 시간은 계약에 없어 이번 그로기에서 본 가장 큰 `leftMs`(없으면 1.5초).
- **가드·패링**: 조작 안내 `{secondary}`·HUD '우클릭 …'·튜토리얼은 `secondaryName` 을 그대로 쓰므로 변경 없이 '우클릭 가드·패링' 으로 보인다(캡처 확인).

### 소유 코드 변경
`GaugeHud.ts`(신규, `WeaponGaugeChip` Container — 하단 묶음과 함께 setY), `gaugeView.ts`·`gaugeView.test.ts`(신규, 순수 계산: 칸 채움·부분 px·테두리·그로기 초·떨림, 테스트 12개), `ResourceHud.ts`(그로기 남은 시간선·상태 글), `HudScene.ts`(2행 배치·겹침 처리·그로기 전체 시간), `theme.ts`(`WGAUGE`·`GROGGY`), `text.ts`(`R56_TEXT`·`r56Text`).

### 검증
`npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(73 파일 557개) 작업 트리 통과. 헤드리스 Playwright(1920×1080, `vite preview`, `?debug=1&uidebug=1&lab&weapon=<무기>`, 스크립트·캡처 `scratchpad/r56/ui/`): 네 무기 실제 스냅샷(시스템이 이미 gauge·groggy 를 채움) + 가짜 값(검기 0·1.5·3단, 울분 20·50·100%, 낙인 2·5, 숨 1.5·3+집중, 그로기 1.5·0.6·1.1초, 긴 갈래 이름 3단계) + Esc 일기장 조작 안내. 그로기 중 무기 줄 프레임 3종(떨림)·평소 1종 확인. 콘솔 오류는 기존 404 1건뿐.

### 임시값 (도영 님 검토 대상)
- 위치: 2행 무기 이름 오른쪽(계약 '무기명 옆'). 그로기는 3행 기력 막대 아래 선 + 상태 글 + 무기 줄 떨림.
- 모양·색: 위 화면 절 그대로(`theme.ts WGAUGE`·`GROGGY`), 깜빡임 0.2초, 떨림 1px·60ms.
- 문구: '그로기 {s}초', '집중', 기본 라벨 '검기'·'울분'·'낙인'·'숨'(시스템 label 우선).
- 판단: 긴 이름일 때 라벨 → '우클릭 …' 순으로 줄임. 검기 `stage` 를 '찬 단 수' 로 읽음(울분은 '구간').

---

## 53라운드 후속 2 (2026-10-03) · 노드 고르기 Esc(Q47) · 적 등장 예고(Q49·Q60) · TUTORIAL_STEP · 시험장 문구
결정: `decisions/2026-10-03-round-53-playtest4.md` Q47·Q49·Q60. 계약: `contracts/ui-system-interface.md` '53라운드 추가'(`ENEMY_INCOMING`·`TUTORIAL_STEP`·`cancelChoose()`), `src/contract/ui.ts`. 시스템 코드 열람 없음.

### 화면
- **노드 고르기 Esc (Q47)**: 고르기 모드 지도에서 Esc → 지도를 닫고 `uiCommands.cancelChoose()` (물러나기는 시스템 몫). 48라운드 '고를 곳이 0개일 때만 닫기'를 대체. 취소 명령은 Esc 를 **뗀 다음 프레임**에 보낸다(재개와 같은 까닭 — 풀린 게임 입력이 누르고 있는 Esc 를 받지 않게, 못 떼도 1초 뒤). 그 사이 안전망('고를 차례인데 지도가 없음')은 1.5초 쉰다. 취소가 먹지 않아 `route.choosing` 이 남으면 안전망이 지도를 다시 연다.
  - '넘어가시겠습니까?' 확인 창이 떠 있으면 Esc 는 확인 창의 '아니오'만 (HUD 가 같은 이벤트를 `takeKey` 로 소비 — 확인 창이 닫힌 뒤 다시 넘어온 같은 Esc 가 고르기까지 취소하지 않게).
  - 고르기 안내 문구에 '· Esc 물러나기'.
- **적 등장 예고 (Q49·Q60)**: '주의 / 적이 다가온다' 경고를 `inCombat` 전환이 아니라 `ENEMY_INCOMING` 의 `delayMs > 0` 일 때 띄운다(일반 전투는 delayMs 0 — 튜토리얼 판별은 시스템 몫). 머무는 시간 = max(1.8초, delayMs). 떠 있는 동안 같은 방의 예고가 또 오면 다시 시작하지 않는다. 안내 패널은 닫는다. 기존 `inCombat` 기반 경고(`shouldWarn`)는 지웠다.
- **TUTORIAL_STEP**: 단계 카드(위쪽 가운데 2배 카드)를 이 이벤트로 — `keys` 는 2배 키 아이콘, 문구 끝 괄호 키는 뗀다(keys 가 비면 괄호에서 키를 뽑는다), 오른쪽 끝에 진행 `index+1/total`(흐림). 다음 단계까지 최대 20초, 노드(또는 시험장 여부)가 바뀌면 거둔다, 런이 끝나면 거둔다.
  - **대체 경로**: 이 이벤트를 아직 한 번도 받지 않았으면 예전처럼 여정 노드의 STORY 공지를 카드로. 받은 뒤로는 공지는 보통 자막이고, 지금 카드와 같은 문구의 공지만 삼킨다(공지가 먼저 와서 자막이 떠 있으면 카드가 올 때 거둔다 — 두 가지를 함께 보내도 한 번만 보이게).
- **시험장 HUD 좌상단**: '무기 시험장 · L 무기 고르기 · Esc 나가기' → '… · **Esc 일기장**' (오기 수정 — Esc 는 일시정지 일기장을 연다).

### 소유 코드 변경
`HudScene.ts`(TUTORIAL_STEP·ENEMY_INCOMING 구독, 고르기 Esc → `cancelRouteChoose`, `afterRelease` 로 뗀 뒤 실행 일반화, 자막 문구 기억), `TutorialHud.ts`(`takeStep`·`enemyIncoming`·`reset`, 카드 출처·위치 기억), `tutorialView.ts`(+test: `incomingWarns`·`stepFromEvent`·`stepFromNotice`·`sameStepText`, `shouldWarn` 삭제), `RouteMap.ts`(쓰지 않게 된 `hasChoices` 삭제), `debug.ts`(`cancelChooseCmd`, `__lopadUi.cancels`), `text.ts`(`labHud`·`chooseHint`·`tutStep`).

### 검증
tsc·eslint 통과, vitest 375 통과. 헤드리스(Playwright, 빌드본, `uidebug=1`, 시험장에서 가짜 route·이벤트): 시험장 문구 확인 → 여정 노드 공지 → 대체 카드 → TUTORIAL_STEP(2/5) 카드로 교체 → 같은 문구 공지 삼킴·다른 공지는 자막 → ENEMY_INCOMING delay 0 무시·900 경고·같은 방 재예고 재시작 없음 → 고르기 지도 Enter(확인 창) → W·Esc 누름·뗌 한 묶음 = 확인 창만 닫힘(취소 0) → Esc = 지도 닫힘 + 뗀 뒤 취소 1회 → choosing false 면 다시 열리지 않음 / true 로 남으면 1.5초 뒤 다시 열림.

### 임시값 (도영 님 검토 대상)
'Esc 물러나기'·'Esc 일기장' 문구, 단계 카드 진행 표시 `n/total`(흐림, 문구 오른쪽), 경고 머묾 max(1.8초, delayMs).

## 53라운드 후속 (2026-10-03) · 시험장 갈래 첫 Esc 버그 · '싸우는 법' 다시 보기 (Q50)
결정: `decisions/2026-10-03-round-53-playtest4.md` Q47~Q50. 계약: `contracts/ui-system-interface.md` '53라운드 추가'(cancelKey: 상점·구조물·lab '0', labBranch '9', 필수 메뉴 없음). 시스템 코드 열람 없음(계약 + `src/contract/ui.ts` 만).

### 시험장 갈래(labBranch) 첫 Esc 에 메뉴 전체가 닫히던 문제
- **원인**: Phaser 3.90 `KeyboardPlugin` 은 DOM 키 이벤트가 올 때마다 그 스텝 동안 쌓인 큐(POST_STEP 에서 비움)를 처음부터 다시 훑고, 중복 방지는 '바로 앞 이벤트와 같으면 건너뜀' 뿐이다. 프레임이 밀려 한 스텝 사이에 키 이벤트가 셋 이상 쌓이면(이동 키 자동 반복 + Esc 누름·뗌, 메뉴가 처음 그려지는 무거운 프레임 등) **같은 Esc 이벤트가 다시 넘어온다**(`repeat` false). 첫 처리로 labBranch 에 '9'(뒤로)를 보내 lab 이 다시 열리고, 다시 넘어온 같은 Esc 가 새로 열린 lab 의 cancelKey '0' 으로 처리돼 전부 닫혔다(= 이전 Esc 가 다음 메뉴의 cancelKey 로 새는 것). 49라운드 노드 지도 확인 창 `inputAfter` 와 같은 원인.
- **수정**: `keyGate.ts` `takeKey(e)` — UI 키 처리기는 **실제로 동작할 때** 이벤트 객체를 기록(WeakSet, UI 씬 전체 공유)하고, 이미 기록된 이벤트면 아무것도 하지 않는다. `escNav.resolveMenuEsc` 가 열린 메뉴(마지막 `MENU_OPEN`)의 cancelKey 만 쓰고, 닫히는 중(MENU_CLOSE 뒤 씬이 멈추기 전)·자동 반복·이미 처리된 이벤트는 무시.
- **같은 실수 점검·적용**: 메뉴 목록 숫자·Enter·위아래(`SelectList` — 고른 결과로 다음 메뉴가 열려도 같은 키로 또 고르지 않게: 시험장 무기 '1' → 갈래 '1', 상점 구매 → 다시 그린 상점에서 또 구매 등), 패 탁자 카드 키, 일시정지 Esc(닫힌 뒤 HUD 가 같은 Esc 로 일시정지를 또 여는 일), HUD Esc·Enter·Tab·M(방금 연 지도를 같은 키가 바로 닫는 일), 결과 Esc. 노드 지도·워프 지도·지역 카드는 기존 처리(시각 기준 `inputAfter`·뗀 뒤 실행·건너뛰기) 그대로.
- 메뉴 id 로 cancelKey 를 추정하는 코드는 원래 없었다(테스트만 labBranch '0' 으로 적혀 있어 '9' 로 고침).

### '싸우는 법' 다시 보기 (Q50)
- 일시정지 일기장 목록: `[1] 더 쓴다 (Esc) / [2] 소리 / [3] 싸우는 법 / [4] 일기장을 덮는다`, 시험장은 `[1] 계속한다 (Esc) / [2] 소리 / [3] 싸우는 법 / [4] 시험장을 나간다`. 페이지 높이 282 → 300(한 줄).
- [3] → 튜토리얼 안내 패널과 **같은 패널**(`TutorialHud.buildHowToPanel`, 스냅샷의 보조 동작 이름·넣기/뽑기로 줄을 만든다)을 화면 가운데, 일기장 위에 띄운다. 뒤는 G00 α0.55 로 덮고 클릭을 막는다. Esc·Enter·클릭으로 닫으면 일기장으로 돌아온다(Esc 한 단계 뒤로). 일시정지 중이라 저절로 닫히지 않는다. 시스템 데이터는 스냅샷(`weapon.secondaryName`·`carry`)만 사용.

### 소유 코드 추가·변경
`keyGate.ts`(신규), `escNav.ts`(+test: labBranch '9'·상점↔시험장 전환·다시 넘어온 Esc), `MenuScene.ts`, `widgets.ts`(`SelectList` takeKey·`setEnabled`), `PauseScene.ts`, `HudScene.ts`, `ResultScene.ts`, `TutorialHud.ts`(`buildHowToPanel` 분리), `text.ts`(`pauseHowTo`).

### 검증
tsc·eslint 통과, vitest 전체 373 통과(UI 57). 헤드리스(Playwright, 빌드본, `uidebug=1`, 스크립트 `scratchpad/labesc.cjs`): 타이틀 [3] → 시험장 → L(lab) → 1(labBranch, cancelKey '9') → **한 작업 안에 W 누름·Esc 누름·Esc 뗌·W 뗌**(프레임 밀림 재현) → lab 으로 한 단계만 돌아옴 → Esc → 닫힘. 대조: 수정을 잠시 끄면 같은 입력에 lab 까지 닫히고 다음 Esc 가 일시정지를 엶. 일시정지 [3] → 패널 → 같은 묶음 Esc → 패널만 닫히고 일기장 유지 → [3] → 클릭 닫기.

### 임시값 (도영 님 검토 대상)
항목 위치·key([3], 덮기·나가기는 [4]로 밀림), 항목 문구 '싸우는 법', 시험장 일기장에도 넣음, 뒤 덮기 α0.55.

## 53라운드 (2026-10-03) · Esc 한 단계 뒤로 · F 넣기/뽑기 표시 · 튜토리얼 안내 · 1920 렌더 규칙
결정: `decisions/2026-10-02-round-51-playtest3.md` §3·§4·§6, `decisions/2026-10-03-round-53-playtest4.md` Q14~Q17. 계약: `contracts/ui-system-interface.md` '53라운드 추가'.

### 화면
- **Esc = 한 단계 뒤로**: HUD(지역 카드 → 튜토리얼 안내 → 노드·워프 지도 → 없으면 일시정지), 일시정지(덮기 확인 → 목록 → 재개), 메뉴(`cancelKey` 있으면 그 줄 · 메타 메뉴는 타이틀 · 반드시 고르는 메뉴는 머무르고 '하나를 골라야 덮을 수 있다' 1.4초), 결과(타이틀). 판단은 `escNav.ts`.
- **F 넣기/뽑기**: HUD 하단 묶음 3행 오른쪽 끝 `[F] 넣음 · 발도 준비`(첫 타 준비는 층 강조) / `[F] 뽑음`(흐림). `carry` 가 null·없으면 숨김. 조작법 줄에 'F 넣기·뽑기'.
- **튜토리얼(여정 노드)**: ① 단계 카드 — 시스템 공지(STORY notice)를 위쪽 가운데 2배 카드로(끝 괄호 키는 2배 키 아이콘), 다음 공지까지 최대 20초. ② 안내 패널 — 배너·지역 카드가 끝나면 가운데 '싸우는 법'(키 아이콘 줄: 이동·공격·우클릭·대쉬·F + 기타 키 한 줄), Enter·Esc·클릭·12초. ③ 경고 — 전투 시작(`inCombat` false→true) 때 '주의 / 적이 다가온다' 깜빡임 1.8초, 안내 패널은 닫힘.
- **1920 렌더**: `scale.width/height` → `UI_SCREEN`. 탄생 연출 안내 카메라는 main 카메라의 뷰포트·zoom·원점을 따른다.

### 소유 코드 추가·변경
`escNav.ts`(+test), `carryView.ts`(+test), `CarryHud.ts`, `keycap.ts`(Container → Graphics → 글), `tutorialView.ts`(+test), `TutorialHud.ts`, `text.ts`(`R53_TEXT`, 조작법 F), `debug.ts`(`snap()`·`scenes()`·`events`), HudScene·MenuScene·PauseScene·ResultScene·TitleScene 등.

### 임시값 (도영 님 검토 대상)
`R53_TEXT` 문구 전부, 안내 패널 12초·단계 카드 20초·경고 1.8초, 단계 카드 위치(y 52), 경고는 튜토리얼 노드에서만.

## 50라운드 (2026-10-02) · 지역 카드(키아트)·일러스트 M 지도·위치 정보 키아트
계약: `contracts/ui-system-interface.md` **§12** (+§10·§11), 승인 #18(49·50라운드 연장). 에셋: `assets/sprites/ui/keyart_{waste,gate,outer,brewery,hall}.png`·`map_bg_f1.png`(아트 커밋 e3de0b4) → `assets/ui/keyart/keyart_<key>.png`·`assets/ui/map_bg_1.png` 사본(수정 금지). 시스템 변경 없음(`UiRouteNode.region` 사용). 시스템 코드 열람 없음.

### 화면
- **지역 카드** (`RegionCard.ts`, depth 90 = HUD 자막 위·노드 지도 아래): `ROUTE_NODE_ENTERED` 의 id 로 스냅샷 `route` 에서 노드를 찾아 `region` 이 마지막으로 카드를 띄운 지역과 다르면 화면 전체에 그 지역 키아트(960×540 1:1) → 아래 띠(G00 α0.55, 가운데 y400·높이 84) 위에 지역 이름(ink_body, Galmuri11 ×2)·짧은 설명(ink_accent)이 배경보다 반 박자 늦게 → 사라짐. 나타남 0.3 + 머묾 1.3 + 사라짐 0.3 = 1.9초. **아무 키·클릭**으로 넘김(0.16초에 사라짐, 뜬 직후 0.2초는 무시). 입력은 게임에도 그대로 간다(카드는 보기만 가림, 게임을 멈추지 않음).
  - 차례: 기존 가운데 배너 차례에 같이 넣는다 — 층 제목 → **지역 카드** → 노드 이름 배너 순서로 겹치지 않는다. 글자 배너 대기 상한 3 은 그대로, 지역 카드는 상한과 관계없이 넣는다.
  - **탄생 연출과 겹치지 않게**: 탄생 중에 온 카드는 `BIRTH_DONE` 뒤로 미룬다. 진입 이벤트가 `BIRTH_STARTED` 보다 먼저 와서 카드가 이미 떴으면 거두고 맨 앞으로 되돌린다. `BIRTH_DONE` 때 지금 노드의 지역을 한 번 더 확인한다(첫 노드 진입 이벤트가 없어도 첫 카드가 뜨게). `RUN_ENDED` 는 카드를 치우고 마지막 지역을 비운다. 무기 시험장(`lab`)에서는 띄우지 않는다.
  - 지역 → 키아트: `region` 은 표시 이름이라 낱말로 찾는다(`theme.REGION_ART`: 성문→gate, 외곽→outer, 양조→brewery, 연회·본영→hall, 황무지·전장·여정→waste). 맞는 것이 없으면 그림 없이 어두운 바탕 카드. 설명은 키별 임시 문구(`text.REGION_TEXT`, 텍스트 팩 `hud.region_<키>` 우선), 키가 없으면 노드 `desc` 첫 문장.
  - 지역 비교는 표시 이름 그대로 — 실게임 1층은 '황무지'(2노드) → '성문' → '외곽 거리' → '양조 구역' → '지배자의 연회장' 이라 카드 5번.
- **M 지도 1층 = 지도 그림** (`RouteMap.ts`, `theme.MAP_BG_FLOORS = [1]`): 배경 일러스트가 있는 층은 **일러스트 좌표계 우선** — 양피지 사다리꼴·원근 투영 대신 그림을 지도 칸(560×약 370)에 비율 유지로 맞춰(560×315, 위아래 가운데) 깔고, 그림자(S0 α0.55, 4px)·테두리(S0 1px). 그림이 없는 층(2층~)은 49라운드 원근 양피지 그대로.
  - **배치** (`routeView.layoutOnPath`): 층별 길 점 목록(`theme.MAP_PATHS[floor]`, 그림 원본 960×540 px)을 길이로 매개화해 단계(col)를 길이 비율로 고르게 놓고, 같은 단계 갈래(row)는 그 자리 접선(앞뒤 40px 로 구함)에 **수직**으로 104px 간격(가운데 정렬, row 0 = 진행 방향 왼쪽 = 대개 위), 그림 가장자리 34px 안으로. 1층 길: (100,112) 황무지 점선 길 → (252,212) 성문 → (420,312)·(520,345) 가운데 아래로 처진 밝은 길(외곽 거리 사이) → (690,305)·(760,250) 양조 구역 → **(855,220) 연회장(보스)**.
  - **원근과 공존**: 깊이 = 그림 위쪽일수록 멂(1 - y/540), 크기 비 1 → 0.82(원근 0.62 보다 약하게) — 들림·그림자 크기·점 크기만 이 깊이를 따른다. 먼 것부터 그려 가까운 것이 위로.
  - 길 점: 어두운 그림 위에서 보이게 점마다 S0 테두리 1px, 지나온 길은 S5(밝게), 고를 길 층 강조 22, 그 외 S2.
  - 지금 노드 이름표가 지도 오른쪽 끝이라 왼쪽으로 넘어가면(보스) 주인공 표시 왼쪽으로 더 비킨다(겹침 수정 — 양피지 지도에도 적용).
- **위치 정보 칸 배경**: 오른쪽 칸 위쪽(범례 위까지, 바깥 여백 8×6)에 **지금 노드 지역 키아트**를 가운데 잘라 덮고(cover) G00 α0.55 로 두 번 어둡게 + 테두리 S1 1px. 키아트가 없는 지역이면 그리지 않는다.
- **성능**: 큰 그림(키아트 5장 각 약 0.5~0.65MB·지도 0.6MB)은 preload 에서 뺐다(49라운드엔 `MAP_BG_FLOORS` 를 모든 UI 씬 preload 에서 읽었다). `kit.ensureImage` 로 **필요할 때 한 번만** 읽는다(같은 키 중복 요청 합침, 실패 키는 다시 읽지 않음, 읽던 씬이 꺼지면 대기 버림). HUD 가 노드 지도 층에서 층·지금 노드가 바뀔 때만 그 층 지도 그림 + 지금 지역 + 바로 다음 단계(links) 지역 키아트를 미리 읽는다 — 타이틀에서는 0건, 실게임 시작 시 `map_bg_1`·`keyart_waste` 2건. 지도·옆 칸 그림은 표시 크기로 **한 번 줄인 캔버스 텍스처**(`kit.derivedTexture`, 고품질 축소, 크기·방식별 1회)를 1:1 로 깐다 — 게임이 pixelArt 최근접 확대라 큰 그림을 그대로 줄이면 깨진다. 그림이 지도를 연 뒤에 도착하면 그 자리(바탕 바로 위·테두리 바로 아래)에 끼운다. 카드는 키아트가 아직 없으면 최대 1.2초 기다리고(오면 바로) 못 읽으면 그림 없이.

### 소유 코드·에셋 추가·변경
| 파일 | 내용 |
|---|---|
| `RegionCard.ts` (신규) | 지역 카드 (키아트 전면 → 이름·설명 → 사라짐, 아무 키 넘김, 키아트 기다림) |
| `regionView.ts`, `regionView.test.ts` (신규) | 순수 계산: 지역 → 키아트 키, 지역 바뀜, 카드 밝기 곡선, 설명 첫 문장 + 길 매개화·그림 맞추기·덮어 자르기·길 위 배치 테스트 (테스트 9개) |
| `routeView.ts` | `MapPathSpec`·`pathSampler`·`fitContain`·`coverCrop`·`layoutOnPath`, `PerspectiveLayout.farScale` |
| `RouteMap.ts` | 일러스트 지도(비율 유지·길 위 배치·점 테두리), 늦게 온 그림 끼우기, 옆 칸 키아트, 보스 이름표 비킴. 사다리꼴 마스크 분기 삭제 |
| `HudScene.ts` | 배너 차례에 지역 카드(`BannerItem`), 진입·탄생·런 종료 처리, 큰 그림 미리 읽기, 디버그 `view.banners` |
| `kit.ts` | `ensureImage`·`derivedTexture`·`mapBgUrl`·`keyartKey/Url`, preload 의 지도 그림 읽기 삭제 |
| `text.ts` | `REGION_TEXT`·`regionText()` |
| `theme.ts` | `MAP_BG_FLOORS=[1]`, `MAP_PATHS`·`MAP_ILLUST`·`REGION_ART`·`REGION_CARD`·`SIDE_ART` (임시값) |
| `assets/ui/keyart/keyart_*.png`, `assets/ui/map_bg_1.png` | 아트 사본 (수정 금지) |

### 임시값 (도영 님 검토 대상)
- 문구(`REGION_TEXT`, 텍스트 팩 `hud.region_<키>` 우선): 황무지 '부러진 창과 깃발만 남은 옛 싸움터' / 성문 "술독 제국 '잔'으로 드는 문" / 외곽 거리 '술 냄새가 골목마다 밴 성 밖 거리' / 양조 구역 '증류탑이 밤낮없이 끓는 곳' / 연회장 '취한 지배자가 잔치를 벌이는 곳'. 지역 이름은 시스템 값 그대로.
- 수치: 카드 0.3·1.3·0.3초, 넘김 0.16초·무시 0.2초, 글자 늦음 0.5, 키아트 기다림 1.2초, 띠 y400·높이 84, 이름–설명 간격 6, depth 90 / 1층 길 점 10개·갈래 간격 104·여백 34·먼 크기 0.82·접선 40, 그림자 4·점 테두리 1 / 옆 칸 여백 8×6·어둡게 2번.
- 판단: ① 지역 카드 뒤에 노드 이름 배너를 그대로 띄운다(카드 1.9초 + 배너 1.6초). ② 카드가 떠 있는 동안 게임을 멈추지 않는다(계약에 정지 요청 없음 — 카드 중 적이 움직일 수 있음). ③ 일러스트 층은 사다리꼴 원근을 버리고 그림 좌표계를 쓴다(깊이는 그림 y 로 약하게만). ④ 지역 비교는 표시 이름(황무지 → 전장처럼 같은 키아트라도 이름이 다르면 카드). ⑤ 옆 칸 키아트는 '살펴보는 곳'이 아니라 지금 지역 고정.

### 검증
작업 트리(시스템 동시 리팩터링 중, 마지막 확인 시점엔 통과)와 **HEAD + UI 변경분** 사본 `scratchpad/iso50` 모두에서 `npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(사본 36 파일 266개)·`npx vite build` 통과. 작업 도중 작업 트리 tsc 는 `src/scenes/game/GameCamera.ts` 오류로 실패한 적 있음(시스템 파일, UI 무관).
헤드리스(Playwright 960×540, `vite preview --port 4197`, 스크립트 `scratchpad/r50ui.cjs`, 스크린샷 `scratchpad/r50ui/`, `uidebug=1` 가짜 route): 타이틀 그림 요청 0 → 실게임 탄생 중 카드 없음 → 클릭 건너뛰기 뒤 '황무지' 카드(실게임 `BIRTH_DONE` 경로, 약 1.9초) → 가짜 '성문' 카드(나타남·머묾) → 카드 뒤 노드 이름 배너 → 진입 + `BIRTH_STARTED` 같은 순간: 연출 중 카드 없음, `BIRTH_DONE` 뒤 '황무지' 카드 → 같은 지역 재진입 카드 없음 → '외곽 거리' 카드 x 키로 넘김(약 0.12초) → 양조 구역·연회장 카드 → M 지도(시작·외곽 거리·보스, 둘러보기) → 고르기·'넘어가시겠습니까?'. 콘솔 오류·경고 0, HTTP 4xx 0. 키아트 요청은 지역마다 1번.
- 참고(기존 동작): 헤드리스에서 M 을 빠르게 연달아 누르면 가끔 한 번이 무시된다 — **HEAD 빌드에서도 같음**(49라운드에 적은 '프레임이 밀리면 같은 키 이벤트를 다시 넘김' 과 같은 원인으로 보임, 열고 바로 닫힘). 이번 변경과 무관.

---

## 49라운드 (2026-10-02) · M 지도(입체·위치 정보)·넘어가기 확인·음소거 이동·무기 자원 게이지·무기 시험장
결정: `decisions/2026-10-02-round-49-playtest2.md` 5절(무기 자원·시험장 UI 부분)·6절(노드 지도). 계약: `contracts/ui-system-interface.md` **§11** — `UiSnapshot.resource`(`UiWeaponResource`)·`muted`·`lab`, `UiRouteNode.region/desc`, `uiCommands.setMuted`·`startWeaponLab`, 메뉴 id `lab`·`labBranch`. 아이콘: `art-assets.md` §7.3 마지막 줄(여정 = 앞으로 뻗은 길) → `assets/ui/kit/node_icons.*` 사본 갱신(아트 커밋 bc1cdbb, 192×96·순서 그대로). 시스템 코드 열람 없음.
값이 비어 있으면(null·빈 문자열) 그리지 않는다.

### 화면
- **M = 지도** (Tab 도 같은 지도, `HudScene` 이 `keydown-M` 을 Tab 과 같은 처리로): 노드 지도 층은 노드 지도 보기(게임 정지), 그 외 층은 워프 지도. 무기 시험장(`lab`)에서는 무시. 보기 모드는 M·Tab·Esc 로 닫는다.
- **노드 지도 다시 그림** (`RouteMap.ts`, 일기장 한 페이지 864×456 그대로):
  - 왼쪽 지도 칸(560×약 370) = **펼친 양피지**: 계단식 사다리꼴(아래 폭 552 → 위 60%), 오른쪽 아래로 4px 그림자(S0 α0.55), 바탕 S4, 지평선 격자(가로 = 깊이 6등분, 멀수록 촘촘 / 세로 7줄이 위로 모임, S3 점선), 위 가장자리 밝은 띠(S5 α0.55, 넘어가는 종이)·아래 말린 가장자리(S2 + 윗선 S5 α0.55), 좌우 계단 테두리 S1.
  - **원근 배치**(`routeView.layoutPerspective`): 진행(col)이 **아래(가까움) → 위(멂)**, 같은 단계 갈래(row)는 좌우. 단계 간격은 멀수록 좁게(곡선 ease 0.55), 좌우 폭은 멀수록 0.62배까지. 가장 먼 간격이 40px 보다 좁아지면 원근을 풀어 고른 간격.
  - 노드 = **땅에서 들린 표지**: 땅 점에 그림자 타원(S1, 가까울수록 큼 15×4 → 9×2), 2px 기둥, 그 위 아이콘(들림 8 → 4px). 먼 노드부터 그려 가까운 것이 위로 겹친다.
  - 길 = 땅 위 점선(그림자 가장자리에서 비움): 가까운 쪽(깊이 < 0.34) 3px 점, 그 외 2px, 간격도 멀수록 좁게. 색은 48라운드와 같음(지나온 길 S0, 고를 길 층 강조 22, 그 외 S2).
  - 이름표는 **지금·갈 수 있는 곳·고른 곳만** 아이콘 오른쪽에(지도 칸을 넘으면 왼쪽). 먼 곳은 아이콘과 오른쪽 칸으로 읽는다. 주인공 표시는 지금 노드 왼쪽(발이 땅에), 커서 촉은 고른 노드 고리 왼쪽(지금 노드면 숨김).
  - **배경 일러스트 자리**: `theme.MAP_BG_FLOORS` 에 층 번호(`UiRoute.floor`)를 넣으면 `assets/ui/map_bg_<floor>.png` 를 읽어 양피지 대신 사다리꼴 모양으로 잘라(GeometryMask) 깐다(그림자·말린 가장자리·테두리는 그대로). 지금은 빈 목록(없는 파일 404 방지). 그림 크기는 지도 칸 552×약 358 에 늘려 맞춘다.
  - 오른쪽 칸(232): **지금 있는 곳**(page_faint) → 지역 `region`(page_title ×2) → '이름 · 종류'(page_body) → 설명 `desc`(줄바꿈). 괘선. **고른 곳**(고르기)/**살펴보는 곳**(보기) → 이름(page_selected)·'지역 · 종류 · 상태'·설명(page_faint) — 지금 있는 곳과 같으면 비움. 아래에 범례 2열×3줄(아이콘 32 + 이름). region·desc 가 없으면 그 줄을 건너뛴다.
- **'넘어가시겠습니까?' 확인** (고르기 모드): available 노드를 Enter·Space(뗀 뒤)·클릭(뗀 뒤)으로 고르면 지도 칸 가운데 `panel_paper` 300×112 창 — '넘어가시겠습니까?'(Galmuri14) / '지역 · 이름'(page_selected) / [예] [아니오] 버튼(Container → Graphics → 글자, 포커스 = 층 강조 20 테두리 2px + page_selected) / 안내 '←→ 고르기 · Enter 정하기 · Esc 아니오'. 뒤 페이지는 G00 α0.5 로 덮고 클릭을 막는다. 기본 포커스 '예'. ←→·A·D 전환, Enter·Space·Y(뗀 뒤) 정하기, Esc·N 아니오. **예일 때만** 한 프레임 뒤 `chooseNode`, 아니오면 지도로 돌아온다.
  - 확인 창은 자신을 열고 닫은 입력 이벤트 시각(`event.timeStamp`) 이전의 키 이벤트를 무시한다 — 헤드리스에서 프레임이 밀리면 Phaser 가 같은 키 이벤트를 다시 넘겨, 창을 연 Enter 가 곧바로 '예' 가 되는 것을 확인했다.
- **HUD 우상단**: 'M 음소거' → **'M 지도'**. 음소거 중이면 그 오른쪽에 `icon_mute`. 노드 지도 층은 'Tab 지도' 줄을 없앴고(M·Tab 같은 지도), 그 외 층은 'Tab 워프' 줄 유지. 좌상단 노드 이름은 '지역 · 이름'.
- **Esc 일기장 소리 설정** (`PauseScene`): 목록 '[1] 더 쓴다 (Esc) / [2] 소리 끄기(음소거 중이면 소리 켜기) / [3] 일기장을 덮는다'. [2] → `setMuted(!muted)`, 처음 상태는 `snapshot.muted`, 누른 뒤에는 화면 상태를 바로 뒤집는다(일시정지 중 스냅샷이 늦을 수 있어). 페이지 높이 264 → 282. 첫 줄 노드 이름도 '지역 · 이름'. UI 쪽에 M 음소거 처리는 원래 없었다(시스템 키였음) — 힌트만 바꿈.
- **무기 자원 게이지** (`ResourceHud.ts`, 계약 §11.1): 자원이 있으면 하단 묶음 64 → **80**(아래 여백 12 유지, 위로 늘고 보스 게이지·자막도 같이 올라감), 3행(y+59)에 라벨(`resource.label`, ink_faint) + 게이지 + 'n/m'(ink_faint) + 상태 글(ink_accent).
  - 기력(stamina): `gauge_frame` 150 막대, 채움 = 회색 띠 × 층 강조 23(ok)·20(low), exhausted 는 회색 띠 + '지침' 깜빡임(1 ↔ 0.55, 0.2초).
  - 화살(ammo): 화살 칸 5×11(촉 층 강조 22·대 G13·깃 G11 / 빈 칸 G04), 간격 3. 16칸이 넘으면 막대. reloading 이면 오른쪽 픽셀 진행 링(반지름 5, 12시부터 시계 방향, 켜짐 강조 22·꺼짐 G04) + '장전'.
  - 열기(heat): 120 막대 + 1/3·2/3 눈금(G00), 채움 색 = 단계(0 회색, 1·2·3 = 강조 20·22·25 달아오를수록 밝게), 오른쪽 단계 눈금 3칸(6×6). overheat 면 막대 가득 + 맥동(1 ↔ 0.55) + 막대 아래 2px 냉각 진행선(G03 바탕, G11 진행) + '과열'. `stage` 가 없으면 비율로 단계를 나눈다.
  - 값은 정수로 표시(바닥 0, 조금 남으면 올림).
- **무기 시험장** (계약 §11.4): 타이틀 목록 끝에 '[3] 무기 시험장' → `startWeaponLab()`. `snapshot.lab` 이면 좌상단 '무기 시험장 · L 무기 고르기 · Esc 나가기', 우상단 미니맵·노드 띠·지도 안내 숨김, M·Tab 무시. Esc 일기장은 제목 '무기 시험장', '[1] 계속한다 (Esc) / [2] 소리 / [3] 시험장을 나간다'(확인 없이 `toTitle()`), 이름·층·세이브·시드 줄과 'Tab 워프' 생략.
  - `lab`·`labBranch` 메뉴는 기존 일기장 메뉴 틀(넓은 페이지 520). 갈래 깊이는 계약에 필드가 없어 **라벨 앞 공백(2칸 = 1단)·트리 기호(└ ├ ㄴ · - 등)·key 의 '.'·'/'·'>' 구분자**로 추정해(`resourceView.menuIndent`) 14px 씩 들여쓰고 '└ ' 를 붙인다. 그만두기 줄은 들여쓰지 않는다.

### 소유 코드·에셋 추가·변경
| 파일 | 내용 |
|---|---|
| `RouteMap.ts` | 입체 지도(양피지·원근·표지·그림자), 오른쪽 위치 정보·범례, 넘어가기 확인 창, 배경 일러스트 자리 |
| `ResourceHud.ts` (신규) | 무기 자원 게이지(기력·화살·열기) |
| `resourceView.ts`, `resourceView.test.ts` (신규) | 순수 계산: 자원 비율·화살 칸·진행 링 점·열기 단계·표시 값, 갈래 들여쓰기, 'M 음소거' 바꾸기 + 원근 배치 테스트 (테스트 11개) |
| `routeView.ts` | `layoutPerspective`·`perspectiveCurve`·`trapezoidRows`·`ellipseRows` |
| `HudScene.ts` | M 키, 'M 지도'·음소거 아이콘, 시험장 모드, 하단 묶음 높이 바꾸기·3행 자원 |
| `PauseScene.ts` | 소리 끄기·켜기, 시험장 일기장 |
| `TitleScene.ts` | '무기 시험장' 항목 |
| `MenuScene.ts`, `widgets.ts` | lab·labBranch 넓은 페이지·들여쓰기(`SelectLine.indent`) |
| `kit.ts` | `mapBgKey`·배경 로드, `Gauge.setPositionY`·`setFillSlot`·`setAlpha` |
| `text.ts` | `ROUTE_TEXT` 추가 키, `R49_TEXT`·`r49Text()`, `controlsLine` 'M 지도' |
| `theme.ts` | `MAP3D`·`MAP_BG_FLOORS`·`RES` (임시값) |
| `debug.ts` | `setMutedCmd`(기록 `muted`), `view.routeMap.confirm` 버튼 좌표 |
| `assets/ui/kit/node_icons.png/json` | 아트 49라운드 사본으로 갱신 (수정 금지) |

### 임시값 (도영 님 검토 대상)
- 문구(텍스트 팩 `hud.<키>` 우선): '지금 있는 곳'·'살펴보는 곳'·'고른 곳', '넘어가시겠습니까?'(결정 원문)·'예'·'아니오'·'←→ 고르기 · Enter 정하기 · Esc 아니오', 'M 지도', 보기 안내 '←→↑↓ 둘러보기 · M·Tab·Esc 닫기', '무기 시험장'(타이틀·일기장 제목), '무기 시험장 · L 무기 고르기 · Esc 나가기'(L 은 계약의 임시 제안 키), '계속한다'·'시험장을 나간다', '소리 끄기'·'소리 켜기', 자원 상태 '지침'·'장전'·'과열'.
- 수치(`theme.ts MAP3D`·`RES`): 오른쪽 칸 232·간격 16, 원근 farScale 0.62·ease 0.55·최소 간격 40·가까운 줄 간격 ≤150, 양피지 위 폭 60%·그림자 4·말림 4·격자 6×7, 들림 8→4·그림자 15×4, 이름표 줄바꿈 96, 확인 창 300×112·버튼 높이 18·최소 폭 64·간격 16·뒤 α0.5 / 하단 묶음 80·3행 y+59, 기력 막대 150, 화살 5×11·간격 3·16칸 상한, 링 반지름 5, 열기 막대 120·눈금 6·간격 3, 맥동 0.2초, 색 슬롯(기력 23·20, 화살 22, 열기 20·22·25, 링 22).
- 판단: 진행 방향을 왼→오에서 **아래→위**로 바꿨다(위쪽이 멀어 보이고 길이 앞으로 뻗게). HUD 노드 띠는 왼→오 그대로. 먼 노드 이름표를 숨겼다. 확인 창 기본 포커스 '예'. 시험장 나가기는 `toTitle()`(계약에 별도 명령 없음). 음소거 중 HUD 에 `icon_mute` 표시.

### 검증
`npx tsc --noEmit`·`npx eslint .`·`npx vitest run`(35 파일 257개)·`npx vite build` 작업 트리에서 통과(시스템 작업 중이던 시점엔 시스템 파일 tsc 오류가 있어 **HEAD + UI 변경분** 사본 `scratchpad/iso49` 로도 확인).
헤드리스(Playwright 960×540, `vite preview --port 4193`, 스크립트 `scratchpad/r49ui.cjs`, 스크린샷 `scratchpad/r49ui/`, `uidebug=1` 가짜 route·resource·lab·메뉴): 타이틀 3항목 → 자원 게이지 10종(+없음) → HUD 'M 지도'·음소거 아이콘·'지역 · 이름' → M 보기(게임 정지·일기장 없음)·방향키·M 닫기·Tab 열기·Esc 닫기(재개) → 고르기: Enter → 확인 창, Esc → 창만 닫힘, →·Enter(아니오) → 선택 없음, Enter·Enter(예) → `chooseNode('b1')`·지도 닫힘, 안전망 재열기 → 클릭 → 확인 → 아니오 클릭 → 다시 클릭 → 예 클릭 → `a1` → 늦은 단계 보기 → Esc 일기장 [2] 두 번 → `setMuted(true)`·`setMuted(false)` → 시험장 HUD·M 무시·lab 메뉴·labBranch 들여쓰기·[3] 선택 기록·시험장 일기장. 콘솔 오류·경고 0, HTTP 4xx 0.
작업 트리 실게임: 타이틀 '[3] 무기 시험장' 클릭 시 화면 변화 없음(시스템 `startWeaponLab` 구현 대기로 보임 — 시스템 코드 미열람). `setMuted` 뒤 `snapshot.muted` 는 HEAD 시스템에서 false 그대로(시스템 반영 대기).

---

## 48라운드 (2026-10-02) · 노드 지도·노드 띠·탄생 연출
결정: `decisions/2026-10-02-round-48-playfeel-route.md` (Q1 카메라 2배, Q3 노드 지도, Q6 탄생, Q9 1층 노드 구성, Q11 워프 비활성 → Tab = 노드 지도 보기). 계약: `contracts/ui-system-interface.md` **§10** (승인 #17) — `UiSnapshot.route`(`UiRoute`·`UiRouteNode`), `uiCommands.chooseNode`, `ROUTE_CHOOSE_OPEN`·`ROUTE_NODE_ENTERED`·`BIRTH_STARTED/DONE`. 아이콘: `contracts/art-assets.md` §6.5 (승인 #18) `assets/sprites/ui/node_icons.*` → `assets/ui/kit/` 사본. 그 외 시스템 코드 열람 없음.
`route` 가 null(또는 노드 0개)이면 전부 기존 동작(방 미니맵·Tab 워프·'시련 n/m').

### 화면
- **노드 지도** (`RouteMap.ts`, HUD 씬 위 depth 100): 화면 G00 α0.55 → 일기장 한 페이지 864×456(책 896×488). 제목 줄: 가운데 '가는 길'(Galmuri14), 왼쪽 층 제목(page_faint), 고르기 모드면 오른쪽 '다음 갈 곳을 고른다'(page_selected) + `rule`.
  - 지도(높이 288): 왼→오 `col`, 단계 간격 = min(128, 폭/단계 수), 단계마다 `row` 수로 세로 가운데 정렬(줄 간격 ≤ 96) → 갈림길이 갈라졌다 합쳐진다. 1층 10노드(7단계) = 단계 간격 115.
  - 노드: `node_icons` 32×32 (행 0 기본 = current·available, 행 1 지나옴 = cleared, 행 2 잠김 = locked·passed; passed 는 노드·이름표 α0.55 추가). 2층부터 강조 1점을 그 층 램프로 바꾼 사본(`kit.ts nodeIconKey`). 시트가 없으면 계단식 픽셀 마름모(반대각선 18, S1/S2 채움 + S5/S4 테두리) + 키트 글리프(여정 mini_start·전투 mini_trial·쉼터 mini_rest·본영 mini_boss ×2, 상점 icon_gold, 이벤트 '?').
  - 상태 표시: current = 층 강조 22 마름모 고리 2px + **주인공 표시**(픽셀 사람 16×22: 그늘 S2 → 할로 강조 20 α0.5 → 몸 G14, 0.42초마다 2px 위아래) / available = 강조 20 바깥 고리 맥동(α1↔0.2, 0.64초) / 고른 노드 = 강조 20 고리 2px + `cursor` 촉.
  - 연결선 점선 2×2: 지나온 길(cleared/current 끼리) S0 6px 간격, 지금 고를 길(current→available) 강조 22 6px, 그 외 S1 9px.
  - 이름표: 노드 아래 6px, 가운데 정렬, 폭 = 단계 간격 - 12 에서 줄바꿈. current page_title, available page_body, 고른 노드 page_selected, 그 외 page_faint.
  - 아래: `rule` → 고른 노드 이름(page_selected ×2) + '종류 · 상태'(page_body) / 오른쪽 범례(아이콘 + 종류 이름 6개, 상점은 `names.shop`) / 거부 사유(page_selected, 오른쪽) / 조작 안내(page_faint).
- **고르기 모드** (`ROUTE_CHOOSE_OPEN`): 게임은 정지하지 않는다(시스템이 입력을 잠금). available 노드만 고를 수 있다 — 마우스(올리면 고름, 눌렀다 **뗀** 뒤) 또는 ←→↑↓·WASD(available 사이를 돌아가며) + Enter·Space(**뗀** 뒤) → 한 프레임 늦게 `chooseNode(id)`. true 면 닫고 1.5초 동안 다시 열지 않음, false 면 '지금은 그리로 갈 수 없다'. Esc·Tab 으로 닫히지 않는다(고를 곳이 0개일 때만 Esc 로 닫힘). 잠긴 노드 클릭은 무시. 어두운 바탕이 클릭을 막는다.
  안전망: 스냅샷 `route.choosing` 인데 지도·메뉴·일시정지·결과·탄생 연출이 없으면 HUD 가 연다(이벤트를 놓쳤거나 메뉴가 닫힌 뒤). `MENU_OPEN`·`RUN_ENDED`·`STAGE_STARTED` 는 지도를 닫는다.
- **Tab = 노드 지도 보기** (route 가 있을 때): 메뉴·일시정지·결과·`menu`·`choosing`·탄생 연출 중이면 무시. 열면 `pause()`(일시정지 일기장은 띄우지 않음), ←→↑↓ 로 노드 둘러보기·마우스 올리기(정보만), Tab·Esc 로 닫고 재개. `RESUMED` 가 오면 닫힘.
- **HUD 우상단 노드 띠** (`RouteStrip.ts`): 방 미니맵 대신 같은 `minimap_frame` 안에 전체 노드를 작은 마름모(반대각선 3, 단계 12px·줄 10px)로: 지금 = 층 강조 22 한 칸 크게, 지나온 곳 G08, 갈 수 있는 곳 G02 + G12 테두리, 먼 곳 G01 + G05 테두리, 지나친 갈래 G03. 연결 1px 점(지나온 G08 2px 간격, 고를 길 G11, 그 외 G04 3px). 아래 '남은 길 N'(현재 → 마지막 단계 수, 마지막이면 '마지막', ink_faint). 틀 크기는 노드에 맞추고(최소 폭 100) 'M 음소거'·'Tab 지도' 줄이 그 아래로 따라 내려간다.
- **좌상단**: route 가 있으면 '층 제목   지금 노드 이름' ('시련 n/m' 대신). 일시정지 일기장 첫 줄도 같음.
- **'Tab 지도'**: HUD 힌트(route 가 있으면 늘 보임)·일시정지 조작법 줄 덧붙임(`controlsLine(…, routeMode)`).
- **노드 진입** (`ROUTE_NODE_ENTERED`): 기존 층 배너와 같은 방식(가운데 Galmuri11 ×2 ink_body, 1.6초)으로 노드 이름. **배너는 이제 차례로** — 층 제목과 노드 이름이 같이 오면 덮어쓰지 않고 이어서(대기 최대 3).
- **탄생 연출** (`BIRTH_STARTED`~`BIRTH_DONE`): HUD 카메라를 숨기고, 안내만 그리는 카메라 하나로 하단 가운데(아래 24px) '아무 키나 눌러 건너뛰기'(ink_faint, 0.3초 나타남). 그동안 Tab·Esc 무시(건너뛰기 입력은 시스템), 자막은 마지막 한 줄·배너는 끝난 뒤로 미룸, 지도 닫음. `RUN_ENDED` 또는 15초가 지나면 스스로 해제.
- **카메라 2배 점검**: UI 씬 카메라는 영향 없음. 상호작용 말풍선은 계약대로 `interactable.screen`(캔버스 px)을 그대로 쓴다 — 줌 1 실게임에서 장부대 위 정확(스크린샷 09). 줌 2 실제 확인은 시스템 반영 후(이 빌드엔 아직 줌 1).

### 같이 고친 것
- **지도를 Esc 로 닫으면 일시정지 일기장이 열리던 문제** (45라운드 워프 지도도 같음): 누르는 프레임에 재개하면 게임 씬이 같은 Esc 를 받아 정지했다. 재개를 **Esc 를 뗀 다음 프레임**으로 미룸(놓쳐도 1초 뒤 재개). `HudScene.resumeAfterRelease`.
- 일시정지 일기장이 디버그 덮어쓰기(`uidebug`)를 반영하도록 `withDebug` 적용(디버그 꺼지면 영향 없음).

### UI 디버그 경로 추가 (`uidebug=1`)
`__lopadUi.fakeChoose(true)` → `chooseNode` 를 시스템으로 보내지 않고 true(기록 `chosen`). `__lopadUi.view.routeMap` = 열린 지도의 노드 화면 좌표(헤드리스 클릭용). 가짜 route 는 `patch({ route })` + `emit('ROUTE_CHOOSE_OPEN', route)`.

### 소유 코드·에셋 추가·변경
| 파일 | 내용 |
|---|---|
| `RouteMap.ts` (신규) | 노드 지도 오버레이(고르기·보기), 픽셀 마름모·고리·주인공 그리기, 종류 이름 |
| `RouteStrip.ts` (신규) | HUD 노드 띠 |
| `routeView.ts`, `routeView.test.ts` (신규) | 순수 계산: 배치·정렬·돌아가며 고르기·남은 단계·연결선 종류·점선 점 (테스트 6개) |
| `HudScene.ts` | 노드 지도 열기·닫기·고르기, 안전망, 노드 띠·우상단 배치, 탄생 연출 숨김, 배너 차례, Esc 재개 지연 |
| `Minimap.ts` | `setVisible` |
| `PauseScene.ts` | route 층 첫 줄·'Tab 지도', `withDebug` |
| `kit.ts` | `NODE_ICON_SHEET`(로드), `nodeIconKey`(층 강조 바꾼 사본) |
| `text.ts` | `ROUTE_TEXT`·`routeText()`, `controlsLine(secondary, routeMode)` |
| `theme.ts` | `ROUTE` 수치(임시값) |
| `debug.ts` | `chooseNodeCmd`, `fakeChoose`, `debugExpose`/`view` |
| `assets/ui/kit/node_icons.png/json` | 아트 사본 (수정 금지) |

### 임시값 (도영 님 검토 대상)
- 문구(`text.ts ROUTE_TEXT`, 텍스트 팩 `hud.<키>` 우선): 지도 제목 '가는 길', '다음 갈 곳을 고른다', 안내 '←→↑↓ 고르기 · Enter·클릭 그리로 간다' / '←→↑↓ 둘러보기 · Tab·Esc 닫기', 상태 '지금 여기'·'갈 수 있다'·'지나온 곳'·'지나친 갈래'·'아직 멀다', 거부 '지금은 그리로 갈 수 없다', 종류 '여정'·'전투'·'상점'(→ `names.shop`)·'쉼터'·'이벤트'·'본영', 'Tab 지도', '남은 길 {n}'·'마지막', '아무 키나 눌러 건너뛰기'.
- 수치(`theme.ts ROUTE`): 페이지 864×456·여백 28·지도 높이 288, 단계 간격 ≤128·줄 ≤96, 노드 반대각선 18, 맥동 고리 24·0.64초, 점선 2px·6/9px, 주인공 흔들림 0.42초, 노드 띠(단계 12·줄 10·마름모 3·최소 폭 100), 탄생 안내 아래 24px·안전 해제 15초, 고르기 뒤 재열기 막기 1.5초, Esc 재개 대기 최대 1초.
- 판단: HUD 노드 띠는 **숨김 대신 전체 노드 축소판 + 남은 길**. 좌상단 '시련 n/m' 자리에 지금 노드 이름. passed 는 잠김 행 + α0.55. 잠김(행 2) 아이콘이 종이 위에서 꽤 흐려 앞길 종류는 이름표로 읽힌다 — 더 진하게 할지 검토.

### 검증 (헤드리스 Playwright 960×540, `vite preview --port 4183`, 스크립트 `scratchpad/r48ui.cjs`, 스크린샷 `scratchpad/r48ui/`)
시스템 작업 트리가 진행 중(런타임 오류 `this.buildArena is not a function`)이라 **HEAD + UI 변경분** 사본(`scratchpad/iso48`)으로 빌드해 확인. `uidebug=1` 가짜 route(1층 10노드).
HUD 노드 띠·'Tab 지도'·좌상단 노드 이름 → Tab 보기(게임 정지, 일시정지 일기장 없음, 방향키 둘러보기) → Tab 닫기·재개 → Esc 닫기·재개(일시정지 없음) → Tab `defaultPrevented` → `ROUTE_CHOOSE_OPEN` 고르기(↓ 이동, Esc 무시, Enter → b1, 지도 닫힘) → 안전망 재열기 → 잠긴 노드 클릭 무시 → 마우스 클릭 → b1 → 노드 진입 배너 → 층 배너 → 노드 배너 차례 → 탄생(HUD 숨김·안내만·Tab 무시·자막 미룸) → 끝(HUD 복귀·자막) → 일시정지 첫 줄·'Tab 지도' → 2층 강조색 → route null(방 미니맵·'Tab 워프'·워프 지도). 고르기 Enter·클릭 전후 `lastAttack` 변화 없음(대조: 평소 클릭은 변함). 콘솔 오류·경고 0, HTTP 4xx 0.

---

## 47라운드 (2026-10-02) · 상호작용 구조물 UI
결정: `decisions/2026-10-02-round-47-structures-impl.md` (Q5 E·C3 2초 누르기, Q7 안내는 UI, Q16 미니맵 점 1개, Q17 문구 자리표시, Q18 임시값). 계약: `contracts/ui-system-interface.md` **§9** (승인 #14) — `UiSnapshot.interactable/statuses`, `UiRoom.structureDot`, 구조물 메뉴 id 6종·`cancelKey`·`structureId`, `STRUCTURE_RESULT`·`CHALLENGE_STARTED`·`CHALLENGE_CLEARED`. 그 외 시스템 코드 열람 없음.
문구는 시스템이 준 문자열 그대로 그린다(계약 §9.8). UI 가 만든 것은 키 틀·초 표시·닫기·범례·조작법 덧붙임뿐(`text.ts STRUCT_TEXT`, 텍스트 팩 `hud.<키>` 우선).

### 화면
- **상호작용 안내** (`StructureHud.ts InteractBubble`, HUD depth 40 — 자막 50 아래): `interactable` 이 있으면 `screen`(구조물 윗변 중앙) 위 6px 에 작은 `panel_ink` 말풍선, 화면 여백 8px 안으로 자름.
  1줄 이름(ink_faint) · 2줄 '[E] 행동'(ink_body) + '· 비용'(ink_accent, `affordable=false` 면 ink_faint α0.55) · `usable=false` 면 3줄 `reasonText`(ink_accent)·행동 줄 ink_faint · `hold` 가 있으면 키 틀 '[E 2초]' + 아래 3px 게이지(G03 바탕, 층 강조 22 채움, `progress`).
  메뉴·일시정지·결과·워프 지도가 떠 있거나 `snapshot.menu` 가 있으면 숨김. 빈 값(null)이면 아무것도 그리지 않음.
- **HUD 상태 칩** (`StatusChips`, depth 45~47): 좌상단 층 제목 아래(y 34부터) 세로 목록. 칩 = `panel_ink` 높이 24 + 왼쪽 3px 종류 띠 + label(ink_faint) + value(ink_body, debuff 는 ink_accent). `remainMs/durationMs` 가 있으면 칩 아래쪽 2px 바가 줄어든다(매 프레임). 아이콘·detail 없음.
  종류 색(팔레트 안, 유채색은 현재 층 램프만): buff 강조 23 · debuff 강조 19 · resource S5 · timer 강조 25 · rule G11 · progress S4.
- **결과 토스트** (`ResultToasts`): `STRUCTURE_RESULT.text` 를 우하단(공지 패널 위 y≤492, 폭 ≤216 — 하단 HUD 묶음 오른쪽 빈 자리)에 아래→위로 쌓음. 2.6초 뒤 0.3초 사라짐, 최대 3개(넘치면 오래된 것부터). tone 별 띠 색: gain 강조 23 · loss 강조 19 · mixed S5 · warn 강조 25(글자 ink_accent) · info G11(글자 ink_faint). `deltas` 는 그리지 않음(골드·HP 는 기존 HUD 수치가 바뀜).
- **도전 판** (`ChallengePanel`): `CHALLENGE_STARTED` → 상단 가운데(y 34) `panel_ink`: label(ink_accent) / goal(ink_body), `timeLimitMs` 가 있으면 오른쪽 남은 시간 '15.7초'(Galmuri11 ×2) + 아래 줄어드는 바(강조 25). 남은 시간은 `statuses` 의 `ring.remainMs` 가 있으면 그것, 없으면 시작 시각 기준. `CHALLENGE_CLEARED` → 결과 문구(clear·flawless ink_accent, timeout ink_faint) 2.8초 뒤 사라짐. 층 시작·런 종료 때 지움.
- **구조물 메뉴** (`MenuScene`): 기존 일기장 한 페이지 그대로. `cancelKey` 가 있으면 **Esc** 와 페이지 오른쪽 위 **'Esc 닫기' 버튼**(Container → Graphics → 글자, 호버 시 테두리 층 강조 20)이 `select(id, cancelKey)`. '0' 키는 목록 줄로 그대로 동작.
  같은 id·structureId 로 `MENU_OPEN` 이 다시 오면 **커서 자리를 지킨 채** 다시 그린다(전당포·카운터 반복 선택). 비활성 줄은 기존 규칙(흐림 + '(불가)', 이유는 detail).
  **`cards`(패 탁자)**: 그만두기 외 줄이 2~4개면 엎어진 패로 그린다 — 카드 104×140(S1 바탕, S2 45° 격자, S4 안쪽 테, 가운데 '?' ×2, 왼쪽 위 '[1]'), 아래 label/detail. 고른 카드는 층 강조 20 테두리 2px + 4px 들림. 1·2·3 즉시, ←→/A·D 이동, ↓ 그만두기, Enter/Space 확정, 클릭. 아래 '[0] 그만둔다' + 조작 안내(page_faint).
  안전망: 구조물 메뉴 `MENU_OPEN` 뒤 60ms 에도 메뉴 씬이 없고 스냅샷 `menu` 가 같은 id 면 HUD 가 직접 띄운다(시스템이 띄우는 것이 기본).
- **미니맵 점** (`Minimap`): `structureDot` 인 **방문한 방**의 가장 위 줄 오른쪽 칸 바깥 모서리에 2×2 점(층 강조 25, 글리프 위). 미방문 방은 기존 규칙대로 그리지 않으므로 점도 없음.
  **워프 지도** (`WarpMap`): 같은 방 칸 오른쪽 위에 4×4 점 + 범례 한 줄 '쓸 것이 남은 곳'(오른쪽 칸 높이 +18).
- **조작법 줄** (`text.ts controlsLine`, 일시정지·타이틀): 텍스트 팩(또는 기본) 줄에 'E ', 'Shift', 'Tab' 이 없으면 ' · E 상호작용 · Shift 달리기 · Tab 워프' 를 덧붙인다(팩 `hud.controlInteract`/`hud.controlSprint`/`hud.warpKeyHint` 우선, 팩 줄에 이미 있으면 덧붙이지 않음).

### UI 디버그 경로 (`debug.ts`, 주소에 `uidebug=1` 일 때만)
`window.__lopadUi.patch(p | s => p)` 로 STATE 스냅샷 위에 가짜 값 덮어쓰기, `emit(이벤트 이름, 페이로드)`, `openMenu(menu)`/`closeMenu()`(가짜 메뉴의 선택은 시스템으로 보내지 않고 `selects` 에 기록). 시스템 값이 비어 있을 때 화면 확인용. 꺼져 있으면 영향 없음.

### 소유 코드 추가·변경
| 파일 | 내용 |
|---|---|
| `StructureHud.ts` (신규) | `InteractBubble`, `StatusChips`, `ResultToasts`, `ChallengePanel`, `swatch()`(팔레트 참조 → 색) |
| `structView.ts`, `structView.test.ts` (신규) | 순수 계산: 조작법 덧붙임, 말풍선 위치 자르기, 타이머 비율, 초 표시, 카드 포커스 이동 (테스트 8개) |
| `debug.ts` (신규) | `uidebug=1` 가짜 스냅샷·이벤트·메뉴 |
| `HudScene.ts` | 위 조각 생성·갱신, 결과·도전 이벤트 구독, 구조물 메뉴 안전망, 디버그 설치 |
| `MenuScene.ts` | Esc·닫기 버튼 → cancelKey, 커서 유지, `cards` 카드 화면 |
| `Minimap.ts`, `WarpMap.ts` | 구조물 점 (+ 워프 지도 범례) |
| `widgets.ts` | `SelectList.cursorIndex()/setCursorIndex()` |
| `text.ts` | `STRUCT_TEXT`·`structText()`, `controlsLine` 덧붙임 |
| `theme.ts` | `STRUCT` 수치·색 참조 (임시값) |

### 임시값 (도영 님 검토 대상)
- 문구: '[E]' / '[E 2초]' 키 틀, 'Esc 닫기', 카드 뒷면 '?', 카드 안내 '1·2·3 또는 ←→ 고르기 · Enter 뒤집기 · 0·Esc 그만두기', 범례 '쓸 것이 남은 곳', 남은 시간 '{sec}초', 조작법 덧붙임 'E 상호작용'·'Shift 달리기'·'Tab 워프'.
- 수치: `theme.ts STRUCT` 전부 (말풍선 여백 6·간격 6·화면 여백 8, 게이지 3px, 칩 높이 24·간격 2·띠 3·바 2·시작 y 34, 토스트 2600ms·최대 3·폭 216, 도전 판 y 34·결과 2800ms, 미니맵 점 2px·워프 점 4px, 카드 104×140·간격 20, 종류·tone 색).

---

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
