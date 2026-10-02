# fx_prod A 묶음 — 인페르노 기반 무기 이펙트 양산 (칼·대검 + 공통 피격·예고·적 투사체) — 43라운드, 2026-10-02

빌드: `python3 parts/art/work/fx_prod/build_a.py` → `assets/sprites/fx/` 25 시트(PNG+JSON, 같은 id 로 **기존 파일 교체**, 신규 2) + 미리보기 2장.
근거: `parts/art/fx-design.md` 전 절, `decisions/2026-10-02-round-42-infernum-fx.md` 43라운드 검수(임시 결정 1~10 수용, 대검 W2 `#d8441c`), 계약 `art-assets.md` §3.2.
콘셉트 생성기 `work/fx_concept/build.py` 를 import 해 재사용(Canvas·겹친 초승달·번개·예고). `concept_*` 파일은 그대로(양산본이 우선, 삭제는 프로듀서 결정).
`README.md`·`art-bible.md`·`fx-design.md` 는 B 묶음(단검·활·보조 7종) 에이전트와 동시 작업이라 손대지 않았다. 바이블에 옮길 표는 아래.
B 묶음 id(`dagger_slash`, `bow_*`, `twin`, `gale`, `pierce`, `scatter`, `dance`, `bleed`, `afterimage`, `assassin`, `flash`, `heavyarrow*`, `rain`, `seek`, 보조 7종)는 건드리지 않았다. `blood` 는 변경 없음(층 램프 피 그대로).

## 0. 팔레트
- `work/palette/build.py` FX_BLOCK greatsword W2 `#e35c1c` → **`#d8441c`** (lab 설명·decision 문구 갱신) → `lopad.json`·`lopad.gpl` 재생성.
- 검증: 재생성 전 사본과 JSON 전체 비교 — 차이는 `fx.weapons.greatsword.ramp[2]`, `fx.weapons.greatsword.lab`, `fx.decision` 3곳뿐. gray·floors·ui·notes 바이트 동일. GPL 은 W2 한 줄만 차이.

