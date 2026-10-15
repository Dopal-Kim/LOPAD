/**
 * P19 자유 전투 효과음 연결 (계약 sound §14 · free-combat §1) — audioMap 에 펼친다. audioLoop2 와 같은 꼴.
 * - 트리거 = free-combat §1 이벤트 문자열 그대로 (움찔·버팀 깨짐·넉백 바람 2~4·벽꽝·볼링·띄움·착지·낙하·폭발·연쇄·점화·연속 처치).
 * - 무기 타격: ENEMY_DAMAGED{weapon} → hit_<무기>(없으면 hit_enemy). 무기가 아닌 피해(폭발·벽꽝·볼링·불·낙하)는 타격음 없음.
 *   hit_enemy_crit 은 위에 겹침. 같은 프레임 순서 = 이벤트 순서(타격 → 넉백 → 벽꽝 — HitReactions 가 그 순서로 낸다).
 * - 새 적: 고수 ENEMY_ATTACK{drummer, beat|rally} · 처치 drummer_death(enemy_death 대신, audioMap ENEMY_OWN_SFX) /
 *   자폭병 run → bomber_fuse 루프(달리는 자폭병이 하나라도 있는 동안) · 예고 bomber_swell(재생 속도 = 1000/ms) · blast → bomber_blast.
 * - 대체 관계(둘 다 울리지 않음): 자폭병 폭발 ↔ 같은 순간 HAZARD_EXPLODED 의 크기 소리 · 위험물 점화 ↔ 같은 순간 drunk_ignite(POOL_IGNITED).
 * - 전투 BGM 강도 2단(`CombatLayerGate`): 살아 있는 적 ≥ 6 → 켬, ≤ 3 이 2초(또는 보스 방) → 끔, 켠 뒤 최소 6초 (mixing.bgmIntensity).
 */
import { Events, type EnemyAttackPayload, type EnemyDamagedPayload } from '../../core/EventBus';
import type {
  ComboStreakPayload,
  EnemyBowledPayload,
  EnemyFellPayload,
  EnemyKnockedPayload,
  EnemyLandedPayload,
  EnemyStaggeredPayload,
  EnemyWallSlamPayload,
  HazardExplodedPayload,
  HazardIgnitedPayload,
} from '../../core/eventsP19';
import { t, type AudioTrigger } from './audioTrigger';

const s = (id: string) => `sfx/${id}`;

export const P19_SFX = {
  hit: (weapon: string) => s(`hit_${weapon}`),
  hitEnemy: s('hit_enemy'),
  hitEnemyCrit: s('hit_enemy_crit'),
  flinch: s('enemy_flinch'),
  staggerBreak: s('enemy_stagger_break'),
  knockWind: (tier: 2 | 3 | 4) => s(`knock_wind${tier}`),
  wallSlam: (surface: EnemyWallSlamPayload['surface']) => s(`wall_slam_${surface}`),
  bowl: s('enemy_bowl'),
  launch: s('enemy_launch'),
  land: s('enemy_land'),
  landSlam: s('enemy_land_slam'),
  fall: (zone: EnemyFellPayload['zone']) => s(`fall_${zone}`),
  explode: { bottle: s('explode_small'), cask: s('explode_mid'), still: s('explode_large') },
  explodeChain: (n: 1 | 2 | 3) => s(`explode_chain${n}`),
  ignite: s('hazard_ignite'),
  streak: (n: 2 | 4 | 6) => s(`streak_${n}`),
  drummerBeat: s('drummer_beat'),
  drummerRally: s('drummer_rally'),
  drummerDeath: s('drummer_death'),
  bomberFuse: s('bomber_fuse'),
  bomberSwell: s('bomber_swell'),
  bomberBlast: s('bomber_blast'),
} as const;

export const P19_WEAPONS = ['katana', 'greatsword', 'dagger', 'bow'] as const;

