/**
 * 술 웅덩이 · 불바다 (47라운드 1-1 독주 술통 웅덩이 구현을 54라운드 Q3 '불붙은 술'과 함께 쓰도록 분리).
 * 씬마다 하나 — 구조물(StrikeKinds)과 보스방(BossArena)이 같은 목록에 웅덩이를 놓는다.
 * - 웅덩이: 플레이어 감속(playerSlow)·미끄러움(slip), 적 감속(enemySlow — 보스 제외). 수명 lifeMs
 * - 불: fireMs 동안 fireTickMs 마다 플레이어 firePlayerAttack · 적(fireMobDamage 가 있으면) 틱 피해. 불이 꺼지면 웅덩이도 사라짐
 * - 번짐(spreadMsPerCell 이 있는 웅덩이만): 불붙으면 연결된(틈 linkGapPx 이하) 웅덩이에 칸마다 그만큼 늦게 옮겨 붙는다.
 *   옮겨 붙기 전 불씨가 출발 칸에서 다음 칸으로 달려가 방향·속도가 보인다(도화선).
 * 구조물 웅덩이(spread 없음)는 47라운드 동작 그대로다.
 * 54라운드 Q26: 불 그림은 라이트맵 위 고정 층이 아니라 **발 기준 앞뒤 정렬** — 그림 피벗(웅덩이 중심) y 의 `entityDepth` 로
 * 캐릭터 뒤 불은 가려지고 앞 불은 위에 그린다(구조물·보스방 같은 규칙). 어둠 속 밝기는 시트 광원(라이트맵 광원)이 낸다.
 */
import Phaser from 'phaser';
import { BOSS_FX, DEPTH, STRUCTURE_FX, entityDepth } from '../../core/Constants';
import { EventBus, Events, type PoolIgnitedPayload } from '../../core/EventBus';
import type { Mob } from '../../objects/Mob';
import type { FxPool } from '../fx/fx';
import { lightRegistryOf, type LightSource } from '../lighting/lightRegistry';
import { linked } from './liquorNet';

export interface PoolSpec {
  owner: 'structure' | 'boss';
  lifeMs: number;
  playerSlow: number;
  enemySlow: number;
  /** 미끄러움 0..1 (0 = 없음) */
  slip: number;
  fireMs: number;
  fireTickMs: number;
  firePlayerAttack: number;
  /** 불이 적에게 주는 틱 피해 (null = 적은 안 다침) */
  fireMobDamage: (() => number) | null;
  fireFx: string;
  /** 칸마다 번지는 지연 ms (null = 번지지 않음) · 연결 틈 px */
  spreadMsPerCell: number | null;
  linkGapPx: number;
  color: number;
  alpha: number;
  /** 불붙을 때 (번져서 붙은 것이면 viaSpread) */
  onIgnite?: (p: Pool, viaSpread: boolean) => void;
  /**
   * 60라운드 계약 art §21 취기 술 웅덩이 그림: 웅덩이 `pool_liquor`(퍼짐 → 루프 → 마름) · 불 `pool_liquor_fire`(같은 피벗으로 교체,
   * 점화 → 루프 → 꺼짐). radiusPx = 그림 반경(월드 px — 시트 radiusPx 도트 × 배율). 있으면 점화 때 POOL_IGNITED (음향 drunk_ignite)
   */
  sheets?: {
    pool: string;
    fire: string;
    radiusPx: number;
    loop: readonly [number, number] | undefined;
    fireLoop: readonly [number, number] | undefined;
  };
}

export interface Pool {
  readonly rect: Phaser.Geom.Rectangle;
  readonly spec: PoolSpec;
  until: number;
  fireUntil: number;
  nextTick: number;
  /** 번져서 불붙을 예정 시각 (0 = 없음) · 출발 칸 */
  igniteAt: number;
  igniteFrom: { x: number; y: number; at: number } | null;
  gfx: Phaser.GameObjects.Rectangle;
  fireGfx: Phaser.GameObjects.Rectangle | null;
  fireFx: ReturnType<FxPool['play']>[];
  /** 60라운드: 웅덩이 그림 (sheets.pool) */
  poolFx: ReturnType<FxPool['play']>;
  ember: Phaser.GameObjects.Arc | null;
  light: LightSource | null;
}

