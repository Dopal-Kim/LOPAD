# 계약: 음향 산출물 ↔ 게임 시스템 로드 형식 (57라운드 Q38 신설)

음향 파트는 아래 형식으로 내보내고, 시스템 파트는 아래 형식만 믿고 로드·재생한다. 변경은 양쪽 합의(인터뷰) 후 이 문서부터 고친다.

- 근거: 29라운드(음향 자율 결정 S1~S9 수용, `assets/audio/manifest.json` 을 음향↔시스템 계약 초안으로 승격 — `contracts/sound-assets.md` 는 '복귀 후'로 미뤄 둠), 57라운드 Q17(소리 OGG 전환)·Q38(OGG q4 / M4A 64·96kbps 대체 / WAV 원본은 재생성 캐시·git 제외 / ffmpeg 를 인코딩 빌드 의존성으로 기록 / manifest `files`·`samples`·`loopStartSample`·`loopEndSample` 승인 → 이 문서 신설). 산출: 음향 64e1654.
- 이 문서의 필드 목록은 64e1654 시점 `assets/audio/manifest.json`(효과음 105 · BGM 6 = 111항목)을 옮긴 것이다.

## 1. 파일·경로 (음향 소유 `assets/audio/**`)
| 파일 | 내용 |
|---|---|
| `assets/audio/manifest.json` | 전체 목록·형식·믹싱·트리거 (아래 2~6절) |
| `assets/audio/sfx/<이름>.ogg` + `.m4a` | 효과음. id = `sfx/<이름>` |
| `assets/audio/bgm/<이름>.ogg` + `.m4a` | 배경음. id = `bgm/<이름>` |

- 같은 소리는 항상 **OGG(1순위) + M4A(대체)** 두 파일이 한 쌍이다. WAV 는 `assets/` 에 두지 않는다(5절).

## 2. manifest 최상위
```ts
interface SoundManifest {
  version: 1;
  generatedBy: string;            // 생성 스크립트 경로 (참고)
  format: SoundFormat;            // 3절
  mixing: {                       // 4절
    masterDb: number; sfxBusDb: number; bgmBusDb: number;
    bgmCrossfadeMs: number; bgmBossDuckDb: number; note?: string;
  };
  bgmByFloor: Record<'1'|'2'|'3'|'4'|'5'|'6'|'7'|'8', string>;  // 층 → bgm id
  bgmByState: { title: string; boss: string; emperor: string }; // 상태 → bgm id
  entries: SoundEntry[];
}
```

## 3. 형식 `format` · 항목 `entries[]`
```ts
interface SoundFormat {
  container: 'ogg'; codec: 'vorbis'; mime: string;          // 1순위 (file)
  alternates: { container: 'm4a'; codec: 'aac-lc'; mime: string }[]; // 대체 (files 의 2번째부터)
  encode: { bgm: { oggQuality: 4; m4aKbps: 64 }; sfx: { oggQuality: 4; m4aKbps: 96 } };
  source: { container: 'wav'; dir: string; note?: string };   // 합성 원본 위치 (5절)
  bitDepth: 16; peakDbfs: -6.0; sfxSampleRate: 44100; bgmSampleRate: 22050; channels: 1;
  filesNote?: string; loopNote?: string;                      // 설명
}

interface SoundEntry {
  id: string;                     // 'sfx/<이름>' | 'bgm/<이름>'
  kind: 'sfx' | 'bgm';
  category: 'combat' | 'boss' | 'world' | 'event' | 'pickup' | 'ui' | 'bgm';
  file: string;                   // 1순위 경로 (.ogg) — = files[0]
  files: string[];                // 같은 소리의 형식별 경로, 선호 순서 [ogg, m4a]
  sampleRate: number;             // sfx 44100 / bgm 22050
  channels: 1;
  samples: number;                // 원본 길이(샘플 수) — 루프·길이 계산 기준
  durationMs: number;             // samples / sampleRate (참고)
  loop: boolean;
  loopStartSample?: number;       // loop 일 때만. 이음매 구간 [start, end)
  loopEndSample?: number;
  gainDb: number;                 // 버스 기준 상대 음량 (4절)
  trigger: { event: string; when: string[] } | null; // 효과음 = 재생 시점, bgm = null (6절)
  floors?: number[];              // bgm 만 — 쓰는 층 (참고, bgmByFloor 와 같은 정보)
  note: string;                   // 소리 설명 (참고)
}
```
- **로드**: 시스템은 `this.load.audio(id, entry.files)` 처럼 `files` 를 선호 순서 그대로 넘겨 **재생 가능한 첫 형식**을 쓴다(Safari 등 OGG 미지원 브라우저는 M4A).
- `file` 은 `files[0]`(OGG)과 같다. 한 경로만 받는 코드는 `file` 을 써도 된다.

