# 게임 시스템 파트 — 구조 문서

LOPAD 게임 코드(Phaser 3 + TypeScript + Vite)의 **현재 구조**: 폴더별 책임, 데이터 파일, 계약 연결, 디버그 훅, 검사 방법.
라운드별 작업·검증·임시값 기록은 [`CHANGELOG.md`](CHANGELOG.md)(옛 README 전체 + 새 기록)에 있다. 이 문서는 구조가 바뀔 때만 고친다.

- 소유: `src/**`(단 `src/ui/**` 제외) · `data/**` · `public/**` · 빌드 설정 · `parts/system/**` (루트 `CLAUDE.md` §2)
- 규약: `.claude/skills/phaser/` (EventBus · GameState · Constants · shutdown 정리 · 데이터 주도)
- UI 경계: 계약 `parts/producer/contracts/ui-system-interface.md` ↔ 코드 `src/contract/ui.ts` (UI 는 이 파일과 phaser 만 import — ESLint 로 강제)

## 1. 실행 · 검사

| 명령 | 용도 |
|---|---|
| `npm run dev` | 개발 서버 (`/assets-game/` = `assets/**`, vite 플러그인) |
| `npm run build` | 배포 빌드 (`dist/`, `assets/**` → `dist/assets-game/`, `data/buildExclude.json` 패턴은 제외) |
| `npm run typecheck` · `npm run lint` · `npm test` · `npm run format:check` | 검사 4종 (모두 통과가 커밋 조건) |

자주 쓰는 주소 옵션(`scenes/game/shared.ts urlParams`): `?debug=1` 디버그 훅 · `?new=1&seed=<s>&weapon=<id>` 새 런 바로 · `?lab&weapon=<id>[&branch=<1차 노드>,<2차 노드>]` 무기 시험장 · `?boss`·`?bossPhase=n`·`?bossPattern=a,b` 1층 보스 · `?nobossintro` 보스 등장 연출 생략 · `?slice=<지역>` 지역 전투 노드 · `?nobirth` 탄생 연출 생략 · `?resetmeta` 메타 초기화. 주소에 옵션이 없으면 해시 한 단어(`#lab` 등)를 옵션으로 읽는다. 층 이동은 디버그 `__lopad.gotoFloor(n)`.

## 2. 부팅 흐름

`main.ts` → Phaser.Game(`config.ts`) → `installContractHost`(계약 명령 구현) → `audio.attach` → `settings.load`(계약 §15 설정 적용) → `runLogRecorder.attach`(런 로그) → `installBootDebug`(`?debug`).
씬: `Boot` → `Preloader`(매니페스트 → 시트·타일셋·외벽·음향 JSON → 그림·소리, 부팅 묶음만 — 무기 묶음은 Game preload, 61 단계 2: 보스 묶음은 보스 노드 Game preload, 61 E: 노드 종류별 묶음 올리고 내리기 `sprites/lazySheets.prepareNodeSheets`) → UI 타이틀 / `Setup`(시작 의식 — 무기 고르기) / `Game`(런) / `WeaponLab`(Game 의 시험장 모드) / `GameOver`(UI 결과 화면이 없을 때의 임시 화면).

## 3. 폴더별 책임

### `src/core/`
- `EventBus.ts` — 시스템 내부 이벤트(`domain:action`)와 페이로드 형식. UI 로 가는 이벤트는 따로(`contract/ui.ts uiBus`).
- `GameState.ts` — 런 상태 싱글턴(`startRun`·`applySave`·`toSave`·층 이동). 메타 보너스는 시작 때 읽음.
- `Constants.ts` → `constants/*` 도메인별(display·colors·assets·world·feel·enemy·player·scenes·boss·bossArt·moves·build·bundle·settings). 엔진·연출 값은 여기, 게임 수치는 `data/*.json`.

