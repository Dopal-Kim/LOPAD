/**
 * 61 G 활 개성·셋째 갈래 '유성' 길 규칙: 코앞 사격 · 튕기는 화살 · 꿰어 박기 · 되튀는 화살 · 낙하 사격 · 구르며 장전 · 화살 그물 ·
 * 이어지는 비 / 혜성(완벽 놓기 화살이 꿰뚫으며 터짐). 유성 1차(하늘 화살)·성우(자동 화살비·넓은 화살비)·별 표적·술별·걸으며 연사는
 * BowBranch·ArrowRain·BranchMoves 가 실행한다.
 */
import { BUILD_ART, BUILD_FX, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload } from '../../../../core/EventBus';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { T, type Pt, type RuleKit } from './RuleKit';

export class BowRules {
  constructor(private readonly k: RuleKit) {}

  /** 낙하 사격: 대쉬 사격이 솟았다가 앞쪽에 세 발로 떨어진다 */
  onAttack(p: PlayerAttackPayload): void {
    const k = this.k;
    const r = k.rt.rule('dashRain');
    if (!r || p.kind !== 'dashAttack') return;
    const pl = k.g.player;
    const l = Math.hypot(p.dirX, p.dirY) || 1;
    const dir = { x: p.dirX / l, y: p.dirY / l };
    const n = k.p(r, 'drops', 3);
    const ahead = T(k.p(r, 'aheadTiles', 3));
    const base = { x: pl.x, y: pl.y };
    for (let i = 0; i < n; i++) {
      const side = (i - (n - 1) / 2) * TILE * 0.9;
      const at = { x: base.x + dir.x * ahead - dir.y * side, y: base.y + dir.y * ahead + dir.x * side };
      k.g.time.delayedCall(k.p(r, 'delayMs', 350) + i * 90, () => {
        if (!k.g.scene.isActive()) return;
        const rad = T(k.p(r, 'radiusTiles', 1));
        if (!k.rt.art.once(BUILD_ART.METEOR_ARROW, at.x, at.y, { scaleMult: PLAYER_RENDER_SCALE * 0.7 }))
          k.rt.fx.ring(at.x, at.y, rad, BUILD_FX.COLOR.METEOR, 200);
        for (const m of k.rt.fx.inCircle(at.x, at.y, rad)) k.hit(m, k.p(r, 'damageMult', 0.6), { x: 0, y: 1 });
      });
    }
    k.fire('b_dropShot', 'rain');
  }

  /** 구르며 장전: 화살이 바닥났을 때 대쉬 → 장전 끝 */
  onDash(): void {
    const k = this.k;
    if (!k.rt.rule('dashReload')) return;
    const res = k.g.player.resource;
    if (res?.kind !== 'ammo' || (res.value > 0 && !res.reloading)) return;
    res.refresh(0);
    k.fire('b_rollReload', 'reload');
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
    k.fire('b_fullBounce', 'bounce');
  }

  onShotHit(shot: Projectile, mob: Mob, died: boolean): void {
    const k = this.k;
    const own = !shot.buildTag;
    const perfect = k.rt.isPerfectShot(shot);
    // 코앞 사격: 가까이 붙은 적은 밀쳐낸다
    const pb = k.rt.rule('pointBlankShove');
    if (pb && own && !died && Math.hypot(mob.x - shot.originX, mob.y - shot.originY) <= T(k.p(pb, 'rangeTiles', 2))) {
      const v = shot.body.velocity;
      k.push(mob, { x: v.x, y: v.y }, k.p(pb, 'knockTiles', 1.5));
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
        k.fire('b_ricochet', 'bounce');
      }
    }
    // 꿰어 박기: 완벽 놓기 화살에 맞은 적은 박혀 멈춘다
    const pin = k.rt.rule('perfectPin');
    if (pin && perfect && !died) {
      k.stun(mob, k.p(pin, 'stunMs', 900));
      k.fire('b_perfectPin', 'pin');
    }
    // 혜성: 완벽 놓기 화살이 맞을 때마다 터진다
    const comet = k.rt.rule('comet');
    if (comet && perfect) {
      const c = { x: mob.body.center.x, y: mob.body.center.y };
      const r = T(k.p(comet, 'burstRadiusTiles', 1));
      k.rt.fx.ring(c.x, c.y, r, BUILD_FX.COLOR.METEOR, 200);
      for (const m of k.rt.fx.inCircle(c.x, c.y, r, new Set([mob])))
        k.hit(m, k.p(comet, 'burstMult', 0.5), { x: m.x - c.x, y: m.y - c.y });
      k.fire('comet', 'burst');
    }
  }

  /** 화살비 한 발 적중 (ArrowRain): 화살 그물 · 이어지는 비 */
  onRainHit(mob: Mob, died: boolean, at: Pt): void {
    const k = this.k;
    const snare = k.rt.rule('rainSnare');
    if (snare && !died) k.stun(mob, k.p(snare, 'stunMs', 500));
    const echo = k.rt.rule('rainKillEcho');
    if (echo && died) {
      const spot = { x: mob.x, y: mob.y };
      k.g.time.delayedCall(k.p(echo, 'delayMs', 250), () => {
        if (!k.g.scene.isActive()) return;
        const r = T(k.p(echo, 'radiusTiles', 1.2));
        if (!k.rt.art.once(BUILD_ART.METEOR_ARROW, spot.x, spot.y, { scaleMult: PLAYER_RENDER_SCALE * 0.7 }))
          k.rt.fx.ring(spot.x, spot.y, r, BUILD_FX.COLOR.METEOR, 200);
        for (const m of k.rt.fx.inCircle(spot.x, spot.y, r)) k.hit(m, k.p(echo, 'damageMult', 0.5), { x: 0, y: 1 });
        k.fire('b_rainEcho', 'echo');
      });
    }
    void at;
  }

  update(_now: number): void {}
}
