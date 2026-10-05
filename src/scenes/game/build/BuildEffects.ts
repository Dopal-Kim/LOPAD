/**
 * 57라운드 빌드 축 월드 도우미 (씬 쪽): 범위 판정(원·원뿔·선) · 피해 · 술 웅덩이·불 웅덩이 · 빌드 투사체 · 플레이스홀더 연출.
 * 갈래 수단·세트·패시브·저주의 그림은 계약 art §21 시트(BuildArt·build/branch)가 있으면 그것, 없으면 이 윤곽으로 그린다.
 */
import Phaser from 'phaser';
import { BUILD_ART, BUILD_FX, DEPTH, TILE } from '../../../core/Constants';
import { BUILD } from '../../../data/build';
import type { Mob } from '../../../objects/Mob';
import type { Projectile, ProjectileVisual } from '../../../objects/Projectile';
import { spriteLibrary } from '../../../systems/sprites/sprites';
import { FX_ACTION, artScale, fxDrawScale } from '../../../systems/sprites/spriteDefs';
import { sheetLoopRange } from './BuildArt';
import type { Pool } from '../../../systems/hazards/LiquorPools';
import type { Game } from '../../Game';
import type { DamageKind } from '../GameCombat';

export interface BuildHitOpts {
  dirX: number;
  dirY: number;
  /** 확정 치명 */
  forceCrit?: boolean;
  tick?: boolean;
  heavy?: boolean;
  knock?: boolean;
  kind?: DamageKind;
  /** 처치 분류 (감각) — 기본 attack */
  killKind?: 'attack' | 'dashAttack' | 'parry' | 'environment';
}

const tileR = (tiles: number) => tiles * TILE;

export class BuildEffects {
  constructor(private readonly g: Game) {}

  /** 살아 있는 적 */
  mobs(): Mob[] {
    return (this.g.mobs.getChildren() as Mob[]).filter((m) => m.active);
  }

  private target(m: Mob): { x: number; y: number; r: number } {
    const b = m.body;
    return { x: b.center.x, y: b.center.y, r: Math.min(b.halfWidth, b.halfHeight) };
  }

  /** 원 (중심 x,y 반경 px) 에 걸친 적 */
  inCircle(x: number, y: number, r: number, exclude?: ReadonlySet<Mob>): Mob[] {
    return this.mobs().filter((m) => {
      if (exclude?.has(m)) return false;
      const t = this.target(m);
      return Math.hypot(t.x - x, t.y - y) <= r + t.r;
    });
  }

  /** 원뿔 (방향 ±arcDeg/2, 반경 r) */
  inCone(x: number, y: number, dirX: number, dirY: number, r: number, arcDeg: number): Mob[] {
    const len = Math.hypot(dirX, dirY) || 1;
    const ux = dirX / len;
    const uy = dirY / len;
    const half = (arcDeg * Math.PI) / 360;
    return this.mobs().filter((m) => {
      const t = this.target(m);
      const dx = t.x - x;
      const dy = t.y - y;
      const d = Math.hypot(dx, dy);
      if (d <= t.r) return true;
      if (d - t.r > r) return false;
      const ang = Math.acos(Math.max(-1, Math.min(1, (dx * ux + dy * uy) / d)));
      return ang <= half + Math.asin(Math.min(1, t.r / d));
    });
  }

  /** 선 (x0,y0 에서 방향으로 len, 반폭 half) */
  inLine(
    x0: number,
    y0: number,
    dirX: number,
    dirY: number,
    len: number,
    half: number,
    exclude?: ReadonlySet<Mob>,
  ): Mob[] {
    const l = Math.hypot(dirX, dirY) || 1;
    const ux = dirX / l;
    const uy = dirY / l;
    return this.mobs().filter((m) => {
      if (exclude?.has(m)) return false;
      const t = this.target(m);
      const dx = t.x - x0;
      const dy = t.y - y0;
      const along = dx * ux + dy * uy;
      if (along < -t.r || along > len + t.r) return false;
      return Math.abs(dx * uy - dy * ux) <= half + t.r;
    });
  }

