/**
 * 타격형·통과형 구조물과 그 환경 효과: 짐(C1) · 독주 술통(1-1, 구르기·웅덩이·불바다) · 증류 화로(1-2, 불붙은 무기·불화살·화상) ·
 * 숨은 벽(1-6, 저장고) · 판돈 종(2-4). 근접 판정·대쉬·화살·밀쳐내기가 여기로 들어온다.
 */
import Phaser from 'phaser';
import { STRUCTURE_FX, TILE } from '../../../core/Constants';
import { EventBus, Events, type StructureBellPayload, type StructureFirePayload } from '../../../core/EventBus';
import { gameState } from '../../../core/GameState';
import type { UiStructureResult } from '../../../contract/ui';
import type { Mob } from '../../../objects/Mob';
import type { Projectile } from '../../../objects/Projectile';
import type { FxPool } from '../../fx';
import { STRUCTURE_RULES, num, structureDef, txt, type StructureDef } from '../data';
import { stakeMods } from '../rules';
import type { Inst, StructureCore } from '../core';

interface Puddle {
  rect: Phaser.Geom.Rectangle;
  until: number;
  fireUntil: number;
  nextTick: number;
  gfx: Phaser.GameObjects.Rectangle;
  fireGfx: Phaser.GameObjects.Rectangle | null;
  fireFx: ReturnType<FxPool['play']>[];
}

interface Burn {
  ticks: number;
  nextAt: number;
  dmg: number;
}

export class StrikeKinds {
  puddles: Puddle[] = [];
  readonly burns = new Map<Mob, Burn>();
  private mobsSlowed = false;

  constructor(private readonly c: StructureCore) {}

  update(time: number, delta: number): void {
    this.updateRolling(time, delta);
    this.updatePuddles(time);
    this.updateBurns(time);
  }

  // --- 전투 훅 ---

  /** 근접 판정 사각형 (베기·대쉬 공격·충격파): 타격형 구조물 + 화로 점화 + 불붙은 무기로 웅덩이 점화 */
  onMeleeSwing(x: number, y: number, w: number, h: number, dirX: number, dirY: number): void {
    const r = new Phaser.Geom.Rectangle(x - w / 2, y - h / 2, w, h);
    this.hitRect(r, dirX, dirY);
    if (this.touchesFlame(r)) this.igniteWeapon('weapon');
    if (this.c.fireActive) this.ignitePuddlesIn(r);
  }

  /** 대쉬 시작: 대쉬 경로가 불꽃을 지나면 무기에 불 */
  onDash(x: number, y: number, dirX: number, dirY: number, lenPx: number): void {
    const line = new Phaser.Geom.Line(x, y, x + dirX * lenPx, y + dirY * lenPx);
    for (const s of this.c.list) {
      if (s.kind !== 'still') continue;
      if (Phaser.Geom.Intersects.LineToRectangle(line, this.flameRect(s))) {
        this.igniteWeapon('weapon');
        return;
      }
    }
  }

  /** 가드 해제 밀쳐내기: 반경 안 술통을 굴린다 */
  onPush(x: number, y: number, radiusPx: number): void {
    for (const s of this.c.list) {
      if (s.kind !== 'cask' || s.state !== 'idle' || s.rolling) continue;
      const dx = s.rect.centerX - x;
      const dy = s.rect.centerY - y;
      const d = Math.hypot(dx, dy);
      if (d > radiusPx + s.rect.width / 2) continue;
      this.startRoll(s, d > 0 ? dx / d : 1, d > 0 ? dy / d : 0);
    }
  }