/** 볼링 연쇄 둘째부터 · 점화 반경 3칸 이상 · 연쇄 4번째부터 오르는 속도 상한 (sound §14) */
export const P19_RATE = {
  BOWL_CHAIN: 1.06,
  IGNITE_BIG: 0.9,
  IGNITE_BIG_TILES: 3,
  CHAIN_MAX: 1.26,
  SWELL_MS: 1000,
  SWELL_MIN: 0.85,
  SWELL_MAX: 1.2,
} as const;
/** 자폭병 심지 루프 정지 페이드 (manifest bomber_fuse) */
export const BOMBER_FUSE_FADE_MS = 80;
/** 같은 순간으로 보는 창 (같은 프레임에 연달아 온다) */
const SAME_MOMENT_MS = 50;

const clock = (): number => (typeof performance !== 'undefined' ? performance.now() : Date.now());

/** 같은 순간 판단용 시각 · 달리는 자폭병 수 (테스트·디버그용으로 내보낸다) */
export const p19Moments = { bomberBlastAt: -Infinity, hazardIgnitedAt: -Infinity, bombersRunning: 0 };

/** 위험물 점화와 같은 순간인가 — audioBuild 의 drunk_ignite(POOL_IGNITED) 가 쉰다 */
export const igniteJustPlayed = (now = clock()): boolean => now - p19Moments.hazardIgnitedAt <= SAME_MOMENT_MS;

/** 무기 타격음 후보 (무기 없음 = 환경 피해 → 없음) */
export function weaponHitSfx(p: Pick<EnemyDamagedPayload, 'weapon' | 'tick'> | undefined): readonly string[] | null {
  if (!p || p.tick || !p.weapon) return null;
  return [P19_SFX.hit(p.weapon), P19_SFX.hitEnemy];
}

/** 연쇄 폭발 위 겹침 (chain ≥ 1 — 3 이상은 explode_chain3) */
export function chainSfx(chain: number): string | null {
  if (!(chain >= 1)) return null;
  return P19_SFX.explodeChain(Math.min(3, Math.floor(chain)) as 1 | 2 | 3);
}

/** chain > 3 은 2^((chain−3)×2/12), 최대 1.26 */
export function chainRate(chain: number): number {
  return chain > 3 ? Math.min(P19_RATE.CHAIN_MAX, 2 ** (((chain - 3) * 2) / 12)) : 1;
}

/** 연속 처치: 2 · 4 · 6 이상 짝수마다 6 */
export function streakSfx(count: number): string | null {
  if (count === 2) return P19_SFX.streak(2);
  if (count === 4) return P19_SFX.streak(4);
  if (count >= 6 && count % 2 === 0) return P19_SFX.streak(6);
  return null;
}

/** 자폭병 부풂: 예고가 1000ms 가 아니면 clamp(1000/ms, 0.85, 1.2) */
export function swellRate(ms: number | undefined): number {
  if (!ms || !(ms > 0)) return 1;
  return Math.min(P19_RATE.SWELL_MAX, Math.max(P19_RATE.SWELL_MIN, P19_RATE.SWELL_MS / ms));
}

const isEnemyPhase = (p: EnemyAttackPayload | undefined, id: string, phase: EnemyAttackPayload['phase']): boolean =>
  p?.id === id && p.phase === phase;

