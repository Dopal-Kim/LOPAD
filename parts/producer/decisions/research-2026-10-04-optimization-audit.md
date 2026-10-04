> 57라운드 파일 최적화 점검(시스템 에이전트 보고 원문, 조사만). 결정은 `2026-10-04-round-57-systems-review.md`.

# 게임 시스템 파트: 파일 최적화 점검 보고 (조사만 함)

## (1) 수행한 작업과 변경 파일
- **저장소 파일은 하나도 바꾸지 않았습니다.** 분석용 스크립트와 빌드 결과는 모두 스크래치패드(`/tmp/claude-0/-home-user-LOPAD/a2d5d0a8-.../scratchpad/`)에만 만들었습니다. 저장소의 `dist/`도 다시 만들지 않았고, 시험 빌드는 스크래치 outDir로 돌렸습니다.
- 읽은 것:
  - 루트 CLAUDE.md, parts/system/CLAUDE.md, phaser 스킬(SKILL.md, conventions.md)
  - `src/**`(`src/ui/**` 제외), `data/**`, 빌드 설정
  - 승인 #8 범위의 시트 JSON과 `audio/manifest.json`. 저장소 `assets/` 대신 `dist/assets-game/` 복사본에서 읽었습니다.
  - PNG·WAV는 이미지 크기·포맷 메타데이터와 압축 시험에만 썼습니다.
- 분석 방법:
  - Preloader의 실제 로드 로직(wantedSheets → sheetJsonCandidates → manifest 필터 → JSON의 image)을 그대로 돌리는 스크래치 vitest를 만들었습니다.
  - 그 결과로 "부팅 때 로드되는 파일"과 "BorderView가 지연 로드하는 파일"을 계산해 dist 전체와 대조했습니다.
- 현재 상태:
  - `tsc` 통과 8.9초, `vitest` 74파일·562테스트 통과 9.4초, `eslint` 오류 없음 11초, `vite build` 16초
  - index 929KB(gzip 317KB), phaser 1.48MB(gzip 340KB), 500KB 청크 경고 있음

### 핵심 결론 (예상과 다른 점)
- **옛 v1/v2 시트는 이미 대부분 지워져 있습니다.** `sprites/*/v2/` 폴더는 비어 있습니다. 게임이 로드하지 않는 파일은 1696개 중 421개, 9.2MB(9%)뿐이고, 그중 시스템이 확실히 판정할 수 있는 건 약 0.9MB·310파일입니다.
- 105MB의 대부분은 **실제로 쓰는 파일의 포맷 문제**입니다. 외벽 PNG 45MB, 스프라이트 PNG 약 30MB, WAV 15MB입니다.
- **가장 큰 위험은 용량이 아니라 GPU 메모리입니다.** 부팅 때 PNG 537장을 RGBA로 풀면 **약 4.4GB**로 추정됩니다(이펙트 2.49GB, 무기 1.70GB).
  - 스프라이트 픽셀 중 불투명 픽셀은 **3.46%** 뿐입니다.
  - 4096px를 넘는 텍스처가 부팅분 16장, 외벽 10장입니다. 예: `fx/v3/greatsword_guard_rush.png` 5568×5376 한 장이 114MB, `katana_issen_line_t4` 7488×2496.
  - Phaser WebGL은 로드할 때 바로 GPU 텍스처를 만들기 때문에 부팅 시점에 다 올라갑니다. 다만 이 수치는 계산 추정이라 브라우저 실측이 필요합니다(Chrome 작업 관리자 GPU 메모리).

## (2) 항목별 표

### A. 에셋 로드·빌드