## 4. 음량·믹싱
- `gainDb` = 버스(`sfxBusDb` / `bgmBusDb`) 기준 상대값(dB). BGM 의 `gainDb` 는 곡 사이 음량(RMS 약 −21 dBFS)을 맞추는 보정값.
- `mixing`: 마스터·버스 음량, BGM 교차 페이드(`bgmCrossfadeMs`), 보스전 BGM 낮춤(`bgmBossDuckDb`). 시스템은 이 값을 읽어 적용한다.
- 권장(현 manifest `mixing.note`): 같은 효과음이 20ms 안에 겹치면 1회로 묶는다.

## 5. 루프 구간 (`loop: true` 항목)
- 이음매 구간은 **`[loopStartSample, loopEndSample)`**(샘플 단위). 현재는 모두 파일 전체 `[0, samples)`.
- 디코더가 끝 패딩을 남겨 버퍼가 `samples` 보다 길 수 있다(특히 M4A). 이때 시스템은 `loopStart = loopStartSample / sampleRate`, `loopEnd = loopEndSample / sampleRate` 로 지정해 패딩을 건너뛴다.
- 현재 루프 항목: 효과음 13(`guard_hold`·`charge_loop`·`katana_iai_hold`·`bow_strain`·`boss1_drink_gulp`·`boss1_barrel_roll`·`boss1_fire_loop`·`katana_guardbreak_hold`·`fire_weapon_loop`·`katana_whirl_loop`·`gs_congest_loop`·`dagger_hotwind_loop`·`bow_deadeye_hold`) + BGM 6.