### `src/contract/` (UI 경계)
- `ui.ts` — 계약 본문(이벤트·스냅샷·메뉴·명령). UI 가 import 하는 유일한 시스템 파일.
- `host.ts` — 명령 구현(일시정지·새 런·이어하기·타이틀·노드 선택·음소거·시험장·설정). `snapshot.ts` — 스냅샷 조립.

### `src/data/` (데이터 로드·검증 — 수치는 `data/*.json`)
- `index.ts` — JSON 로드 + 검증(`validate*`) → `PLAYER_DATA`·`ENEMIES`·`BOSSES`·`STAGES`·`RUN`·`WEAPONS`·`ECONOMY`·`STORY`·`PALETTE`·`LIGHTING` …
- 형식: `types.ts`(공통) · `comboTypes`(연격) · `moveTypes`(기본기) · `weaponKitTypes`(무기 자원·고유 자원) · `buildTypes`(빌드 축) · `bundle2Types`(2차 묶음). 검증: `validateCombo`·`validateMoves`·`validateWeaponKit`·`validateUtil`. `bossPatterns.ts` = 보스 패턴 이름·수치 형식의 단일 출처.
- `floorScope.ts` — **층 노출**(61 P4·P5): 항목 `floor` = 처음 켜지는 층, `gameState.build.floor`(시험장 null). `narrative.ts` — 서사 문장(story.json clues·weaponVoice·boss1·nameSmudge)·배치(narrative.json).
- `scope.ts` — **로드 범위**(`stages.json` run.`loadFloors`, 61라운드: 1층만). 범위 밖 층의 데이터는 남기고 부팅 그림(보스 시트·층 타일셋)만 뺀다.

### `src/scenes/`
- `Game.ts` — 런 씬 생애주기만(모듈 생성 → 런 준비 → 노드 진입 → 월드 → 플레이어 → 풀·연출 → 물리 배선 → 방 상태 머신 → 구조물 → 계약 연결 → 디버그 → 이벤트 표). 실제 일은 `scenes/game/*` 모듈:
  - 진행: `Progression`(런 시작 모드·세이브·처치 → 각성 게이지·스테이지 보상·엔딩·사망·정산·결과) · `growth/GrowthFlow`(61 G P12 무기 성장 — 게이지 적립·눈금 메뉴(개성 발현·1차/2차 각성·단련)·처음 안내 기록·시험장 조작·스냅샷 `growth`) · `BossFlow`(61: 보스 등장·처치 연출 시간표 · 보스 대사 · 보상 미루기 — 데이터 `bosses.json show`·`linesKey`; 61 E: 등장 동작 `BossIntroArt` · 결정타·쓰러짐 파편·불 끄기 `BossFinale`) · `RouteFlow`(노드 진입·클리어 → 출구 → 노드 선택·전환) · `BirthFlow`(탄생 연출) · `LabMode`(무기 시험장) · `Economy`(드랍·상점, 61: 상점 상인 `ShopKeeper` E) · `directorHost`(방 상태 머신 생성)
  - 전투: `GameCombat`(피해 계산 `rollDamage`·적 피격 공통 경로 `hitMob`·접촉·투사체) · `PlayerStrikes`·`MoveStrikes`·`IssenStrikes`·`CrackLineStrikes`·`BowShots`·`ArrowRain`·`BrandMarks`·`StrikeSchedule`·`StrikeDots`
  - 연출: `SwingFx`·`MotionFx`·`WeaponFeedback`·`FxWiring`·`GameCamera`·`swingShake`·`bladeTip`·`HitShapeOverlay`·`AnchorDebug`
  - 빌드 축 `build/*`(BuildRuntime·BuildCombat(+`combat/*`)·BuildMenus(패시브·저주)·BuildEffects·BuildDefense·BuildPerfect·AwakenFlow(각성 연출·외형·지연 로드)·BuildArt, 무기별 갈래 `branch/*`, 개성 카드·셋째 갈래 규칙 `traits/*`(TraitRules 창구 + RuleKit + 무기별 Katana/Greatsword/Dagger/BowRules)) · 2차 묶음 `bundle/*`(BundleRuntime·NodeFlow·EventNode·BossBreaks·EliteSystem(+EliteArt)·Consumables·ShopMenu·BundleProps·bundleRewards)
  - 서사: `story/StoryBeats`(61 P8 서사 소품·무기 한마디·일기장 — BundleRuntime 이 만든다)
  - 계약·디버그: `UiRelay`(스냅샷·자막·UI 중계) · `DebugHooks`(+`debug/combatDebug`·`worldDebug`)
