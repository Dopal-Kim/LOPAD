# 무기 데이터 변경 이력 (`data/weapons.json` 에서 옮김)

- 61라운드 P9: 데이터 파일 안의 변경 이력 주석(`_note`·`_note56`·`_note58`·`_noteQ8`·`_artNote`·`_note60`)과 자리표시 이름 표시(`_tmpName`)를 이 문서로 옮겼다. 데이터에는 현재 값만 남는다.
- 아래는 옮기기 직전(61라운드 시작, 커밋 `50a2677`) 문장을 그대로 둔 것이다. 지금 값과 다를 수 있다 — 61라운드 이후 바뀐 점은 맨 아래 '61라운드 4동사 개편' 절과 `parts/system/README.md` 61라운드 절을 본다.
- 경로 표기: `weapons.<무기>.<필드>`, 배열 원소는 `[id]`(id 가 없으면 번호).


## katana

- `weapons.katana.resource` · `_note`: 49라운드 임시값: 기력 — 공격·대쉬·대쉬 공격이 소모(칼 보통), 시간 회복. 바닥나면 이동 감속·강한 타(3타·대쉬 공격) 불가. 비전투 달리기는 소모 없음 56라운드 Q7·Q19: 기력 0 → 그로기 groggyMs(1.5초, 공격·대쉬 불가·패링만, 시간이 지나야만 풀림 — 풀리면 max × recoverRatio)
- `weapons.katana.carry` · `_note`: 49라운드 임시값: 허리 칼집. 1타가 발도(뽑기 = 첫 타). 51라운드 Q4: F = 넣기/뽑기, 자동 납도 끔(sheatheAfterMs 0), 넣은 동안 기력 회복 ×sheathedRegenMult, 넣은 채 첫 타 = 발도(확정 치명)
- `weapons.katana.combo` · `_note`: 48라운드 임시값: '씽 씽씽'. 판정 = 몸 중심(발 위 10px). 51라운드 Q3 템포(임시): 3연격(1타 시작 → 3타 끝) 약 1.1초 — hitAtMs = 판정 프레임 시작(예비 동작 구간). 55라운드 §17 K-A 발도 초승달(Q19): 1타 대각 올려베기(+70°→−40°) → 2타 대각 내려베기(−70°→+40°, X자) → 3타 수평 발도 150°(−75°→+75° — 왼 허리 칼집에서 뽑는 방향, 55라운드 Q26 · 그림과 같은 방향, R×1.25, 내반경 = 초승달) + 150ms 뒤 같은 호 잔상 베기 50%. 각도 = 조준 0°·화면 시계 방향 +(leftTransform rotate = 왼쪽 조준은 180° 회전, 아트 dirTransform 과 같게 — 확인 전 임시), R = radiusPx × 갈래·강화·크기 배율. step = 방향키를 누를 때만 내딛기(Q21, 구간 = 몸 시트 stepPx.frames). 타 시간은 51라운드 Q3 템포(3연격 약 1.1초) 유지 — 아트 8ddce9c 새 시트(제안 260·210·410ms)를 두 구간 맞춤으로 늘여 재생(이펙트 판정 프레임 = 몸 판정 프레임). 내반경 0.45 = 아트 그림 값(임시)
- `weapons.katana.combo` · `_artNote`: 55라운드 §17 그림 이름 표: 키 → 후보(앞이 우선, 로드된 첫 시트). 아트 새 시트 명세가 오면 각 배열 앞에 새 이름만 넣는다. 지금은 기존 combo1~3 으로 대체(로직 먼저)
- `weapons.katana.combo` · `_note58`: 58라운드 Q1: 3타 = 찌르기(일섬 대체 — 일섬은 대쉬 공격 전용 moves.issenDash). 아트 player_katana_thrust 시간 그대로 710/250, 다음 타 560(cancelAt). 3연격 470 + 440 + 710 = 1620ms(56 Q49 1.65초 안). 찌르기 판정·피해는 검기 단수별 moves.thrust.byKi(검기 전부 소모)
- `weapons.katana.combo` · `_note56`: 56라운드 Q1 템포 약 1.5초·사거리 ×1.15(반경 33→38)·타당 피해 상향(임시 1.8/1.3/2.0) — 아트 combo56 새 시트 시간 그대로(rise 470/150 · fall 440/120 · issen 740/250). Q2 3타 = 일섬(move issen — 무기 데이터 issen), 55라운드 3타 발도 초승달·잔상 베기는 그림 표에 남겨 둠(Q35 재사용 후보)
- `weapons.katana.secondary` · `_note`: 56라운드 Q48: 우클릭 = 가드(누르는 동안 피해 감소·느려짐), 누른 직후 0.15초(player.perfectGuard) 안에 맞으면 패링(피해 0·튕겨냄·PARRY·검기 1단·간파 반격 자리). 그로기 중에도 이 가드로 버틴다. 11라운드 패링 창 0.2초 대체. 감소·이동 배율은 임시값, 떼도 밀쳐내지 않음
- `weapons.katana.personality` · `_note`: 57라운드 Q22~Q37 갈래 재설계 (설계안 design-2026-10-04-build-axis 2.2~2.5): 1단 = 새 동작(move) + 연격 한 타 변화(comboChange), 2단 α = 동작 심화 / β = 고유 자원 규칙 전환(rule). tags = 갈래 노드 태그(노드 태그마다 1점). 새 이름은 자리표시(_tmpName). 옛 갈래 배율(damageMult·hitboxMult)은 새 표에 없어 1.0 — 갈래 그림 배율 = 판정 배율(55 Q15). 2단은 1층 런에서 개성 수급으로 닿지 않음(시험장 검수)
- `weapons.katana.personality.branches[iai]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.katana.personality.branches[iai].art` · `_note`: 57 갈래 아트 (branch57): 몸·무기 katana_spin(+ki1~3) 15프레임, 홀드 루프 f2~5, 뗌 f6, 뗀 뒤 40ms 판정 · fx katana_spin(뗀 순간, 2회전은 다시) · katana_spin_ready(0.4초 준비 반짝임)
- `weapons.katana.personality.branches[iai].art` · `_note60`: 60라운드 계약 art §21: 1단 연격 변화 — 2타 fx katana_fall 을 katana_fall_wide 로 1:1 교체(replaceFx)
- `weapons.katana.personality.branches[iai].next[vortex]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.katana.personality.branches[iai].next[vortex].art` · `_note60`: 60라운드 계약 art §21: 지속 회전 루프 · 탄 되받아침
- `weapons.katana.personality.branches[iai].next[zangetsu]` · `_note`: 27라운드 이름 재사용, 효과 재정의. 일섬(대쉬 공격 — 58 Q1) 궤적은 칼 전투 파일(병행 작업)과 합친 뒤 연결
- `weapons.katana.personality.branches[iai].next[zangetsu].art` · `_note60`: 60라운드 계약 art §21: 달 궤적 (48 도트 간격, 접선 회전)
- `weapons.katana.personality.branches[batto]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.katana.personality.branches[batto].art` · `_note`: 57 갈래 아트: 몸·무기 katana_guardbreak(+ki1~3) 15프레임, 준비 루프 f5~8(600ms), 뗌 f9 · fx katana_guardbreak(뗀 순간). 아트 판정 rect 192×64 도트는 참고 — 데이터 3×1칸이 기준
- `weapons.katana.personality.branches[batto].next[cleave].art` · `_note60`: 60라운드 계약 art §21: 균열(뗀 자리·4행, 판정 + 40ms) · 처형. 균열 4칸 = 60 Q3 아트 제안 채택(rule crackTiles)
- `weapons.katana.personality.branches[batto].next[meikyo]` · `_note`: 검기 규칙 전환 — 칼 검기·찌르기 강화(58 Q1)를 병행 작업 중이라 그쪽과 합친 뒤 연결 (지금은 패링 창만)
- `weapons.katana.personality.branches[batto].next[meikyo].art` · `_note60`: 60라운드 계약 art §21: 검기 단수 발밑 고리(rowsAre stacks 1~5) · 패링. 명경은 검기 통합 뒤 켬(live false)
- `weapons.katana.issen` · `_note`: 56라운드 Q2·Q3·Q28·Q29 (몸 시트 player_katana_issen 메모 기준, 월드 px): 220~370ms 조준 4방향으로 64px(4칸) 돌진·적 관통·벽에 막히면 멈춤·돌진 중 무적, 판정 250~330ms = 출발 원점 뒤 6px ~ 이동 거리 + 16px, 폭 18px. 선 시트는 220ms 에 출발 발 위치(바닥 깊이), 실제 이동 칸 수로 t1~t4. 분신은 검기 3단 소모 시에만 — 420ms 출발, 570ms(도착) 선 위 적 전부 50% 1회. 분신이 없으면 _solo 선(끝 폭발은 연출만)
- `weapons.katana.gauge` · `_note`: 56라운드 Q14 검기(劍氣) 3단 (임시값): 근접 적중마다 gainPerHit, 패링 성공 시 1단 즉시, 일섬이 전부 소모(단마다 피해 +25%), 3단이면 그림자 분신(Q28). 칼날 빛 재→호박→백열은 아트 오버레이 전까지 무기 곱 틴트
- `weapons.katana.moves` · `_note`: 56라운드 2단계 Q40·Q53·Q55·Q60 (임시값 — 시각·판정·이동은 아트 JSON player_katana_counter·_iai 값, 피해·기력·창은 시스템 임시값). 판정 R = combo.radiusPx 38
- `weapons.katana.moves.thrust` · `_note`: 58라운드 Q1 3타 찌르기 (임시값): 검기를 전부 소모해 단수(0~3)별 판정·피해·fx — 판정은 아트 player_katana_thrust hitShape.byKiLevel(도트 ÷ R 152: 시작 16 · 끝 197.6/228/258.4/288.8 · 폭 40/44/48/56) 그대로, 피해 배율은 시스템 임시값(단마다 +25% — 일섬 issenDamagePerStage 와 같게). 내딛기 = 아트 lungePx(조준 방향 10px, 220~330ms easeOut, 방향키와 무관 — 아트 제안)
- `weapons.katana.moves.issenDash` · `_note`: 58라운드 Q1 일섬 = 대쉬 공격 전용: 대쉬 후 attackWindowMs(0.3초) 안 좌클릭 → 4칸 일섬 돌진(무적·관통, 기하·선·분신은 무기 데이터 issen — 56 Q28·Q29 그대로). 몸 player_katana_issen_dash(없으면 issen) 시간 740/250. 58 Q10(60라운드 적용): 대쉬 공격 기본 배율(player.dash.attackDamageMult ×1.5)은 빼고(useDashAttackMult false) 일섬 자체 피해 2.0(임시) × 갈래 배율(대쉬 공격 갈래·패시브)·검기만. 피해·기력 임시값