  /** 가장 가까운 적 (exclude 빼고, maxPx 안) */
  nearest(x: number, y: number, maxPx: number, exclude?: ReadonlySet<Mob>): Mob | null {
    let best: Mob | null = null;
    let bd = maxPx;
    for (const m of this.mobs()) {
      if (exclude?.has(m)) continue;
      const d = Math.hypot(m.x - x, m.y - y);
      if (d <= bd) {
        bd = d;
        best = m;
      }
    }
    return best;
  }

  /** 공격력 × mult 피해 (치명·빌드 배율은 rollDamage) → 처치면 onKill. 반환: 처치 */
  damage(mob: Mob, mult: number, o: BuildHitOpts): boolean {
    const g = this.g;
    if (!mob.active) return false;
    const { dmg, crit } = g.combat.rollDamage(mult, Boolean(o.forceCrit), o.kind ?? 'other', mob);
    return this.raw(mob, dmg, { ...o, crit });
  }

  /** 정해진 피해 */
  raw(mob: Mob, dmg: number, o: BuildHitOpts & { crit?: boolean }): boolean {
    const g = this.g;
    if (!mob.active || dmg <= 0) return false;
    const died = g.combat.hitMob(mob, Math.max(1, Math.round(dmg)), {
      crit: Boolean(o.crit),
      dirX: o.dirX,
      dirY: o.dirY,
      ...(o.tick ? { tick: true } : {}),
      ...(o.heavy ? { heavy: true } : {}),
      ...(o.knock === false ? { knock: false } : {}),
    });
    if (died) g.progress.onKill(mob, o.killKind ?? 'attack');
    return died;
  }

  // --- 웅덩이 ---

  /** 술 웅덩이 (취기 — 반경 px, 수명 ms). 불붙으면 적에게만 술불 틱 */
  liquorPool(x: number, y: number, radiusPx: number, lifeMs: number): Pool {
    const g = this.g;
    const L = BUILD.drunk.liquorPool;
    const side = radiusPx * 2;
    const rect = new Phaser.Geom.Rectangle(x - radiusPx, y - radiusPx, side, side);
    return g.pools.add(rect, {
      owner: 'structure',
      lifeMs,
      playerSlow: L.playerSlow,
      enemySlow: L.enemySlow,
      slip: L.slip,
      fireMs: L.fireMs,
      fireTickMs: L.fireTickMs,
      firePlayerAttack: 0,
      fireMobDamage: () => Math.max(1, Math.round(g.combat.rollDamage(L.fireTickMult).dmg)),
      fireFx: 'fire_pool',
      spreadMsPerCell: L.spreadMsPerCell,
      linkGapPx: L.linkGapTiles * TILE,
      color: BUILD_FX.COLOR.LIQUOR,
      alpha: BUILD_FX.LIQUOR_ALPHA,
      sheets: this.liquorSheets(),
    });
  }

  /** 60라운드 계약 art §21 술 웅덩이 그림 (pool_liquor · pool_liquor_fire — 반경 1칸 = 64 도트) */
  private liquorSheets(): NonNullable<Parameters<Game['pools']['add']>[1]['sheets']> | undefined {
    const fx = this.g.fx;
    const def = fx.sheet(BUILD_ART.POOL_LIQUOR);
    if (!def) return undefined;
    const dots = (def as unknown as { radiusPx?: number }).radiusPx;
    return {
      pool: BUILD_ART.POOL_LIQUOR,
      fire: BUILD_ART.POOL_LIQUOR_FIRE,
      radiusPx: dots ? dots * artScale(def) : TILE,
      loop: sheetLoopRange(def),
      fireLoop: sheetLoopRange(fx.sheet(BUILD_ART.POOL_LIQUOR_FIRE)),
    };
  }

