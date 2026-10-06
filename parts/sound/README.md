# 음향 파트 README

## 산출물
| 경로 | 내용 |
|---|---|
| `parts/sound/sound-design.md` | 음향 바이블: 톤, 악기(합성 방식), 층별 BGM 매핑, 효과음 표(트리거 제안) |
| `parts/sound/work/build.py` | **단일 소스.** 효과음·BGM 합성 → OGG·M4A 인코딩 → 매니페스트 → 검증을 전부 재생성. 합성은 파이썬 표준 라이브러리만, 고정 시드로 결정적 |
| `parts/sound/work/sfx_bundle2.py` · `sfx_branch2.py` · `sfx_passive.py` | 60라운드 효과음 정의(2차 묶음 25 · 2단 갈래 32 · 패시브 10). `build.py` 가 이 순서로 import 해 등록한다(시드 = 등록 순서) |
| `parts/sound/work/sfx_core61.py` | 61라운드 P11 핵심 20종 품질 패스(같은 키 18종을 `redo()` 로 다시 등록 — 순서·시드 유지) + 새 2종(`guard_block`·`combo_finish`) + 변주 23 |
| `parts/sound/work/sfx_stage61.py` | 61라운드 단계 2·3: 신규 적 2종(독주 행상·술통 짐꾼) 12 · 보스 '만취' 패스(새 11 + `redo()` 다시 9 + 보관 1) · 칼 발도 검기 단수 5 · 가드(다시 2 + 새 1). 6절 = 단계 4(보스 `BOSS_ACTION` 새 동작 6 + 변주 2 · 화살비 다시 2, round `61-4`), 7절 = P12 무기 성장(새 8 + 변주 2 · 옛 6 트리거 이동), 8절 = P13(새 5 + 변주 2 · `boss1_break_pillar` 다시, round `61-5`), 9절 = P13 개성 발동음 15 + 공명 2(round `61-5`). 61-5 까지의 마지막 모듈(1,700줄을 넘어 61-6 부터 새 모듈로 나눔) |
| `parts/sound/work/sfx_p14.py` | 61라운드 단계 6 (P14): 그림 속 입구 전환 3(`transition_enter`·`_exit`·`_floor`) · 수련장 과제 종 `training_task`(+ 변주 2) · 방 도장 `training_stamp`, round `61-6`. **마지막 모듈 — 새 효과음은 이 파일 끝에만** |
| `parts/sound/work/bgm_training.py` | 61라운드 단계 6 (P14) 수련장 곡 `training`(72 s, 44.1 kHz 스테레오) — `bgm_floor1` 의 악기·버스 재사용, manifest `bgmByState.training`. 1층 곡 뒤에 등록 |
| `parts/sound/work/bgm_floor1.py` | 61라운드 P11 1층 전용 BGM 5파일(벽 밖 · 잔 거리 · 만취 3국면), 44.1 kHz 스테레오. 기존 6곡 뒤에 등록 |
| `parts/sound/work/mixing.py` | 61라운드 믹싱 권장값(동시 재생 상한·우선순위·덕킹·변주·리미터·보스 국면 교차) → manifest `mixing`, 항목별 `priority` |
| `parts/sound/work/listen_index.py` → `listen_index.json` | 청취 검수(들어보기) 페이지용 목록: 전 효과음·BGM 의 분류·한 줄 설명·트리거·길이·루프·ogg/m4a 경로. 매니페스트를 쓸 때마다 함께 재생성 |
| `parts/sound/work/encode.py` | 배포 형식 인코딩·검증(57라운드 Q17). ffmpeg(libvorbis·aac), bitexact 로 결정적 |
| `parts/sound/work/wav/{sfx,bgm}/*.wav` | 합성 원본 **작업 캐시**(git 제외, `work/.gitignore`). `build.py` 로 바이트 단위 재생성 — 저장소·빌드 결과에 넣지 않는다 |
| `assets/audio/sfx/*.{ogg,m4a}` | 효과음 **312종**(61라운드 단계 6 P14: 전환 3 + 수련장 2 + 변주 2 — 아래 '61-6' 절. 그 전 305종 = 61라운드 단계 5 P13 개성: 행동 갈래 `trait_<act>` 15 + `resonance_on`·`resonance_proc` — 아래 '61-5 개성' 절. 그 전 288종 = 61라운드 단계 5 P13: 새 5 + 변주 2 · `boss1_break_pillar` 다시 — 아래 61-5 절. 그 전 281종 = 61라운드 단계 4: P12 무기 성장 새 8 + 변주 2 · 보스 `BOSS_ACTION` 새 6 + 변주 2, 화살비 다시 2 — 아래 61-4 절들. 그 전 263종 = 61라운드 단계 2·3: 새 29 + 다시 11 + `boss1_cup_shatter` 보관 — 아래 61-2 절. 그 전 234종 = 61라운드: 핵심 18종 다시 만듦 + 새 2 + 변주 23. 그 전 209종 = 29라운드 42 + 54라운드 1층 보스 '만취' `boss1_*` 18 + 55라운드 대검 차지·칼 잔상 9 + 56라운드 가드·자원·무기 새 수단 34 + 56라운드 검수 활 2 + 57·58라운드 빌드 축·갈래 1단·찌르기·균열·상태 37 + 60라운드 2차 묶음 25·2단 갈래 32·패시브 10 — 그중 `gs_plunge`·`gs_crack`·`katana_echo` 는 보관), 원본 44.1 kHz / mono / 피크 -6 dBFS |
| `assets/audio/bgm/*.{ogg,m4a}` | BGM **12파일**(61-6 수련장 `training` 72 s 44.1 kHz 스테레오 추가): 기존 6곡(22.05 kHz / mono, 27~32 s 루프) + 61라운드 1층 전용 5파일(`f1_outside`·`f1_jan` 96 s, `f1_boss_p1~3` 72 s — 44.1 kHz / **stereo**). 피크 -6 dBFS(보스 p1·p2 는 공통 이득이라 더 낮음) |
| `assets/audio/manifest.json` | 시스템 파트가 읽을 목록(계약 초안): 파일(`file` 1순위 + `files` 형식별)·샘플 수·길이·루프 구간·권장 음량·트리거 이벤트 제안·층별 BGM 매핑 |

## 사용법
```
python3 parts/sound/work/build.py            # 전부: 합성 → 인코딩 → 매니페스트 → 검증 표 (약 7분 — 61라운드 1층 스테레오 BGM 이 대부분, 3 프로세스 병렬)
python3 parts/sound/work/build.py sfx        # 효과음만 (+인코딩·매니페스트)
python3 parts/sound/work/build.py bgm        # BGM 만 (+인코딩·매니페스트)
python3 parts/sound/work/build.py sfx parry  # 특정 소리만
python3 parts/sound/work/build.py encode     # 작업 캐시 WAV → OGG·M4A 만 다시 (+매니페스트)
python3 parts/sound/work/build.py verify     # 검증(WAV 피크·클리핑·경계 + OGG·M4A 디코드 길이·정렬·피크·루프 이음매·용량)
python3 parts/sound/work/build.py listen     # 들어보기 목록(listen_index.json)만 다시
```
새로 받은 저장소에는 WAV 캐시가 없으므로 `encode`·`manifest`·`verify` 전에 `build.py`(전부)를 한 번 돌린다.
새 효과음은 `@sfx('이름', '트리거', '설명', gainDb)` 데코레이터 함수 하나를 **마지막 모듈(61-6 부터 `sfx_p14.py`) 끝**에 추가하면 매니페스트·들어보기 목록까지 자동 반영된다(`build.py` 본문 중간이나 앞 모듈에 끼우면 시드가 밀려 뒤 소리가 바뀐다). 새 소리의 분류는 `listen_index.py` 의 `EXPLICIT`/`SUBGROUP` 에 적는다(60라운드 모듈 소리는 모듈 이름으로 자동). BGM 은 `@bgm(...)`.

## 자율 결정 (29라운드, 도영 님 부재 중 권장안으로 결정 — 복귀 후 검토)
음향 파트 개시 BLANK(`parts/sound/CLAUDE.md`, GDD 8장) 네 항목을 아래와 같이 정했다. 근거는 `parts/producer/decisions/2026-10-01-round-29-autonomous-demo.md` 의 자율 진행 지시.

| # | 항목 | 결정 | 대안(검토용) | 이유 |
|---|---|---|---|---|
| S1 | 제작 도구 | **파이썬 표준 라이브러리 절차 합성**(`wave/array/math/random`), 외부 라이브러리·다운로드·샘플 없음. RBJ 바이쿼드·Karplus-Strong·Schroeder 리버브 직접 구현 | jsfxr/sfxr 계열, 무료 샘플(CC0), 외부 스킬 | 네트워크 금지 조건, 재현성(단일 스크립트), 라이선스 문제 없음 |
| S2 | BGM 곡 수·분위기 | **6곡**: title / floor_low(1~2층) / floor_mid(3~5층) / floor_high(6~8층) / boss(1~7층) / emperor(8층 보스). 층 구간은 스토리 바이블의 외곽→전선·군부→귀족·수도 구분을 따름 | 층별 8곡, 혹은 보스별 곡 | 데모 범위. 3구간은 세계관의 분위기 경계와 일치하고 재사용이 쉽다 |
| S3 | 효과음 목록 | 지시받은 29종 + 보강 13종 = **42종** (bow_draw, hit_enemy_crit, enemy_hurt, charger_dash, boss_start, boss_telegraph, boss_fan, boss_die, shop_buy, trial_clear, fate_decided, menu_cancel, save). 보강분은 `data/weapons·enemies·bosses.json` 의 행동(조준 차지, 치명, 보스 돌진 예고·부채꼴, 구매, 저장)에 대응 | 29종만 | 데이터에 있는 행동에 소리가 비면 데모에서 바로 티가 난다. 전부 짧고 용량 작음 |
| S4 | 파일 포맷 | ~~WAV PCM 16 bit mono~~ → **57라운드 Q17: 배포 = Ogg Vorbis + M4A(AAC) 대체**, 합성 원본 WAV(SFX 44.1 kHz, BGM 22.05 kHz, 16 bit mono)는 작업 캐시. 아래 '추가 (57라운드 Q17)' | OGG(ffmpeg 변환, ~1/8), SFX 도 22.05 kHz | 브라우저 호환·무손실·검증 용이. 배포 시 OGG 변환은 한 줄로 가능 |
| S5 | 라우드니스 기준 | 피크 **-6 dBFS** 정규화(전 파일). BGM 은 매니페스트 `gainDb` 로 RMS ≈ -21 dBFS 로 보정. 버스: SFX 0 dB, BGM -8 dB, 보스전 BGM 추가 -3 dB | LUFS 기준 측정 | 표준 라이브러리만으로 측정 가능한 지표. 헤드룸 6 dB 로 믹스 시 클리핑 여유 |
| S6 | 루프 규격 | BGM 은 박자 격자에 맞춘 정수 마디 길이(96/100/140/60 BPM), 랩어라운드 렌더 + 필터·리버브 상태 연속화로 경계 클릭 제거. `guard_hold` 는 0.6 s 루프 | 인트로+루프 2파일 | 데모에서 단일 파일 루프가 가장 다루기 쉽다 |
| S7 | 톤 | "화약·강철·목재·돌" 재료 중심, 드라이. 마법적 질감은 개성 변화·그림자 걸음에만. 주인공 목소리 없음(스토리 톤: 말이 없는 망령) | 더 판타지한 질감, 보컬 포함 | 스토리 바이블(현실 밀착, 마법은 희귀한 이질) |
| S8 | 트리거 이름 | `ui-system-interface.md` 에 있는 이벤트(`PLAYER_DAMAGED, PLAYER_HEALED, GOLD_CHANGED, WEAPON_EVOLVED, BOSS_STARTED/PHASE/DIED, STAGE_STARTED, ROOM_ENTERED, FATE_DECIDED, RUN_ENDED, STORY`)는 그대로 쓰고, 없는 것은 **제안** 이름(`PLAYER_ATTACK, PLAYER_SECONDARY, PLAYER_DASH, PARRY_SUCCESS, ENEMY_DAMAGED, ENEMY_DIED, ENEMY_TELEGRAPH, ENEMY_ATTACK, BOSS_TELEGRAPH, BOSS_ATTACK, ROOM_CLEARED, ITEM_PICKUP, SHOP_PURCHASE, WEAPON_REINFORCED, UI_MENU_MOVE/SELECT/CANCEL`). 시스템 파트가 확정하면 매니페스트만 고친다 | — | 계약 초안이지 확정이 아님 |
| S9 | 매니페스트 위치·형식 | `assets/audio/manifest.json` (아트 계약의 `manifest.json` 관례를 따름). `entries[]` + `bgmByFloor` + `bgmByState` + `mixing` | `parts/producer/contracts/` 에 계약 문서 | 쓰기 권한이 음향 소유 경로에만 있음. 승인되면 프로듀서가 `contracts/sound-assets.md` 로 승격 |