| # | 경로 | 문제 | 제안 | 절감·효과 | 위험도 | 소유 |
|---|---|---|---|---|---|---|
| A1 | `sprites/fx/v3`, `sprites/weapons/v3` 전체 | 부팅 VRAM 약 4.4GB 추정, 불투명 3.46%, 큰 프레임(대검 fx 696×672×8방향) | 시트를 **트림 아틀라스**로 변환(Phaser가 trim 오프셋을 자체 처리) | VRAM 수 GB → 수백 MB 추정, 요청 수도 감소 | 높음 (앵커·피벗 계약 변경, 도구 필요) | 아트+시스템 |
| A2 | `Preloader.ts` queueJsons | 고른 무기와 상관없이 4무기 시트를 모두 부팅 때 로드. 무기는 런마다 고정(GameState.startRun) | 무기 시트를 런 시작(Setup → Game) 때 그 무기만 지연 로드. 시험장은 바꿀 때 로드 | 대검 런 약 2.75GB, 칼 약 1.0GB, 단검 약 0.32GB, 활 약 0.08GB, 공용 약 0.3GB. 칼·단검·활 런에서 VRAM 크게 감소 | 중 | 시스템 |
| A3 | 고유 자원 오버레이 `*_ki1~3`, `*_grudge1~3` | 불투명 0.18%인데 VRAM 약 1.1GB(대검 0.92GB) | A1 트림, 또는 오버레이 방식 재검토(아트 결정) | 약 1GB | 중 | 아트 |
| A4 | `tiles/border/**` 45MB, 84파일 | 전부 쓰이지만(지연 로드) PNG가 너무 큼. `outer/north.png` 6214×818 하나가 5.3MB. 가로가 4096을 넘는 파일 10개 | WebP로 전환. 표본 8장 기준 무손실 −31%, 손실 q90 −93%, 256색 팔레트 −90% | 45MB → 약 31MB(무손실) 또는 약 3~5MB(손실) | 중 (그림 품질 판단, 4096 초과는 일부 GPU에서 깨짐) | 아트 |
| A5 | 스프라이트 PNG 약 30MB | PNG는 이미 최적화돼 있음(재압축 이득 0%) | 무손실 WebP. 상위 25장 표본 −56% | 약 −15MB | 낮음~중 (로더 확장자만 바꾸면 됨) | 아트(+시스템 로더) |
| A6 | `audio/bgm` 6개 7.7MB, `audio/sfx` 105개 6.6MB | WAV. BGM은 22kHz 모노 30초 루프 | OGG Vorbis q4로 시험: BGM 8.0→1.0MB, SFX 6.9→1.0MB. Safari 대비 m4a/mp3 대체 경로 필요 | 약 −13MB (−87%) | 중 (루프 이음매 확인 필요) | 음향 |
| A7 | 미사용 레거시 `sprites/fx/*.png·json` 루트 226개(`concept_*` 포함) | 0.72MB | 빌드 복사에서 제외, 원본 삭제는 제안만 | 0.72MB, 226파일 | 낮음 | 아트 |
| A8 | 미사용 `sprites/weapons/` 루트 62개 | 옛 `*_combo1~3`, `carry_*`, `icon` 등 | 같은 처리. 단 `dagger_attack`, `greatsword_attack` 루트 2벌은 **아직 로드 중**이라 남김 | 0.09MB | 낮음 | 아트 |
| A9 | 미사용 `sprites/bosses/stage1_*` 루트 10개, `tiles/stage1_<지역>.*` 루트 10개(v2로 대체됨), `sprites/structures/set_outer_stall_side.*` | 미사용 | 같은 처리. emperor 루트 시트와 `tiles/stageN.*`는 사용 중 | 약 0.05MB | 낮음 | 아트 |
| A10 | `sprites/ui/**` 48개 3.35MB | 아트 원본. 승인 #10으로 `ui/kit`에 복사본이 있고 23개가 해시까지 같음. keyart, map_bg도 중복. 시스템은 로드하지 않음 | 빌드에서 제외. UI 코드가 읽는지 확인 필요 | 3.35MB, 48파일 | 낮음 (UI 확인 후) | 아트/UI |
| A11 | `ui/keyart` 2.7MB, `ui/fonts`(Galmuri9/14/Bold) 1.6MB, `ui/map_bg_1.png` | 시스템은 Galmuri11만 씀(`public/style.css`). 나머지는 UI 코드 사용 여부를 모름 | UI 쪽 확인 | 최대 약 4MB | 낮음 | UI |
| A12 | `vite.config.ts` gameAssets 플러그인 | `assets/**`를 통째로 `cpSync`. `.md` 4개와 manifest(65KB, 전체 1696파일 목록)도 같이 나감 | 복사·manifest에 필터 추가(제외 목록 또는 Preloader 로직 기반 사용 집합). 빠뜨림 방지 테스트도 함께 | A7~A10 합계 약 4.3MB, 약 360파일(1700 → 약 1340) | 낮음~중 | 시스템 |
| A13 | 부팅 요청 수 | 부팅 때 파일 약 1190개(시트 JSON 약 540 + PNG 537 + WAV 105). JSON 요청 후보 916개 중 519개 적중 | 빌드 때 시트 JSON을 묶음 하나로 합치고 Preloader가 그것 하나만 읽게 | 요청 약 540개 감소 | 중 | 시스템 |
| A14 | `SHEET_TIERS`의 v2 단계 (`spriteMeta.ts`, `Constants.ASSETS.V2_DIR`) | 스프라이트 v2 폴더가 비어 있어 죽은 후보 경로. 타일 v2는 사용 중이라 유지 | 스프라이트 후보에서 v2 제거 | 코드 단순화(성능 영향은 미미) | 낮음 (계약 art §11 경로 계층 문구와 연관) | 시스템 |

