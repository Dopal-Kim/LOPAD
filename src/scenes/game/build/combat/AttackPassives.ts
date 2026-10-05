/**
 * 57라운드 빌드 축 — 공격·이동 순간에 붙는 패시브 (BuildCombat 에서 분리, 60라운드 6-1 정리 — 동작 그대로):
 * 파쇄 연격 짧은 균열 · 깨진 거울(분신 한 번 더) · 독한 숨(술 뿜기) · 취권(휘는 돌진 베기) ·
 * 이동기 경로 효과(돌파 4 경로 베기 · 불붙은 소매 불씨 · 술바다 점화).
 */
import { BUILD_ART, BUILD_FX, TILE } from '../../../../core/Constants';
import type { PlayerAttackPayload } from '../../../../core/EventBus';
import { gameState } from '../../../../core/GameState';
import { PLAYER_DATA } from '../../../../data';
import type { ComboChangeDef } from '../../../../data/buildTypes';
import { param } from '../../../../systems/build/buildMods';
import type { Game } from '../../../Game';
import { T } from '../../shared';
import type { BuildRuntime } from '../BuildRuntime';
import { emitProc } from './common';

export class AttackPassives {
  /** 깨진 거울: 대쉬 뒤 첫 공격을 분신이 한 번 더 (이미 썼으면 true) */
  private mirrorUsed = true;
  /** 취권 연속 횟수 · 비틀 끝 */
  fistChain = 0;
  private fistStaggerUntil = -Infinity;

  constructor(
    private readonly g: Game,
    private readonly rt: BuildRuntime,
  ) {}

  private get now(): number {
    return this.g.time.now;
  }

  /** 공격 페이로드마다 (BuildCombat.onAttack 끝): 깨진 거울 · 독한 숨 · 취권 */
  onAttack(p: PlayerAttackPayload): void {
    this.mirror(p);
    this.liquorBreath(p);
    this.drunkFist(p);
  }

  /** 4타 내려찍기 끝 짧은 균열 (파쇄 연격 변화) */
  shortCrack(p: PlayerAttackPayload, C: NonNullable<ComboChangeDef['crack']>): void {
    const pl = this.g.player;
    const len = T(C.lengthTiles);
    const half = T(C.widthTiles) / 2;
    const reach = gameState.weapon.hitbox.reach;
    const x0 = pl.x + p.dirX * reach;
    const y0 = pl.y + p.dirY * reach;
    // 60라운드 계약 art §21 greatsword_cleave_crack (V 끝점 충격원 중심, 조준 방향 회전 — 판정 길이에 맞춤)
    if (!this.rt.art.lineFx(BUILD_ART.CLEAVE_COMBO_CRACK, x0, y0, p.dirX, p.dirY, len))
      this.rt.fx.lineFx(x0, y0, p.dirX, p.dirY, len, half, BUILD_FX.COLOR.CRACK);
    for (const m of this.rt.fx.inLine(x0, y0, p.dirX, p.dirY, len, half))
      this.rt.fx.damage(m, p.damageMult * C.damageMult, { dirX: p.dirX, dirY: p.dirY, kind: 'attack' });
  }

  /** 깨진 거울: 대쉬 후 windowMs 안 첫 공격을 분신이 delayMs 뒤 한 번 더 (×damageMult) */
  private mirror(p: PlayerAttackPayload): void {
    const r = this.rt.rule('mirrorClone');
    if (!r || this.mirrorUsed || this.now - this.rt.dashAt > param(r, 'windowMs')) return;
    this.mirrorUsed = true;
    const pl = this.g.player;
    const at = { x: pl.x - p.dirX * T(0.6), y: pl.y - p.dirY * T(0.6) };
    const mult = param(r, 'damageMult');
    const reach = gameState.weapon.hitbox.reach * 1.6;
    this.g.time.delayedCall(param(r, 'delayMs'), () => {
      if (!this.g.scene.isActive()) return;
      emitProc(r);
      this.rt.fx.clone(at.x, at.y);
      this.rt.fx.coneFx(at.x, at.y, p.dirX, p.dirY, reach, 120, BUILD_FX.COLOR.CLONE);
      for (const m of this.rt.fx.inCone(at.x, at.y, p.dirX, p.dirY, reach, 120))
        this.rt.fx.damage(m, p.damageMult * mult, {
          dirX: p.dirX,
          dirY: p.dirY,
          kind: p.kind === 'dashAttack' ? 'dashAttack' : 'attack',
        });
    });
    this.rt.record('mirror');
  }