export interface LiquorHost {
  scene: Phaser.Scene;
  player: {
    body: { center: { x: number; y: number } };
    envSpeedMult: number;
    envSlip: number;
    takeHit(attack: number, time: number): unknown;
  };
  mobs: Phaser.Physics.Arcade.Group;
  fx: FxPool;
  hitMob(m: Mob, dmg: number, o: { crit: boolean; dirX: number; dirY: number; tick?: boolean }): boolean;
  onKill(m: Mob, kind: 'environment'): void;
}

/** 47라운드 구조물 불 이펙트 배치: 48×24 시트로 3×3 타일을 덮기 — y-10 / y+10 두 장 (아트 pivotNote) */
const FIRE_FX_OFFSET_Y = 10;
/** 1칸 웅덩이 불 이펙트 배율 (3칸 시트를 1칸 크기로 — 임시) */
const CELL_FIRE_SCALE = 0.5;
/** 큰 웅덩이(이 폭 이상, 타일 2칸 초과)면 47라운드 두 장 배치 */
const BIG_POOL_PX = 40;

const cellOf = (r: Phaser.Geom.Rectangle) => ({ x: r.x, y: r.y, w: r.width, h: r.height });

export class LiquorPools {
  pools: Pool[] = [];
  private mobsSlowed = false;

  constructor(private readonly host: LiquorHost) {}

  private get now(): number {
    return this.host.scene.time.now;
  }

  /** 웅덩이 추가 (rect 는 월드 사각형) */
  add(rect: Phaser.Geom.Rectangle, spec: PoolSpec, time = this.now): Pool {
    const gfx = this.host.scene.add
      .rectangle(rect.centerX, rect.centerY, rect.width, rect.height, spec.color, spec.alpha)
      .setDepth(STRUCTURE_FX.FLOOR_DEPTH);
    const p: Pool = {
      rect,
      spec,
      until: time + spec.lifeMs,
      fireUntil: 0,
      nextTick: 0,
      igniteAt: 0,
      igniteFrom: null,
      gfx,
      fireGfx: null,
      fireFx: [],
      poolFx: null,
      ember: null,
      light: null,
    };
    const sh = spec.sheets;
    if (sh && this.host.fx.has(sh.pool)) {
      p.poolFx = this.host.fx.play(sh.pool, rect.centerX, rect.centerY, {
        depth: STRUCTURE_FX.FLOOR_DEPTH,
        belowLighting: true,
        durationMs: spec.lifeMs,
        hooks: false,
        scaleMult: sh.radiusPx > 0 ? rect.width / 2 / sh.radiusPx : 1,
        ...(sh.loop ? { loopRange: sh.loop } : {}),
      });
      if (p.poolFx) gfx.setAlpha(0);
    }
    this.pools.push(p);
    return p;
  }

  burning(p: Pool, time = this.now): boolean {
    return p.fireUntil > 0 && time < p.fireUntil;
  }

  /** 불붙이기 (이미 붙었으면 무시) */
  ignite(p: Pool, viaSpread = false): void {
    if (p.fireUntil !== 0) return;
    const now = this.now;
    const s = p.spec;
    p.igniteAt = 0;
    p.igniteFrom = null;
    p.ember?.destroy();
    p.ember = null;
    p.fireUntil = now + s.fireMs;
    p.until = Math.max(p.until, p.fireUntil);
    p.nextTick = now + s.fireTickMs;
    this.drawFire(p);
    s.onIgnite?.(p, viaSpread);
    if (s.sheets)
      EventBus.emit(Events.POOL_IGNITED, { x: p.rect.centerX, y: p.rect.centerY } satisfies PoolIgnitedPayload);
    if (s.spreadMsPerCell !== null) this.spreadFrom(p, now);
  }

  /** 사각형에 닿는 웅덩이에 불 (불붙은 무기 베기 등). 하나라도 붙였으면 true */
  igniteIn(r: Phaser.Geom.Rectangle): boolean {
    let any = false;
    for (const p of this.pools)
      if (p.fireUntil === 0 && Phaser.Geom.Intersects.RectangleToRectangle(r, p.rect)) {
        this.ignite(p);
        any = true;
      }
    return any;
  }

