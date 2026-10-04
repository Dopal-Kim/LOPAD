/**
 * 55라운드 Q8 재 파편 입자 수식 (계약 §16 `fx/v3/particles_ash` kinds·recipes). Phaser 의존 없음 — 그리기는 `ashParticles`.
 * - kinds.<이름>: frames [시작, 끝] · frameMode loop(frameMs 간격 반복)|life(수명 진행도로 식음) · lifeMs·speedPxPerSec [최소, 최대] ·
 *   gravityPxPerSec2(+ 아래) · dragPerSec(속도 × e^(−drag·t)) · swayPx/Hz · rotate(진행 방향)
 * - recipes.<적중 시트>: kind → 개수 + coneDeg (공격 방향 ±coneDeg/2 로 발사)
 * 길이(속도·중력·흔들림)는 시트 도트 단위 → `unit`(= 도트 배율, pixelScale 0.5 → 월드 0.25)으로 월드 단위로 바꾼다.
 */

export interface AshKind {
  start: number;
  count: number;
  mode: 'loop' | 'life';
  lifeMs: [number, number];
  speed: [number, number];
  gravity: number;
  drag: number;
  frameMs: number;
  swayPx: number;
  swayHz: number;
  rotate: boolean;
}

export interface AshRecipe {
  kinds: Record<string, number>;
  coneDeg: number;
}

export interface AshParticle {
  kind: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  ageMs: number;
  lifeMs: number;
  /** 흔들림 위상·loop 시작 프레임을 흩는 값 (0..1) */
  seed: number;
}

const DEFAULT_FRAME_MS = 80;

function num(v: unknown, fallback: number): number {
  return typeof v === 'number' && Number.isFinite(v) ? v : fallback;
}

function range(v: unknown, fallback: [number, number]): [number, number] {
  if (Array.isArray(v) && v.length >= 2 && typeof v[0] === 'number' && typeof v[1] === 'number')
    return [Math.min(v[0], v[1]), Math.max(v[0], v[1])];
  if (typeof v === 'number') return [v, v];
  return fallback;
}

/** JSON kinds → 월드 단위 kind 표 (형식이 틀린 항목은 버린다) */
export function parseAshKinds(raw: unknown, unit: number): Record<string, AshKind> {
  const out: Record<string, AshKind> = {};
  if (!raw || typeof raw !== 'object') return out;
  for (const [name, v] of Object.entries(raw as Record<string, unknown>)) {
    const k = v as Record<string, unknown> | null;
    if (!k || typeof k !== 'object') continue;
    const fr = range(k.frames, [-1, -1]);
    if (fr[0] < 0) continue;
    const [s0, s1] = range(k.speedPxPerSec, [0, 0]);
    out[name] = {
      start: fr[0],
      count: fr[1] - fr[0] + 1,
      mode: k.frameMode === 'life' ? 'life' : 'loop',
      lifeMs: range(k.lifeMs, [300, 300]),
      speed: [s0 * unit, s1 * unit],
      gravity: num(k.gravityPxPerSec2, 0) * unit,
      drag: num(k.dragPerSec, 0),
      frameMs: num(k.frameMs, DEFAULT_FRAME_MS),
      swayPx: num(k.swayPx, 0) * unit,
      swayHz: num(k.swayHz, 0),
      rotate: k.rotate === true,
    };
  }
  return out;
}

/** JSON recipes → 시트 id 별 묶음 */
export function parseAshRecipes(raw: unknown): Record<string, AshRecipe> {
  const out: Record<string, AshRecipe> = {};
  if (!raw || typeof raw !== 'object') return out;
  for (const [sheet, v] of Object.entries(raw as Record<string, unknown>)) {
    if (!v || typeof v !== 'object') continue;
    const kinds: Record<string, number> = {};
    let coneDeg = 60;
    for (const [k, n] of Object.entries(v as Record<string, unknown>)) {
      if (k === 'coneDeg') coneDeg = num(n, coneDeg);
      else if (typeof n === 'number' && n > 0) kinds[k] = Math.floor(n);
    }
    out[sheet] = { kinds, coneDeg };
  }
  return out;
}

function lerp(r: [number, number], t: number): number {
  return r[0] + (r[1] - r[0]) * t;
}

/**
 * 묶음 하나를 (x, y) 에서 진행 각 `angle`(rad) 둘레 ±coneDeg/2 로 낸다. `factor` = 개수 배율(동시 다수 적중이면 0.5, 올림).
 * `rng` 는 0..1
 */
export function spawnAsh(
  recipe: AshRecipe,
  kinds: Record<string, AshKind>,
  x: number,
  y: number,
  angle: number,
  factor: number,
  rng: () => number,
): AshParticle[] {
  const out: AshParticle[] = [];
  const half = ((recipe.coneDeg / 2) * Math.PI) / 180;
  for (const [name, n] of Object.entries(recipe.kinds)) {
    const k = kinds[name];
    if (!k) continue;
    const count = Math.ceil(n * Math.max(0, factor));
    for (let i = 0; i < count; i++) {
      const a = angle + (rng() * 2 - 1) * half;
      const sp = lerp(k.speed, rng());
      out.push({
        kind: name,
        x,
        y,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp,
        ageMs: 0,
        lifeMs: lerp(k.lifeMs, rng()),
        seed: rng(),
      });
    }
  }
  return out;
}

/** dtMs 만큼 진행 (끌림 → 중력 → 이동). 수명이 다하면 false */
export function stepAsh(p: AshParticle, k: AshKind, dtMs: number): boolean {
  const dt = Math.max(0, dtMs) / 1000;
  const keep = Math.exp(-k.drag * dt);
  p.vx *= keep;
  p.vy = p.vy * keep + k.gravity * dt;
  p.x += p.vx * dt;
  p.y += p.vy * dt;
  p.ageMs += dtMs;
  return p.ageMs < p.lifeMs;
}

/** 지금 프레임 (시트 열): loop = frameMs 간격으로 범위 반복(시작은 seed 로 흩음), life = 수명 진행도 */
export function ashFrame(p: AshParticle, k: AshKind): number {
  if (k.count <= 1) return k.start;
  if (k.mode === 'life') {
    const t = Math.max(0, Math.min(0.9999, p.ageMs / Math.max(1, p.lifeMs)));
    return k.start + Math.floor(t * k.count);
  }
  const offset = Math.floor(p.seed * k.count);
  return k.start + ((Math.floor(p.ageMs / Math.max(1, k.frameMs)) + offset) % k.count);
}

/** 그릴 위치 = 상태 위치 + 좌우 흔들림, 도트 격자(`unit`)에 맞춤 */
export function ashDrawPos(p: AshParticle, k: AshKind, unit: number): { x: number; y: number } {
  const sway = k.swayPx > 0 ? k.swayPx * Math.sin(2 * Math.PI * (k.swayHz * (p.ageMs / 1000) + p.seed)) : 0;
  const snap = (v: number) => (unit > 0 ? Math.round(v / unit) * unit : v);
  return { x: snap(p.x + sway), y: snap(p.y) };
}
