/**
 * 잔상 궤적 리본 (42라운드 Q3, fx-design §6.1). 베기 호·대쉬 베기 이펙트의 이전 위치를 이어 그리는 정수 픽셀 폴리라인.
 * - 시트 JSON `trail {color, alpha, ms, fromFrame, widthRatio}` 가 있으면 그 값(색 = 몸통, 수명, 폭 = BAND_PX × 비율),
 *   없으면 kind 기본값. 투사체는 꼬리 시트가 있으므로 리본을 쓰지 않는다(fx-design §6.1).
 * - 두께 최신 → 오래된 1px, 색 = 코어(백열 G15) → 층 강조색 → 몸통(무기 보조색 W1) → 투명.
 * - Graphics 하나가 트레일 하나. 매 프레임 `source()` 에서 위치를 받아 샘플에 넣고(SAMPLE_MS 간격), 수명이 지난 샘플은 버린다.
 *   source 가 null 을 돌려주면 더 찍지 않고 남은 샘플이 사라질 때까지 그린다.
 * - 히트스톱 중 `setPaused(true)` 면 샘플 시각을 멈춘 시간만큼 뒤로 미뤄 그대로 유지한다.
 * - `feelSettings.trail` 이 false 면 `start()` 가 아무것도 만들지 않는다.
 * 수식(색·두께 보간)은 Phaser 없이 `trailMath.ts` 에서 테스트한다.
 */
import Phaser from 'phaser';
import { FEEL } from '../core/Constants';
import { PALETTE } from '../data';
import { feelSettings } from './feel';
import { fxCoreColor, fxWeaponColor, hexToInt, rampFor } from './palette';
import { segmentStyle, type TrailPalette } from './trailMath';

export type TrailKind = 'slash' | 'sheet';

/** 현재 위치. null 이면 샘플링 종료 */
export type TrailSource = () => { x: number; y: number } | null;

export interface TrailOptions {
  /** 샘플 상한·수명 (없으면 kind 기본값) */
  samples?: number;
  lifeMs?: number;
  /** 몸통 색 덮어쓰기 (JSON trail.color) · 알파 배율 */
  color?: number;
  alpha?: number;
  /** 최신 구간 두께 px (없으면 WIDTH_FROM) */
  width?: number;
  depth: number;
}

export interface TrailHandle {
  readonly id: number;
  /** 샘플링 종료 (남은 샘플은 수명대로 사라진다) */
  stop(): void;
  readonly active: boolean;
}

interface Sample {
  x: number;
  y: number;
  t: number;
}

interface Trail {
  id: number;
  kind: TrailKind;
  g: Phaser.GameObjects.Graphics;
  source: TrailSource | null;
  samples: Sample[];
  maxSamples: number;
  lifeMs: number;
  palette: TrailPalette;
  alpha: number;
  widthFrom: number;
  lastSampleAt: number;
}

export class TrailRenderer {
  private readonly trails = new Set<Trail>();
  private nextId = 1;
  private paused = false;
  private pausedAt = 0;
  private accent: number = FEEL.TRAIL.CORE_COLOR;
  private weapon: number | null = null;
  private core: number = FEEL.TRAIL.CORE_COLOR;
  /** 디버그: 만든 수 */
  count = 0;

  constructor(private readonly scene: Phaser.Scene) {
    const core = fxCoreColor(PALETTE, 0);
    if (core) this.core = hexToInt(core);
  }

  /** 층 진입: 강조색 = 층 램프 light1. 무기: 몸통 = 보조색 W1 (fx-design §6.1, 팔레트 fx 블록이 없으면 강조색만) */
  setContext(floor: number, weaponId: string): void {
    const ramp = rampFor(PALETTE, floor);
    const hex = ramp?.[FEEL.TRAIL.ACCENT_RAMP_INDEX];
    this.accent = hex ? hexToInt(hex) : FEEL.TRAIL.CORE_COLOR;
    const w = fxWeaponColor(PALETTE, weaponId, FEEL.TRAIL.WEAPON_RAMP_INDEX);
    this.weapon = w ? hexToInt(w) : null;
  }

