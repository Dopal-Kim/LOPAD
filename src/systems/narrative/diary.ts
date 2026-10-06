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
  /** 61 G (계약 UI §18 firstTime): 본 처음 안내 카드 — 'trait'·'awaken1'·'awaken2' */
  guides: string[];
  /** 61 단계 6 (P14 §1, 계약 UI §19): 수련장 기록 — 런과 무관, 일기장에만 */
  training: TrainingRecord;
}

/** 61 단계 6 수련장 기록 (메타 `diary.training`) */
export interface TrainingRecord {
  /** 도장 찍힌 방 id */
  stamped: string[];
  /** 도장 전 방의 마친 과제 (방 id → 과제 id) — 도장이 찍히면 비운다 */
  progress: Record<string, string[]>;
  /** 첫 생 '수련장부터 / 바로 벽 밖으로' 를 이미 물었다 */
  offered: boolean;
  /** 방에 들어간 수 */
  visits: number;
}

export function emptyTrainingRecord(): TrainingRecord {
  return { stamped: [], progress: {}, offered: false, visits: 0 };
}

const strings = (v: unknown): string[] => (Array.isArray(v) ? v.filter((c): c is string => typeof c === 'string') : []);

export function readTrainingRecord(v: unknown): TrainingRecord {
  if (!v || typeof v !== 'object') return emptyTrainingRecord();
  const t = v as Partial<TrainingRecord>;
  const progress: Record<string, string[]> = {};
  for (const [k, ids] of Object.entries(t.progress ?? {})) {
    const list = strings(ids);
    if (list.length > 0) progress[k] = list;
  }
  return { stamped: strings(t.stamped), progress, offered: t.offered === true, visits: nonNegNum(t.visits) };
}

function nonNegNum(v: unknown): number {
  return typeof v === 'number' && Number.isFinite(v) && v > 0 ? Math.floor(v) : 0;
}

export function emptyDiary(): DiaryRecord {
  return {
    lives: 0,
    deaths: 0,
    bossKills: {},
    clues: [],
    lastName: '',
    pastLives: [],
    guides: [],
    training: emptyTrainingRecord(),
  };
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
    guides: Array.isArray(d.guides) ? d.guides.filter((c): c is string => typeof c === 'string') : [],
    training: readTrainingRecord(d.training),
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

/** 61 G: 처음 안내 카드를 봤다 (계약 §18 firstTime) */
export function recordGuide(d: DiaryRecord, guide: string): DiaryRecord {
  return d.guides.includes(guide) ? d : { ...d, guides: [...d.guides, guide] };
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
