# 2026-10-02 · 35라운드 · 전투 이펙트·양상 디벨롭 (보스 시트 7개보다 먼저)

### 도영 님 지시 (원문)
> 보스 7개 이전에 전투 이펙트나 양상을 먼저 디벨롭

### Q1. 범위 (복수)
- 결정: **피격 피드백**(히트스톱·화면 흔들림·넉백·피격 플래시·피 튀김·데미지 숫자·치명타 강조), **적·보스 공격 양상 다양화**(예고 표시·적 투사체 스프라이트·적 행동 추가·보스 패턴 2→4종), **2차 진화 전용 이펙트 16종**, **보조 동작·대쉬 연출 강화** 전부.

### Q2. 순서
- 결정: **피격 피드백 → 적·보스 양상 → 나머지(2차 이펙트, 보조 동작 연출)**. 보스 시트 7개는 그 뒤. 2~8층 타일셋은 병행.

### 작업 분담 (프로듀서)
- 시스템: 히트스톱·흔들림·넉백·데미지 숫자(Galmuri11, 시스템 씬에서 직접 그림; `public/style.css` 에 @font-face 를 `assets-game/ui/fonts/` 경로로 선언 — UI 소유 파일을 URL 로만 참조)·치명타 강조·이펙트 재생 훅. 임시값 기록.
- 아트: 피격 이펙트(피 튀김·타격 섬광·치명타 버스트·넉백 먼지), 적 공격 예고 마커, 적 투사체 스프라이트. `assets/sprites/fx/` 추가, 계약 §3 형식.

## 시스템 반영 기록 (임시값)
2026-10-02 시스템 파트가 1단계 "피격 피드백" 을 코드에 반영하며 둔 임시값. 모두 도영 님 재인터뷰 대상. 구현·검증은 `parts/system/README.md` "35라운드 반영 (1단계)". 상수는 `src/core/Constants.ts` `FEEL`, 런타임 배율은 `__lopad.setFeel()`.

| 항목 | 임시값 | 근거·메모 |
|---|---|---|
| 히트스톱 | 일반 40ms · 치명 70ms · 보스 적중 60ms(치명과 겹치면 긴 쪽) · 플레이어 피격 90ms · 중첩 금지 80ms(마지막 시작 기준) | 물리·개체 애니·적 AI·입력 소비만 멈춤. UI·데미지 숫자·흔들림은 계속. 씬 시계는 흐름(지연 호출 ≤90ms 어긋남 허용) |
| 화면 흔들림 | 적중 2px/60ms · 치명 4/100 · 플레이어 피격 5/140 · 보스 벽 충돌 6/160 · 대검 충격파 4/100 | 진폭 선형 감쇠, 매 프레임 무작위 방향 정수 오프셋, 활성 중 가장 큰 것만. 카메라 추종 스크롤 반올림 **뒤에** 더해 보간과 섞이지 않음 |
| 넉백 | 일반 6px · 치명 10px · 100ms 선형 감쇠 · 보스 1/4(AI 속도에 더하기만, 패턴 유지) · 플레이어 피격 8px/100ms(대쉬 중 제외) | 초속 2d/T 중점 적분(프레임 속도 무관). 일반 적은 100ms 동안 AI 정지(비틀거림). 벽은 Arcade 충돌. 가드 반격은 기존 밀쳐내기 유지(넉백 생략). 지속 피해 틱은 넉백·정지·흔들림 없음 |
| 적중점 | 바디 중심에서 공격 방향 반대쪽으로 반폭×0.6 | 섬광·숫자 위치. 피(시트)는 히트박스 중심(계약 anchor) |
| 피격 이펙트 깊이·시점 | `hit_spark` 적중 즉시 개체 위(4.5) · 치명은 `crit_burst` 가 섬광 **대신** · `blood` 바닥 깊이(0.95) 얼룩 프레임 500ms 유지 후 150ms 페이드 · `knock_dust` 넉백 끝 발 접지점 바닥 깊이 · `player_hit` 플레이어 중심 개체 위 | 아트 JSON note 를 따름(아트 권장 300~800ms 중 500). 플레이스홀더(시트 없을 때): 흰 원 r3→2.2배 120ms, 층 램프 base 색 점 4개 180ms, 링 6→18px 160ms, G7 먼지 3개 200ms |
| 데미지 숫자 | 적중점 −10px 에서 위로 14px, 600ms(Quad.Out), 끝 200ms 페이드, 가로 ±4px, 풀 24 | 일반 G13 `#d8d9db` · 치명 층 램프 23(light1) + `!` + 1.5배 · 플레이어 G11 `#b2b4b8` + `-` · 틱 0.8배. 깊이 5(월드 최상) |
| 글꼴 | Galmuri11 11px, `public/style.css` `@font-face` → `assets-game/ui/fonts/Galmuri11.woff2`(UI 소유 파일 URL 참조), `document.fonts.load` 대기 상한 3초, 실패 시 monospace | 34라운드 규칙(숫자만이라도 11px 통일). 1.5배는 비정수 배율이라 치명 숫자 가장자리가 약간 뭉개짐 — 2배(정수)로 바꿀지 인터뷰 |
| 설정 훅 | `feelSettings { shake, hitstop, knockback: 배율, numbers: 표시 }` 기본 1/1/1/true, 저장 안 함 | 접근성 설정 UI 는 계약 추가 필요(교차 참조 후보) |
| 신설 내부 이벤트 | `BOSS_WALL_HIT { id, x, y }`, `PlayerDamagedPayload.source?` | UI 계약 페이로드는 그대로(`source` 는 중계 시 제거) |
| 2단계 시트 | `telegraph_line/circle/cone`, `enemy_bullet`, `boss_fan_shot`, `muzzle_flash` 는 **로드만** | 적·보스 양상 디벨롭(2단계)에서 연결 |