### B. 코드 (`src/**`, ui 제외, 297파일 · 약 5.7만 줄)

| # | 경로 | 문제 | 제안 | 효과 | 위험도 |
|---|---|---|---|---|---|
| B1 | 죽은 export: `Constants.CELL`, `Constants.RHYTHM_DOT`(16줄), `EventBus.EnemyDiedPayload`, `types.SecondaryKind`, `weapon56Types.WeaponGaugeKind`, `fonts.resetFonts`, `fx.baseFxAnimKey`, `mapgen.renderAscii`, `mapgen/types.DIR_OPP`, `moves.moveById`, `setup/autoStrokes.AUTO_PRESETS`, `strokeFxPaint.glowDot`, `weaponResource.isAmmo` | 어디서도 안 씀(테스트 포함). UI는 ESLint로 `contract/ui.ts`만 import할 수 있어 판정이 유효함 | 삭제 | 소량 정리 | 낮음 (기계적) |
| B2 | 리듬 잔재: `personality.ts` `rhythmFeatures`, `RhythmSample`(테스트만 사용), `data/personality.json` `rhythm`, `weights.key*`, `weapons.json` `affinity.key*` | 49라운드부터 무기 결정에 쓰지 않음. 주석에 "호환용 유지"라고 적혀 있음 | 코드·데이터·타입·테스트 함께 제거 | 개념 정리 | 낮음 (그러나 49라운드 결정이 '유지'였으므로 인터뷰) |
| B3 | `SecondaryDriver.releaseLegacy`(옛 조준 사격) | 활에 `draw` 데이터가 있어 지금 데이터로는 닿지 않는 경로 | 제거하거나 그대로 둠 | 약 15줄 | 낮음 |
| B4 | 반복되는 작은 함수: `clamp01` 4곳(dodgeTrialArena, personality, strokeFxMath, weaponResource), 검증 `num`/`str` 3벌(validate56, validateMoves, validateCombo), `border.ts`와 `tileskin.ts`의 `num` | 중복 | `systems/mathUtil.ts`, `data/validateUtil.ts`로 공통화 | 소량 | 낮음 (기계적) |
| B5 | `src/systems/` 단일 폴더에 134파일 | 책임 묶음이 섞여 있음: strokeFx 7, dodgeTrial 10, audio 5, fx 계열 약 10, 무기 기술 수학 약 12, sprite 3 | 하위 폴더 `fx/`, `strokeFx/`, `dodgeTrial/`, `audio/`, `weapon/`, `sprites/`로 이동. import 경로만 바뀜 | 탐색성 향상 | 중 (넓은 diff, 다른 브랜치와 충돌) |
| B6 | `core/Constants.ts` 1042줄(FEEL 180, QUARTER 82, ENEMY_FX 65 …) | 비대함. 이미 `BossConstants`, `MoveConstants` 분리 선례가 있음 | `core/constants/` 아래 도메인별 파일로 나누고 `Constants.ts`는 재수출만 | 가독성 | 낮음~중 |
| B7 | `systems/spriteDefs.ts` 928줄, export 89개 | 동작 이름 표, 시트 JSON 타입, 경로, 애니 키, 단위 변환이 한 파일에 섞임 | `spriteActions.ts`, `sheetJson.ts`, `sheetPaths.ts`로 분리 | 가독성 | 중 |
| B8 | `systems/telegraph.ts` 746줄 (TelegraphFx 클래스 하나, 메서드 30개) | 원·선·부채꼴·경로·오라 그리기가 한 클래스에 모임 | 경로 표식과 도형 그리기를 분리 | 가독성 | 중 |
| B9 | 라운드 번호가 들어간 이름: `validate56.ts`, `weapon56Types.ts`, `weapon56.test.ts`, `fxContract55.test.ts`, `SFX56`(39회), `WEAPON_MOTIONS_56`, `sfx56Ids` | 의미가 아니라 시기로 붙인 이름 | 의미 있는 이름으로 변경(예: `validateWeaponKit`) | 가독성 | 낮음 (이름 선택이라 인터뷰) |
| B10 | 디버그 코드가 운영 번들에 포함: `debug/index.ts`(524줄), `scenes/game/DebugHooks.ts`(500줄), `WeaponLab` | 약 15~25KB (minified) | `import.meta.env.DEV` 또는 데모 플래그로 분리, 또는 동적 import | 소량 | 중 (데모 확인용 `?boss`, `?lab` 쿼리를 계속 쓸지에 달림) |
| B11 | `objects/boss/legacyRegression.test.ts`(563줄) + `__fixtures__/bosses.legacy.json`(538줄) | 54라운드 보스 모듈 전환 때 만든 회귀 고정 테스트 | 유지하거나 삭제 | 약 1100줄 | 낮음 (테스트 범위가 줄어듦) |
| B12 | `comboArt.legacyComboArt`, BowShots `legacyTail`, telegraph "옛 시트" 루프, MeleeDriver "step 없는 옛 대검" | 확인해 보니 **아직 쓰입니다**(단검 연격에 hitShape 없음, 시트가 없을 때의 폴백) | 유지. 단검 데이터가 새 형식으로 옮겨지면 함께 제거 | – | – |
| B13 | 내 파일 안에서만 쓰는 export 242개 | `export`가 불필요 | 일괄로 export 제거 (선택) | 미미 | 낮음 |
| B14 | 고아 모듈 | 없음 (확인 완료) | – | – | – |