  /** 플레이어 화살: 화로 불꽃 통과 → 불화살, 불화살 → 웅덩이 점화, 타격형 구조물 맞힘 */
  tickShots(shots: readonly Projectile[]): void {
    const fireOn = this.c.fireActive;
    for (const shot of shots) {
      if (!shot.active || shot.owner !== 'player') continue;
      const pt = { x: shot.x, y: shot.y };
      if (
        !shot.fire &&
        (fireOn || this.c.list.some((s) => s.kind === 'still' && this.flameRect(s).contains(pt.x, pt.y)))
      ) {
        shot.fire = true;
        shot.setTint(Phaser.Display.Color.HexStringToColor(this.stillTint).color);
        if (!fireOn) EventBus.emit(Events.STRUCTURE_FIRE, { target: 'arrow' } satisfies StructureFirePayload);
      }
      if (shot.fire)
        for (const p of this.puddles) if (p.fireUntil === 0 && p.rect.contains(pt.x, pt.y)) this.ignitePuddle(p);
      for (const s of this.c.list) {
        if (!this.isHittable(s) || !s.rect.contains(pt.x, pt.y)) continue;
        const v = shot.body.velocity;
        if (!shot.registerHit(s)) continue;
        const len = Math.hypot(v.x, v.y) || 1;
        this.onHit(s, v.x / len, v.y / len);
        if (!shot.active) break;
      }
    }
  }

  /** 무기 적중 직후 (근접·화살): 불붙은 무기·불화살이면 화상 */
  onMobHit(mob: Mob, viaFireArrow: boolean): void {
    if (!mob.active) return;
    if (!viaFireArrow && !this.c.fireActive) return;
    const def = this.c.stillDef;
    if (!def) return;
    const dmg = Math.max(1, Math.round(gameState.attack * num(def, 'burnAttackMult')));
    this.burns.set(mob, { ticks: num(def, 'burnTicks'), nextAt: this.c.now + num(def, 'burnTickMs'), dmg });
  }

  // --- 타격형 ---

  isHittable(s: Inst): boolean {
    if (s.state === 'broken' || s.state === 'used') return false;
    return s.kind === 'crate' || (s.kind === 'cask' && !s.rolling) || s.kind === 'hiddenWall' || s.kind === 'stakeBell';
  }

  private hitRect(r: Phaser.Geom.Rectangle, dirX: number, dirY: number): void {
    for (const s of [...this.c.list]) {
      if (!this.isHittable(s)) continue;
      if (!Phaser.Geom.Intersects.RectangleToRectangle(r, s.rect)) continue;
      this.onHit(s, dirX, dirY);
    }
  }

  onHit(s: Inst, dirX: number, dirY: number): void {
    const now = this.c.now;
    if (now < s.lastHitAt + STRUCTURE_RULES.hitCooldownMs) return;
    s.lastHitAt = now;
    EventBus.emit(Events.STRUCTURE_HIT, this.c.evt(s));
    switch (s.kind) {
      case 'crate':
        this.breakCrate(s);
        break;
      case 'cask':
        this.c.setVisual(s, 'hit');
        this.startRoll(s, dirX, dirY);
        break;
      case 'hiddenWall':
        this.hitWall(s);
        break;
      case 'stakeBell':
        this.hitBell(s);
        break;
    }
  }

  private breakCrate(s: Inst): void {
    const c = this.c;
    s.state = 'broken';
    c.removeBodies(s);
    c.setVisual(s, 'broken');
    c.emitBroken(s);
    const d = s.def;
    const rng = c.host.rng;
    const r = s.rect;
    if (rng.chance(num(d, 'goldChance'))) {
      const [lo, hi] = d.params.gold as [number, number];
      c.host.spawnPickup(r.centerX, r.centerY, 'gold', rng.int(lo, hi));
    }
    if (rng.chance(num(d, 'potionChance'))) c.host.spawnPickup(r.centerX + 6, r.centerY, 'potion', 1);
  }

  // --- 1-1 독주 술통 ---

  private startRoll(s: Inst, dx: number, dy: number): void {
    const len = Math.hypot(dx, dy);
    if (len === 0 || s.rolling) return;
    s.rolling = { dx: dx / len, dy: dy / len, traveled: 0 };
    this.c.removeBodies(s);
    this.c.setVisual(s, 'active');
    const v = s.views[0];
    if (v.def?.rollRotate !== false) v.setRotation(Math.atan2(dy, dx) - Math.PI / 2);
  }