## 시스템 반영 기록 2단계 (임시값)
2026-10-02 시스템 파트가 2단계 "적·보스 공격 양상 다양화" 를 코드에 반영하며 둔 임시값. 모두 도영 님 재인터뷰 대상. 구현·검증은 `parts/system/README.md` "35라운드 반영 (2단계)". 수치는 `data/enemies.json`·`data/bosses.json`, 연출 상수는 `src/core/Constants.ts` `ENEMY_FX`.

| 항목 | 임시값 | 근거·메모 |
|---|---|---|
| 예고 마커 공통 | 바닥 깊이(`FX_GROUND` 0.95), 시트 2프레임 120ms 루프(JSON `frameDurationsMs`), 예고 끝·경직·사망 시 즉시 제거. 시트가 없으면 G13 `#d8d9db` 점선(6px/4px, 두께 2) · 원 · 부채꼴을 120ms 로 깜빡(알파 0.85 ↔ 0.38) | 아트 JSON pivotNote 를 따름. `telegraph_line` 은 TileSprite 로 길이 방향 타일링 + 회전, `circle`/`cone` 은 scale = R / 15 |
| 결사병 돌진 예고선 | 길이 = 돌진 거리(속도 × 시간 = 14칸/s × 0.4s = 5.6칸 ≈ 90px), 예고 0.6초 동안 플레이어를 따라 돌고 돌진 시작에 사라짐 | 돌진 방향이 예고 끝에 정해지므로 선도 끝까지 따라간다 |
| 사수 조준선·재장전 | `ranged.telegraphMs` 300 · `telegraphTiles` 3(48px) · 조준 중 정지 · 총구 = 바디 중심 + 바라보는 방향 8px, 위 2px(`muzzle_flash`, 총구 프레임에 맞춤) · 탄 `enemy_bullet`(진행 각도 회전) · `reload { shots 3, reloadMs 2000, retreatSpeedMult 1 }` 재장전 중 뒤로 물러나고 사격 없음, 끝나면 첫 사격까지 평시 간격의 절반(750ms) | 재장전 애니 없음 → 걷기/대기 그대로. `ENEMY_TELEGRAPH { kind: 'shot' }` 는 `sfx/archer_telegraph` 로 매핑되나 자산이 없어 무음 |
| 결사병 방패 막기 | `shield { frontDeg 60(전체각 = 반각 30°), reduction 0.5 }`, 최소 1 피해, 막으면 `hit_spark` + 숫자 + 히트스톱 40ms + 흔들림 2px/60ms 만(피·치명 버스트·넉백 없음), 돌진 중 정면 = 돌진 방향, 경직 중·지속 피해 틱은 막지 않음. `ENEMY_BEHAVIOR { kind: 'block' }` | 정면 각이 좁게 느껴지면 90°~120° 로 재인터뷰 |
| 징집병 집단 돌격 | `pack { minCount 3, rangeTiles 6, speedMult 1.4, durationMs 2000, cooldownMs 4000 }` — 같은 방 같은 종이 3마리 이상이고 누군가 6칸 안이면 전원 1.4배 2초, 그 뒤 4초 쿨타임. 방(씬) 공유 상태(`PackCharge`), 발동 프레임에 먼저 갱신된 개체는 다음 프레임부터(≤1프레임 지연). `ENEMY_BEHAVIOR { kind: 'pack' }` 1회 | 소환된 징집병도 머릿수에 든다 |
| 보스 패턴 목록 | `phases[].patterns`: 1~7층 보스 1페이즈 `[dash, slam]`, 2페이즈 `[dash, fan, slam, summon]`; 황제 1페이즈 `[dash, slam]`, 2·3페이즈 `[dash, fan, slam, volley]`(소환 없음). 패턴 간격 `patternIntervalMs`(없으면 `dash.intervalMs`), 패턴별 쿨타임이 지난 후보 중 시드 RNG(`floorSeed:boss:<id>`)로 선택, 후보가 없으면 돌진. `fan.afterDash` 연계는 유지(부채꼴 쿨타임이 끝났을 때만) | 패턴 목록이 없으면 옛 동작(dash + fan) |
| 부채꼴 예고 | `fan.telegraphMs` 400 · `telegraphTiles` 5(80px) · `telegraph_cone`(반각 = spreadDeg/2, 4방향 행은 지배 축) · spreadDeg > 120 이면 원 마커 · 탄 `boss_fan_shot`(2프레임 루프, 회전 없음) · 쿨타임 = `fan.intervalMs` | `BOSS_TELEGRAPH { attack: 'fan' }` 신설 |
| 내리찍기 | `slam { telegraphMs 800, radiusTiles 2.5, attack = 그 보스 1페이즈 돌진 공격력, cooldownMs 4000 }` — 예고 시작 시점의 플레이어 위치에 원 마커, 끝나면 반경(+플레이어 반폭) 안이면 피해 1회, 충격파 = `crush` 시트 재사용(없으면 링), 흔들림 = 벽 충돌값 6px/160ms. 보스는 제자리(이동·점프 없음) | `BOSS_TELEGRAPH/BOSS_ATTACK { attack: 'slam' }` |
| 소환 | `summon { enemy 'dummy', count 2, max 4, cooldownMs 15000 }` — 보스 바디 반폭 + 12px 양옆(막힌 자리면 방 안 무작위), 같은 종이 max 이상이면 후보에서 제외, 소환 후 frame 3 유지 ≥150ms. 보스가 죽으면 남은 부하는 시체만 남기고 즉시 제거(보상 없음) | `BOSS_ATTACK { attack: 'summon' }`(예고 없음) |
| 정렬 사격(황제) | `volley { telegraphMs 500, telegraphTiles 12, count 5, shotGapMs 120, projectileSpeedTiles 9, attack 14, projectileSize 6, projectileLifeMs 3500, cooldownMs 5000, sprite boss_fan_shot }` — 예고선이 플레이어를 따라가고, 끝난 시점 방향으로 5발 일직선 | `BOSS_TELEGRAPH/BOSS_ATTACK { attack: 'volley' }` |
| 투사체 시트 | `ProjectileSpec.sprite`(데이터) → 시트 JSON 의 `rotate`·`pivot`·`loop` 그대로. 패링 반사 시 텍스처 유지, 회전 시트만 180° 반전(원형 탄은 그대로) | 플레이어 위 깊이(`PROJECTILE` 3) 기존 유지 |
| 음향 매핑 | 기존 유지: `BOSS_TELEGRAPH` 는 dash 만 `boss_telegraph`, `BOSS_ATTACK` 은 fan 만 `boss_fan`. 새 attack(slam·summon·volley)·`ENEMY_BEHAVIOR` 는 자산 없음 → 음향 파트 전달 | |
| roomFloors(37·40라운드) | `roomFloors[start/trial/rest/boss]` 목록이 있으면 방 내부 바닥은 그 목록(좌표 해시), 복도·목록 없음·빈 목록은 `tiles["1"]`. 벽 자동타일 인덱스가 `tiles["2"]` 의 첫 항목이면(정면 벽) 그 목록을 좌표 해시로 섞음(19·20 / 21·22). 소품 `maxPerRoom`(방당 상한)·`weight`(가중, 0 = 안 놓음). 시트 크기·인덱스는 JSON 값으로만(128×64·128×80 모두 동작) | 옛 형식 JSON(roomFloors 없음)은 그대로 |
| 39라운드 반영 | 치명 데미지 숫자 배율 1.5 → **2.0**(정수 배율). 넉백 중 적 비틀거림(AI 100ms 정지) 유지 | `FEEL.DAMAGE_TEXT.CRIT_SCALE` |