## 검증 (2026-10-01, `build.py verify`)
- 파일 48개(SFX 42 + BGM 6), 총 **10.04 MB**, 클리핑 0, 전 파일 피크 -6.00 dBFS.
- 루프 파일 경계차는 모두 파일 내 최대 인접 샘플차 이하(비율 ≤ 0.29) — 클릭 없음.
- 표 전체는 `python3 parts/sound/work/build.py verify` 로 재출력.

## 추가 (54라운드, 2026-10-03)
- 1층 보스 '만취' 새 패턴 효과음 18종(`boss1_*`, 루프 3종 포함). 목록·연결 권장은 `sound-design.md` 4-3-1.
- 기존 방식 그대로(새 도구·형식 결정 없음). 시드가 SFX 등록 순서라 새 항목은 **반드시 목록 맨 뒤**에 추가 — 기존 42종 파일은 바이트 단위로 변하지 않았다.
- 검증: 파일 66개(SFX 60 + BGM 6), 총 11.63 MB, 클리핑 0, 전 파일 피크 -6.00 dBFS, 새 루프 경계비 ≤ 0.15.

## 추가 (55라운드, 2026-10-04)
- 대검 홀드 차지 8종(`charge_start`, `charge_stage1~3`, `charge_loop` 루프, `charge_slam_lv1~3`) + 칼 3타 잔상 베기 `katana_echo`. 목록·연결 권장은 `sound-design.md` 4-1-1.
- 기존 방식 그대로, 새 항목은 목록 맨 뒤 — 기존 66개 파일(SFX 60 + BGM 6) 바이트 불변(md5 대조).
- 검증: 파일 75개(SFX 69 + BGM 6), 총 12.22 MB, 클리핑 0, 전 파일 피크 -6.00 dBFS, `charge_loop` 경계비 0.23.

## 추가 (56라운드, 2026-10-04)
- 가드·자원 11종(`perfect_guard`, `parry_perfect`, `groggy_start`, `kenki_stage1~3`, `utbun_full`, `brand_apply`, `brand_burst`, `overheat_burst`, `breath_focus`) + 칼 6 + 대검 8 + 단검 5(`dagger_backstab`, `dagger_flurry1~4`) + 활 4 = 34종. 목록·연결 권장은 `sound-design.md` 4-1-2.
- 재사용: `bow_draw`(같은 키 기존 파일), 일반 발사 `bow_aimed`, 도약 찍기 차지분 `charge_slam_lv1~3`.
- 기존 방식 그대로, 새 항목은 목록 맨 뒤 — 기존 75개 파일 바이트 불변(md5 대조), 매니페스트는 항목 추가만.
- 검증: 파일 109개(SFX 103 + BGM 6), 총 14.14 MB, 클리핑 0, 전 파일 피크 -6.00 dBFS, `katana_iai_hold` 경계비 0.10.

## 추가 (56라운드 검수 Q44~Q47, 2026-10-04)
- 새 2종: 활 가득 당김 알림 `bow_full_draw`(0.15 s) + 오래 쥐어 흔들릴 때 시위 떨림 루프 `bow_strain`(1.00 s, 경계비 0.05). `arrow_rain_impact` 뒤에 등록.
- 문서·메타만: `gs_drag` 3타만(트리거 `combo:3`), `parry`+`parry_perfect` 겹침·`bow_draw` 유지·울분 가득 1회·`gs_` 이름 유지 '결정됨' 표시(`sound-design.md` 4-1-2).
- 기존 109개 파일 바이트 불변(md5 대조), 매니페스트는 2항목 추가 + `gs_drag`·`utbun_full` 의 trigger/note 갱신.
- 검증: 파일 111개(SFX 105 + BGM 6), 총 14.24 MB, 클리핑 0, 전 파일 피크 -6.00 dBFS.

## 추가 (57라운드 Q17 '소리 OGG 전환', 2026-10-04)
근거: `parts/producer/decisions/2026-10-04-round-57-systems-review.md` Q16~Q19(용량·형식 '소리 OGG 전환'), 점검 `research-2026-10-04-optimization-audit.md` A6. 소리 자체(합성)는 바꾸지 않았다 — 캐시 WAV 111개가 이전 `assets/audio/*.wav` 와 md5 동일.

- **배포 형식**: 1순위 `.ogg`(Ogg Vorbis), 2순위 `.m4a`(AAC-LC, Ogg 를 못 여는 Safari 대비). 품질은 시험 인코딩 기준 **제안값**(확정은 인터뷰): OGG q4(BGM·SFX), M4A BGM 64 kbps·SFX 96 kbps(ffmpeg `aac` fast 코더, PNS 끔). 자세한 근거는 `sound-design.md` 7장.
- **WAV 원본**: `build.py` 가 바이트 단위로 재생성(md5 111/111 일치, 약 45초)하므로 `assets/audio/` 에서 지우고 `parts/sound/work/wav/`(git 제외 작업 캐시)로 옮겼다. 빌드 결과(`dist`)에 WAV 가 더는 들어가지 않는다.
- **이음매·길이**: OGG 는 마지막 granule = 원본 샘플 수(참조 디코더 libvorbisfile·ffmpeg 둘 다 길이 차 0). ffmpeg 6.1 디코더가 한 페이지짜리 짧은 파일 끝을 잘못 자르는 문제는 SFX 페이지를 50 ms 로 나눠 피했다. M4A 는 무비 timescale = 샘플레이트로 edit list 길이를 샘플 정확하게 쓰고, 루프 13종은 앞뒤에 반대쪽 끝 2048 샘플을 이어 인코딩한 뒤 edit list 로 잘라 AAC 첫 프레임 열화가 이음매에 오지 않게 했다.
- **매니페스트**: `file` 은 1순위(.ogg) 경로 그대로 의미 유지, `files`(형식별 선호 순서)·`samples`·루프 항목의 `loopStartSample`/`loopEndSample` 추가, `format` 에 코덱·대체 형식·인코딩 설정·원본 위치 추가. 항목 순서·id·트리거·음량은 그대로.
- **용량**: WAV 14.24 MB → OGG 1.96 MB(13.8%) + M4A 2.41 MB = 배포 4.37 MB. 브라우저 한 곳은 한 형식만 받는다(OGG 1.96 MB / M4A 2.41 MB).
- **검증**(`build.py verify`, 111개 문제 0): WAV 피크 -6.00 dBFS·클리핑 0. OGG 길이 차 0(ffmpeg/libvorbisfile), 피크 -7.19~-5.07 dBFS, 클리핑 0. M4A edit list 길이 = 샘플 수, 앞 정렬 0, 피크 SFX 최대 -4.58·BGM 최대 -5.99 dBFS, 클리핑 0. 루프 13종 이음매 튐 비율 OGG ≤ 0.34, M4A ≤ 0.90(≤ 1 통과).
- 실제 청취(특히 Safari 에서 M4A 루프)는 컨테이너에서 못 했다 — 수치 검증만.

## 추가 (57라운드 Q39 · 58라운드, 2026-10-04)
- 새 37종: 세트 3(`set_tier1~3`) · 이중 개성 `dual_trait` · 저주 `curse_take`·`curse_end` · 피의 계약 `blood_pact` · 완벽 회피 `perfect_evade` · 각성 4(`awaken_katana/greatsword/dagger/bow`, 공용 뼈대 + 무기 서명) · 칼 회전 베기 `katana_spin_ready`·`katana_spin` · 가드 불가 내려베기 `katana_guardbreak_hold`(루프)·`katana_guardbreak` · 3타 찌르기 `katana_thrust` + 검기 겹침 `katana_thrust_ki1~3` · 대검 균열 `gs_crack_line_lv1~3` · 중압 `gs_quake_ring` · 파쇄 탄 소멸 `gs_shatter_snuff` · 단검 `dagger_fan_throw`·`dagger_cross_clone` · 활 `bow_rapid1~3`·`bow_pierce` · 상태 `mark_stack`·`boil_burst`·`stillness`·`drunk_ignite`·`drunk_sway`·`endure_trigger`. 목록·연결 권장·재사용은 `sound-design.md` 4-1-3.
- 재사용: 휘둘러 내리찍기 강타 `charge_slam_lv1~3`, 마시기 `potion_use`, 술불 지속 `boss1_fire_loop`, 표식 기폭 `brand_burst`, 대쉬 일섬 `issen_*`·`shadow_clone`.
- 기존 방식 그대로, `bow_strain` 뒤에 등록 — 기존 111개 파일(WAV 캐시·OGG·M4A) 바이트 불변(md5 대조), 매니페스트는 37항목 추가만(기존 항목·최상위 필드 동일). 전체 `build.py sfx` 재실행으로 142개 WAV·배포 파일 바이트 재현 확인.
- 검증(`build.py verify`, 148개 문제 0): WAV 피크 -6.00 dBFS·클리핑 0, OGG 길이 차 0, 새 루프 `katana_guardbreak_hold` 이음매 튐 비율 OGG 0.63·M4A 0.78(처음 만든 판은 M4A 1.56 이라 톱니 고역을 줄이고 험 위상을 옮겨 고침). 총 WAV 17.09 MB → 배포 5.20 MB(OGG 2.37 MB / M4A 2.84 MB).
- 새 트리거 이벤트(제안, 시스템 확정 필요): `MARK_CHANGED`·`STATUS_BURST`·`SET_EFFECT`·`POOL_IGNITED`·`DRUNK_SWAY`·`ENDURE_TRIGGERED`, 조건 키 `kind:awaken`·`move:spin|guardbreak|fan_throw|cross_clone|rapid|pierce|crack`·`kenki`·`part:crack|quake`·`branch:pressure`·`source:bloodPact`. 계약 `sound-assets.md` §5 루프 목록(8개로)·§6 이벤트 목록 갱신은 프로듀서 소관.