  private updateRolling(time: number, delta: number): void {
    const c = this.c;
    for (const s of c.list) {
      const r = s.rolling;
      if (!r || s.state === 'broken') continue;
      const d = s.def;
      const speed = num(d, 'rollTilesPerSec') * TILE;
      const step = (speed * delta) / 1000;
      const cx = s.rect.centerX + r.dx * step;
      const cy = s.rect.centerY + r.dy * step;
      const half = s.rect.width / 2;
      // 벽·단단한 칸
      if (!c.host.world.isWalkableAt(cx + r.dx * half, cy + r.dy * half)) {
        this.shatterCask(s, time);
        continue;
      }
      // 다른 단단한 구조물
      const next = new Phaser.Geom.Rectangle(cx - half, cy - s.rect.height / 2, s.rect.width, s.rect.height);
      if (
        c.list.some((o) => o !== s && o.bodies.length > 0 && Phaser.Geom.Intersects.RectangleToRectangle(next, o.rect))
      ) {
        this.shatterCask(s, time);
        continue;
      }
      // 적
      let victim: Mob | null = null;
      for (const child of c.host.mobs.getChildren()) {
        const m = child as Mob;
        if (!m.active) continue;
        const b = m.body;
        if (Phaser.Geom.Intersects.RectangleToRectangle(next, new Phaser.Geom.Rectangle(b.x, b.y, b.width, b.height))) {
          victim = m;
          break;
        }
      }
      s.rect.setPosition(next.x, next.y);
      s.views[0].moveTo(next.centerX, next.bottom);
      r.traveled += step;
      if (victim) {
        const dmg = Math.round(gameState.attack * num(d, 'impactAttackMult'));
        if (c.host.hitMob(victim, dmg, { crit: false, dirX: r.dx, dirY: r.dy })) c.host.onKill(victim, 'environment');
        else victim.stun(time, num(d, 'impactStunMs'), 'hit');
        this.shatterCask(s, time);
        continue;
      }
      if (r.traveled >= num(d, 'rollMaxTiles') * TILE) this.stopRoll(s);
    }
  }

  /** 다 굴러가고 멈춤: 그 자리 칸에 다시 단단하게 */
  private stopRoll(s: Inst): void {
    s.rolling = null;
    const tx = Math.floor(s.rect.centerX / TILE);
    const ty = Math.floor(s.rect.centerY / TILE);
    s.rect.setPosition(tx * TILE, ty * TILE);
    s.p = { ...s.p, tx, ty };
    s.views[0].moveTo(s.rect.centerX, s.rect.bottom);
    s.views[0].setRotation(0);
    this.c.setVisual(s, 'idle');
    this.c.addSolid(s);
  }

  private shatterCask(s: Inst, time: number): void {
    s.rolling = null;
    s.state = 'broken';
    s.views[0].setRotation(0);
    this.c.setVisual(s, 'broken');
    this.c.emitBroken(s);
    this.spawnPuddle(s.def, s.rect.centerX, s.rect.centerY, time);
  }

  private spawnPuddle(d: StructureDef, x: number, y: number, time: number): void {
    const size = num(d, 'puddleTiles') * TILE;
    const rect = new Phaser.Geom.Rectangle(x - size / 2, y - size / 2, size, size);
    const gfx = this.c.host.scene.add
      .rectangle(rect.centerX, rect.centerY, size, size, STRUCTURE_FX.PUDDLE_COLOR, STRUCTURE_FX.PUDDLE_ALPHA)
      .setDepth(STRUCTURE_FX.FLOOR_DEPTH);
    const p: Puddle = {
      rect,
      until: time + num(d, 'puddleMs'),
      fireUntil: 0,
      nextTick: 0,
      gfx,
      fireGfx: null,
      fireFx: [],
    };
    this.puddles.push(p);
    // 화로 곁이면 바로 불바다
    if (
      this.c.list.some(
        (s) => s.kind === 'still' && Phaser.Geom.Intersects.RectangleToRectangle(rect, this.flameRect(s)),
      )
    )
      this.ignitePuddle(p);
  }

