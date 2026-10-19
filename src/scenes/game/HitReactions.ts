/**
 * P19 자유 전투 타격 반응 적용 (방향 문서 ④B · 계약 free-combat §1). 규칙(단계·버팀·피해 수식)은 `systems/reactions`.
 * - `apply`: 피격 직후 — 띄움 / 체공 연장 / 움찔(버팀) / 넉백 단계 (ENEMY_LAUNCHED·STAGGERED·KNOCKED)
 * - `update`: 날아가는 적(2단계 이상) — 낙하 구역(S2 `world.fallZoneAt`) → ENEMY_FELL · 벽·소품 → ENEMY_WALL_SLAM ·
 *   다른 적(3단계 이상) → ENEMY_BOWLED
 * - 연속 처치 (ENEMY_DIED → COMBO_STREAK)
 * 같은 프레임 같은 적은 KNOCKED(피격 순간) → WALL_SLAM(그 뒤 update) 순서.
 */
import { BRUTAL, FEEL, REACTION, TILE } from '../../core/Constants';
import {
  EventBus,
  Events,
  type ComboStreakPayload,
  type EnemyBowledPayload,
  type EnemyFellPayload,
  type EnemyKnockedPayload,
  type EnemyLaunchedPayload,
  type EnemyStaggeredPayload,
  type EnemyWallSlamPayload,
} from '../../core/EventBus';
import { gameState } from '../../core/GameState';
import type { Mob } from '../../objects/Mob';
import {
  StreakCounter,
  bowlDamage,
  effectivePoise,
  extendAir,
  fallOutcome,
  knockDistancePx,
  knockMs,
  overcomesPoise,
  wallSlamDamage,
  type StrikeReaction,
} from '../../systems/reactions';
import type { Game } from '../Game';

/** S2 가 TileWorld 에 더하는 낙하 구역 판정 (없으면 낙하 없음) */
type FallZone = 'water' | 'drop' | 'fire';
interface FallWorld {
  fallZoneAt?: (x: number, y: number) => FallZone | null;
}

/** 물리가 날아가는 쪽에서 막혔는가 (반대쪽 벽에 기대 있던 것은 세지 않는다) */
function blockedAlong(
  b: { left: boolean; right: boolean; up: boolean; down: boolean },
  u: { x: number; y: number },
): boolean {
  const T = 0.3;
  return (b.left && u.x < -T) || (b.right && u.x > T) || (b.up && u.y < -T) || (b.down && u.y > T);
}

export interface ReactionHit {
  /** 그 타 실제 피해 */
  dmg: number;
  /** 공격 진행 방향 단위벡터 */
  nx: number;
  ny: number;
  /** false 면 넉백 없음 (이미 미는 중인 타) */
  knock: boolean;
  /** 추가 넉백 배율 (대검 끌어내기) */
  knockMult?: number;
}

export class HitReactions {
  private readonly streak = new StreakCounter();
  /** 디버그·봇: 반응 횟수 */
  readonly counts: Record<string, number> = {};

  constructor(private readonly g: Game) {}

  private count(key: string): void {
    this.counts[key] = (this.counts[key] ?? 0) + 1;
  }

