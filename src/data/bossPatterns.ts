/**
 * 54라운드 Q4: 보스 패턴 이름·수치 형식의 단일 출처 (Phaser 의존 없음 — 데이터 검증·패턴 모듈·이벤트가 함께 쓴다).
 *
 * 수치는 `data/bosses.json` 의 `patterns.<이름>` 객체 하나로 통일한다:
 * - 보스 공통 `patterns.<이름>` = 기본값
 * - 페이즈 `phases[i].patterns.<이름>` = 그 페이즈에서 바꾸는 값만 (얕은 객체는 한 단계 더 합친다)
 * - `patterns.<이름>.empowered` = 1층 '한 잔 더'를 다 마신 뒤 다음 패턴 강화값 (있을 때만)
 * 페이즈의 `pick` 은 그 페이즈에서 고르는 패턴 목록, `intervalMs` 는 패턴 사이 간격.
 */

/** 패턴 이름 (선택 가능한 것 + 페이즈 전환 연출 phaseDrink). 이벤트 페이로드·레지스트리·검증이 이 목록 하나를 본다 */
export const BOSS_PATTERN_NAMES = [
  'dash',
  'fan',
  'slam',
  'summon',
  'volley',
  // 54라운드 1층 '만취'
  'drink',
  'spin',
  'drunkDash',
  'caskRoll',
  'fireSpill',
  'lightsOut',
  'phaseDrink',
] as const;

export type BossPatternName = (typeof BOSS_PATTERN_NAMES)[number];

export function isBossPatternName(v: unknown): v is BossPatternName {
  return typeof v === 'string' && (BOSS_PATTERN_NAMES as readonly string[]).includes(v);
}

/** 패턴 수치 한 벌 (모듈이 자기 형식으로 읽는다) */
export type PatternParams = Record<string, unknown>;

/** 검증 형식: 필수 숫자 · 선택 숫자 · 문자열 · 불리언 · 숫자 배열 · 패턴 이름 배열 */
interface PatternSchema {
  num: readonly string[];
  optNum?: readonly string[];
  str?: readonly string[];
  optStr?: readonly string[];
  optBool?: readonly string[];
  optNumArr?: readonly string[];
  optNames?: readonly string[];
  optName?: readonly string[];
}

export const BOSS_PATTERN_SCHEMAS: Record<BossPatternName, PatternSchema> = {
  dash: {
    num: ['telegraphMs', 'speedTiles', 'durationMs', 'attack', 'wallStunMs'],
    optNum: ['repeat', 'repeatTelegraphRatio', 'cooldownMs'],
  },
  fan: {
    num: ['cooldownMs', 'count', 'spreadDeg', 'projectileSpeedTiles', 'attack', 'projectileSize', 'projectileLifeMs'],
    optNum: ['telegraphMs', 'telegraphTiles'],
    optBool: ['afterDash'],
    optStr: ['sprite'],
  },
  slam: { num: ['telegraphMs', 'radiusTiles', 'attack', 'cooldownMs'] },
  summon: { num: ['count', 'max', 'cooldownMs'], str: ['enemy'] },
  volley: {
    num: [
      'telegraphMs',
      'telegraphTiles',
      'count',
      'shotGapMs',
      'projectileSpeedTiles',
      'attack',
      'projectileSize',
      'projectileLifeMs',
      'cooldownMs',
    ],
    optStr: ['sprite'],
  },
  drink: {
    num: ['liftMs', 'gulpMs', 'finishMs', 'breakStunMs', 'cooldownMs', 'cupW', 'cupH', 'cupLiftPx'],
    optBool: ['empowerNext'],
    optNames: ['triggers'],
  },
  spin: { num: ['durationMs', 'tiltDeg', 'periodMs', 'rampMs', 'cooldownMs'], optNum: ['blur'], optName: ['next'] },
  drunkDash: {
    num: ['speedTiles', 'durationMs', 'attack', 'wallStunMs', 'repeat', 'bendRatio', 'fallMs', 'cooldownMs'],
    optNumArr: ['telegraphSeqMs'],
    optNum: ['telegraphMs', 'leanDeg'],
  },
  caskRoll: {
    num: [
      'telegraphMs',
      'speedTiles',
      'bounces',
      'maxTiles',
      'attack',
      'radiusPx',
      'puddleEveryTiles',
      'puddleMs',
      'bossHitDamage',
      'bossHitStunMs',
      'cooldownMs',
      'count',
      'spreadDeg',
    ],
    optNum: ['radiusFromArt'],
  },
  fireSpill: {
    num: [
      'telegraphMs',
      'lengthTiles',
      'wobbleTiles',
      'puddleMs',
      'torchTelegraphMs',
      'torchFlightMs',
      'spreadMsPerCell',
      'fireMs',
      'fireTickMs',
      'firePlayerAttack',
      'cooldownMs',
    ],
    optNum: ['arms', 'armSpreadDeg'],
  },
  lightsOut: {
    num: ['telegraphMs', 'radiusTiles', 'attack', 'fadeMs', 'durationMs', 'cooldownMs', 'toppleGapMs'],
    str: ['darkAmbient'],
    optName: ['next'],
  },
  phaseDrink: { num: ['durationMs'], optBool: ['invulnerable'] },
};

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

