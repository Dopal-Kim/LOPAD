/**
 * 획 곡선 (51라운드 1절 "획이 너무 두껍고 부드럽지가 않아 … 곡선에도 엄청 매끄러운 연출"): 포인터 입력점을
 * 구심(centripetal) Catmull-Rom 스플라인으로 잇고 **일정 간격(STEP_PX)으로 다시 찍은 표본**을 만든다.
 * 표본마다 경로 길이·속도·폭·빛 세기·생성 시각을 갖는다. 폭은 속도 반응(빠를수록 가늘고 밝게) + 낮은 주파수 흔들림
 * + 시작·끝 가늘어짐(붓 느낌). Phaser·캔버스 의존 없음 — 그리기는 `strokeFxPaint.ts`.
 *
 * 입력점 k 가 들어오면 구간 (k-2 → k-1) 이 확정된다(Catmull-Rom 은 다음 점이 필요). 아직 확정 안 된 마지막 구간은
 * `tail()` 이 임시 표본으로 돌려준다(펜 끝까지 늦지 않게 그리기용, 저장하지 않음).
 */
import { STROKE_FX, gapIntensity, gapWidth, type StrokeFxConfig } from './strokeFxMath';

export interface StrokeSample {
  x: number;
  y: number;
  /** 획 시작부터의 경로 길이 px */
  s: number;
  /** 속도 px/s (평활) */
  v: number;
  /** 틈 폭 px (속도·흔들림·시작 가늘어짐 반영, 끝 가늘어짐은 finish 때) */
  w: number;
  /** 흔들림 없는 폭 px (빛 레이어용 — 넓은 빛 테두리에 흔들림이 부풀어 물결지지 않게) */
  wb: number;
  /** 빛 세기 0~1 */
  i: number;
  /** 생성 시각 (장면 시간 ms) — 식는 곡선 기준 */
  born: number;
}

interface RawPoint {
  x: number;
  y: number;
  t: number;
  v: number;
}

interface SamplerState {
  /** 다음 표본까지 남은 거리 */
  toNext: number;
  /** 지금까지 걸어온 곡선 길이 */
  s: number;
  /** 직전 표본 폭 (평활) */
  lastW: number;
}

/** 0~1 → 0~1 부드러운 계단 */
export function smoothstep(x: number): number {
  const t = Math.max(0, Math.min(1, x));
  return t * t * (3 - 2 * t);
}

/**
 * 구심 Catmull-Rom (Barry–Goldman, alpha 0.5): p1 → p2 사이 t(0~1) 점. 점이 겹치면 직선 보간으로 물러난다.
 * 구심형은 급한 꺾임에서 고리·뾰족한 넘침이 생기지 않는다.
 */
export function catmullRom(
  p0: { x: number; y: number },
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  p3: { x: number; y: number },
  t: number,
  alpha = 0.5,
): { x: number; y: number } {
  const d = (a: { x: number; y: number }, b: { x: number; y: number }) =>
    Math.max(1e-4, Math.pow(Math.hypot(b.x - a.x, b.y - a.y), alpha));
  const t0 = 0;
  const t1 = t0 + d(p0, p1);
  const t2 = t1 + d(p1, p2);
  const t3 = t2 + d(p2, p3);
  const u = t1 + (t2 - t1) * t;
  const lerp = (a: { x: number; y: number }, b: { x: number; y: number }, ta: number, tb: number) => {
    const k = tb - ta < 1e-6 ? 0 : (u - ta) / (tb - ta);
    return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k };
  };
  const a1 = lerp(p0, p1, t0, t1);
  const a2 = lerp(p1, p2, t1, t2);
  const a3 = lerp(p2, p3, t2, t3);
  const b1 = lerp(a1, a2, t0, t2);
  const b2 = lerp(a2, a3, t1, t3);
  return lerp(b1, b2, t1, t2);
}

/** 한 획의 매끄러운 경로 (점진적) */
export class StrokePath {
  private readonly raw: RawPoint[] = [];
  /** 확정된 표본 */
  readonly samples: StrokeSample[] = [];
  private readonly state: SamplerState = { toNext: 0, s: 0, lastW: -1 };
  private speed = 0;
  private finished = false;
  /** 폭 흔들림 위상 (획마다 다르게) */
  private readonly phase: [number, number];

  constructor(
    rnd: () => number = Math.random,
    private readonly C: StrokeFxConfig = STROKE_FX,
  ) {
    this.phase = [rnd() * Math.PI * 2, rnd() * Math.PI * 2];
  }

  get rawCount(): number {
    return this.raw.length;
  }

  get done(): boolean {
    return this.finished;
  }

  /** 지금까지 확정된 길이 */
  get length(): number {
    return this.state.s;
  }

  /** 마지막 입력점의 평활 속도 px/s */
  get lastSpeed(): number {
    return this.speed;
  }

  /** 입력점 추가 (같은 자리면 무시). now = 장면 시간 */
  push(x: number, y: number, t: number, now: number): void {
    if (this.finished) return;
    const prev = this.raw[this.raw.length - 1];
    if (prev) {
      const dist = Math.hypot(x - prev.x, y - prev.y);
      if (dist < this.C.SPLINE.MIN_INPUT_PX) return;
      const inst = (dist / Math.max(this.C.MIN_DT_MS, t - prev.t)) * 1000;
      this.speed = this.raw.length === 1 ? inst : this.speed + (inst - this.speed) * this.C.SPEED_SMOOTH;
      if (this.raw.length === 1) prev.v = this.speed; // 첫 점이 0 속도(굵은 점)로 시작하지 않게
    }
    this.raw.push({ x, y, t, v: this.speed });
    const n = this.raw.length;
    if (n === 1) {
      this.emit(this.state, x, y, 0, this.speed, now, this.samples);
      this.state.toNext = this.C.SPLINE.STEP_PX;
    } else if (n >= 3) this.segment(n - 3, this.state, now, this.samples);
  }