## 6. 트리거 `trigger`
- `event` = 시스템 내부 이벤트 이름, `when` = 조건 문자열 목록(`'키:값'` 꼴, 예 `'weapon:katana'`·`'phase:hold'`·`'boss:1'`). 빈 목록이면 조건 없음.
- 29라운드 결정대로 이 이벤트들은 **시스템 내부 EventBus** 이름이며 UI 계약(`ui-system-interface.md`)의 이벤트가 아니다. 트리거 → 재생 매핑은 시스템이 구현한다.
- **예외(61 단계 2·3)**: 파훼 소리는 UI 계약 이벤트 `ui:boss-break`(`ui-system-interface.md` §17, `{kind: cup|pillar|cask|stumble|finisher}`)를 트리거로 쓴다 — 위 29라운드 원칙(트리거 = 내부 EventBus)의 명시적 예외. 시스템 내부 `BOSS_BREAK` 는 break_count(`distinct:true`)에만 쓴다.
- 새 소리에 새 이벤트·조건 키가 필요하면 음향이 manifest 에 적고 시스템에 요청한다(이 문서 갱신 동반).
- 현 manifest 의 `event` 이름(참고): `BOSS_ATTACK`·`BOSS_DIED`·`BOSS_PHASE`·`BOSS_STARTED`·`BOSS_TELEGRAPH`·`BRAND_BURST`·`BRAND_CHANGED`·`BREATH_FOCUS`·`ENEMY_ATTACK`·`ENEMY_DAMAGED`·`ENEMY_DIED`·`ENEMY_TELEGRAPH`·`FATE_DECIDED`·`GOLD_CHANGED`·`GROGGY`·`ITEM_PICKUP`·`KENKI_CHANGED`·`OVERHEAT`·`PARRY_SUCCESS`·`PERFECT_GUARD`·`PLAYER_ATTACK`·`PLAYER_CHARGE`·`PLAYER_DAMAGED`·`PLAYER_DASH`·`PLAYER_HEALED`·`PLAYER_SECONDARY`·`PLAYER_SKILL`·`ROOM_CLEARED`·`ROOM_ENTERED`·`RUN_ENDED`·`SHOP_PURCHASE`·`STAGE_STARTED`·`STORY`·`UI_MENU_CANCEL`·`UI_MENU_MOVE`·`UI_MENU_SELECT`·`UTBUN_CHANGED`·`WEAPON_EVOLVED`·`WEAPON_REINFORCED`. (61 단계 2·3 추가) `PLAYER_COMBO_FINISH{weapon}`·`boss:intro`·`boss:fight`·`boss:speech`·`boss:fallen`·`ui:boss-break`(위 예외)·`EXIT_OPENED`.
- 57·58라운드 효과음 37종(음향 요청, 시스템 확정 대기): 이벤트 `MARK_CHANGED`·`STATUS_BURST`·`SET_EFFECT`·`POOL_IGNITED`·`DRUNK_SWAY`·`ENDURE_TRIGGERED` 와 UI 계약 §14.11 의 `TAG_SET_CHANGED`·`DUAL_TRAIT_GAINED`·`CURSE_GAINED`·`CURSE_ENDED`·`PERFECT_SUCCESS`, 조건 키 `WEAPON_EVOLVED{kind:awaken}`·`CURSE_GAINED{source:bloodPact}`·`move:`·`kenki:`·`part:`·`branch:`. 시스템이 이름을 확정하면 이 목록을 갱신한다.
- 60라운드 효과음 67종(음향 요청, 시스템 확정 대기): 새 이벤트 `ELITE_SPAWNED`·`ELITE_PREFIX{prefix,phase}`·`CONSUMABLE_IMPACT{id}`·`BOSS_BREAK{distinct,kind,count}`·`STATUS_CHANGED{id,phase}`·`BRANCH_EFFECT{branch,effect,stack?}`·`PASSIVE_PROC{passive,fire?}`, 기존 이벤트 새 조건 키 `ENEMY_DIED{elite}`·`BOSS_DIED{finisher}`·`SHOP_PURCHASE{group:reroll|mapInfo}`·`UI_MENU_SELECT{menu:event}`·`ROOM_ENTERED{type:event}`·`CHALLENGE_STARTED/CLEARED{kind,outcome}`·`NODE_GRADED{grade}`·`HIDDEN_NODE_FOUND`·`CONSUMABLE_USED{id}`·`STRUCTURE_USED{kind:still}`·`branch:`·`stage:4|5`·`phase:` 계열. 갈래·패시브·접두어 id 는 음향 임시 영문이며 시스템 실제 id 로 manifest 를 맞춘다. `potion_use` 는 `PLAYER_HEALED{source:potion}` 으로 좁힐 것.
- **(60라운드 시스템 확정)** 시스템 이벤트 이름(EventBus): `TAG_SET_CHANGED`·`DUAL_TRAIT_GAINED`·`CURSE_GAINED{id,source}`·`CURSE_ENDED`·`PERFECT_SUCCESS{kind}`·`MARK_CHANGED`·`STATUS_BURST{kind}`·`SET_EFFECT{tag,effect}`·`POOL_IGNITED`·`DRUNK_SWAY`·`ENDURE_TRIGGERED{source}`·`BRANCH_EFFECT{branch,effect,stack?}`·`PASSIVE_PROC{passive,fire?}`·`STATUS_CHANGED{id,phase}`·`ELITE_SPAWNED{id,prefix}`·`ELITE_PREFIX{prefix,phase,count?}`·`CONSUMABLE_USED{id}`·`CONSUMABLE_IMPACT{id}`·`BOSS_BREAK{kind,distinct,count}`·`NODE_GRADED{grade}`·`HIDDEN_NODE_FOUND{nodeId}`·`EVENT_NODE_ENTERED{id}`·`STRUCTURE_FIRE{target}`·`WEAPON_GAUGE`. 갈래 id 는 시스템 노드 id(zangetsu·meikyo·resonance·clot·dance·heatwave·volley·giant 등). 시스템은 manifest 의 옛 이름을 `audioBuild.SOUND_ID_ALIASES` 로 대응한다. 음향은 manifest 를 이 이름으로 맞췄다(60라운드).
- 보관 항목(60라운드 Q6): `gs_plunge`·`gs_crack`·`katana_echo` — 파일·manifest 항목은 남기되 시스템은 연결하지 않는다.

## 7. 원본·인코딩 (음향 파트 규칙)
- **WAV 원본은 재생성 캐시**다: 합성 스크립트가 `format.source.dir`(음향 작업 폴더)에 바이트 단위로 같게 다시 만든다. **git 에 넣지 않고 배포하지 않는다**(음향 작업 폴더의 `.gitignore`).
- 인코딩: OGG Vorbis 품질 4, M4A(AAC-LC) BGM 64kbps · 효과음 96kbps. 원본 형식은 16bit 모노, 효과음 44.1kHz · BGM 22.05kHz, 피크 −6 dBFS.
- **ffmpeg** 는 음향 인코딩(WAV → OGG·M4A) 빌드 의존성이다. 저장소에는 인코딩 결과(`.ogg`·`.m4a`)와 manifest 가 커밋된다.
- 소리를 추가·수정하면 음향 파트가 OGG·M4A 한 쌍과 manifest 항목(`files`·`samples`·루프 구간 포함)을 함께 갱신한다.

## 8. 계약 범위
- 시스템이 의존하는 것은 `assets/audio/manifest.json` 과 그 안에 적힌 오디오 파일뿐이다. 음향 작업 폴더(`parts/sound/**`)의 스크립트·원본은 계약이 아니다(바뀌어도 시스템에 영향 없음).
- UI 는 소리를 직접 다루지 않는다(음소거는 `ui-system-interface.md` §11.3 `setMuted`).