- `Setup.ts` — 시작 의식(이름 → 3획 → 회피 시험 → 운명). `Preloader.ts` — 부팅 로드. `WeaponLab.ts` — 시험장 씬 키.

### `src/objects/`
- `Player.ts` — 상태 머신(이동·달리기·대쉬·연격 입력·피격) + `player/*`(MeleeDriver 연격 · SecondaryDriver 우클릭 · BasicMoves/BranchMoves·무기별 moves 기본기 · PlayerDefense 피격·가드·패링 · PlayerGauges 고유 자원 · PlayerGear 무기 자원·휴대 · PlayerPoses 자세 · ScarOverlay 등 상흔).
- `GrowthOverlay`(61 G 각성 외형 a1·a2·a2_glow — WeaponOverlay 가 쓴다)
- `Mob.ts`(적·보스 공통 바탕) · `Enemy.ts`(일반 적 행동: 추격·사격·돌진·방패·집단 돌격 · 61: 독주 행상·술통 짐꾼은 `enemy/hazardBrains`) · `Boss.ts` + `boss/*`(패턴 상태 머신, `boss/patterns/*` 패턴별) · `Projectile` · `Pickup` · `LabDummy` · `EntityVisual`(시트 애니·그림자·시체) · `WeaponOverlay`(무기 오버레이).

