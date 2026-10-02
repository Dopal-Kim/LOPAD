# evolution_fx — 35라운드 3단계: 2차 진화 이펙트 16종 + 보조 동작·대쉬 연출 7종 (아트, 2026-10-02)

빌드: `python3 parts/art/work/evolution_fx/build.py` → `assets/sprites/fx/` 23종 PNG/JSON(전부 **새 파일**, 기존 fx 미변경) + 미리보기 3장.
`README.md`·`art-bible.md` 는 다른 아트 에이전트와 동시 작업 중이라 손대지 않았다. 바이블 4.3 에 옮길 내용은 맨 아래 "바이블 반영 대기".

## A. 2차 진화 16종 (`fx/<노드id>`, 1층 호박 램프, 런타임 스왑)

| id | 크기 | 방향 | 프레임 · ms · 루프 | 앵커 · 피벗 · 깊이 | 색 (무채 / 강조) | 연출 · 재생 시점 |
|---|---|---|---|---|---|---|
| wide 만월 | 64×64 | 4 | 6 · 50/60/80/100/120/140 | player_pivot (32,42) · 위 | G15 / 17 18 19 21 22 24 26 27 | 거합(r19·220°)보다 큰 r26·280° 보름달 호 + 안쪽 r19 달무리 띠(1~3f) + 머리 순백 글린트. `attack_frame2`, iai **대신** |
| zangetsu 잔월 | 48×48 | 4 | 4 · 75×4 · **루프** | player_pivot (24,34) · **바닥** | — / 18 19 21 24 26 27 | 거합 자리에 남는 3px 어두운 띠 + 띠를 따라 도는 글린트 2개(4프레임 = 한 바퀴 = 틱 300ms). 0프레임 = 틱 순간(띠 한 단 밝음 + 바깥 점선). `after_iai`, 위치 고정, 1000ms 뒤 제거 |
| longinvuln 허보 | 32×32 | 4 | 4 · 50/70/90/110 | player_pivot (16,26) · 위, 플레이어 따라감 | — / 18 19 20 21 22 23 25 | 돌진 실루엣 테두리(25→23→21→18) + 성긴 격자 속(몸이 비침) + 몸 뒤 속도선 2줄, 뒤로 1px 씩 처짐. `dash_start`, batto 와 동시 가능 |
| dashcrit 급소 | 24×24 | any | 4 · 40/50/60/70 | hitbox_center (12,12) · 위 | — / 19 21 22 24 25 26 27 | 흰 점 + 고리 → 십자 r8 + 마름모 r6 → 점선 마름모 r9 → 조각. `hit`(대쉬 베기 적중), crit_burst 대신 |
| quake 지진 | 64×64 | any | 6 · 50/70/100/**70**/100/130 | hitbox_center (32,32) · 바닥 | G06 G09 / 17 18 19 21 22 24 26 27 | 0~2f 1단 링 r6→19(220ms) → 3f 부터 2단 링 r8→28(1.6배) + 바닥 균열(길이·각도 불규칙, 누적) + 파편. **3프레임 시작 = 시스템 2단 판정(220ms 뒤)**. `hit_judge`, crush 대신 |
| pulverize 분쇄 | 48×48 | any | 4 · 40/60/80/100 | hitbox_center (24,24) · 바닥 | — / 17 18 19 21 22 24 26 27 | 링 r7→22 + 바깥으로 튀는 2px 쐐기 8개 + 축 4방향 X 표(투사체 소멸). `hit_judge`, crush 대신 |
| ironwall 철벽 | 32×32 | 4 | 3 · 40/60/80 | player_pivot **(16,22)** · 위 | — / 18 19 21 22 24 25 26 27 | 몸 중심에서 바라보는 쪽 9px 에 서는 세로 벽(27/25 → 5px 26/24/22 + 바깥 물결 → 점선 21). `guard_release`, guard_wave 와 동시 |
| giant 거인 | 32×40 | any | 4 · 90×4 · **루프** | player_pivot (16,36) · **바닥**, 플레이어 따라감 | — / 18 19 21 22 24 25 | 발밑 타원 고리(r13, 도는 밝은 토막) + 안쪽 점선 고리 + 몸 양옆 2px 기둥이 솟음(주기 12px = 4프레임, 이음새 없음). `attack_start`~attack 종료 |
| dance 난무 | 32×32 | 4 | 6 · 40×6 | player_pivot (16,26) · 위 | — / 17 18 19 21 22 24 26 27 | 호 r7.5 → r10.5(**반대 방향**) → r13, 각 2프레임(긋는 중 → 전체). 0·2·4프레임 = 1·2·3타(80ms). `attack_frame2`, twin 대신 |
| bleed 출혈 | 16×16 | any | 4 · 125×4 · **루프** | hitbox_center (8,8) · 위, 적 따라감 | — / 17 18 19 22 24 | 2×3 핏방울 2줄(위상 다름)이 떨어지며 길어지고 바닥에 튐. 한 바퀴 500ms = 틱, 0프레임 틱 글린트(24/22). 출혈 소진 시 제거 |
| afterimage 잔상 | 24×24 | 4 | 4 · 60/80/100/120 | player_pivot (12,23) · 바닥, 위치 고정 | — / 17 18 19 20 21 22 24 27 | 돌진 실루엣을 20/19/18 로 채운 분신 + 테두리 + 몸을 가로지르는 베기 사선(24→27 2줄→22 점선). `dash_start` 출발점(경로 길면 중간점 하나 더) |
| assassin 암살 | 32×32 | any | 4 · 40/60/80/100 | hitbox_center (16,16) · 위 | G01 G02 / 17 19 22 23 24 25 27 | 바닥 그림자 웅덩이(G01/G02 타원) + 흰 점 → 대각선 3px 섬광 베기(27/25 + 22 가지) → 점선 → 조각. `hit`(그림자 걸음 직후 공격 적중) |
| flash 섬광 | 24×8 | any (rotate) | 4 · 50×4 · **루프** | projectile (22,4) · 화살 아래 | — / 19 21 22 24 25 26 27 | 관통 꼬리(16)보다 8px 길고 순백 코어(27) 4단 띠 + 끝 흔들림. `loop_move`, pierce 대신 |
| heavyarrow 중시 | 16×8 | any (rotate) | 1 | projectile (8,4) | G05 G08 G13 / 19 21 25 27 | 3폭 자루(G13/G8/G5 + 25 글로우) + 큰 촉(27/25) + 두 겹 깃(21/19). 조준 사격 화살(bow_arrow_aimed) 대신 |
| heavyarrow_hit | 24×24 | any | 3 · 50/80/110 | hitbox_center (12,12) · 위 | G06 G09 G12 / 19 22 24 25 27 | 충격 별(27/25) + 네 귀퉁이 먼지 퍼짐 + 점선 고리. `hit`(중시 적중 = 경직 600ms 시작) |
| rain 폭우 | 24×24 | any (rotate) | 4 · 40/50/60/70 | projectile (3,12) = 발사점 | — / 17 18 21 22 24 25 26 27 | 5갈래 ±50° 섬광(산탄 3갈래 ±24° 보다 넓고 김) 뻗었다 어두워짐. `shot`, scatter 대신 |
| seek 추적 | 16×16 | any (rotate) | 4 · 60×4 · **루프** | projectile (13,8) · 화살 아래 | — / 19 21 22 24 26 | 꼬인 두 가닥 파동(24/22)이 뒤로 흐름(4프레임 = 2π, 이음새 없음) + 교차점 26 글린트. `loop_move` |