### C. 데이터 (`data/**`, 14파일 · 137KB, 번들 안에서 약 93KB)
- 거의 깨끗합니다. stageN, rarity, art 키처럼 동적으로 접근하는 키를 빼면 쓰이지 않는 키는 다음뿐입니다.
  - B2의 리듬 잔재
  - `_note`, `_artNote`, `_note56`, `_tutorial`, `_borderRegions`, `_source` 같은 설명용 키
  - `palette.json`의 정보성 필드: `floors[].hue`, `sat`, `v_mid`, `romaja`, `gray_roles`, `total_slots` 등. 아트 팔레트 기록이라 번들 약 7KB를 차지합니다.
- `story.json`의 `ui.*` 문구(`title.newRun`, `pause.confirmQuit` 등 14개)는 시스템 코드에서 직접 참조하지 않습니다. UI 계약으로 전달되는지는 UI 쪽 확인이 필요합니다.
- 중복 정의는 찾지 못했습니다.

### D. 테스트·빌드·번들

| # | 항목 | 제안 | 효과 | 위험도 |
|---|---|---|---|---|
| D1 | `structures/placement.test.ts` 4.9초(전체 테스트 시간의 절반), `mapgen.test.ts` 2.1초 | 같은 시드·층의 `generateFloor` 결과를 파일 안에서 메모이즈 | 테스트 −4초 안팎 | 낮음 (기계적) |
| D2 | vitest 워커 74개 생성 | vitest가 직접 `isolate: false`를 쓰면 3.2초 단축된다고 알려 줌 | −3초 | 중 (전역 상태 누수 가능) |
| D3 | index 929KB 청크 경고 | `manualChunks`로 data와 ui를 별도 청크로(캐시 이득), 경고 한도 조정은 외형용 | 경고 해소, 코드만 바뀔 때 재다운로드 감소 | 낮음 |
| D4 | phaser 1.48MB | Matter 미사용이므로 `phaser-arcade-physics.min.js`(1.09MB) 별칭 검토 | 약 −0.4MB, gzip 약 −100KB | 중 (UMD 호환, UI도 영향) |
| D5 | 운영 번들의 런타임 데이터 검증(validate56 등 약 20KB) | 테스트·빌드 단계로 옮김 | 소량 | 중 (런타임 안전망이 사라짐) |

## (3) 바로 해도 되는 기계적 정리 vs 인터뷰 필요

**기계적(결정된 것의 수행·명백한 정리):**
- B1 죽은 export 삭제
- B4 중복 작은 함수 공통화
- D1 테스트 메모이즈
- A12 중 `.md` 파일 빌드 제외(LICENSE-OFL.txt는 OFL 라이선스 조건상 유지)

