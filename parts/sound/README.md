# 음향 파트 README

## 산출물
| 경로 | 내용 |
|---|---|
| `parts/sound/sound-design.md` | 음향 바이블: 톤, 악기(합성 방식), 층별 BGM 매핑, 효과음 표(트리거 제안) |
| `parts/sound/work/build.py` | **단일 소스.** 효과음·BGM 합성 → OGG·M4A 인코딩 → 매니페스트 → 검증을 전부 재생성. 합성은 파이썬 표준 라이브러리만, 고정 시드로 결정적 |
| `parts/sound/work/sfx_bundle2.py` · `sfx_branch2.py` · `sfx_passive.py` | 60라운드 효과음 정의(2차 묶음 25 · 2단 갈래 32 · 패시브 10). `build.py` 가 이 순서로 import 해 등록한다(시드 = 등록 순서) |
| `parts/sound/work/sfx_core61.py` | 61라운드 P11 핵심 20종 품질 패스(같은 키 18종을 `redo()` 로 다시 등록 — 순서·시드 유지) + 새 2종(`guard_block`·`combo_finish`) + 변주 23. **마지막 모듈 — 새 효과음은 이 파일 끝에만** |
| `parts/sound/work/bgm_floor1.py` | 61라운드 P11 1층 전용 BGM 5파일(벽 밖 · 잔 거리 · 만취 3국면), 44.1 kHz 스테레오. 기존 6곡 뒤에 등록 |
| `parts/sound/work/mixing.py` | 61라운드 믹싱 권장값(동시 재생 상한·우선순위·덕킹·변주·리미터·보스 국면 교차) → manifest `mixing`, 항목별 `priority` |
| `parts/sound/work/listen_index.py` → `listen_index.json` | 청취 검수(들어보기) 페이지용 목록: 전 효과음·BGM 의 분류·한 줄 설명·트리거·길이·루프·ogg/m4a 경로. 매니페스트를 쓸 때마다 함께 재생성 |
| `parts/sound/work/encode.py` | 배포 형식 인코딩·검증(57라운드 Q17). ffmpeg(libvorbis·aac), bitexact 로 결정적 |
| `parts/sound/work/wav/{sfx,bgm}/*.wav` | 합성 원본 **작업 캐시**(git 제외, `work/.gitignore`). `build.py` 로 바이트 단위 재생성 — 저장소·빌드 결과에 넣지 않는다 |
| `assets/audio/sfx/*.{ogg,m4a}` | 효과음 **234종**(61라운드: 핵심 18종 다시 만듦 + 새 2 + 변주 23. 그 전 209종 = 29라운드 42 + 54라운드 1층 보스 '만취' `boss1_*` 18 + 55라운드 대검 차지·칼 잔상 9 + 56라운드 가드·자원·무기 새 수단 34 + 56라운드 검수 활 2 + 57·58라운드 빌드 축·갈래 1단·찌르기·균열·상태 37 + 60라운드 2차 묶음 25·2단 갈래 32·패시브 10 — 그중 `gs_plunge`·`gs_crack`·`katana_echo` 는 보관), 원본 44.1 kHz / mono / 피크 -6 dBFS |
| `assets/audio/bgm/*.{ogg,m4a}` | BGM 11파일: 기존 6곡(22.05 kHz / mono, 27~32 s 루프) + 61라운드 1층 전용 5파일(`f1_outside`·`f1_jan` 96 s, `f1_boss_p1~3` 72 s — 44.1 kHz / **stereo**). 피크 -6 dBFS(보스 p1·p2 는 공통 이득이라 더 낮음) |
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
새 효과음은 `@sfx('이름', '트리거', '설명', gainDb)` 데코레이터 함수 하나를 **마지막 모듈(`sfx_core61.py`) 끝**에 추가하면 매니페스트·들어보기 목록까지 자동 반영된다(`build.py` 본문 중간이나 앞 모듈에 끼우면 시드가 밀려 뒤 소리가 바뀐다). 새 소리의 분류는 `listen_index.py` 의 `EXPLICIT`/`SUBGROUP` 에 적는다(60라운드 모듈 소리는 모듈 이름으로 자동). BGM 은 `@bgm(...)`.

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

## 교차 참조 (29라운드 전체 공개 하에 읽은 것)
- 읽기: `parts/story/world-bible.md`, `parts/producer/contracts/story-text.md`, `parts/producer/contracts/ui-system-interface.md`(이벤트 이름), `parts/producer/contracts/art-assets.md`(매니페스트 관례), `data/weapons.json`, `data/enemies.json`, `data/bosses.json`, `data/stages.json`(층 순서).
- 60라운드 읽기(지시 범위): 아트 fx JSON 26개 `assets/sprites/fx/v3/{katana_whirl_loop,katana_whirl_reflect,katana_moon_trail,katana_cleave_crack,katana_execute,katana_mirror_ki,katana_mirror_parry,greatsword_quake_fork,greatsword_echo_counter,greatsword_giant_ring,greatsword_charge_flash_lv4,greatsword_congest_aura,greatsword_congest_burst,dagger_frenzy_clone_in,dagger_frenzy_clone_out,dagger_brand_bleed,dagger_brand_hop,dagger_stuck_blade,dagger_hotwind_trail,dagger_hotwind_burst,bow_arrow_split,bow_arrow_stuck,bow_arrow_recall,bow_deadeye_scope,bow_link_stack,bow_skypierce_line}.json` — 계약 `art-assets.md` §21 이 타이밍 기준으로 가리키는 런타임 데이터(타이밍 필드만 참고).
- 61라운드 읽기(자율 모드, 지시 범위): `parts/story/world-bible.md` §0(분위기), 공개 자료 `parts/producer/decisions/2026-10-05-round-61-autonomous-stage1.md`·`review-2026-10-05-stage1-design-audit.md`(SD-1·SD-2·SD-4, SY-1 무기 4동사 표)·`2026-10-05-round-60-parallel-production.md`(Q22)·`parts/producer/contracts/sound-assets.md`. 다른 파트 소유 경로(src·data·assets/sprites 등)는 읽지 않았다.
- 쓰기: `parts/sound/**`, `assets/audio/**` 만.

## 미완료 · 보류
- 실제 청취 검수는 도영 님 복귀 후(컨테이너에서 재생 불가, 수치 검증만 수행). **61라운드 새 BGM 5파일·품질 패스 20종·변주 23 도 청취 전** — 데모에서 들어보고 피드백으로 다듬는다.
- 시스템 파트의 오디오 로더·트리거 연동은 시스템 소유 — 매니페스트 초안을 전달만 한다.
- 진화별 전용 효과음, 엔딩 2종 음악, 층별 BGM 세분화는 `sound-design.md` 6장 참조.
