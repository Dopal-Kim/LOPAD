/**
 * 54라운드 꺾은선 예고 (57라운드 B8: telegraph.ts 에서 분리): 선 시트 토막을 마디마다 이어 붙인다
 * (시트가 없으면 Graphics 꺾은 점선). 끝에 화살촉, opts.aura 면 첫 점(또는 auraAt)에 수렴 오라.
 * 깜빡임·마감 직전 가속은 `TelegraphFx` 의 선 예고와 같은 규칙.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX } from '../../core/Constants';
import { spriteLibrary } from '../sprites/sprites';
import { FX_ACTION, frameDurations, fxDrawScale } from '../sprites/spriteDefs';
import { auraLabel, drawDashedPolyline, makeAura, makeTip, placeholderAlpha, speedUpAura } from './shapes';
import type {
  AuraObject,
  Point,
  TelegraphOptions,
  TelegraphPathHandle,
  TelegraphStyle,
  TelegraphSummary,
} from './types';

interface PathMarker {
  points: Point[];
  segs: Phaser.GameObjects.TileSprite[];
  gfx: Phaser.GameObjects.Graphics | null;
  tip: Phaser.GameObjects.Graphics;
  aura?: AuraObject;
  texture?: string;
  scale: number;
  originX: number;
  originY: number;
  frameH: number;
  createdAt: number;
  expireAt: number;
  blinkMs: number;
  nextBlinkAt: number;
  phase: number;
  final: boolean;
  alive: boolean;
}

export class PathTelegraphs {
  private readonly paths = new Set<PathMarker>();

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly style: TelegraphStyle,
  ) {}

  get size(): number {
    return this.paths.size;
  }

  create(points: readonly Point[], durationMs: number, opts: TelegraphOptions = {}): TelegraphPathHandle {
    const id = ENEMY_FX.TELEGRAPH_IDS.LINE;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    const now = this.scene.time.now;
    const sheet = Boolean(def && texture && this.scene.textures.exists(texture));
    const blink = sheet ? frameDurations(def!)[0] || ENEMY_FX.PLACEHOLDER.BLINK_MS : ENEMY_FX.PLACEHOLDER.BLINK_MS;
    const m: PathMarker = {
      points: [],
      segs: [],
      gfx: sheet ? null : this.scene.add.graphics().setDepth(DEPTH.FX_GROUND),
      tip: makeTip(this.scene, this.style),
      texture: sheet ? texture! : undefined,
      scale: sheet ? fxDrawScale(def!) : 1,
      originX: sheet ? def!.pivot.x / def!.frameWidth : 0,
      originY: sheet ? def!.pivot.y / def!.frameHeight : 0,
      frameH: sheet ? def!.frameHeight : 0,
      createdAt: now,
      expireAt: now + durationMs,
      blinkMs: blink,
      nextBlinkAt: now + blink,
      phase: 0,
      final: false,
      alive: true,
    };
    this.paths.add(m);
    this.draw(m, points);
    if (opts.aura && points.length > 0)
      m.aura = makeAura(this.scene, opts.auraAt?.x ?? points[0].x, opts.auraAt?.y ?? points[0].y, this.style);
    return {
      kind: 'path',
      aim: (x, y) => {
        if (!m.alive || m.points.length === 0) return;
        const dx = x - m.points[0].x;
        const dy = y - m.points[0].y;
        this.draw(
          m,
          m.points.map((p) => ({ x: p.x + dx, y: p.y + dy })),
        );
      },
      setPoints: (pts) => {
        if (m.alive) this.draw(m, pts);
      },
      end: () => this.release(m),
      get active() {
        return m.alive;
      },
    };
  }

  /** 매 프레임: 만료·마감 직전 가속·깜빡임 */
  update(time: number): void {
    for (const m of [...this.paths]) this.updateOne(m, time);
  }

  /** 61라운드: 그림 개체 전부 (어둠 위로 올리기 — TelegraphFx.setAboveDark) */
  forEachObject(fn: (o: { depth: number; setDepth(d: number): unknown }) => void): void {
    for (const m of this.paths) {
      for (const s of m.segs) fn(s);
      if (m.gfx) fn(m.gfx);
      fn(m.tip);
      if (m.aura) fn(m.aura);
    }
  }

  /** 히트스톱: 오라 시트 애니 정지 */
  setPaused(on: boolean): void {
    for (const p of this.paths)
      if (p.aura instanceof Phaser.GameObjects.Sprite) {
        if (on) p.aura.anims.pause();
        else p.aura.anims.resume();
      }
  }

  summary(now: number): TelegraphSummary[] {
    return [...this.paths].map((m) => {
      const first = m.points[0] ?? { x: 0, y: 0 };
      const last = m.points[m.points.length - 1] ?? first;
      let length = 0;
      for (let i = 1; i < m.points.length; i++)
        length += Math.hypot(m.points[i].x - m.points[i - 1].x, m.points[i].y - m.points[i - 1].y);
      return {
        kind: 'path' as const,
        x: Math.round(first.x),
        y: Math.round(first.y),
        angle: +Math.atan2(last.y - first.y, last.x - first.x).toFixed(3),
        length: Math.round(length),
        radius: 0,
        sheet: m.segs.length > 0,
        remainingMs: Math.max(0, Math.round(m.expireAt - now)),
        final: m.final,
        frame: m.segs.length > 0 ? m.phase : null,
        scale: m.scale,
        closingRatio: null,
        tip: true,
        aura: auraLabel(m.aura),
        alpha: 1,
        points: m.points.length,
      };
    });
  }

  /** 꺾은선: 마디 몇 군데 (어둠 속에서도 경로 전체가 읽히게) */
  lightPoints(out: { x: number; y: number; radius: number }[]): void {
    for (const m of this.paths) {
      if (!m.alive || m.points.length === 0) continue;
      const step = Math.max(1, Math.floor(m.points.length / ENEMY_FX.PATH_LIGHT_POINTS));
      for (let i = 0; i < m.points.length; i += step) out.push({ x: m.points[i].x, y: m.points[i].y, radius: 0 });
    }
  }

  destroy(): void {
    for (const m of [...this.paths]) this.release(m);
  }

  private draw(m: PathMarker, points: readonly Point[]): void {
    m.points = points.map((p) => ({ x: p.x, y: p.y }));
    const n = Math.max(0, m.points.length - 1);
    if (m.texture) {
      while (m.segs.length < n)
        m.segs.push(
          this.scene.add
            .tileSprite(0, 0, 1, m.frameH, m.texture, m.phase)
            .setOrigin(m.originX, m.originY)
            .setScale(m.scale, ENEMY_FX.BOLD.LINE_SCALE_Y * m.scale)
            .setDepth(DEPTH.FX_GROUND),
        );
      for (let i = 0; i < m.segs.length; i++) {
        const seg = m.segs[i];
        if (i >= n) {
          seg.setVisible(false);
          continue;
        }
        const a = m.points[i];
        const b = m.points[i + 1];
        const len = Math.hypot(b.x - a.x, b.y - a.y);
        // 마디 사이 틈이 보이지 않게 1px 겹친다
        seg
          .setVisible(len > 0.01)
          .setPosition(a.x, a.y)
          .setRotation(Math.atan2(b.y - a.y, b.x - a.x))
          .setSize(Math.max(1, Math.round((len + 1) / m.scale)), m.frameH);
      }
    } else if (m.gfx) drawDashedPolyline(m.gfx, m.points);
    if (n >= 1) {
      const a = m.points[n - 1];
      const b = m.points[n];
      m.tip
        .setVisible(true)
        .setPosition(Math.round(b.x), Math.round(b.y))
        .setRotation(Math.atan2(b.y - a.y, b.x - a.x));
    } else m.tip.setVisible(false);
  }

  private updateOne(m: PathMarker, time: number): void {
    const B = ENEMY_FX.BOLD;
    if (time >= m.expireAt) {
      this.release(m);
      return;
    }
    if (!m.final && m.expireAt - time <= B.FINAL_MS) {
      m.final = true;
      speedUpAura(m.aura);
      m.nextBlinkAt = Math.min(m.nextBlinkAt, time);
    }
    if (time < m.nextBlinkAt) return;
    m.nextBlinkAt = time + (m.final ? m.blinkMs / B.FINAL_BLINK_DIV : m.blinkMs);
    m.phase = m.phase === 0 ? 1 : 0;
    const low = m.phase === 1;
    for (const seg of m.segs) {
      seg.setFrame(m.phase);
      if (m.final) seg.setAlpha(low ? B.FINAL_LOW_ALPHA : 1);
    }
    m.gfx?.setAlpha(placeholderAlpha(low));
    if (m.aura instanceof Phaser.GameObjects.Graphics) m.aura.setAlpha(placeholderAlpha(low));
    m.tip.setAlpha(low ? 0.6 : 1);
  }

  private release(m: PathMarker): void {
    if (!m.alive) return;
    m.alive = false;
    this.paths.delete(m);
    for (const s of m.segs) s.destroy();
    m.gfx?.destroy();
    m.tip.destroy();
    m.aura?.destroy();
  }
}
