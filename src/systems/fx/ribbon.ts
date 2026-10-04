/**
 * 55라운드 Q7·Q14 ④ 칼끝 잔상 리본 (계약 §16 `fx/v3/ribbon_ash`·`ribbon_ash_thin`) — 42라운드 흰 리본(TrailRenderer) 대체.
 * - 점 = `source(t)` 가 주는 위치(칼끝·몸 중심). t 는 플레이 시계 ms(히트스톱 동안 멈춤)라 정지 중에는 리본도 그대로 굳는다.
 *   프레임 사이도 SAMPLE_MS 간격으로 찍어 빠른 칼끝이 직선으로 끊기지 않게 한다.
 * - 그리기 = Phaser Rope(WebGL)에 리본 텍스처를 가로로 늘여 붙인다(꼬리 재 → 머리 호박, 반투명 없음, 세로 = 텍스처 두께).
 *   나이 프레임 = 가장 새 점의 나이 (LIFE_MS 안에 4단계로 식고 사라짐). WebGL 이 아니거나 텍스처가 없으면 1px 선 폴백.
 * - `feelSettings.trail` 이 false 면 만들지 않는다. 수식은 `ribbonMath`.
 */
import Phaser from 'phaser';
import { FEEL } from '../core/Constants';
import { feelSettings } from './feel';
import { pruneRibbon, pushRibbonSample, ribbonAgeFrame, sampleTimes, type RibbonSample } from './ribbonMath';
import { spriteLibrary } from './sprites';
import { FX_ACTION, artScale, fxDrawScale } from './spriteDefs';

/** 플레이 시계 t 의 위치. null 이면 더 찍지 않는다 (남은 점은 수명대로 사라진다) */
export type RibbonSource = (t: number) => { x: number; y: number } | null;

export interface RibbonOptions {
  /** 텍스처 시트 id (없으면 FEEL.RIBBON.SHEET) */
  sheet?: string;
  depth: number;
  lifeMs?: number;
}

export interface RibbonHandle {
  readonly id: number;
  stop(): void;
  readonly active: boolean;
}

interface Ribbon {
  id: number;
  sheet: string;
  source: RibbonSource | null;
  samples: RibbonSample[];
  lifeMs: number;
  lastT: number | null;
  rope: Phaser.GameObjects.Rope | null;
  line: Phaser.GameObjects.Graphics | null;
  frames: number;
  scale: number;
  unit: number;
}

export class RibbonRenderer {
  private readonly ribbons = new Set<Ribbon>();
  private nextId = 1;
  /** 디버그: 만든 수 */
  count = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    /** 플레이 시계 (히트스톱 동안 멈춘 ms) */
    private readonly clock: () => number,
  ) {}

  start(source: RibbonSource, opts: RibbonOptions): RibbonHandle | null {
    if (!feelSettings.trail) return null;
    const sheet = opts.sheet ?? FEEL.RIBBON.SHEET;
    const def = spriteLibrary.sheet(sheet, FX_ACTION);
    const texture = spriteLibrary.textureKey(sheet, FX_ACTION);
    const webgl = this.scene.sys.game.renderer.type === Phaser.WEBGL;
    const useRope = Boolean(def && texture && this.scene.textures.exists(texture) && webgl);
    const r: Ribbon = {
      id: this.nextId++,
      sheet,
      source,
      samples: [],
      lifeMs: Math.max(1, opts.lifeMs ?? FEEL.RIBBON.LIFE_MS),
      lastT: null,
      rope: useRope
        ? this.scene.add
            .rope(0, 0, texture!, 0, [
              { x: 0, y: 0 },
              { x: 1, y: 0 },
            ])
            .setDepth(opts.depth)
            .setVisible(false)
        : null,
      line: useRope ? null : this.scene.add.graphics().setDepth(opts.depth),
      frames: def?.frames ?? 1,
      scale: def ? fxDrawScale(def) : 1,
      unit: def ? artScale(def) : 0,
    };
    this.ribbons.add(r);
    this.count += 1;
    this.sample(r, this.clock());
    this.draw(r, this.clock());
    return {
      id: r.id,
      stop: () => {
        r.source = null;
      },
      get active() {
        return r.source !== null || r.samples.length > 0;
      },
    };
  }

  /** 매 프레임: 점 찍기·버리기·그리기 (히트스톱 중엔 호출되지 않거나 시계가 멈춰 그대로) */
  update(): void {
    const now = this.clock();
    for (const r of this.ribbons) {
      if (r.source) this.sample(r, now);
      pruneRibbon(r.samples, now, r.lifeMs, FEEL.RIBBON.MAX_POINTS);
      if (r.samples.length === 0 && r.source === null) {
        this.release(r);
        continue;
      }
      this.draw(r, now);
    }
  }

  summary(): { id: number; kind: string; samples: number; sampling: boolean; width: number; lifeMs: number }[] {
    return [...this.ribbons].map((r) => ({
      id: r.id,
      kind: r.sheet,
      samples: r.samples.length,
      sampling: r.source !== null,
      width: r.rope ? r.rope.frame.height : 1,
      lifeMs: r.lifeMs,
    }));
  }

  get activeCount(): number {
    return this.ribbons.size;
  }

  destroy(): void {
    for (const r of this.ribbons) this.release(r);
    this.ribbons.clear();
  }

  private release(r: Ribbon): void {
    r.rope?.destroy();
    r.line?.destroy();
    this.ribbons.delete(r);
  }

  private sample(r: Ribbon, now: number): void {
    for (const t of sampleTimes(r.lastT, now, FEEL.RIBBON.SAMPLE_MS)) {
      const p = r.source?.(t);
      if (!p) {
        r.source = null;
        break;
      }
      pushRibbonSample(r.samples, p.x, p.y, t, r.unit);
    }
    r.lastT = now;
  }

  private draw(r: Ribbon, now: number): void {
    const s = r.samples;
    const head = s[s.length - 1];
    if (r.rope) {
      if (s.length < 2) {
        r.rope.setVisible(false);
        return;
      }
      const o = s[0];
      const k = r.scale;
      r.rope.setFrame(ribbonAgeFrame(now - head.t, r.lifeMs, r.frames));
      r.rope.setPosition(o.x, o.y).setScale(k);
      r.rope.setPoints(s.map((p) => ({ x: (p.x - o.x) / k, y: (p.y - o.y) / k })));
      r.rope.setVisible(true);
      return;
    }
    const g = r.line!;
    g.clear();
    if (s.length < 2) return;
    const cold = ribbonAgeFrame(now - head.t, r.lifeMs, 2) > 0;
    const R = FEEL.RIBBON;
    for (let i = 1; i < s.length; i++) {
      const color = cold || i < s.length / 2 ? R.FALLBACK_TAIL : R.FALLBACK_HEAD;
      g.lineStyle(1, color, 1);
      g.lineBetween(s[i - 1].x, s[i - 1].y, s[i].x, s[i].y);
    }
  }
}