  /** 점을 덮는 웅덩이에 불 (불화살·횃불). 하나라도 붙였으면 true */
  igniteAt(x: number, y: number): boolean {
    let any = false;
    for (const p of this.pools)
      if (p.fireUntil === 0 && p.rect.contains(x, y)) {
        this.ignite(p);
        any = true;
      }
    return any;
  }

  /** 가장 가까운 웅덩이 (radiusPx 안) */
  nearest(x: number, y: number, radiusPx: number): Pool | null {
    let best: Pool | null = null;
    let bd = radiusPx;
    for (const p of this.pools) {
      const d = Math.hypot(p.rect.centerX - x, p.rect.centerY - y);
      if (d <= bd) {
        bd = d;
        best = p;
      }
    }
    return best;
  }

  /** 연결된 웅덩이에 한 칸씩 늦게 옮겨 붙는다 (불씨가 출발 칸 → 다음 칸으로 달린다) */
  private spreadFrom(src: Pool, now: number): void {
    const ms = src.spec.spreadMsPerCell ?? 0;
    for (const p of this.pools) {
      if (p === src || p.fireUntil !== 0 || p.igniteAt !== 0) continue;
      if (!linked(cellOf(src.rect), cellOf(p.rect), Math.max(src.spec.linkGapPx, p.spec.linkGapPx))) continue;
      p.igniteAt = now + ms;
      p.igniteFrom = { x: src.rect.centerX, y: src.rect.centerY, at: now };
      const E = BOSS_FX.EMBER;
      p.ember = this.host.scene.add
        .circle(src.rect.centerX, src.rect.centerY, E.R, E.COLOR, 1)
        .setDepth(DEPTH.FX_GROUND + 0.01);
    }
  }

  private drawFire(p: Pool): void {
    const fx = this.host.fx;
    const s = p.spec;
    // 60라운드: 취기 술 웅덩이는 같은 피벗의 pool_liquor_fire 로 교체
    const sh = s.sheets;
    if (sh && p.poolFx && fx.has(sh.fire)) {
      fx.stop(p.poolFx, 0, false);
      p.poolFx = null;
      p.fireFx.push(
        fx.play(sh.fire, p.rect.centerX, p.rect.centerY, {
          depth: entityDepth(p.rect.centerY),
          belowLighting: true,
          durationMs: s.fireMs,
          scaleMult: sh.radiusPx > 0 ? p.rect.width / 2 / sh.radiusPx : 1,
          ...(sh.fireLoop ? { loopRange: sh.fireLoop } : {}),
        }),
      );
      return;
    }
    if (fx.has(s.fireFx)) {
      // 발 기준 앞뒤 정렬 (Q26): 깊이 = 그 장의 피벗 y (라이트맵 아래 — 빛은 시트 광원)
      const at = (y: number, durationMs: number, scaleMult?: number) =>
        fx.play(s.fireFx, p.rect.centerX, y, {
          depth: entityDepth(y),
          belowLighting: true,
          durationMs,
          ...(scaleMult === undefined ? {} : { scaleMult }),
        });
      if (p.rect.width >= BIG_POOL_PX) {
        p.fireFx.push(at(p.rect.centerY - FIRE_FX_OFFSET_Y, s.fireMs));
        const second = fx.sheet(s.fireFx)?.frameDurationsMs?.[0] ?? 110;
        this.host.scene.time.delayedCall(second, () => {
          if (p.fireUntil > this.now)
            p.fireFx.push(at(p.rect.centerY + FIRE_FX_OFFSET_Y, Math.max(0, p.fireUntil - this.now)));
        });
      } else p.fireFx.push(at(p.rect.centerY, s.fireMs, CELL_FIRE_SCALE));
      return;
    }
    p.fireGfx = this.host.scene.add
      .rectangle(
        p.rect.centerX,
        p.rect.centerY,
        p.rect.width,
        p.rect.height,
        STRUCTURE_FX.FIRE_COLOR,
        STRUCTURE_FX.FIRE_ALPHA,
      )
      .setDepth(STRUCTURE_FX.FLOOR_DEPTH + 0.01);
    // 시트가 없으면 광원도 직접 (보스 웅덩이 — 어둠 속 광원, Q8)
    if (s.owner === 'boss')
      p.light = lightRegistryOf(this.host.scene).add(BOSS_FX.FIRE_LIGHT, {
        x: p.rect.centerX,
        y: p.rect.centerY,
        until: p.fireUntil,
        now: this.now,
      });
  }