## 추가 (60라운드 Q5~Q7, 2026-10-05)
근거: `parts/producer/decisions/2026-10-05-round-60-parallel-production.md` Q5(37종 구성 유지)·Q6(`gs_plunge`·`gs_crack`·`katana_echo` 보관)·Q7(다음 범위: 2차 묶음 효과음 + 2단 갈래 16종 효과음 + 패시브별 소리 + 청취 검수 페이지).
- **새 67종**: 2차 묶음 25(엘리트 공용 등장 + 접두어 4 + 처치 · 도전 성소 발동·성공·실패 · 성과 등급 완·양 · 상점 리롤 · 지도 정보 구매 · 소모품 3종(화염 술병 투척·착탄 / 깡술 / 냉수) · 이벤트 진입·선택 · 숨은 노드 발견 · 파훼 다양성·결정타 · 증류 화로 통과·불 무기 루프·꺼짐) + 2단 갈래 16종 32파일(아트 fx JSON 의 프레임 시간·spawnAtMs·burstAtMs 에 맞춤) + 패시브 9종 10파일. 목록·연결 권장·패시브 고른 이유는 `sound-design.md` 4-7.
- **새 루프 5**: `fire_weapon_loop`(1.0 s) · `katana_whirl_loop`(0.96 s = 240 ms × 4) · `gs_congest_loop`(0.75 s) · `dagger_hotwind_loop`(1.12 s = 280 ms × 4) · `bow_deadeye_hold`(0.72 s = 360 ms × 2). 루프 효과음 8 → 13(계약 §5 목록 갱신은 프로듀서 소관).
- **코드 정리(CLAUDE.md 6-1)**: `build.py`(3,200줄)에 더 붙이지 않고 모듈 3개로 분리 + 들어보기 목록 생성기 `listen_index.py`. `build.py` 는 `sys.modules['build']` 를 먼저 걸어 모듈이 같은 DSP 유틸·SFX 표를 쓰게 했다.
- **보관 3종**: 오디오·매니페스트 항목 그대로, `note` 앞에 '[보관 — 60라운드 Q6 …]' 표시만(바이트 불변). 들어보기 목록에서는 `status: archived`.
- 기존 148개(WAV 캐시·OGG·M4A) 바이트 불변(md5 대조), 매니페스트는 67항목 추가 + 보관 3종 note 표시만(최상위 필드 동일). 전체 `build.py` 재실행으로 215개 WAV·OGG·M4A·manifest·listen_index 바이트 재현 확인.
- **검증**(`build.py verify`, 215개 문제 0): WAV 피크 -6.00 dBFS·클리핑 0, OGG 길이 차 0. 새 루프 이음매 튐 비율 OGG ≤ 0.40 · M4A ≤ 0.34(`fire_weapon_loop` 0.23/0.34, `katana_whirl_loop` 0.01/0.02, `gs_congest_loop` 0.40/0.04, `dagger_hotwind_loop` 0.01/0.31, `bow_deadeye_hold` 0.22/0.19). 총 WAV 21.95 MB → 배포 6.60 MB(OGG 3.05 MB / M4A 3.55 MB).
- **새 트리거(제안, 시스템 확정 필요)**: 이벤트 `ELITE_SPAWNED`·`ELITE_PREFIX`·`CONSUMABLE_IMPACT`·`BOSS_BREAK`·`STATUS_CHANGED`·`BRANCH_EFFECT`·`PASSIVE_PROC`, 기존 이벤트의 새 조건 키 `elite:true`·`prefix:`·`group:reroll|mapInfo`·`id:fireBottle|strongDrink|coldWater`·`type:event`·`menu:event`·`kind:warFlag`·`outcome:fail`·`grade:`·`kind:still`·`finisher:true`·`branch:<갈래 id>`·`stage:4|5`·`move:whirl`·`phase:reflect|cleave|fork`·`target:knife`·`over50`·`moving`. 계약 §6 갱신은 프로듀서 소관.
- 들어보기 목록 `parts/sound/work/listen_index.json`: 215항목(효과음 209 + BGM 6), 18분류. 메인 세션이 청취 검수 페이지를 만든다.

## 추가 (60라운드 Q22 청취 검수 1차 수정, 2026-10-05)
도영 님 메모 8건 반영(원문은 결정 파일). 기존 함수만 다시 써서 다른 소리는 바이트 불변(md5 대조, 바뀐 것은 아래 7개 WAV·OGG·M4A뿐), `build.py verify` 215개 문제 0.
- `charge_stage1~3`: 종·징 제거 → 기를 모음(빨려드는 공기 + 차오르는 압력 55→70 Hz) → 힘을 다해 모음(9 Hz 떨림 60→95 Hz + 쇠 끼익 + 땅 떨림) → 다 짜내 타이밍 알림(0 s 단단한 '척' + '파앗' → 12 Hz 끓어 넘침).
- `kenki_stage1~3`: 칼날 울림 제거 → 지글지글(지짐 + 잔 타닥) → 타오름(불 붙는 '훅' + 치솟는 불길) → 빛남(번쩍 오르는 고역 + 일렁이는 반짝임).
- `hit_player`: 프라이팬 같던 900 Hz 금속 울림 제거 → 몸통 충격 + 가죽·천 '퍽' + 뼈 저음 + 숨 밀림.
- `dash`: **파일은 그대로, manifest `gainDb` -3 → -5 dB**.
- ~~확인 필요(바꾸지 않음): `charge_stage4`·`kenki_stage4`·`kenki_stage5` 가 새 흐름과 어긋남~~ → 60라운드 Q25 로 다시 만듦(아래 절).

## 추가 (60라운드 Q25 4·5단 재제작, 2026-10-05)
도영 님 결정 Q25: 고친 1~3단과 같은 방향으로. `sfx_branch2.py` 의 세 함수만 다시 썼다(`jing` 을 쓰는 다른 소리는 그대로). 바뀐 파일은 이 3종의 WAV·OGG·M4A 9개뿐이고 나머지는 md5 불변이다. manifest 는 이 3항목의 `note`·`samples`·`durationMs` 만 바뀌었고 `build.py verify` 215개 문제 0.
- `charge_stage4`(1.54 s): 징을 빼고 3단 '척'을 더 무겁게 했다. 0 s 낮은 '척' + 쿵 두 겹(0 s · 0.09 s) + 위로 터지는 공기 → 땅이 갈라지는 저음(낮은 균열 0.3 s + 자갈) + 15 Hz 로 떨리는 압력·땅 떨림.
- `kenki_stage4`(1.29 s): 칼날 울림을 뺐다. 3단 '빛남'(`_kenki(3)`) 위에 불꽃이 맺히는 지속 고역 반짝임(8.2k·10.5k) + 1.6 Hz 로 숨 쉬듯 맥동 + 불꽃 알갱이.
- `kenki_stage5`(1.19 s): 칼날 울림을 뺐다. 빛이 고리로 이어지는 반짝임 다섯(0.12 s 부터 70 ms 간격 = 기존 초승달 다섯 타이밍, 점점 높게) → 0.47 s 짧은 백열 '화악' + 타닥.

## 추가 (시스템 효과음 연결 — 트리거 이름 맞춤, 2026-10-05)
시스템이 확정한 id·이벤트 이름(메인 세션 전달, 계약 `sound-assets.md` §6)으로 manifest `trigger` 32항목을 기계적으로 고쳤다. 오디오·다른 필드는 그대로(WAV·OGG·M4A 645개 md5 불변, `build.py verify` 215개 문제 0).
- 패시브 `brokenGlass`→`brokenShard`, `strongBreath`→`harshBreath` · 접두어 `drinker`→`guzzler`, `leader`→`ringleader` · 갈래 `moon`→`zangetsu`, `mirror`→`meikyo`, `echo`→`resonance`, `congest`→`clot`, `frenzy`→`dance`, `hotwind`→`heatwave`, `split`→`volley`, `pressure`→`giant`, `bleed`→`twinBrand`.
- 이벤트: `event_enter` → `EVENT_NODE_ENTERED`, `break_finisher` → `BOSS_BREAK{kind:finisher}`, `still_ignite` → `STRUCTURE_FIRE`(target weapon·arrow 둘 다라 조건 없음), `kenki_stage1~5` → `WEAPON_GAUGE{stage:N,delta>0}`, `katana_thrust_ki1~3` 조건 `kenki:` → `kenkiStage:`, `potion_use` → `PLAYER_HEALED{source:potion}`.
- 갈래 조건이던 GROGGY·OVERHEAT·BREATH_FOCUS 6항목 → `BRANCH_EFFECT`. effect 값은 음향 임시(시스템 확인 필요): `gs_congest_loop` hold · `gs_congest_burst` burst · `dagger_hotwind_loop` trail · `dagger_hotwind_burst` burst · `bow_deadeye_lock` lock · `bow_deadeye_hold` hold.
- `sound-design.md` 표의 트리거 칸도 같이 맞췄다.

## 추가 (시스템 실제 이벤트 이름 2차 맞춤, 2026-10-05)
시스템이 확정한 실제 이벤트·페이로드(메인 세션 전달)로 manifest `trigger` **22항목**을 기계적으로 고쳤다. 오디오 불변(WAV·OGG·M4A 645개 md5 동일), `build.py verify` 215개 문제 0, `listen_index.json` 재생성.
- 게이지 `WEAPON_GAUGE{weapon,gauge:kenki|grudge|brand|breath,event:stage|full|consume|apply|focusStart|focusEnd,stage?,delta?,marks?,back?}`: `kenki_stage1~5` → `gauge:kenki,event:stage,stage:N`(오를 때만 — `delta>0` 조건 뺌), `utbun_full` → `gauge:grudge,event:full`, `brand_apply` → `gauge:brand,event:apply`(등 뒤 = `back`), `breath_focus` → `gauge:breath,event:focusStart`. `groggy_start` → `WEAPON_RESOURCE{event:groggy}`.
- 폭발: `overheat_burst` → `PLAYER_SKILL{weapon:dagger,move:overheat,phase:burst}`, `brand_burst` → `PLAYER_SKILL{weapon:dagger,move:brand,phase:burst}`, `dagger_hotwind_burst` → 같은 과열 폭발 + `branch:heatwave`.
- 갈래: `gs_quake_fork` → `BRANCH_EFFECT{quake,fork}`, `gs_quake_ring` → `{giant,ring}`, `dagger_knife_step` → `{flyknife,step}`, `katana_mirror_parry` → `{meikyo,parry}`, `gs_echo_counter` → `{resonance,counter}`, `dagger_bleed` → `{bleed,bleed}`, `bow_arrow_split` → `{volley,split}`, `katana_guardbreak_hold` → `PLAYER_BRANCH_MOVE{move:unblockable,phase:hold}`.
- 루프 시작·멈춤: `dagger_hotwind_loop` → `effect:trail_start`(멈춤 `trail_end`), `bow_deadeye_hold` → `effect:hold_start`(멈춤 `hold_end`), `gs_congest_loop` 트리거 그대로(멈춤 `effect:end|burst`). manifest 트리거는 한 개라 멈춤 이벤트는 해당 `note` 끝에 적었다(`brand_apply` note 에 `back:true` 표기도 추가).
- `sound-design.md` 표 트리거 칸도 맞췄다.

## 추가 (60라운드 Q40 — 중압 진동·거인 4단 트리거 맞춤, 2026-10-05)
근거: `parts/producer/decisions/2026-10-05-round-60-parallel-production.md` Q40·Q40 보충, 시스템 c96a1f7. manifest `trigger`·`note` **9항목**을 기계적으로 고쳤다. 오디오 불변(WAV·OGG·M4A 645개 md5 동일), `build.py verify` 215개 문제 0, `listen_index.json` 재생성.
- `gs_quake_ring` → `BRANCH_EFFECT{branch:weight,effect:ring,stack:1|2|3}`(중압 1~3단 원형 진동, stack 별 gain +0/+1.5/+3 dB 유지). 이전 `{giant,ring}` 표기 제거, note 에 '거인 4단에서는 울리지 않음'.
- 거인 4단: `charge_slam_lv4`(`PLAYER_CHARGE{phase:release,stage:4}`) 하나만 — note 에 lv3·`gs_quake_ring`·`gs_crack_line_lv3` 모두 무음 명시. `charge_stage4` → `PLAYER_CHARGE{phase:stage,stage:4}`(두 payload 에 weapon 키 없음 → weapon 조건 뺌).
- `gs_crack_line_lv1~3`: note 에 '균열이 보일 때만(중압 런·거인 4단에서는 울리지 않음)'.
- `brand_burst`·`overheat_burst`·`dagger_hotwind_burst`: `weapon:dagger` 조건 뺌(불필요). kenki `event:stage` 는 이미 delta 조건 없음.
- `sound-design.md` 표 트리거 칸·연결 메모도 맞췄다.

