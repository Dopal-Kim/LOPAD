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

형식: 44.1 kHz / 16 bit / mono / 피크 -6 dBFS. `gainDb` 는 SFX 버스 기준 권장 상대 음량. 트리거는 **제안**이며 시스템 파트가 실제 이벤트 이름으로 확정한다(`ui-system-interface.md` 에 이미 있는 이름은 그대로 썼다).

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
3. 포맷 최종: WAV 유지(총 10 MB) vs OGG 변환(ffmpeg 있음, 약 1/8 용량). 웹 배포라면 OGG 권장.
4. 효과음 추가 후보: 진화별 전용음(만월·잔월·파쇄 충격파·출혈 틱·추적 화살), 상점 진입, 휴식 방, 엔딩 분기 2종.
5. 외부 도구(jsfxr/sfxr, 무료 샘플)로 질감 보강할지.