  /** 피격 직후 (살아 있는 적). 보스는 넉백만(¼ — 패턴을 끊지 않음) */
  apply(mob: Mob, r: StrikeReaction, h: ReactionHit): void {
    if (!mob.active) return;
    const id = mob.spriteId;
    // 공중의 적을 치면 체공이 늘어난다 (최대 2회) — 넉백은 그대로 (일섬이 공중 적을 끌고 간다)
    const air = mob.airState;
    if (air) mob.extendAir(extendAir(air));
    const poise = effectivePoise(mob.poiseAgainst(h.nx, h.ny), mob.elite !== null);
    if (!air && r.launch && mob.canLaunch() && poise <= r.launchMaxPoise) {
      if (mob.launch(REACTION.LAUNCH.AIR_MS)) {
        this.count('launch');
        const p: EnemyLaunchedPayload = { id, x: mob.x, y: mob.y, airMs: REACTION.LAUNCH.AIR_MS };
        EventBus.emit(Events.ENEMY_LAUNCHED, p);
        return;
      }
    }
    if (mob.canStagger(this.g.time.now) && overcomesPoise(r.power, poise)) {
      mob.stagger(REACTION.FLINCH_MS);
      this.count('stagger');
      // P21 (dark-brutal §4): 버팀이 깨지면 잠시 처형 가능
      if (poise > 0) mob.poiseBrokenUntil = this.g.time.now + BRUTAL.EXEC.BROKEN_WINDOW_MS;
      const p: EnemyStaggeredPayload = {
        id,
        x: mob.x,
        y: mob.y,
        kind: poise > 0 ? 'stagger' : 'flinch',
        ms: REACTION.FLINCH_MS,
      };
      EventBus.emit(Events.ENEMY_STAGGERED, p);
    }
    if (!h.knock) return;
    const boss = mob.isBoss;
    const dist = knockDistancePx(r.tier, TILE, {
      boss,
      elite: mob.elite !== null,
      weaponMult: gameState.weapon.def.feel?.knockbackMult,
      mult: h.knockMult,
    });
    const ms = knockMs(r.tier);
    mob.shove(h.nx, h.ny, dist, ms, boss, boss ? undefined : (m, dx, dy) => this.onShoveEnd(m, dx, dy));
    mob.flight =
      !boss && r.tier >= REACTION.WALL_SLAM.MIN_TIER
        ? { tier: r.tier, damage: h.dmg, speed0: (2 * dist) / (ms / 1000), chain: 0, hit: new Set([mob]) }
        : null;
    this.count(`knock${r.tier}`);
    const p: EnemyKnockedPayload = {
      id,
      x: mob.x,
      y: mob.y,
      tier: r.tier,
      dirX: h.nx,
      dirY: h.ny,
      distTiles: Math.round((dist / TILE) * 100) / 100,
    };
    EventBus.emit(Events.ENEMY_KNOCKED, p);
  }

  /** 넉백 끝: 발밑 먼지 */
  private onShoveEnd(mob: Mob, dirX: number, dirY: number): void {
    if (!this.g.scene.isActive() || !mob.active) return;
    this.g.hitFx.knockDust(mob.x, mob.body.bottom, dirX, dirY);
  }

  /** 매 프레임 (적 update 뒤): 날아가는 적의 낙하·벽꽝·볼링 */
  update(): void {
    const list = this.g.mobs.getChildren() as Mob[];
    for (const mob of list) {
      const f = mob.flight;
      const u = mob.shoveDir;
      if (!mob.active || !f || !u) continue;
      const c = mob.body.center;
      const r = Math.min(mob.body.halfWidth, mob.body.halfHeight);
      const ahead = r + REACTION.WALL_SLAM.PROBE_PAD_PX;
      const px = c.x + u.x * ahead;
      const py = c.y + u.y * ahead;
      const zone = (this.g.world as FallWorld).fallZoneAt?.(px, py) ?? null;
      if (zone) {
        this.fall(mob, zone, u);
        continue;
      }
      const cask = this.g.structures.caskAt(px, py);
      if (cask || !this.g.world.isWalkableAt(px, py) || blockedAlong(mob.body.blocked, u)) {
        this.wallSlam(mob, cask ? 'prop' : 'wall', px, py);
        continue;
      }
      if (f.tier >= REACTION.BOWL.MIN_TIER && f.chain < REACTION.BOWL.MAX_CHAIN) this.bowl(mob, list, u);
    }
  }

  /** 벽꽝: 속도 기반 추가 피해 + 쓰러짐 (술통·상자면 그것도 부서진다) */
  private wallSlam(mob: Mob, surface: EnemyWallSlamPayload['surface'], x: number, y: number): void {
    const g = this.g;
    const f = mob.flight;
    if (!f) return;
    const ratio = mob.shoveSpeedRatio;
    const bonus = wallSlamDamage(f.damage, ratio);
    const u = mob.shoveDir ?? { x: 0, y: 0 };
    mob.stopShove();
    if (surface === 'prop') g.structures.burstCasksIn(x, y, TILE * 0.5);
    this.count('wallSlam');
    const p: EnemyWallSlamPayload = {
      id: mob.spriteId,
      x,
      y,
      speed: Math.round(f.speed0 * ratio),
      bonusDamage: bonus,
      surface,
    };
    EventBus.emit(Events.ENEMY_WALL_SLAM, p);
    const W = REACTION.WALL_SLAM;
    g.shake.add(g.time.now, W.SHAKE.PX, W.SHAKE.MS, u);
    g.hitFx.knockDust(x, y, -u.x, -u.y);
    if (this.envHit(mob, bonus, u)) return;
    mob.stagger(W.DOWN_MS);
    g.hitStop.request(g.time.now, W.HITSTOP_MS);
  }