  /** 불 웅덩이 (잔불 심장·불씨): 바로 불, ms 동안 tickMs 마다 공격 × tickMult */
  firePatch(x: number, y: number, radiusPx: number, ms: number, tickMs: number, tickMult: number): Pool {
    const g = this.g;
    const side = radiusPx * 2;
    const rect = new Phaser.Geom.Rectangle(x - radiusPx, y - radiusPx, side, side);
    const pool = g.pools.add(rect, {
      owner: 'structure',
      lifeMs: ms,
      playerSlow: 0,
      enemySlow: 0,
      slip: 0,
      fireMs: ms,
      fireTickMs: tickMs,
      firePlayerAttack: 0,
      fireMobDamage: () => Math.max(1, Math.round(g.combat.rollDamage(tickMult).dmg)),
      fireFx: 'fire_pool',
      spreadMsPerCell: null,
      linkGapPx: 0,
      color: BUILD_FX.COLOR.EMBER,
      alpha: 0.2,
    });
    g.pools.ignite(pool);
    return pool;
  }

  /** (x,y) 반경 안 웅덩이 */
  poolsNear(x: number, y: number, r: number): Pool[] {
    return this.g.pools
      .of('structure')
      .filter((p) => Math.hypot(p.rect.centerX - x, p.rect.centerY - y) <= r + p.rect.width / 2);
  }

  /** 점이 웅덩이 위인가 */
  onPool(x: number, y: number): boolean {
    return this.g.pools.of('structure').some((p) => p.rect.contains(x, y));
  }

  // --- 투사체 ---

  /** 빌드 투사체 (플레이스홀더 사각형). 피해는 GameCombat.onPlayerShotHit 경로 */
  shot(
    x: number,
    y: number,
    dirX: number,
    dirY: number,
    attack: number,
    o: {
      tag: string;
      speedTiles: number;
      lifeMs: number;
      pierce?: number;
      sizePx?: number;
      crit?: boolean;
      tint?: number;
      /** 투사체 이펙트 시트 (`fx/<id>` — anchor projectile·rotate). 없거나 안 올라왔으면 플레이스홀더 사각형 */
      sprite?: string;
    },
  ): Projectile | null {
    const g = this.g;
    const shot = g.playerShots.get() as Projectile | null;
    if (!shot) return null;
    const len = Math.hypot(dirX, dirY) || 1;
    shot.launch(
      x,
      y,
      dirX / len,
      dirY / len,
      {
        speedPx: o.speedTiles * TILE,
        attack: Math.max(1, Math.round(attack)),
        size: o.sizePx ?? BUILD_FX.SHOT_SIZE_PX,
        lifeMs: o.lifeMs,
      },
      g.time.now,
      'player',
      o.pierce ?? 0,
      o.sprite ? this.shotVisual(o.sprite) : {},
    );
    shot.buildTag = o.tag;
    shot.crit = Boolean(o.crit);
    if (o.tint !== undefined) shot.setTint(o.tint);
    return shot;
  }

  /** 투사체 시트 외형 (GameCombat.fire 와 같은 규칙 — 회전·원점·루프·그리는 배율) */
  shotVisual(id: string): ProjectileVisual {
    if (!this.g.fx.has(id)) return {};
    const def = spriteLibrary.sheet(id, FX_ACTION);
    if (!def) return {};
    return {
      texture: spriteLibrary.textureKey(id, FX_ACTION),
      rotate: def.rotate !== false,
      originX: def.pivot.x / def.frameWidth,
      originY: def.pivot.y / def.frameHeight,
      anim: def.loop && def.frames > 1 ? spriteLibrary.animKey(id, FX_ACTION, 'down') : null,
      scale: fxDrawScale(def),
    };
  }

  /** 이미 나간 투사체의 외형을 바꾼다 (저격 관통 화살 — 화살 시트 대신) */
  restyle(shot: Projectile, id: string): boolean {
    const v = this.shotVisual(id);
    if (!v.texture || !this.g.textures.exists(v.texture)) return false;
    shot
      .setTexture(v.texture, 0)
      .setOrigin(v.originX ?? 0.5, v.originY ?? 0.5)
      .clearTint();
    if (v.anim && this.g.anims.exists(v.anim)) shot.play(v.anim, true);
    return true;
  }