**인터뷰 필요 (메인 세션에서 도영 님께):**
1. A2: 무기 시트를 선택 무기만 지연 로드할지. 런 시작 때 짧은 로딩이 생김 (추천: 진행)
2. A1/A3: 트림 아틀라스 파이프라인 도입 여부와 도구. 선택지는 (a) 아트 파트 오프라인 Python 스크립트 (추천), (b) 빌드 단계 Node 의존성(sharp 등) 신규 도입. 아트 계약 §11 시트 JSON 형식 변경을 동반함
3. A12: 빌드 제외 방식. (a) Preloader 로직으로 사용 집합을 계산해 그것만 복사하고 테스트로 검증 (추천), (b) 수동 제외 패턴 목록. `sprites/ui/**` 제외 포함 여부
4. A13: 시트 JSON 묶음 빌드 도입 여부
5. A4/A5/A6: 포맷 전환. 외벽 WebP(무손실 또는 손실), 스프라이트 무손실 WebP, 오디오 OGG(+Safari 대체 포맷). 각각 아트·음향 파트 작업 요청
6. A7~A9: 미사용 레거시 원본 삭제를 아트 파트에 요청할지
7. B2: 리듬 잔재 제거. 49라운드에서 '호환용 유지'로 결정된 사항을 뒤집는 것
8. B3, B11: 옛 조준 사격 경로와 보스 레거시 회귀 테스트를 유지할지 삭제할지
9. B5, B6, B7, B8: 폴더·파일 분리 구조와 이름
10. B9: 라운드 번호 이름을 무엇으로 바꿀지
11. B10, D5: 디버그 코드와 런타임 검증을 운영 번들에서 뺄지(데모 쿼리 유지 여부)
12. A14: 스프라이트 v2 후보 단계 제거(계약 문구 정리 동반)
13. D2, D3, D4: vitest isolate, 청크 분할, phaser 경량 빌드 별칭

## (4) 추천 순서
1. **브라우저에서 GPU 메모리 실측.** 4.4GB 추정이 맞는지부터 확인합니다(Chrome 작업 관리자, `?weapon=greatsword`와 `?weapon=bow` 비교).
2. 기계적 정리: B1, B4, D1. 위험이 낮고 이후 작업의 바탕이 됩니다.
3. A2 선택 무기 지연 로드. 시스템 단독으로 할 수 있고, 칼·단검·활 런의 VRAM을 즉시 줄입니다.
4. A12 빌드 필터와 사용 집합 테스트(약 4.3MB, 약 360파일). 이어서 A13 JSON 묶음.
5. 아트·음향 요청 묶음: A1/A3 트림 아틀라스(가장 큰 효과), A4 외벽 WebP와 4096 초과 해소, A6 OGG, A5 스프라이트 WebP, A7~A9 레거시 정리.
6. 구조 정리: B6, B7, B8, B5. 다음 기능을 추가하기 전에 CLAUDE.md 6-1에 따라 진행합니다.
7. 나머지: B2, B3, B9, B10, B11, D2~D5.

예상 dist 변화는 A12 + A4(무손실) + A5 + A6 기준 약 105MB → 약 60MB, A4를 손실로 하면 약 35MB입니다.

## 교차 참조 요청
- **UI 파트(`src/ui/**`)**: UI 코드가 로드하는 에셋 목록이 필요합니다. 특히 `sprites/ui/**`(아트 원본), `ui/keyart/*`, `ui/fonts/Galmuri9·14·Bold`, `ui/map_bg_1.png`, `ui/weapons/*`를 쓰는지에 따라 A10·A11 빌드 제외 범위가 정해집니다. 직접 열지 않았습니다.
- **UI 파트**: `data/story.json` `ui.*` 문구 14개가 계약으로 전달돼 쓰이는지 확인이 필요합니다(C항).
- **아트 파트**: A1·A3·A4·A5·A7~A9는 아트 소유 파일의 변경·삭제 제안입니다. 진행하려면 아트 파트 작업 요청이 필요합니다. A1은 계약 `art-assets.md` §11 시트 형식 변경을 동반합니다.
- **음향 파트**: A6 OGG 전환과 `manifest.json` `file`·`format` 갱신이 필요합니다.

## 미완료 사항
- 브라우저 실측(GPU 메모리, 실제 네트워크 요청, 로드 시간)은 이 환경에 브라우저가 없어 하지 못했습니다. VRAM 수치는 PNG 크기 × 4바이트 계산 추정입니다.
- UI가 로드하는 에셋은 격리 규칙 때문에 판정하지 못했습니다(교차 참조 요청).
- 오디오 ID 중 템플릿 문자열로 만드는 것(charge_stage1~3, kenki_stage1~3, flurry2~4, bgm/floor_*)은 동적 참조로 보고 미사용으로 분류하지 않았습니다.
- 압축 절감률은 표본 기준입니다(외벽 8장, 스프라이트 상위 25장, 오디오는 전량 시험 인코딩).