## 1. 시트 목록 (A 묶음)
| id | 크기 · 프레임 · ms | 방향 | 앵커 · 피벗 · 깊이 · spawn | 색 (무채 / 코어 / 층 강조 / 보조) | 연출 |
|---|---|---|---|---|---|
| katana_slash | 48 · 5 · 40/50/60/70/90 | 4 | player_pivot (24,34) · 위 · attack_frame2 | — / X0 X1 / 22 24 27 / 칼 W0~3 | 콘셉트 승격. 본 띠 + 바깥 잔상(+1f), f0 예비 코어선, f2 광선 2, f4 꼬리 |
| iai | 64 · 7 · 40/40/60/80/100/120/140 | 4 | player_pivot (32,42) · 위 · attack_frame2 | 동일 | 콘셉트 승격. 3겹 + f1 섬광 + f2 광선 3 + 꼬리 3 |
| batto | 64 · 7 · 40/40/40/50/60/70/80 | 4 | player_pivot (32,42) · **아래** · dash_start, followsPlayer | 동일 | 몸 뒤 속도선 3줄(W0 테두리·W2/X 코어) + 전방 발도 호 2겹(r14, ±45°). 예비→섬광→광선→식음→점선→조각 |
| wide | 96 · 7 · 40/50/70/90/110/140/160 | 4 | player_pivot (48,58) · 위 · attack_frame2 | 동일 | 콘셉트 승격. 3겹 + 보름달 고리(f3 닫힘) + 네 귀 글린트 |
| zangetsu | 64 · 4 · 75×4 루프 | 4 | player_pivot (32,42) · 바닥 · after_iai | — / X0 X1 / — / 칼 | 콘셉트 승격. 어두운 3띠 + 번개 토막 + 도는 글린트, f0 = 틱 |
| longinvuln | 64 · 5 · 40/50/70/90/110 | 4 | player_pivot (32,42) · 위 · dash_start, followsPlayer | — / X0 X1 / 22 27 / 칼 | 돌진 실루엣(player_dash f1 마스크, (24,19)) 윤곽 W3→W2→W1→W0 점선 + 앞 가장자리 코어 + 성긴 사선(mod 3/4) + 속도선 3 |
| dashcrit | 64 · 5 · 40/40/50/60/80 | any | hitbox_center (32,32) · 위 · hit | — / X0 X1 / 22 24 27 / 칼 | hit_burst 구조 + 광선 8(W0·W2·X0 3겹) + 고리 r8→14→20 + 네 귀 글린트 |
| greatsword_slash | 48 · 5 · 40/50/60/70/90 | 4 | player_pivot (24,34) · 위 · attack_frame2 | G06 G09 / X0 X1 / 24 27 / 대검 | 두께 6.5 호 2겹 + 호 아래 바닥 불티 + 재 |
| crush | 64 · 6 · 40/50/70/90/110/130 | any | hitbox_center (32,40)=바닥 · 바닥 · hit_judge | G06 G09 / X0 X1 / 22 26 27 / 대검 | 콘셉트 quake_bolt 승격: 낙뢰 3겹+가지 → 섬광 별 → 링 r8→16→24 + 균열 + 재 |
| weight | 64 · 6 · 40/50/70/90/110/130 | any | hitbox_center (32,40)=바닥 · 바닥 · hit_judge | G06 G09 / X0 X1 / 22 24 27 / 대검 | 섬광 별 → 양옆 먼지 뭉치(puff) + 링 r7→13→19 + 용암 균열(W2→W1→W0 점) + 불씨 → 재 |
| quake | 96 · 7 · 40/50/60/70/90/110/140 | any | hitbox_center (48,56)=바닥 · 바닥 · hit_judge | G06 G09 / X0 X1 / 22 24 27 / 대검 | **2단 낙뢰**: f1 1단(3겹) → 링 r10→20, **f4(220ms) 2단** 4겹 더 굵은 낙뢰(다른 각도) + 링 r28→36→42 + 균열 10 + 재·불티 |
| pulverize | 64 · 5 · 40/40/60/80/110 | any | hitbox_center (32,32) · 바닥 · hit_judge | G06 G09 / X0 X1 / 22 24 27 / 대검 | 코어 → 링 r8 + 쐐기 파편 8 분출 + X 표(X1→27) → r15 → r21 점선 → 재 |
| ironwall | 64 · 4 · 40/50/70/90 | 4 | player_pivot **(32,42)** · 위 · guard_release | G06 G09 / X0 X1 / 22 24 27 / 대검 | 몸 중심 전방 10px 벽 4px(W0·W2/W3·X0, ±12) 섬광 → 벽 뒤 가지 번개 + 전방 물결 + 재 → 점선 |
| giant | 64 · 4 · 90×4 루프 | any | player_pivot (32,52)=발 · 바닥 · attack_start, followsPlayer | G06 / X1 / 22 / 대검 | 발밑 고리 r20(W0 + 도는 W2 토막 + X1) + 안쪽 W1 점선 + 양옆 고정 용암 기둥(x 14/48, 16px, 밝은 토막이 3px/f 상승, 12px 주기 = 이음새 없음) |
| hit_burst (신규) | 24 · 4 · 40/40/40/50 | any | hitbox_center (12,12) · 위 · hit | — / X0 X1 / 18 22 26 / — | 콘셉트 승격. 광선 6 (18·26·X 코어) |
| hit_spark | 24 · 4 (동일 그림) | any | 동일, `alias: hit_burst` | 동일 | 호환용. **16→24 로 커짐**. 시스템이 hit_burst 로 전환하면 삭제 가능 |
| crit_burst | 32 · 5 · 40/40/50/60/80 | any | hitbox_center (16,16) · 위 · hit_crit | — / X0 X1 / 18 19 21 22 24 26 27 / — | 광선 8 (3겹) + 고리 r8→12→14.5 + 네 귀 글린트 → 불티 |
| telegraph_line | 16 · 2 · 120 루프, tile·rotate | any | hitbox_center (0,8) · 바닥 | — / — / 18 22 24 25 27 / — | 콘셉트 승격. 4px 실선(y6~9), 코어 토막이 +x 로 8px/f 흐름 |
| telegraph_circle | 64 · 6 · **진행도** | any | hitbox_center (32,32) · 바닥 | — / X0 / 18 20 21 22 23 24 26 27 / — | 콘셉트 승격. 범위 링 r22(scale = R/22), 수렴 링 r31→22, f5 백열 |
| telegraph_cone | 64 · 6 · **진행도** | 4 | hitbox_center (32,32)=꼭짓점 · 바닥 | — / X0 / 18 20 21 22 23 24 26 27 / — | 선과 같은 4~5px 구조 두 변(코어 토막이 꼭짓점→바깥 흐름) + 범위 호 r27(scale = R/27) + 수렴 점선 호, f5 백열 |
| telegraph_aura (신규) | 64 · 4 · 100×4 루프 | any | hitbox_center (32,32) · 바닥, followsTarget | — / X0 / 18 20 21 22 23 25 27 / — | 콘셉트 + 3회차 비평 반영: 토막 안쪽 끝에 안으로 향한 쐐기 2px (정지 화면에서도 수렴) |
| enemy_bullet | 8 · 1, rotate | any | projectile (5,4) · 위 | — / X0 / 18 21 22 24 / — | 18 림 + 22 몸 + **X0 코어** (어두운 바닥에서 보이게) + 꼬리 24/21. 기존 G01 구슬 대체 |
| boss_fan_shot | 10 · 2 · 80 루프 | any | projectile (5,5) · 위 | — / X0 / 18 19 21 22 24 26 27 / — | 18 림 + 21/22 몸 + 코어 27↔X0 맥동 |
| muzzle_flash | 12 · 2 · 40/60 | 4 | hitbox_center (6,6)=총구 · 위 · enemy_shoot | — / X0 / 22 23 25 27 / — | 쐐기 X0 코어 + 27/25 + 23 + 대각 광선 → 작은 불꽃 |

