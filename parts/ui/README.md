# 게임 UI 파트 — 작업 기록

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