  /** 매 프레임: 번짐 · 감속·미끄러움 · 불 틱 · 만료 */
  update(time: number): void {
    const P = this.host.player;
    if (this.pools.length === 0) {
      if (this.mobsSlowed) {
        for (const ch of this.host.mobs.getChildren()) (ch as Mob).speedMult = 1;
        this.mobsSlowed = false;
      }
      P.envSpeedMult = 1;
      P.envSlip = 0;
      return;
    }
    // 번짐: 불씨가 출발 칸에서 이 칸으로 달려와 닿으면 불
    for (const p of this.pools) {
      if (p.igniteAt === 0) continue;
      const f = p.igniteFrom;
      if (f && p.ember) {
        const t = Math.min(1, (time - f.at) / Math.max(1, p.igniteAt - f.at));
        p.ember.setPosition(f.x + (p.rect.centerX - f.x) * t, f.y + (p.rect.centerY - f.y) * t);
      }
      if (time >= p.igniteAt) this.ignite(p, true);
    }
    const pc = P.body.center;
    let slow = 0;
    let slip = 0;
    for (const p of this.pools)
      if (p.rect.contains(pc.x, pc.y)) {
        slow = Math.max(slow, p.spec.playerSlow);
        slip = Math.max(slip, p.spec.slip);
      }
    P.envSpeedMult = 1 - slow;
    P.envSlip = slip;
    for (const ch of this.host.mobs.getChildren()) {
      const m = ch as Mob;
      if (!m.active) continue;
      let ms = 0;
      for (const p of this.pools)
        if (p.rect.contains(m.body.center.x, m.body.center.y)) ms = Math.max(ms, p.spec.enemySlow);
      m.speedMult = 1 - ms;
    }
    this.mobsSlowed = true;
    // 불바다 틱 (플레이어 피해는 무적 시간이 겹침을 막는다)
    for (const p of this.pools) {
      if (p.fireUntil === 0 || time >= p.fireUntil || time < p.nextTick) continue;
      p.nextTick = time + p.spec.fireTickMs;
      const dmgOf = p.spec.fireMobDamage;
      if (dmgOf) {
        const dmg = dmgOf();
        for (const ch of [...this.host.mobs.getChildren()]) {
          const m = ch as Mob;
          if (!m.active || !p.rect.contains(m.body.center.x, m.body.center.y)) continue;
          if (this.host.hitMob(m, dmg, { crit: false, dirX: 0, dirY: 0, tick: true }))
            this.host.onKill(m, 'environment');
        }
      }
      if (p.rect.contains(pc.x, pc.y) && p.spec.firePlayerAttack > 0) P.takeHit(p.spec.firePlayerAttack, time);
    }
    const expired = (p: Pool) => time >= p.until || (p.fireUntil > 0 && time >= p.fireUntil);
    for (const p of this.pools) if (expired(p)) this.release(p);
    this.pools = this.pools.filter((p) => !expired(p));
  }

  /** 주인(구조물·보스)의 웅덩이 */
  of(owner: PoolSpec['owner']): Pool[] {
    return this.pools.filter((p) => p.spec.owner === owner);
  }

  private release(p: Pool): void {
    p.gfx.destroy();
    if (p.poolFx) this.host.fx.finish(p.poolFx);
    p.fireGfx?.destroy();
    p.ember?.destroy();
    if (p.light) lightRegistryOf(this.host.scene).remove(p.light);
    for (const h of p.fireFx) if (this.host.fx.isActive(h)) this.host.fx.finish(h);
  }

  destroy(): void {
    for (const p of this.pools) this.release(p);
    this.pools = [];
  }
}
