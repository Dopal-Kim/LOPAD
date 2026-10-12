/**
 * 62 루프 1 (P15 · 계약 UI §20) 시작 의식 데이터 (Phaser 의존 없음): `data/narrative.json` ritual — 안내 한 줄 · 획 ↔ 무기 규칙 ·
 * 왜 이 무기인지(무기 목소리 말투) · 회피 시험 결과 한 줄 · 회피 시험 과제(탄생 전장 사수). 형식이 틀리면 부팅에서 바로 예외.
 * 화면 문구에 숫자를 넣지 않는다(판정 수치 금지 — `noDigits`).
 */
import narrativeJson from '../../data/narrative.json';
import { WEAPONS } from './index';

export type TrialGrade = 'S' | 'A' | 'B' | 'C';
export const TRIAL_GRADES: readonly TrialGrade[] = ['S', 'A', 'B', 'C'];

/** 사격 모양: aimed = 주인공을 겨눈 한 발 · fan = 주인공 쪽 부채꼴 여러 발 */
export type TrialPattern = 'aimed' | 'fan';

export interface TrialTaskDef {
  id: string;
  /** 짧은 명령형 (키캡 없음 — verb 로 UI 가 붙인다) */
  label: string;
  verb?: 'dash';
  /** 사수 수 (spots 앞에서부터) — 여럿이면 차례로 쏜다 */
  shooters: number;
  pattern: TrialPattern;
  fanCount?: number;
  fanDeg?: number;
  /** 쏘는 횟수 · 간격 ms */
  volleys: number;
  intervalMs: number;
}

/** 62 art §30 탄생 전장 소품 (structures/v3) — at = 가운데 기준 비율, w·h 칸 */
export interface TrialPropDef {
  sheet: string;
  at: [number, number];
  w: number;
  h: number;
  /** 걷기·화살을 막는 엄폐 */
  solid?: boolean;
  /** 바닥에 깔림 (캐릭터 아래) */
  floor?: boolean;
}

export interface RitualTrialData {
  /** 탄생 전장 타일셋 (route.json 황폐한 전장 지역 타일셋) */
  tileset: string;
  /** 전투장 내부 크기 [가로, 세로] 타일 */
  arenaTiles: [number, number];
  /** 카메라 배율 (게임 카메라와 같은 2배) */
  zoom: number;
  cardMs: number;
  firstCardMs: number;
  clearMs: number;
  shotSpeedTiles: number;
  telegraphMs: number;
  bulletLifeMs: number;
  /** 등급별 최대 피격 (S·A·B — 넘으면 C) */
  grade: Record<'S' | 'A' | 'B', number>;
  bonus: Record<TrialGrade, number>;
  tasks: TrialTaskDef[];
  /** 사수 자리: 전투장 가운데 기준 반 폭·반 높이 비율 [x, y] */
  spots: [number, number][];
  /** 주인공 시작 자리 (같은 비율) */
  start: [number, number];
  /** 탄생 전장 소품 (없으면 빈 목록) */
  props: TrialPropDef[];
}

export interface RitualData {
  hints: Record<'name' | 'rewrite' | 'strokes' | 'trial' | 'trialSkip' | 'fate', string>;
  redraw: { key: string; label: string };
  meta: { key: string; label: string };
  /** 무기 id → 획 모양 한 줄 (예 '곧고 빠르게') */
  legend: Record<string, string>;
  /** 무기 id → 왜 이 무기인지 (strokes = 획이 불렀다 · remembered = 두 번째 생 손이 기억한 무기) */
  why: Record<string, { strokes: string; remembered: string }>;
  /** 회피 시험 결과 한 줄 (등급별 · 건너뜀) */
  gift: Record<TrialGrade | 'skipped', string>;
  /** 일기장 문장 (단계별 위쪽 한두 줄 — 스토리 62 의식 팩) */
  lines: Record<RitualLineKey, string>;
  trial: RitualTrialData;
}

export const RITUAL_LINE_KEYS = [
  'name',
  'strokes',
  'trialIntro',
  'trialEnd',
  'fate',
  'rewrite',
  'rewritePrompt',
] as const;
export type RitualLineKey = (typeof RITUAL_LINE_KEYS)[number];

function fail(msg: string): never {
  throw new Error(`[data] ${msg}`);
}

const str = (v: unknown, at: string): string => {
  if (typeof v !== 'string' || !v) fail(`${at} 비어 있음`);
  return v;
};