## 추가 (61라운드 P11 — 1층 BGM 3곡 · 핵심 효과음 20종 품질 패스 · 믹싱, 2026-10-05 자율 모드)
근거: `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md` P11(자율 모드 — 인터뷰 없이 판단, 이유를 여기 기록), 점검 `review-2026-10-05-stage1-design-audit.md` SD-1·SD-2·SD-4, 60 Q22 청취 메모. 분위기 참고 `parts/story/world-bible.md` §0. 도구는 그대로(표준 라이브러리 합성 + ffmpeg, 외부 샘플 없음).

**1. 1층 전용 BGM — 5파일 (`work/bgm_floor1.py`, 설계표 `sound-design.md` 3-1)**
| id | 길이 | 형식 | 쓰는 곳 | gainDb | RMS(정규화 후) |
|---|---|---|---|---|---|
| `bgm/f1_outside` | 96 s | 44.1 kHz 스테레오 | 벽 밖 여정(탄생지·버려진 길·국경 초소) — `bgmByFloorState.1.journey` | +3.5 | -26.5 dBFS |
| `bgm/f1_jan` | 96 s (3/4 150 BPM 80마디) | 〃 | 1층 전투 — `bgmByFloor.1`(기존 키, `floor_low` 대체) = `bgmByFloorState.1.combat` | +3.5 | -24.5 |
| `bgm/f1_boss_p1` | 72 s (6/8 72마디) | 〃 | 만취 1국면 — `bgmByFloorState.1.boss` = `bossPhases[0]` | 0 | -22.8 |
| `bgm/f1_boss_p2` | 72 s | 〃 | 2국면 = p1 + 타악 — `bossPhases[1]` | 0 | -21.1 |
| `bgm/f1_boss_p3` | 72 s | 〃 | 3국면 = p2 울렁임 + 왜곡·불 — `bossPhases[2]` | 0 | -20.2 |

판단과 이유:
- **보스 = 루프 3개(스템 아님)**: 스템은 시스템이 세 소스를 샘플 단위로 맞춰 재생해야 한다. 완성 믹스 3개 + 같은 길이·박자·바탕·**공통 이득**(p1·p2 피크 -9.65·-6.37 dBFS)이면 기존 교차 페이드만으로 동작하고, 재생 위치를 이어 주면 '층이 쌓이는' 느낌이 된다(`mixing.bgmPhaseCrossfadeMs` 800, `bgmPhaseSyncPosition`).
- **인트로 없음**(점검 SD-1 은 '루프 + 인트로'): 기존 단일 파일 루프 방식을 지켰다. 보스 진입은 `boss_start` 효과음이 인트로 역할.
- **키**: `bgmByFloor.1` 은 기존 키 그대로 새 곡을 가리켜 시스템이 바꾸지 않아도 1층 전투가 새 곡이 된다. `bgmByState.boss` 는 `bgm/boss` 그대로(2~7층 공용) — 1층 보스·여정은 **새 최상위 키 `bgmByFloorState`** 로만 알 수 있다(시스템 연결 필요). `floor_low` 는 2층 전용으로(`floors` [1,2] → [2], 오디오 불변).
- **스테레오 44.1 kHz**: 파이프라인을 스테레오 대응으로 넓혔다(`write_wav_stereo`, `wav_info`·`encode.py` 의 길이·이음매·정렬을 채널별로). 모노 경로는 그대로 — 기존 파일 md5 불변으로 확인. M4A 는 채널당 64 kbps(= 128 kbps), OGG q4.
- **용량**: 새 5파일이 OGG 6.11 MB / M4A 6.36 MB. 브라우저 한 곳이 받는 소리 전체 OGG 3.05 → **9.36 MB**(M4A 10.03 MB). 1층 곡은 1층에서만 쓰므로 **층 진입 때 지연 로드** 권장(시스템 판단).
- 빌드 시간: 곡이 길고 스테레오라 BGM 합성이 늘어 `build_bgm` 을 group 단위 3 프로세스 병렬로 바꿨다(곡마다 시드 고정 → 결과 동일, 재실행 md5 일치 확인).

**2. 핵심 효과음 20종 품질 패스 + 변주 23 (`work/sfx_core61.py`, 표 `sound-design.md` 4-8)**
- 다시 만든 같은 키 18: `hit_enemy` · `hit_enemy_crit` · `enemy_death` · `hit_player` · `dash` · `perfect_guard` · `parry` · `parry_perfect` · `swing_katana` · `swing_greatsword` · `swing_dagger` · `bow_shot` · `pickup_gold` · `pickup_potion` · `door_open` · `menu_move` · `menu_select` · `menu_cancel`.
- 새 키 2: `guard_block`(`PLAYER_DAMAGED{guarded:true}`, -2 dB), `combo_finish`(`PLAYER_ATTACK{finisher:true}`, -3 dB) — **트리거 제안, 시스템 확정 필요**.
- 변주 23: `hit_enemy_v2·v3`, `hit_enemy_crit_v2`, `enemy_death_v2·v3`, `hit_player_v2·v3`, `dash_v2·v3`, `guard_block_v2`, `combo_finish_v2`, `parry_v2`, `swing_katana_v2·v3`, `swing_greatsword_v2·v3`, `swing_dagger_v2·v3`, `bow_shot_v2·v3`, `pickup_gold_v2·v3`, `menu_move_v2`. manifest: 변주 항목 `trigger: null` + `variantOf`, 원본 항목 `variants`(원본 포함), `mixing.variantGroups`.
- 권장 음량 변경 3: `hit_enemy` 0 → -3(짧은 구간 음량 +7 dB 중 일부 되돌림), `dash` -5 → -3(파일이 약 3 dB 작아져 합쳐서 Q22 판보다 약 1 dB 작음 — Q22 '조금 더 줄여' 유지), `pickup_potion` -4 → -2(울림을 줄여 약 5 dB 작아진 만큼 일부 보정).
- 방향(Q22 '프라이팬 같은 금속성' 지양): 오래 남는 중역 금속 울림을 모두 뺐고(`hit_enemy_crit` 1.8 kHz, `parry` 1.5·2.6 kHz 0.22 s, `perfect_guard` 880·1175 Hz 종, `menu_select` 1.3 kHz, `swing_katana` 2.4 kHz), 무게는 85~250 Hz 몸통 + 300 Hz '퍽'(노트북 스피커에서도 들리게), 날카로움은 짧은 '딱' + 고역 '샥'. 대역별 시간 분석(30 ms 창, 1 kHz 대역)으로 확인: 옛 `parry` 는 300 ms 에도 -28 dBFS 로 울렸고, 새 `parry` 는 150 ms 에 -42, 새 `hit_enemy` 는 60 ms 에 -36 dBFS 아래.
- `menu_move` 는 0.06 s 로 만들었다가 ffmpeg 6.1 OGG 디코더가 끝을 128 샘플 잘라 검증에 걸려 **0.08 s** 로(소리는 0.05 s 안에 끝).
- 안 고친 것: 차지·검기 단계(Q22·Q25 에서 이미), 보스 효과음(단계 3 P6 과 함께), `guard_hold`·`guard_push`(P1 4동사의 가드 입력 확정 후).

**3. 믹싱 권장값 (`work/mixing.py` → manifest `mixing` + 효과음 항목별 `priority`, 표 `sound-design.md` 5장)**
- 동시 재생 상한 `voices.maxSfx` 12(UI 별도 2), 같은 그룹(원본 + 변주) 기본 3 + 예외, 빼앗기 = 낮은 우선순위·오래된 것부터(loop 제외).
- 우선순위 4 보스 예고·신호 > 3 피격·방어 판정(적 예고 포함) > 2 타격·공격 > 1 환경·획득·부가음, 0 UI. 분포: 4 = 7개, 3 = 12, 2 = 158, 1 = 52, 0 = 5.
- 덕킹(우선순위 4 → SFX -6 dB·BGM -3 dB, 피격 → SFX -3 dB 150 ms), 변주 선택(직전과 다른 것) + 재생 속도 ±3 %, 마스터 리미터, 보스 국면 교차.

**검증·불변**
- `build.py verify`: 245개(효과음 234 + BGM 11) **문제 0**. 새 루프 이음매 튐 비율 OGG / M4A: `f1_outside` 0.10 / 0.17, `f1_jan` 0.30 / 0.58, `f1_boss_p1` 0.28 / 0.12, `f1_boss_p2` 0.23 / 0.28, `f1_boss_p3` 0.62 / 0.24(≤ 1 통과). OGG 길이 차 0(ffmpeg·libvorbisfile), M4A elst = 샘플 수.
- 총 WAV 91.42 MB → 배포 19.39 MB(OGG 9.36 / M4A 10.03 MB). 효과음만 OGG 2.28 MB.
- md5(작업 시작 전 대조): WAV 캐시·OGG·M4A 646개 중 **591개 바이트 불변**, 바뀐 것은 위 18종 × 3(54) + manifest, 새 파일 90개(효과음 25 + BGM 5, × 3). 전체 `build.py` 재실행 결과도 같음.
- `listen_index.json` 245항목 재생성(변주는 원본 분류, `round: "61"`, `priority`·`variants`·`variantOf`·`use`·`channels` 추가).

**시스템에 전달할 것(계약 `sound-assets.md` 갱신은 프로듀서 소관)**
1. 새 최상위 키 `bgmByFloorState`(`{"1": {journey, combat, boss, bossPhases[3]}}`) + `bgmByFloorStateNote`. `bgmByFloor`·`bgmByState` 의 키는 그대로(값만 `bgmByFloor.1` → `bgm/f1_jan`).
2. BGM 항목에 `use`(floor·state·phase), 새 곡은 `sampleRate` 44100 · `channels` 2 — 루프 초는 항목의 sampleRate 로 계산(format 의 `bgmSampleRate`·`channels` 는 기존 곡 기준, `format.perEntryNote`).
3. 효과음 항목에 `priority`(0~4), 원본에 `variants`, 변주에 `variantOf` + `trigger: null`(트리거를 직접 묶지 말 것 — 원본 트리거에서 고른다).
4. `mixing` 새 키: `dedupeMs`·`voices`·`priority`·`ducking`·`variation`·`masterLimiter`·`bgmPhaseCrossfadeMs`·`bgmPhaseSyncPosition`·`bgmPhaseNote`·`bgmJourneyNote`·`variantGroups`.
5. 새 트리거 제안: `PLAYER_DAMAGED{guarded:true}` → `guard_block`, `PLAYER_ATTACK{finisher:true}`(마지막 타 **적중** 때, 활 제외) → `combo_finish`.

## 추가 (61라운드 단계 2·3 — 신규 적 2종 · 보스 '만취' 패스 P6 · 발도 검기 단수 · 가드, 2026-10-05 자율 모드)
근거: `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md`(자율 모드 — 인터뷰 없이 판단, 이유를 여기 기록), 점검 `review-2026-10-05-stage1-design-audit.md` SY-1(4동사)·SY-5(신규 적 = 보스 예습)·SY-8(보스 재구성), 계약 `art-assets.md` §23(행상 throw 놓음 550 ms · 짐꾼 push 놓음 530 ms · 굴러가는 통 60 ms × 8). 도구 그대로(표준 라이브러리 합성 + ffmpeg). 코드 `work/sfx_stage61.py`, 설계표 `sound-design.md` **4-9**.