## B. 보조 동작 · 대쉬 연출 7종

| id | 크기 | 방향 | 프레임 · ms | 앵커 · 피벗 · 깊이 | 색 | 연출 · 재생 시점 |
|---|---|---|---|---|---|---|
| parry_flash | 32×32 | any | 4 · 40/60/80/100 | hitbox_center (16,16) = 접점(없으면 플레이어 몸 중심) · 위 | G15 / 18 19 21 22 23 24 25 27 | 흰 별 섬광(G15 십자) → 깨끗한 동심 고리 r5.5/r10.5(시간 정지) → 점선 고리 → 조각. `parry_success`, 히트스톱과 같이 |
| guard_wave | 48×24 | 4 | 4 · 50/60/70/80 | player_pivot (24,14)=발 · **바닥** | G06 G09 / 17 18 19 21 22 24 25 27 | 발에서 바라보는 쪽으로 퍼지는 반타원(세로 0.5) 충격파 r8→24 + 가장자리 먼지. `guard_release` |
| shadowstep_ghost | 16×24 | 4 | 3 · 60/80/100 | player_pivot (8,23) · 바닥, 위치 고정 | G02 G03 G04 / — | idle 실루엣을 명도 3단(G02~G04)으로 눌러 찍음 → 줄무늬로 흩어짐 → 테두리 조각. `shadowstep_start` 출발점 |
| aim_charge | 24×24 | any | 6 · 100×6 (**진행도 기반**) | player_pivot (12,12)=**몸 중심** · 위 | — / 18 20 22 24 25 27 | 점선 빈 고리 r9 → 위에서 시계 방향으로 72°씩 참(끝 25 점) → 5프레임 = 완료 발광(25 고리 + 27 눈금·코어). `frame = min(5, floor(progress*5))` |
| aim_line | 8×2 | any (rotate, **tile**) | 1 | player_pivot (0,1)=선 시작 · 바닥 | — / 20 22 | 4 on / 4 off 점선(위 22, 아래 20). TileSprite 폭 = 사거리, 회전 = 커서 각도 |
| dash_dust | 16×8 | 4 | 3 · 50/70/90 | player_pivot (8,6)=발 · 바닥, 위치 고정 | G06 G09 G12 / — | 대쉬 반대쪽으로 퍼지는 먼지 뭉치(옆: 뒤로 길게 / 상하: 좌우 두 뭉치). `dash_start` 출발점 |
| dash_trail | 16×24 | 4 | 3 · 40/60/80 | player_pivot (8,23) · 바닥, 위치 고정 | G02 G03 G04 / — | 돌진 실루엣을 이동 방향 줄무늬(옆 = 가로, 상하 = 세로)로 끊음 → 성겨짐 → 조각. 대쉬 중 40~50ms 마다 현재 위치에 하나씩(각 180ms) |