/** 화면 문구에 숫자 금지 (§20 '수치 금지') */
const noDigits = (v: unknown, at: string): string => {
  const s = str(v, at);
  if (/[0-9]/.test(s)) fail(`${at} 에 숫자가 있다 (의식 문구는 수치 금지)`);
  return s;
};

const pos = (v: unknown, at: string): number => {
  if (typeof v !== 'number' || !Number.isFinite(v) || v <= 0) fail(`${at} 는 양수`);
  return v;
};

export function validateRitual(d: RitualData, weapons: readonly string[]): RitualData {
  for (const k of ['name', 'rewrite', 'strokes', 'trial', 'trialSkip', 'fate'] as const)
    str(d.hints?.[k], `ritual.hints.${k}`);
  str(d.redraw?.key, 'ritual.redraw.key');
  noDigits(d.redraw?.label, 'ritual.redraw.label');
  str(d.meta?.key, 'ritual.meta.key');
  noDigits(d.meta?.label, 'ritual.meta.label');
  for (const w of weapons) {
    noDigits(d.legend?.[w], `ritual.legend.${w}`);
    noDigits(d.why?.[w]?.strokes, `ritual.why.${w}.strokes`);
    noDigits(d.why?.[w]?.remembered, `ritual.why.${w}.remembered`);
  }
  for (const g of [...TRIAL_GRADES, 'skipped'] as const) noDigits(d.gift?.[g], `ritual.gift.${g}`);
  for (const k of RITUAL_LINE_KEYS) noDigits(d.lines?.[k], `ritual.lines.${k}`);
  const T = d.trial;
  str(T?.tileset, 'ritual.trial.tileset');
  if (!Array.isArray(T.arenaTiles) || T.arenaTiles.length !== 2) fail('ritual.trial.arenaTiles 는 [w, h]');
  T.arenaTiles.forEach((n, i) => pos(n, `ritual.trial.arenaTiles[${i}]`));
  for (const k of [
    'zoom',
    'cardMs',
    'firstCardMs',
    'clearMs',
    'shotSpeedTiles',
    'telegraphMs',
    'bulletLifeMs',
  ] as const)
    pos(T[k], `ritual.trial.${k}`);
  if (!(T.grade.S <= T.grade.A && T.grade.A <= T.grade.B)) fail('ritual.trial.grade 는 S ≤ A ≤ B');
  for (const g of TRIAL_GRADES) if (!(T.bonus[g] >= 0)) fail(`ritual.trial.bonus.${g} 는 0 이상`);
  if (!Array.isArray(T.tasks) || T.tasks.length === 0) fail('ritual.trial.tasks 비어 있음');
  const ids = new Set<string>();
  for (const t of T.tasks) {
    str(t.id, 'ritual.trial.tasks[].id');
    if (ids.has(t.id)) fail(`ritual.trial.tasks 중복 ${t.id}`);
    ids.add(t.id);
    noDigits(t.label, `ritual.trial.tasks.${t.id}.label`);
    if (t.pattern !== 'aimed' && t.pattern !== 'fan') fail(`ritual.trial.tasks.${t.id}.pattern 은 aimed | fan`);
    if (t.pattern === 'fan') {
      pos(t.fanCount, `ritual.trial.tasks.${t.id}.fanCount`);
      pos(t.fanDeg, `ritual.trial.tasks.${t.id}.fanDeg`);
    }
    pos(t.volleys, `ritual.trial.tasks.${t.id}.volleys`);
    pos(t.intervalMs, `ritual.trial.tasks.${t.id}.intervalMs`);
    if (!(t.shooters >= 1 && t.shooters <= T.spots.length)) fail(`ritual.trial.tasks.${t.id}.shooters 는 1..spots 수`);
  }
  if (!Array.isArray(T.props)) fail('ritual.trial.props 는 배열');
  for (const p of T.props) {
    str(p.sheet, 'ritual.trial.props[].sheet');
    if (!Array.isArray(p.at) || p.at.length !== 2) fail(`ritual.trial.props.${p.sheet}.at 는 [x, y]`);
    pos(p.w, `ritual.trial.props.${p.sheet}.w`);
    pos(p.h, `ritual.trial.props.${p.sheet}.h`);
  }
  return d;
}

export const RITUAL_DATA: RitualData = validateRitual(
  (narrativeJson as unknown as { ritual: RitualData }).ritual,
  Object.keys(WEAPONS),
);
