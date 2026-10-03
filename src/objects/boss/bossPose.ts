/**
 * 보스 몸 연출 (BossPoseApi 구현). 35라운드 attack phaseFrames 규칙(예고 frame 0 · 돌진 1↔2 · 멈춤 frame 3)을 그대로 옮기고,
 * 54라운드 계약 §15 v3 동작(drink·drink_break·stagger_dash·fall·kick·throw·phase_drink·slam)의 JSON 이벤트 키
 * (phaseFrames·impactFrame·releaseFrame·cupAnchors·footAnchors·handAnchors)를 읽는다. 시트가 없으면 임시 연출(기울기·눕힘·색).
 */
import Phaser from 'phaser';
import { BOSS_FX, SPRITES } from '../../core/Constants';
import { spriteLibrary } from '../../systems/sprites';
import { artScale, facingOf, frameDurations, frameStarts, type Facing, type SheetJson } from '../../systems/spriteDefs';
import type { EntityVisual } from '../EntityVisual';
import type { BossPoseApi, Vec } from './types';

type Host = Phaser.GameObjects.Sprite;

/** 앵커 값 하나: {x, y[, w, h]} 또는 [x, y] */
function asRect(v: unknown): { x: number; y: number; w: number; h: number } | null {
  if (Array.isArray(v) && typeof v[0] === 'number' && typeof v[1] === 'number') return { x: v[0], y: v[1], w: 0, h: 0 };
  if (v && typeof v === 'object') {
    const o = v as Record<string, unknown>;
    if (typeof o.x === 'number' && typeof o.y === 'number')
      return { x: o.x, y: o.y, w: typeof o.w === 'number' ? o.w : 0, h: typeof o.h === 'number' ? o.h : 0 };
  }
  return null;
}

/** 프레임별 앵커 표 (방향 → 열 목록, 또는 시트 프레임 순서 배열)에서 (방향, 열) 값 */
export function anchorAt(raw: unknown, dir: Facing, col: number, frames: number, rowIndex: number): unknown {
  if (Array.isArray(raw)) return raw.length > frames ? raw[rowIndex * frames + col] : raw[col];
  if (raw && typeof raw === 'object') {
    const byDir = (raw as Record<string, unknown>)[dir];
    if (Array.isArray(byDir)) return byDir[col];
  }
  return null;
}

export class BossPose implements BossPoseApi {
  private seq = 0;

  constructor(
    private readonly host: Host,
    private readonly visual: EntityVisual,
    private readonly name: string,
  ) {}

  get facing(): Facing {
    return this.visual.facing;
  }

  private sheet(action: string): SheetJson | undefined {
    return this.visual.hasAction(action) ? this.visual.sheet(action) : undefined;
  }

  /** attack 국면 (54라운드 아트 v3 는 멈춤 열 이름이 recover — 구 시트 recover_or_fan 과 같은 뜻으로 읽는다) */
  private get attackFrames(): SheetJson['phaseFrames'] | null {
    const pf = spriteLibrary.sheet(this.name, 'attack')?.phaseFrames;
    if (!pf) return null;
    return pf.recover_or_fan || !pf.recover ? pf : { ...pf, recover_or_fan: pf.recover };
  }

  private dirTo(t: Vec | undefined): Facing {
    return t ? facingOf(t.x - this.host.x, t.y - this.host.y, this.visual.facing) : this.visual.facing;
  }

  // --- 35라운드 attack 국면 (그대로) ---

  dashTelegraph(time: number, target: Vec, fitMs: number, first: boolean): void {
    const pf = this.attackFrames;
    const dir = this.dirTo(target);
    this.seq++;
    // 54라운드 아트 v3 attack: holdFrame (예고 끝 자세) — 구 시트는 telegraph[0]
    const hold = spriteLibrary.sheet(this.name, 'attack')?.holdFrame ?? pf?.telegraph?.[0];
    if (pf?.telegraph?.length && hold !== undefined) this.visual.hold('attack', dir, hold, time);
    else if (first) this.visual.oneShot('attack', dir, time, fitMs);
  }

  dashLoop(dirX: number, dirY: number): void {
    const pf = this.attackFrames;
    if (!pf?.dash?.length) return;
    this.seq++;
    this.visual.loopFrames('attack', facingOf(dirX, dirY, this.visual.facing), pf.dash, SPRITES.BOSS_DASH_FRAME_MS);
  }

  recover(time: number, ms?: number): void {
    const pf = this.attackFrames;
    const def = spriteLibrary.sheet(this.name, 'attack');
    this.seq++;
    if (!pf?.recover_or_fan?.length || !def) {
      this.visual.release();
      return;
    }
    const col = pf.recover_or_fan[0];
    this.visual.hold('attack', this.visual.facing, col, time, ms ?? frameDurations(def)[col] ?? 0);
  }

  holdFacing(time: number, target: Vec, ms?: number): void {
    if (this.attackFrames?.recover_or_fan?.length) {
      this.visual.facing = this.dirTo(target);
      this.recover(time, ms);
    } else {
      this.seq++;
      this.visual.oneShot('attack', this.dirTo(target), time, ms);
    }
  }

  recoverHoldMs(): number {
    const def = spriteLibrary.sheet(this.name, 'attack');
    const col = this.attackFrames?.recover_or_fan?.[0];
    return def && col !== undefined ? (frameDurations(def)[col] ?? 0) : 0;
  }