  start(kind: TrailKind, source: TrailSource, opts: TrailOptions): TrailHandle | null {
    if (!feelSettings.trail) return null;
    const K = FEEL.TRAIL.SLASH;
    const lifeMs = Math.max(1, opts.lifeMs ?? K.LIFE_MS);
    // 시트 리본: 수명 동안 SAMPLE_MS 간격으로 찍히는 만큼 (+1)
    const samples = opts.samples ?? (kind === 'sheet' ? Math.ceil(lifeMs / FEEL.TRAIL.SAMPLE_MS) + 1 : K.SAMPLES);
    const g = this.scene.add.graphics().setDepth(opts.depth);
    const t: Trail = {
      id: this.nextId++,
      kind,
      g,
      source,
      samples: [],
      maxSamples: Math.max(2, samples),
      lifeMs,
      palette: {
        core: this.core,
        accent: this.accent,
        body: opts.color ?? this.weapon ?? this.accent,
      },
      alpha: opts.alpha ?? 1,
      widthFrom: Math.max(1, Math.round(opts.width ?? FEEL.TRAIL.WIDTH_FROM)),
      lastSampleAt: -Infinity,
    };
    this.trails.add(t);
    this.count += 1;
    this.sample(t, this.scene.time.now);
    return {
      id: t.id,
      stop: () => {
        t.source = null;
      },
      get active() {
        return t.source !== null || t.samples.length > 0;
      },
    };
  }

  /** 매 프레임: 샘플 추가·만료·그리기 */
  update(time: number): void {
    if (this.paused) return;
    for (const t of this.trails) {
      if (t.source) this.sample(t, time);
      t.samples = t.samples.filter((s) => time - s.t < t.lifeMs);
      if (t.samples.length === 0 && t.source === null) {
        t.g.destroy();
        this.trails.delete(t);
        continue;
      }
      this.draw(t, time);
    }
  }

  /** 히트스톱: 멈춘 동안 샘플 시각을 밀어 그대로 유지 */
  setPaused(on: boolean): void {
    if (on === this.paused) return;
    const now = this.scene.time.now;
    if (on) this.pausedAt = now;
    else {
      const shift = now - this.pausedAt;
      for (const t of this.trails) {
        for (const s of t.samples) s.t += shift;
        t.lastSampleAt += shift;
      }
    }
    this.paused = on;
  }

  summary(): {
    id: number;
    kind: TrailKind;
    samples: number;
    sampling: boolean;
    body: number;
    width: number;
    lifeMs: number;
    points: [number, number][];
  }[] {
    return [...this.trails].map((t) => ({
      id: t.id,
      kind: t.kind,
      body: t.palette.body,
      width: t.widthFrom,
      lifeMs: t.lifeMs,
      samples: t.samples.length,
      sampling: t.source !== null,
      points: t.samples.map((s) => [s.x, s.y] as [number, number]),
    }));
  }

  get activeCount(): number {
    return this.trails.size;
  }

  destroy(): void {
    for (const t of this.trails) t.g.destroy();
    this.trails.clear();
  }

  private sample(t: Trail, time: number): void {
    if (time - t.lastSampleAt < FEEL.TRAIL.SAMPLE_MS) return;
    const p = t.source?.();
    if (!p) {
      t.source = null;
      return;
    }
    const x = Math.round(p.x);
    const y = Math.round(p.y);
    const last = t.samples[t.samples.length - 1];
    if (last && last.x === x && last.y === y) {
      last.t = time; // 제자리면 최신 샘플만 갱신
      return;
    }
    t.samples.push({ x, y, t: time });
    t.lastSampleAt = time;
    while (t.samples.length > t.maxSamples) t.samples.shift();
  }

  /** 오래된 → 최신 순으로 구간을 그린다. 구간 스타일은 최신도(0..1)·나이로 정한다 */
  private draw(t: Trail, time: number): void {
    const g = t.g;
    g.clear();
    const n = t.samples.length;
    if (n < 2) return;
    for (let i = 1; i < n; i++) {
      const a = t.samples[i - 1];
      const b = t.samples[i];
      const recency = i / (n - 1);
      const age = (time - b.t) / t.lifeMs;
      const st = segmentStyle(recency, age, t.palette, t.widthFrom, FEEL.TRAIL.WIDTH_TO);
      if (st.alpha <= 0) continue;
      g.lineStyle(st.width, st.color, st.alpha * t.alpha);
      g.beginPath();
      g.moveTo(a.x, a.y);
      g.lineTo(b.x, b.y);
      g.strokePath();
      if (st.coreWidth > 0) {
        g.lineStyle(st.coreWidth, t.palette.core, st.coreAlpha * t.alpha);
        g.beginPath();
        g.moveTo(a.x, a.y);
        g.lineTo(b.x, b.y);
        g.strokePath();
      }
    }
  }
}
