/**
 * 활 개성·셋째 갈래 '유성' 길 규칙 (61 G → 61 단계 5 P13 전투 양상):
 * 코앞 사격(가까운 적 → 벽·기둥·적에게 처박기) · 튕기는 화살 · 꿰어 박기(완벽 놓기 → 화살째 밀려 벽에 박힘/그 자리 묶음) ·
 * 되튀는 화살 · 낙하 사격 · 화살 덫(대쉬 자리에 덫 → 밟은 적 묶음) · 화살 그물(화살비 한가운데로 끌어모아 묶음) · 이어지는 비 ·
 * 흩날리는 살(연사 처치 → 사방으로 화살) · 꿰미(관통 화살에 꿰인 적들이 함께 끌려가 부딪침) / 혜성.
 * 유성 1차(하늘 화살)·별 표적(하늘 화살 자리로 빨아들임)·술별·걸으며 연사·불화살은 BowBranch·ArrowRain·BranchMoves.
 */
import Phaser from 'phaser';
import { BUILD_ART, BUILD_FX, DEPTH, TILE, TRAIT_FX } from '../../../../core/Constants';
import type { PlayerAttackPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import type { ActiveRule } from '../../../../systems/build/buildMods';
import type { FxHandle } from '../../../../systems/fx/fx';
import { sheetLoopRange } from '../BuildArt';
import { traitFxId } from '../../../../systems/growth/traitArt';
import { T, type Pt, type RuleKit } from './RuleKit';

interface Trap {
  at: Pt;
  until: number;
  fx: FxHandle | null;
  gfx: Phaser.GameObjects.Graphics | null;
}

const unit = (x: number, y: number): Pt => {
  const l = Math.hypot(x, y) || 1;
  return { x: x / l, y: y / l };
};

export class BowRules {
  private traps: Trap[] = [];
  private strideAt = -Infinity;
  /** 꿰미: 관통 화살 → 꿴 적 차례 */
  private readonly skewers = new WeakMap<Projectile, Mob[]>();
  /** 공명(덫 비)이 듣는 '덫이 적을 묶음' */
  onTrap: ((mob: Mob) => void) | null = null;

  constructor(private readonly k: RuleKit) {}

  /** 낙하 사격: 대쉬 사격이 솟았다가 앞쪽에 세 발로 떨어진다 */
  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    const r = k.rt.rule('dashRain');
    if (!r || p.kind !== 'dashAttack') return;
    const pl = k.g.player;
    const dir = unit(p.dirX, p.dirY);
    const n = k.p(r, 'drops', 3);
    const ahead = T(k.p(r, 'aheadTiles', 3));
    const base = { x: pl.x, y: pl.y };
    for (let i = 0; i < n; i++) {
      const side = (i - (n - 1) / 2) * TILE * 0.9;
      const at = { x: base.x + dir.x * ahead - dir.y * side, y: base.y + dir.y * ahead + dir.x * side };
      k.g.time.delayedCall(k.p(r, 'delayMs', 350) + i * 90, () => {
        if (!k.g.scene.isActive()) return;
        this.skyArrow(at, T(k.p(r, 'radiusTiles', 1)), k.p(r, 'damageMult', 0.6), 'b_dropShot');
      });
    }
    k.fire('b_dropShot', 'rain');
  }

  /**
   * 하늘 화살 한 발 (개성 전용 fx → bow_meteor_arrow — 없으면 고리). 피해는 그 시트의 판정 칸 시작에
   * (art §27 낙하 시트 `impactFrame 3`·`impactAtMs 120` — FxPool.leadMs)
   */
  skyArrow(at: Pt, r: number, mult: number, trait: string): void {
    const k = this.k;
    const played = k.moves.fx(trait, at, { fallbacks: [BUILD_ART.METEOR_ARROW], scale: 0.7 });
    if (!played) k.rt.fx.ring(at.x, at.y, r, BUILD_FX.COLOR.METEOR, 200);
    const lead = played ? k.g.fx.leadMs(played.id) : 0;
    const land = () => {
      if (!k.g.scene.isActive()) return;
      for (const m of k.rt.fx.inCircle(at.x, at.y, r)) k.hit(m, mult, { x: 0, y: 1 });
    };
    if (lead > 0) k.g.time.delayedCall(lead, land);
    else land();
  }

  /** 대쉬: 화살 덫 (떠난 자리) */
  onDash(p: { x: number; y: number }): void {
    const k = this.k;
    const r = k.rt.rule('dashTrap');
    if (!r) return;
    const max = k.p(r, 'maxTraps', 3);
    while (this.traps.length >= max) this.clearTrap(this.traps.shift()!);
    const at = { x: p.x, y: p.y };
    const ms = k.p(r, 'lifeMs', 6000);
    const g = k.g;
    // art §27 덫 수명 시트 (`loopRange [0,3]` — 덫이 남아 있는 동안 반복, 밟히면 끄고 `_snap`) → 없으면 꽂힌 화살
    const own = traitFxId('bow', 'b_arrowTrap');
    const id = g.fx.has(own) ? own : g.fx.has(BUILD_ART.ARROW_STUCK) ? BUILD_ART.ARROW_STUCK : null;
    const range = id ? sheetLoopRange(g.fx.sheet(id)) : undefined;
    const fx = id
      ? g.fx.play(id, at.x, at.y, {
          depth: DEPTH.PICKUP,
          durationMs: ms,
          hooks: false,
          ...(range ? { loopRange: range } : {}),
        })
      : null;
    let gfx: Phaser.GameObjects.Graphics | null = null;
    if (!fx) {
      const D = TRAIT_FX.TRAP;
      gfx = g.add.graphics().setDepth(DEPTH.PICKUP);
      gfx.lineStyle(1, D.COLOR, 1);
      for (const dx of [-D.PX, 0, D.PX]) gfx.lineBetween(at.x + dx, at.y, at.x + dx * 0.6, at.y - D.PX * 2);
    }
    this.traps.push({ at, until: k.now + ms, fx, gfx });
    k.fire('b_arrowTrap', 'set');
  }

  private clearTrap(t: Trap): void {
    this.k.g.fx.finish(t.fx);
    t.gfx?.destroy();
  }

  onArrowSpawn(shot: Projectile, p: PlayerAttackPayload): void {
    const k = this.k;
    // 혜성: 완벽 놓기 화살은 끝까지 꿰뚫는다 (맞을 때마다 터짐 — onShotHit)
    const comet = k.rt.rule('comet');
    if (comet && p.bowPower === 'perfect') shot.pierceLeft = Math.max(shot.pierceLeft, k.p(comet, 'pierce', 99));
    // 되튀는 화살: 가득 당겨 쏜 화살이 끝에 닿으면 한 번 돌아온다
    const bounce = k.rt.rule('fullBounce');
    if (bounce && (p.bowPower === 'full' || p.bowPower === 'perfect') && !shot.buildTag) {
      const prev = shot.onEnd;
      shot.onEnd = (s, reason) => {
        prev?.(s, reason);
        this.bounceBack(s, k.p(bounce, 'damageMult', 0.6));
      };
    }
    // 꿰미: 관통 화살이 꿴 적을 기억한다
    if (k.rt.rule('skewerDrag') && !shot.buildTag && shot.pierceLeft > 0) this.skewers.set(shot, []);
  }

  private bounceBack(s: Projectile, mult: number): void {
    const k = this.k;
    if (!k.g.scene.isActive()) return;
    const v = s.body.velocity;
    const l = Math.hypot(v.x, v.y);
    if (l <= 0) return;
    const back = { x: -v.x / l, y: -v.y / l };
    k.shot({ x: s.x + back.x * 4, y: s.y + back.y * 4 }, back, mult, {
      tag: 'bounce',
      speedTiles: 12,
      rangeTiles: 6,
      pierce: 1,
      tint: BUILD_FX.COLOR.METEOR,
    });
    k.moves.fx('b_fullBounce', s, { fallbacks: ['hit_bow'] });
    k.fire('b_fullBounce', 'bounce');
  }

  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    const k = this.k;
    const own = !shot.buildTag;
    const perfect = k.rt.isPerfectShot(shot);
    const v = shot.body.velocity;
    // 코앞 사격: 가까이 붙은 적은 날려 벽·기둥·뒤의 적에게 처박는다
    const pb = k.rt.rule('pointBlankShove');
    if (pb && own && !died && Math.hypot(mob.x - shot.originX, mob.y - shot.originY) <= T(k.p(pb, 'rangeTiles', 2))) {
      k.moves.fx(
        'b_pointBlank',
        { x: mob.x, y: mob.y - 8 },
        { angle: Math.atan2(v.y, v.x), fallbacks: ['hit_bow_heavy'] },
      );
      k.moves.slam(mob, { x: v.x, y: v.y }, k.p(pb, 'knockTiles', 2), 'b_pointBlank', {
        slamMult: k.p(pb, 'slamMult', 0.5),
        slamStunMs: k.p(pb, 'slamStunMs', 600),
      });
      k.fire('b_pointBlank', 'push');
    }
    // 튕기는 화살: 짧게 쏜 화살로 쓰러뜨리면 가까운 적에게
    const ric = k.rt.rule('killRicochet');
    if (ric && own && died && !perfect && !k.rt.isStrongShot(shot)) {
      const next = k.rt.fx.nearest(mob.x, mob.y, T(k.p(ric, 'rangeTiles', 4)), new Set([mob]));
      if (next) {
        k.shot({ x: mob.x, y: mob.y - 6 }, { x: next.x - mob.x, y: next.y - mob.y }, k.p(ric, 'damageMult', 0.6), {
          tag: 'ricochet',
          speedTiles: 14,
          rangeTiles: k.p(ric, 'rangeTiles', 4) + 1,
        });
        k.moves.fx('b_ricochet', { x: mob.x, y: mob.y - 6 }, { fallbacks: ['hit_bow'], flipX: next.x < mob.x });
        k.fire('b_ricochet', 'bounce');
      }
    }
    // 꿰어 박기: 완벽 놓기 화살에 맞은 적이 화살째 밀려가 벽에 박히거나 그 자리에 꽂힌다
    const pin = k.rt.rule('perfectPin');
    if (pin && perfect && !died) this.pinShot(mob, unit(v.x, v.y), pin);
    // 꿰미: 먼저 꿴 적들이 지금 맞은 적에게 끌려와 부딪친다
    const sk = this.skewers.get(shot);
    const skew = k.rt.rule('skewerDrag');
    if (sk && skew && mob.active) {
      for (const m of sk) {
        if (!m.active || m.isBoss) continue;
        k.moves.chainLine(m, mob, TRAIT_FX.CHAIN_COLOR, 240);
        k.moves.pull(m, mob, Math.hypot(m.x - mob.x, m.y - mob.y) / TILE, 'b_skewer', {
          stopTiles: 0,
          slamMult: k.p(skew, 'slamMult', 0.4),
          slamStunMs: k.p(skew, 'slamStunMs', 700),
        });
      }
      if (sk.length > 0) {
        k.moves.fx(
          'b_skewer',
          { x: mob.x, y: mob.y - 8 },
          { angle: Math.atan2(v.y, v.x), fallbacks: ['bow_arrow_pierce_hit'] },
        );
        k.fire('b_skewer', 'drag', { n: sk.length });
      }
      sk.push(mob);
    }
    // 혜성: 완벽 놓기 화살이 맞을 때마다 터진다
    const comet = k.rt.rule('comet');
    if (comet && perfect) {
      const c = mob.body ? { x: mob.body.center.x, y: mob.body.center.y } : { x: mob.x, y: mob.y - 8 };
      const r = T(k.p(comet, 'burstRadiusTiles', 1));
      k.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.METEOR, 200);
      for (const m of k.rt.fx.inCircle(c.x, c.y, r, new Set([mob])))
        k.hit(m, k.p(comet, 'burstMult', 0.5), { x: m.x - c.x, y: m.y - c.y });
      k.fire('comet', 'burst');
    }
  }

  private pinShot(mob: Mob, u: Pt, pin: ActiveRule): void {
    const k = this.k;
    // art §27 꽂힌 화살 수명 시트 (f0 박힘 → loopRange [1,4] → f5 사라짐, 회전) → 없으면 bow_arrow_stuck
    const stick = (at: Pt, ms: number) => {
      const own = traitFxId('bow', 'b_perfectPin');
      const id = k.g.fx.has(own) ? own : BUILD_ART.ARROW_STUCK;
      const range = sheetLoopRange(k.g.fx.sheet(id));
      if (k.g.fx.has(id))
        k.g.fx.play(id, at.x, at.y, {
          angle: Math.atan2(u.y, u.x),
          depth: DEPTH.HIT_FX,
          durationMs: ms,
          hooks: false,
          ...(range ? { loopRange: range } : {}),
        });
    };
    k.moves.slam(
      mob,
      u,
      k.p(pin, 'pinTiles', 2.5),
      'b_perfectPin',
      { slamMult: k.p(pin, 'slamMult', 0.5), slamStunMs: 0 },
      (res) => {
        if (!mob.active) return;
        const wall = res.kind === 'wall';
        const ms = wall ? k.p(pin, 'wallBindMs', 1600) : k.p(pin, 'bindMs', 1000);
        k.moves.bind(mob, ms, 'b_perfectPin', wall ? res.at : null);
        stick(wall ? res.at : { x: mob.x, y: mob.y - 6 }, ms);
        k.fire('b_perfectPin', wall ? 'wall' : 'pin');
      },
    );
  }

  /** 화살비 한 발 적중 (ArrowRain): 화살 그물(한가운데로 끌어모아 묶음) · 이어지는 비 */
  onRainHit(mob: Mob, died: boolean, _at: Pt, center: Pt): void {
    const k = this.k;
    const snare = k.rt.rule('rainSnare');
    if (snare && !died && !k.moves.isBound(mob)) {
      k.moves.fx('b_rainSnare', center, { depth: DEPTH.FX_GROUND });
      k.moves.chainLine(mob, center, TRAIT_FX.BIND.COLOR, 220);
      k.moves.pull(mob, center, k.p(snare, 'pullTiles', 1.5), 'b_rainSnare', { stopTiles: 0.3 });
      k.g.time.delayedCall(180, () => {
        if (k.g.scene.isActive() && mob.active) k.moves.bind(mob, k.p(snare, 'bindMs', 600), 'b_rainSnare', center);
      });
      k.fire('b_rainSnare', 'snare');
    }
    const echo = k.rt.rule('rainKillEcho');
    if (echo && died) {
      const spot = { x: mob.x, y: mob.y };
      k.g.time.delayedCall(k.p(echo, 'delayMs', 250), () => {
        if (!k.g.scene.isActive()) return;
        this.skyArrow(spot, T(k.p(echo, 'radiusTiles', 1.2)), k.p(echo, 'damageMult', 0.5), 'b_rainEcho');
        k.fire('b_rainEcho', 'echo');
      });
    }
  }

  update(now: number): void {
    this.strideDust(now);
    if (this.traps.length === 0) return;
    const k = this.k;
    const r = k.rt.rule('dashTrap');
    this.traps = this.traps.filter((t) => {
      if (now >= t.until || !r) {
        this.clearTrap(t);
        return false;
      }
      const victim = k.rt.fx.inCircle(t.at.x, t.at.y, T(k.p(r, 'radiusTiles', 0.7)))[0];
      if (!victim) return true;
      // 덫 발동: 묶음 + 한 발
      k.hit(victim, k.p(r, 'damageMult', 0.4), { x: 0, y: -1 });
      if (victim.active) {
        k.moves.bind(victim, k.p(r, 'bindMs', 1200), 'b_arrowTrap', t.at);
        this.onTrap?.(victim);
      }
      k.moves.fx('b_arrowTrap', t.at, { part: 'snap', fallbacks: ['hit_bow_heavy', 'hit_bow'] });
      k.fire('b_arrowTrap', 'snap');
      this.clearTrap(t);
      return false;
    });
  }

  /** 걸으며 연사 (art §27 `b_rapidStride` 발밑 먼지): 연사하며 걷는 동안 짧게 (그림이 없으면 아무것도 안 함) */
  private strideDust(now: number): void {
    const k = this.k;
    const pl = k.g.player;
    if (!pl || now < this.strideAt || !k.rt.rule('rapidStride') || !pl.branchMoves.volleying) return;
    const v = pl.body.velocity;
    if (v.lengthSq() < 1) return;
    this.strideAt = now + TRAIT_FX.STRIDE_DUST_MS;
    k.moves.fx('b_rapidStride', pl, { depth: DEPTH.FX_GROUND, flipX: v.x < 0 });
  }

  destroy(): void {
    for (const t of this.traps) this.clearTrap(t);
    this.traps = [];
    this.onTrap = null;
  }
}
