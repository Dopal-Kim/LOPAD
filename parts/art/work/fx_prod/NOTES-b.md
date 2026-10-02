# fx_prod — B 묶음: 단검 7 · 활 9 · 보조 동작/대쉬 7 (43라운드 양산, 아트, 2026-10-02)

빌드: `python3 parts/art/work/fx_prod/build_b.py` → `assets/sprites/fx/` 23종 PNG/JSON(**같은 id 로 기존 파일 교체**) + `preview_b.png`(3배 블록 + 1배 띠) + `preview_b_fight.png`(1배 목업 + 3배).
칼·대검·공통·예고 묶음은 `build_a.py`/`NOTES-a.md`(다른 아트 에이전트). `README.md`·`art-bible.md`·`fx-design.md`·`palette/**` 는 손대지 않았다 — 바이블 4.3 에 옮길 내용은 아래 표.
근거: `fx-design.md` 전 절(3층 색 · 겹 1프레임 지연 · 섬광 → 광선 → 긴 꼬리 · 보조색 1무기/시트 · 예산 ≤11), 결정 `2026-10-02-round-42-infernum-fx.md` 43라운드 검수 절, 계약 `art-assets.md` §3~3.2.

## A. 단검 7종 (보조색 보라 그림자 `fx.weapons.dagger`, 층 강조 ≤3 = 글린트·불티만)

| id | 크기 | 방향 | 프레임 · ms · 루프 | 앵커 · 피벗 · 깊이 | 색 | 연출 · 재생 시점 |
|---|---|---|---|---|---|---|
| dagger_slash | **48** (32) | 4 | **5** · 40/50/60/70/90 | player_pivot **(24,34)** · 위 | X0 X1 / 22 24 27 / W0~W3 | 짧고 빠른 호(140°, r11, 3.6px) 2겹 = 본 띠(W0·W1·W2·W3 + 1px 코어) + 바깥 r+3 **그림자 잔상**(W1/W0, 1프레임 지연). f0 예비 코어 점선 → f1 본 → f2 광선 2 + 식음 → f3 어두운 띠 → f4 점선 꼬리. `attack_frame2`, 트레일 W1 0.6 120ms f2~ |
| twin | **64** (32) | 4 | **7** · 40/40/60/80/100/120/140 | player_pivot **(32,42)** · 위 | 같음 | 안쪽 호 r13 **f1 백열 = 1타**, 바깥 호 r19 **f2 백열 = 2타**(1프레임 늦음), 각자 그림자. f2 광선 3 → f3 식음 → f4 어두운 띠 → f5 점선 → f6 꼬리. 섬광 X1 0.18 40ms f1 + 흔들림 2px 60ms, 트레일 0.7 180ms |
| gale | **64** (24) | 4 | 4 · 60/70/80/90 · 루프 | player_pivot (32,42) · **아래**, 따라감 | X1 / — / W0~W3 | 몸 뒤를 감싸는 호(r10.5, 도는 W3 글린트) + 뒤로 흐르는 곡선 바람 줄 3(2px: 색 + W0 그림자 밑줄) + 가운데 줄 X1 코어 토막. 토막 9 on 3 off, 3px/프레임 → 4프레임 = 주기 12 = 이음새 없음. `loop_move`, 방향 = 이동 방향 |
| dance | **96** (32) | 4 | **7** · 40/40/50/70/110/140/160 | player_pivot **(48,58)** · 위 | 같음 | 3중 베기 군집: r14 정방향(f1 백열) → r21 **역방향**(f2 백열) → r28 정방향(f3 백열 + 광선 4 + 네 귀 글린트) 각자 그림자 → f4 식음 → f5 점선 셋 → f6 꼬리. `hitFrames [1,2,3]`. 섬광 0.22 + 흔들림 3px 80ms, 트레일 0.7 220ms. twin 대체 |
| bleed | **24** (16) | any | 4 · 125×4 · 루프 | hitbox_center (12,12) · 위, 적 따라감 | X1 / **17 18 20 (피)** / W0 W1 | 핏방울 3줄(위상 0/2/1, 3×4 + 늘어진 꼬리 → 바닥 튐) + W1 그늘·W0 밑 + 발밑 W0 웅덩이. f0 = 틱 글린트 X1. 한 바퀴 500ms = 틱 |
| afterimage | **64** (24) | 4 | **5** · 40/60/80/100/130 | player_pivot **(32,42)** · 바닥, 고정 | X0 X1 / 22 24 27 / W0~W3 | 대쉬 출발점 분신 군집: 돌진 실루엣(W2, 우·하 림) + 좌우(대쉬에 수직) 11→15→18px 로 벌어지는 분신 W1 → 세로 줄무늬 → 조각, W0 웅덩이 13→15→13→9→5 수축, f1 교차 베기 2줄(W3 + X0/X1). `dash_start` |
| assassin | **64** (32) | any | **5** · 40/50/60/80/110 | hitbox_center (32,32) · 위 | X0 X1 / 24 25 27 / W0~W3 | 콘셉트 `concept_assassin` 48 → 64 승격: 웅덩이 r15~18 + 분신 3(idle 실루엣, W0→W1→W2)이 모여듦 → 교차 섬광 2줄(3겹) → 세로 줄무늬 → 웅덩이 수축. `hit` |