## greatsword

- `weapons.greatsword.resource` · `_note`: 49라운드 임시값: 기력 — 대검은 크게 소모, 회복 느림. 바닥나면 이동 감속·강한 타(3타·대쉬 공격·내리찍기) 불가 56라운드 Q7·Q19: 기력 0 → 그로기 groggyMs(1.5초, 공격·대쉬 불가·가드만)
- `weapons.greatsword.resource.cost` · `_note`: 55라운드 순환 연격 H1·V·H2·V (V = 옛 3타 값), 차지 내려찍기 = slam (임시값)
- `weapons.greatsword.carry` · `_note`: 49라운드 임시값: 등에 멤. 1타 f0~f1 이 곧 등에서 끌어올리기(아트 메모) → 별도 뽑기 없이 1타(drawMs 0). 51라운드 Q4: F = 넣기/뽑기, 자동으로 넣지 않음, 넣은 동안 기력 회복 ×sheathedRegenMult, 넣은 채 첫 타 = 끌어내기(넉백 ×knockbackMult)
- `weapons.greatsword.weight` · `_note`: 49라운드 임시값: 타마다 반 걸음(8px) 전진, 휘두른 뒤 감속 유지, 3타 타격 후 0.3초 정지
- `weapons.greatsword.slam` · `_note`: 49라운드 임시값: 충격파 계열(파쇄·지진·분쇄) 발현 후 3타 = 마우스 방향 짧은 도약 → 내려찍기 → 충격파. 시트 player_greatsword_slam 메모(leapFrames·impactFrame·impactOffsetPx)가 있으면 시간·착지점은 시트. 반경 40 = fx/greatsword_slam 그림 반경
- `weapons.greatsword.dashSlash` · `_note`: 49라운드 임시값: 대쉬 공격 = 달려들며(24px) 크게 한 번 휘두르고 잠깐 멈춤. 시트 player_greatsword_dashslash(hitFrames·recoverFrames·hitRadiusPx·arcDeg·fxReuse)가 있으면 시트 값. 이펙트는 2타 이펙트 재사용
- `weapons.greatsword.combo` · `_note`: 48라운드 '훙 훙 훙' → 55라운드 §17 G-C 관성 순환(Q18): H1 수평 시계 150°(−75°→+75°) → V 정면 내려찍기(쐐기 40° R×1.3 + 끝점 충격원 0.35R) → H2 수평 반시계 150°(+75°→−75°) → V → H1 … 입력이 이어지는 한 끊김 없이 교대(loop). 관성(Q23): 이어지는 타마다 공속 +5%, 최대 +20%, 1초 무입력·피격 시 초기화, 최대일 때 충격원 ×maxImpactMult. 홀드 차지(Q22): 0.4/0.8/1.2초 3단, 쐐기 ×1.3/1.5/1.8, 3단 충격파 링, 차지 중 이동 ×0.35. 타 시간은 51라운드 Q3 템포(대검 약 2초) 유지 — 아트 8ddce9c 새 시트(제안 H 490·V 530ms)를 두 구간 맞춤으로 늘여 재생. 차지 내려찍기 480/120ms·내반경 0.35·충격원 배율 1.0/1.15/1.3·관성 최대 1.3 = 아트 값. 차지 피해·holdMs·링 크기·지연은 임시값(55라운드 Q31 데모 확인). 막타(heavy — 큰 스파크·히트스톱 ×1.8·흔들림·충격파 갈래)는 차지 내려찍기만(+3단 링), 연격 V 는 일반 타격(55라운드 Q30) — 기력 바닥이어도 V 는 막히지 않는다
- `weapons.greatsword.combo` · `_artNote`: 55라운드 §17 그림 이름 표 (칼과 같은 규칙). V·차지는 기존 내리찍기 몸(slam)으로 대체, 휘두름 이펙트 없이 끝점 바닥 충격(fx/greatsword_slam)
- `weapons.greatsword.combo.charge` · `_noteQ8`: 58라운드 Q8(60라운드 적용): 내려찍기 쐐기 길이 = R × 단계 lengthMult 1.0/1.1/1.2 (옛 1.3/1.5/1.8) — 쐐기는 가까운 적만, 먼 적은 균열(crackLine 3/4/5칸)이 맞힌다. 데모로 조정
- `weapons.greatsword.combo.charge.crackLine` · `_note`: 58라운드 Q3 (임시값): 차지를 떼면 어느 갈래든 마우스 방향으로 휘둘러 내리찍고(몸 greatsword_charge_swing 790/290 — 없으면 charge_slam) 칼끝이 바닥에 닿은 자리(몸 slamAnchors, 없으면 쐐기 끝점)에서 균열이 커서 쪽으로. 칸 수 = min(차지 단계 최대 tilesByStage, 찍은 자리 → 커서 거리 / tilePx 반올림(최소 1), 벽까지(내림)) — 아트 pickRule, 그림 = 그림 표 crack_line fx[칸 수 − 1](t1~t5, 회전). 앞머리가 지나간 칸만 판정(적마다 1회), 앞머리 속도 = fx 메모 frontPxByFrame(없으면 msPerTile). 반폭 7 = 아트 hitShape.halfWidthPx 28 도트. 땅 충격(ground_crack m/m/l)도 찍은 자리에. 그림이 없으면 칸마다 ground_crack s 를 tileCrackScale 로. 56라운드 Q10 꽂아내리기 대체
- `weapons.greatsword.combo` · `_note58`: 58라운드 Q3: 차지 = 휘둘러 내리찍기 + 균열이 커서까지(charge.crackLine) — 꽂아내리기 폐기(어느 갈래든, Q11 코드·데이터 삭제). Q8: 단계 쐐기 길이 ×1.0~1.2 (charge._noteQ8)
- `weapons.greatsword.combo` · `_note56`: 56라운드 Q5·Q25 무게: 아트 combo56_body 새 시트 시간 그대로(H 820/380 · V 920/440 · 차지 내려찍기 700/180, 3타 약 2.6초 — 55라운드 Q29 '약 2초' 대체), 몸 시트 holdFrames(선딜 버팀)·dragFrames(끌림 — dragStepPx 를 방향키와 무관하게 미끄러짐). Q6 8방향(조준각 8분할 행). Q10 기본 차지 = 충격파 링 없는 강한 내려찍기(꽂아내리기는 58 Q11 삭제). 균열 crackRow: V s(관성 최대 m) · 차지 1·2단 m · 3단 l
- `weapons.greatsword.personality` · `_note`: 57라운드 Q22~Q37 갈래 재설계 (설계안 design-2026-10-04-build-axis 2.2~2.5): 1단 = 새 동작(move) + 연격 한 타 변화(comboChange), 2단 α = 동작 심화 / β = 고유 자원 규칙 전환(rule). tags = 갈래 노드 태그(노드 태그마다 1점). 새 이름은 자리표시(_tmpName). 옛 갈래 배율(damageMult·hitboxMult)은 새 표에 없어 1.0 — 갈래 그림 배율 = 판정 배율(55 Q15). 2단은 1층 런에서 개성 수급으로 닿지 않음(시험장 검수)
- `weapons.greatsword.personality.branches[crush]` · `_note`: 58 Q3 차지 = 휘둘러 내리찍기 + 균열(모든 갈래 공통)로 바뀜 → 파쇄는 그 균열을 강화하는 쪽으로 (설계안 꽂아내리기 직선 균열 4/6/8칸 대신 58 Q3 3/4/5칸 그대로, 그림 교체 + 탄 지움)
- `weapons.greatsword.personality.branches[crush].art` · `_note`: 57 갈래 아트: 기본 균열 greatsword_charge_crack_line_tN 을 greatsword_shatter_crack_tN 으로 1:1 교체 · 탄을 지운 자리 greatsword_shatter_snuff
- `weapons.greatsword.personality.branches[crush].art` · `_note60`: 60라운드 계약 art §21: 4타(V) 균열 2칸 그림 greatsword_cleave_crack (comboChange crack)
- `weapons.greatsword.personality.branches[crush].next[quake]` · `_note`: 공중제비 착지 균열 1줄은 대검 새 기본기(병행 작업)와 합친 뒤
- `weapons.greatsword.personality.branches[crush].next[quake].art` · `_note60`: 60라운드 계약 art §21: 균열 끝 3갈래 greatsword_quake_fork. 갈래 각 2칸 = 60 Q3 아트 제안 채택(rule lengthTiles)
- `weapons.greatsword.personality.branches[crush].next[resonance]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.greatsword.personality.branches[crush].next[resonance].art` · `_note60`: 60라운드 계약 art §21: 퍼펙트 가드 반격 greatsword_echo_counter
- `weapons.greatsword.personality.branches[weight]` · `_note`: 58 Q3 이후: 기본 균열 대신 내리찍은 자리 원형 진동 (아트 greatsword_quake_ring 행 lv1~3)
- `weapons.greatsword.personality.branches[weight].art` · `_note`: 57 갈래 아트: greatsword_quake_ring (행 lv1~3 = 차지 단계, 반경 2.5/3/3.5칸, 중심 slam_point, 기본 균열 대신)
- `weapons.greatsword.personality.branches[weight].next[giant]` · `_note60`: 57 Q43 거인 차지 4단 (60라운드 연결): 차지 단계에 4단을 더함(systems/build/current chargeStages) — 그림 키 stage4Art(charge4: 번쩍임 greatsword_charge_flash_lv4), 진동 = greatsword_giant_ring(lv4, 반경 ringRadiusTiles), 차지 중 끊기지 않음·피해 damageTaken·흡수 greatsword_brace_absorb. 4단 피격 판정 배율 ringMult(임시 1.0)
- `weapons.greatsword.personality.branches[weight].next[giant].art` · `_note60`: 60라운드 계약 art §21: 차지 4단 진동 lv4 · 4단 번쩍임 · 피격 흡수(재사용)
- `weapons.greatsword.personality.branches[weight].next[clot]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.greatsword.personality.branches[weight].next[clot].art` · `_note60`: 60라운드 계약 art §21: 그로기 오라 · 폭발(반지름 144 도트). 폭발 반경 2.25칸 = 60 Q3 아트 제안 채택(rule burstRadiusTiles)
- `weapons.greatsword.gauge` · `_note`: 56라운드 Q15 울분(鬱憤) (임시값): 가드로 줄인 피해 × blockGainMult(퍼펙트 가드 = 원래 피해 × perfectMult, 그로기 중 가드 × groggyMult) 가 쌓이고, 차지 내려찍기가 전부 소모해 피해 +slamDamageBonus·판정 길이 +slamRangeBonus (가득 기준, 비율만큼)
- `weapons.greatsword.moves` · `_note`: 56라운드 2단계 Q41·Q54·Q55·Q61·Q63 (임시값 — 시각·판정·이동은 아트 JSON player_greatsword_tackle·_brace_upswing·_leap_slam·_guard_rush 값, 피해·기력·창은 시스템 임시값). 판정 R = combo.radiusPx 51