  /** 볼링: 날아가는 적이 다른 적과 닿으면 둘 다 피해 + 맞은 적은 1칸 밀림 (연쇄 MAX_CHAIN 번까지) */
  private bowl(mob: Mob, list: readonly Mob[], u: { x: number; y: number }): void {
    const f = mob.flight;
    if (!f) return;
    const c = mob.body.center;
    const r = Math.min(mob.body.halfWidth, mob.body.halfHeight);
    const B = REACTION.BOWL;
    for (const o of list) {
      if (!o.active || f.hit.has(o) || o.isBoss) continue;
      const oc = o.body.center;
      const or = Math.min(o.body.halfWidth, o.body.halfHeight);
      if (Math.hypot(oc.x - c.x, oc.y - c.y) > r + or + B.CONTACT_PAD_PX) continue;
      f.hit.add(o);
      const dmg = bowlDamage(f.damage);
      const x = (c.x + oc.x) / 2;
      const y = (c.y + oc.y) / 2;
      this.count('bowl');
      const p: EnemyBowledPayload = { hitter: mob.spriteId, target: o.spriteId, x, y, damage: dmg, chain: f.chain };
      EventBus.emit(Events.ENEMY_BOWLED, p);
      this.g.shake.add(this.g.time.now, FEEL.SHAKE.HIT.PX, FEEL.SHAKE.HIT.MS, u);
      const chain = f.chain + 1;
      // 맞은 적: 1칸 날림 — 연쇄가 남았으면 그 적도 볼링을 일으킬 수 있다
      if (!this.envHit(o, dmg, u) && o.active) {
        o.shove(u.x, u.y, B.PUSH_TILES * TILE, B.PUSH_MS);
        o.flight = { tier: f.tier, damage: f.damage, speed0: f.speed0, chain, hit: new Set([...f.hit, o]) };
        o.stagger(REACTION.FLINCH_MS);
      }
      // 날아간 적: 부딪쳐 멈춤
      mob.stopShove();
      if (!this.envHit(mob, dmg, u) && mob.active) mob.stagger(REACTION.FLINCH_MS);
      return;
    }
  }

  /** 밀어 떨어뜨리기: 일반 적 즉사 · 정예 HP 30% 피해 후 밀려온 쪽 2칸 뒤로 · 보스 없음 */
  private fall(mob: Mob, zone: FallZone, u: { x: number; y: number }): void {
    const out = fallOutcome({ isBoss: mob.isBoss, elite: mob.elite !== null });
    if (out === 'none') return;
    mob.stopShove();
    this.count('fell');
    // P21: 곧 오는 처치의 사망 변형 (물 = drown · 불 = burn)
    this.g.brutal?.gore.markFell(mob, zone);
    const p: EnemyFellPayload = { id: mob.spriteId, x: mob.x, y: mob.y, zone };
    EventBus.emit(Events.ENEMY_FELL, p);
    if (out === 'die') {
      this.envHit(mob, Math.max(1, mob.hp), u);
      return;
    }
    if (this.envHit(mob, Math.max(1, Math.round(mob.maxHp * REACTION.FALL.ELITE_HP_RATIO)), u)) return;
    // shortcut: 정예는 문 근처 대신 밀려온 쪽 걸을 수 있는 자리로 — S2 문 위치 API 가 생기면 그쪽으로
    for (let d = 2; d <= 6; d++) {
      const x = mob.x - u.x * d * TILE;
      const y = mob.y - u.y * d * TILE;
      if (this.g.world.isWalkableAt(x, y)) {
        mob.body.reset(x, y);
        break;
      }
    }
  }

  /** 환경 피해 (벽꽝·볼링·낙하) — 반응 없이 피해만, 처치는 감각 '환경'. 죽었으면 true */
  private envHit(mob: Mob, dmg: number, u: { x: number; y: number }): boolean {
    if (!mob.active) return true;
    const died = this.g.combat.hitMob(mob, dmg, {
      crit: false,
      dirX: u.x,
      dirY: u.y,
      heavy: true,
      knock: false,
      env: true,
    });
    if (died) this.g.progress.onKill(mob, 'environment');
    return died;
  }

  /** 연속 처치 (처치 사이 ≤ 1.5초 — 2 이상일 때마다) */
  onEnemyDied(): void {
    const n = this.streak.onKill(this.g.time.now);
    if (n < 2) return;
    const p: ComboStreakPayload = { count: n, windowMs: REACTION.STREAK.WINDOW_MS };
    EventBus.emit(Events.COMBO_STREAK, p);
  }
}
