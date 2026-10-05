/**
 * 57라운드 빌드 축 — 투사체 규칙 (BuildCombat 에서 분리, 60라운드 6-1 정리 — 동작 그대로, BowShots · GameCombat.onPlayerShotHit):
 * 원격 2·4 사거리·속도·관통 · 무한 관통 피해 · 원격 6 적중 분열 · 흩어진 촉(끝에서 2발).
 */
import { TILE } from '../../../../core/Constants';
import type { Mob } from '../../../../objects/Mob';
import type { Projectile } from '../../../../objects/Projectile';
import { param } from '../../../../systems/build/buildMods';
import type { Game } from '../../../Game';
import type { BuildCombat } from '../BuildCombat';
import type { BuildRuntime } from '../BuildRuntime';

export class ShotRules {
  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
    private readonly combat: BuildCombat,
  ) {}

  /** 화살·빌드 투사체 발사 배율: 사거리(수명)·속도·관통 (원격 2·4, 긴 시위) */
  shotMods(): { speedMult: number; lifeMult: number; pierceAdd: number } {
    return {
      speedMult: 1 + this.rt.stat('projectileSpeedMult'),
      lifeMult: (1 + this.rt.stat('projectileRangeMult')) / (1 + this.rt.stat('projectileSpeedMult')),
      pierceAdd: this.rt.stat('pierceAdd'),
    };
  }

  /** 화살 하나가 나감 — 끝날 때 흩어진 촉 */
  onShotSpawn(shot: Projectile): void {
    if (this.rt.rule('shotSplitAtEnd') && !shot.buildTag) shot.onEnd = (s) => this.splitAtEnd(s);
  }

  /** 투사체 적중 배율 (대상 배율 + 무한 관통이면 원격 4 피해 +15%) · 확정 치명 */
  shotBonus(shot: Projectile, mob: Mob): { mult: number; forceCrit: boolean } {
    let mult = this.combat.damageMultFor(mob);
    if (shot.pierceLeft === Infinity) mult *= 1 + this.rt.stat('pierceDamageAdd');
    return { mult, forceCrit: this.combat.forceCritOn(mob) };
  }

  afterShot(shot: Projectile, mob: Mob, crit: boolean, died: boolean): void {
    const v = shot.body.velocity;
    if (crit && !died) this.combat.crackOnCrit(mob);
    if (!died) this.combat.onHitCommon(mob, v.x, v.y, this.rt.isStrongShot(shot));
    // 원격 6: 적중 시 확률 분열 (분열·파편은 다시 분열하지 않음)
    const split = this.rt.rule('projectileSplit');
    if (split && !shot.buildTag && this.g.rng.chance(param(split, 'chance'))) {
      const n = param(split, 'count', 2);
      const spread = (param(split, 'spreadDeg', 30) * Math.PI) / 180;
      const base = Math.atan2(v.y, v.x);
      const speed = v.length() / TILE;
      for (let i = 0; i < n; i++) {
        const a = base + (n === 1 ? 0 : (i / (n - 1) - 0.5) * spread);
        const s = this.rt.fx.shot(shot.x, shot.y, Math.cos(a), Math.sin(a), shot.attack * param(split, 'damageMult'), {
          tag: 'split',
          speedTiles: speed || 10,
          lifeMs: 500,
        });
        s?.registerHit(mob);
      }
    }
  }

  /** 흩어진 촉: 화살이 벽·사거리 끝에서 2발로 */
  private splitAtEnd(s: Projectile): void {
    const r = this.rt.rule('shotSplitAtEnd');
    if (!r) return;
    const v = s.body.velocity;
    const base = Math.atan2(v.y, v.x) + Math.PI;
    const spread = (param(r, 'spreadDeg', 50) * Math.PI) / 180;
    const n = param(r, 'count', 2);
    for (let i = 0; i < n; i++) {
      const a = base + (i / Math.max(1, n - 1) - 0.5) * spread;
      this.rt.fx.shot(
        s.x - Math.cos(base) * 2,
        s.y - Math.sin(base) * 2,
        Math.cos(a),
        Math.sin(a),
        s.attack * param(r, 'damageMult'),
        {
          tag: 'split',
          speedTiles: 9,
          lifeMs: 450,
        },
      );
    }
  }
}