**새 29 · 다시 11 · 보관 1** (트리거는 전부 **제안** — 시스템 이름 규칙(`EVENT{키:값}`)으로 썼고 실제 이름·값은 시스템 확정)
| 묶음 | 키 | 트리거 제안 |
|---|---|---|
| 독주 행상 (새 4) | `peddler_wick` · `peddler_throw` · `peddler_hurt` · `peddler_death` | `ENEMY_TELEGRAPH{enemy:peddler}` · `ENEMY_ATTACK{enemy:peddler,phase:throw}` · `ENEMY_DAMAGED{enemy:peddler,aux:true}` · `ENEMY_DIED{enemy:peddler}` |
| 술통 짐꾼 (새 8) | `porter_windup` · `porter_push` · `porter_barrel_roll`(루프) · `barrel_return` · `porter_barrel_break` · `porter_liquor_spill` · `porter_hurt` · `porter_death` | `ENEMY_TELEGRAPH{enemy:porter}` · `ENEMY_ATTACK{enemy:porter,phase:push\|roll\|return\|break\|spill}` · `ENEMY_DAMAGED{enemy:porter,aux:true}` · `ENEMY_DIED{enemy:porter}` |
| 보스 파훼·결정타 (새 4 + 다시 1) | `boss1_break_cup` · `boss1_break_pillar` · `boss1_break_barrel` · `boss1_break_reel` · `break_finisher`(다시) | `BOSS_BREAK{kind:cup\|pillar\|barrel\|reel}` · `BOSS_BREAK{kind:finisher}`(그대로) |
| 보스 등장·국면·쓰러짐 (새 3 + 다시 2) | `boss1_entrance` · `boss1_phase_drink`(다시, 트리거 좁힘) · `boss1_phase_blackout` · `boss1_die` · `boss1_spin_start`(다시) | `BOSS_STARTED{boss:1}` · `BOSS_PHASE{boss:1,phase:2}` · `BOSS_PHASE{boss:1,phase:3}` · `BOSS_DIED{boss:1}` · 그대로 |
| 보스 등불 (다시 2) | `boss1_candle_topple`(꺼짐) · `boss1_candle_relight`(다시 켜짐) | 그대로(`attack:darkness,phase:topple\|relight`) |
| 보스 1국면 패턴 (새 4) | `boss1_dash_telegraph` · `boss1_dash` · `boss1_slam_telegraph` · `boss1_slam` | `BOSS_TELEGRAPH{boss:1,attack:dash\|slam}` · `BOSS_ATTACK{boss:1,attack:dash\|slam}` |
| 보스 금속·얇은 소리 다시 (4) | `boss1_drink_lift` · `boss1_drink_finish` · `boss1_barrel_kick` · `boss1_barrel_bounce` | 그대로 |
| 보관 (1) | `boss1_cup_shatter` | (연결 끊음 — `boss1_break_cup` 이 대신) |
| 칼 발도 (새 5) | `katana_iai_ki1` ~ `ki5` | `PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:1~5}` |
| 가드 (다시 2 + 새 1) | `guard_hold`(1.2 s 루프) · `guard_push` · `guard_block_heavy` | 그대로 · `PLAYER_SECONDARY{kind:guard,phase:release,weapon:greatsword}`(weapon 조건 추가) · `PLAYER_DAMAGED{guarded:true,weapon:greatsword}` |

판단과 이유:
- **행상 병 착탄 = `bottle_burst` 재사용(새 파일 없음)**: 아트 §23 이 행상 병에 소모품과 같은 fx 사슬(`fire_bottle_thrown → fire_bottle_burst → fire_pool`)을 쓴다. 같은 물건은 같은 소리여야 플레이어가 '내가 던지는 술병과 같은 것'으로 읽고, 1층 소리 수도 늘지 않는다. 트리거가 하나뿐이라 manifest 에는 새 항목을 만들지 않고 시스템이 `ENEMY_ATTACK{enemy:peddler,phase:impact}` 에서 `sfx/bottle_burst` 를 재생하도록 요청한다(웅덩이는 기존대로 `boss1_fire_loop` 1개).
- **예고 = 놓는 순간까지 커지다 뚝 끊김**: `peddler_wick`(0.55 s)·`porter_windup`(0.53 s)은 시트 프레임 0 에서 시작해 놓음 프레임에서 30 ms 만에 끊긴다. 소리가 끊기는 지점이 곧 피하기 신호이고, 이어서 `peddler_throw`·`porter_push` 가 프레임 5 에 붙는다. 예고는 우선순위 3(`ENEMY_TELEGRAPH`).
- **되치기 '탕' 하나를 짐꾼·보스가 공유(`barrel_return`)**: SY-5 '신규 적 = 보스 예습'. 짐꾼에서 들은 '탕'이 보스전에서 그대로 들리면 파훼가 귀로 이어진다. 보스 쪽은 `BOSS_ATTACK{boss:1,attack:barrel,phase:return}` 에서 같은 id 를 재생하도록 요청. 벽에 튕기는 `boss1_barrel_bounce` 는 일부러 더 둔하게(쳐낸 것 ≠ 벽에 맞은 것).
- **파훼 4종 = 공통 신호 + 재료**: 4종이 같은 뼈대(넓은 '쾅' → 아래로 꺼지는 '부웅' → 0.14 s 주저앉는 '쿵')를 갖고 재료(도자기·술 / 기둥·돌 / 통·술 / 몸이 비틀려 나뒹굶)만 다르다. 손맛을 위해 `BOSS_BREAK` 우선순위를 2 → 3 으로 올리고(`break_count`·`break_finisher` 포함, 오디오 불변), 재생 동안 다른 타격음을 -4 dB 300 ms 누르는 덕킹을 추가했다(`mixing.py`).
- **`boss1_cup_shatter` 보관**: 잔 깨짐이 이제 파훼(`BOSS_BREAK{kind:cup}`)이므로 같은 순간 두 소리가 겹치지 않게 연결을 끊었다. 파일·항목·시드는 그대로(`listen_index` '보관' 분류, note 앞 `[보관 …]`).
- **결정타 다시**: '크고 묵직하게' → 칼날 울림 D6·쪼개지는 쇠·징·종(울림이 남던 금속·얇은 소리)을 모두 빼고 몸통(150→32)·큰 북 둘·0.9 s 낮은 울림·흙돌로. 파일 0.08 s = 일격(옛 규칙 유지). `boss1_die` 는 첫 0.3 s 를 일부러 조용히 두어 결정타와 같은 프레임에 겹쳐도 한 방이 먼저 들린다.
- **국면 전환에 '세상이 돈다'를 넣음**: P6 '세상이 돈다 = 국면 전환 연출(설정에서 끄기)'. 끄는 설정은 멀미 대책(그림)이라 소리는 그대로 둔다. `boss1_phase_drink` 는 트리거를 `BOSS_PHASE{boss:1}` → `{boss:1,phase:2}` 로 좁혔고, 3국면은 새 `boss1_phase_blackout`. 3국면 진입 확정 소등은 기존 패턴 소리 `boss1_candle_topple`(다시 만든 '등불 꺼짐')이 이어서 맡는다(국면 소리에 넣지 않음 — 이후 반복 소등과 같은 소리).
- **1국면 돌진·내리찍기 새로 (지시 범위 밖이지만 P6 패스에 포함)**: 1국면 패턴 3개 중 술통만 전용 소리가 있었고 돌진은 공용 `boss_telegraph`(쇠 긁힘), 내리찍기는 소리가 없었다. 기둥 파훼의 출발점이라 전용으로 만들었다.
- **발도 = 대체(겹침 아님)**: 단수별 무게를 정확히 쌓으려고 `katana_iai_ki1~5` 를 완성된 발도음으로 만들고 `katana_iai_release`(0단)를 대신하게 했다(찌르기 `katana_thrust_ki*` 는 겹침 방식 — 그대로). 옛 발도의 880 Hz 칼날 울림 대신 3.7~4.5 kHz 0.05 s 쇳빛만.
- **가드**: 4동사 확정(우 = 가드, 칼·대검). `guard_push` 는 대검만(떼면 밀쳐내기) → `weapon:greatsword` 조건 추가. `guard_block` 은 61 P11 판이 아직 청취 전이라 바이트 그대로 두고, 무게가 다른 대검용 `guard_block_heavy` 를 새로 만들었다. `guard_hold` 는 1.24 kHz 쇠 험을 빼고 1.2 s 로 늘려 반복이 덜 들리게.
- **적 목소리 없음**: 행상의 '흑'·짐꾼의 '끙'은 성대음 없는 노이즈 포먼트 + 가슴 저역(소리 바이블 1장). 사망 시 쓰러짐 시각은 행상 0.18 s · 짐꾼 0.34 s(무릎 0.16 s)로 잡았다 — death 시트의 실제 쓰러짐 프레임은 아트 JSON 에만 있어 확인하지 못함(아래 미완료).

**검증·불변**
- `build.py sfx` 전체 재합성 후 md5 대조(작업 시작 전 736개): **702개 바이트 불변**, 바뀐 것 = 다시 만든 11종 × 3(WAV·OGG·M4A) + manifest, 새 파일 87개(29 × 3). BGM 은 손대지 않음.
- `build.py verify`: **274개(효과음 263 + BGM 11) 문제 0**. 새 루프 이음매 튐 비율 OGG / M4A: `guard_hold` 0.04 / 0.05, `porter_barrel_roll` 0.70 / 0.30(≤ 1 통과).
- 용량: 효과음 OGG 2.28 → 2.66 MB, 브라우저 한 곳이 받는 전체 OGG 9.36 → 9.74 MB(M4A 10.46 MB).
- 수치 확인(청취 불가 대신): 50 ms 창 음량·대역(0.7~2 kHz) 시간 분석으로 예고 두 개가 0.55·0.53 s 에서 끊기는지, 파훼 4종이 첫 0.3 s 에 -10~-12 dBFS 로 몰리는지, 발도 1→5단의 저역(<250 Hz)이 -23 → -19 dB 로 커지는지, 다시 만든 금속성 소리(`barrel_bounce`·`candle_topple`·`break_finisher` 등)의 0.7~2 kHz 대역이 오래 남지 않는지(남는 것은 술·불 노이즈뿐) 확인. `listen_index.json` 274항목 재생성(새 `round: "61-2"` 41항목, '보관' 4).

**시스템에 전달할 것(계약 `sound-assets.md` 갱신은 프로듀서 소관)**
1. 새 트리거 이벤트·조건(제안): `ENEMY_TELEGRAPH{enemy:peddler|porter}`, `ENEMY_ATTACK{enemy:peddler,phase:throw|impact}`, `ENEMY_ATTACK{enemy:porter,phase:push|roll|return|break|spill}`, `ENEMY_DAMAGED{enemy:<id>,aux:true}`, `ENEMY_DIED{enemy:<id>}`, `BOSS_BREAK{kind:cup|pillar|barrel|reel}`, `BOSS_STARTED{boss:1}`, `BOSS_PHASE{boss:1,phase:2|3}`, `BOSS_DIED{boss:1}`, `BOSS_TELEGRAPH/ATTACK{boss:1,attack:dash|slam}`, `BOSS_ATTACK{boss:1,attack:barrel,phase:return}`, `PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:N}`, `PLAYER_SECONDARY{kind:guard,phase:release,weapon:greatsword}`, `PLAYER_DAMAGED{guarded:true,weapon:greatsword}`. 실제 이름·값(특히 BOSS_BREAK kind, 발도의 move 이름, 짐꾼 통 사건 이름)이 다르면 알려 주면 manifest 를 맞춘다.
2. **대체(둘 다 울리지 않게)**: `boss1_entrance` ↔ `boss_start`, `boss1_die` ↔ `boss_die`, `boss1_phase_drink`/`boss1_phase_blackout` ↔ `boss_phase`, `boss1_dash_telegraph` ↔ `boss_telegraph`, `katana_iai_ki1~5` ↔ `katana_iai_release`(kenkiStage ≥ 1 이면 ki 만), `guard_block_heavy` ↔ `guard_block`(대검), `peddler_hurt`/`porter_hurt` ↔ `enemy_hurt`, `peddler_death`/`porter_death` ↔ `enemy_death`(엘리트면 `elite_die` 위에 겹침 가능), `boss1_break_reel` ↔ `boss1_fall`(파훼로 인정된 넘어짐일 때). 조건이 더 많은(구체적인) 항목 하나만 재생하는 규칙이면 자동으로 맞는다.
3. **재사용(새 항목 없음)**: 행상 병 착탄 → `sfx/bottle_burst`, 보스 술통 되치기 → `sfx/barrel_return`, 불 웅덩이 → `sfx/boss1_fire_loop`, 술 웅덩이 점화 → `sfx/drunk_ignite`.
4. 연결 끊기: `boss1_cup_shatter`(보관). 루프 새 1(`porter_barrel_roll`, 멈춤·깨짐에 80 ms 페이드아웃)·길이 바뀜 1(`guard_hold` 0.6 → 1.2 s — 루프 구간은 manifest `loopEndSample`).
5. 믹싱: `BOSS_BREAK` 우선순위 3(manifest `priority` 이미 반영), `mixing.ducking` 에 BOSS_BREAK 줄, `perGroupOverrides` 4개 추가.

