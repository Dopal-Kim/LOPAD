/**
 * 보스방 술 웅덩이 (BossArena 에서 분리 — 61 단계 5 길이 정리): 술 뿌리기 줄 → 웅덩이 칸 · 술 방울 그림 · 웅덩이 수치(보스 소유).
 * 술통 자국·깨짐 웅덩이·불붙은 술이 같은 칸 규칙(`puddleCell`)을 쓴다.
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH, TILE } from '../../core/Constants';
import type { BossArenaParams } from '../../data/types';
import type { Vec } from '../../objects/boss/types';
import type { FxPool } from '../fx/fx';
import { cellsAlong } from '../hazards/liquorNet';
import type { LiquorPools, PoolSpec } from '../hazards/LiquorPools';
import type { TileWorld } from '../../world/TileWorld';

/** 웅덩이 불 수치 (fireSpill 과 같은 이름) */
export interface PoolFire {
  fireMs: number;
  fireTickMs: number;
  firePlayerAttack: number;
  spreadMsPerCell: number;
}

export class BossLiquor {
  constructor(
    private readonly host: { scene: Phaser.Scene; world: TileWorld; pools: LiquorPools; fx: FxPool },
    private readonly L: BossArenaParams['liquor'],
  ) {}

  private get now(): number {
    return this.host.scene.time.now;
  }

  /** 술 뿌리기: 점 목록을 따라 웅덩이 칸 + 술 방울 그림 (from = 잔 마구리, 없으면 첫 점) */
  spill(points: readonly Vec[], p: PoolFire & { puddleMs: number }, from?: Vec): void {
    for (const c of cellsAlong(points, TILE / 2, TILE)) this.puddleCell(c.tx, c.ty, p.puddleMs, p);
    this.globs(points, from ?? points[0]);
  }

  /** 술 방울 (아트 boss1_liquor_glob): 잔 마구리(없으면 첫 점)에서 줄 위 몇 군데로 날아간다 (그림만) */
  private globs(points: readonly Vec[], from: Vec): void {
    const id = BOSS_FX.SHEETS.GLOB;
    const H = this.host;
    if (!H.fx.has(id) || points.length < 2) return;
    const G = BOSS_FX.GLOBS;
    for (let i = 0; i < G.COUNT; i++) {
      const to = points[Math.round(((i + 1) / G.COUNT) * (points.length - 1))];
      const ms = (G.FLIGHT_MS * (i + 1)) / G.COUNT;
      const pos = {
        x: from.x,
        y: from.y,
        active: true,
        depth: DEPTH.PROJECTILE,
        rotation: Math.atan2(to.y - from.y, to.x - from.x),
      };
      H.fx.play(id, from.x, from.y, { follow: pos, durationMs: ms, depth: DEPTH.PROJECTILE, angle: pos.rotation });
      H.scene.tweens.add({ targets: pos, x: to.x, y: to.y, duration: ms, onComplete: () => (pos.active = false) });
    }
  }

  private spec(p: PoolFire): Omit<PoolSpec, 'lifeMs'> {
    const L = this.L;
    return {
      owner: 'boss',
      playerSlow: L.playerSlow,
      enemySlow: 0,
      slip: L.slip,
      fireMs: p.fireMs,
      fireTickMs: p.fireTickMs,
      firePlayerAttack: p.firePlayerAttack,
      // 보스가 쏟은 술의 불은 보스·적을 다치게 하지 않는다 (임시값 — 보고서 질문)
      fireMobDamage: null,
      fireFx: 'fire_pool',
      spreadMsPerCell: p.spreadMsPerCell,
      linkGapPx: L.linkGapPx,
      color: Phaser.Display.Color.HexStringToColor(L.color).color,
      alpha: L.alpha,
    };
  }

  /** 칸 (tx, ty) 에 보스 웅덩이 — 걸을 수 없는 칸이면 없음, 이미 있으면 수명만 늘린다 */
  puddleCell(tx: number, ty: number, lifeMs: number, fire: PoolFire): void {
    const size = this.L.cellTiles * TILE;
    const x = tx * TILE + TILE / 2;
    const y = ty * TILE + TILE / 2;
    if (!this.host.world.isWalkableAt(x, y)) return;
    const pools = this.host.pools;
    const now = this.now;
    for (const p of pools.pools)
      if (p.spec.owner === 'boss' && p.rect.contains(x, y)) {
        if (p.fireUntil === 0) p.until = Math.max(p.until, now + lifeMs);
        return;
      }
    pools.add(new Phaser.Geom.Rectangle(x - size / 2, y - size / 2, size, size), { ...this.spec(fire), lifeMs });
  }
}