전부 색 예산 ≤11(무기) / 층 램프 ≤8 + 코어(공통), 고립 0, 반투명 0 — `color_report` 마지막 실행 ALL OK.

## 2. JSON §3.2 필드 (수치 = fx-design.md 6절)
- `weapon`, `secondary: "fx.weapons.<id>"` — 칼·대검 시트. 공통은 `weapon: "any"`.
- `trail {color: W1, alpha, ms, fromFrame}`: katana_slash·greatsword_slash 0.6/120/f2 · iai·batto 0.7/180/f2 · longinvuln 0.7/180/f1 · wide 0.7/220/f2. 적중형(dashcrit)·투사체·예고에는 없음.
- `flash {color, alpha, ms:40, atFrame}`: iai X1 0.18 f1 · wide X1 0.22 f1 · crush·quake·pulverize 대검 W3 `#f9b23c` 0.16 f1.
- `shake {px, ms}`: iai 2/60 · wide 3/80 · crush·weight 2/60 · quake·pulverize 4/120.
- `quake.secondStage {frame:4, atMs:220, flash, shake}` — 2단 판정 시각에 두 번째 섬광·흔들림.
- `progressDriven`: telegraph_circle·telegraph_cone (`frame = min(5, floor(progress*6))`, ms 는 참고값). `followsTarget`: telegraph_aura. `followsPlayer`: batto·longinvuln·giant. `tile·rotate·drawnFacing`: telegraph_line. `rotate·drawnFacing`: enemy_bullet. `scale: "allowed"`: 예고 4종. `depth`, `pivotNote`, `note` 전부 기입. hit_spark 에 `alias: "hit_burst"`.

## 3. see → critique → fix 기록
1. 1회차(3배): 색 예산 초과 3종 — weight·quake 층 강조 4칸(22·24·26·27) → 26 제거, telegraph_cone 9칸 → 코어 맥동 27↔25 를 27↔24 로(24 는 수렴 호가 이미 씀). 2회차 시각: weight 먼지가 평평한 회색 덩어리('귀')로 읽힘, giant 기둥이 통째로 스크롤해 공중에 떠 보임, longinvuln 속 체커(mod 2)가 회색 몸통으로 읽힘.
2. 2회차(5배): 먼지를 `puff`(어긋난 어두운 디스크 2 + 위·왼쪽 밝은 디스크 + 돌기)로 → 구름으로 읽힘. 기둥을 고정(고리 높이에서 위로 16px) + 안을 흐르는 밝은 토막(12px 주기/4f)으로 → 이음새 없이 '솟는 용암'. 속 사선 mod 3/4 → 비치는 몸.
3. 3회차(1배 띠 + 전투 목업): 은빛 베기·호박 예고·대검 적색이 세 층으로 분리됨. 대검 W2 `#d8441c` 가 1층 호박 21 과 겹치지 않음. 지진 2단 낙뢰(f4)가 1배에서 가장 큰 사건으로 읽힘. 닫히는 원 f5·부채꼴·오라 1배 가독 OK. 섬광 오버레이(W3 0.16)는 바닥 디테일을 지우지 않음. SHIP.