  /**
   * 반복 타일 선 (계약 art §21 `tile: true` — bow_skypierce_line 주기 64 도트, 트림 안 함): 선 시작부터 주기마다 같은 시트를
   * 이어 깔고 진행 각도로 회전. 시트가 없으면 false
   */
  tileLine(id: string, x: number, y: number, dirX: number, dirY: number, len: number): boolean {
    const fx = this.g.fx;
    const def = fx.sheet(id);
    if (!def || !fx.has(id)) return false;
    const l = Math.hypot(dirX, dirY) || 1;
    const ux = dirX / l;
    const uy = dirY / l;
    const period = Math.max(1, def.frameWidth * fxDrawScale(def));
    const angle = Math.atan2(uy, ux);
    const n = Math.max(1, Math.ceil(len / period));
    for (let i = 0; i < n; i++)
      fx.play(id, x + ux * period * i, y + uy * period * i, { angle, depth: DEPTH.HIT_FX, hooks: i === 0 });
    return true;
  }

  // --- 플레이스홀더 연출 ---

  private fade(obj: Phaser.GameObjects.Graphics, ms: number = BUILD_FX.FADE_MS): void {
    this.g.tweens.add({ targets: obj, alpha: 0, duration: ms, onComplete: () => obj.destroy() });
  }

  ring(x: number, y: number, r: number, color: number, ms?: number): void {
    const gfx = this.g.add.graphics().setDepth(DEPTH.ATTACK);
    gfx.lineStyle(BUILD_FX.STROKE_PX, color, 0.9).strokeCircle(x, y, r);
    this.fade(gfx, ms);
  }

  coneFx(x: number, y: number, dirX: number, dirY: number, r: number, arcDeg: number, color: number): void {
    const gfx = this.g.add.graphics().setDepth(DEPTH.ATTACK);
    const a = Math.atan2(dirY, dirX);
    const h = (arcDeg * Math.PI) / 360;
    gfx.lineStyle(BUILD_FX.STROKE_PX, color, 0.9);
    gfx.beginPath();
    gfx.moveTo(x, y);
    gfx.arc(x, y, r, a - h, a + h, false);
    gfx.closePath();
    gfx.strokePath();
    this.fade(gfx);
  }

  lineFx(
    x0: number,
    y0: number,
    dirX: number,
    dirY: number,
    len: number,
    half: number,
    color: number,
    ms?: number,
  ): void {
    const gfx = this.g.add.graphics().setDepth(DEPTH.FX_GROUND + 0.01);
    gfx.setPosition(x0, y0).setRotation(Math.atan2(dirY, dirX));
    gfx.fillStyle(color, BUILD_FX.ZONE_ALPHA).fillRect(0, -half, len, half * 2);
    gfx.lineStyle(BUILD_FX.STROKE_PX, color, 0.9).strokeRect(0, -half, len, half * 2);
    this.fade(gfx, ms);
  }

  /** 오래 남는 사각 영역 표시 (달 궤적·불씨 줄) */
  zone(x: number, y: number, w: number, h: number, color: number, ms: number): void {
    const r = this.g.add.rectangle(x, y, w, h, color, BUILD_FX.ZONE_ALPHA).setDepth(DEPTH.FX_GROUND + 0.01);
    this.g.tweens.add({ targets: r, alpha: 0, duration: ms, onComplete: () => r.destroy() });
  }

  /** 그림자 분신 (플레이스홀더 — 주인공 그림 반투명 복사) */
  clone(x: number, y: number): void {
    const g = this.g;
    const p = g.player;
    const img = g.add
      .image(x, y, p.texture.key, p.frame.name)
      .setOrigin(p.originX, p.originY)
      .setScale(p.scaleX, p.scaleY)
      .setFlipX(p.flipX)
      .setTint(BUILD_FX.COLOR.CLONE)
      .setAlpha(BUILD_FX.CLONE_ALPHA)
      .setDepth(p.depth - DEPTH.OVERLAY_STEP);
    g.tweens.add({ targets: img, alpha: 0, duration: BUILD_FX.CLONE_MS, onComplete: () => img.destroy() });
  }

  /** 몸 위 영문 문구 */
  callout(text: string): void {
    const p = this.g.player;
    this.g.feedback.callouts.show(p.x, p.body.top, text);
  }
}

export { tileR };
