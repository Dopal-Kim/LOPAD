# 자유 전투 계약 (P19, 62 방향 재설정)

근거: `parts/producer/decisions/2026-10-14-P19-free-combat.md`. 시스템·UI·아트·음향이 이 문서만 보고 동시에 작업한다. 값은 1차 — 2단계 재측정 뒤 이 문서 아래 '조정 기록'에 덧붙인다.

## 1. 새 이벤트 (시스템 EventBus 내부 이름 · 페이로드) — 시스템 S1·S2·S3 가 낸다
| 이벤트 | 문자열 | 페이로드 | 누가 쓰나 |
|---|---|---|---|
| `ENEMY_STAGGERED` | `enemy:staggered` | `{id, x, y, kind:'flinch'\|'stagger', ms}` (flinch = 움찔 · stagger = 버팀이 깨짐) | 음향·fx |
| `ENEMY_KNOCKED` | `enemy:knocked` | `{id, x, y, tier:1\|2\|3\|4, dirX, dirY, distTiles}` (1 밀림 · 2 날림 · 3 크게 날림 · 4 화면 가로지름) | 음향·fx |
| `ENEMY_WALL_SLAM` | `enemy:wall-slam` | `{id, x, y, speed, bonusDamage, surface:'wall'\|'prop'\|'pillar'}` | 음향·fx·UI 팝 |
| `ENEMY_BOWLED` | `enemy:bowled` | `{hitter, target, x, y, damage}` (날아간 적이 다른 적과 부딪침) | 음향·fx·UI 팝 |
| `ENEMY_LAUNCHED` / `ENEMY_LANDED` | `enemy:launched` / `enemy:landed` | `{id, x, y, airMs}` / `{id, x, y, slam:boolean}` | 음향·fx |
| `ENEMY_FELL` | `enemy:fell` | `{id, x, y, zone:'water'\|'drop'\|'fire'}` (낙하 구역에 밀려 떨어짐 = 즉사, 군주 제외) | 음향·fx·UI 팝 |
| `HAZARD_EXPLODED` | `hazard:exploded` | `{x, y, kind:'cask'\|'still'\|'bottle', chain:number}` (chain 0 = 첫 폭발, 1+ = 연쇄 몇 번째) | 음향·fx·UI 팝 |
| `HAZARD_IGNITED` | `hazard:ignited` | `{x, y, kind:'pool'\|'cask'\|'still', radiusTiles}` | 음향·fx |
| `COMBO_STREAK` | `combo:streak` | `{count, windowMs}` (연속 처치 — 처치 사이 ≤ 1.5초) | UI 팝·음향 |
- UI 는 위 이벤트를 `UI_EVENTS` 로 받는다: 시스템이 같은 이름의 `ui:` 접두 이벤트(`ui:enemy-wall-slam` 등)로 중계(계약 ui-system-interface §28).
- 같은 프레임 같은 적의 KNOCKED → WALL_SLAM 순서 보장.

## 2. 예고 색 언어 (적 공격 텔레그래프 — 시스템이 그리고 UI·아트가 같은 색을 쓴다)
| 단계 | 뜻 | 색 | 모양 |
|---|---|---|---|
| 경고 | 근접 휘두름·돌진 준비(막기·회피 가능) | 호박 `#ffb347` | 바닥 부채꼴/선, 350ms 이상 |
| 위험 | 막을 수 없음(잡기·광역·폭발) | 적 `#ff4a3a` | 채운 원/부채꼴 + 바깥 테 맥박 |
| 원거리 | 조준·투척 궤적 | 청백 `#9fd8ff` | 점선 궤적 + 착탄 원 |
| 기회 | 버팀이 깨짐·띄워짐(추가타 기회) | 금 `#ffe08a` | 적 발밑 짧은 반짝 |
- 예고 최소 350ms(일반), 위험은 500ms 이상. 접촉 피해 없음(몸에 닿는 것만으로 피해 주지 않는다).