  release(): void {
    this.seq++;
    this.visual.release();
  }

  // --- 54라운드 v3 동작 ---

  phase(
    action: string,
    phase: string,
    time: number,
    opts: { loop?: boolean; fitMs?: number; target?: Vec; thenLoop?: string } = {},
  ): boolean {
    const def = this.sheet(action);
    const cols = def?.phaseFrames?.[phase];
    if (!def || !cols || cols.length === 0) return false;
    const dir = this.dirTo(opts.target);
    const token = ++this.seq;
    if (opts.loop) {
      const d = frameDurations(def);
      const avg = cols.reduce((a, c) => a + (d[c] ?? 100), 0) / cols.length;
      return this.visual.loopFrames(action, dir, cols, avg);
    }
    const ms = this.visual.playFrames(action, dir, cols, time, opts.fitMs);
    if (ms > 0 && opts.thenLoop) {
      const next = opts.thenLoop;
      this.host.scene.time.delayedCall(ms, () => {
        if (this.host.active && token === this.seq) this.phase(action, next, this.host.scene.time.now, { loop: true });
      });
    }
    return ms > 0;
  }

  play(action: string, time: number, opts: { fitMs?: number; keyAtMs?: number; target?: Vec } = {}): boolean {
    const def = this.sheet(action);
    if (!def) return false;
    this.seq++;
    const dir = this.dirTo(opts.target);
    const kf = def.impactFrame ?? def.releaseFrame;
    const key = opts.keyAtMs !== undefined && typeof kf === 'number' ? { frame: kf, atMs: opts.keyAtMs } : undefined;
    return this.visual.oneShot(action, dir, time, opts.fitMs, key) > 0;
  }

  keyFrameMs(action: string, key: 'impactFrame' | 'releaseFrame'): number | null {
    const def = this.sheet(action);
    const kf = def?.[key];
    if (!def || typeof kf !== 'number') return null;
    return frameStarts(def)[kf] ?? null;
  }

  lean(rad: number): void {
    this.host.setRotation(rad);
  }

  lie(on: boolean): void {
    const sign = this.visual.facing === 'left' ? -1 : 1;
    this.host.setRotation(on ? BOSS_FX.LIE_ROTATION * sign : 0);
  }

  get cupArt(): boolean {
    return Boolean(this.sheet('drink')?.cupAnchors);
  }

  /** 현재 프레임이 그 동작 시트면 (열, 행) */
  private frameOf(action: string): { def: SheetJson; col: number; row: number; dir: Facing } | null {
    const def = this.sheet(action);
    const tex = spriteLibrary.textureKey(this.name, action);
    if (!def || !tex || this.host.texture.key !== tex) return null;
    const idx = Number(this.host.frame.name);
    if (!Number.isFinite(idx)) return null;
    const row = Math.floor(idx / def.frames);
    const dir = (def.directions[row] as Facing | undefined) ?? this.visual.facing;
    return { def, col: idx % def.frames, row, dir };
  }

  private toWorld(def: SheetJson, x: number, y: number): Vec {
    const s = artScale(def);
    return { x: this.host.x + (x - def.pivot.x) * s, y: this.host.y + (y - def.pivot.y) * s };
  }

  cupRect(fallback: { w: number; h: number; lift: number }): { x: number; y: number; w: number; h: number } {
    const f = this.frameOf('drink');
    const r = f ? asRect(anchorAt(f.def.cupAnchors, f.dir, f.col, f.def.frames, f.row)) : null;
    if (f && r && r.w > 0 && r.h > 0) {
      // 계약 §15 {x, y, w, h}: x·y = 사각형 왼쪽 위 (시트 도트) — 아트 확인 질문 (보고서)
      const a = this.toWorld(f.def, r.x, r.y);
      const s = artScale(f.def);
      return { x: a.x, y: a.y, w: r.w * s, h: r.h * s };
    }
    return {
      x: this.host.x - fallback.w / 2,
      y: this.host.y - fallback.lift - fallback.h / 2,
      w: fallback.w,
      h: fallback.h,
    };
  }

  anchor(action: string, key: 'footAnchors' | 'handAnchors', at?: 'impactFrame' | 'releaseFrame'): Vec | null {
    const f = this.frameOf(action);
    if (!at) {
      if (!f) return null;
      const r = asRect(anchorAt(f.def[key], f.dir, f.col, f.def.frames, f.row));
      return r ? this.toWorld(f.def, r.x + r.w / 2, r.y + r.h / 2) : null;
    }
    // 이벤트 프레임의 점 (재생 전 예고 동안에도 같은 자리). 그 프레임이 null 이면(횃불을 놓은 프레임) 바로 앞의 점 — 아트 54라운드 2차
    const def = this.sheet(action);
    const kf = def?.[at];
    if (!def || typeof kf !== 'number') return null;
    const dir = f?.dir ?? this.visual.facing;
    const row = f?.row ?? Math.max(0, def.directions.indexOf(dir));
    for (let col = Math.min(kf, def.frames - 1); col >= 0; col--) {
      const r = asRect(anchorAt(def[key], dir, col, def.frames, row));
      if (r) return this.toWorld(def, r.x + r.w / 2, r.y + r.h / 2);
    }
    return null;
  }
}