### `src/systems/` (Phaser 의존을 줄인 규칙·계산 — 대부분 단위 테스트가 붙어 있다)
- 런·진행: `route`(노드 지도 생성·검증, 61: 단마다 종류·웨이브 `columns`·`nodeWaves`) · `routeArena`(노드 전투장, 61: 방 다양화 `arenaVariety`·세트 후보 `pickSetPiece`·소품 장면 `pickPropScene`) · `enemyIntro`(새 적 소개) · `RoomDirector`(방 상태 머신·웨이브) · `save`(런 세이브 `lopad.save`) · `meta`(메타 세이브 `lopad.meta`: 영혼·강화·도감·**설정·런 로그**) · `personality` · `passives` · `senses` · `economy` · `story` · `tutorial`/`tutorialDirector` · `birth` · `traversal` · `TextMenu`(메뉴 브로커)
- 근접 판정(61 단계 4): 방향 = 판정 원점(발 위 가슴)에서 커서로 · 맞음 = 바디에서 그림 몸통 중심까지(`weapon/hitShapes.shapeHitBody`) · 단검 가속 그림만큼 찌르기 길이(`reachMult`)
- 전투 감각: `feel`(히트스톱·흔들림·넉백·`feelSettings` 배율) · `hitFeel` · `Combat`·`defense` · `packCharge` · `weapon/*`(연격·판정 모양 `hitShapes`·자원·고유 자원·활 당김·4동사 `verbs` 등) · `telegraph/*` · `hazards/*`(술 웅덩이 `LiquorPools` · 61 신규 적 위험물 `EnemyHazards` — 화염 술병·술통 굴림·되치기, 계산 `hazardMath`) · `boss/*`(보스 전장 `BossArena` — 61 단계 4: 소등(등불 끄기·처치 때 불 끄기·림)은 `arenaDarkness`·불타기·'세상이 돈다' `drunkScreen` · 61 E: 약점 잔 `cupWeakPoint`·기둥 균열 `pillars`·파훼 고리 `breakDaze`·소등 림 `bossRim`(원 림 / 가벼운 림 `_rim_lite` / tintFill — `bossVram.rimKind`)·보스방 VRAM 지연 로드 `bossVram`·로드 묶음 `bossSheets`·등장 시간표 `introArt`·순수 규칙 `bossArtRules`)
- 무기 성장 `growth/*`(61 G P12 — 눈금 `growth`·메뉴 `growthMenu`·스냅샷 `uiGrowth`) · 빌드 축 `build/*` · 2차 묶음 `bundle2/*` · 구조물 `structures/*`(StructureSystem 창구 + core·kinds·interact·placement·setpiece)
- 그림·소리: `sprites/*`(시트 경로·로드 묶음 `sheetSets`·애니 등록 · 61 E 노드별 묶음·씬 도중 로드/해제 `lazySheets`) · `fx/*`(FxPool·섬광 `screenFx`·피해 숫자·리본·잔상 · 씬 종료 중 반납 검사 `fxRelease` · 피해 숫자 합치기/비켜 띄우기 `damageNumberLayout`) · `lighting/*` · `strokeFx/*`(3획 연출) · `dodgeTrial/*`(회피 시험) · `audio/*`(오디오 매니저 `audio` · 이벤트 → 효과음 표 `audioMap`·`audioBuild` · 61 믹싱 규칙 `audioMix`·목소리 상한/덕킹 `audioVoices`·층 BGM 지연 로드 `audioLazy`) · `palette` · `display`(1920×1080 캔버스·논리 960×540) · `fonts`
- 61라운드 도구: `settings`(계약 §15 설정 적용·저장) · `runlog/*`(런 로그) · `sim/*`(헤드리스 수치 추정) · `vram`(텍스처 VRAM 추정)
- 기타: `mapgen/*`(방+복도 층 — 노드 지도 이전 층 형식) · `setup/*`(개성 선택 계산) · `rng` · `mathUtil` · `keyEvents` · `InputSystem`

### `src/world/`
- `TileWorld`(타일맵·문·출구) · `QuarterView`(쿼터뷰 벽) · `tileskin`(타일셋 해석) · `border`/`BorderView`(외벽 테두리, 지역 노드 진입 때 지연 로드) · `bigProps*`(큰 소품 배치) · `SetPieceView`·`StructureView` · `floorFeatures` · `quarterScale`(64도트 = 1칸 환산)

### `src/debug/`
- `index.ts` — `?debug=1` 이면 게임 씬이 `window.__lopad` 를 만든다(상태·이동·적·보스·구조물·노드·무기·빌드·묶음 조회와 조작).
- `boot.ts` — 씬과 무관한 훅(타이틀부터): `__lopad.runlog.dump()`·`runlog.clear()` · `__lopad.vram()` / `vram({ all: true })` · `__lopad.settings()`·`setSettings({...})`.
- `bossQuery.ts` — `?boss…` 주소 옵션. 보스 연출 상태는 `__lopad.boss.flow()`.

## 4. 데이터 파일 (`data/*.json`)