## 3. 전투장 형태 틀 (시스템 S2 데이터 · 아트 S2 그림 기준)
- 파일: `data/arenas/<id>.json` — `{ id, name, regions:[지역 id], size:{w:[min,max], h:[min,max]}, mask: string[], legend?, variants:{flipX, flipY, scale:[0.85,1.15]}, doors:[{side, at}], hazards:[{kind, slot}], props:[세트 id], lighting:{ambient, lights:[{x,y,kind}]}, stage:'battle'|'elite'|'event'|'shop'|'rest'|'boss' }`.
- `mask` 문자: `.` 바닥 · `#` 벽 · `~` 낙하 구역(물·낭떠러지 — 밀려 떨어지면 즉사) · `=` 다리 · `c` 엄폐(돌기둥) · `h` 위험물 자리 · `D` 문 자리 · `S` 적 등장 자리 · `P` 주인공 시작 · `^` 높은 단(두 단 테라스 위층, 계단 `/` 로 연결).
- 1층 형태 7종 + 보스: 원형 광장 · 부두 · 십자로 · 두 단 테라스 · 술창고 · 성벽 회랑 · 증류소 마당 (+ 보스 연회장 56×34). 넓이 화면의 1.8~3배(평균 48×30칸). 모든 바닥 칸 도달 가능, 문 사이 경로 보장.

## 4. 카메라 신호
- 카메라 줌: 탐색 1.75, 전투 중(살아 있는 적 ≥ 1) 1.6 으로 0.6초에 걸쳐 물러남, 보스 1.5. 시스템이 정하고 `UiSnapshot.camera{zoom, combat:boolean}` 로 알린다(UI 는 화면 밖 적 표식·월드 → 화면 좌표에 사용).
- 화면 밖 적: `UiSnapshot.offscreen[{id, angle, distTiles, threat:'warn'|'danger'|'ranged'|null}]`(시스템 S3) — UI 가 가장자리 표식.

## 5. 측정
- 봇 드라이버는 `parts/system/tools/bot/`(시스템 S3 가 scratchpad/a64/drv 에서 옮김) — P19 ⑥ 지표를 `npm run bot:metrics`(또는 node 스크립트)로 재현.

## 조정 기록 · 계약 보강 (P19 2단계)
- §1 보강: `ENEMY_DAMAGED.weapon?`(무기 적중 — 환경 피해엔 없음), `ENEMY_BOWLED.chain`, `ENEMY_TELEGRAPH.ms`, `ENEMY_ATTACK` kind 'drum'·phase beat/rally/run/runEnd/blast, 내부 `combat:alive{count}`(전투 북 층). UI 중계 페이로드에는 `screen{x,y}`(논리 960×540, 줌·스크롤 반영).
- §3 보강: 마스크 `_` = 테라스 단 끝(아래 단 착지, 걷기 막힘), `legend` 로 `~` = water|drop, `doors` = [{side:'west'|'east', at:0..1}] 입구·출구 순, `lighting.lights` 좌표 = 마스크 칸, 확장 필드 `lighting.ambientByRegion`·`centerArt`·`dress`. 주인공은 낙하 구역에 들어가지 못함(적만 떨어짐). 형태 id: plaza_fountain·dock_quay·crossroad·terrace·cellar·rampart·distillery·banquet_hall. 노드 이름 `route.json shapeNames`(스토리 65 팩).
- §4 보강: `UiSnapshot.camera{zoom(논리 배율), combat, view{x,y,w,h}}`, `UiOffscreenEnemy{id:number, angle(화면 가운데 → 적), distTiles(주인공 기준), threat}`.
- 새 UI 이벤트 `ui:enemy-bark`(UiEnemyBark{screen,id,x,y,kind,text} — 머리 위 말풍선, 같은 적 4초·전체 1.5초 간격) — UI 미구현.
