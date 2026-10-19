/**
 * P21 어둠·잔혹 효과음 연결 (계약 sound §15 · dark-brutal §2·§9) — audioMap 에 펼친다. audioP19 와 같은 꼴.
 * - 살·뼈 층: enemy:gore{cut} → flesh_slash·flesh_stab·bone_crush·arrow_stick (무기 타격음 hit_<무기> 위에 겹침), amount ≥ 2 → blood_splat(+110ms).
 * - 사망: enemy:death-variant 가 같은 적의 ENEMY_DIED 와 같은 순간이면 enemy_death 대신 body_fall(+ 변형 층) — audioMap ENEMY_DIED 가
 *   `deathVariantComing` 으로 쉰다. 전용 사망음(행상·짐꾼·고수·엘리트·자폭병)이 있는 적은 body_fall 생략(변형 층만).
 * - 처형: player:execute → execute_hit 를 결정타(impactMs)까지 늦춰. 단검은 flesh_stab +3dB 0.9 를 같은 순간.
 * - 주인공: PLAYER_DAMAGED(막지 않음) → hero_crack, 상처 단계 ≥ 2 → hero_ember_hiss · player:wounded 단계 상승·화살 → 층 ·
 *   player:low-hp → heartbeat_loop(페이드 400/600ms, 속도 = HP 비율) · PLAYER_DIED → 1.1초에 끔.
 * - 적 신음: enemy:wounded{stage} → enemy_groan_1|2 (80ms 늦게, 군주 제외).
 * - 고어 설정 0·1 의 끄기·낮추기는 manifest `mixing.gore.levels` (audio.playSfx — `goreGainOf`).
 */
import { BOSSES } from '../../data';
import { Events, type PlayerDamagedPayload } from '../../core/EventBus';
import type {
  EnemyDeathVariantPayload,
  EnemyGorePayload,
  EnemyWoundedPayload,
  GoreCut,
  LowHpPayload,
  PlayerExecutePayload,
  PlayerWoundedPayload,
} from '../../core/eventsP21';
import { t, type AudioTrigger } from './audioTrigger';

const s = (id: string) => `sfx/${id}`;

export const P21_SFX = {
  cut: { slash: s('flesh_slash'), stab: s('flesh_stab'), crush: s('bone_crush'), pierce: s('arrow_stick') } as Record<
    GoreCut,
    string
  >,
  bloodSplat: s('blood_splat'),
  dismember: s('dismember'),
  bodyFall: s('body_fall'),
  bodyFallArmor: s('body_fall_armor'),
  arrowStick: s('arrow_stick'),
  ignite: s('hazard_ignite'),
  executeHit: s('execute_hit'),
  fleshStab: s('flesh_stab'),
  heroCrack: s('hero_crack'),
  heroEmberHiss: s('hero_ember_hiss'),
  heartbeat: s('heartbeat_loop'),
  groan: (stage: 1 | 2) => s(`enemy_groan_${stage}`),
} as const;

/** 전용 사망음이 있는 적 (body_fall 생략 — audioMap ENEMY_OWN_SFX·자폭병과 같은 목록) */
export const OWN_DEATH_ENEMIES = new Set(['peddler', 'porter', 'drummer', 'bomber']);
/** 큰 적 (쓰러짐 0.9 · 신음 0.88) — 나머지는 작은 적 (신음 1.06) */
const BIG_ENEMIES = new Set(['porter', 'charger']);
const HEART = { FADE_IN_MS: 400, FADE_OUT_MS: 600, DEATH_FADE_MS: 1100, AT: 0.25, LOW: 0.1, MAX_RATE: 1.15 } as const;

const db = (v: number) => 10 ** (v / 20);

/** enemy:gore 살 층 음량: amount 1 −3 · 2 0 · 3 +1.5 dB, 무기 없음(폭발 등) −3 dB 더 */
export function goreLayerGain(p: Pick<EnemyGorePayload, 'amount' | 'weapon'>): number {
  const a = p.amount === 1 ? -3 : p.amount === 3 ? 1.5 : 0;
  return db(a + (p.weapon ? 0 : -3));
}

/** enemy:gore 살 층 재생 속도 (무기·결) */
export function goreLayerRate(p: Pick<EnemyGorePayload, 'cut' | 'weapon'>): number {
  if (p.cut === 'slash' && p.weapon === 'greatsword') return 0.88;
  if (p.cut === 'stab') return p.weapon === 'dagger' ? 1.06 : p.weapon === 'katana' ? 0.97 : 1;
  if (p.cut === 'crush' && p.weapon === 'greatsword') return 0.94;
  return 1;
}