## dagger

- `weapons.dagger.resource` · `_note`: 49라운드 임시값: 과열 — 연격이 이어질수록 가열(단계 0→3, 공격속도↑·이펙트 강화). 최대 열을 1.5초 유지하면 과열 → 1.6초 냉각(공격 불가) 56라운드 Q18: 100% 즉시 과열 → 낙인 일괄 폭발, 식는 동안(1.2초) 공격 가능·느려짐(gauge.coolingSpeedMult)
- `weapons.dagger.carry` · `_note`: 49라운드: 손(역수)
- `weapons.dagger.combo` · `_note`: 48라운드 임시값: '슈슈슉' 찌르기 3연타 — 몸 중심에서 앞으로 뻗는 직사각형(길이·폭, 아트 JSON thrust 가 있으면 그 값·비틀림 각도). 51라운드 Q3 템포(임시): 3연격 약 0.5초(가열 단계 배속으로 더 빨라짐)
- `weapons.dagger.personality` · `_note`: 57라운드 Q22~Q37 갈래 재설계 (설계안 design-2026-10-04-build-axis 2.2~2.5): 1단 = 새 동작(move) + 연격 한 타 변화(comboChange), 2단 α = 동작 심화 / β = 고유 자원 규칙 전환(rule). tags = 갈래 노드 태그(노드 태그마다 1점). 새 이름은 자리표시(_tmpName). 옛 갈래 배율(damageMult·hitboxMult)은 새 표에 없어 1.0 — 갈래 그림 배율 = 판정 배율(55 Q15). 2단은 1층 런에서 개성 수급으로 닿지 않음(시험장 검수)
- `weapons.dagger.personality.branches[twin].art` · `_note`: 57 갈래 아트: fx dagger_cross_clone (대상 히트박스 중심, 생성 + 120ms 교차 베기)
- `weapons.dagger.personality.branches[twin].art` · `_note60`: 60라운드 계약 art §21: 1단 연격 변화 — 3타 fx dagger_combo3 → dagger_combo3_double 1:1 교체 · 쌍낙인 옮겨감 dagger_brand_hop
- `weapons.dagger.personality.branches[twin].next[dance].art` · `_note60`: 60라운드 계약 art §21: 분신 나타남·사라짐 (상주 분신 색 교체 shadowPalette 는 아직 반투명 복사)
- `weapons.dagger.personality.branches[twin].next[bleed].art` · `_note60`: 60라운드 계약 art §21: 출혈 루프 dagger_brand_bleed
- `weapons.dagger.personality.branches[gale].art` · `_note`: 57 갈래 아트: 몸·무기 dagger_fan_throw (releaseFrame 2 = 100ms, fanDeg ±15) · fx dagger_fan_throw · 투사체 dagger_thrown
- `weapons.dagger.personality.branches[gale].art` · `_note60`: 60라운드 계약 art §21: 이동 중 90ms 마다 재 실루엣 dagger_gale_wind
- `weapons.dagger.personality.branches[gale].next[flyknife]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.dagger.personality.branches[gale].next[flyknife].art` · `_note60`: 60라운드 계약 art §21: 박힌 단검 dagger_stuck_blade (비도 투척 = dagger_thrown ×5 재사용)
- `weapons.dagger.personality.branches[gale].next[heatwave]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.dagger.personality.branches[gale].next[heatwave]` · `_note`: 과열 폭발 범위 ×2 는 과열 규칙(병행 작업 범위) — 지금은 이동기 가열·가속·화상·무적만
- `weapons.dagger.personality.branches[gale].next[heatwave].art` · `_note60`: 60라운드 계약 art §21: 과열 50%+ 이동 루프 · 과열 폭발 dagger_overheat_burst → dagger_hotwind_burst 1:1 교체
- `weapons.dagger` · `_note56`: 56라운드 Q4: 피해 ×1.4(0.6 → 0.84), 찌르기 수평 사거리 ×1.5(모든 방향 — 판정은 fx v3 dagger_combo* 메모 thrust 144/144/168 도트, 대체 데이터 24 → 36), 무기 그림 1.3배는 아트
- `weapons.dagger.gauge` · `_note`: 56라운드 Q16·Q18 낙인(烙印) (임시값): 같은 적 타격마다 perHit(등 뒤 backGain), 최대 max, 과열 단계마다 획득 +heatGainPerStage. 그림자 걸음으로 그 적 뒤에 서면 전부 폭발(표식 × burstDamagePerMark × 공격력). 과열 100% → 반경 overheatBurstRadiusTiles 낙인 일괄 폭발, 식는 동안(cooldownMs) 공격 속도 ×coolingSpeedMult·이동 ×coolingMoveMult (공격 가능)
- `weapons.dagger.moves` · `_note`: 56라운드 2단계 Q42·Q55 (임시값 — 시각·판정은 아트 JSON player_dagger_backstab·_flurry 값, 피해·홀드·가열은 시스템 임시값). 판정 R = reach + width/2 = 27