/** 패턴 수치 합치기: 얕은 객체는 한 단계 더 합치고, 나머지(숫자·문자열·배열)는 덮어쓴다 */
export function mergeParams(base: PatternParams | undefined, over: PatternParams | undefined): PatternParams {
  const out: PatternParams = { ...(base ?? {}) };
  for (const [k, v] of Object.entries(over ?? {})) {
    const b = out[k];
    out[k] = isPlainObject(b) && isPlainObject(v) ? { ...b, ...v } : v;
  }
  return out;
}

/** 수치 해석에 필요한 최소 형식 (BossDef 와 같은 모양) */
export interface PatternSource {
  patterns?: Partial<Record<BossPatternName, PatternParams>>;
  phases: { patterns?: Partial<Record<BossPatternName, PatternParams>> }[];
}

/**
 * 페이즈 i 의 패턴 수치: 공통 → 페이즈 덮어쓰기 → (강화 중이면) empowered 덮어쓰기. `empowered` 키 자체는 결과에서 뺀다.
 * 수치가 전혀 없으면 null
 */
export function resolvePatternParams(
  def: PatternSource,
  phaseIndex: number,
  name: BossPatternName,
  empowered = false,
): PatternParams | null {
  const base = def.patterns?.[name];
  const over = def.phases[phaseIndex]?.patterns?.[name];
  if (!base && !over) return null;
  let p = mergeParams(base, over);
  if (empowered && isPlainObject(p.empowered)) p = mergeParams(p, p.empowered);
  delete p.empowered;
  return p;
}

/** HP 비율 → 페이즈 번호 (hpFraction 이하인 마지막 페이즈) */
export function phaseIndexFor(frac: number, phases: readonly { hpFraction: number }[]): number {
  let idx = 0;
  phases.forEach((p, i) => {
    if (frac <= p.hpFraction) idx = i;
  });
  return idx;
}

/** 수치 한 벌 검증. 문제가 있으면 오류 메시지 목록 */
export function checkPatternParams(name: BossPatternName, p: PatternParams, path: string): string[] {
  const s = BOSS_PATTERN_SCHEMAS[name];
  const errs: string[] = [];
  const isNum = (v: unknown) => typeof v === 'number' && !Number.isNaN(v);
  for (const k of s.num) if (!isNum(p[k])) errs.push(`${path}.${k} 는 숫자여야 합니다 (받은 값: ${String(p[k])})`);
  for (const k of s.optNum ?? []) if (p[k] !== undefined && !isNum(p[k])) errs.push(`${path}.${k} 는 숫자`);
  for (const k of s.str ?? []) if (typeof p[k] !== 'string') errs.push(`${path}.${k} 는 문자열`);
  for (const k of s.optStr ?? [])
    if (p[k] !== undefined && typeof p[k] !== 'string') errs.push(`${path}.${k} 는 문자열`);
  for (const k of s.optBool ?? [])
    if (p[k] !== undefined && typeof p[k] !== 'boolean') errs.push(`${path}.${k} 는 참/거짓`);
  for (const k of s.optNumArr ?? [])
    if (p[k] !== undefined && (!Array.isArray(p[k]) || !(p[k] as unknown[]).every(isNum)))
      errs.push(`${path}.${k} 는 숫자 배열`);
  for (const k of s.optNames ?? [])
    if (p[k] !== undefined && (!Array.isArray(p[k]) || !(p[k] as unknown[]).every(isBossPatternName)))
      errs.push(`${path}.${k} 는 패턴 이름 배열`);
  for (const k of s.optName ?? [])
    if (p[k] !== undefined && !isBossPatternName(p[k])) errs.push(`${path}.${k} 는 패턴 이름`);
  return errs;
}