export const P19_AUDIO_TRIGGERS: readonly AudioTrigger[] = [
  // --- 무기 타격 (ENEMY_DAMAGED{weapon}) ---
  t<EnemyDamagedPayload>({
    event: Events.ENEMY_DAMAGED,
    note: 'P19 무기 타격 → hit_<무기>(없으면 hit_enemy) · 무기가 아닌 피해·틱은 타격음 없음',
    sfx: (p) => weaponHitSfx(p),
  }),
  t<EnemyDamagedPayload>({
    event: Events.ENEMY_DAMAGED,
    note: 'P19 치명 → hit_enemy_crit 을 무기 타격음 위에 겹침',
    when: (p) => p.crit && !p.tick,
    sfx: () => P19_SFX.hitEnemyCrit,
  }),

  // --- 타격 반응 (free-combat §1) ---
  t<EnemyStaggeredPayload>({
    event: Events.ENEMY_STAGGERED,
    note: 'P19 움찔 → enemy_flinch · 버팀 깨짐 → enemy_stagger_break',
    sfx: (p) => (p.kind === 'stagger' ? P19_SFX.staggerBreak : P19_SFX.flinch),
  }),
  t<EnemyKnockedPayload>({
    event: Events.ENEMY_KNOCKED,
    note: 'P19 넉백 2~4단 → knock_wind2~4 (1단 무음)',
    sfx: (p) => (p.tier >= 2 ? P19_SFX.knockWind(p.tier as 2 | 3 | 4) : null),
  }),
  t<EnemyWallSlamPayload>({
    event: Events.ENEMY_WALL_SLAM,
    note: 'P19 벽꽝 → wall_slam_wall|prop|pillar',
    sfx: (p) => P19_SFX.wallSlam(p.surface),
  }),
  t<EnemyBowledPayload>({
    event: Events.ENEMY_BOWLED,
    note: 'P19 볼링 → enemy_bowl (연쇄 둘째부터 재생 속도 1.06)',
    sfx: () => P19_SFX.bowl,
    rate: (p) => ((p.chain ?? 0) >= 1 ? P19_RATE.BOWL_CHAIN : 1),
  }),
  t({
    event: Events.ENEMY_LAUNCHED,
    note: 'P19 띄움(첫 띄움만 — 체공 연장은 이벤트 없음) → enemy_launch',
    sfx: P19_SFX.launch,
  }),
  t<EnemyLandedPayload>({
    event: Events.ENEMY_LANDED,
    note: 'P19 착지 → enemy_land · 내리꽂힘 → enemy_land_slam',
    sfx: (p) => (p.slam ? P19_SFX.landSlam : P19_SFX.land),
  }),
  t<EnemyFellPayload>({
    event: Events.ENEMY_FELL,
    note: 'P19 낙하 구역 → fall_water|drop|fire',
    sfx: (p) => P19_SFX.fall(p.zone),
  }),

  // --- 위험물 ---
  t<HazardExplodedPayload>({
    event: Events.HAZARD_EXPLODED,
    note: 'P19 폭발 술병·술통·증류기 → explode_small|mid|large — 같은 순간 자폭병 폭발이면 bomber_blast 가 대신',
    when: (p) => p.chain > 0 || clock() - p19Moments.bomberBlastAt > SAME_MOMENT_MS,
    sfx: (p) => P19_SFX.explode[p.kind] ?? null,
  }),
  t<HazardExplodedPayload>({
    event: Events.HAZARD_EXPLODED,
    note: 'P19 연쇄(chain ≥ 1) → explode_chain1|2|3 겹침 (chain > 3 속도 2^((chain−3)×2/12), 최대 1.26)',
    sfx: (p) => chainSfx(p.chain),
    rate: (p) => chainRate(p.chain),
  }),
  t<HazardIgnitedPayload>({
    event: Events.HAZARD_IGNITED,
    note: 'P19 점화 → hazard_ignite (반경 ≥ 3칸 속도 0.9) — 같은 순간 drunk_ignite 는 쉰다',
    when: () => {
      p19Moments.hazardIgnitedAt = clock();
      return true;
    },
    sfx: () => P19_SFX.ignite,
    rate: (p) => (p.radiusTiles >= P19_RATE.IGNITE_BIG_TILES ? P19_RATE.IGNITE_BIG : 1),
  }),
  t<ComboStreakPayload>({
    event: Events.COMBO_STREAK,
    note: 'P19 연속 처치 2 → streak_2 · 4 → streak_4 · 6 이상 짝수 → streak_6',
    sfx: (p) => streakSfx(p.count),
  }),

  // --- 새 적: 권주 고수 · 술독병 ---
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: 'P19 고수 북 한 박 → drummer_beat (변주 _v2 번갈아)',
    when: (p) => isEnemyPhase(p, 'drummer', 'beat'),
    sfx: () => P19_SFX.drummerBeat,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: 'P19 고수 오라가 처음 켜짐 → drummer_rally',
    when: (p) => isEnemyPhase(p, 'drummer', 'rally'),
    sfx: () => P19_SFX.drummerRally,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: 'P19 자폭병 달리기 시작 → bomber_fuse 루프 (달리는 자폭병이 하나라도 있는 동안)',
    when: (p) => {
      if (!isEnemyPhase(p, 'bomber', 'run')) return false;
      p19Moments.bombersRunning += 1;
      return true;
    },
    loop: P19_SFX.bomberFuse,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: 'P19 자폭병 달리기 끝(심지 붙음·쓰러짐) → 마지막 하나면 bomber_fuse 80ms 페이드',
    when: (p) => {
      if (!isEnemyPhase(p, 'bomber', 'runEnd')) return false;
      p19Moments.bombersRunning = Math.max(0, p19Moments.bombersRunning - 1);
      return p19Moments.bombersRunning === 0;
    },
    stop: [P19_SFX.bomberFuse],
    stopFadeMs: BOMBER_FUSE_FADE_MS,
  }),
  t<EnemyAttackPayload>({
    event: Events.ENEMY_ATTACK,
    note: 'P19 자폭병 폭발 → bomber_blast (같은 순간 HAZARD_EXPLODED 크기 소리 대신)',
    when: (p) => {
      if (!isEnemyPhase(p, 'bomber', 'blast')) return false;
      p19Moments.bomberBlastAt = clock();
      return true;
    },
    sfx: () => P19_SFX.bomberBlast,
  }),
  t({
    event: Events.NODE_ENTERED,
    note: 'P19 노드 진입: 달리는 자폭병 수 초기화 (루프는 층·노드 전환이 멈춘다)',
    when: () => {
      p19Moments.bombersRunning = 0;
      return true;
    },
    stop: [P19_SFX.bomberFuse],
  }),
];