## bow

- `weapons.bow.resource` · `_note`: 49라운드 임시값: 화살 탄창 8발(조준 사격도 1발). 비면 자동 장전 1.3초, R = 수동 장전
- `weapons.bow.carry` · `_note`: 49라운드: 손
- `weapons.bow.ranged` · `_note`: 51라운드 Q3 템포(임시): 시위 당김 drawMs(클릭 → 화살이 떠나는 프레임) 를 보이게 늘이고 다음 발 간격 cooldownMs 520. 느려진 만큼 한 발 피해↑(damageMult 0.9 → 1.1)
- `weapons.bow.personality` · `_note`: 57라운드 Q22~Q37 갈래 재설계 (설계안 design-2026-10-04-build-axis 2.2~2.5): 1단 = 새 동작(move) + 연격 한 타 변화(comboChange), 2단 α = 동작 심화 / β = 고유 자원 규칙 전환(rule). tags = 갈래 노드 태그(노드 태그마다 1점). 새 이름은 자리표시(_tmpName). 옛 갈래 배율(damageMult·hitboxMult)은 새 표에 없어 1.0 — 갈래 그림 배율 = 판정 배율(55 Q15). 2단은 1층 런에서 개성 수급으로 닿지 않음(시험장 검수)
- `weapons.bow.personality.branches[rapid].art` · `_note`: 57 갈래 아트: 몸·무기 bow_rapid_loop (루프 f2~9 = 400ms 2발, releaseFrames 4·8) + 기존 rapid 화살
- `weapons.bow.personality.branches[rapid].art` · `_note60`: 60라운드 계약 art §21: 1단 연격 변화 — 충전 고리 aim_charge → aim_charge_quick 1:1 교체
- `weapons.bow.personality.branches[rapid].next[volley].art` · `_note60`: 60라운드 계약 art §21: 분열 순간 bow_arrow_split · 갈라진 화살 = bow_arrow_rapid(재사용)
- `weapons.bow.personality.branches[rapid].next[quiver]` · `_note`: 53 이름 유지, 효과 재정의. 박힌 화살 밟아 회수는 화살 그림(박힌 화살) 후 연결
- `weapons.bow.personality.branches[rapid].next[quiver].art` · `_note60`: 60라운드 계약 art §21: 떨어진 화살 · 회수
- `weapons.bow.personality.branches[snipe].mods.snipe` · `_note`: 57 저격: 거리 배율 최대 ×1.6(12칸, 조준 사격) — 모든 화살 ×1.5 · 임시값
- `weapons.bow.personality.branches[snipe].art` · `_note`: 57 갈래 아트: 완벽 놓기 화살 bow_arrow_pierce (bow_arrow 대신) · 꿰뚫을 때마다 bow_arrow_pierce_hit
- `weapons.bow.personality.branches[snipe].art` · `_note60`: 60라운드 계약 art §21: 가득 당김 순간 bow_snipe_full
- `weapons.bow.personality.branches[snipe].next[deadeye]` · `_note`: 정밀 조준 1.2 → 2.0초는 숨 규칙(병행 작업 범위)과 합친 뒤
- `weapons.bow.personality.branches[snipe].next[deadeye].mods.snipe` · `_note`: 57 필중: 거리 배율 상한 ×2.2(조준 사격) — 모든 화살 ×2.0 · 임시값
- `weapons.bow.personality.branches[snipe].next[deadeye].art` · `_note60`: 60라운드 계약 art §21: 정밀 조준(숨 집중) 커서 스코프
- `weapons.bow.personality.branches[snipe].next[skypierce]` · `_tmpName`: true (자리표시 이름 — 61라운드 자율 모드에서 확정 이름으로 씀)
- `weapons.bow.personality.branches[snipe].next[skypierce]` · `_note`: 2단 관통 대체 (S-1). 53 Q17 관통 자막은 1단 저격 관통 화살 설명으로
- `weapons.bow.personality.branches[snipe].next[skypierce].art` · `_note60`: 60라운드 계약 art §21: 연결 스택 고리(rowsAre stacks 1~3) · 3스택 선(tile: true 반복)
- `weapons.bow.draw` · `_note`: 56라운드 Q9·Q20 (임시값): 우클릭 누르는 동안 당김(fullMs = 진행 f0~5), 떼면 발사, 자동 발사 없음, 당기는 중 이동 secondary.moveMult. 가득 전 = 약한 1발(weakDamageMult, 관통 없음). 가득 직후 perfectWindowMs 안 = 완벽(조준 사격 × perfectDamageMult, 화살 미소모, 숨 회복, fx bow_perfect_release). 가득 뒤 strainAfterMs 넘게 쥐면 흔들림 동작·조준선 흔들림·위력 감소(strainRampMs 동안 strainMinMult 까지)
- `weapons.bow.gauge` · `_note`: 56라운드 Q17 숨(呼吸) + 재장전 유지 (임시값): 완벽 놓기마다 perfectGain, 가득 차면 다음 당김이 가득에 닿는 순간 집중 — focusMs 동안 물리 배속 focusTimeScale(감속)·완벽 창 ×focusPerfectWindowMult·조준선 흔들림 없음, 놓으면 숨 0
- `weapons.bow.moves` · `_note`: 56라운드 2단계 Q43·Q52·Q55 화살비 (임시값 — 시각은 아트 JSON player_bow_arrow_rain, 첫 낙하·작은 판정·피해는 시스템 임시값)

## 61라운드 4동사 개편 (이 문서로 옮긴 뒤 바뀐 점)
- 자세한 표·이유는 `parts/system/CHANGELOG.md` '61라운드 무기 4동사' 절. 요약: 칼 F 넣기·대치 일격 → 좌 홀드 발도(검기 소모) · 찌르기 검기 단수(`moves.thrust.byKi`)·일섬 분신(`issen.shadow`) 삭제 · 대검 막다가 떼면 돌진(`moves.guardRush`) 삭제, 버티기 → 중압(`brace.windowMs`), 도약 → 파쇄 대쉬 공격(`leap.lengthMult`·`crackRow`) · 단검 과열(`overheatHoldMs`·`cooldownMs`·낙인 `overheatBurstRadiusTiles`·`coolingSpeedMult`·`coolingMoveMult`) → 가속(`hidden`) · 활 숨 → 저격(`gauge.branch`), 화살비 → 좌 홀드(`arrowRain.holdMs`) · 기력 `cost.hits`·`slam` → `hold`·`guardBlock` · 옛 `hitbox` → `combo.radiusPx`·`ranged.cooldownMs/arrowSizePx/spawnPx` · 명경 `live:false` 해제.