## 4. 임시 결정 (도영 님 검수 대상)
1. **batto 7프레임 380ms** — 대쉬(240ms)보다 길어 꼬리 140ms 가 대쉬 끝난 뒤 남는다(의도: 긴 잔상). 짧게 원하면 f5·f6 제거(5f 230ms).
2. **ironwall 피벗 (32,42) = 발** 로 통일(기존 (16,22) 몸 중심 규약 폐기). 벽은 몸 중심 전방 10px → down 방향은 발 선과 같은 높이에 가로 벽, up 은 머리 위 20px.
3. **giant 64×64 피벗 (32,52)** (설계 8절 '루프형 ×1.33' = 43×53 대신 64 정사각으로). 기둥 높이 16px = 몸통 높이.
4. **quake 96 · 7f, 피벗 (48,56)** — 설계 8절 표의 '적중형 64·5~6f' 대신 지시대로 96·7f. 2단 판정 시각 220ms 유지(f4 시작). 낙뢰는 캔버스 위 가장자리에서 떨어지므로 회전 없음(any).
5. **hit_spark 를 24×24 hit_burst 와 같은 그림으로 교체** — 시스템 로드 크기 자동이지만 16→24 커짐. hit_burst 로 전환되면 hit_spark 파일 삭제 요청.
6. **enemy_bullet 을 발광 탄(18 림 + 22 몸 + X0 코어)으로** — '어두운 G01 구슬' 이미지는 버렸다. 화승총 탄이 빛나는 것이 어색하면 코어만 X0 로 두고 몸을 G04 로 되돌리는 대안.
7. **telegraph_cone 반지름 27 (scale = R/27)**, 변 두께 5px(18·몸·코어·몸·18) — 선(6px)과 1px 차이. 꼭짓점 = 캔버스 중심이라 캔버스 절반만 쓴다(기존과 같음).
8. **trail 대상에 longinvuln 포함**(6.1 '대쉬 베기(허보)'), fromFrame 1. dashcrit 은 적중형이라 제외.
9. **crush 에도 flash(W3 0.16)·shake 2px 60ms** — 6.2 표에는 지진·분쇄만 있으나 crush 도 낙뢰 모티프라 1차 수치(4절 표)로 넣었다.
10. **weight 섬광 없음, shake 2px 60ms 만** — 낙뢰가 아니라 내려찍기.
11. JSON 의 `flash`·`trail`·`shake` 를 콘셉트의 문자열 메모가 아니라 **구조화 객체**로 기입(계약 §3.2 형식). `scale` 은 기존 관례대로 `"allowed"` 문자열 유지.

## 5. 시스템 전달 요점
- **크기·피벗 변경**: katana_slash·greatsword_slash 32→48 (16,26)→(24,34) / iai 48→64 (24,34)→(32,42) / batto 32→64 (16,26)→(32,42), 4f→7f / wide 64→96 (32,42)→(48,58), 6f→7f / zangetsu 48→64 (24,34)→(32,42) / longinvuln 32→64 (16,26)→(32,42), 4f→5f / dashcrit 24→64 (12,12)→(32,32), 4f→5f / crush 48→64 (24,24)→(32,40)=바닥, 4f→6f / weight 32×24→64 (16,22)→(32,40), 4f→6f / quake 64→96 (32,32)→(48,56)=바닥, 6f→7f / pulverize 48→64 (24,24)→(32,32), 4f→5f / ironwall 32→64 (16,22)→(32,42)=발, 3f→4f / giant 32×40→64 (16,36)→(32,52) / hit_spark 16→24 (8,8)→(12,12) / crit_burst 32 유지, 5f / telegraph_line 8→16 (0,4)→(0,8), 두께 2→4 / telegraph_circle 32→64 (16,16)→(32,32), 2f 루프→**6f 진행도**, scale R/15→R/22 / telegraph_cone 32→64, 2f 루프→**6f 진행도**, scale R/15→R/27 / enemy_bullet·boss_fan_shot·muzzle_flash 크기·피벗 동일.
- **신규 id**: `hit_burst`(24, hit_spark 대체), `telegraph_aura`(64 루프, followsTarget — 돌진·대기술 예고).
- **재생 시점**: 기존 spawn 키 유지. f0(예비 40ms)는 판정 40ms 전 재생(`spawn: attack_frame2 - 40ms`)이 이상적, 불가하면 f0 를 건너뛰고 f1 부터.
- **2단 판정**: quake f4 시작 = 220ms. `secondStage` 필드 참조.
- **깊이**: batto 아래(플레이어), longinvuln 위, giant·zangetsu·crush·weight·quake·pulverize·예고 4종 바닥, 나머지 위.
- **blood**·**B 묶음**은 이 노트 범위 밖.

## 6. 바이블 반영 대기 (art-bible 4.3 에 추가/교체할 행)
위 1절 표 전체 + 4.3.1 의 hit_spark·telegraph_*·enemy_bullet·boss_fan_shot·muzzle_flash 행 교체 + 4.3.2 의 wide·zangetsu·longinvuln·dashcrit·quake·pulverize·ironwall·giant 행 교체 + 4.3 의 katana_slash·greatsword_slash·iai·batto·crush·weight 행 교체. 원칙 한 줄: "무기 이펙트는 W0 가장자리 → 보조 램프 몸체 → 1px 백열 코어, 같은 궤적 2~3겹을 1프레임씩 어긋나게. 적·보스 예고와 공통 피격은 층 램프 + 코어만."