## B. 활 9종 (보조색 번개 청백 `fx.weapons.bow`, 투사체 `rotate`·`drawnFacing right` 유지)

| id | 크기 | 방향 | 프레임 · ms · 루프 | 앵커 · 피벗 · 깊이 | 색 | 연출 · 재생 시점 |
|---|---|---|---|---|---|---|
| bow_arrow | **12×6** (8×8) | any(rotate) | 1 | projectile **(6,3)** | X0 X1 / — / W1 W2 W3 | 코어 자루(X1 + W2 그늘) + 청백 깃·꼬리(W1/W2) + 촉 W3→X0 |
| bow_arrow_aimed | **16×8** (12×6) | any(rotate) | 1 | projectile **(8,4)** | X0 X1 / — / W0~W3 | 3폭 자루(W3 / X1 / W2) + W0 밑 가장자리 + 긴 촉 X0 2px + 깃 2겹 |
| pierce | **32×8** (16×8) | any(rotate) | 4 · 60×4 · 루프 | projectile **(30,4)** · 화살 아래 | X1 / — / W0~W3 | 빛줄: 코어 X1(머리 9px) → W3 → W2 → W1, 위아래 W2/W1, 머리 쪽 W0 가장자리, 끝 흔들림. `loop_move` |
| scatter | **32** (16) | any(rotate) | 4 · 40/50/60/70 | projectile **(4,16)** = 발사점 | X0 X1 / 24 27 / W0~W3 | ±24° 3갈래 번개 광선(3겹 W0·W2·X0/X1) 짧게 → 전체 → 바깥 토막 점선 → 조각. 발사점 섬광 X0 + W3 링. `shot` |
| flash | **32×8** (24×8) | any(rotate) | 4 · 50×4 · 루프 | projectile **(30,4)** · 화살 아래 | X0 X1 / — / W0~W3 | 코어 X0/X1 거의 전체 + W3 띠 + W0 가장자리 + 꼬리를 뛰는 번개 토막 2(W3/X1, 3px/프레임 뒤로). pierce 대체 |
| heavyarrow | 16×8 | any(rotate) | 1 | projectile (8,4) | X0 X1 / — / W0~W3 | 두꺼운 자루(W0 테두리·W3·X1·W2) + 큰 미늘촉(W3 + X0 2px) + 깃 2겹. `aimed_shot` (무채 자루 → 보조색) |
| heavyarrow_hit | **64** (24) | any | **5** · 40/50/60/80/110 | hitbox_center **(32,44)** · 위 | X0 X1 / 22 26 27 / W0~W3 | 콘셉트 `concept_heavyarrow_bolt` 48 → 64 승격: 가는 예고선 → 번개 낙하 3겹 + 가지 2 + 적중 십자 X0 → 링 r8 + 가지 번개 3 → 점선 잔광 + 링 r14 → 꼬리 r18. 섬광 W3 `#cdefff` 0.14 40ms f1 + 흔들림 2px 60ms. 번개는 캔버스 위에서 떨어짐(회전 없음) |
| rain | **32** (24) | any(rotate) | 4 · 40/50/60/70 | projectile **(4,16)** | X0 X1 / 24 27 / W0~W3 | ±50°/±25°/0° 5갈래, scatter 와 같은 구조. `shot`, scatter 대체 |
| seek | **24** (16) | any(rotate) | 4 · 60×4 · 루프 | projectile **(20,12)** · 화살 아래 | X0 X1 / — / W0~W3 | 유도 소용돌이: 꼬인 두 가닥(W3/W2 → 뒤로 W1/W0, 진폭 커짐)이 뒤로 흐름(4f = 2π) + 교차점 X0 + 머리 X1 |