  private ignitePuddlesIn(r: Phaser.Geom.Rectangle): void {
    for (const p of this.puddles)
      if (p.fireUntil === 0 && Phaser.Geom.Intersects.RectangleToRectangle(r, p.rect)) this.ignitePuddle(p);
  }

  private ignitePuddle(p: Puddle): void {
    const c = this.c;
    const d = structureDef('cask');
    const now = c.now;
    p.fireUntil = now + num(d, 'fireMs');
    p.until = Math.max(p.until, p.fireUntil);
    p.nextTick = now + num(d, 'fireTickMs');
    const fxId = String(d.params.fireFx ?? 'fire_pool');
    const fx = c.host.fx;
    if (fx.has(fxId)) {
      // 48×24 시트로 3×3 타일을 덮기: y-10 / y+10 두 장, 두 번째는 1프레임 어긋나게 (아트 pivotNote)
      const dur = num(d, 'fireMs');
      p.fireFx.push(
        fx.play(fxId, p.rect.centerX, p.rect.centerY - 10, { depth: STRUCTURE_FX.FLOOR_DEPTH + 0.01, durationMs: dur }),
      );
      const second = fx.sheet(fxId)?.frameDurationsMs?.[0] ?? 110;
      c.host.scene.time.delayedCall(second, () => {
        if (p.fireUntil > c.now)
          p.fireFx.push(
            fx.play(fxId, p.rect.centerX, p.rect.centerY + 10, {
              depth: STRUCTURE_FX.FLOOR_DEPTH + 0.02,
              durationMs: Math.max(0, p.fireUntil - c.now),
            }),
          );
      });
    } else {
      p.fireGfx = c.host.scene.add
        .rectangle(
          p.rect.centerX,
          p.rect.centerY,
          p.rect.width,
          p.rect.height,
          STRUCTURE_FX.FIRE_COLOR,
          STRUCTURE_FX.FIRE_ALPHA,
        )
        .setDepth(STRUCTURE_FX.FLOOR_DEPTH + 0.01);
    }
    EventBus.emit(Events.STRUCTURE_FIRE, { target: 'pool' } satisfies StructureFirePayload);
    const cask = c.find('cask');
    if (cask) c.result(cask, 'info', txt(cask.def, 'ignite'), {});
  }

