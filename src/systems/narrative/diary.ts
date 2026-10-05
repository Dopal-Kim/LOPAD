/**
 * 61라운드 P7·P8 일기장 이력 (메타 세이브 `lopad.meta` diary — 영구). Phaser 의존 없음.
 * 다시 태어난 수(lives — 운명이 정해진 생) · 사망 수 · 층 보스 처치 수 · 읽은 단서 · 지난 이름 · 지난 생 기록(최근 N).
 * 쓰임: 단서 `repeatLast`(두 번째 생부터) · E4 '지난 생의 기록' · 시작 의식 단축(첫 생만 전체) · 이름 덧쓰기.
 * 옛 메타(diary 없음)는 런 수·클리어 수로 채운다 (이미 여러 번 해 본 사람이 다시 첫 생 의식을 겪지 않게).
 */
import { metaStore, type MetaData, type MetaStore } from '../meta';

export interface PastLife {
  name: string;
  weapon: string;
  floor: number;
  kills: number;
  cleared: boolean;
  /** 그 생에 쓰러뜨린 층 보스 (stage id) */
  bosses: string[];
}

export interface DiaryRecord {
  /** 다시 태어난 수 (시작 의식에서 운명이 정해진 생 — 지금 생 포함) */
  lives: number;
  deaths: number;
  /** 층 보스 처치 수 (stage id → 수) */
  bossKills: Record<string, number>;
  /** 읽은 단서 id */
  clues: string[];
  /** 지난 생에 적은 이름 (덧쓰기 기본값) */
  lastName: string;
  /** 지난 생 기록 (오래된 것부터, 최근 N) */
  pastLives: PastLife[];
}

export function emptyDiary(): DiaryRecord {
  return { lives: 0, deaths: 0, bossKills: {}, clues: [], lastName: '', pastLives: [] };
}

const nonNeg = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) && v > 0 ? Math.floor(v) : 0);

/** 메타에서 일기장 (없거나 깨졌으면 런 수로 채운 새 기록) */
export function readDiary(meta: Pick<MetaData, 'runs' | 'clears'> & { diary?: Partial<DiaryRecord> }): DiaryRecord {
  const d = meta.diary;
  if (!d || typeof d !== 'object') {
    const runs = nonNeg(meta.runs);
    return { ...emptyDiary(), lives: runs, deaths: Math.max(0, runs - nonNeg(meta.clears)) };
  }
  const bossKills: Record<string, number> = {};
  for (const [k, v] of Object.entries(d.bossKills ?? {})) if (nonNeg(v) > 0) bossKills[k] = nonNeg(v);
  return {
    lives: nonNeg(d.lives),
    deaths: nonNeg(d.deaths),
    bossKills,
    clues: Array.isArray(d.clues) ? d.clues.filter((c): c is string => typeof c === 'string') : [],
    lastName: typeof d.lastName === 'string' ? d.lastName : '',
    pastLives: Array.isArray(d.pastLives) ? d.pastLives.filter((p) => p && typeof p === 'object') : [],
  };
}

/** 시작 의식 전: 이번이 첫 생인가 (전체 의식 — 이름 → 3획 → 회피 시험 → 튜토리얼) */
export function isFirstLife(d: DiaryRecord): boolean {
  return d.lives === 0;
}

/** 런 안: 지금 생이 첫 생인가 (운명이 정해진 뒤 — lives 에 지금 생이 들어 있다). 튜토리얼 표식 */
export function inFirstLife(d: DiaryRecord): boolean {
  return d.lives <= 1;
}

/** 운명이 정해짐 (시작 의식 끝) — 생 +1, 이름 */
export function recordBirth(d: DiaryRecord, name: string): DiaryRecord {
  return { ...d, lives: d.lives + 1, lastName: name };
}

/** 생이 끝남 (사망·클리어) — 지난 생 기록 (최근 max) · 사망 수 */
export function recordLifeEnd(d: DiaryRecord, life: PastLife, max: number): DiaryRecord {
  const pastLives = [...d.pastLives, life].slice(-Math.max(1, max));
  return { ...d, deaths: d.deaths + (life.cleared ? 0 : 1), pastLives };
}

export function recordBossKill(d: DiaryRecord, stageId: string): DiaryRecord {
  return { ...d, bossKills: { ...d.bossKills, [stageId]: (d.bossKills[stageId] ?? 0) + 1 } };
}

export function recordClue(d: DiaryRecord, clue: string): DiaryRecord {
  return d.clues.includes(clue) ? d : { ...d, clues: [...d.clues, clue] };
}

/** 지난 생에 이 층 보스를 쓰러뜨렸나 (이번 생 처치는 뺀다) */
export function bossKilledBefore(d: DiaryRecord, stageId: string, killedThisLife: boolean): boolean {
  return (d.bossKills[stageId] ?? 0) - (killedThisLife ? 1 : 0) > 0;
}

/** 지난 생의 기록이 있나 (지금 생 말고) */
export function hasPastLife(d: DiaryRecord): boolean {
  return d.pastLives.length > 0 || d.deaths > 0;
}

/** 단서 줄: 지난 생에 본 기록이 있으면 마지막 줄을 repeatLast 로 */
export function clueLines(c: { lines: readonly string[]; repeatLast: string }, repeat: boolean): string[] {
  if (!repeat || c.lines.length === 0) return [...c.lines];
  return [...c.lines.slice(0, -1), c.repeatLast];
}

/** E4 '지난 생의 기록을 읽는다': 만취를 쓰러뜨린 생이 있음 → 지난 생 기록 있음(무작위 한 줄) → 첫 생 */
export function diaryReadLine(
  t: { bossKilledBefore: string; tips: readonly string[]; empty: string },
  s: { bossKilledBefore: boolean; hasPastLife: boolean },
  roll: number,
): string {
  if (s.bossKilledBefore) return t.bossKilledBefore;
  if (s.hasPastLife && t.tips.length > 0) return t.tips[Math.min(t.tips.length - 1, Math.floor(roll * t.tips.length))];
  return t.empty;
}

const KO_COUNT = ['', '한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟', '아홉'];

/** 한글 수 관형사 (1~9 — '두 겹'), 그 밖은 숫자 */
export function koreanCount(n: number): string {
  const i = Math.floor(n);
  return i >= 1 && i < KO_COUNT.length ? KO_COUNT[i] : String(i);
}

/** 메타 세이브의 일기장 (지금 값) */
export function diaryNow(store: MetaStore = metaStore): DiaryRecord {
  return readDiary(store.read());
}

/** 메타 세이브의 일기장 고쳐 쓰기 (읽고 → fn → 씀) */
export function updateDiary(fn: (d: DiaryRecord) => DiaryRecord, store: MetaStore = metaStore): DiaryRecord {
  const meta = store.read();
  const next = fn(readDiary(meta));
  store.write({ ...meta, diary: next });
  return next;
}
