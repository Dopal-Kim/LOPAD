/**
 * 61 단계 5 (P13 §1) 개성 전투 양상 도구 — 개성 규칙(Katana/Greatsword/Dagger/BowRules·branch/*)이 함께 쓰는 '보이는 새 행동':
 * - 띄움(launch): 그림만 포물선으로 올렸다 떨어뜨림(바디·그림자는 바닥 — EntityVisual.setLift), 떠 있는 동안 무방비, 착지 충격
 * - 처박기(slam): 미는 길을 미리 훑어 벽·기둥(걸을 수 없는 칸)·다른 적·술통에 닿으면 그 자리에서 '박힘' — 피해·경직·흔들림
 *   (술통이면 터뜨려 술 웅덩이). 다른 적이면 둘 다 다치고 그 적은 조금 더 밀린다(서로 부딪힘)
 * - 끌어당김(pull) · 묶음(bind — 발밑 고리 + 묶인 자리까지 사슬 선) · 불똥(ignite — 술 웅덩이 점화·술통 터뜨리기)
 * - 그림: 아트 전용 fx `trait_<무기>_<개성>[_<부위>]`(로드돼 있으면) → 기존 fx 후보 → 윤곽 (`fx`)
 * 공명(ResonanceRules)은 `listen` 으로 처박기·끌려옴·묶음·착지 사건을 받는다. 보스는 밀거나 띄우지 않는다(피해만).
 */
import Phaser from 'phaser';
import { BUILD_FX, DEPTH, TILE, TRAIT_FX } from '../../../../core/Constants';
import { gameState } from '../../../../core/GameState';
import type { Mob } from '../../../../objects/Mob';
import type { FxHandle } from '../../../../systems/fx/fx';
import { traitFxId } from '../../../../systems/growth/traitArt';
import { fxDrawScale } from '../../../../systems/sprites/spriteDefs';
import { sheetLoopRange } from '../BuildArt';
import { PLAYER_RENDER_SCALE } from '../../../../systems/weapon/playerScale';
import { T } from '../../shared';
import type { Pt, RuleKit } from './RuleKit';

export type SlamKind = 'wall' | 'mob' | 'cask' | 'none';

export interface SlamResult {
  kind: SlamKind;
  mob: Mob;
  /** 맞닿은 자리 (none 이면 멈춘 자리) */
  at: Pt;
  other: Mob | null;
  trait: string;
}

/** 공명이 받는 사건 */
export interface MoveListener {
  onSlam?(r: SlamResult): void;
  /** 개성이 적을 밀거나 끌어당김 (처박기 포함) */
  onDisplaced?(mob: Mob, trait: string, how: 'push' | 'pull'): void;
  onBind?(mob: Mob, trait: string): void;
  onLand?(mob: Mob, trait: string): void;
}

export interface SlamOpts {
  /** 박힐 때 피해 배율 (공격력 ×) · 경직 ms */
  slamMult: number;
  slamStunMs: number;
  /** 아무것도 안 박혀도 끝에 경직 (기본 0) */
  endStunMs?: number;
  /** 처박기 대신 끌어당김으로 셈 (공명 onDisplaced) */
  how?: 'push' | 'pull';
}

export interface LaunchOpts {
  /** 띄움 시작 그림 좌우 뒤집기 (시트 flipX allowed — 어깨 너머) */
  flipX?: boolean;
  heightTiles: number;
  airMs: number;
  landRadiusTiles?: number;
  landMult?: number;
}

interface Bind {
  mob: Mob;
  until: number;
  anchor: Pt | null;
  gfx: Phaser.GameObjects.Graphics;
  /** 전용 묶음 수명 그림 (없으면 null — 윤곽 고리) */
  art: FxHandle | null;
}

/** 개성 fx 재생 결과 (재생한 시트 id · 핸들 · 전용 그림인지) */
export interface TraitFxPlay {
  id: string;
  handle: FxHandle | null;
  own: boolean;
}

const unit = (x: number, y: number): Pt => {
  const l = Math.hypot(x, y) || 1;
  return { x: x / l, y: y / l };
};

