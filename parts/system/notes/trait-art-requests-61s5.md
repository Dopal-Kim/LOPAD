# 61 단계 5 (P13) 개성 그림 요청 — 전투 fx · 카드 그림

시스템 → 아트. 근거: `parts/producer/decisions/2026-10-06-P13-combat-variety.md` §1, 계약 art §27 · UI §18.1. 개성 목록 = `data/traits.json` (무기당 14장 + 공명 9).
지금은 아래 '지금 대체' 열의 기존 fx(또는 윤곽)로 그린다. 파일이 매니페스트에 생기면 **시스템 수정 없이** 전용 그림으로 바뀐다.

## 0. 공통 규칙

| 항목 | 규칙 |
|---|---|
| 전투 fx 이름 | `sprites/fx/v3/trait_<무기>_<개성 id>[_<부위>].png/.json` (공명은 `trait_<공명 id>[_<부위>]` — 예 `trait_res_katana_insight`) |
| 부위 | 없음(본체) · `launch`(띄움 시작) · `land`(착지) · `impact`(벽·기둥·적에 박힘) · `bind`(묶임 고리) · `in`/`out`(나타남·사라짐) · `soak`(빨아들임) · `fire`(불길) · `spark`(불똥) · `snap`(덫 닫힘) · `burst`(터짐) · `mark`(표식) · `wave`(투사체) |
| 단위 | 도트, `pixelScale: 0.5` (64 도트 = 1칸 = 월드 16px). 아래 크기는 프레임 한 장 |
| 그리는 배율 | 전용 fx 는 시트 배율 그대로(시스템이 더 키우지 않음). 대체 fx 만 주인공 렌더 배율을 곱한다 |
| 앵커 | `mob_feet`(적 발 피벗) · `hitbox_center`(몸 중심) · `player_pivot`(주인공 발) · `contact`(박힌 자리 — 벽 면·두 적 사이) · `projectile`(진행 각도로 회전, `rotate: true`, `drawnFacing: "right"`) · `floor`(바닥 깊이) |
| 회전 | `angle` 을 받는 fx(표에 '회전')는 오른쪽을 보고 그린다 — 시스템이 진행·충돌 방향으로 돌린다 |
| 루프 | '수명' = `loopRange` 시트(생김 → 루프 → 사라짐, 시스템이 `durationMs` 로 끝냄). 그 밖은 1회 |
| 광원 | JSON `light` (색·반경 도트·ms). '없음' 이면 넣지 않음 |
| 색 | 무기 강조색 + 1층 램프. 불 = `pool_liquor_fire` 계열, 묶음·사슬 = 청회(#9ab0d8), 사슬 끌림 = 적갈(#b04848), 달 = 청백(#c8d8f0) |
| 로드 | 얻은 개성·이 무기 공명의 fx 만 지연 로드(`TraitRules.loadFx`) — 런 VRAM 부담 작게. 한 장 0.3~1.5MB 안팎 권장 |

## 1. 전투 fx 표 (개성 56 + 공명 9)

### 칼 (katana)

| 이름 | 개성 | 모양 | 크기(도트) | 프레임·ms | 루프 | 앵커 | 광원 | 지금 대체 |
|---|---|---|---|---|---|---|---|---|
| `trait_katana_k_shadowThrust` | 그림자 찌르기 | 쓰러진 적 자리에서 그림자 분신이 다음 적으로 찌르는 가는 직선 + 끝 섬광 (회전) | 256×64 | 6f 40/40/50/60/80/100 | 1회 | contact(쓰러진 자리, 왼끝) | 없음 | `afterimage` + 윤곽 선 |
| `trait_katana_k_edgeLift_launch` · `_land` | 칼등 띄우기 | launch: 칼등이 아래에서 위로 쳐올리는 호 + 먼지 · land: 떨어진 자리 원형 먼지·금 | 96×128 · 128×64 | 5f 40/50/60/70/90 · 6f 40/50/60/80/100/140 | 1회 | mob_feet · floor | 없음 · land 백열 r48 100ms | `dash_dust` · `crush` |
| `trait_katana_k_parryShove` · `_impact` | 흘려 밀기 | 본체: 패링 둘레로 퍼지는 반달 파동 · impact: 벽·기둥·적에 박히는 충돌(파편 + 금, 회전) | 192×192 · 128×128 | 5f 40/50/60/80/100 · 6f 40/50/60/70/90/120 | 1회 | player_pivot · contact | 본체 없음 · impact 백열 r48 120ms | `guard_wave` · `hit_burst` |
| `trait_katana_k_bladeBind` | 칼 감기 | 칼날이 적 무기를 감아 채는 나선 섬광 (끌어당김 선은 시스템 윤곽) | 96×96 | 5f 40/50/60/70/90 | 1회 | hitbox_center | 없음 | `katana_counter` |
| `trait_katana_k_shadowVault_out` · `_in` | 그림자 넘기 | out: 주인공 실루엣이 먹물처럼 흩어짐 · in: 적 등 뒤에서 실루엣이 모이며 돌아서 베기 | 96×144 · 128×144 | 6f 40/40/50/60/70/90 · 6f 40/40/50/60/80/100 | 1회 | player_pivot | 없음 | `shadowstep_ghost`·`afterimage` · `katana_counter` |
| `trait_katana_k_issenBack` | 물러서며 베기 | 뒤로 물러서며 그리는 원형 한 바퀴 베기 (가는 선) | 192×192 | 6f 30/40/50/60/80/100 | 1회 | player_pivot(판정 원점) | 없음 | `katana_spin` |
| `trait_katana_k_iaiWave_launch` · `_wave` | 발도풍 | launch: 발도 순간 앞으로 터지는 초승달 · wave: 날아가는 초승달 검풍 (투사체) | 128×128 · 96×64 | 4f 40/50/60/80 · 4f 60 루프 | 1회 · 투사체 루프 | player_pivot(회전) · projectile | wave 청백 r40 | `katana_crescent` · 윤곽 사각형 |
| `trait_katana_k_iaiChain` | 연쇄 발도 | 다음 적 앞까지 미끄러지는 낮은 잔상 줄 (회전) | 192×64 | 5f 40/40/50/60/80 | 1회 | player_pivot(왼끝) | 없음 | `dash_trail`·`afterimage` |
| `trait_katana_bloodGale` | 피바람 | 회전 한 바퀴를 더 도는 붉은 피바람 고리 | 192×192 | 6f 40/40/50/60/70/90 | 1회 | floor(주인공 발) | 없음 | `chain_bloodlust` |
| `trait_katana_liquorWhirl` · `_fire` | 술 회오리 | 술 줄기가 칼을 따라 감기는 회오리 · fire: 불붙은 술 회오리 | 192×192 | 6f 40/50/50/60/70/90 | 1회 | floor | fire 주황 r96 300ms | `pool_liquor` · `pool_liquor_fire` |
| `trait_katana_k_sparkCleave` · `_spark` | 불똥 내려베기 | 본체: 선 끝 작은 불씨 웅덩이(바닥) · spark: 바닥을 긁는 불똥 튐 | 96×64 · 48×48 | 6f 60 루프(수명) · 4f 40/40/50/60 | 본체 수명 · spark 1회 | floor | 본체 주황 r48 · spark 주황 r24 60ms | `fire_pool` · 점 윤곽 |
| `trait_katana_k_groundPin_bind` · `_impact` | 땅에 박기 | bind: 적 발밑 바닥 금 + 박힌 말뚝 고리(수명) · impact: 묶임이 풀리며 튕겨 나가는 충돌 | 128×64 · 128×128 | 4f 80 루프(수명) · 6f | 수명 · 1회 | floor · contact | 없음 | `katana_cleave_crack` · `hit_burst` |
| `trait_katana_k_moonRelay` | 달빛 잇기 | 달 분신이 다음 적으로 옮겨 가며 긋는 청백 선 (회전) | 256×64 | 6f 40/40/50/60/80/100 | 1회 | contact(쓰러진 자리) | 청백 r32 | `katana_fullmoon` |
| `trait_katana_k_moonPools` | 취월 | 술 웅덩이 수면에서 솟아오르는 달 분신 실루엣 + 물결 | 128×160 | 7f 40/40/50/60/70/80/100 | 1회 | floor(웅덩이 중심) | 청백 r48 | `katana_fullmoon`·`katana_crescent` |
| `trait_res_katana_insight` | 공명 되받는 달 | 밀치거나 끌어온 적 옆에 나타나는 작은 달 분신 | 96×144 | 6f | 1회 | contact | 청백 r32 | `katana_fullmoon` |
| `trait_res_katana_breach` | 공명 칼바람 길 | 대쉬 길을 따라 남는 바람 칼날 줄 (회전, 반복 타일 가능 `tile: true` 64 도트) | 64×64 타일 | 6f 40/40/50/60/80/100 | 1회 | 길 시작점 | 없음 | `katana_issen_line_t2_solo`·윤곽 선 |
| `trait_res_katana_chain` | 공명 끊이지 않는 칼 | 쓰러진 자리에서 퍼지는 바람 칼날 고리 | 160×160 | 5f | 1회 | hitbox_center | 없음 | `katana_spin` |

### 대검 (greatsword)

| 이름 | 개성 | 모양 | 크기(도트) | 프레임·ms | 루프 | 앵커 | 광원 | 지금 대체 |
|---|---|---|---|---|---|---|---|---|
| `trait_greatsword_g_launch_launch` · `_impact` | 날려 보내기 | launch: 넷째 타에 날아가는 적 뒤로 남는 충격 꼬리 · impact: 벽·기둥·적에 처박히는 큰 충돌(돌가루·금, 회전) | 128×96 · 160×160 | 5f · 7f 40/40/50/60/70/90/120 | 1회 | hitbox_center · contact | impact 백열 r64 140ms | `hit_greatsword_heavy` · `hit_burst` |
| `trait_greatsword_g_swatBack` | 쳐내기 | 화살·술병을 쳐 내는 둔탁한 금속 섬광 (회전 = 되돌아가는 쪽) | 96×96 | 4f 30/40/50/70 | 1회 | projectile 자리 | 백열 r32 60ms | `katana_whirl_reflect`·`hit_spark` |
| `trait_greatsword_g_quakeGuard` · `_launch` · `_land` | 되받는 땅울림 | 본체: 막은 자리에서 앞으로 달리는 땅울림 금 (회전) · launch/land: 띄움·착지 | 256×96 · 96×128 · 128×64 | 6f · 5f · 6f | 1회 | player_pivot(왼끝) · mob_feet · floor | 없음 | `greatsword_charge_crack_line_t2` · `dash_dust` · `crush` |
| `trait_greatsword_g_guardPull` | 끌어당기기 | 가드를 떼며 둘레를 안쪽으로 빨아들이는 고리 | 192×192 | 5f | 1회 | floor | 없음 | `greatsword_brace_absorb` |
| `trait_greatsword_g_shoulderFlip_launch` · `_land` · `_impact` | 어깨 너머 | 어깨로 들어 넘기는 호 · 등 뒤 바닥 메침 먼지 · 벽에 박힘 | 128×128 · 128×64 · 160×160 | 5f · 6f · 7f | 1회 | mob_feet · floor · contact | land 백열 r48 | `dash_dust` · `crush` · `hit_burst` |
| `trait_greatsword_g_ramWall_impact` | 들이받기 | 밀고 간 적이 벽·적에 처박히는 큰 충돌 (회전) | 160×160 | 7f | 1회 | contact | 백열 r64 140ms | `hit_burst`·`crush` |
| `trait_greatsword_g_boilingSteel_soak` · `_fire` | 끓는 쇠 | soak: 술이 칼날로 빨려 드는 소용돌이 · fire: 균열 따라 솟는 불기둥 한 칸 | 128×128 · 64×96 | 5f · 6f 60 루프(수명) | 1회 · 수명 | player_pivot · floor | fire 주황 r48 | `greatsword_charge_ring` · `fire_pool` |
| `trait_greatsword_g_crackPull` | 빨아들이는 균열 | 적 발밑에서 균열 쪽으로 끌리는 흙 자국 (회전) | 96×48 | 4f | 1회 | mob_feet | 없음 | 윤곽 선 |
| `trait_greatsword_splitRoad` | 갈라진 길 | 균열에서 튀어 오른 돌이 탄을 되받아치는 섬광 | 64×64 | 4f | 1회 | projectile 자리 | 없음 | `katana_whirl_reflect`·`hit_spark` |
| `trait_greatsword_g_leapToss_launch` · `_land` | 띄워 올리기 | 착지 충격에 둘레 적이 떠오르는 흙기둥 · 착지 먼지 | 96×128 · 128×64 | 5f · 6f | 1회 | mob_feet · floor | 없음 | `dash_dust` · `crush` |
| `trait_greatsword_g_crushedBreath` · `_impact` | 짓눌린 숨 | 진동 한가운데로 끌어모으는 눌린 고리 · 모인 적끼리 부딪는 충돌 | 192×192 · 128×128 | 6f · 6f | 1회 | floor · contact | 없음 | 윤곽 · `hit_burst` |
| `trait_greatsword_jarCrush_burst` | 술독 짓누르기 | 모인 술이 불붙어 터지는 술독 폭발 | 192×192 | 7f | 1회 | floor | 주황 r96 300ms | `fire_bottle_burst` |
| `trait_greatsword_g_rageRoar` · `_impact` | 포효 | 폭주 시작 포효 음파 고리 · 밀려난 적 충돌 | 256×256 · 128×128 | 6f · 6f | 1회 | player_pivot · contact | 붉은 r96 200ms | `guard_wave` · `hit_burst` |
| `trait_greatsword_g_rageFire` | 술기운 폭주 | 발밑 술에 불이 옮겨 붙는 불꽃 튐 | 96×64 | 5f | 1회 | floor | 주황 r48 | 점 윤곽 |
| `trait_res_greatsword_weight` | 공명 무너뜨림 | 처박힌 자리 바닥이 갈라지며 둘레가 튀어 오르는 금 | 192×192 | 6f | 1회 | floor(contact) | 없음 | `greatsword_quake_fork`·`crush` |
| `trait_res_greatsword_insight` | 공명 막고 되치는 대검 | 주인공 둘레 360° 튕겨 내기 고리 | 256×256 | 5f | 1회 | player_pivot | 백열 r96 100ms | `guard_perfect_fx`·`guard_wave` |

### 단검 (dagger)

| 이름 | 개성 | 모양 | 크기(도트) | 프레임·ms | 루프 | 앵커 | 광원 | 지금 대체 |
|---|---|---|---|---|---|---|---|---|
| `trait_dagger_d_pullThrow` | 뽑아 던지기 | 쓰러진 적에게서 단검이 뽑혀 나가는 섬광 (투척 단검은 `dagger_thrown`) | 64×64 | 4f | 1회 | hitbox_center | 없음 | `dagger_brand_burst` |
| `trait_dagger_d_brandChain` · `_impact` | 낙인 사슬 | 두 적 사이에 걸리는 붉은 낙인 사슬 (회전, 길이 늘림 `tile` 가능) · 끌려와 부딪는 충돌 | 192×48 · 128×128 | 5f · 6f | 1회 | 가운데 · contact | 붉은 r32 | `dagger_brand_hop` · `hit_burst` |
| `trait_dagger_d_shadowKnot` · `_bind` | 그림자 매듭 | 매듭이 조여지는 섬광 · 적 발밑 그림자 매듭 고리(수명) | 96×96 · 128×64 | 5f · 4f 80 루프 | 1회 · 수명 | hitbox_center · floor | 없음 | `dagger_brand_mark` · 윤곽 고리 |
| `trait_dagger_d_stepBack_out` · `_in` | 되짚어 걷기 | 그림자 걸음 끝 자리에서 사라짐 · 처음 자리에 되돌아와 나타남 (지나는 길 베기 선은 윤곽) | 96×144 | 6f | 1회 | player_pivot | 없음 | `shadowstep_ghost` |
| `trait_dagger_d_dashBrand` | 스치는 낙인 | 스쳐 지나간 적 몸에 그어지는 짧은 낙인 자국 | 64×64 | 4f | 1회 | hitbox_center | 없음 | `hit_dagger` |
| `trait_dagger_d_dashPierce` | 꿰찌르기 | 대쉬 찌르기가 두 적을 꿰는 긴 관통선 (회전) | 192×48 | 5f | 1회 | player_pivot(왼끝) | 없음 | `dagger_combo3_double` |
| `trait_dagger_d_flurryPull` | 휘감는 난타 | 난타 둘레로 감겨 드는 바람 소용돌이 (짧게 반복 재생) | 160×160 | 4f 50 | 1회(250ms마다) | floor | 없음 | 윤곽 선 |
| `trait_dagger_d_sparkFlurry` | 불티 난타 | 난타 끝에 흩날리는 불티 폭발 | 160×160 | 6f | 1회 | player_pivot | 주황 r64 200ms | `dagger_hotwind_burst`·`fire_bottle_burst` |
| `trait_dagger_twinBrand` | 쌍낙인 | 옆 적에 낙인이 옮겨 붙는 표시 | 64×64 | 4f | 1회 | hitbox_center | 없음 | 없음(`dagger_brand_hop` 이 날아감) |
| `trait_dagger_d_cloneShield` | 분신 방패 | 분신이 대신 맞고 깨지는 실루엣 | 96×144 | 6f | 1회 | player_pivot | 없음 | `dagger_frenzy_clone_out` |
| `trait_dagger_d_galeReturn` | 돌아오는 칼 | 되돌아오는 단검에 꿰여 끌려오는 표시(갈고리 섬광) | 64×64 | 4f | 1회 | hitbox_center | 없음 | `dagger_brand_hop` |
| `trait_dagger_liquorThrow` | 독주 투척 | 술병이 깨지며 술이 튀는 자국 | 128×96 | 5f | 1회 | floor | 없음 | `fire_bottle_burst`(×0.6) |
| `trait_dagger_d_ghostBind_bind` | 그림자 사냥 | 적 발이 제 그림자에 붙잡히는 검은 손 고리(수명) | 128×64 | 4f 80 루프 | 수명 | floor | 없음 | 윤곽 고리 |
| `trait_dagger_d_ghostFire` | 취한 그림자 | 그림자가 지난 웅덩이에 불이 옮겨 붙는 불꽃 | 96×64 | 5f | 1회 | floor | 주황 r48 | 점 윤곽 |
| `trait_res_dagger_vital` | 공명 얽힌 급소 | 낙인 폭발에서 옆 적으로 뻗는 사슬 끝 | 96×96 | 5f | 1회 | hitbox_center | 붉은 r32 | `dagger_brand_hop` |
| `trait_res_dagger_breach_mark` | 공명 그림자 길 | 그림자 길을 밟은 적에 붙는 낙인 그림자 (길 자체는 윤곽 띠 2.5초) | 64×64 | 4f | 1회 | hitbox_center | 없음 | `dagger_brand_mark` |

### 활 (bow)

| 이름 | 개성 | 모양 | 크기(도트) | 프레임·ms | 루프 | 앵커 | 광원 | 지금 대체 |
|---|---|---|---|---|---|---|---|---|
| `trait_bow_b_pointBlank` · `_impact` | 코앞 사격 | 코앞 화살이 적을 날리는 충격 원뿔 (회전) · 벽·적에 처박힘 | 96×96 · 128×128 | 4f · 6f | 1회 | hitbox_center · contact | impact 백열 r48 | `hit_bow_heavy` · `hit_burst` |
| `trait_bow_b_ricochet` | 튕기는 화살 | 쓰러진 적에서 화살이 꺾여 튀는 섬광 | 64×64 | 4f | 1회 | hitbox_center | 없음 | `hit_bow` |
| `trait_bow_b_perfectPin` · `_bind` · `_impact` | 꿰어 박기 | 본체: 벽·바닥에 꽂혀 떨리는 굵은 화살(수명, 회전) · bind: 꽂힌 적 발밑 고리 · impact: 화살째 벽에 박힘 | 96×48 · 128×64 · 128×128 | 6f 루프(수명) · 4f 루프 · 6f | 수명 · 수명 · 1회 | contact · floor · contact | impact 백열 r48 | `bow_arrow_stuck` · 윤곽 · `hit_burst` |
| `trait_bow_b_fullBounce` | 되튀는 화살 | 끝에 닿아 되튀는 섬광 | 64×64 | 4f | 1회 | projectile 자리 | 없음 | `hit_bow` |
| `trait_bow_b_dropShot` | 낙하 사격 | 하늘에서 꽂히는 화살 한 발 + 바닥 표식 | 96×192 | 6f(f3 판정) | 1회 | floor | 없음 | `bow_meteor_arrow` |
| `trait_bow_b_arrowTrap` · `_snap` | 화살 덫 | 본체: 바닥에 세워진 화살 셋 덫(수명) · snap: 밟으면 화살이 접혀 묶는 닫힘 | 64×64 · 96×96 | 4f 루프(수명) · 5f | 수명 · 1회 | floor | 없음 | `bow_arrow_stuck` · `hit_bow_heavy` |
| `trait_bow_b_rainSnare` · `_bind` | 화살 그물 | 화살비 한가운데 그물이 오므라드는 고리 · 묶인 적 발밑 그물 고리(수명) | 192×192 · 128×64 | 6f · 4f 루프 | 1회 · 수명 | floor | 없음 | 윤곽 |
| `trait_bow_b_rainEcho` | 이어지는 비 | 쓰러진 자리에 떨어지는 화살 한 다발 | 96×192 | 6f | 1회 | floor | 없음 | `bow_meteor_arrow` |
| `trait_bow_b_scatterVolley` | 흩날리는 살 | 쓰러진 자리에서 사방으로 흩어지는 화살 꽃 (화살 자체는 `bow_arrow_rapid`) | 128×128 | 5f | 1회 | hitbox_center | 없음 | `bow_arrow_split` |
| `trait_bow_b_rapidStride` | 걸으며 연사 | (이동 개성 — 지금 그림 없음) 연사 중 발밑 짧은 먼지 | 64×32 | 4f | 1회 | player_pivot | 없음 | 없음 — **선택 요청** |
| `trait_bow_b_skewer` · `_impact` | 꿰미 | 꿰인 적들이 화살 끝으로 끌려가는 꼬챙이 섬광 (회전) · 서로 부딪힘 | 128×64 · 128×128 | 5f · 6f | 1회 | hitbox_center · contact | 없음 | `bow_arrow_pierce_hit` · `hit_burst` |
| `trait_bow_fireArrow` | 불화살 한 발 | 화살이 지나간 웅덩이에 불이 확 번지는 순간 | 96×64 | 5f | 1회 | floor | 주황 r48 | 없음(웅덩이 불 그림) |
| `trait_bow_b_starWell` | 별 표적 | 하늘 화살 자리로 빨려 드는 별빛 소용돌이 | 192×192 | 6f | 1회 | floor | 금빛 r64 200ms | `bow_link_stack` |
| `trait_bow_b_starDrunk` | 술별 | 하늘 화살이 술에 떨어져 불붙는 순간 | 96×64 | 5f | 1회 | floor | 주황 r48 | 점 윤곽 |
| `trait_res_bow_weight` | 공명 말뚝 박기 | 밀리거나 끌려온 적에 위에서 꽂히는 말뚝 화살 | 64×96 | 5f | 1회 | hitbox_center | 없음 | `bow_arrow_stuck` |
| `trait_res_bow_breach` | 공명 덫 비 | 덫에 묶인 적 위로 떨어지는 하늘 화살 | 96×192 | 6f(f3 판정) | 1회 | floor | 없음 | `bow_meteor_arrow` |

### 공통 (모든 무기)

| 이름 | 쓰는 곳 | 모양 | 크기(도트) | 프레임·ms | 루프 | 앵커 | 광원 | 지금 대체 |
|---|---|---|---|---|---|---|---|---|
| `trait_<공명 id>` (켜짐 순간) | 공명이 켜진 뒤 전투로 돌아오면 주인공 둘레 1회 | 같은 태그 두 카드가 엮이는 두 고리가 겹치는 표시 (태그 색) | 192×192 | 7f | 1회 | player_pivot | 금빛 r64 300ms | `set_flash` · 윤곽 고리 |
| 묶음 사슬 선 | 끌어당김·사슬·덫 묶음 | 지금은 점선 윤곽(시스템). 반복 타일 `tile: true` 64 도트 사슬 한 마디를 주면 그것으로 깐다 — **선택 요청** | 64×16 | 1~2f | 고정 | 선 시작 | 없음 | 점선 윤곽 |

## 2. 카드 그림 (`sprites/ui_traits/<무기>_<개성 id>.png` — 키 `ui_traits/<무기>_<개성 id>`)

크기는 UI 와 맞춰 확정(계약 art §27). Gemini 콘셉트 → 도트 보정. 카드 한 장 = 그 개성의 '한 순간'을 그린다(키캡·숫자 없음).

| 파일 | 이름 | 한 줄 콘셉트 |
|---|---|---|
| `katana_k_shadowThrust` | 그림자 찌르기 | 쓰러지는 적 뒤로 그림자 칼끝이 다음 적의 가슴을 꿰뚫는다 |
| `katana_k_edgeLift` | 칼등 띄우기 | 휘청이는 병사를 칼등으로 쳐올려 공중에 띄운 순간 |
| `katana_k_parryShove` | 흘려 밀기 | 칼을 비스듬히 대어 흘린 적이 돌기둥에 처박힌다 |
| `katana_k_bladeBind` | 칼 감기 | 칼날이 상대 창대를 감아 앞으로 끌어당긴다 |
| `katana_k_shadowVault` | 그림자 넘기 | 내리찍는 칼끝을 스치며 적의 등 뒤로 넘어가는 실루엣 |
| `katana_k_issenBack` | 물러서며 베기 | 일섬 끝에 뒤로 미끄러지며 그리는 둥근 칼 궤적 |
| `katana_k_iaiWave` | 발도풍 | 칼집에서 뽑힌 칼끝에서 초승달 바람이 날아간다 |
| `katana_k_iaiChain` | 연쇄 발도 | 쓰러지는 적을 지나 다음 적 앞으로 미끄러지는 낮은 자세 |
| `katana_bloodGale` | 피바람 | 회전 베기의 핏빛 고리가 한 바퀴 더 감긴다 |
| `katana_liquorWhirl` | 술 회오리 | 바닥의 술이 칼을 따라 감겨 불 회오리가 된다 |
| `katana_k_sparkCleave` | 불똥 내려베기 | 내려친 칼이 돌바닥을 긁으며 술 웅덩이에 불똥을 튀긴다 |
| `katana_k_groundPin` | 땅에 박기 | 투구가 갈라진 적이 무릎까지 바닥에 박혀 있다 |
| `katana_k_moonRelay` | 달빛 잇기 | 달 분신이 쓰러진 적에서 다음 적으로 건너가는 청백 선 |
| `katana_k_moonPools` | 취월 | 술 웅덩이마다 비친 달에서 분신이 솟아 칼을 든다 |
| `greatsword_g_launch` | 날려 보내기 | 넷째 타에 날아간 병사가 벽에 부딪혀 돌가루가 튄다 |
| `greatsword_g_swatBack` | 쳐내기 | 대검 면이 날아오는 술병을 쳐서 던진 행상에게 돌려보낸다 |
| `greatsword_g_quakeGuard` | 되받는 땅울림 | 막아 낸 충격이 땅을 타고 번져 앞줄 적이 떠오른다 |
| `greatsword_g_guardPull` | 끌어당기기 | 대검을 내리며 둘레 적을 앞으로 끌어당기는 손짓 |
| `greatsword_g_shoulderFlip` | 어깨 너머 | 태클로 들어 올린 적을 등 뒤 바닥에 메친다 |
| `greatsword_g_ramWall` | 들이받기 | 어깨로 밀고 나간 적이 기둥에 처박힌다 |
| `greatsword_g_boilingSteel` | 끓는 쇠 | 모으는 대검에 술이 빨려 들어 칼날이 끓는다 |
| `greatsword_g_crackPull` | 빨아들이는 균열 | 균열 양옆의 적이 금 쪽으로 미끄러져 들어간다 |
| `greatsword_splitRoad` | 갈라진 길 | 갈라진 바닥 위를 달리며 날아온 화살을 튕겨 낸다 |
| `greatsword_g_leapToss` | 띄워 올리기 | 도약 찍기 착지에 둘레 적이 공중으로 떠오른다 |
| `greatsword_g_crushedBreath` | 짓눌린 숨 | 진동 한가운데로 끌려온 적들이 서로 머리를 박는다 |
| `greatsword_jarCrush` | 술독 짓누르기 | 진동이 모은 술 웅덩이에 불이 붙어 크게 터진다 |
| `greatsword_g_rageRoar` | 포효 | 폭주하는 전사의 포효에 적들이 벽까지 밀려난다 |
| `greatsword_g_rageFire` | 술기운 폭주 | 불붙은 술 위를 밟으며 붉게 달아오른 대검 |
| `dagger_d_pullThrow` | 뽑아 던지기 | 쓰러진 적에게서 뽑은 단검이 다음 적에게 날아간다 |
| `dagger_d_brandChain` | 낙인 사슬 | 붉은 낙인 사슬에 묶인 두 적이 서로 부딪친다 |
| `dagger_d_shadowKnot` | 그림자 매듭 | 적의 그림자가 매듭처럼 발목을 묶는다 |
| `dagger_d_stepBack` | 되짚어 걷기 | 그림자 걸음 뒤 처음 자리로 되돌아오며 그은 검은 선 |
| `dagger_d_dashBrand` | 스치는 낙인 | 스쳐 지나간 적의 옆구리에 붉은 낙인이 남는다 |
| `dagger_d_dashPierce` | 꿰찌르기 | 한 번의 찌르기가 두 적을 한 줄로 꿰뚫는다 |
| `dagger_d_flurryPull` | 휘감는 난타 | 난타의 바람에 둘레 적이 빨려 든다 |
| `dagger_d_sparkFlurry` | 불티 난타 | 난타 끝 불티가 술 웅덩이에 떨어져 불이 붙는다 |
| `dagger_twinBrand` | 쌍낙인 | 분신이 교차 베기로 옆 적에게 낙인을 옮긴다 |
| `dagger_d_cloneShield` | 분신 방패 | 날아든 칼을 분신이 대신 맞고 흩어진다 |
| `dagger_d_galeReturn` | 돌아오는 칼 | 되돌아오는 단검이 꿰인 적을 끌고 손으로 온다 |
| `dagger_liquorThrow` | 독주 투척 | 부채꼴 단검 사이에 술병 하나가 깨진다 |
| `dagger_d_ghostBind` | 그림자 사냥 | 그림자 손이 적의 발목을 붙잡는다 |
| `dagger_d_ghostFire` | 취한 그림자 | 그림자가 지나간 웅덩이에 불이 옮겨 붙는다 |
| `bow_b_pointBlank` | 코앞 사격 | 코앞 화살에 날아간 병사가 벽에 부딪힌다 |
| `bow_b_ricochet` | 튕기는 화살 | 쓰러진 적에서 꺾인 화살이 옆 적에게 튄다 |
| `bow_b_perfectPin` | 꿰어 박기 | 화살째 밀려간 적이 기둥에 꽂혀 있다 |
| `bow_b_fullBounce` | 되튀는 화살 | 가득 당긴 화살이 벽에 닿아 되튀어 돌아온다 |
| `bow_b_dropShot` | 낙하 사격 | 구르며 쏜 화살이 하늘로 솟았다 세 발로 떨어진다 |
| `bow_b_arrowTrap` | 화살 덫 | 떠난 자리에 세워 둔 화살 덫을 적이 밟는다 |
| `bow_b_rainSnare` | 화살 그물 | 화살비가 그물처럼 오므라들어 적을 한데 묶는다 |
| `bow_b_rainEcho` | 이어지는 비 | 쓰러진 자리에 화살 한 다발이 더 떨어진다 |
| `bow_b_scatterVolley` | 흩날리는 살 | 연사에 쓰러진 적 자리에서 화살이 꽃처럼 흩어진다 |
| `bow_b_rapidStride` | 걸으며 연사 | 걸음을 멈추지 않고 쏟아붓는 연사 |
| `bow_b_skewer` | 꿰미 | 한 화살에 꿰인 적들이 꼬챙이처럼 끌려간다 |
| `bow_fireArrow` | 불화살 한 발 | 완벽하게 놓은 화살이 술 웅덩이 줄을 불태운다 |
| `bow_b_starWell` | 별 표적 | 하늘 화살 자리로 둘레 적이 빨려 든다 |
| `bow_b_starDrunk` | 술별 | 하늘 화살이 술 웅덩이에 떨어져 불꽃이 핀다 |

공명 카드 그림은 계약에 칸이 없다(`UiResonance` 에 iconKey 없음) — 필요하면 UI·프로듀서 결정 뒤 `ui_traits/<공명 id>.png` 로 추가 요청.

## 3. 음향 (참고 — sound §11)

발동음 후보: `sfx/trait_<무기>_<개성 id>` → 행동 갈래 `sfx/trait_<act>`(launch·slam·pull·bind·clone·blink·wave·throw·rain·ignite·deflect·shield·spin·mark·burst·move) → 없으면 무음. 공명 발동 `sfx/<공명 id>` → `sfx/resonance_proc`, 공명 켜짐 `sfx/resonance_on` → `trait_manifest` → `dual_trait`. 트리거 `TRAIT_PROC{weapon,trait,act,resonance?}` · `RESONANCE_ON{weapon,id,tag,name}` (같은 개성 120ms 안 한 번).