## 추가 (61라운드 단계 2·3 — 트리거 이름 동기화, 2026-10-05 자율 모드)
시스템이 확정한 실제 이름(시스템 보고)에 맞춰 manifest `trigger` 를 고쳤다. 오디오 파일은 바이트 그대로 — `build.py manifest` 로 manifest·`listen_index.json` 만 다시 썼다. 코드 `work/sfx_stage61.py`·`sfx_core61.py`·`sfx_bundle2.py`(트리거 문자열·note), `work/mixing.py`(우선순위 표·덕킹 문구·`bgmBossDefeat`). 위 61-2 절의 '트리거 제안' 표는 당시 기록으로 두고, 지금 값은 이 절과 `sound-design.md` 4-9 가 기준이다.

| 키 | 옛 제안 | 확정(manifest) |
|---|---|---|
| `peddler_wick` | `ENEMY_TELEGRAPH{enemy:peddler}` | `ENEMY_TELEGRAPH{kind:throw}` |
| `peddler_throw` | `ENEMY_ATTACK{enemy:peddler,phase:throw}` | `ENEMY_ATTACK{kind:throw,phase:throw}` |
| (착탄) `bottle_burst` 재사용 | `ENEMY_ATTACK{enemy:peddler,phase:impact}` | `ENEMY_ATTACK{kind:throw,phase:burst}` — manifest 항목은 하나라 트리거는 소모품(`CONSUMABLE_IMPACT{id:fireBottle}`) 그대로, 행상 착탄은 시스템 audioMap 이 같은 id 재생 |
| `porter_windup` | `ENEMY_TELEGRAPH{enemy:porter}` | `ENEMY_TELEGRAPH{kind:roll}` |
| `porter_push` | `ENEMY_ATTACK{enemy:porter,phase:push}` | `ENEMY_ATTACK{kind:roll,phase:push}` |
| `porter_barrel_roll`(루프) | `ENEMY_ATTACK{enemy:porter,phase:roll}` | 시작 `ENEMY_ATTACK{kind:roll,phase:push}`(porter_push 와 함께) · 정지 `phase:rollEnd` 80 ms 페이드(note) |
| `barrel_return` · `porter_barrel_break` · `porter_liquor_spill` | `{enemy:porter,phase:return\|break\|spill}` | `{kind:roll,phase:return\|break\|spill}` |
| `peddler_hurt`·`_death`·`porter_hurt`·`_death` | `ENEMY_DAMAGED/DIED{enemy:<id>}` | 그대로(공용 소리 대체는 시스템 audioMap 처리) |
| `boss1_break_cup`·`_pillar`·`_barrel`·`_reel` | `BOSS_BREAK{kind:cup\|pillar\|barrel\|reel}` | `ui:boss-break{kind:cup\|pillar\|cask\|stumble}` (id·파일 이름은 그대로) |
| `break_finisher` | `BOSS_BREAK{kind:finisher}` | `ui:boss-break{kind:finisher}` |
| `break_count` | `BOSS_BREAK{distinct:true}` | 그대로 — `ui:boss-break` payload 에 `distinct` 가 없어 내부 `BOSS_BREAK` 유지(시스템 확인 필요) |
| `boss1_entrance` | `BOSS_STARTED{boss:1}` | `boss:intro`(조건 없음 — payload 미확인) |
| `boss1_die` | `BOSS_DIED{boss:1}` | 그대로 |
| `combo_finish` | `PLAYER_ATTACK{finisher:true}` | `PLAYER_COMBO_FINISH`(payload `weapon`, 마지막 타 첫 적중 1회, 활 없음) |
| `guard_block` · `guard_block_heavy` | `PLAYER_DAMAGED{guarded:true}` · `{guarded:true,weapon:greatsword}` | 그대로 |

- 우선순위: `mixing.priority.tiers` 에 `boss:intro`(4)·`ui:boss-break`(3) 를 더해 값 불변(`boss1_entrance` 4, 파훼 4종·결정타 3, `combo_finish` 2).
- BGM: `mixing.bgmBossDefeat` 새 키 = `{fadeOutOn: BOSS_DIED, fadeOutMs: 900, silentUntil: EXIT_OPENED, resume: floorState}`(61라운드 프로듀서 판단 '보스 처치 뒤 EXIT_OPENED 까지 정적'). 보스 곡 시작은 `boss:fight` 권장(등장 소리 `boss1_entrance` 가 인트로) — note 에만 적음. `boss:speech`·`boss:fallen` 에는 붙인 소리 없음.

## 추가 (61라운드 단계 4 — 보스 `BOSS_ACTION` 새 동작 · 화살비 타이밍, 2026-10-05 자율 모드)
근거: `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md` 단계 4 배분('새 보스 동작 소리 → 음향'), 시스템 EventBus `BOSS_ACTION {id, action, index?}` 의 새 action, 서서 시작 화살비(`releasesAtMs [240,360,480]`, 770 ms). 도구 그대로. 코드 `work/sfx_stage61.py` 6절, 설계표 `sound-design.md` **4-10**.

| id | 길이 | 트리거(manifest) | 우선순위 |
|---|---|---|---|
| `boss1_intro_roar` 새 | 1.25 s | `BOSS_ACTION{boss:1,action:introRoar}` | 4 |
| `boss1_cup_struck` 새 | 0.62 s | `BOSS_ACTION{boss:1,action:cupStruck}` | 3 |
| `boss1_pillar_crack1~3` 새 | 0.50 / 0.75 / 1.05 s | `BOSS_ACTION{boss:1,action:pillarCrack,index:1~3}` | 3 |
| `boss1_flame_snuff` 새 + `_v2`·`_v3` | 0.34 s | `BOSS_ACTION{boss:1,action:flameSnuff}` (변주는 `trigger: null` + `variantOf`) | 1 |
| `arrow_rain_launch` 다시 | 0.78 → **0.53 s** | 그대로 | 2 |
| `arrow_rain_impact` 다시 | 0.63 s | 그대로 | 2 |

- 표기: 기존 manifest 에 `BOSS_ACTION` 항목이 없어(54라운드 패턴 소리는 `BOSS_TELEGRAPH/ATTACK` 표기 + 시스템 대응표) 보스 관례 `EVENT{boss:1,키:값}` 에 payload 필드 `action`·`index` 를 그대로 썼다.
- 판단·이유는 `sound-design.md` 4-10(포효 1.4 s 창, 균열 = 구조가 다른 3 파일, 촛불 = 짧은 머리·작은 꼬리·변주 3·그룹 4, 잔 '팅' 은 2 kHz 위 짧은 정보음).
- 화살비: `launch` = 첫 발사 240 ms 에 1회 → 시위 0/0.12/0.24 s(옛 0/0.06/0.12 s 는 120 ms 간격과 어긋남), 바람은 0.47 s(= 낙하 휘파람 시작 710 ms) 전에 끝. `impact` = 첫 꽂힘 − 100 ms → '툭' 9개 0.10 + 0.04 s × k(낙하 9곳 × 40 ms, 옛 판은 3개뿐).
- 믹싱: `mixing.priority` 가 조건 하나로 등급을 가를 수 있게(`EVENT{키:값}` 꼴, `TIERS` 에 `BOSS_ACTION{action:…}` 넷 추가 — 다른 항목의 priority 불변 확인). `perGroupOverrides` 에 `boss1_flame_snuff` 4 · `boss1_cup_struck` 2. 덕킹 규칙은 늘리지 않음(포효는 기존 '우선순위 4' 규칙이 그대로 걸림).

**검증·불변**
- 작업 전 md5 822개 대조: 바뀐 것 = `arrow_rain_launch`·`arrow_rain_impact` × 3(WAV·OGG·M4A) + manifest, 나머지 바이트 불변. 새 파일 24개(8 × 3).
- `build.py verify`: **282개(효과음 271 + BGM 11) 문제 0**. 효과음 OGG 2.74 MB, 브라우저 1곳 OGG 9.82 MB / M4A 10.52 MB.
- 수치 확인(20 ms 창 음량): launch 머리 0·0.12·0.24 s, 0.42 s 에 -40 dB 아래 / impact 머리 0.10~0.42 s 아홉 / 촛불 머리 -16 → 40 ms 에 -27 dB, 연기 약 -37 dB / 포효 0~0.72 s -11~-18 dB 유지 후 감쇠.
- `listen_index.json` 282항목 재생성(새 round `61-4` 10항목, 소분류 '잔 · 기둥 (파훼 전)'·'처치 연출 · 촛불 꺼짐').
- `npx vitest run src/systems/audio`: 36 중 35 통과, 1 실패 = `audioDefs.test.ts` '쓰이지 않는 매니페스트 효과음 없음' — 새 8 id 가 시스템 audioMap 에 아직 연결되지 않아서(시스템 작업 대기, 아래).

**시스템에 전달할 것(계약 `sound-assets.md` 갱신은 프로듀서 소관)**
1. `bossActionSfx`(또는 BOSS_ACTION 트리거)에 연결: `introRoar` → `sfx/boss1_intro_roar`, `cupStruck` → `sfx/boss1_cup_struck`, `pillarCrack` → `sfx/boss1_pillar_crack<index>`(index 1~3, 범위 밖은 1·3 으로 자름 — 지금 `bossActionSfx(action)` 은 index 를 받지 않음), `flameSnuff` → `sfx/boss1_flame_snuff`(변주 v2·v3 는 기존 variants 규칙). 연결되면 위 테스트가 통과한다.
2. 대체·겹침: `introRoar` 는 `boss1_entrance` 와 별개(둘 다 재생 — 시각이 3.8 s 떨어져 겹치지 않음). `pillarCrack` 은 같은 프레임의 `ui:boss-break{kind:pillar}`(`boss1_break_pillar`) 위에 **겹침**(대체 아님). `cupStruck` 은 잔이 깨지는 타에는 오지 않는다는 전제(깨지면 `boss1_break_cup` 만).
3. 화살비: 이벤트 시각은 그대로(launch = `releasesAtMs[0]`, impact = 첫 꽂힘 − `RAIN_IMPACT_SFX_LEAD_MS` 100). 시각을 바꾸면 알려 달라.

## 추가 (61라운드 단계 4 — P12 무기 성장 소리, 계약 sound §10, 2026-10-05 자율 모드)
근거: `parts/producer/decisions/2026-10-05-P12-weapon-growth.md`, 계약 `sound-assets.md` §10, 시스템 확정 이벤트(`WEAPON_AWAKEN`·`TRAIT_GAINED`·`GROWTH_MARK`·`GROWTH_GAINED`·`WEAPON_TEMPERED`), 아트 `fx/v4/awaken1_crack`·`awaken2_bloom` 시각. 코드 `work/sfx_stage61.py` 7절, 설계표 `sound-design.md` **4-11**.

| id | 길이 | 트리거(manifest) | 우선순위 |
|---|---|---|---|
| `awaken1` | 1.90 s (정점 0.25 s) | `WEAPON_AWAKEN{stage:1}` | 4 |
| `awaken2` | 2.30 s (정점 0.42 s) | `WEAPON_AWAKEN{stage:2}` | 4 |
| `awaken_tail_katana`·`_greatsword`·`_dagger`·`_bow` | 1.05 · 1.25 · 0.95 · 1.15 s (본소리 0.5 s 부터) | `WEAPON_AWAKEN{weapon:<무기>}` | 4 |
| `trait_manifest` | 0.75 s | `TRAIT_GAINED` (시스템은 `GROWTH_MARK{kind:trait\|temper}` 에도) | 1 |
| `growth_tick` + `_v2`·`_v3` | 0.12 s, -12 dB | `GROWTH_GAINED` (300 ms 묶음) | 1 |

