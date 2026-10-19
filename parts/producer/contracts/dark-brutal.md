# 어두운 톤 · 잔혹 전투 · 상흔 계약 (P21)

근거: `parts/producer/decisions/2026-10-19-P21-dark-brutal.md`. 시스템·UI·아트·음향·스토리가 이 문서만 보고 동시에 작업한다. 기존 계약(free-combat·ui-system-interface·art-assets·sound-assets)은 그대로 유효 — 이 문서가 덧붙인다. 값은 1차, 2차 측정 뒤 아래 '조정 기록'에.

## 1. 고어 설정
- `settings.gore: 2 | 1 | 0` — 2 전체(기본) · 1 줄임(절단·잘린 조각 없음, 피 양 1/3·색 더 어둡게, 데칼 1/3) · 0 끔(피 대신 먹·재 입자, 데칼·사망 변형 없음, 처형은 일반 강타 모양).
- 시스템 `SETTINGS.DEFAULT.gore = 2`, UI `UI_DEFAULT_SETTINGS.gore = 2`(둘이 같은지 테스트). UI 는 설정 화면 + 첫 실행 안내 카드(한 번, `localStorage 'lopad.goreNotice'`)에서 바꾼다.

## 2. 새 이벤트 (시스템이 낸다)
| 이벤트 | 문자열 | 페이로드 | 누가 쓰나 |
|---|---|---|---|
| `ENEMY_WOUNDED` | `enemy:wounded` | `{id, x, y, stage:1\|2, kind}` (HP ≤ 66% → 1, ≤ 33% → 2) | 음향(신음)·fx |
| `ENEMY_GORE` | `enemy:gore` | `{id, x, y, dirX, dirY, weapon:'katana'\|'greatsword'\|'dagger'\|'bow'\|null, cut:'slash'\|'stab'\|'crush'\|'pierce', amount:1\|2\|3}` (적중마다 — 피 분출) | 음향(살 층)·fx |
| `ENEMY_DEATH_VARIANT` | `enemy:death-variant` | `{id, x, y, kind, variant:'collapse'\|'behead'\|'bisect'\|'pinned'\|'burn'\|'drown', dirX, dirY}` (ENEMY_DIED 바로 뒤) | 음향·fx |
| `ENEMY_EXECUTABLE` | `enemy:executable` | `{id, on:boolean}` | UI 표식 |
| `PLAYER_EXECUTE` | `player:execute` | `{target, x, y, weapon, ms}` (처형 시작 — 끝나면 일반 ENEMY_DIED + DEATH_VARIANT) | 음향·UI·fx |
| `PLAYER_WOUNDED` | `player:wounded` | `{stage:0\|1\|2\|3, arrows:number}` (단계가 바뀔 때·화살 박힐 때) | 음향·UI |
| `LOW_HP` | `player:low-hp` | `{on:boolean, ratio}` (HP ≤ 25% 진입/이탈) | 음향(심장)·UI |
- UI 중계: `ui:enemy-executable`(screen 포함)·`ui:player-execute`·`ui:player-wounded`·`ui:low-hp` (free-combat §1 의 중계 규칙과 같다). `UiSnapshot.player.wound{stage, arrows}`.

## 3. 상처 상태 규칙
- **주인공**: HP 비율 > 75% → 0, ≤ 75% → 1(가는 균열·재 떨어짐), ≤ 50% → 2(균열 벌어짐·불씨가 새어 흐름), ≤ 25% → 3(가슴·팔 크게 갈라짐·불씨 뚝뚝·숨이 불꽃). 회복하면 단계도 내려간다(현재 HP 따름).
  - 박힌 화살: 원거리 피격마다 1대(최대 5) — 앵커 `back`·`shoulderL`·`shoulderR`·`thigh`·`arm` 순. 노드가 바뀌면 사라짐.
  - 피격 피: 주인공은 붉은 피가 아니라 **검은 타르 + 불씨 + 재**(숯빛 망령).
- **적**: stage 1 = 베인 자국 스탬프 2~3 + 옷 피 젖음 틴트, stage 2 = 스탬프 4~6 + 피 방울 흘림(걸을 때 0.4초마다 바닥 데칼) + 이동 −10%(절뚝). 적중 방향에 스탬프를 붙인다. 군주는 stage 표시만(이동 감속 없음).

## 4. 처형
- 조건: 적이 `stagger`(버팀 깨짐) 중이거나 HP ≤ 15% · 주인공 앞 부채꼴 1.2칸 안 · 군주 제외(엘리트는 HP ≤ 15% 일 때만).
- 공격 키를 누르면 그 공격이 처형으로 바뀐다(따로 키 없음). 0.45초 무적, 슬로 0.3배 120ms, 줌 펀치, 처치 → 각성 게이지 +(일반 처치의 2배).
- 무기별 처형(사망 변형): 칼 = 목 베기(behead), 대검 = 내려쳐 두 동강(bisect), 단검 = 뒤로 돌아 목 찌르기(collapse + 큰 분출), 활 = 근접 화살 박아 넘어뜨림(pinned).
- 처형 동작 시트가 없으면 시스템은 그 무기의 마지막 연격 시트로 대신한다.