전부 색 예산(무채 ≤4 + 강조 ≤8) 안, 고립 픽셀 0, 반투명 0 (`color_report` 매 실행 검사, 마지막 실행 ALL OK).

## see → critique → fix 기록
- 1차: 강조색 9~10색 초과 7종(wide·dashcrit·quake·pulverize·dance·afterimage·rain). 잔월 띠를 무작위로 뚫어 1배에서 체커 노이즈. 급소가 24px 캔버스에서 점 하나. 지진 균열이 등간격·같은 길이라 바퀴살. 철벽이 캔버스 중심 회전이라 down 방향 벽이 발밑에 걸림. 거인 기둥이 1px 비처럼 흩어짐. 출혈·대쉬 먼지가 1배에서 안 보임. 출발 위치에 남는 이펙트(잔상·그림자 걸음·대쉬 잔상·먼지)가 미리보기에서 주인공에 가려짐.
- 2차: 색 한 단씩 합쳐 전부 ≤8. 잔월은 3px 단색 띠 + 띠 안의 밝은 토막. 급소 코어 2×2·십자 r8·마름모 r6/r9. 지진 균열 각도·길이 흩뜨림(결정적 표). 철벽 피벗 (16,22)로 몸 중심 기준. 거인 양옆 2px 기둥 + 바깥 1px. 출혈 방울 2×3 + 22/24 글린트. 먼지 반지름 확대. 미리보기에서 위치 고정 이펙트는 주인공을 대쉬 방향으로 10px 옮겨 보이게.
- 3차: 루프 이음새 코드 검증 — 잔월 글린트 이동을 0.1125/프레임으로(4프레임에 다음 글린트 자리까지 = 이음새 없음, 이전엔 2프레임 주기), 거인 점선 고리 위상 22.5°×4 = 90° 주기 일치. 거인 기둥(12px 주기/4프레임), 출혈(위상 4), 추적(2π/4)은 처음부터 이음새 없음. 1배 미리보기 재확인 — SHIP.