export class TraitMoves {
  private readonly airborne = new Map<Mob, Phaser.Tweens.Tween>();
  private binds: Bind[] = [];
  private bossBindReadyAt = -Infinity;
  private readonly listeners: MoveListener[] = [];
  /** 디버그: 마지막 처박기 */
  lastSlam: { kind: SlamKind; trait: string; t: number } | null = null;
  readonly counts: Record<string, number> = {};

  constructor(private readonly k: RuleKit) {}

  listen(l: MoveListener): void {
    this.listeners.push(l);
  }

  private get g() {
    return this.k.g;
  }

  private count(key: string): void {
    this.counts[key] = (this.counts[key] ?? 0) + 1;
  }

  // --- 그림 ---

  /**
   * 개성 fx: `trait_<무기>_<개성>[_part]` → fallbacks(기존 fx id) 중 로드된 첫 시트. 하나도 없으면 null (호출 쪽이 윤곽).
   * 전용 시트(art §27 메타)만: `flipX`(시트 flipX allowed — 그림 기준 방향과 반대일 때) · `lifeMs`(수명 시트 loopRange — 그 시간 반복 뒤
   * 사라짐 구간) · `lengthPx`(길이 있는 회전 선 `TRAIT_FX.LINE_DOTS` 를 그 길이로 가로 배율, 0.6~1.6)
   */
  fx(
    trait: string,
    at: Pt,
    o: {
      part?: string;
      fallbacks?: readonly string[];
      angle?: number;
      scale?: number;
      depth?: number;
      tint?: number;
      flipX?: boolean;
      lifeMs?: number;
      lengthPx?: number;
    } = {},
  ): TraitFxPlay | null {
    const fx = this.g.fx;
    const own = traitFxId(gameState.weapon.id, trait, o.part);
    const id = [own, ...(o.fallbacks ?? [])].find((c) => fx.has(c));
    if (!id) return null;
    const mine = id === own;
    const def = mine ? fx.sheet(id) : null;
    const range = def && o.lifeMs ? sheetLoopRange(def) : undefined;
    const lineDots = mine ? TRAIT_FX.LINE_DOTS[trait] : undefined;
    const sx =
      def && lineDots && o.lengthPx
        ? Math.max(TRAIT_FX.LINE_SCALE[0], Math.min(TRAIT_FX.LINE_SCALE[1], o.lengthPx / (lineDots * fxDrawScale(def))))
        : 1;
    const handle = fx.play(id, at.x, at.y, {
      ...(o.angle !== undefined ? { angle: o.angle } : {}),
      depth: o.depth ?? DEPTH.HIT_FX,
      scaleMult: (o.scale ?? 1) * (mine ? 1 : PLAYER_RENDER_SCALE),
      ...(sx !== 1 ? { scaleXMult: sx } : {}),
      ...(mine && o.flipX && (def as { flipX?: unknown } | null)?.flipX === 'allowed' ? { flipX: true } : {}),
      ...(o.lifeMs ? { durationMs: o.lifeMs } : {}),
      ...(range ? { loopRange: range } : {}),
      ...(o.tint !== undefined && !mine ? { tint: o.tint } : {}),
      hooks: false,
    });
    return { id, handle, own: mine };
  }

  /** 불똥·불티 점 (윤곽 — 전용 fx 가 없을 때 함께) */
  sparks(at: Pt, color: number = TRAIT_FX.SPARK.COLOR): void {
    const S = TRAIT_FX.SPARK;
    for (let i = 0; i < S.N; i++) {
      const a = (i / S.N) * Math.PI * 2 + Math.random() * 0.6;
      const d = 6 + Math.random() * 8;
      const dot = this.g.add.circle(at.x, at.y, S.R, color, 1).setDepth(DEPTH.HIT_FX);
      this.g.tweens.add({
        targets: dot,
        x: at.x + Math.cos(a) * d,
        y: at.y + Math.sin(a) * d - 6,
        alpha: 0,
        duration: S.MS,
        onComplete: () => dot.destroy(),
      });
    }
  }