## 5. 사망 변형 선택 (처형 외)
- 대검 막타 + 넘친 피해 ≥ 최대 HP 30% → bisect · 칼 막타 + 넘친 피해 ≥ 30% → behead · 활 막타 + 1.5칸 안에 벽 → pinned · 불 위험물 → burn · 물 낙하 → drown · 나머지 collapse.
- gore 1 은 behead·bisect → collapse(대신 큰 분출), gore 0 은 모두 collapse.

## 6. 피·시체 지속
- 바닥 피 데칼: 노드당 최대 160 장, 넘치면 오래된 것부터 알파 0 으로 1초. 시체: 최대 24 구, 넘치면 가장 오래된 것부터 3초에 걸쳐 어둡게 사라짐. 노드가 바뀌면 둘 다 비운다.
- 시체 밑 피 웅덩이는 1.5초에 걸쳐 퍼진다(스케일 0.3 → 1).
- 벽 근처(1칸)에서 맞으면 벽 튐 데칼.
- 깊이: 데칼은 바닥 층(그림자 위, 몸 아래). 잘린 조각(머리·팔·윗몸)은 짧게 날아 튀고(0.5~0.9초) 바닥에 남아 시체 수에 포함.

## 7. 화면 톤 신호 (시스템 후처리 — 월드 카메라만, HUD 씬 제외)
- `data/grade.json`: `{ saturation, contrast, brightness, shadowTint:'#rrggbb', vignette:{strength, radius}, grain:{amount, fps}, byRegion?:{...}, lowHp:{saturation, vignetteColor:'#rrggbb', pulseHz}, title:{...} }` — 아트 A 가 값을, 시스템이 읽기를 맡는다. WebGL 이면 카메라 postFX(ColorMatrix + Vignette)와 그레인(작은 노이즈 텍스처 타일 · ADD 0.04~0.08), Canvas 면 그레인·비네트만.
- 예고 색(free-combat §2)·위험물 빛·주인공 눈/불씨는 보정 뒤에도 원래 색이 보여야 한다 → 시스템은 이것들을 보정 영향이 적은 층(가산 블렌드 또는 별도 카메라)에 둔다.
- 조명: `data/lighting.json` 주변광을 내리고(아트 A 제안 값), 주인공·적 림 광원을 유지·강화.

## 8. 아트 산출물 경로·규격
- `assets/sprites/fx/v5/`: `blood_spray_{slash,stab,crush,pierce}` (방향 오른쪽 기준, 시스템이 회전), `blood_drip`, `blood_pool`(웅덩이 3변형), `blood_decal_floor`(12변형 1장 아틀라스), `blood_decal_wall`(6), `tar_ember_hit`(주인공 피격), `ash_chips`, `wound_cut`(적 상처 스탬프 10변형, 16~24도트), `stuck_arrow`(앵커별 각도 5), `gore_parts_<enemy>`(머리·팔·윗몸 조각), `ink_ash_burst`(gore 0 대체).
- `assets/sprites/enemies/v4/<enemy>_death_<variant>.png/json` — 적 7종(dummy 제외 6 + 군주는 collapse 만) × 변형.
- `assets/sprites/player/` 주인공 상흔 오버레이: `hero_wound{1,2,3}_<본 시트 이름>` — 본 시트와 **같은 프레임 이름·같은 크기**(투명 + 상흔 층만). 무기 오버레이와 같은 동기 방식. 최소 범위: 대기·달리기·대쉬·피격·칼/대검/단검/활 연격. 없는 시트는 오버레이 없음.
- 처형 동작: `hero_execute_{katana,greatsword,dagger,bow}` (본 시트 규격, 무기 오버레이 포함).
- 타이틀: `assets/sprites/title/` 같은 파일 이름으로 교체(title.json 층 구성 유지 — 층 추가는 title.json 에 적고 UI 가 읽는다).
- 각 시트는 `parts/art/work/atlas57/verify.py` 통과 + art-assets 계약 §37 에 목록.

## 9. 음향 산출물
- `assets/audio/sfx/` 새 키(manifest 등록): `flesh_slash`·`flesh_stab`·`bone_crush`·`dismember`·`blood_splat`·`body_fall`·`execute_hit`·`hero_crack`·`hero_ember_hiss`·`arrow_stick`·`heartbeat_loop`·`enemy_groan_{1,2}`. 타이틀 `bgm/title_dark`, 1스테이지 BGM 어둡게(같은 키 교체 또는 새 키 + sound-assets §15 에 적음).

## 10. 스토리 산출물
- `parts/story/text-pack-66-dark.{md,json}`: 반응 팝 문구 교체안(free-combat 반응 8종 + 연속 처치), 적 대사 톤 교체, 타이틀 문구, 잔혹 묘사 안내문, 고어 설정 이름·설명, 처형 이름 4종, 저HP 문구(쓴다면). 용어집 갱신.

## 조정 기록