## 9. 61라운드 (1층 BGM·핵심 효과음·믹싱)
- **BGM**: 새 최상위 키 `bgmByFloorState` = `{"1": {"journey": "bgm/f1_outside", "combat": "bgm/f1_jan", "boss": "bgm/f1_boss_p1", "bossPhases": ["bgm/f1_boss_p1","bgm/f1_boss_p2","bgm/f1_boss_p3"]}}`. `bgmByFloor["1"]` = `bgm/f1_jan`(키 유지). 보스 국면 전환(`BOSS_PHASE`)은 다음 곡을 **현재 재생 위치에서** 시작해 800ms 교차 페이드(`mixing.bgmPhaseCrossfadeMs`·`bgmPhaseSyncPosition`). 새 BGM 은 44.1kHz 스테레오 — 루프 길이는 각 항목 `sampleRate` 로 계산. BGM 항목 `use`(floor·state·phase). `floor_low` 는 2층 전용.
- **효과음 필드**: 모든 효과음 `priority`(0 UI ~ 4 보스 예고), 원본 `variants`(원본 포함 목록), 변주 `variantOf`·`trigger: null` — 원본 트리거가 오면 목록에서 직전과 다른 것을 골라 재생 속도 ±3%.
- **`mixing` 새 키**: `dedupeMs`·`voices`(효과음 12·UI 2·같은 소리 3)·`priority`·`ducking`(우선순위 4 → 효과음 −6·BGM −3dB, 주인공 피격 → 효과음 −3dB 150ms)·`variation`·`masterLimiter`·`bgmPhase*`·`bgmJourneyNote`·`variantGroups`. 넘치면 우선순위 낮고 오래된 것부터 끊음(루프 제외). (61 단계 2·3) `bgmBossDefeat` = `{fadeOutOn: BOSS_DIED, fadeMs: 900, silentUntil: EXIT_OPENED, resume: floorState}` — 보스 처치 때 BGM 을 900ms 에 걸쳐 끄고 출구가 열릴 때까지 무음, 그 뒤 층 상태 곡으로 돌아감(정확한 필드 이름은 manifest 기준).
- **새 트리거 (61 단계 2·3 확정)**: `PLAYER_DAMAGED{guarded:true}` → `guard_block`(**대검이면 `guard_block_heavy`**), ~~`PLAYER_ATTACK{finisher:true}`~~ → **`PLAYER_COMBO_FINISH{weapon}`**(연격 마지막 타 첫 적중 1회, 활 해당 없음) → `combo_finish`.
- 용량: 브라우저 1곳 OGG 약 9.4MB — 1층 BGM 은 지연 로드 권장.
- **(61 단계 2·3 음향)** 새 효과음 29·다시 11. 루프 목록에 `porter_barrel_roll`(0.96s, 멈추거나 깨질 때 80ms 페이드) 추가, `guard_hold` 1.2s(루프 구간은 `loopEndSample`). 트리거는 ~~제안값(시스템 확정 후 manifest 맞춤)~~ → **시스템 확정(61 단계 2·3)**: 행상 `ENEMY_TELEGRAPH{kind:throw}`·`ENEMY_ATTACK{kind:throw,phase:throw|burst}`(burst → `sfx/bottle_burst` 재사용)·짐꾼 `ENEMY_TELEGRAPH{kind:roll}`·`ENEMY_ATTACK{kind:roll,phase:push|return|break|spill|rollEnd}`(`porter_barrel_roll` 은 push 에서 시작, rollEnd 에서 80ms 페이드)·파훼 `ui:boss-break{kind:cup|pillar|cask|stumble|finisher}`(내부 reel → stumble)·break_count 는 `BOSS_BREAK{distinct:true}`·보스 등장 `boss:intro`·처치 `BOSS_DIED{boss:1}`·`BOSS_STARTED/PHASE{boss:1}`·1국면 `BOSS_TELEGRAPH/ATTACK{attack:dash|slam}`·발도 `PLAYER_SKILL{weapon:katana,move:iai,phase:release,kenkiStage:1~5}`·대검 `guard_block_heavy`·`guard_push`. **대체 관계(둘 다 울리지 않음)**: `boss1_entrance`↔`boss_start`, `boss1_die`↔`boss_die`, `boss1_phase_drink`/`_blackout`↔`boss_phase`, `boss1_dash_telegraph`↔`boss_telegraph`, `katana_iai_ki*`↔`katana_iai_release`, `guard_block_heavy`↔`guard_block`(대검), 행상·짐꾼 hurt/death ↔ `enemy_hurt`/`enemy_death`, `boss1_break_reel`↔`boss1_fall`(`ui:boss-break{kind:stumble}` 기준 — stumble 이 오면 break_reel 만). `boss1_cup_shatter` 는 보관(연결 끊음). `BOSS_BREAK` 우선순위 3, 파훼·결정타 동안 우선순위 2 이하 −4dB 300ms.