  /**
   * 사슬·묶음 선 (잠깐): art §27 공통 사슬 타일 `trait_common_chain`(행 bind 청회 · drag 적갈, 열 0 기본 · 1 팽팽, 피벗 = 선 시작,
   * 오른쪽으로 반복) 을 선 방향으로 돌려 이어 깐다 — 마지막 조각은 끝에 맞춰 겹친다. 시트가 없으면 점선 윤곽
   */
  chainLine(a: Pt, b: Pt, color: number = TRAIT_FX.CHAIN_COLOR, ms = 260): void {
    if (this.chainTile(a, b, color === TRAIT_FX.BIND.COLOR ? 'bind' : 'drag', ms)) return;
    const gfx = this.g.add.graphics().setDepth(DEPTH.HIT_FX);
    gfx.lineStyle(TRAIT_FX.BIND.LINE_PX, color, TRAIT_FX.BIND.ALPHA);
    // 점선 사슬
    const n = Math.max(2, Math.round(Math.hypot(b.x - a.x, b.y - a.y) / 5));
    for (let i = 0; i < n; i += 2) {
      const t0 = i / n;
      const t1 = Math.min(1, (i + 1) / n);
      gfx.lineBetween(a.x + (b.x - a.x) * t0, a.y + (b.y - a.y) * t0, a.x + (b.x - a.x) * t1, a.y + (b.y - a.y) * t1);
    }
    this.g.tweens.add({ targets: gfx, alpha: 0, duration: ms, onComplete: () => gfx.destroy() });
  }

  private chainTile(a: Pt, b: Pt, row: 'bind' | 'drag', ms: number): boolean {
    const fx = this.g.fx;
    const id = TRAIT_FX.CHAIN_SHEET;
    const def = fx.has(id) ? fx.sheet(id) : null;
    if (!def) return false;
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    if (len < 1) return true;
    const u = unit(b.x - a.x, b.y - a.y);
    const period = Math.max(1, def.frameWidth * fxDrawScale(def));
    const angle = Math.atan2(u.y, u.x);
    const n = Math.max(1, Math.ceil(len / period));
    for (let i = 0; i < n; i++) {
      const d = i === n - 1 && n > 1 ? Math.max(0, len - period) : i * period;
      const h = fx.play(id, a.x + u.x * d, a.y + u.y * d, {
        dir: row,
        angle,
        staticFrame: row === 'drag' ? 1 : 0,
        depth: DEPTH.HIT_FX,
        hooks: false,
      });
      this.g.time.delayedCall(ms, () => fx.stop(h, 0, true));
    }
    return true;
  }

  // --- 상태 ---

  isAirborne(mob: Mob): boolean {
    return this.airborne.has(mob);
  }

  isBound(mob: Mob): boolean {
    return this.binds.some((b) => b.mob === mob && b.until > this.k.now);
  }

  /** 묶음 풀기 (땅에 박기 — 다시 치면 튕겨 나감). 수명 그림은 사라짐 구간으로 */
  unbind(mob: Mob): boolean {
    const i = this.binds.findIndex((b) => b.mob === mob);
    if (i < 0) return false;
    this.endBind(this.binds[i]);
    this.binds.splice(i, 1);
    return true;
  }

  private endBind(b: Bind): void {
    b.gfx.destroy();
    if (b.art) this.g.fx.finish(b.art);
  }

  // --- 띄움 ---

  /** 띄움: 보스·경직 면역(통 갑옷) 제외. 떠 있는 동안 무방비(경직), 떨어질 때 둘레 피해 */
  launch(mob: Mob, trait: string, o: LaunchOpts): boolean {
    const k = this.k;
    if (!mob.active || mob.isBoss || mob.stunImmune || this.airborne.has(mob)) return false;
    const ms = Math.max(120, o.airMs);
    const h = T(o.heightTiles);
    k.stun(mob, ms + 80);
    this.fx(trait, { x: mob.x, y: mob.y }, { part: 'launch', fallbacks: ['dash_dust'], flipX: o.flipX });
    if (!mob.visual.animated) k.rt.fx.ring(mob.x, mob.y, TILE * 0.6, BUILD_FX.COLOR.METEOR, ms);
    const tween = this.g.tweens.addCounter({
      from: 0,
      to: 1,
      duration: ms,
      onUpdate: (tw) => {
        const v = tw.getValue() ?? 0;
        if (mob.active) mob.visual.setLift(4 * h * v * (1 - v));
      },
      onComplete: () => this.land(mob, trait, o),
    });
    this.airborne.set(mob, tween);
    this.count('launch');
    for (const l of this.listeners) l.onDisplaced?.(mob, trait, 'push');
    return true;
  }

