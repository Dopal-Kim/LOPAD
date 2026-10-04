# 음향 파트 README

## 산출물
| 경로 | 내용 |
|---|---|
| `parts/sound/sound-design.md` | 음향 바이블: 톤, 악기(합성 방식), 층별 BGM 매핑, 효과음 표(트리거 제안) |
| `parts/sound/work/build.py` | **단일 소스.** 효과음·BGM·매니페스트를 전부 재생성. 파이썬 표준 라이브러리만 사용, 고정 시드로 결정적 |
| `assets/audio/sfx/*.wav` | 효과음 103종(29라운드 42 + 54라운드 1층 보스 '만취' `boss1_*` 18 + 55라운드 대검 차지·칼 잔상 9 + 56라운드 가드·자원·무기 새 수단 34), 44.1 kHz / 16 bit / mono, 피크 -6 dBFS |
| `assets/audio/bgm/*.wav` | BGM 6곡, 22.05 kHz / 16 bit / mono, 27~32 s 루프, 피크 -6 dBFS |
| `assets/audio/manifest.json` | 시스템 파트가 읽을 목록(계약 초안): 파일·길이·루프·권장 음량·트리거 이벤트 제안·층별 BGM 매핑 |

## 사용법
```
python3 parts/sound/work/build.py            # 전부 재생성 + 검증 표 (약 30초)
python3 parts/sound/work/build.py sfx        # 효과음만 (+매니페스트)
python3 parts/sound/work/build.py bgm        # BGM 만 (+매니페스트)
python3 parts/sound/work/build.py sfx parry  # 특정 소리만
python3 parts/sound/work/build.py verify     # 생성된 파일 검증(길이·피크·클리핑·루프 경계·용량)
```
새 효과음은 `build.py` 의 `@sfx('이름', '트리거', '설명', gainDb)` 데코레이터 함수 하나를 추가하면 매니페스트까지 자동 반영된다. BGM 은 `@bgm(...)`.

## 자율 결정 (29라운드, 도영 님 부재 중 권장안으로 결정 — 복귀 후 검토)
음향 파트 개시 BLANK(`parts/sound/CLAUDE.md`, GDD 8장) 네 항목을 아래와 같이 정했다. 근거는 `parts/producer/decisions/2026-10-01-round-29-autonomous-demo.md` 의 자율 진행 지시.

| # | 항목 | 결정 | 대안(검토용) | 이유 |
|---|---|---|---|---|
| S1 | 제작 도구 | **파이썬 표준 라이브러리 절차 합성**(`wave/array/math/random`), 외부 라이브러리·다운로드·샘플 없음. RBJ 바이쿼드·Karplus-Strong·Schroeder 리버브 직접 구현 | jsfxr/sfxr 계열, 무료 샘플(CC0), 외부 스킬 | 네트워크 금지 조건, 재현성(단일 스크립트), 라이선스 문제 없음 |
| S2 | BGM 곡 수·분위기 | **6곡**: title / floor_low(1~2층) / floor_mid(3~5층) / floor_high(6~8층) / boss(1~7층) / emperor(8층 보스). 층 구간은 스토리 바이블의 외곽→전선·군부→귀족·수도 구분을 따름 | 층별 8곡, 혹은 보스별 곡 | 데모 범위. 3구간은 세계관의 분위기 경계와 일치하고 재사용이 쉽다 |
| S3 | 효과음 목록 | 지시받은 29종 + 보강 13종 = **42종** (bow_draw, hit_enemy_crit, enemy_hurt, charger_dash, boss_start, boss_telegraph, boss_fan, boss_die, shop_buy, trial_clear, fate_decided, menu_cancel, save). 보강분은 `data/weapons·enemies·bosses.json` 의 행동(조준 차지, 치명, 보스 돌진 예고·부채꼴, 구매, 저장)에 대응 | 29종만 | 데이터에 있는 행동에 소리가 비면 데모에서 바로 티가 난다. 전부 짧고 용량 작음 |
| S4 | 파일 포맷 | **WAV PCM 16 bit mono.** SFX 44.1 kHz, BGM 22.05 kHz(각 3 MB 이하 조건 충족, 최대 1.35 MB). 총 10.0 MB | OGG(ffmpeg 변환, ~1/8), SFX 도 22.05 kHz | 브라우저 호환·무손실·검증 용이. 배포 시 OGG 변환은 한 줄로 가능 |
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

## 교차 참조 (29라운드 전체 공개 하에 읽은 것)
- 읽기: `parts/story/world-bible.md`, `parts/producer/contracts/story-text.md`, `parts/producer/contracts/ui-system-interface.md`(이벤트 이름), `parts/producer/contracts/art-assets.md`(매니페스트 관례), `data/weapons.json`, `data/enemies.json`, `data/bosses.json`, `data/stages.json`(층 순서).
- 쓰기: `parts/sound/**`, `assets/audio/**` 만.

## 미완료 · 보류
- 실제 청취 검수는 도영 님 복귀 후(컨테이너에서 재생 불가, 수치 검증만 수행).
- 시스템 파트의 오디오 로더·트리거 연동은 시스템 소유 — 매니페스트 초안을 전달만 한다.
- OGG 변환, 진화별 전용 효과음, 엔딩 2종 음악, 층별 BGM 세분화는 `sound-design.md` 6장 참조.