| 파일 | 내용 |
|---|---|
| `player.json` | 기본 능력치·대쉬·패링·달리기·피격 무적 |
| `weapons.json` | 무기 4종(연격·우클릭·4동사·자원·고유 자원·갈래 트리 — 1차 갈래 3 × 2차 길 2) + 규칙 |
| `growth.json` · `traits.json` | 61 G P12 무기 성장: 눈금(1층 30/90/150/220/290 + 70마다 단련)·획득 배율·단련·연출 · 갈래·길(art §26 id ↔ 노드 id, 이름·한 줄·바뀌는 칸·길 색) / 개성 카드 56 (무기당 기본 8 + 갈래마다 2) |
| `enemies.json` · `bosses.json` | 적 5종(61: 독주 행상 `throw`·술통 짐꾼 `roll` — 형식 `src/data/enemyTypes.ts`, 소개 문구 `intro`) · 층 보스(1층 '만취' 3국면 패턴 · 61: 그림 배율·시작 자리·파훼 피해 배율·등장/처치 연출 `show`·대사 키 `linesKey`·소등 광원 `arena.darkLights`) |
| `stages.json` | 층 순서·세이브 횟수·**로드 층 수(`loadFloors`)** · 층별 적 배율·웨이브 |
| `route.json` | 노드 지도(층 여정·갈래·노드 종류·지역·세트 배치·튜토리얼 · 61: 1층 `columns` 단별 종류·웨이브, `arena.variety` 방 다양화, 전투 세트 후보 `setPieceVariants`) |
| `structures.json` | 상호작용 구조물 |
| `economy.json` · `meta.json` | 드랍·상점·능력치 보상 · 영혼·영구 강화 |
| `personality.json` | 개성 선택 의식 가중 |
| `build.json` · `passives.json` · `curses.json` | 빌드 축(태그·세트·패시브·저주 — 61 G: 이중 개성·최종 각성 파일 폐지) |
| `bundle2.json` | 2차 묶음(노드 보상·위험·이벤트·숨은 노드·상점·성소·등급·엘리트·파훼·소모품) |
| `story.json` | 문구(스토리 파트 텍스트 팩 — 61: 단서·무기 한마디·만취 대사·이름 번짐) |
| `narrative.json` | 61 서사 연결 수치·서사 소품 배치·시작 의식 문구 |
| `palette.json` · `lighting.json` | 층 램프 · 동적 조명 |
| `buildExclude.json` | 배포 빌드에서 뺄 에셋 경로 패턴(원본 보관) |

## 5. 세이브

| 키 | 모듈 | 내용 | 수명 |
|---|---|---|---|
| `lopad.save` | `systems/save` | 층 전환 세이브(런당 최대 2회, v6 — 무기 성장 게이지·경로·개성·단련·눈금) | 사망·클리어·새 런에 삭제 |
| `lopad.meta` | `systems/meta` | 영혼·강화·도감·엔딩 기록 · `settings`(계약 §15) · `runLogs`(최근 20런 요약) · `diary`(61 일기장 이력 — `systems/narrative/diary`) | 영구 (`?resetmeta` 로 초기화) |
| `lopad.mute` | `systems/audio` | 빠른 음소거 | 영구 |

## 6. 61라운드 밸런스·성능 도구 사용법

- **런 로그**: 데모 플레이 뒤 `?debug=1` 로 열고 `__lopad.runlog.dump()` → `saved`(끝난 런들) · `byKind`(노드 종류별 평균 시간·처치·피격·피해·메뉴) · `current`(진행 중).
- **수치 추정**: `npx vitest run src/systems/sim --silent=false` → 무기 4종 DPS 와 1층 길 3종(전투 많음·보통·적음)의 노드별 시간·처치·받는 피해. 보스 싸움 길이는 `sim/bossSim.ts`(파훼 피해 창·활 공격 비율 — `bossSim.test` 가 4무기 90~120초를 지킨다). 가정값은 `core/constants/settings.ts SIM`.
- **VRAM**: `__lopad.vram()` → `mb`(고유 텍스처 추정 합) · `over4096` · `top` · `byGroup` · `dupImages`. 목표 런당 500MB 이하(61 P9). 보스방은 `__lopad.boss.arena().vram`(지연 로드 기록·최고값 — 61 E 묶음 나눔은 CHANGELOG 61 E 절).

## 7. 61라운드 단계 4 무기 성장 (P12 · 계약 UI §18 · art §26 · sound §10)