  private updatePuddles(time: number): void {
    const c = this.c;
    const P = c.host.player;
    if (this.puddles.length === 0) {
      if (this.mobsSlowed) {
        for (const ch of c.host.mobs.getChildren()) (ch as Mob).speedMult = 1;
        this.mobsSlowed = false;
      }
      P.envSpeedMult = 1;
      return;
    }
    const d = structureDef('cask');
    const pc = P.body.center;
    let playerIn: Puddle | null = null;
    for (const p of this.puddles) if (p.rect.contains(pc.x, pc.y)) playerIn = p;
    P.envSpeedMult = playerIn ? 1 - num(d, 'playerSlow') : 1;
    for (const ch of c.host.mobs.getChildren()) {
      const m = ch as Mob;
      if (!m.active) continue;
      const inside = this.puddles.some((p) => p.rect.contains(m.body.center.x, m.body.center.y));
      m.speedMult = inside ? 1 - num(d, 'enemySlow') : 1;
    }
    this.mobsSlowed = true;
    // 불바다 틱
    for (const p of this.puddles) {
      if (p.fireUntil === 0 || time >= p.fireUntil || time < p.nextTick) continue;
      p.nextTick = time + num(d, 'fireTickMs');
      const dmg = Math.max(1, Math.round(gameState.attack * num(d, 'fireAttackMult')));
      for (const ch of [...c.host.mobs.getChildren()]) {
        const m = ch as Mob;
        if (!m.active || !p.rect.contains(m.body.center.x, m.body.center.y)) continue;
        if (c.host.hitMob(m, dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) c.host.onKill(m, 'environment');
      }
      if (p.rect.contains(pc.x, pc.y)) P.takeHit(num(d, 'firePlayerAttack'), time);
    }
    // 만료
    const expired = (p: Puddle) => time >= p.until || (p.fireUntil > 0 && time >= p.fireUntil);
    for (const p of this.puddles) if (expired(p)) this.destroyPuddle(p);
    this.puddles = this.puddles.filter((p) => !expired(p));
  }

  private destroyPuddle(p: Puddle): void {
    p.gfx.destroy();
    p.fireGfx?.destroy();
    for (const h of p.fireFx) if (this.c.host.fx.isActive(h)) this.c.host.fx.stop(h);
  }

  // --- 1-2 증류 화로 · 화상 ---

  private get stillTint(): string {
    const d = this.c.stillDef;
    return d && typeof d.params.arrowTint === 'string' ? d.params.arrowTint : '#ff9a3c';
  }

  /** 불꽃 영역: 시트 fireBox(프레임 좌표) → 월드, 없으면 발판. 여유 flamePadPx */
  private flameRect(s: Inst): Phaser.Geom.Rectangle {
    const pad = num(s.def, 'flamePadPx');
    const v = s.views[0];
    const fb = v.def?.fireBox;
    if (fb) {
      const a = v.frameToWorld(fb.x, fb.y);
      if (a) return new Phaser.Geom.Rectangle(a.x - pad, a.y - pad, fb.w + pad * 2, fb.h + pad * 2);
    }
    return new Phaser.Geom.Rectangle(s.rect.x - pad, s.rect.y - pad, s.rect.width + pad * 2, s.rect.height + pad * 2);
  }

  private touchesFlame(r: Phaser.Geom.Rectangle): boolean {
    return this.c.list.some(
      (s) => s.kind === 'still' && Phaser.Geom.Intersects.RectangleToRectangle(r, this.flameRect(s)),
    );
  }

  private igniteWeapon(target: 'weapon' | 'arrow'): void {
    const c = this.c;
    const d = c.stillDef;
    if (!d) return;
    const was = c.fireActive;
    c.fireWeaponUntil = c.now + num(d, 'fireMs');
    if (!was) {
      EventBus.emit(Events.STRUCTURE_FIRE, { target } satisfies StructureFirePayload);
      c.result(c.find('still')!, 'gain', txt(d, 'ignite'), {});
    }
  }

  private updateBurns(time: number): void {
    if (this.burns.size === 0) return;
    const c = this.c;
    const d = c.stillDef;
    const tick = d ? num(d, 'burnTickMs') : 500;
    for (const [mob, b] of [...this.burns]) {
      if (!mob.active) {
        this.burns.delete(mob);
        continue;
      }
      if (time < b.nextAt) continue;
      b.nextAt = time + tick;
      b.ticks -= 1;
      if (c.host.hitMob(mob, b.dmg, { crit: false, dirX: 0, dirY: 0, tick: true })) {
        c.host.onKill(mob, 'attack');
        this.burns.delete(mob);
        continue;
      }
      mob.flashColor(STRUCTURE_FX.BURN_COLOR);
      if (b.ticks <= 0) this.burns.delete(mob);
    }
  }

  // --- 1-6 숨은 벽 ---

  private hitWall(s: Inst): void {
    const c = this.c;
    s.hits += 1;
    const need = num(s.def, 'hits');
    if (s.hits < need) {
      c.setVisual(s, 'hit');
      c.host.scene.time.delayedCall(STRUCTURE_FX.HIT_FLASH_MS + 10, () => {
        if (s.state === 'idle') c.setVisual(s, `damaged${Math.min(2, s.hits)}`);
      });
      return;
    }
    s.state = 'broken';
    c.setVisual(s, 'broken');
    const cellar = s.p.cellar!;
    c.host.world.carveCellar(cellar.inner, cellar.opening, cellar.ring);
    c.emitBroken(s);
    this.fillCellar(s);
  }

  /** 저장고 안: 짐 3~4 + 70% 궤짝(반값) / 30% 물약 + 골드 */
  private fillCellar(s: Inst): void {
    const core = this.c;
    const d = s.def;
    const c = s.p.cellar!;
    const rng = core.host.rng;
    const free: { x: number; y: number }[] = [];
    for (let y = c.inner.y; y < c.inner.y + c.inner.h; y++)
      for (let x = c.inner.x; x < c.inner.x + c.inner.w; x++) free.push({ x, y });
    // 입구 바로 안쪽 줄은 비워 통로로 둔다
    const nearOpening = (t: { x: number; y: number }) =>
      c.opening.some((o) => Math.abs(o.x - t.x) + Math.abs(o.y - t.y) <= 1);
    const spots = rng.shuffle(free.filter((t) => !nearOpening(t)));
    const used = new Set<string>();
    const take = (w: number, h: number): { x: number; y: number } | null => {
      for (const t of spots) {
        let ok = true;
        for (let y = t.y; y < t.y + h && ok; y++)
          for (let x = t.x; x < t.x + w && ok; x++) {
            const inside = x < c.inner.x + c.inner.w && y < c.inner.y + c.inner.h;
            if (!inside || used.has(`${x},${y}`) || nearOpening({ x, y })) ok = false;
          }
        if (!ok) continue;
        for (let y = t.y; y < t.y + h; y++) for (let x = t.x; x < t.x + w; x++) used.add(`${x},${y}`);
        return t;
      }
      return null;
    };
    const deltas: UiStructureResult['deltas'] = {};
    if (rng.chance(num(d, 'chestChance'))) {
      const chest = structureDef('chest');
      const t = take(chest.size[0], chest.size[1]);
      if (t) core.spawnExtra('chest', s.roomId, t.x, t.y, num(d, 'chestDiscount'));
    } else {
      const cx = (c.inner.x + c.inner.w / 2) * TILE;
      const cy = (c.inner.y + c.inner.h / 2) * TILE;
      for (let i = 0; i < num(d, 'potions'); i++) core.host.spawnPickup(cx + i * 8, cy, 'potion', 1);
      core.host.spawnPickup(cx, cy + 8, 'gold', num(d, 'gold'));
      deltas.potions = num(d, 'potions');
      deltas.gold = num(d, 'gold');
    }
    const [lo, hi] = d.params.crates as [number, number];
    const n = rng.int(lo, hi);
    for (let i = 0; i < n; i++) {
      const t = take(1, 1);
      if (t) core.spawnExtra('crate', s.roomId, t.x, t.y);
    }
    core.result(s, 'gain', txt(d, 'broken'), deltas);
  }

  // --- 2-4 판돈 종 ---

  private hitBell(s: Inst): void {
    const c = this.c;
    const d = s.def;
    const max = num(d, 'maxRings');
    if (s.rings >= max) return;
    const next = stakeMods(c.stakeRings + 1, c.bellParams);
    const vars = {
      hp: Math.round((next.hpMult - 1) * 100),
      extra: next.extra,
      gold: next.goldMult.toFixed(1),
      pers: next.personalityMult.toFixed(1),
    };
    if (!s.warned) {
      s.warned = true;
      c.setVisual(s, 'hit');
      EventBus.emit(Events.STRUCTURE_BELL, {
        id: s.id,
        confirmed: false,
        rings: c.stakeRings,
      } satisfies StructureBellPayload);
      c.result(s, 'warn', txt(d, 'warn', vars), {});
      return;
    }
    s.warned = false;
    s.rings += 1;
    c.stakeRings += 1;
    c.setVisual(s, 'active');
    EventBus.emit(Events.STRUCTURE_BELL, {
      id: s.id,
      confirmed: true,
      rings: c.stakeRings,
    } satisfies StructureBellPayload);
    c.result(s, 'mixed', txt(d, 'rung', vars), {});
    if (s.rings >= max) {
      s.state = 'used';
      c.host.scene.time.delayedCall(600, () => c.setVisual(s, 'used'));
    }
  }

  destroy(): void {
    for (const p of this.puddles) {
      p.gfx.destroy();
      p.fireGfx?.destroy();
    }
    this.puddles = [];
    this.burns.clear();
  }
}