/** heartbeat 재생 속도: HP 비율 0.25 → 1.0, ≤ 0.10 → 1.15 (선형) */
export function heartbeatRate(ratio: number): number {
  const k = Math.min(1, Math.max(0, (HEART.AT - ratio) / (HEART.AT - HEART.LOW)));
  return 1 + (HEART.MAX_RATE - 1) * k;
}

/** 사망 변형 → body_fall 줄 (전용 사망음 적·익사 제외) */
export function bodyFallSfx(p: EnemyDeathVariantPayload): string | null {
  if (p.variant === 'drown' || p.elite || OWN_DEATH_ENEMIES.has(p.id)) return null;
  return p.armored ? P21_SFX.bodyFallArmor : P21_SFX.bodyFall;
}

const EXECUTE_RATE: Record<string, number> = { katana: 1, greatsword: 0.9, dagger: 1.08, bow: 1.04 };

export const P21_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  // --- 살·뼈·피 층 ---
  t<EnemyGorePayload>({
    event: Events.ENEMY_GORE,
    note: 'P21 적중 살 층 cut slash|stab|crush|pierce → flesh_slash|flesh_stab|bone_crush|arrow_stick (amount 음량 · 무기 속도)',
    sfx: (p) => P21_SFX.cut[p.cut] ?? null,
    gain: (p) => goreLayerGain(p),
    rate: (p) => goreLayerRate(p),
  }),
  t<EnemyGorePayload>({
    event: Events.ENEMY_GORE,
    note: 'P21 amount ≥ 2 → blood_splat 110ms 늦게 (amount 3 +2dB · 0.92)',
    when: (p) => p.amount >= 2,
    sfx: () => P21_SFX.bloodSplat,
    delayMs: () => 110,
    gain: (p) => (p.amount === 3 ? db(2) : 1),
    rate: (p) => (p.amount === 3 ? 0.92 : 1),
  }),

  // --- 사망 변형 (enemy_death 대신) ---
  t<EnemyDeathVariantPayload>({
    event: Events.ENEMY_DEATH_VARIANT,
    note: 'P21 쓰러짐 → body_fall (갑옷 body_fall_armor · 큰 적 0.9 · pinned −6dB) — 전용 사망음 적·익사는 없음',
    sfx: (p) => bodyFallSfx(p),
    gain: (p) => (p.variant === 'pinned' ? db(-6) : 1),
    rate: (p) => (BIG_ENEMIES.has(p.id) ? 0.9 : 1),
  }),
  t<EnemyDeathVariantPayload>({
    event: Events.ENEMY_DEATH_VARIANT,
    note: 'P21 behead·bisect → dismember (bisect 0.92)',
    when: (p) => p.variant === 'behead' || p.variant === 'bisect',
    sfx: () => P21_SFX.dismember,
    rate: (p) => (p.variant === 'bisect' ? 0.92 : 1),
  }),
  t<EnemyDeathVariantPayload>({
    event: Events.ENEMY_DEATH_VARIANT,
    note: 'P21 pinned → arrow_stick +2dB 0.8',
    when: (p) => p.variant === 'pinned',
    sfx: () => P21_SFX.arrowStick,
    gain: () => db(2),
    rate: () => 0.8,
  }),
  t<EnemyDeathVariantPayload>({
    event: Events.ENEMY_DEATH_VARIANT,
    note: 'P21 burn → hazard_ignite −6dB 1.1',
    when: (p) => p.variant === 'burn',
    sfx: () => P21_SFX.ignite,
    gain: () => db(-6),
    rate: () => 1.1,
  }),

  // --- 처형 ---
  t<PlayerExecutePayload>({
    event: Events.PLAYER_EXECUTE,
    note: 'P21 처형 → execute_hit 를 결정타 프레임(impactMs)에 (칼 1.0 · 대검 0.9 · 단검 1.08 · 활 1.04)',
    sfx: () => P21_SFX.executeHit,
    delayMs: (p) => p.impactMs ?? 0,
    rate: (p) => EXECUTE_RATE[p.weapon] ?? 1,
  }),
  t<PlayerExecutePayload>({
    event: Events.PLAYER_EXECUTE,
    note: 'P21 단검 처형 (collapse + 큰 분출) → flesh_stab +3dB 0.9 같은 순간',
    when: (p) => p.weapon === 'dagger',
    sfx: () => P21_SFX.fleshStab,
    delayMs: (p) => p.impactMs ?? 0,
    gain: () => db(3),
    rate: () => 0.9,
  }),

  // --- 주인공 상흔 ---
  t<PlayerDamagedPayload>({
    event: Events.PLAYER_DAMAGED,
    note: 'P21 막지 않은 피격 → hero_crack 겹침 (hit_player 그대로)',
    when: (p) => !p.guarded && p.amount > 0,
    sfx: () => P21_SFX.heroCrack,
  }),
  t<PlayerDamagedPayload>({
    event: Events.PLAYER_DAMAGED,
    note: 'P21 막지 않은 피격 · 상처 단계 ≥ 2 → hero_ember_hiss (단계 3 0.92) · 저HP 심장 박동 속도',
    when: (p) => !p.guarded && p.amount > 0 && (p.woundStage ?? 0) >= 2,
    sfx: () => P21_SFX.heroEmberHiss,
    rate: (p) => (p.woundStage === 3 ? 0.92 : 1),
    loopRate: (p) => ({ id: P21_SFX.heartbeat, rate: heartbeatRate(p.maxHp > 0 ? p.hp / p.maxHp : 1) }),
  }),
  t<PlayerWoundedPayload>({
    event: Events.PLAYER_WOUNDED,
    note: 'P21 상처 단계 상승 → hero_crack 0.85 (단계 3 +2dB) · 회복으로 내려가면 없음',
    when: (p) => Boolean(p.rose) && p.stage > 0,
    sfx: () => P21_SFX.heroCrack,
    gain: (p) => (p.stage === 3 ? db(2) : 1),
    rate: () => 0.85,
  }),
  t<PlayerWoundedPayload>({
    event: Events.PLAYER_WOUNDED,
    note: 'P21 상처 단계 2·3 으로 오름 → hero_ember_hiss 0.9',
    when: (p) => Boolean(p.rose) && p.stage >= 2,
    sfx: () => P21_SFX.heroEmberHiss,
    rate: () => 0.9,
  }),
  t<PlayerWoundedPayload>({
    event: Events.PLAYER_WOUNDED,
    note: 'P21 박힌 화살이 늘어남 → arrow_stick −3dB 1.1',
    when: (p) => Boolean(p.arrowAdded),
    sfx: () => P21_SFX.arrowStick,
    gain: () => db(-3),
    rate: () => 1.1,
  }),
  t<LowHpPayload>({
    event: Events.LOW_HP,
    note: 'P21 HP ≤ 25% 진입 → heartbeat_loop 루프 (400ms 페이드 인, 속도 = HP 비율)',
    when: (p) => p.on,
    loop: P21_SFX.heartbeat,
    loopFadeInMs: HEART.FADE_IN_MS,
    loopRate: (p) => ({ id: P21_SFX.heartbeat, rate: heartbeatRate(p.ratio) }),
  }),
  t<LowHpPayload>({
    event: Events.LOW_HP,
    note: 'P21 HP ≤ 25% 이탈 → heartbeat_loop 600ms 페이드 아웃',
    when: (p) => !p.on,
    stop: [P21_SFX.heartbeat],
    stopFadeMs: HEART.FADE_OUT_MS,
  }),
  t({
    event: Events.PLAYER_DIED,
    note: 'P21 사망 → heartbeat_loop 1.1초에 끔 (death_slow 와 함께)',
    stop: [P21_SFX.heartbeat],
    stopFadeMs: HEART.DEATH_FADE_MS,
  }),

  // --- 적 신음 ---
  t<EnemyWoundedPayload>({
    event: Events.ENEMY_WOUNDED,
    note: 'P21 적 상처 단계 1·2 → enemy_groan_1|2 (80ms 늦게 · 작은 적 1.06 · 큰 적 0.88 · 군주 제외)',
    when: (p) => !BOSSES[p.kind],
    sfx: (p) => P21_SFX.groan(p.stage),
    delayMs: () => 80,
    rate: (p) => (BIG_ENEMIES.has(p.kind) ? 0.88 : 1.06),
  }),
];

/** 이 표가 고를 수 있는 효과음 id 전부 (매니페스트 대조 테스트용) */
export function p21SfxIds(): string[] {
  const X = P21_SFX;
  return [
    ...Object.values(X.cut),
    X.bloodSplat,
    X.dismember,
    X.bodyFall,
    X.bodyFallArmor,
    X.executeHit,
    X.heroCrack,
    X.heroEmberHiss,
    X.heartbeat,
    X.groan(1),
    X.groan(2),
  ];
}

/**
 * manifest `mixing.gore.levels` → 이 효과음(원본 id — 변주는 원본 그룹)의 음량 배율. 0 = 끔. 설정이 없으면 1
 */
export function goreGainOf(
  levels: Record<string, { mute?: string[]; gainDb?: Record<string, number> }> | undefined,
  group: string,
  gore: number,
): number {
  const L = levels?.[String(gore)];
  if (!L) return 1;
  if (L.mute?.includes(group)) return 0;
  const g = L.gainDb?.[group];
  return typeof g === 'number' ? db(g) : 1;
}