  private land(mob: Mob, trait: string, o: LaunchOpts): void {
    const k = this.k;
    this.airborne.delete(mob);
    if (!mob.active || !k.g.scene.isActive()) return;
    mob.visual.setLift(0);
    const at = { x: mob.x, y: mob.y };
    const r = T(o.landRadiusTiles ?? 0);
    if (!this.fx(trait, at, { part: 'land', fallbacks: ['crush', 'dash_dust'], depth: DEPTH.FX_GROUND }))
      k.rt.fx.ring(at.x, at.y, Math.max(r, TILE * 0.5), BUILD_FX.COLOR.RING, 200);
    k.g.shake.add(k.now, TRAIT_FX.LAUNCH_SHAKE.PX, TRAIT_FX.LAUNCH_SHAKE.MS);
    if (r > 0 && (o.landMult ?? 0) > 0)
      for (const m of k.rt.fx.inCircle(at.x, at.y, r)) k.hit(m, o.landMult ?? 0, unit(m.x - at.x, m.y - at.y));
    for (const l of this.listeners) l.onLand?.(mob, trait);
  }

  // --- 처박기 ---

  /** 미는 길 훑기: 벽·기둥 → 다른 적 → 술통. 멈출 거리와 닿은 것 */
  private probe(mob: Mob, u: Pt, dist: number): { travel: number; kind: SlamKind; other: Mob | null; at: Pt } {
    const g = this.g;
    const c = mob.body.center;
    const r = Math.min(mob.body.halfWidth, mob.body.halfHeight);
    const step = TRAIT_FX.SLAM_STEP_PX;
    const others = this.k.rt.fx.mobs().filter((m) => m !== mob);
    for (let d = step; d <= dist + 0.01; d += step) {
      const x = c.x + u.x * d;
      const y = c.y + u.y * d;
      if (!g.world.isWalkableAt(x + u.x * r, y + u.y * r))
        return { travel: Math.max(0, d - step), kind: 'wall', other: null, at: { x: x + u.x * r, y: y + u.y * r } };
      for (const m of others) {
        const mc = m.body.center;
        const mr = Math.min(m.body.halfWidth, m.body.halfHeight);
        if (Math.hypot(mc.x - x, mc.y - y) <= r + mr + TRAIT_FX.SLAM_CONTACT_PAD_PX)
          return { travel: Math.max(0, d - step), kind: 'mob', other: m, at: { x: (x + mc.x) / 2, y: (y + mc.y) / 2 } };
      }
      if (g.structures.caskAt(x + u.x * r, y + u.y * r))
        return { travel: Math.max(0, d - step), kind: 'cask', other: null, at: { x: x + u.x * r, y: y + u.y * r } };
    }
    return { travel: dist, kind: 'none', other: null, at: { x: c.x + u.x * dist, y: c.y + u.y * dist } };
  }

