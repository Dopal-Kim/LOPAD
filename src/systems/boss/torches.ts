/**
 * 54라운드 Q3 불붙은 술 — 날아가는 횃불 (BossArena 에서 분리, 54라운드 2차 정리). 포물선으로 flightMs 동안 날아가 to 에 떨어지면
 * onLand(to) 를 부른다(웅덩이 점화는 방이). 그림: 아트 boss1_torch(회전 시트, 광원은 시트) → 임시 원 + 불씨 광원
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH } from '../../core/Constants';
import type { Vec } from '../../objects/boss/types';
import type { FxHandle, FxPool } from '../fx/fx';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';

interface Torch {
  from: Vec;
  to: Vec;
  at: number;
  ms: number;
  fx: FxHandle | null;
  view: Phaser.GameObjects.Arc | null;
  light: LightSource | null;
  pos: { x: number; y: number; active: boolean; depth: number; rotation: number };
}

export class TorchFlights {
  private list: Torch[] = [];

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: FxPool,
    private readonly onLand: (to: Vec) => void,
  ) {}

  get count(): number {
    return this.list.length;
  }

  /** from 에서 to 로 (출발 = 보스 throw_torch 손끝 — 패턴이 넘긴다) */
  throw(from: Vec, to: Vec, flightMs: number, now: number): void {
    const T = BOSS_FX.TORCH;
    const pos = { x: from.x, y: from.y, active: true, depth: DEPTH.PROJECTILE, rotation: 0 };
    const fxId = BOSS_FX.SHEETS.TORCH;
    const fx = this.fx.has(fxId)
      ? this.fx.play(fxId, from.x, from.y, { follow: pos, durationMs: flightMs + 100, depth: DEPTH.PROJECTILE })
      : null;
    const view = fx ? null : this.scene.add.circle(from.x, from.y, T.R, T.COLOR, 1).setDepth(DEPTH.PROJECTILE);
    const light = view
      ? lightRegistryOf(this.scene).add(BOSS_FX.EMBER.LIGHT, { x: from.x, y: from.y, anchor: view })
      : null;
    this.list.push({ from: { ...from }, to: { ...to }, at: now, ms: Math.max(1, flightMs), fx, view, light, pos });
  }

  update(time: number): void {
    const T = BOSS_FX.TORCH;
    const rotate = Boolean(this.fx.sheet(BOSS_FX.SHEETS.TORCH)?.rotate);
    for (const t of this.list) {
      const k = Math.min(1, (time - t.at) / t.ms);
      const lift = Math.sin(k * Math.PI) * T.ARC_PX;
      const px = t.from.x + (t.to.x - t.from.x) * k;
      const py = t.from.y + (t.to.y - t.from.y) * k - lift;
      // 진행 각도 (포물선 접선) — 회전 시트(rotate)면 그대로
      const ang = Math.atan2(t.to.y - t.from.y - Math.cos(k * Math.PI) * Math.PI * T.ARC_PX, t.to.x - t.from.x);
      t.pos.x = px;
      t.pos.y = py;
      t.pos.rotation = ang;
      t.view?.setPosition(px, py);
      if (t.fx && rotate) t.fx.sprite.setRotation(ang);
      if (k < 1) continue;
      this.onLand(t.to);
      this.end(t);
    }
    this.list = this.list.filter((t) => t.pos.active);
  }

  private end(t: Torch): void {
    t.pos.active = false;
    if (t.fx && this.fx.isActive(t.fx)) this.fx.stop(t.fx);
    t.view?.destroy();
    lightRegistryOf(this.scene).remove(t.light);
  }

  destroy(): void {
    for (const t of this.list) this.end(t);
    this.list = [];
  }
}