- 옛 소리 트리거 이동(오디오 그대로, note 앞 `[폴백 …]`): `evolve` → `WEAPON_AWAKEN`, `dual_trait` → `TRAIT_GAINED`, `awaken_<무기>` → `WEAPON_AWAKEN{stage:2,weapon}`, `reinforce` → `WEAPON_TEMPERED`(현행 단련). 시스템이 새 id 가 없을 때의 폴백으로 쓰고 테스트가 존재를 검사하므로 지우지 않았다. 옛 `dual_trait_get` 이라는 id 는 manifest 에 없었다(같은 뜻 = `dual_trait`).
- 믹싱: `mixing.TIERS` 4 에 `WEAPON_AWAKEN`(각성·꼬리·폴백 evolve/awaken_* 가 1 → 4). 덕킹 규칙은 그대로(기존 '우선순위 4' 규칙이 걸림).
- 검증: 작업 전 md5 846개 중 바뀐 것 0(새 파일 30 + manifest·listen_index 만). `build.py verify` **292개(효과음 281 + BGM 11) 문제 0**(꼬리 앞을 무음으로 두었을 때 M4A 앞 정렬 4건 → 아주 작은 바람을 깔아 해결). OGG 9.94 MB / M4A 10.65 MB. `listen_index.json` 292항목.
- `npx vitest run src/systems/audio`: 36 중 35 통과, 1 실패 = '쓰이지 않는 manifest 효과음 없음' — 새 10 id(awaken1·2, awaken_tail_×4, trait_manifest, growth_tick·v2·v3). 시스템 audioMap(`GROWTH_SFX`)은 이미 이 id 를 찾지만, 테스트의 `used` 목록에 `GROWTH_SFX` 가 들어 있지 않다(`audioBuild.ts` 주석 '음향 제작 대기 id 라 고정 id 표에 넣지 않는다'). 시스템이 `used` 에 `GROWTH_SFX`(awaken1·awaken2·traitManifest·growthTick·awakenTail(4무기))를 넣으면 통과(음향은 src 를 고치지 않음). 같은 실행에서 61-4 `BOSS_ACTION` 8 id 는 이미 연결되어 통과.

## 추가 (61라운드 단계 5 — P13 기둥 무너짐 · 포물선 술병 · 바닥 줍기, 2026-10-06 자율 모드)
근거: `parts/producer/decisions/2026-10-06-P13-combat-variety.md` §3·§4·§5, 계약 `sound-assets.md` §11, 시스템 확정 트리거 `src/systems/audio/audioDrops.ts`(읽기만). 도구 그대로(표준 라이브러리 합성 + ffmpeg). 코드 `work/sfx_stage61.py` 8절, 설계표 `sound-design.md` **4-12**.

| id | 길이 | 트리거(manifest) | gainDb | 우선순위 |
|---|---|---|---|---|
| `boss1_pillar_collapse` 새 | 1.30 s | `BOSS_ACTION{boss:1,action:pillarCollapse}` (땅에 닿는 프레임 23) | 0 | 3 |
| `boss1_break_pillar` 다시 | 1.90 → 1.10 s | `ui:boss-break{kind:pillar}` (그대로) — 와르르 빼고 부딪힘·돌 균열 위주 | 0 | 3 |
| `boss1_lob_bottle` 새 | 0.85 s | `BOSS_ACTION{boss:1,action:lobThrow,index:0}` | -2 | 3 |
| `voucher_drop` 새 + `_v2`·`_v3` | 0.25 s | `PICKUP_LANDED{kind:voucher}` (크기별 속도 = 시스템) | -8 | 1 |
| `voucher_pickup` 새 | 0.25 s | `PICKUP_COLLECTED{kind:voucher}` (크기별 속도 = 시스템) | -4 | 1 |
| `item_pickup` 새 | 0.30 s | `PICKUP_COLLECTED{kind:consumable}` | -2 | 1 |

- 판단·이유는 `sound-design.md` 4-12(무너짐 = 땅에 닿는 한 순간, break_pillar 를 돌 재료로 맞춤, 포물선 = 솟아 멀어지는 대역, 전표 = 둥근 머리·울림 0·변주 3, 줍기 = 2 kHz 위 짧은 정보음).
- 폴백 유지(오디오 바이트 그대로, note 에 61-5 쓰임만 덧붙임): `pickup_gold`·`pickup_potion`·`boss1_torch_throw`·`boss1_pillar_crack3`. `boss1_pillar_crack3` note 의 '3단에서 멈춤, 무너지지 않음'은 '4번째 충돌에 무너짐'으로 고침.
- 믹싱(`work/mixing.py`): `TIERS` 3 에 `BOSS_ACTION{action:pillarCollapse|lobThrow}`, 1 에 `PICKUP_LANDED`·`PICKUP_COLLECTED`(줍기류 1 = 빼앗기 1순위). `perGroupOverrides` `voucher_drop`·`voucher_pickup` 3 · `item_pickup` 2 · `boss1_pillar_collapse`·`boss1_lob_bottle` 1. 덕킹: 파훼 규칙(-4 dB 300 ms)에 기둥 무너짐 포함 + 새 줄 '우선순위 ≥ 2 재생 → 줍기류 -4 dB 150 ms'. 다른 항목 priority 불변 확인.

**검증·불변**
- 작업 전 md5 878개 대조: 바뀐 것 = `boss1_break_pillar` × 3(WAV·OGG·M4A) + manifest + listen_index, 새 파일 21개(7 × 3). 나머지 바이트 불변.
- `build.py verify`: **299개(효과음 288 + BGM 11) 문제 0**. 효과음 OGG 2.91 MB, 브라우저 1곳 OGG 9.99 MB / M4A 10.68 MB.
- 수치 확인(40 ms 창 음량): collapse 0~0.4 s -10~-14 dB → 와르르 0.8 s 까지 -24~-30 → 먼지 -36~-46 / break_pillar 0.4 s 부터 감쇠, 0.64 s -45 dB 아래(무너짐 꼬리 없음) / lob 0~0.6 s -15~-25 dB 로 서서히 작아짐 / voucher_drop 0.16 s 에 -44~-53 dB(겹쳐도 짧다) / 줍기 둘 0.24 s 에 -60 dB.
- `listen_index.json` 299항목 재생성(새 round `61-5` 8항목, 소분류 '기둥 무너짐'·'기둥 숨기 방지'·'바닥 줍기 · 전표/소모품').
- `npx vitest run src/systems/audio`: 36 중 35 통과, 1 실패 = `audioDefs.test.ts` '쓰이지 않는 manifest 효과음 없음' — 새 7 id(`boss1_pillar_collapse`·`boss1_lob_bottle`·`voucher_drop`(+v2·v3)·`voucher_pickup`·`item_pickup`). `audioDrops.ts` 의 `P13_SFX` 가 이미 이 id 를 찾지만 테스트의 `used` 목록에 `P13_SFX` 가 없다(트리거가 함수 `sfx: () => [...]` 라 `staticSfxIds()` 에도 안 잡힘). 시스템이 `used` 에 `P13_SFX.pillarCollapse·lobBottle·voucherDrop·voucherPickup·itemPickup` 을 넣으면 통과(변주 v2·v3 는 `variantOf` 로 자동). 음향은 src 를 고치지 않음.

**시스템에 전달할 것(계약 `sound-assets.md` 갱신은 프로듀서 소관)**
1. 위 테스트 `used` 에 `P13_SFX` 5개 추가.
2. `voucher_drop` 은 변주 그룹(`variants` 3) — 함수형 트리거(`audioDrops.ts`)에서도 변주 고르기(직전과 다른 것)와 크기별 속도 × ±3 % 흔들기가 함께 걸리는지 확인.
3. 4번째 충돌 순서: `ui:boss-break{kind:pillar}`(break_pillar, 부딪힘) → 프레임 23 `BOSS_ACTION pillarCollapse`(collapse). 4번째 충돌에 `pillarCrack` 이 또 오면(index 4 등) 크랙음이 겹치므로 보내지 않거나 무시 권장.

## 추가 (61라운드 단계 5 — P13 개성 발동음 · 공명, 2026-10-06 자율 모드)
근거: 계약 `sound-assets.md` §11 마지막 줄(후보 순서 `trait_<무기>_<개성 id>` → `trait_<act>` → 무음, 공명 `<공명 id>` → `resonance_proc`, 켜짐 `resonance_on` → `trait_manifest`), 시스템 요청 `parts/system/notes/trait-art-requests-61s5.md` §3, `data/traits.json`(읽기만 — act 분포). 도구 그대로(표준 라이브러리 합성 + ffmpeg). 코드 `work/sfx_stage61.py` 9절, 설계표 `sound-design.md` **4-13**.

- **새 17**: 행동 갈래 15 `trait_launch`·`slam`·`pull`·`bind`·`clone`·`blink`·`wave`·`throw`·`rain`·`ignite`·`deflect`·`shield`·`spin`·`mark`·`burst`(0.30~0.57 s, -7~-9 dB, 트리거 `TRAIT_PROC{act:<act>}`) + `resonance_on`(1.08 s, -3 dB, `RESONANCE_ON`, G6·D7 두 종이 5도로 맞물림) + `resonance_proc`(0.40 s, -7 dB, `TRAIT_PROC{resonance}`).
- **'특색' 층**: 주 타격음을 대체하지 않게 0 ms '딱' 없음(첫 5 ms -15~-65 dB, `hit_enemy` -9 dB), 120~150 Hz 아래 깎음(slam·burst 만 80~90 Hz), 쇠 울림 없음, 리버브 작게. act `move`(1장, 이동 개성)는 일부러 소리 없음.
- **믹싱**(`work/mixing.py`): `TIERS` 1 에 `TRAIT_PROC`, 2 에 `RESONANCE_ON` → 개성 층 우선순위 1(빼앗기 1순위), 공명 켜짐 2. `perGroupOverrides` `trait_<act>` 각 2 · `resonance_proc` 2 · `resonance_on` 1, 새 키 `voices.layerMax`(개성 층 전체 동시 3 — 시스템 구현 필요). 다른 항목 priority 불변.
- **검증·불변**: 작업 전 md5 898개 중 바뀐 것 = manifest 만, 새 파일 51개(17 × WAV·OGG·M4A). 기존 288 항목 manifest 내용 동일(새 17 항목 + `mixing.voices`·`mixing.priority` 만 바뀜). `build.py sfx` 전체 재실행 바이트 재현. `build.py verify` **316개(효과음 305 + BGM 11) 문제 0**, 브라우저 1곳 OGG 10.12 MB / M4A 10.78 MB. `listen_index.json` 316항목(새 분류 'trait' 개성 발동 · 공명).
- `npx vitest run src/systems/audio`: 36 중 35 통과, 1 실패 = `audioDefs.test.ts` '쓰이지 않는 manifest 효과음 없음' — 새 17 id 전부. 시스템이 개성 후보 표(`trait_<act>` 15·`resonance_proc`·`resonance_on`)를 테스트 `used` 에 넣으면 통과(음향은 src 를 고치지 않음).
- 청취 전(수치 검증만).

## 추가 (61라운드 단계 6 — P14 그림 속 입구 전환 · 수련장, 2026-10-06 자율 모드)
근거: 설계 `parts/producer/decisions/2026-10-06-P14-tutorial-color-transition.md` §1·§3, 계약 `sound-assets.md` §12(시스템 확정 줄), 시스템 확정 트리거 `src/systems/audio/audioTraining.ts`(읽기만). 도구 그대로(표준 라이브러리 합성 + ffmpeg). 코드 `work/sfx_p14.py`·`work/bgm_training.py`, 설계표 `sound-design.md` **3-2 · 4-14**.