/** 이 표가 고를 수 있는 효과음 id 전부 (매니페스트 대조 테스트용) */
export function p19SfxIds(): string[] {
  const X = P19_SFX;
  return [
    ...P19_WEAPONS.map((w) => X.hit(w)),
    X.flinch,
    X.staggerBreak,
    ...([2, 3, 4] as const).map((n) => X.knockWind(n)),
    ...(['wall', 'prop', 'pillar'] as const).map((k) => X.wallSlam(k)),
    X.bowl,
    X.launch,
    X.land,
    X.landSlam,
    ...(['water', 'drop', 'fire'] as const).map((z) => X.fall(z)),
    ...Object.values(X.explode),
    ...([1, 2, 3] as const).map((n) => X.explodeChain(n)),
    X.ignite,
    ...([2, 4, 6] as const).map((n) => X.streak(n)),
    X.drummerBeat,
    X.drummerRally,
    X.drummerDeath,
    X.bomberFuse,
    X.bomberSwell,
    X.bomberBlast,
  ];
}

// --- 전투 BGM 강도 2단 (mixing.bgmIntensity) ---

/** 켜기·끄기 기준 (manifest onWhen·offWhen 문장의 수 — 시간 값은 매니페스트 숫자 필드를 쓴다) */
export const COMBAT_LAYER = { ON_ALIVE: 6, OFF_ALIVE: 3, OFF_HOLD_MS: 2000, MIN_ON_MS: 6000 } as const;

/** 살아 있는 적 수 → 타악 층 켬/끔 (켠 뒤 minOnMs 안에는 끄지 않는다 — 웨이브 겹침 사이 깜빡임 방지) */
export class CombatLayerGate {
  private on = false;
  private onAt = 0;
  private alive = 0;
  private boss = false;
  private lowSince: number | null = null;

  constructor(private readonly minOnMs: number = COMBAT_LAYER.MIN_ON_MS) {}

  set(alive: number, boss: boolean, now: number): void {
    this.alive = alive;
    this.boss = boss;
    if (alive <= COMBAT_LAYER.OFF_ALIVE) this.lowSince ??= now;
    else this.lowSince = null;
  }

  /** 지금 켜져 있어야 하는가 (매 프레임) */
  isOn(now: number): boolean {
    if (this.boss) this.on = false;
    else if (!this.on && this.alive >= COMBAT_LAYER.ON_ALIVE) {
      this.on = true;
      this.onAt = now;
    } else if (
      this.on &&
      now - this.onAt >= this.minOnMs &&
      this.lowSince !== null &&
      (this.alive === 0 || now - this.lowSince >= COMBAT_LAYER.OFF_HOLD_MS)
    )
      this.on = false;
    return this.on;
  }

  reset(): void {
    this.on = false;
    this.alive = 0;
    this.lowSince = null;
  }
}
