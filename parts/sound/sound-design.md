# LOPAD 음향 바이블 (1차, 29라운드 자율 결정)

> 도영 님 부재 중 권장안으로 결정한 1차 설계다. 모든 수치·이름은 복귀 후 검토 대상이며, 되돌리기 쉬운 형태(단일 스크립트 `parts/sound/work/build.py` 재실행)로 되어 있다.
> 세계관 근거: `parts/story/world-bible.md`(르네상스풍 화약 전장, 건조한 해학 + 서늘함, 8층 제국), 층 이름은 `parts/producer/contracts/story-text.md`.

## 1. 톤 — "화약·강철·목재·돌, 그리고 정적"

| 원칙 | 내용 |
|---|---|
| 재료가 들린다 | 모든 효과음은 네 재료 중 하나를 바탕으로 한다. **화약**(짧은 격발 + 낮은 폭음 + 연기 쉿), **강철**(비조화 배음의 울림), **목재**(피치가 떨어지는 둔탁음 + 삐걱), **돌**(긴 저역 마찰). 마법적인 소리는 '개성'(evolve)과 그림자 걸음에만 허용 — 세계에서 마법은 "희귀한 이질"이다. |
| 건조하다 | 리버브는 크게 쓰지 않는다. 전투음은 거의 드라이, 월드 이벤트(문·본영·층 진입)만 돌방 울림. BGM 은 층이 오를수록 리버브가 커진다(외곽의 소란 → 수도의 정적). |
| 서늘한 한 줄 | 큰 이벤트(보스 등장·개성 변화·황제)에 아주 작은 고음 사인 한 가닥을 깔아 '이질'을 암시한다. 주인공은 말이 없으므로 **목소리 효과음은 없다**(신음도 노이즈로만). |
| 해학은 리듬으로 | 1~2층 류트는 미세 디튠·타이밍 흔들림으로 '취한' 느낌을 낸다. 황제 곡의 메트로놈 틱은 '정연함'을 비꼰다. |
| 피크 -6 dBFS | 모든 파일은 피크 -6 dBFS 로 정규화. 실제 밸런스는 매니페스트 `gainDb` 와 버스(BGM -8 dB)로 맞춘다. |

## 2. 악기 = 합성 방식 (파이썬 표준 라이브러리만)

외부 도구·샘플·네트워크 없이 `wave / array / math / random` 으로 절차 합성한다. `build.py` 의 프리셋 이름 기준.

| 프리셋 | 합성 | 쓰는 곳 |
|---|---|---|
| `burst` | 백색 노이즈 → RBJ 바이쿼드(저/대/고역) → 지수 감쇠 | 격발, 타격, 걸쇠, 발 디딤 |
| `whoosh` | 노이즈 → 컷오프가 지수 스윕하는 밴드패스 → 어택/릴리즈 | 휘두름, 대쉬, 투사체 |
| `thud` | 사인 피치 하강(예 140→50 Hz) + 지수 감쇠 | 목재·몸통·문·북 |
| `metal` | 비조화 배음 합(1, 1.47, 2.09, 2.56, 3.73, 5.11배) 각각 다른 감쇠 | 패링, 갑옷, 동전, 쇠사슬, 모루 |
| `bell` | 비조화 배음(1, 2, 2.76, 4.07, 5.4배) 긴 감쇠 | 개성 변화, 타이틀 종, 운명 결정 |
| `pluck` | Karplus-Strong 현(지연선 + 평균 감쇠) | 활시위, 1~2층 류트 |
| `kick / snare / handdrum` | thud + 클릭 / 고역 노이즈 + 짧은 톤 / thud + 슬랩 노이즈 | 모든 북 |
| `organ` | 사인 배음 1·2·3·4·6·8 + 미세 디튠 두 겹 | 6~8층 |
| `flute` | 사인 + 2배음 0.25 + 비브라토 4.6 Hz | 황제 선율 |
| `horn` | 톱니 두 겹(디튠) → 저역통과 700~1100 Hz | 3~5층 뿔나팔, 보스 스탭 |
| `reverb` | Schroeder: 병렬 콤 4(29.7/37.1/41.1/43.7 ms × size) + 직렬 올패스 2, 댐핑 | 월드 이벤트, BGM |
| `echo` | 단일 피드백 딜레이(저역통과) | 1~2층 류트 |

루프 처리 규칙: 루프 재료(드론·노이즈)는 길이에 정수 주기로 맞추고(`tone_loop`, `lfo_loop`), 노이즈는 끝↔처음 크로스페이드(`noise_loop`), 필터·리버브·에코는 버퍼를 두 번 이어 처리한 뒷절반을 취해(`wrap2`, `loop=True`) 경계에서 상태가 이어진다. 음표는 `wrap=True` 로 섞어 꼬리가 앞으로 감긴다.

## 3. BGM — 층별 매핑