| 어디 | 무엇 |
|---|---|
| `data/growth.json` · `data/traits.json` → `src/data/growth.ts` | 눈금·갈래·길·개성 검증 (화면 문구에 숫자 금지 `plainLine`) |
| `systems/weapon/weapons.ts WeaponState` | 게이지(누적)·경로(노드 id)·개성·단련·처리한 눈금 · `branchId`/`pathId`(art id) |
| `systems/growth/*` | 눈금 목록·대기 눈금·종류 보정 · 개성 풀/제시(갈래 개성 우선 1장) · 메뉴 줄 · 스냅샷 · 외형(`growthLookOf`) |
| `scenes/game/growth/GrowthFlow` | 적립(`Progression.gainGrowth`)·메뉴·적용·이벤트·처음 안내(메타 `diary.guides`)·미리보기 그림(`sprites/looks`) |
| `scenes/game/build/AwakenFlow` | 정지 0.8/1.0초 + `fx/v4/awaken1_crack`·`awaken2_bloom`(swapFrame 에 새 외형) · 고른 갈래·길만 지연 로드 · 2차 궤적 색 |
| `scenes/game/build/traits/*` | 개성 카드·셋째 갈래(만월·광전·백귀·유성 계열) 규칙 실행 |
| 이벤트 | 시스템 `GROWTH_GAINED`·`GROWTH_MARK`·`TRAIT_GAINED`·`WEAPON_AWAKEN`·`WEAPON_TEMPERED` / UI `ui:growth-gain`·`ui:awaken`·`ui:trait-gained` |
| 디버그 | `__lopad.growth()` · `setPersonality(v)`(게이지를 v 까지) · `evolveTo(노드 id)` · `build.trait(id)` · `build.openEvolveMenu()`(다음 눈금까지) · 시험장 L → 갈래·게이지 |

## 8. 61라운드 무기 4동사 (구조)

모든 무기: **좌 = 연격 · 우 = 시그니처 · Space = 대쉬(+대쉬 직후 좌 = 대쉬 공격) · 좌 홀드 = 고유 자원 기술**. 1단 갈래는 이 넷 중 한 칸의 기술을 '바꾼다'(같은 계기의 기본 동작을 대신). 결정 이유·수치 표는 `CHANGELOG.md` '61라운드 무기 4동사' 절.

| 어디 | 무엇 |
|---|---|
| `data/weapons.json` `verbs` · 갈래 노드 `verbs` | 4칸 표시 이름·설명 (키캡 문자열은 `core/constants/player.ts VERB_KEYS`) |
| `systems/weapon/moves.ts` | 동작 표(`verb`·`trigger`) · `availableMoves`(갈래가 같은 계기 기본 동작을 뺀다) · `pickMove` |
| `systems/weapon/verbs.ts` | 스냅샷 `weaponVerbs`(계약 61 추가) · 시험장 한 줄 |
| `objects/player/BranchMoves.ts` `filter` | 칼 좌 홀드: 누름을 미뤘다가 문턱을 넘으면 발도(`BasicMoves.startIai`) 또는 선풍·투구가르기, 짧게 떼면 연격 |
| `objects/player/MeleeDriver.ts` | 대검 좌 홀드 = 차지(ChargeHold) · 대쉬 공격 자리(`BasicMoves.tryDashAttack`) |
| `objects/player/BasicMoves.ts` | 시그니처 후속(간파 반격·등 뒤 치명) · 단검 난타·활 화살비(좌 홀드) · 중압 버티기(막은 직후 우 뗌 — `SecondaryDriver.hold`) |
| `systems/weapon/dps.ts` + `dps.test.ts` | 기본 공격 지속 DPS 추정 · `weapons.rules.dpsBaseline` 대역을 테스트가 지킨다 |
| 이벤트 `PLAYER_HOLD_VERB` | 좌 홀드 기술이 나갔다 (튜토리얼 홀드 단계 · 런 로그 후보) |
| `parts/system/notes/weapons-history.md` | `weapons.json` 에서 옮긴 옛 `_note` 변경 이력 |
