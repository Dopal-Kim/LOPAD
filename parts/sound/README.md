# 음향 파트 README

## 산출물
| 경로 | 내용 |
|---|---|
| `parts/sound/sound-design.md` | 음향 바이블: 톤, 악기(합성 방식), 층별 BGM 매핑, 효과음 표(트리거 제안) |
| `parts/sound/work/build.py` | **단일 소스.** 효과음·BGM 합성 → OGG·M4A 인코딩 → 매니페스트 → 검증을 전부 재생성. 합성은 파이썬 표준 라이브러리만, 고정 시드로 결정적 |
| `parts/sound/work/encode.py` | 배포 형식 인코딩·검증(57라운드 Q17). ffmpeg(libvorbis·aac), bitexact 로 결정적 |
| `parts/sound/work/wav/{sfx,bgm}/*.wav` | 합성 원본 **작업 캐시**(git 제외, `work/.gitignore`). `build.py` 로 바이트 단위 재생성 — 저장소·빌드 결과에 넣지 않는다 |
| `assets/audio/sfx/*.{ogg,m4a}` | 효과음 142종(29라운드 42 + 54라운드 1층 보스 '만취' `boss1_*` 18 + 55라운드 대검 차지·칼 잔상 9 + 56라운드 가드·자원·무기 새 수단 34 + 56라운드 검수 활 2 + 57·58라운드 빌드 축·갈래 1단·찌르기·균열·상태 37), 원본 44.1 kHz / mono / 피크 -6 dBFS |
| `assets/audio/bgm/*.{ogg,m4a}` | BGM 6곡, 원본 22.05 kHz / mono, 27~32 s 루프, 피크 -6 dBFS |
| `assets/audio/manifest.json` | 시스템 파트가 읽을 목록(계약 초안): 파일(`file` 1순위 + `files` 형식별)·샘플 수·길이·루프 구간·권장 음량·트리거 이벤트 제안·층별 BGM 매핑 |

## 사용법
```
python3 parts/sound/work/build.py            # 전부: 합성 → 인코딩 → 매니페스트 → 검증 표 (약 80초)
python3 parts/sound/work/build.py sfx        # 효과음만 (+인코딩·매니페스트)
python3 parts/sound/work/build.py bgm        # BGM 만 (+인코딩·매니페스트)
python3 parts/sound/work/build.py sfx parry  # 특정 소리만
python3 parts/sound/work/build.py encode     # 작업 캐시 WAV → OGG·M4A 만 다시 (+매니페스트)
python3 parts/sound/work/build.py verify     # 검증(WAV 피크·클리핑·경계 + OGG·M4A 디코드 길이·정렬·피크·루프 이음매·용량)
```
새로 받은 저장소에는 WAV 캐시가 없으므로 `encode`·`manifest`·`verify` 전에 `build.py`(전부)를 한 번 돌린다.
새 효과음은 `build.py` 의 `@sfx('이름', '트리거', '설명', gainDb)` 데코레이터 함수 하나를 추가하면 매니페스트까지 자동 반영된다. BGM 은 `@bgm(...)`.

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

## 교차 참조 (29라운드 전체 공개 하에 읽은 것)
- 읽기: `parts/story/world-bible.md`, `parts/producer/contracts/story-text.md`, `parts/producer/contracts/ui-system-interface.md`(이벤트 이름), `parts/producer/contracts/art-assets.md`(매니페스트 관례), `data/weapons.json`, `data/enemies.json`, `data/bosses.json`, `data/stages.json`(층 순서).
- 쓰기: `parts/sound/**`, `assets/audio/**` 만.

## 미완료 · 보류
- 실제 청취 검수는 도영 님 복귀 후(컨테이너에서 재생 불가, 수치 검증만 수행).
- 시스템 파트의 오디오 로더·트리거 연동은 시스템 소유 — 매니페스트 초안을 전달만 한다.
- 진화별 전용 효과음, 엔딩 2종 음악, 층별 BGM 세분화는 `sound-design.md` 6장 참조.