| id | 길이 | 트리거(manifest) | gainDb | 우선순위 |
|---|---|---|---|---|
| `transition_enter` | 1.45 s | `TRANSITION_BEGIN{mode:enterNode\|training}` — 1.10 s 어둠이 덮임 → 붓질 걷힘 | -2 | 3 |
| `transition_exit` | 1.30 s | `TRANSITION_BEGIN{mode:exitRoom}` — 0 s 붓 한 획, 0.95 s 액자 '톡' | -2 | 3 |
| `transition_floor` | 1.60 s | `TRANSITION_BEGIN{mode:floor}` — 1.22 s 덮임 + 낮은 '둥' | -2 | 3 |
| `training_task` + `_v2`·`_v3` | 0.40 s | `TRAINING_TASK` (A5 · C6 · E6 번갈아) | -7 | 2 |
| `training_stamp` | 0.60 s | `TRAINING_STAMP` — 0 s '쿡', 0.30 s 인주 '쩍' | -3 | 3 |
| BGM `training` | 72 s 루프 | `bgmByState.training` | +1.8 (RMS ≈ -23) | — |

- **재료**: 전환은 종이·바람·먹·붓·나무 액자만(쇠·화약 없음 — 그림 세계로 넘어가는 소리를 전투 재료와 가름). 과제 종은 거의 조화 배음(1·2·3)에 6.5 kHz 위를 깎아 자주 울려도 덜 날카롭게, 변주 3음은 수련장 곡과 같은 A 단조 화음. 도장은 딱 소리 없는 둔탁한 '쿡'(900 Hz 위 깎음) + 떼어낼 때 인주 끈적.
- **수련장 곡**: `f1_jan` 과 같은 악기(콘트라베이스·손풍금·바이올린·류트·손북·A1 드론·바람)로 A 단조 3/4 90 BPM, 잔 거리 주제를 느리고 맑게(처지는 음 없음). 삼전음·몰아치기 없음.
- **믹싱**(`work/mixing.py`): `TIERS` 3 에 `TRANSITION_BEGIN`·`TRAINING_STAMP`, 2 에 `TRAINING_TASK`(줍기류 1 보다 위 — 기존 '우선순위 ≥ 2 → 줍기류 -4 dB' 규칙이 걸림). `perGroupOverrides` 전환 3종 각 1 · `training_task` 2 · `training_stamp` 1. 덕킹 새 3줄: 전환음 → 효과음(≤2) -8 dB 소리 길이 동안, 전환음 → BGM -4 dB, 도장 → 효과음(≤1) -4 dB 300 ms. 새 키 `mixing.transition`(`skipFadeMs` 150 — 건너뛰면 전환음 페이드, floor 는 transition_floor 하나만). manifest `bgmByState.training` 추가(`build.py` 가 BGM spec 의 `state` 로 채움).
- **검증·불변**: 작업 전 md5 948개(배포 OGG·M4A + WAV 캐시) 전부 그대로, 바뀐 것 = manifest·listen_index 만, 새 파일 24개(효과음 7 × WAV·OGG·M4A + BGM 1 × 3). 기존 316 항목 manifest 내용 동일(바뀐 최상위 = `format.perEntryNote`·`mixing`(priority·ducking·voices·variantGroups·transition)·`bgmByState`). `build.py verify` **324개(효과음 312 + BGM 12) 문제 0**, `training` 루프 이음매 OGG 0.14 · M4A 0.08(≤1 통과), 브라우저 1곳 OGG 11.35 MB / M4A 11.98 MB(수련장 곡 +1.2 MB — 지연 로드 권장). `listen_index.json` 324항목(새 분류 `p14` '그림 속 입구 전환 · 수련장', round `61-6`).
- 수치(50 ms 창): enter 0~0.25 s 종이 -29~-35 dB(밝음 7 kHz) → 바람이 커지며 1.10 s 정점 -13 dB → 붓질 -22~-29 / exit 0~0.3 s 붓 -25 → 종이 결 -35~-40 → 0.95 s 액자 '톡' -19 / floor 1.22 s 정점 -13(낮은 대역) / stamp 0 s -12 → 0.35~0.4 s 인주 -27~-31 / task 0.35 s 에 -50.
- `npx vitest run src/systems/audio`: 37 중 35 통과, 실패 2 — ① `audioDefs.test.ts` '쓰이지 않는 manifest 효과음 없음' = 새 7 id(`P14_SFX` 가 테스트 `used` 에 없음, 변주 v2·v3 은 `variantOf` 로 따라옴) ② `audioMix.test.ts` 덕킹 규칙 수 `toHaveLength(4)` → 지금 6(새 3줄 중 효과음 대상 2줄은 파서가 읽고, '전환음 → BGM' 줄은 읽지 않음 — 원 manifest 를 바꿔 넣어 본 결과). 음향은 src 를 고치지 않음.
- 청취 전(수치 검증만).

## 교차 참조 (29라운드 전체 공개 하에 읽은 것)
- 읽기: `parts/story/world-bible.md`, `parts/producer/contracts/story-text.md`, `parts/producer/contracts/ui-system-interface.md`(이벤트 이름), `parts/producer/contracts/art-assets.md`(매니페스트 관례), `data/weapons.json`, `data/enemies.json`, `data/bosses.json`, `data/stages.json`(층 순서).
- 60라운드 읽기(지시 범위): 아트 fx JSON 26개 `assets/sprites/fx/v3/{katana_whirl_loop,katana_whirl_reflect,katana_moon_trail,katana_cleave_crack,katana_execute,katana_mirror_ki,katana_mirror_parry,greatsword_quake_fork,greatsword_echo_counter,greatsword_giant_ring,greatsword_charge_flash_lv4,greatsword_congest_aura,greatsword_congest_burst,dagger_frenzy_clone_in,dagger_frenzy_clone_out,dagger_brand_bleed,dagger_brand_hop,dagger_stuck_blade,dagger_hotwind_trail,dagger_hotwind_burst,bow_arrow_split,bow_arrow_stuck,bow_arrow_recall,bow_deadeye_scope,bow_link_stack,bow_skypierce_line}.json` — 계약 `art-assets.md` §21 이 타이밍 기준으로 가리키는 런타임 데이터(타이밍 필드만 참고).
- 61라운드 읽기(자율 모드, 지시 범위): `parts/story/world-bible.md` §0(분위기), 공개 자료 `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md`·`review-2026-10-05-stage1-design-audit.md`(SD-1·SD-2·SD-4, SY-1 무기 4동사 표)·`2026-10-05-round-60-parallel-production.md`(Q22)·`parts/producer/contracts/sound-assets.md`. 다른 파트 소유 경로(src·data·assets/sprites 등)는 읽지 않았다.
- 61라운드 단계 2·3 읽기: 공개 자료만 — `CLAUDE.md`, `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md`·`review-2026-10-05-stage1-design-audit.md`(SY-1·SY-5·SY-8·SD 절), `parts/producer/contracts/sound-assets.md`·`art-assets.md` §23·`ui-system-interface.md`(보스 이벤트 이름 검색). 아트 JSON(death 프레임 시각)은 읽지 않음.
- 61라운드 단계 4 읽기(자율 모드 — 기록으로 고지, 루트 CLAUDE.md §3 읽기 전체 공개): 공개 자료 `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md`·`contracts/sound-assets.md`·`art-assets.md`(화살비 서서 시작 판)·`ui-system-interface.md`(§17 `ui:boss-roar`). 시스템(읽기만, 이벤트 시각·payload 확인): `src/systems/audio/audioDefs.test.ts`·`audioMix.test.ts`·`audioMap.ts`(bossActionSfx)·`audioMoves.ts`(화살비 id), `src/core/EventBus.ts`(BossActionPayload), `src/systems/boss/BossArena.ts`(pillarCrack index·flameSnuff 호출부), `src/scenes/game/BossIntroArt.ts`·`BossFinale.ts`·`ArrowRain.ts`(이벤트 시각), `src/core/constants/{moves,bossArt}.ts`(낙하 앞당김 100 ms·촛불 간격), `data/bosses.json`(show 시간표)·`data/weapons.json`(활 arrowRain). 수정 없음.
- 61라운드 단계 4 P12 읽기: 공개 자료 `2026-10-05-P12-weapon-growth.md`·`contracts/sound-assets.md` §10·`art-assets.md` §26·`ui-system-interface.md` §18, 시스템(읽기만) `src/systems/audio/audioBuild.ts`(GROWTH_SFX·트리거)·`audioDefs.test.ts`·`audioBuild.test.ts`, 아트(읽기만, 프레임 시각) `assets/sprites/fx/v4/awaken1_crack.json`·`awaken2_bloom.json`. 수정 없음.
- 61라운드 단계 5 P13 읽기: 공개 자료 `2026-10-06-P13-combat-variety.md`·`contracts/sound-assets.md` §9~§11, 시스템(읽기만, 지시 범위) `src/systems/audio/audioDrops.ts`(트리거·폴백·크기별 속도)·`audioDefs.test.ts`(미사용 id 검사)·`audioMap.ts`(GOLD_CHANGED·ITEM_PICKED 의 pickup_gold·pickup_potion 쓰임 확인). 수정 없음.
- 61라운드 단계 5 P13 개성 읽기(지시 범위): 공개 자료 `contracts/sound-assets.md` §11, 시스템 `parts/system/notes/trait-art-requests-61s5.md`(§3 중심), `data/traits.json`(act 분포만). 수정 없음.
- 61라운드 단계 6 P14 읽기(지시 범위): 공개 자료 `2026-10-06-P14-tutorial-color-transition.md`·`contracts/sound-assets.md` §12, 시스템(읽기만) `src/systems/audio/audioTraining.ts`(트리거·모드 매핑). `audioMix.test.ts` 덕킹 파싱은 소스를 열지 않고 manifest 를 바꿔 넣어 테스트 결과로만 확인. 수정 없음.
- 쓰기: `parts/sound/**`, `assets/audio/**` 만.

## 미완료 · 보류
- 실제 청취 검수는 도영 님 복귀 후(컨테이너에서 재생 불가, 수치 검증만 수행). **61-2 새 29·다시 11 도 청취 전. 61-4 새 8·다시 2 와 P12 성장 새 8·변주 2 도 청취 전.**
- ~~61-4: `boss1_break_pillar` 의 '와르르'가 프로듀서 판단과 어긋날 수 있음~~ → 61-5 에서 와르르를 `boss1_pillar_collapse` 로 옮기고 break_pillar 를 다시 만듦. **61-5 새 5·변주 2·다시 1 도 청취 전.**
- 61-2: 행상·짐꾼 death 시트의 쓰러짐 프레임 시각 미확인(소리는 행상 0.18 s · 짐꾼 0.34 s 가정) — 데모에서 어긋나면 시각만 옮겨 다시 만든다. 트리거 이름은 시스템 확정값으로 동기화함(위 절) — 남은 확인: `break_count` 의 `distinct` 이벤트, `boss:intro` payload, 행상·짐꾼 `ENEMY_*` 에 `enemy` 필드 유무. **61라운드 새 BGM 5파일·품질 패스 20종·변주 23 도 청취 전** — 데모에서 들어보고 피드백으로 다듬는다.
- **61-6 새 7(전환 3 · 수련장 2 · 변주 2)과 수련장 BGM 도 청취 전.** 전환음 시간 축은 설계 수치(enter 1.1 s 덮임, exit ~1.3 s)에 맞춤 — UI 연출 실제 시각과 어긋나면 시각만 옮겨 다시 만든다.
- 시스템 파트의 오디오 로더·트리거 연동은 시스템 소유 — 매니페스트 초안을 전달만 한다.
- 진화별 전용 효과음, 엔딩 2종 음악, 층별 BGM 세분화는 `sound-design.md` 6장 참조.