  /** 독한 숨: 마시기 직후 다음 공격 1회 = 앞 원뿔 술 뿜기 (맞은 자리 웅덩이, 술불 위면 ×fireMult) */
  private liquorBreath(p: PlayerAttackPayload): void {
    const r = this.rt.rule('liquorBreath');
    if (!r || this.now >= this.rt.liquorBreathUntil) return;
    this.rt.liquorBreathUntil = -Infinity;
    const pl = this.g.player;
    const range = T(param(r, 'rangeTiles'));
    const arc = param(r, 'arcDeg', 60);
    const onFire = this.g.pools.of('structure').some((q) => q.rect.contains(pl.x, pl.y) && this.g.pools.burning(q));
    const mult = param(r, 'damageMult') * (onFire ? param(r, 'fireMult', 1) : 1);
    this.rt.fx.coneFx(pl.x, pl.y, p.dirX, p.dirY, range, arc, onFire ? BUILD_FX.COLOR.BURN : BUILD_FX.COLOR.LIQUOR);
    for (const m of this.rt.fx.inCone(pl.x, pl.y, p.dirX, p.dirY, range, arc)) {
      const c = m.body.center;
      this.rt.fx.damage(m, mult, { dirX: p.dirX, dirY: p.dirY });
      this.rt.fx.liquorPool(c.x, c.y, T(1), 6000);
    }
    emitProc(r, onFire);
    this.rt.record('liquorBreath', { onFire });
  }

  /** 취권: 취기 중 대쉬 직후 windowMs 안 공격 = 휘는 2칸 돌진 베기 (연속 chain 회, 끝나면 비틀) */
  private drunkFist(p: PlayerAttackPayload): void {
    const r = this.rt.rule('drunkFist');
    const now = this.now;
    if (!r || !this.rt.drunkActive || now < this.fistStaggerUntil) return;
    if (now - this.rt.dashAt > param(r, 'windowMs') && this.fistChain === 0) return;
    if (now - this.rt.dashAt > param(r, 'windowMs') + 900) {
      this.fistChain = 0;
      return;
    }
    const pl = this.g.player;
    const dist = T(param(r, 'lungeTiles'));
    const side = this.fistChain % 2 === 0 ? 1 : -1;
    // 휘는 궤적: 진행 방향에서 ±25° 기울인 돌진
    const a = Math.atan2(p.dirY, p.dirX) + side * 0.44;
    pl.startLunge(Math.cos(a), Math.sin(a), dist, 160, now);
    emitProc(r);
    const radius = T(param(r, 'radiusTiles', 1.2));
    const mult = param(r, 'damageMult');
    this.g.time.delayedCall(140, () => {
      if (!this.g.scene.isActive()) return;
      this.rt.fx.ring(pl.x, pl.y, radius, BUILD_FX.COLOR.DRUNK_TINT);
      for (const m of this.rt.fx.inCircle(pl.x, pl.y, radius))
        this.rt.fx.damage(m, mult, { dirX: Math.cos(a), dirY: Math.sin(a), kind: 'dashAttack' });
    });
    this.fistChain += 1;
    this.rt.dashAt = now; // 다음 연속 창
    if (this.fistChain >= param(r, 'chain', 3)) {
      this.fistChain = 0;
      this.fistStaggerUntil = now + param(r, 'staggerMs');
      pl.slowUntil(now + param(r, 'staggerMs'));
    }
    this.rt.record('drunkFist', this.fistChain);
  }

  // --- 이동기 (대쉬·그림자 걸음) ---

  onMove(x: number, y: number, dirX: number, dirY: number, kind: 'dash' | 'shadowstep', distPx?: number): void {
    const len = distPx ?? PLAYER_DATA.dash.distanceTiles * TILE;
    this.mirrorUsed = false;
    // 돌파 4: 경로 베기 1회 (×0.8)
    const trail = this.rt.rule('moveTrail');
    if (trail && len > 0) {
      const half = T(param(trail, 'widthTiles', 1)) / 2;
      this.g.time.delayedCall(kind === 'dash' ? 90 : 0, () => {
        if (!this.g.scene.isActive()) return;
        this.rt.fx.lineFx(x, y, dirX, dirY, len, half, BUILD_FX.COLOR.SPIN);
        for (const m of this.rt.fx.inLine(x, y, dirX, dirY, len, half))
          this.rt.fx.damage(m, param(trail, 'damageMult'), { dirX, dirY, kind: 'dashAttack' });
      });
    }
    // 불붙은 소매: 경로 불씨
    const sleeve = this.rt.rule('dashEmbers');
    if (sleeve && len > 0) {
      emitProc(sleeve);
      const ms = param(sleeve, 'ms');
      const l = Math.hypot(dirX, dirY) || 1;
      const steps = Math.max(1, Math.round(len / TILE));
      for (let i = 0; i <= steps; i++) {
        const px = x + ((dirX / l) * (len * i)) / steps;
        const py = y + ((dirY / l) * (len * i)) / steps;
        this.rt.fx.firePatch(px, py, TILE / 2, ms, param(sleeve, 'tickMs'), param(sleeve, 'tickMult'));
      }
    }
    // 술바다: 취기 중 대쉬가 지나간 웅덩이 점화
    if (this.rt.rule('drunkSea') && this.rt.drunkActive && len > 0) {
      const l = Math.hypot(dirX, dirY) || 1;
      for (let d = 0; d <= len; d += TILE / 2) this.g.pools.igniteAt(x + (dirX / l) * d, y + (dirY / l) * d);
    }
    this.rt.branch.onPlayerMove(kind);
  }
}