## 임시 결정 (도영 님 확인 필요)
1. **2차 이펙트는 1차를 '대체'한다**: wide↔iai, dance↔twin, quake·pulverize↔crush, flash↔pierce, rain↔scatter, heavyarrow↔bow_arrow_aimed, dashcrit↔crit_burst(대쉬 베기 적중 시). 겹쳐 재생하는 것은 zangetsu(iai 뒤에 이어서), longinvuln(batto 위), ironwall(guard_wave 위), giant·bleed·afterimage·assassin·seek(기존과 독립). 겹침 방식이 좋으면 시스템이 둘 다 띄워도 그림은 충돌하지 않게 그렸다(2차는 더 크거나 바닥 깊이).
2. **ironwall 피벗 (16,22)** — player_pivot 앵커지만 발이 아니라 캔버스 중심이 몸 중심에 오도록 발에서 6px 위. 32 캔버스로 down 방향 벽을 발 아래 두려면 불가피.
3. **aim_charge 는 시간이 아니라 진행도 기반**(`progressDriven: true`), 피벗 = 몸 중심(발에서 위로 11px). 5프레임(완료 발광)은 완료 즉시 발사되므로 1~2프레임만 보임 — 더 보이게 하려면 발사 뒤 60ms 유지.
4. **guard_wave 반경 24px** = 밀쳐내기 2.5칸(40px)의 60%. 48 캔버스 한계. 나머지는 적 넉백으로 읽힌다고 봄. 전체 반경이 필요하면 scale 1.6 허용(`scale` 메모 없음, 필요 시 추가).
5. **giant 오라 = 발밑 고리 + 양옆 기둥, 플레이어 아래 깊이.** 몸 위에 겹치는 발광은 주인공 흑백 기조를 해쳐 피했다.
6. **bleed 는 적 히트박스 중심에 붙어 따라감**(`followsTarget`), 16×16 이라 24×24 덩치 적에는 작게 보임 — 그대로 둘지, 덩치 적은 2개 띄울지.
7. **shadowstep_ghost·dash_trail 은 player PNG 알파를 마스크로 재사용**(idle 0프레임 / dash 1프레임). 플레이어 시트가 바뀌면 재빌드 필요(빌드 스크립트가 자동 반영).
8. **zangetsu 루프 4프레임 = 300ms = 틱 간격, bleed 루프 4프레임 = 500ms = 틱 간격** — 0프레임이 틱 순간. 시스템 틱 타이머와 애니 시작을 맞추면 글린트가 피해 틱과 동기.
9. JSON 추가 메모 필드: `depth`(above/below 문자열), `followsPlayer`, `followsTarget`, `progressDriven`, `pivotNote`, `note`. 계약 §3.1 에 없는 필드이므로 프로듀서가 계약 반영 여부 결정 (combat_fx 의 `tailFrames`·`tile`·`scale` 과 같은 성격).
10. 미리보기 바닥은 지시대로 G02. 실제 1층 바닥은 G04 라 무채 잔상(G02~G04)은 게임에서 미리보기보다 조금 덜 보인다 — 1층에서 확인 후 필요하면 G01 포함으로 한 단 어둡게.

## 시스템 전달 요점 (재생 시점 · 깊이 · 루프 종료)
- **재생 시점 키(`spawn`)**: `attack_frame2`(wide·dance) / `after_iai`(zangetsu: iai 마지막 프레임 끝난 시각, 같은 피벗 위치 고정) / `dash_start`(longinvuln 따라감, afterimage·dash_dust·dash_trail 위치 고정) / `hit`(dashcrit·bleed·assassin·heavyarrow_hit) / `hit_judge`(quake·pulverize: 대검 적중 판정 시작, crush 와 같음) / `guard_release`(ironwall·guard_wave) / `attack_start`(giant) / `loop_move`(flash·seek: 투사체에 부착) / `shot`(rain) / `aimed_shot`(heavyarrow 텍스처) / `parry_success` / `shadowstep_start` / `aim_charge`(aim_charge·aim_line).
- **깊이**: 바닥(캐릭터 아래) = zangetsu·quake·pulverize·giant·afterimage·guard_wave·shadowstep_ghost·aim_line·dash_dust·dash_trail·flash·seek(화살 아래). 위 = 나머지.
- **루프 종료 조건**: zangetsu = 궤적 지속(1000ms) 끝 / giant = attack 애니 종료 / bleed = 출혈 횟수 소진(재적중 시 갱신, 대상 사망 시 즉시) / flash·seek = 투사체 소멸 / aim_charge·aim_line = 발사 또는 취소.
- **quake 2단**: 3프레임(인덱스 3) 시작 시각 = 50+70+100 = 220ms = 시스템 2단 판정 시각. 판정 타이밍을 바꾸면 ms 배열도 같이.
- **투사체 회전**: heavyarrow·flash·rain·seek·aim_line 은 우향 그림, `rotate: true`. seek 는 화살이 선회해도 각도만 따라가면 됨.
- **4방향 의미**: ironwall·guard_wave = 바라보는 방향, longinvuln·afterimage·dash_dust·dash_trail·shadowstep_ghost = 대쉬/바라보는 방향(먼지는 반대쪽으로 퍼짐), wide·zangetsu·dance = 공격 방향(1차 호와 같은 SWEEP).

## 바이블 반영 대기 (art-bible 4.3 에 추가할 행)
위 A·B 표 그대로 + 원칙 한 줄: "2차 진화 이펙트는 1차와 같은 계열에 한 겹 더(더 큰 호·남는 띠·두 번째 링·세 번째 호·더 긴 꼬리)로 구분하고, 보조 동작·대쉬 잔상은 무채(G02~G04)로 둬 층 스왑과 무관하게 한다."