  /** 획 끝: 마지막 구간 확정 + 끝 가늘어짐 */
  finish(now: number): void {
    if (this.finished) return;
    const n = this.raw.length;
    if (n >= 2) this.segment(n - 2, this.state, now, this.samples);
    this.finished = true;
    // 끝점이 간격에 걸리지 않았으면 끝점 그대로 하나 더
    const last = this.raw[n - 1];
    const tail = this.samples[this.samples.length - 1];
    if (last && tail && Math.hypot(last.x - tail.x, last.y - tail.y) > 0.05) {
      const s = this.state.s;
      this.samples.push({ ...tail, x: last.x, y: last.y, s });
    }
    const S = this.C.SPLINE;
    const total = this.samples[this.samples.length - 1]?.s ?? 0;
    for (const p of this.samples) {
      const k = (total - p.s) / S.TAPER_OUT_PX;
      if (k >= 1) continue;
      const f = S.TAPER_MIN + (1 - S.TAPER_MIN) * smoothstep(k);
      p.w *= f;
      p.wb *= f;
    }
  }

  /** 확정 안 된 마지막 구간의 임시 표본 (펜 끝까지). finish 뒤엔 빈 배열 */
  tail(now: number): StrokeSample[] {
    const n = this.raw.length;
    if (this.finished || n < 2) return [];
    const st = { ...this.state };
    const out: StrokeSample[] = [];
    this.segment(n - 2, st, now, out);
    const last = this.raw[n - 1];
    const prev = out[out.length - 1] ?? this.samples[this.samples.length - 1];
    if (prev && Math.hypot(last.x - prev.x, last.y - prev.y) > 0.05)
      out.push({ ...prev, x: last.x, y: last.y, s: st.s });
    return out;
  }

  /** 구간 i → i+1 을 곡선으로 걸으며 STEP 간격 표본 */
  private segment(i: number, st: SamplerState, now: number, out: StrokeSample[]): void {
    const r = this.raw;
    const p1 = r[i];
    const p2 = r[i + 1];
    const p0 = r[i - 1] ?? p1;
    const p3 = r[i + 2] ?? p2;
    const S = this.C.SPLINE;
    const latest = r[r.length - 1].t;
    const chord = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    const m = Math.max(4, Math.ceil(chord / S.SUBDIV_PX));
    let px = p1.x;
    let py = p1.y;
    for (let k = 1; k <= m; k++) {
      const t = k / m;
      const q = catmullRom(p0, p1, p2, p3, t, S.ALPHA);
      let d = Math.hypot(q.x - px, q.y - py);
      let ax = px;
      let ay = py;
      while (d >= st.toNext) {
        const f = st.toNext / d;
        ax += (q.x - ax) * f;
        ay += (q.y - ay) * f;
        st.s += st.toNext;
        d -= st.toNext;
        st.toNext = S.STEP_PX;
        const v = p1.v + (p2.v - p1.v) * t;
        // 생성 시각: 입력 시각을 보간해 지금(마지막 입력점)에서 거슬러 — 이벤트가 몰려 와도 식는 곡선이 고르게
        const born = now - Math.max(0, latest - (p1.t + (p2.t - p1.t) * t));
        this.emit(st, ax, ay, st.s, v, born, out);
      }
      st.toNext -= d;
      st.s += d;
      px = q.x;
      py = q.y;
    }
  }

  private emit(st: SamplerState, x: number, y: number, s: number, v: number, born: number, out: StrokeSample[]): void {
    const S = this.C.SPLINE;
    const base = gapWidth(v, this.C);
    st.lastW = st.lastW < 0 ? base : st.lastW + (base - st.lastW) * S.WIDTH_SMOOTH;
    const [l1, l2] = S.NOISE_WAVE_PX;
    const noise =
      1 +
      S.NOISE_AMP *
        (0.6 * Math.sin((s / l1) * Math.PI * 2 + this.phase[0]) +
          0.4 * Math.sin((s / l2) * Math.PI * 2 + this.phase[1]));
    const taperIn = S.TAPER_MIN + (1 - S.TAPER_MIN) * smoothstep(s / S.TAPER_IN_PX);
    const wb = st.lastW * taperIn;
    out.push({ x, y, s, v, w: wb * noise, wb, i: gapIntensity(v, this.C), born });
  }
}

/** 표본 → 평평한 점 배열 [x0,y0,x1,y1,…] (빛 터짐 광선·경로 자르기용) */
export function flatten(samples: StrokeSample[]): number[] {
  const out: number[] = [];
  for (const p of samples) out.push(p.x, p.y);
  return out;
}

/** 경로 길이 비율 frac 까지의 표본 개수 (빛 터짐 섬광이 획을 따라 달릴 때) */
export function prefixCount(samples: StrokeSample[], frac: number): number {
  if (samples.length === 0) return 0;
  const total = samples[samples.length - 1].s;
  const goal = total * Math.max(0, Math.min(1, frac));
  let lo = 0;
  let hi = samples.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (samples[mid].s <= goal) lo = mid;
    else hi = mid - 1;
  }
  return lo + 1;
}