| 곡 | 파일 | 길이 | 매핑 | 설계 |
|---|---|---|---|---|
| title | `bgm/title.wav` | 32.0 s | 타이틀·개성 선택 | A1 톱니 드론(컷오프 LFO 16 s) + E2·A2, 바람, 4초마다 멀리서 북(저역통과·큰 리버브), 드문 종 4음(E C D A), 중반에 서늘한 고음 한 가닥 |
| floor_low | `bgm/floor_low.wav` | 30.0 s (96 BPM, 12마디) | 1~2층 (술독 '잔', 도박장 '패') | A1 드론, 류트 아르페지오(스윙 8분음, ±0.6% 디튠, ±12 ms 흔들림), 베이스 류트, 손북(1박 둔탁·2.5/4박 슬랩), 술잔 부딪힘 4회, 에코 + 작은 리버브. 진행 Am Am Dm Em / Am G F E / Am Dm E Am |
| floor_mid | `bgm/floor_mid.wav` | 28.8 s (100 BPM, 12마디) | 3~5층 (야전병원 '붕', 용병 '계', 첩보 '귀') | D2 드론 + Eb2 반음 긴장(2마디 주기로 들락), 행진 스네어(1강·2에 16분 2타·3·4에 3연, 4마디마다 롤), 낮은 북 1·3박, 뿔나팔 스탭 4/8/12마디(D → D+A → D+A+Bb), 멀리 포성 2회 |
| floor_high | `bgm/floor_high.wav` | 32.0 s | 6~8층 (연회 '연', 근위 '적', 수도 '평상') | 오르간 지속 화음 8초씩 Dm Bb Gm A(어택 1.6 s, 겹침), 페달, 느린 윗소리 5음, 희미한 고음 반짝임·공기, 큰 리버브(wet 0.5) — 북 없음 |
| boss | `bgm/boss.wav` | 27.4 s (140 BPM, 16마디) | 1~7층 보스전 | E1 드론, 톱니 오스티나토 8분음(E E G E / E E F E, 2마디 교대), 킥 1·3·4.5박, 톰 16분 연타, 스네어 2·4, 삼전음(E+Bb) 뿔나팔 2마디마다, 8·16마디 쇠 타격 + 스네어 롤 |
| emperor | `bgm/emperor.wav` | 32.0 s (60 BPM) | 황제 '평' 보스전 | D3·A3 사인 패드 + D2 삼각, 플루트 풍 단선율 16음(D E F# A B A F# E D B A B D E D –), 매 박 메트로놈 틱, 16초 주기로 부푸는 90 Hz 저역 노이즈("붉은 두려움"), 큰 리버브 |

전환 권장: 크로스페이드 1200 ms. 보스 방 진입 시 층 BGM → boss(8층은 emperor). 보스 사망 후 층 BGM 복귀. 일시정지 시 BGM -6 dB 덕킹(선택).

## 4. 효과음 표

형식: 44.1 kHz / 16 bit / mono / 피크 -6 dBFS(합성 원본 기준 — 배포 파일은 OGG·M4A, 7장). `gainDb` 는 SFX 버스 기준 권장 상대 음량. 트리거는 **제안**이며 시스템 파트가 실제 이벤트 이름으로 확정한다(`ui-system-interface.md` 에 이미 있는 이름은 그대로 썼다).

### 4-1. 무기 (주인공)
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| swing_katana | 0.20 s | `PLAYER_ATTACK` weapon:katana | 5.2k→1.4k 밴드 스윕 바람 + 얇은 강철 | -2 |
| swing_greatsword | 0.39 s | `PLAYER_ATTACK` weapon:greatsword | 900→180 스윕, 끝에 둔탁한 무게 | -1 |
| swing_dagger | 0.11 s | `PLAYER_ATTACK` weapon:dagger | 7k→2.5k 아주 짧은 스침 | -3 |
| bow_shot | 0.30 s | `PLAYER_ATTACK` weapon:bow | 현(190 Hz) 튕김 + 상승 바람 | -2 |
| bow_draw | 0.60 s | `PLAYER_SECONDARY` aimedshot start | 삐걱이는 나무·현(차지 600 ms 에 맞춤) | -8 |
| bow_aimed | 0.48 s | `PLAYER_SECONDARY` aimedshot release | 깊은 현(110 Hz) + 꿰뚫는 바람 | -1 |
| parry | 0.60 s | `PARRY_SUCCESS` | 강철 1.5k+2.6k 울림, 작은 리버브 | 0 |
| guard_hold | 0.60 s **루프** | `PLAYER_SECONDARY` guard hold | 62 Hz 톱니 저역 + 10 Hz 떨리는 럼블 + 희미한 쇠 험 | -10 |
| guard_push | 0.48 s | `PLAYER_SECONDARY` guard release | 95→28 Hz 압력 + 바람 | 0 |
| shadowstep | 0.42 s | `PLAYER_SECONDARY` shadowstep | 역방향 바람(600→4.5k 상승) + 꺼지는 저음, 끝에 딸깍 | -2 |
| dash | 0.23 s | `PLAYER_DASH` | 700→3.2k 바람 + 발 디딤 | -3 |

### 4-1-1. 대검 홀드 차지 · 칼 3타 잔상 베기 (55라운드, 9종)
결정 근거: `parts/producer/decisions/2026-10-03-round-55-weapon-fx-overhaul.md` Q22(칼 잔상 베기 150 ms 뒤)·Q24(차지 0.4/0.8/1.2 s 3단)·Q27(3단만 백열)·Q30(막타 = 차지 내려찍기만)·Q32(음향 병행 제작). 기존 방식(build.py 절차 합성, 44.1 kHz/16 bit/mono, 피크 -6 dBFS, 목소리 없음) 그대로. 트리거는 **제안**(시스템 이벤트 후보 `PLAYER_CHARGE {phase: start|stage|release, stage}`).

| id | 길이 | 루프 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|---|
| charge_start | 0.30 s | - | `PLAYER_CHARGE` weapon:greatsword phase:start | 손잡이 고쳐 쥠 + 1.6k→4.2k 쇠 긁힘(34 Hz 떨림) + 760 Hz 쇠 울림 + 420→1500 Hz 숨처럼 차오르는 노이즈(목소리 아님) + 58→88 Hz 무게 | -4 |
| charge_stage1 | 0.62 s | - | `PLAYER_CHARGE` phase:stage stage:1 (0.4 s) | 호박빛 '징' D4(294 Hz), 비조화 배음, 첫 0.12 s 음높이 +1.2% 휘어 오름, 어둡게(LP 2.2k) | -6 |
| charge_stage2 | 0.82 s | - | `PLAYER_CHARGE` phase:stage stage:2 (0.8 s) | '징' A4(440 Hz) + D4 겹침, 윗배음 조금 열림 | -4 |
| charge_stage3 | 1.25 s | - | `PLAYER_CHARGE` phase:stage stage:3 (1.2 s) | '징' D5(587 Hz), 가장 밝게(LP 8.2k) + 아래 옥타브 D4 + 3.5k 백열 반짝임 + 상승 바람, 작은 울림 | -2 |
| charge_loop | 1.00 s | 루프 | `PLAYER_CHARGE` phase:start 부터 release·취소까지 | 55 Hz 톱니 저역 + 110/113 Hz 3 Hz 맥놀이 + 4 Hz 떨리는 럼블 + 희미한 D4 험(정수 주기·랩어라운드) | -12 |
| charge_slam_lv1 | 0.60 s | - | `PLAYER_CHARGE` phase:release stage:1 | 125→36 Hz 강타 + 저역 폭발 + 1.8k 돌 깨짐 + 640 Hz 칼날 쇳소리 + 부스러기 6 | -2 |
| charge_slam_lv2 | 0.80 s | - | `PLAYER_CHARGE` phase:release stage:2 | 115→30 Hz 더 무거운 강타(×1.3) + 저역 럼블 + 부스러기 10 | -2 |
| charge_slam_lv3 | 1.40 s | - | `PLAYER_CHARGE` phase:release stage:3 (막타·충격파 링) | 105→26 Hz 강타(×1.6) + 50→24 Hz 충격파 저음 + 2.6k→220 Hz 퍼져 나가는 바람(링) + 땅울림 + 부스러기 16 + 1.3k 백열 쇳소리, 울림 | 0 |
| katana_echo | 0.25 s | - | `PLAYER_ATTACK` weapon:katana combo:3 phase:echo (본 타격 150 ms 뒤 후속 판정) | 6.8k→2.2k 얇은 바람 + 3.3k 쇠 틱, 고역통과 1.4k, 32 ms 간격 3겹 반복(잔상) | -4 |

설계 메모:
- **내려찍기는 단계별 파일 3개**(재생 속도 변주 안 씀). 근거: ① 3단은 충격파 꼬리가 붙어 구조가 다르다 — 속도만으로는 못 만든다. ② 재생 속도를 올리면 음높이가 올라가 더 가볍게 들린다(단계가 오를수록 무거워져야 하는 것과 반대). ③ 아트 fx `greatsword_charge_slam_lv1~3` 와 1:1 대응. 용량 증가는 3개 합쳐 약 240 KB.
- 단계 '징'은 D4→A4→D5(5도·4도 상승)로 D 단조 BGM 과 부딪치지 않는다. 앞 단계 꼬리가 다음 단계와 겹쳐도 협화.
- 0.18 s 홀드 인식 전에 떼거나 1단(0.4 s) 전에 떼었을 때의 소리는 정하지 않았다 — 기존 `swing_greatsword`(일반 내려찍기)로 두는 것을 권장.

연결 권장:
- 홀드 인식(0.18 s) 시점에 charge_start + charge_loop(150 ms 페이드인) 동시 시작. 단계 도달마다 charge_stageN 1회. 루프 재생 속도를 단계마다 1.0/1.03/1.06 으로 올리면 긴장이 쌓인다(선택).
- 떼면 charge_loop 80~120 ms 페이드아웃, charge_slam_lvN 은 **판정(impact) 프레임**에 재생(떼는 순간이 아님). 파일 0 ms 가 타격 순간이다.
- 피격 취소 시 charge_loop 즉시 페이드아웃(60 ms), 울리던 stage 음은 그대로 둔다.
- charge_slam_lv3 와 겹쳐 쓰는 막타 적중음(`hit_enemy_crit` 등)은 그대로 재생해도 된다(대역이 다름). 화면 흔들림·히트스톱과 같은 프레임 권장.
- katana_echo 는 잔상 판정 시점(본 타격 +150 ms)에 재생. 본 휘두름(`swing_katana`)과 20 ms 중복 규칙에 걸리지 않도록 다른 키이므로 그대로 겹친다. ±4% 랜덤 피치 권장.

### 4-1-2. 56라운드 가드·자원·무기별 새 공격 수단 (34종 + 검수 후 2종 = 36종)
결정 근거: `parts/producer/decisions/2026-10-04-round-56-weapon-feedback.md` Q2·Q3·Q7~Q10·Q13~Q20·Q28~Q29·Q40~Q43, 검수 Q44~Q47(아래 '검수 결정' 참고). 도영 님 평가 "효과음 괜찮아"(기존 톤 유지). 기존 방식(build.py 절차 합성, 44.1 kHz/16 bit/mono, 피크 -6 dBFS, 목소리 없음) 그대로, `katana_echo` 뒤에 추가 — 기존 75개 파일 바이트 불변(md5 대조). 트리거는 **제안**(시스템이 실제 이벤트 이름으로 확정).

새 재료·음색 규칙:
- **검기(칼) = '칼날 울림'**(`blade_ring`: 위로 긁는 쇠 스침 + 하모닉에 가까운 얇은 배음). 대검 차지의 비조화 '징'(`jing`)과 귀로 구분된다. 단계 A4 → D5 → A5(재 → 호박 → 백열, 윗배음·고역이 단계마다 열림).
- **찢김**(`tear`): 70~95 Hz 로 거칠게 떨리는 밴드 스윕 노이즈 — 일섬·발도·간파의 '공기 찢김'. 일반 휘두름(`whoosh`)보다 날카롭다.
- **재·낙인**(`sizzle`, `ash_pop`): 지짐 쉿 + 재 폭발 '펑'. 마법음이 아니라 '불·재' 재료로 둔다(그림자 분신만 이질 허용).
- 숨 헐떡임(그로기)·숨 들이켬(숨 집중)은 성대음 없이 노이즈 포먼트·밴드 노이즈로만.
- 음높이는 D 단조 축(D·A) — 차지 '징'·BGM 과 협화.

| id | 길이 | 루프 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|---|
| perfect_guard | 0.95 s | - | `PERFECT_GUARD` | 흡수된 작은 둔탁음 + 맑은 종형 금속 A5·D6 + 4.4k 반짝임, 작은 울림 | 0 |
| parry_perfect | 0.79 s | - | `PARRY_SUCCESS` weapon:katana (기존 `parry` 위에 겹침) | 1.8k 위 대역만: 칼날 울림 A6 '키잉' + 3.1k 쇠 + 위로 번뜩이는 스침 | -2 |
| groggy_start | 1.38 s | - | `GROGGY` phase:start | 220→70 Hz 기운 빠짐 + 헐떡임 2회(노이즈 포먼트) + 무릎 꺾임 둔탁음 + 갑옷 처짐 | -1 |
| kenki_stage1 | 0.47 s | - | `KENKI_CHANGED` stage:1 | 칼날 울림 A4, 어둡게(재) | -6 |
| kenki_stage2 | 0.62 s | - | `KENKI_CHANGED` stage:2 | 칼날 울림 D5 + 아래 옥타브, 조금 밝게(호박) | -5 |
| kenki_stage3 | 0.89 s | - | `KENKI_CHANGED` stage:3 | 칼날 울림 A5 + 미세 떨림 + 3.5k 백열 고음, 작은 울림 | -4 |
| utbun_full | 1.13 s | - | `UTBUN_CHANGED` full:true (가득 차는 순간 1회만, Q47) | 끓어오르는 저역 잔불 + 0.3 s 불씨 '훅' + 타닥 18 + 달아오른 D4 쇠 험 | -3 |
| brand_apply | 0.19 s | - | `BRAND_CHANGED` delta>0 | 5.6k 지짐 '칙' + 틱 | -7 |
| brand_burst | 0.79 s | - | `BRAND_BURST` | 60 ms 빨려드는 역바람 → 재 폭발 '펑'(0.06 s) + 지짐 꼬리 | -1 |
| overheat_burst | 1.50 s | - | `OVERHEAT` full:true | 큰 재 폭발 + 엇갈린 작은 폭발 4 + 길게 식는 증기 쉿 + 타닥 | 0 |
| breath_focus | 0.98 s | - | `BREATH_FOCUS` phase:start | 빨려드는 바람 0.45 s → 110→46 Hz 내려앉음(감속) + 희미한 D7 한 가닥 | -3 |
| issen_dash | 0.39 s | - | 칼 일섬 돌진 | 칼집 딸깍 + 디딤 + 1.8k→7.5k 공기 찢김 + 6.5k→2.4k 칼바람 | -1 |
| issen_burst | 0.83 s | - | 칼 일섬 선 터짐 | 선을 따라 0.1 s 동안 번지는 파열 9 + 낮은 폭음 + 칼날 울림 D6 | -1 |
| shadow_clone | 0.65 s | - | 칼 그림자 분신(검기 3단 일섬) | 0.37 s 동안 빨려드는 어두운 역바람 + 낮은 찢김 → 0.37 s 도착 베기 | -2 |
| katana_counter | 0.47 s | - | 칼 간파 반격 | 7.2k→2k 칼바람 + 찢김 + 0.06 s 적중 머리 + 칼날 울림 | -1 |
| katana_iai_hold | 2.00 s | 루프 | 칼 대치 일격 홀드 | D2 톱니 저역(0.5 Hz 조임) + A6 칼날 험(3 Hz 떨림) + 공기 + 1 s 간격 맥박 | -12 |
| katana_iai_release | 0.68 s | - | 칼 대치 일격 발도 | 딸깍 → 30 ms 뒤 9k 까지 찢는 발도 + 칼날 울림 A5 + 무게 | 0 |
| gs_plunge | 0.69 s | - | 대검 땅 꽂기(발현 후 차지) | 100→34 Hz 강타 + 흙 파고듦 + 자갈 + 21 Hz 떨리는 칼날 | -1 |
| gs_crack | 1.00 s | - | 대검 균열 충격파 | 앞으로 뻗는 갈라짐 14(점점 어둡게) + 55→26 Hz 충격파 + 땅울림 | 0 |
| gs_drag | 0.38 s | - | 대검 **3타** 뒤 끌림(Q46) | 칼끝 돌바닥 긁힘(27 Hz) + 장화 미끄러짐 + 자갈 | -5 |
| gs_tackle | 0.52 s | - | 대검 어깨 태클(대쉬 공격) | 무거운 박차기 + 낮은 돌진 바람 + 갑옷 + 0.16 s 어깨 충돌 | -1 |
| gs_brace_upswing | 0.58 s | - | 대검 버티기 올려베기 | 발 박기 + 쇠 긁힘 + 180→1.3k 치솟는 무거운 바람 | -1 |
| gs_leap | 0.53 s | - | 대검 공중제비 도약 | 강한 박차기 + 도는 바람 2회 + 갑옷 출렁 | -2 |
| gs_leap_slam | 0.93 s | - | 대검 도약 착지 찍기 | 지면 강타(×1.2) + 몸 내려앉음 + 갑옷 + 흙먼지 | 0 |
| gs_guard_rush | 0.63 s | - | 대검 막다가 떼면 돌진 | 가드 풀며 터지는 압력 + 앞으로 미는 바람 + 디딤 3 | 0 |
| dagger_backstab | 0.48 s | - | 단검 등 뒤 치명 찌르기 | 짧은 스침 → 0.04 s 파고드는 찌르기 + 날 박힘 + 2.2k 치명 울림 | -1 |
| dagger_flurry1~4 | 0.07 s ×4 | - | 단검 고속 난타(찌를 때마다 1개) | 짧은 찌르기 4변주(기본/낮고 둔탁/높고 가벼움/쇠 스침) | -5 |
| bow_release_weak | 0.21 s | - | 활 일찍 놓기 | 둔한 240 Hz 시위 '퉁'(LP 1.6k) + 13 Hz 흔들리는 바람 + 연기 쉿 | -4 |
| bow_release_perfect | 0.50 s | - | 활 완벽 놓기 | 110 Hz 깊은 시위 + 맑은 '팅' A5 + 9k 까지 꿰뚫는 바람 | 0 |
| arrow_rain_launch | 0.78 s | - | 활 화살비 발사 | 시위 3번(0/0.06/0.12 s) + 하늘로 멀어지는 바람 | -2 |
| arrow_rain_impact | 0.63 s | - | 활 화살비 낙하 | 0.1 s 내려오는 휘파람 → 흙에 꽂힘 3(0.1/0.16/0.23 s) + 화살대 떨림 | -2 |
| bow_full_draw | 0.15 s | - | 활 가득 당김 알림(Q44) `PLAYER_SECONDARY{kind:aimedshot,phase:full}` | 딸깍(5.2k) + 활대 멈춤 나무 '톡'(320→210 Hz) + 팽팽한 시위 '틱' D4(고역통과 500) + 아주 작은 A6 쇠 반짝임, 드라이 | -4 |
| bow_strain | 1.00 s | 루프 | 활 오래 쥐어 흔들림(Q44) `PLAYER_SECONDARY{kind:aimedshot,phase:strain}` | 한계까지 당긴 시위 험 95/98 Hz 톱니(3 Hz 맥놀이, 밴드 1.2k) × 7·11 Hz 불규칙 떨림 + 28 Hz 나무 삐걱(5 Hz 일렁임) + 드문 삐걱 딸깍 3(랩어라운드). `bow_draw` 끝 음색(95 Hz·1.2k·28 Hz)을 이어받음, 정수 주기 이음매 | -10 |

연결 권장:
- **퍼펙트 가드·패링**: `perfect_guard` 는 피해 무시 판정 프레임에 1회(일반 가드 피격음 대신). 칼 패링은 기존 `parry` + `parry_perfect` 동시 재생(문구 'PARRY'·검기 1단 충전과 같은 프레임) — **결정됨(Q45)**. 다른 무기 패링은 `parry` 만.
- **그로기**: 기력 0 순간 `groggy_start` 1회. 그로기 1.5 s 동안 가드하면 기존 `guard_hold` 그대로.
- **검기**: 단계가 **오를 때만** 해당 단계음(패링 즉시 충전 포함). 소모 때는 일섬·분신 소리가 대신한다.
- **일섬**: 발도 순간 `issen_dash` → 선 폭발 연출 프레임에 `issen_burst`. 검기 3단이면 분신 출발 시점(일섬 +0.2 s)에 `shadow_clone`(파일 0.37 s = 도착 베기 = 50% 피해 판정, Q29 '몸 기준 570 ms' 와 맞음).
- **대치 일격**: 홀드 시작에 `katana_iai_hold`(200 ms 페이드인), 떼면 루프 60 ms 페이드아웃 + `katana_iai_release`(파일 0.03 s 가 칼이 나오는 순간).
- **대검 꽂아내리기**: `gs_plunge` 와 `gs_crack` 같은 프레임(또는 crack 40 ms 뒤). 울분 소모로 강화된 차지는 `gs_crack`/`charge_slam_lvN` rate 0.92 로 더 무겁게(선택).
- **도약 찍기**: 박찰 때 `gs_leap`, 착지 판정 프레임에 `gs_leap_slam` + (차지 1단 이상이면) `charge_slam_lvN` 겹침. 차지 루프·단계음은 공중에서도 유지.
- **끌림**: 대검 3연격의 **3타에만** 휘두름 끝(몸이 끌려가는 구간 시작)에 `gs_drag` — **결정됨(Q46, 3타만)**. 1·2타에는 재생하지 않는다.
- **낙인**: 스택마다 `brand_apply`(20 ms 중복 규칙으로 다수 적 동시 표식은 1회). 기폭 `brand_burst` 는 스택 수에 따라 gain +0~3 dB 권장. 과열 100% 는 `overheat_burst` 1회(개별 기폭음은 생략).
- **고속 난타**: 찌를 때마다 `dagger_flurry1~4` 중 직전과 다른 하나 + ±3% rate. 20 ms 중복 규칙은 키가 달라 걸리지 않는다.
- **활**: 당기기 시작 = 기존 `bow_draw`(재사용, 아래 참고). 가득 찬 순간(완벽 놓기 창 0.15 s 시작) `bow_full_draw` 1회(파일 0 ms = 가득 찬 순간) — **결정됨(Q44)**. 너무 오래 쥐어 조준선이 흔들리기 시작하면 `bow_strain` 루프(150~200 ms 페이드인), 떼거나 취소하면 60 ms 페이드아웃(흔들림 단계 위력 감소와 같은 시점) — **결정됨(Q44)**. 떼는 순간 약한/일반/완벽에 따라 `bow_release_weak` / 기존 `bow_aimed` / `bow_release_perfect`. 숨 가득 → 감속 진입 순간 `breath_focus`. 화살비는 발사 `arrow_rain_launch`, 낙하 `arrow_rain_impact`(파일 0.1 s = 첫 꽂힘).

재사용(새로 만들지 않음):
- `bow_draw` — 같은 키가 이미 있음(0.60 s, 삐걱이는 나무·현). '당기기 시작' 용도 그대로 — **결정됨(Q47, 기존 유지)**. 가득 찬 뒤 흔들림 전까지는 정적, 흔들림 단계는 `bow_strain`(Q44).
- 일반(완벽 아닌) 가득 당긴 발사 = 기존 `bow_aimed`. 도약 찍기 차지 단계분 = 기존 `charge_slam_lv1~3`. 그로기 중 가드 = 기존 `guard_hold`.

검수 결정 (56라운드 Q44~Q47, 2026-10-04):
- Q44 활 가득 당김 알림: **짧은 '틱' `bow_full_draw` 추가** + 오래 쥐어 흔들릴 때 **작은 시위 떨림음 `bow_strain`(루프)** 함께 — 제작 완료(`arrow_rain_impact` 뒤에 등록, 기존 109개 파일 바이트 불변 md5 대조).
- Q45 칼 패링 성공음: **기존 `parry` + `parry_perfect` 겹치기** — 제작·문서 그대로, 결정됨.
- Q46 대검 끌림음 `gs_drag`: **3타만** — 연결 권장·매니페스트 트리거(`combo:3`) 갱신(오디오 파일은 그대로).
- Q47 세부: `bow_draw` 기존 유지 · 울분 가득(`utbun_full`)은 가득 차는 순간 **한 번만**(반복음 없음) · 대검 키 이름 **`gs_` 유지** — 이미 그대로, 결정됨.

### 4-1-3. 57·58라운드 빌드 축·갈래 1단 수단·칼 찌르기·대검 균열·상태 (37종)
결정 근거: `parts/producer/decisions/2026-10-04-round-57-systems-review.md` Q22~Q39(Q39 '특성·갈래 본격 디벨롭' 음향 병행), `2026-10-04-round-58-weapon-feedback2.md` Q1(3타 찌르기·검기 소모 강화)·Q3(휘둘러 내리찍기 + 균열 3/4/5칸)·Q5~Q7·Q11, 설계안 `design-2026-10-04-build-axis.md` 6.1·`-chwigi.md`. 트리거 이벤트 이름은 UI 계약 §14.11(`TAG_SET_CHANGED`·`DUAL_TRAIT_GAINED`·`CURSE_GAINED`·`CURSE_ENDED`·`PERFECT_SUCCESS`)에 있는 것은 그대로, 없는 것은 **제안**. 기존 방식 그대로(build.py 절차 합성, 피크 -6 dBFS, 목소리 없음), `bow_strain` 뒤에 등록 — 기존 111개 파일 바이트 불변(WAV·OGG·M4A md5 대조).

새 재료·음색 규칙:
- **세트 = 걸쇠가 맞물리는 강철 + D 단조 종**(`latch`): 2단계 D5 → 4단계 D5·A5 → 6단계 D5·A5·D6 + 낮은 북 + 서늘한 한 가닥. 태그 공용(태그별 색은 UI·아트가 맡음).
- **이중 개성 = 어긋난 두 종이 한 음으로 겹침**(`glide_bell`, A4 ±1.5% → A4). 개성(evolve) 계열 '이질' 허용.
- **저주 = 깃펜·밀랍 도장·쇠사슬 + 낮은 삼전음 D2–G#2**(`tritone_drone`). 해제는 삼전음이 5도(D–A)로 풀림. 피의 계약은 피·심장 박동(`heartbeat`)이 더해진 짙은 판.
- **각성 = 공용 뼈대**(`_awaken_core`: 모여드는 바람·열리는 D 드론 → 0.9 s 북 + 종 아르페지오 D4 A4 D5 F5 A5 D6) **+ 무기 서명**(칼 달빛 칼날 울림 / 대검 산사태·징 / 단검 그림자 셋 교차 베기 / 활 유성 낙하). 4파일.
- 음높이는 D 단조 축 유지(검기 A4·D5·A5, 차지 '징' D4·A4·D5 와 협화).

| id | 길이 | 루프 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|---|
| set_tier1 | 0.70 s | - | `TAG_SET_CHANGED` stage:2 (오를 때만) | 걸쇠 '철컥' + 종 D5 | -5 |
| set_tier2 | 0.95 s | - | `TAG_SET_CHANGED` stage:4 | 걸쇠 둘 + 종 D5·A5 + 자물쇠 몸통 | -4 |
| set_tier3 | 1.40 s | - | `TAG_SET_CHANGED` stage:6 | 무거운 자물쇠 + 종 D5·A5·D6 + 낮은 북 + 고음 한 가닥, 울림 | -2 |
| dual_trait | 1.50 s | - | `DUAL_TRAIT_GAINED` | 두 종 A4 ±1.5% → 0.45 s 에 한 음 + D5 피어남 + 바람 | -2 |
| curse_take | 1.30 s | - | `CURSE_GAINED` | 깃펜 → 0.2 s 밀랍 도장 + 쇠사슬 3 + 삼전음 드론 | -2 |
| curse_end | 1.00 s | - | `CURSE_ENDED` | 족쇄 딸깍 + 사슬 떨어짐 4 + 빠지는 숨(노이즈) + D–A 로 풀림 | -4 |
| blood_pact | 1.80 s | - | `CURSE_GAINED` source:bloodPact (개성 '피의 계약' 칸) | 손바닥 긋는 찢김 → 핏방울 3 + 심장 2회 + 어두운 D4 종 + 짙은 삼전음 | -1 |
| perfect_evade | 0.62 s | - | `PERFECT_SUCCESS` kind:perfectEvade | 1.2 kHz 위만: 스쳐 지나가는 날 바람(오르내림) + '팅' A6 + D7 | -2 |
| awaken_katana | 2.60 s | - | `WEAPON_EVOLVED` kind:awaken weapon:katana | 공용 뼈대 + 0.9 s 찢김·초승달 베기 + 칼날 울림 A5·D6(떨림) | 0 |
| awaken_greatsword | 2.60 s | - | 〃 weapon:greatsword | 공용 뼈대 + 0.9 s 강타(×1.6) + 굴러 내리는 바위 18 + 자갈 + 징 D4·A4 | 0 |
| awaken_dagger | 2.60 s | - | 〃 weapon:dagger | 공용 뼈대 + 빨려드는 역바람 3겹 → 0.9 s 교차 베기 3 + 재 폭발 3 | 0 |
| awaken_bow | 2.60 s | - | 〃 weapon:bow | 깊은 시위 110 Hz + 0.35~0.9 s 떨어지는 휘파람 → 유성 폭음 + 불티 26 + 공용 종 | 0 |
| katana_spin_ready | 0.32 s | - | `PLAYER_SKILL` katana move:spin phase:ready (0.4 s 홀드 도달) | 딸깍 + 칼날 울림 A5 | -6 |
| katana_spin | 0.52 s | - | `PLAYER_SKILL` katana move:spin phase:release | 발 돌림 + 대역이 올랐다 내려오는 한 바퀴 칼바람 + 찢김 + 칼날 울림 D5 | -1 |
| katana_guardbreak_hold | 1.00 s | 루프 | `PLAYER_SKILL` katana move:guardbreak phase:hold | 달아오르는 칼: D3 웅웅(2 Hz) + 6 Hz 떨리는 A5 험 + 열기 노이즈 + 잔불 타닥 10 | -11 |
| katana_guardbreak | 0.77 s | - | `PLAYER_SKILL` katana move:guardbreak phase:strike | 0~0.1 s 내려오는 칼바람 → 0.1 s 판정: 쪼개지는 쇠 720 Hz + 강타 115→38 Hz + 칼날 울림 D5 | 0 |
| katana_thrust | 0.28 s | - | `PLAYER_ATTACK` katana combo:3 | 반 발 디딤 + 곧게 뚫는 좁은 '쉭'(2.2→5.2k, Q 2.4) + 칼끝 틱 | -2 |
| katana_thrust_ki1 | 0.47 s | - | `PLAYER_ATTACK` katana combo:3 kenki:1 (겹침) | 0.2 s 뻗는 찢김 + 칼날 울림 A4(재) | -5 |
| katana_thrust_ki2 | 0.58 s | - | 〃 kenki:2 | 0.24 s 찢김 + 칼날 울림 D5(호박) | -4 |
| katana_thrust_ki3 | 0.78 s | - | 〃 kenki:3 | 0.3 s 찢김 + 칼날 울림 A5(백열) + 3.5k 고음, 울림 | -3 |
| gs_crack_line_lv1 | 0.73 s | - | `PLAYER_CHARGE` greatsword release stage:1 part:crack | 커서 쪽으로 달려가는 갈라짐 9(3칸 × 칸당 0.06 s) + 끝 '툭' + 땅울림 | -1 |
| gs_crack_line_lv2 | 0.79 s | - | 〃 stage:2 | 4칸(0.24 s), 갈라짐 12 | -1 |
| gs_crack_line_lv3 | 0.85 s | - | 〃 stage:3 | 5칸(0.30 s), 갈라짐 15 | 0 |
| gs_quake_ring | 1.00 s | - | `PLAYER_CHARGE` greatsword release branch:pressure part:quake (중압) | 12 Hz 로 떨리는 땅(48→34 Hz) + 안으로 빨려드는 바람 → 0.32 s 짓눌림 '쿵' + 자갈 | 0 |
| gs_shatter_snuff | 0.27 s | - | `PLAYER_SKILL` greatsword move:crack phase:snuff (파쇄: 투사체 소멸) | 으스러지는 '빠직'(돌·쇠 파편) + 먼지 '푹' | -4 |
| dagger_fan_throw | 0.34 s | - | `PLAYER_SKILL` dagger move:fan_throw (질풍) | 손목 딸깍 + 25 ms 간격 높은 바람 3(음높이 다름) + 칼날 틱 | -2 |
| dagger_cross_clone | 0.62 s | - | `PLAYER_SKILL` dagger move:cross_clone (쌍격) | 0.16 s 빨려드는 어두운 역바람 → 0.16·0.19 s 엇갈린 두 베기(X) + 낮은 몸통 | -2 |
| bow_rapid1~3 | 0.13 s ×3 | - | `PLAYER_ATTACK` bow move:rapid variant:1~3 (속사) | 짧은 시위 '틱'(220/196/247 Hz) + 짧은 화살 바람 | -4 |
| bow_pierce | 0.26 s | - | `PLAYER_SKILL` bow move:pierce phase:pass (저격, 적마다) | 박혔다 빠지는 '퍽' + 계속 뻗어 나가는 3.8→7.5k 바람 | -3 |
| mark_stack | 0.18 s | - | `MARK_CHANGED` delta>0 (공용 표식) | 붉은 분필 긋는 '슥' + 나무 틱 (낙인 지짐과 구분) | -8 |
| boil_burst | 0.82 s | - | `STATUS_BURST` kind:boil (상흔 4 끓음) | 0.14 s 빨라지는 거품 → 젖은 재 폭발 + 핏방울 + 지짐 | -2 |
| stillness | 1.10 s | - | `SET_EFFECT` tag:insight effect:stillness (간파 6 정적) | 빨려드는 숨(노이즈) → 0.12 s '틱' + 얼어붙는 A5·D6 + 내려앉는 92→40 Hz | -3 |
| drunk_ignite | 0.62 s | - | `POOL_IGNITED` (술 웅덩이 점화·술불) | 작은 '훅' 95→45 Hz + 300→2.4k 번지는 불길 + 타닥 9 | -3 |
| drunk_sway | 0.47 s | - | `DRUNK_SWAY` (취기 4 취보 '휘청') | 7 Hz 일렁이는 바람 + 장화 미끄러짐 + 술 출렁 + 작은 잔 '팅' | -3 |
| endure_trigger | 1.02 s | - | `ENDURE_TRIGGERED` (버팀 4·6, 패시브 '마지막 잔') | 심장 두 번 + 발 박는 강철 + 차오르는 숨(노이즈) + 낮은 D2 | -1 |

연결 권장:
- **세트**: 단계가 **오를 때만** 해당 단계음 1회(내려갈 때 없음). 같은 프레임에 두 태그가 오르면 높은 단계 하나만.
- **이중 개성·저주·각성**: 메뉴 선택 확정 프레임. 피의 계약은 `curse_take` 대신 `blood_pact` 하나만. 각성은 파일 0.9 s 가 정점 — 무기 외형 전환·화면 번쩍임을 재생 시작 + 0.9 s 에 맞추면 좋다(또는 재생을 0.9 s 앞당김). 각성 때 기존 `evolve` 는 겹치지 않는다.
- **완벽 회피**: `dash`·`shadowstep` 위에 겹침(1.2 kHz 아래를 비워 둠). 간파 세트 진행 연출과 같은 프레임.
- **회전 베기**: 0.4 s 홀드 도달 `katana_spin_ready` → 떼면 `katana_spin`. 검기 소모 2회전은 같은 파일 0.28 s 뒤 rate 1.05.
- **가드 불가 내려베기**: 홀드 시작 `katana_guardbreak_hold`(150 ms 페이드인, 0.6 s 까지 rate 1.0→1.06 선택) → 0.6 s 도달 알림은 `katana_spin_ready` 를 rate 0.667(A5→D5)로 재사용 → 떼면 루프 60 ms 페이드아웃 + `katana_guardbreak` 를 **판정 프레임 100 ms 앞**에서(파일 0.1 s = 판정).
- **3타 찌르기**: 매번 `katana_thrust`, 검기를 소모하면 같은 프레임에 그 단수의 `katana_thrust_ki1~3` 겹침(아트 오버레이 `katana_thrust_ki1~3` 와 1:1). 재생 속도 변주를 쓰지 않은 이유는 차지 내려찍기와 같다(음높이가 D 단조 축을 벗어나고 가벼워짐).
- **대검 휘둘러 내리찍기(58 Q3)**: 판정 프레임에 기존 `charge_slam_lvN` + `gs_crack_line_lvN` 동시. 커서·벽 때문에 균열이 짧게 끝나면 그 시점에 균열음 80 ms 페이드아웃. 중압 갈래는 균열 대신 진동이므로 `gs_crack_line` 대신 `gs_quake_ring`. 파쇄 갈래는 `gs_crack_line` 그대로 + 탄을 지울 때마다 `gs_shatter_snuff`.
- **질풍·쌍격**: 투척 `dagger_fan_throw` 1회(3자루 함께), 적중은 기존 `hit_enemy` + `brand_apply`. 분신 교차는 `brand_burst` 와 같은 프레임에 겹침.
- **속사**: 발마다 `bow_rapid1~3` 중 직전과 다른 것 + ±3% rate. 일찍 놓기·완벽 놓기 판정은 기존 `bow_release_weak`/`bow_release_perfect` 그대로.
- **관통**: 완벽 놓기 = 기존 `bow_release_perfect`, 적을 뚫을 때마다 `bow_pierce` + `hit_enemy`.
- **표식**: 쌓일 때마다 `mark_stack`(표식 2·3 은 rate 1.06·1.12). **술 점화**: 웅덩이마다 `drunk_ignite`(연쇄는 80~150 ms 시차), 타는 동안 기존 `boss1_fire_loop` 1개(가까운 웅덩이 기준).

재사용(새로 만들지 않음):
- 대검 휘둘러 내리찍기 강타 = 기존 `charge_slam_lv1~3`(원래 휘둘러 내리찍기용으로 만든 소리, 58 Q7 '단계와 관계없이 휘둘러 내리찍기'와 일치). 균열 부분만 새로(`gs_crack_line_lv1~3`).
- 마시기 사건(독주·깡술·카운터) = 기존 `potion_use`. 술불 지속 = `boss1_fire_loop`. 표식 6 기폭 = 기존 `brand_burst`. 대쉬 일섬(58 Q1) = 기존 `issen_dash`·`issen_burst`·`shadow_clone`. 속사의 기본 사격음은 기존 `bow_shot`(0.30 s, 초당 5발에는 길어 `bow_rapid1~3` 를 새로 만듦).

현재 결정과 어긋나 보이는 기존 항목(파일·매니페스트는 그대로 둠 — 인터뷰 대상):
- `gs_plunge`·`gs_crack`: 트리거 `mode:plunge` — 58 Q11 로 꽂아내리기 코드·데이터 삭제. 쓰는 곳이 없으면 보관/삭제 결정 필요.
- `katana_echo`: 트리거 `combo:3 phase:echo` — 58 Q1 로 3타가 찌르기가 되어 잔상 베기가 남는지 불명.

### 4-2. 타격·적
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| hit_enemy | 0.15 s | `ENEMY_DAMAGED` | 2.2k 타격 + 160→60 몸통 | 0 |
| hit_enemy_crit | 0.25 s | `ENEMY_DAMAGED` crit:true | hit_enemy + 1.8k 강철 울림 | 0 |
| enemy_hurt | 0.10 s | `ENEMY_DAMAGED` (보조, 겹쳐 재생) | 1.2k→700 짧은 숨 노이즈 | -6 |
| hit_player | 0.35 s | `PLAYER_DAMAGED` | 120→38 충격 + 갑옷 쇳소리, 소프트클립 | 0 |
| enemy_death | 0.45 s | `ENEMY_DIED` | 신음 노이즈(900→350) + 몸 떨어짐 | -2 |
| charger_telegraph | 0.60 s | `ENEMY_TELEGRAPH` enemy:charger | 갑옷 덜그럭 + 가속하는 발 디딤 + 상승 저음 (`telegraphMs` 600) | -3 |
| charger_dash | 0.43 s | `ENEMY_ATTACK` enemy:charger | 무거운 바람 + 갑옷 | -2 |
| archer_shot | 0.60 s | `ENEMY_ATTACK` enemy:archer | 화승총: 4.5k 격발 + 350 Hz 폭음 + 연기 쉿 (사수 attack 2프레임에 맞춰 재생) | -1 |

### 4-3. 보스
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| boss_start | 1.60 s | `BOSS_STARTED` | 큰 북 + 420 Hz 쇠 울림 + 서늘한 고음 | 0 |
| boss_telegraph | 0.65 s | `BOSS_TELEGRAPH` attack:dash | 55→140 Hz 으르렁 + 쇠 긁힘 (`telegraphMs` 550~700) | -2 |
| boss_fan | 0.35 s | `BOSS_ATTACK` attack:fan | 투척음 3연 | -3 |
| boss_phase | 1.30 s | `BOSS_PHASE` | 낮은 북 + 불협(√2 배음) 쇳소리 부풀기 | 0 |
| boss_die | 2.20 s | `BOSS_DIED` | 160→30 추락 + 북 + 쇠 조각 5개 흩어짐 | 0 |

### 4-3-1. 1층 보스 '만취' 새 패턴 (54라운드, 18종)
결정 근거: `parts/producer/decisions/2026-10-03-round-54-boss1-patterns.md`. 기존 제작 방식(build.py 절차 합성, 44.1 kHz/16 bit/mono, 피크 -6 dBFS)을 그대로 따랐다. 목소리 금지 원칙에 따라 '크아' 숨은 성대음 없이 노이즈 포먼트(F1 820→560, F2 1250→1050, F3 2600 Hz)와 거친 진폭 떨림으로만 만든다. 새 재료 **유리(잔)·액체(술)·불**은 기존 4재료의 보조로만 쓴다. 트리거는 **제안**(시스템이 실제 이벤트·패턴 이름으로 확정).

| id | 길이 | 루프 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|---|
| boss1_drink_lift | 0.50 s | - | `BOSS_TELEGRAPH` attack:drink phase:lift | 옷 스침 + 유리잔 틱 + 잔 속 출렁 | -3 |
| boss1_drink_gulp | 2.00 s | 루프 | `BOSS_ATTACK` attack:drink phase:gulp | 0.4 s 간격 꿀꺽 5번(105→245 Hz 액체 톤 + 목 둔탁음) + 흐름 노이즈 + 거품 | -4 |
| boss1_drink_finish | 1.00 s | - | `BOSS_ATTACK` attack:drink phase:finish | '크아'(노이즈 포먼트) + 잔 내려놓는 '탁' | -2 |
| boss1_cup_shatter | 1.20 s | - | `BOSS_ATTACK` attack:drink phase:broken (약점 적중) | 깨짐 크랙 + 유리 조각 14개 + 뒤집어쓰는 첨벙 + 물방울 | 0 |
| boss1_spin_start | 2.20 s | - | `BOSS_ATTACK` attack:spin phase:start | 72→46 Hz 톱니 두 겹(3% 디튠 맥놀이), 0.5 Hz(주기 2 s, 화면 기울기와 같음) 피치·컷오프 울렁임 + 소용돌이 바람 + 희미한 2.9 kHz 이질 고음 | -2 |
| boss1_reel_telegraph | 0.30 s | - | `BOSS_TELEGRAPH` attack:reel (타당 1회) | 11 Hz 휘청이는 60→130 Hz 으르렁 + 엇박 발 끌림 2회. 최단 예고 300 ms 에 맞춤 | -2 |
| boss1_reel_dash | 0.44 s | - | `BOSS_ATTACK` attack:reel (타당 1회) | 380→1400 Hz 바람, 컷오프 7 Hz 흔들림(휘는 궤적) + 디딤 + 옷 펄럭 | -2 |
| boss1_fall | 1.10 s | - | `BOSS_ATTACK` attack:reel phase:fall | 큰 몸통 충격 + 한 번 튐 + 소품 구름 4회 + 먼지 | 0 |
| boss1_barrel_kick | 0.55 s | - | `BOSS_ATTACK` attack:barrel phase:kick | 장화 타격 + 속 빈 통 공명(230·520 Hz) + 쇠테 틱 + 출렁 | -1 |
| boss1_barrel_roll | 1.20 s | 루프 | `BOSS_ATTACK` attack:barrel phase:roll | 0.12 s 간격 덜컹 10회(0.6 s 마다 강세) + 180 Hz 굴림 + 속 술 출렁 | -6 |
| boss1_barrel_bounce | 0.50 s | - | `BOSS_ATTACK` attack:barrel phase:bounce | 돌에 부딪는 통 + 공명(210·480 Hz) + 쇠테 덜그럭 + 출렁 | -2 |
| boss1_liquor_splash | 0.70 s | - | `BOSS_ATTACK` attack:fire phase:splash | 휙 + 4k→700 Hz 첨벙 + 물방울 10개 | -3 |
| boss1_torch_throw | 0.60 s | - | `BOSS_ATTACK` attack:fire phase:throw | 9 Hz 맥동하는 불 바람(회전) + 타닥 | -3 |
| boss1_ignite | 1.10 s | - | `BOSS_ATTACK` attack:fire phase:ignite | 낮은 펑 + 200→2.5k 치솟는 불길 + 타닥 16 | -1 |
| boss1_fire_loop | 2.00 s | 루프 | `BOSS_ATTACK` attack:fire phase:burn | 일렁이는 400 Hz 불길(0.5·1.5 Hz) + 쉿 + 타닥 22 | -8 |
| boss1_candle_topple | 1.00 s | - | `BOSS_ATTACK` attack:darkness phase:topple | 쇠 촛대 쨍그랑(520 Hz) + 튐 + 불꽃 '훅' + 120→60 Hz 내려앉음 | -2 |
| boss1_candle_relight | 0.70 s | - | `BOSS_ATTACK` attack:darkness phase:relight | 촛대 틱 + 500→2.5k '화륵' + 따뜻한 저역 + 작은 타닥 | -3 |
| boss1_phase_drink | 1.80 s | - | `BOSS_PHASE` boss:1 (선택) | 잔 출렁 + 빠른 꿀꺽 3번 + 큰 '크아' + 낮은 북 | 0 |

연결 권장:
- 마시기 2 s = lift → gulp(루프, 2.0 s 한 바퀴) → finish. 약점 적중 시 gulp 즉시 정지 후 cup_shatter.
- 3연 취권: 매 돌진마다 reel_telegraph(예고 시작) → reel_dash(실행). 1·2·3타 재생 속도 1.0/1.06/1.12 로 올리면 점점 격해지는 느낌. 세 번째 뒤 fall.
- 루프 3종(gulp·barrel_roll·fire_loop)은 상태가 끝날 때 80~150 ms 페이드아웃 권장. fire_loop 는 웅덩이 여러 개여도 1개만 재생(가장 가까운 웅덩이 기준 음량) 권장.
- 촛대 여러 개가 동시에 쓰러지면 20 ms 중복 규칙에 따라 1회 재생되므로, 시차(80~150 ms)를 두면 '연쇄로 꺼지는' 느낌이 난다.
- phase_drink 는 선택: 기존 `boss_phase` 대신 쓰거나 뒤에 이어 붙인다(1층 보스 한정).

### 4-4. 획득·소모·상점
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| pickup_gold | 0.27 s | `GOLD_CHANGED` delta>0 | 2.9k·3.7k 동전 두 번 | -4 |
| pickup_potion | 0.35 s | `ITEM_PICKUP` item:potion | 유리 2.1k 울림 + 액체 블립 | -4 |
| potion_use | 0.50 s | `PLAYER_HEALED` | 뚜껑 딸깍, 꿀꺽 2회, 숨 | -3 |
| shop_buy | 0.45 s | `SHOP_PURCHASE` | 동전 3개 + 나무 좌판 두드림 | -4 |

### 4-5. 맵·월드
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| level_enter | 1.80 s | `STAGE_STARTED` | 멀리서 북, 바람, 55 Hz 드론 부풀기, 큰 리버브 | -2 |
| door_close | 0.45 s | `ROOM_ENTERED` type:trial (문 잠길 때) | 나무 문 + 쇠 걸쇠, 돌방 울림 | -1 |
| door_open | 0.70 s | `ROOM_CLEARED` | 걸쇠 풀림 + 나무 삐걱 | -3 |
| trial_clear | 0.80 s | `STORY` notice trialClear | 북 두 번 | -3 |
| boss_unlock | 1.20 s | `STORY` notice bossUnlocked ('본영 문 열림') | 쇠사슬 3회 + 무거운 울림 | 0 |
| exit_open | 1.40 s | `STORY` notice exitOpened ('오르는 길 열림') | 돌 미끄러짐 + 낮은 종 | -1 |
| save | 0.55 s | `STORY` notice saved | 깃펜 긁기 2회 | -8 |

### 4-6. UI·연출
| id | 길이 | 트리거 제안 | 질감 | gainDb |
|---|---|---|---|---|
| menu_move | 0.07 s | `UI_MENU_MOVE` | 나무 톡 | -8 |
| menu_select | 0.15 s | `UI_MENU_SELECT` | 도장 둔탁음 + 쇠 틱 | -6 |
| menu_cancel | 0.14 s | `UI_MENU_CANCEL` | 종이 넘기는 스침 | -8 |
| fate_decided | 1.30 s | `FATE_DECIDED` | 일기장 덮는 둔탁음 + 220 Hz 종 | -2 |
| evolve | 1.60 s | `WEAPON_EVOLVED` | 73→110 Hz 드론 부풀기 + 종 아르페지오(D A D A D 상승) + 바람, 큰 리버브 | -1 |
| reinforce | 0.60 s | `WEAPON_REINFORCED` | 모루 망치질 1.05k + 둔탁음 | -2 |
| player_death | 2.40 s | `RUN_ENDED` reason:death | 110→32 Hz 꺼지는 저음, 멀어지는 심장 박동 2회, 바람 | 0 |

## 5. 믹싱 기준 (매니페스트 `mixing`)
- 마스터 0 dB, SFX 버스 0 dB, BGM 버스 **-8 dB**. 보스전 중 BGM 추가 -3 dB(`bgmBossDuckDb`).
- 같은 효과음이 20 ms 안에 여러 번 요청되면 1회만 재생(산탄·난무·충격파 중복 방지).
- 동시 재생 상한 권장: 효과음 8 보이스. 넘치면 가장 오래된/작은 것을 끊는다.
- 피치 변주 권장: hit_enemy·swing_* 는 재생마다 ±4% 랜덤 피치(`detune` 또는 `rate`)로 반복감을 줄인다. 파일은 원본 하나만 둔다.

## 6. 다음 단계 (복귀 후 인터뷰 대상)
1. 톤 방향 확인: "건조·재료 중심·마법은 이질"이 맞는지, 더 멜로딕한 BGM 을 원하는지.
2. 층별 BGM 세분화(8곡) 여부. 현재는 3구간 + 보스 + 황제 + 타이틀 = 6곡.
3. ~~포맷 최종: WAV 유지(총 10 MB) vs OGG 변환~~ → **57라운드 Q17 OGG 전환 완료**(7장). 품질 수치·대체 형식은 인터뷰 확정 대기.
4. 효과음 추가 후보: 진화별 전용음(만월·잔월·파쇄 충격파·출혈 틱·추적 화살), 상점 진입, 휴식 방, 엔딩 분기 2종.
5. 외부 도구(jsfxr/sfxr, 무료 샘플)로 질감 보강할지.

## 7. 배포 형식 (57라운드 Q17 '소리 OGG 전환', 2026-10-04)

결정 근거: `parts/producer/decisions/2026-10-04-round-57-systems-review.md` Q16~Q19(용량·형식), 점검 `research-2026-10-04-optimization-audit.md` A6. 합성(소리)은 바꾸지 않았다.

| 항목 | 값 | 상태 |
|---|---|---|
| 1순위 | `.ogg` Ogg Vorbis(libvorbis), **q4**(BGM·SFX 같음) | Q17 결정(OGG) · 품질 q4 는 제안 |
| 2순위 | `.m4a` AAC-LC(ffmpeg `aac`, fast 코더, PNS 끔), **BGM 64 kbps · SFX 96 kbps** | 제안(대체 형식 자체가 인터뷰 대상) |
| 원본 | WAV 16 bit mono(SFX 44.1 kHz, BGM 22.05 kHz) → `parts/sound/work/wav/` 작업 캐시(git 제외) | `build.py` 로 바이트 재생성 확인(md5 111/111) |
| 피크 기준 | 원본 -6 dBFS 그대로. 손실 압축 뒤 피크는 OGG ≤ -5.07, M4A ≤ -4.58 dBFS(헤드룸 안) | - |

시험 인코딩(111개 전량, 스크래치에서) — 총 용량과 파형 SNR 중앙값(잡음 위주 소리는 코덱이 잡음을 비슷한 잡음으로 바꿔 SNR 이 낮게 나오므로 참고값):

| 설정 | BGM 6곡 | SFX 105개 | 비고 |
|---|---|---|---|
| WAV(원본) | 7.66 MB | 6.57 MB | - |
| OGG q3 | 0.90 MB | 0.93 MB | SNR 중앙 26.2 / 22.4 dB |
| **OGG q4** | **0.97 MB** | **0.99 MB** | SNR 중앙 27.7 / 22.9 dB, 피크 최대 -5.81 / -5.07 dBFS |
| OGG q5 | 1.10 MB | 1.09 MB | SNR 중앙 29.1 / 24.7 dB, SFX 피크 최대 -4.31 |
| OGG q6 | 1.23 MB | 1.20 MB | SNR 중앙 31.0 / 27.0 dB |
| **M4A 64k / 96k (fast)** | **1.43 MB** | **0.99 MB** | SFX 피크 최대 -4.58, 1개만 -5 dBFS 초과 |
| M4A 기본 twoloop 코더 | 1.50 MB | 1.02 MB | 저역 과도에서 피크 +5.7 dB 튐(guard_push -0.29 dBFS) — 채택 안 함 |
| MP3 V4(LAME) | 1.25 MB | 0.77 MB | 대체 후보. 길이·이음매 양호(ffmpeg 기준)지만 Safari 의 LAME 지연 정보 처리 불확실 |

이음매·길이 규칙(`encode.py`):
- **OGG**: 마지막 페이지 granule = 원본 샘플 수 → 디코드 길이가 샘플 정확(libvorbisfile·ffmpeg 둘 다 차 0). ffmpeg 6.1 디코더는 한 페이지에 다 들어가는 짧은 파일의 끝을 잘못 자른다(-128 또는 +수백 샘플) — SFX 는 페이지를 50 ms 로 나눠 해결(용량 +약 1.5%). BGM 은 기본 1 s 페이지로 이미 정확.
- **M4A**: 무비 timescale 을 샘플레이트로 두어 edit list 표시 길이 = 샘플 수(기본 1 ms 단위면 boss 가 약 9 샘플 길어진다). 루프 13종은 [끝 2048 | 루프 N | 앞 2048] 로 인코딩한 뒤 edit list mediaTime 을 +2048 → AAC 첫 프레임(프라이밍) 열화가 이음매에 오지 않는다(패딩 없이 하면 첫 1024 샘플 SNR 이 7~15 dB 로 떨어짐). ffmpeg 6.1 은 edit list 끝 자르기를 무시해 끝 패딩(4~1009 샘플)이 남는다 → 매니페스트 `loopEndSample` 로 루프 끝을 지정하도록 권장.
- 결정적: `-fflags +bitexact`. 같은 ffmpeg/libvorbis 버전이면 재인코딩 결과 바이트 동일(확인함).

루프 검증 지표(`build.py verify` '이음매' 열): 튐 비율 = 디코드 결과의 이음매 한 칸 변화 ÷ 같은 파일 안쪽 인접 샘플 변화의 99.9 백분위(≤ 1 이면 이음매가 파일 안 평범한 한 칸보다 작다 = 클릭 없음), 괄호는 원본 대비 이음매 오차(dBFS, 참고값).