## C. 보조 동작 · 대쉬 7종

| id | 크기 | 방향 | 프레임 · ms | 앵커 · 피벗 · 깊이 | 색 | 연출 · 재생 시점 |
|---|---|---|---|---|---|---|
| parry_flash | **48** (32) | any | **5** · 40/50/60/80/100 | hitbox_center **(24,24)** = 접점 · 위 | X0 X1 / 18 19 21 22 24 25 27 / **보조색 없음** | 시간 정지 섬광: f0 전체 X0 십자 + X1 코어(히트스톱·오버레이 X1 0.25 40ms 동시) → f1 동심 고리 2(24/22, 4px 간격) + 짧은 X0 광선 → f2 고리 확장 + 네 귀 글린트 → f3 점선 → f4 조각. `parry_success` |
| guard_wave | **64×32** (48×24) | 4 | 4 · 50/60/70/80 | player_pivot **(32,16)** = 발 · 바닥 | X1 / — / 대검 W0~W3 (W2 = **#d8441c**) + G06 G09 | 발 앞 반타원(세로 0.5) 3겹(W0 테두리·W2 용암·X1 1px 점선) r10→18→25→29 + 가장자리 재 + 짧은 균열 2(W2 → f3 W0 점). 반경 29 ≈ 밀쳐내기 40px 의 70%. `guard_release` |
| shadowstep_ghost | 16×24 | 4 | 3 · 60/80/100 | player_pivot (8,23) · 바닥, 고정 | — / — / **단검 W0 W1** (무채 → 보조색) | 출발점 실루엣 W0 단색 + W1 림 → 세로 줄무늬 W1(2 on 1 off) → 조각, 발밑 W0 웅덩이 r7→5→3. 암살 분신과 같은 어휘. `shadowstep_start` |
| aim_charge | **32** (24) | any | 6 · 진행도 | player_pivot **(16,16)** = 몸 중심 · 위 | X0 X1 / — / 활 W0~W3 | r10 고리 W1 점선 + 눈금 4 → 진행도만큼 W3(가장자리 W0 2.8px)로 참, 머리 X1 2px → f5 완료 = X0 고리 + W3 점선 고리 r13 + 네 귀 가지 번개(4~5px, W3 + X1 끝) + 중심 X0. `frame = min(5, floor(progress*5))` |
| aim_line | 8×2 | any(rotate, tile) | **2 (상태)** · fps 0 | player_pivot (0,1) · 바닥 | X0 X1 / — / W2 W3 | 코어 점선 4 on / 4 off: **f0 차지 중** = X1 코어 + W2 밑줄, **f1 완료** = X0 코어 + W3 밑줄. `stateFrames {charging:0, complete:1}` — 미지원이면 f0 만 |
| dash_dust | 16×8 | 4 | 3 · 50/70/90 | player_pivot (8,6) · 바닥, 고정 | G06 G09 G12 | **그림 유지**(42라운드 결정: 무채). JSON 에 `weapon: any` 추가 |
| dash_trail | 16×24 | 4 | 3 · 40/60/80 | player_pivot (8,23) · 바닥, 고정 | G02 G03 G04 | **그림 유지**(결정: 시스템 틴트). JSON `tint` 메모: 발도술·허보·잔상 노드일 때 그 무기 W1 로 **`setTintFill`**(시트가 G02~G04 라 곱셈 `setTint` 는 검게 됨) |

검사(`color_report`, 마지막 실행 **ALL OK**): 시트마다 무채 ≤2(먼지·잔상 예외 3) + 코어 ≤2 + 층 강조 ≤3(보조색 없는 parry 는 ≤8) + 보조 4, 합 ≤11 · 한 시트에 한 무기 · 고립 픽셀 0 · 반투명 0. PNG 크기 = frameWidth×frames · frameHeight×directions 확인.

## see → critique → fix 기록 (3회)
1. **1회차**(3배 블록 + 1배 띠 + 목업): 단검 그림자 잔상이 W0 단색이라 어두운 바닥(미리보기 G02, 실제 1~2층)에서 보이지 않음 → 그림자 띠를 [W1, W0] 2톤 2.4px 로. 질풍이 짧은 점선 3줄이라 바람으로 안 읽힘 → 몸 뒤를 감싸는 호 + 곡선 줄 2px(색 + W0 밑줄), 주기 12 / 3px·프레임. 잔상 분신이 ±8px 로 겹쳐 덩어리 → ±11/15/18 로 벌림, f3 점선 테두리가 사선 해치 노이즈 → 조각만. 잔상 층 강조 4칸(22·24·25·27) 초과 → 25 제거. 출혈 방울 19/18 명도차 부족 → 20/18/17. 그림자 걸음 f0 W0 실루엣이 어두운 바닥에서 사라짐 → W1 전체 림.
2. **2회차**: 그림자 2톤이 바깥 두 번째 고리로 읽혀 '겹' 성립, 난무 3호 = 백열/정상/식음 세 단계가 한 프레임에 보여 군집이 읽힘, 출혈·잔상 OK, ALL OK. 남은 것: 질풍이 화살촉 모양(곡률 과함, 줄 짧음).
3. **3회차**: 질풍 곡률 0.55→0.32, 길이 22/27→26/29 → 바람 스우시로 읽힘. 목업 1배: 보라 호 + 백열 코어 / 호박 패링 링 / 청백 번개 / 흑백 캐릭터가 네 층으로 분리, 패링 오버레이 0.25 는 바닥 디테일을 지우지 않음. **SHIP.**

## 임시 결정 (도영 님 검수 대상)
1. **크기·피벗 변경**(fx-design 8절 적용): 위 표의 굵은 값. 투사체 피벗은 기존 비율 유지(화살 중심 = 꼬리 끝 2px 앞, 발사점 = (4,16)). bleed·seek 16→24, flash 24→32, pierce 16→32(지시대로; 8절의 "pierce/scatter 유지" 문구 대신 지시 목록을 따름).
2. **난무 타격 시각**: 기존 0·2·4프레임(80ms 간격) → **f1/f2/f3 시작(0/40/90ms, f0 제외 기준)**. 3타가 더 촘촘(인페르노식 연타). 시스템 `hitFrames` 를 읽어 판정을 맞추거나, 판정은 그대로 두고 그림만 겹쳐도 됨.
3. **쌍격 2타 = f2 시작(40ms 뒤, f0 제외)**. 기존 "2프레임 = 두 번째 타격" 과 같은 간격.
4. **aim_line 2프레임(상태 프레임)**: 차지 완료 시 코어 X0 (fx-design 5절). 시간 애니가 아니라 `stateFrames` 로 고르는 방식 — 계약에 없는 필드. 미지원이면 f0 만 써도 됨. 4px 굵기(fx-design 5절) 대신 지시대로 8×2 유지.
5. **gale 64**: 바람이 몸 뒤 24~29px 까지 뻗음(기존 24 캔버스의 2배). 좁은 방에서 길면 길이 26/29 → 18/22 로 줄일 수 있음.
6. **guard_wave 는 대검 보조색**(fx-design 5절). 팔레트 `fx.weapons.greatsword.ramp[2]` 는 다른 에이전트가 `#d8441c` 로 갱신했고 그 값을 사용했다 — 혹시 옛 값이면 스크립트가 결정값으로 덮어 그린다(팔레트 파일은 쓰지 않음).
7. **shadowstep_ghost 가 무채 → 단검 보조색**(fx-design 5절대로). 층 스왑 무관은 유지(보조색은 고정색).
8. **dash_trail 틴트 방식 = `setTintFill`** 권고(아트 메모). 곱셈 틴트를 쓰려면 밝은 무채(G08~G12) 시트가 따로 필요 — 그 경우 재인터뷰.
9. 예비 프레임 f0(40ms) 는 dagger_slash·twin·dance 에 넣었다(결정: spawn 오프셋 지원 시 유지). 미지원이면 f1 부터 재생(JSON `spawnNote`).
10. 2차 적중형 afterimage 를 **64·5f** 로(8절 "적중형 64 · 5~6f" 적용, 24→64 는 분신 3 + 웅덩이가 들어가야 해서).

## 시스템 전달 요점
- **크기·피벗 변경** (로드 크기는 JSON 자동): dagger_slash 32→48 pv(24,34) / twin 32→64 pv(32,42) / gale 24→64 pv(32,42) / dance 32→96 pv(48,58) / bleed 16→24 pv(12,12) / afterimage 24→64 pv(32,42) / assassin 32→64 pv(32,32) / bow_arrow 8×8→12×6 pv(6,3) / bow_arrow_aimed 12×6→16×8 pv(8,4) / pierce 16×8→32×8 pv(30,4) / scatter 16→32 pv(4,16) / flash 24×8→32×8 pv(30,4) / heavyarrow_hit 24→64 pv(32,44) / rain 24→32 pv(4,16) / seek 16→24 pv(20,12) / parry_flash 32→48 pv(24,24) / guard_wave 48×24→64×32 pv(32,16) / aim_charge 24→32 pv(16,16). 변경 없음: heavyarrow, shadowstep_ghost, aim_line(프레임 1→2), dash_dust, dash_trail.
- **프레임 수 변경**: dagger_slash 4→5, twin 4→7, dance 6→7, afterimage 4→5, assassin 4→5, heavyarrow_hit 3→5, parry_flash 4→5, aim_line 1→2. ms 배열은 JSON.
- **JSON 신규 필드**(계약 §3.2): `weapon`, `secondary`, `trail{color,alpha,ms,fromFrame,widthRatio}`(dagger_slash·twin·dance), `flash{color,alpha,ms,atFrame}`(twin·dance·heavyarrow_hit·parry_flash), `shake{px,ms}`(twin·dance·heavyarrow_hit), `hitFrames`(twin·dance), `spawnNote`, `stateFrames`(aim_line), `tint`(dash_trail), `tailFrames`, `followsPlayer`/`followsTarget`/`progressDriven`/`pivotNote` 는 기존대로.
- **재생 시점·깊이·루프 종료** 는 35라운드와 동일(`spawn` 키 그대로). gale 은 `followsPlayer: true` 명시.

## 바이블 반영 대기 (art-bible 4.3.2 표 교체)
위 A·B·C 표 그대로 + 4.3 베기 행의 dagger_slash / bow_arrow / bow_arrow_aimed / pierce / scatter / twin / gale 수치.
