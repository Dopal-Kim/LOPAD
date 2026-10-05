import { BOSS_DARK_PHASE_BY_FLOOR, BOSS_PHASE_MARKS_BY_FLOOR, BOSS_PHASE_NAMES_BY_FLOOR } from './themeStory';
import { fill } from './fmt';

/**
 * 61라운드 단계 3 보스 UI (P6·P10) — 순수 계산 (Phaser·계약 값 import 없음).
 *
 * 계약 스냅샷 `boss` 는 `{ name, hp, maxHp, phase }` 이고, 시스템 D(보스 재구성)가 더할 수 있는 값을 **있으면 쓰고 없으면 기본값**으로 읽는다:
 *  - `phaseName: string` / `phaseNames: string[]` — 없으면 층 기본(1층 얼큰·만취·인사불성), 그것도 없으면 'n국면'.
 *  - `phaseMarks: number[]` (체력 비율 0~1, 또는 퍼센트) — 없으면 층 기본(1층 65%·30%).
 *  - `broken: boolean | { leftMs, totalMs }` — 파훼로 무너진 동안(받는 피해 증가).
 *  - `candles: { x, y, lit }[]` (논리 화면 좌표) · `dark: boolean`(또는 `lightsOut`) — 3국면 촛대 안내.
 * 이벤트 `BOSS_BREAK`(계약 추가 예정) 페이로드 `{ kind: 'cup'|'pillar'|'cask'|'stumble'|'finisher', label?, text? }`.
 */
export interface BossCandle {
  x: number;
  y: number;
  lit: boolean;
}

export interface BossLook {
  name: string;
  hp: number;
  maxHp: number;
  ratio: number;
  /** 1부터 */
  phase: number;
  phaseNames: string[];
  phaseName: string;
  /** 국면 경계 체력 비율 (큰 것부터) */
  marks: number[];
  broken: { leftMs: number; totalMs: number } | null;
  candles: BossCandle[] | null;
  /** 어둠 국면 (촛대 안내를 띄운다) */
  dark: boolean;
}

function num(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}
function strs(v: unknown): string[] | null {
  if (!Array.isArray(v)) return null;
  const out = v.filter((x): x is string => typeof x === 'string' && x.trim().length > 0).map((x) => x.trim());
  return out.length ? out : null;
}

/** 국면 이름 목록: 스냅샷 → 층 기본 → 빈 목록 */
export function phaseNamesFor(stageIndex: number, given?: unknown): string[] {
  return strs(given) ?? [...(BOSS_PHASE_NAMES_BY_FLOOR[stageIndex] ?? [])];
}

/** 국면 이름 (목록에 없으면 'n국면') */
export function phaseNameOf(phase: number, names: string[], nTemplate: string): string {
  return names[phase - 1] ?? fill(nTemplate, { n: phase });
}

/** 국면 경계: 0~1 비율로 (1 보다 크면 퍼센트로 본다), 0·1 끝과 중복은 뺀다, 큰 것부터 */
export function normMarks(v: unknown, stageIndex: number): number[] {
  const raw = Array.isArray(v) ? v.map(num).filter((x): x is number => x !== null) : null;
  const src = raw && raw.length ? raw : [...(BOSS_PHASE_MARKS_BY_FLOOR[stageIndex] ?? [])];
  const out = src.map((m) => (m > 1 ? m / 100 : m)).filter((m) => m > 0 && m < 1);
  return [...new Set(out)].sort((a, b) => b - a);
}

function readCandles(v: unknown): BossCandle[] | null {
  if (!Array.isArray(v)) return null;
  const out: BossCandle[] = [];
  for (const c of v) {
    if (!c || typeof c !== 'object') continue;
    const o = c as Record<string, unknown>;
    const x = num(o.x);
    const y = num(o.y);
    if (x === null || y === null) continue;
    const lit = typeof o.lit === 'boolean' ? o.lit : typeof o.on === 'boolean' ? o.on : false;
    out.push({ x, y, lit });
  }
  return out;
}

function readBroken(v: unknown): BossLook['broken'] {
  if (v === true) return { leftMs: 0, totalMs: 0 };
  if (!v || typeof v !== 'object') return null;
  const o = v as Record<string, unknown>;
  const left = num(o.leftMs) ?? 0;
  const total = num(o.totalMs) ?? num(o.durationMs) ?? 0;
  if (o.active === false) return null;
  return { leftMs: Math.max(0, left), totalMs: Math.max(0, total) };
}

/** 스냅샷 `boss` 읽기 (살아 있지 않거나 없으면 null) */
export function readBoss(boss: unknown, stageIndex: number, nTemplate: string): BossLook | null {
  if (!boss || typeof boss !== 'object') return null;
  const o = boss as Record<string, unknown>;
  const hp = num(o.hp) ?? 0;
  const maxHp = Math.max(1, num(o.maxHp) ?? 1);
  if (hp <= 0) return null;
  const phase = Math.max(1, Math.round(num(o.phase) ?? 1));
  const names = phaseNamesFor(stageIndex, o.phaseNames);
  const given = typeof o.phaseName === 'string' && o.phaseName.trim() ? o.phaseName.trim() : null;
  const darkPhase = BOSS_DARK_PHASE_BY_FLOOR[stageIndex];
  const darkFlag = typeof o.dark === 'boolean' ? o.dark : typeof o.lightsOut === 'boolean' ? o.lightsOut : null;
  return {
    name: typeof o.name === 'string' ? o.name : '',
    hp,
    maxHp,
    ratio: Math.max(0, Math.min(1, hp / maxHp)),
    phase,
    phaseNames: names,
    phaseName: given ?? phaseNameOf(phase, names, nTemplate),
    marks: normMarks(o.phaseMarks, stageIndex),
    broken: readBroken(o.broken),
    candles: readCandles(o.candles),
    dark: darkFlag ?? (darkPhase !== undefined && phase >= darkPhase),
  };
}