  /**
   * 처박기: dir 쪽으로 tiles 칸 밀되, 길에 벽·기둥·적·술통이 있으면 거기서 박힌다 (보스는 밀지 않음 — 피해만 없음).
   * 결과는 밀기가 끝날 때 onDone 으로 (리스너 onSlam 도)
   */
  slam(mob: Mob, dir: Pt, tiles: number, trait: string, o: SlamOpts, onDone?: (r: SlamResult) => void): boolean {
    const k = this.k;
    if (!mob.active || mob.isBoss) return false;
    const u = unit(dir.x, dir.y);
    const p = this.probe(mob, u, T(tiles));
    const ms = Math.min(
      TRAIT_FX.SLAM_MAX_MS,
      Math.max(TRAIT_FX.SLAM_MIN_MS, (p.travel / TILE) * TRAIT_FX.SLAM_MS_PER_TILE),
    );
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      const r = this.impact(mob, u, p.kind, p.other, p.at, trait, o);
      onDone?.(r);
    };
    if (p.travel >= 1) mob.shove(u.x, u.y, p.travel, ms, false, () => finish());
    // 밀기가 다른 경직에 끊겨도 박힘은 일어난다
    k.g.time.delayedCall(p.travel >= 1 ? ms + 40 : 0, () => {
      if (k.g.scene.isActive()) finish();
    });
    for (const l of this.listeners) l.onDisplaced?.(mob, trait, o.how ?? 'push');
    return true;
  }

  private impact(mob: Mob, u: Pt, kind: SlamKind, other: Mob | null, at: Pt, trait: string, o: SlamOpts): SlamResult {
    const k = this.k;
    const res: SlamResult = { kind, mob, at, other, trait };
    this.lastSlam = { kind, trait, t: Math.round(k.now) };
    if (kind === 'none') {
      if (o.endStunMs) k.stun(mob, o.endStunMs);
      return res;
    }
    this.count(`slam_${kind}`);
    const angle = Math.atan2(u.y, u.x);
    if (!this.fx(trait, at, { part: 'impact', angle, fallbacks: ['hit_burst', 'crush', 'hit_spark'] }))
      k.rt.fx.ring(at.x, at.y, TILE * 0.5, BUILD_FX.COLOR.CRACK, 200);
    k.g.shake.add(k.now, TRAIT_FX.SLAM_SHAKE.PX, TRAIT_FX.SLAM_SHAKE.MS, u);
    if (mob.active) {
      k.hit(mob, o.slamMult, u, { heavy: true });
      if (mob.active) k.stun(mob, o.slamStunMs);
    }
    // 부딪친 적: 피해 + (보스가 아니면) 경직·반 칸 더 밀림 — 보스는 피해만
    if (kind === 'mob' && other?.active) {
      k.hit(other, o.slamMult, u, { heavy: true });
      if (other.active && !other.isBoss) {
        k.stun(other, o.slamStunMs);
        other.shove(u.x, u.y, TILE * 0.6, 140);
      }
    }
    // 술통에 박힘 → 터져 술 웅덩이
    if (kind === 'cask') k.g.structures.burstCasksIn(at.x, at.y, TILE * 0.5);
    for (const l of this.listeners) l.onSlam?.(res);
    return res;
  }

  // --- 끌어당김 · 묶음 ---

  /** 끌어당김: to 쪽으로 tiles 칸 (to 와 stopTiles 칸 앞에서 멈춤) — 처박기와 같은 길 검사(다른 적과 부딪치면 박힘) */
  pull(mob: Mob, to: Pt, tiles: number, trait: string, o: Partial<SlamOpts> & { stopTiles?: number } = {}): boolean {
    if (!mob.active || mob.isBoss) return false;
    const d = Math.hypot(to.x - mob.x, to.y - mob.y);
    const n = Math.min(tiles, Math.max(0, d / TILE - (o.stopTiles ?? 0.6)));
    if (n <= 0.05) return false;
    return this.slam(mob, { x: to.x - mob.x, y: to.y - mob.y }, n, trait, {
      slamMult: o.slamMult ?? 0,
      slamStunMs: o.slamStunMs ?? 0,
      endStunMs: o.endStunMs,
      how: 'pull',
    });
  }

  /** 묶음: ms 동안 제자리(경직) + 발밑 고리 · anchor 가 있으면 그 자리까지 사슬 선. 보스는 짧게·드물게(묶어 가두기 방지) */
  bind(mob: Mob, ms: number, trait: string, anchor: Pt | null = null): boolean {
    const k = this.k;
    if (!mob.active || ms <= 0) return false;
    if (mob.isBoss) {
      if (k.now < this.bossBindReadyAt) return false;
      this.bossBindReadyAt = k.now + TRAIT_FX.BOSS_BIND.COOLDOWN_MS;
    }
    const dur = mob.isBoss ? ms * TRAIT_FX.BOSS_BIND.MULT : ms;
    k.stun(mob, dur);
    this.unbind(mob);
    const gfx = k.g.add.graphics().setDepth(DEPTH.FX_GROUND + 0.02);
    // art §27 묶음 수명 시트 (`_bind` loopRange — 묶인 동안 반복, 풀리면 사라짐) — 있으면 발밑 고리 윤곽 대신
    const art = this.fx(
      trait,
      { x: mob.x, y: mob.y },
      { part: 'bind', fallbacks: [], depth: DEPTH.FX_GROUND, lifeMs: dur },
    );
    this.binds.push({ mob, until: k.now + dur, anchor, gfx, art: art?.handle ?? null });
    this.count('bind');
    for (const l of this.listeners) l.onBind?.(mob, trait);
    return true;
  }

  private drawBinds(now: number): void {
    const B = TRAIT_FX.BIND;
    this.binds = this.binds.filter((b) => {
      if (!b.mob.active || now >= b.until) {
        this.endBind(b);
        return false;
      }
      const left = (b.until - now) / 1000;
      const x = b.mob.x;
      const y = b.mob.y;
      b.gfx.clear();
      b.gfx.lineStyle(B.LINE_PX, B.COLOR, B.ALPHA * Math.min(1, left * 3));
      if (!b.art) {
        b.gfx.strokeEllipse(x, y, B.RING_R * 2, B.RING_R);
        // 고리 둘레 매듭 점 (돌아감)
        for (let i = 0; i < 4; i++) {
          const a = now / 300 + (i * Math.PI) / 2;
          b.gfx
            .fillStyle(B.COLOR, B.ALPHA)
            .fillCircle(x + Math.cos(a) * B.RING_R, y + Math.sin(a) * B.RING_R * 0.5, 1.2);
        }
      }
      if (b.anchor) b.gfx.lineBetween(x, y, b.anchor.x, b.anchor.y);
      return true;
    });
  }

  // --- 환경 ---

  /** 원 안 술 웅덩이 점화 (불이 붙은 수) */
  igniteCircle(at: Pt, r: number): number {
    let n = 0;
    for (const q of this.k.rt.fx.poolsNear(at.x, at.y, r))
      if (!this.g.pools.burning(q)) {
        this.g.pools.ignite(q);
        n += 1;
      }
    return n;
  }

  /** 선 위 술 웅덩이 점화 (불이 붙은 수) */
  igniteLine(from: Pt, dir: Pt, len: number, half: number): number {
    const u = unit(dir.x, dir.y);
    let n = 0;
    for (const q of this.g.pools.of('structure')) {
      const dx = q.rect.centerX - from.x;
      const dy = q.rect.centerY - from.y;
      const along = dx * u.x + dy * u.y;
      const off = Math.abs(dx * u.y - dy * u.x);
      const pr = q.rect.width / 2;
      if (along < -pr || along > len + pr || off > half + pr || this.g.pools.burning(q)) continue;
      this.g.pools.ignite(q);
      n += 1;
    }
    return n;
  }

  /** 선 위 술통 터뜨리기 (터뜨린 수) */
  burstCasksOnLine(from: Pt, dir: Pt, len: number, half: number): number {
    const u = unit(dir.x, dir.y);
    let n = 0;
    for (let d = 0; d <= len; d += TILE * 0.5)
      n += this.g.structures.burstCasksIn(from.x + u.x * d, from.y + u.y * d, half);
    return n;
  }

  update(now: number): void {
    if (this.binds.length > 0) this.drawBinds(now);
  }

  debug(): Record<string, unknown> {
    return {
      airborne: this.airborne.size,
      binds: this.binds.length,
      lastSlam: this.lastSlam,
      counts: { ...this.counts },
    };
  }

  destroy(): void {
    for (const [mob, tw] of this.airborne) {
      tw.stop();
      if (mob.active) mob.visual.setLift(0);
    }
    this.airborne.clear();
    for (const b of this.binds) this.endBind(b);
    this.binds = [];
    this.listeners.length = 0;
  }
}