/** 국면 띠 '얼큰 → 만취 → 인사불성': 지난 국면 · 지금 · 다음 */
export function phaseStrip(names: string[], phase: number): { text: string; state: 'past' | 'now' | 'next' }[] {
  return names.map((text, i) => ({ text, state: i + 1 < phase ? 'past' : i + 1 === phase ? 'now' : 'next' }));
}

/** 국면 눈금 x (막대 안쪽 왼쪽·폭, 정수). 체력이 이미 지나간 눈금은 passed */
export function tickXs(
  marks: number[],
  innerX: number,
  innerW: number,
  ratio: number,
): { x: number; passed: boolean }[] {
  return marks.map((m) => ({ x: innerX + Math.round(innerW * m), passed: ratio <= m }));
}

export type CandleGuide =
  { kind: 'mark'; x: number; y: number } | { kind: 'arrow'; x: number; y: number; dx: number; dy: number };

/**
 * 꺼진 촛대 안내: 화면 안(가장자리 여백 안)이면 촛대 위 표지, 밖이면 화면 가운데에서 촛대 쪽으로 그은 선이
 * 여백 사각형과 만나는 자리에 화살(dx·dy = 단위 방향). 켜진 촛대는 빼고, 가까운 것부터.
 */
export function candleGuides(
  candles: BossCandle[] | null,
  screen: { w: number; h: number },
  edge: number,
  center?: { x: number; y: number },
): CandleGuide[] {
  if (!candles) return [];
  const cx = center?.x ?? screen.w / 2;
  const cy = center?.y ?? screen.h / 2;
  const left = edge;
  const right = screen.w - edge;
  const top = edge;
  const bottom = screen.h - edge;
  return candles
    .filter((c) => !c.lit)
    .map((c) => ({ c, d: Math.hypot(c.x - cx, c.y - cy) }))
    .sort((a, b) => a.d - b.d)
    .map(({ c, d }): CandleGuide => {
      if (c.x >= left && c.x <= right && c.y >= top && c.y <= bottom)
        return { kind: 'mark', x: Math.round(c.x), y: Math.round(c.y) };
      const vx = c.x - cx;
      const vy = c.y - cy;
      const len = d || 1;
      // 가운데에서 촛대 쪽 선이 여백 사각형을 나가는 자리
      const tx = vx > 0 ? (right - cx) / vx : vx < 0 ? (left - cx) / vx : Infinity;
      const ty = vy > 0 ? (bottom - cy) / vy : vy < 0 ? (top - cy) / vy : Infinity;
      const t = Math.min(tx, ty);
      return { kind: 'arrow', x: Math.round(cx + vx * t), y: Math.round(cy + vy * t), dx: vx / len, dy: vy / len };
    });
}

/** 파훼 종류 (텍스트 팩 C · 54라운드 패턴 이름) */
export type BossBreakKind = 'cup' | 'pillar' | 'cask' | 'stumble' | 'finisher' | 'other';
export interface BossBreakView {
  kind: BossBreakKind;
  finisher: boolean;
  /** 시스템이 준 이름·문장 (없으면 UI 기본 낱말) */
  label: string | null;
  text: string | null;
}
const BREAK_KINDS: Record<string, BossBreakKind> = {
  cup: 'cup',
  pillar: 'pillar',
  cask: 'cask',
  stumble: 'stumble',
  finisher: 'finisher',
};

export function readBossBreak(p: unknown): BossBreakView | null {
  if (!p || typeof p !== 'object') return null;
  const o = p as Record<string, unknown>;
  const raw = typeof o.kind === 'string' ? o.kind : '';
  const kind = BREAK_KINDS[raw] ?? 'other';
  const s = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v.trim() : null);
  return {
    kind,
    finisher: kind === 'finisher' || o.finisher === true,
    label: s(o.label) ?? s(o.name),
    text: s(o.text),
  };
}

/** 파훼 이름 낱말 키 (textStory) */
export function breakLabelKey(
  kind: BossBreakKind,
): 'breakCup' | 'breakPillar' | 'breakCask' | 'breakStumble' | 'breakAny' {
  switch (kind) {
    case 'cup':
      return 'breakCup';
    case 'pillar':
      return 'breakPillar';
    case 'cask':
      return 'breakCask';
    case 'stumble':
      return 'breakStumble';
    default:
      return 'breakAny';
  }
}

/** BOSS_STARTED·PHASE·DIED 페이로드 (계약 §1 `{ name, hp, maxHp, phase }` + 있으면 `phaseName`·`finisher`) */
export function readBossEvent(p: unknown): {
  name: string;
  phase: number;
  phaseName: string | null;
  finisher: boolean;
} {
  const o = p && typeof p === 'object' ? (p as Record<string, unknown>) : {};
  return {
    name: typeof o.name === 'string' ? o.name : '',
    phase: Math.max(1, Math.round(num(o.phase) ?? 1)),
    phaseName: typeof o.phaseName === 'string' && o.phaseName.trim() ? o.phaseName.trim() : null,
    finisher: o.finisher === true,
  };
}
