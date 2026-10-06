/**
 * 61 단계 6 (P14 §1 수련장, 계약 UI §19) 데이터 로더·검증 — `data/training.json`.
 * 방 8 (순서 = 지도 순서) · 방마다 준비(적·허수아비·줍기·웅덩이·보스)와 과제 조건 · 문장(스토리 팩 text 복사, 키 training.<room>.<slot>).
 * Phaser 의존 없음.
 */
import trainingJson from '../../data/training.json';
import { ENEMIES, WEAPONS } from './index';
import { TRAITS } from './growth';
import type { WeaponVerbSlot } from './types';

/** where 값: 같음 · 목록(하나라도) · 범위 */
export type TrainingWhereValue =
  string | number | boolean | (string | number | boolean)[] | { gte?: number; lte?: number };
/** 사건 하나: 시스템 EventBus 이벤트 이름 + 페이로드 일부 */
export interface TrainingEventSpec {
  on: string;
  where?: Record<string, TrainingWhereValue>;
}
/** 과제 하나 (정규화 뒤 — any 는 늘 채워짐, branch·trait 과제는 any 를 코드가 채운다) */
export interface TrainingTaskDef {
  id: string;
  verb?: WeaponVerbSlot;
  count: number;
  any: TrainingEventSpec[];
  /** 그 사건이 이 사건 뒤 withinMs 안에 왔을 때만 */
  after?: { any: TrainingEventSpec[]; withinMs: number };
  /** 사건 뒤 dodgeMs 동안 맞지 않으면 완료 (0 = 훈련 예고 길이 — tuning.drillMs) */
  dodgeMs?: number;
  /** 1차 갈래 n(1~3) 깨우기 */
  branch?: number;
  /** 대표 개성 n(1~2) 발동 */
  trait?: number;
}
export interface TrainingSpawnDef {
  id: string;
  count: number;
  elite?: boolean;
}
export interface TrainingPickupDef {
  kind: 'gold' | 'potion' | 'consumable';
  value?: number;
  id?: string;
  /** 방 가운데 기준 칸 */
  at: [number, number];
}
export interface TrainingSetupDef {
  /** '표시까지 걷기' 표식 (방 가운데 기준 칸) */
  marker?: [number, number];
  dummies?: { role: 'target' | 'turret'; at: [number, number] }[];
  pickups?: TrainingPickupDef[];
  /** 들어설 때 물약 수 (없으면 그대로) */
  potions?: number;
  enemies?: TrainingSpawnDef[];
  /** 훈련 예고 (원·선·부채) 차례 */
  drills?: ('circle' | 'line' | 'cone')[];
  /** 술 웅덩이 자리 (칸) */
  pools?: [number, number][];
  /** 각성 게이지 과제 (허수아비·적을 칠 때마다 게이지) */
  gauge?: boolean;
  /** 만취 그림자 (보스 노드 전장 + 약한 보스) */
  boss?: boolean;
}
export interface TrainingRoomDef {
  id: string;
  /** 쥐여 줄 무기 (null = 지금 무기 — 런에서 왔으면 런 무기) */
  weapon: string | null;
  setup: TrainingSetupDef;
  tasks: TrainingTaskDef[];
}
export interface TrainingTuning {
  gaugePerHit: number;
  respawnMs: number;
  drillEveryMs: number;
  drillMs: number;
  drillHit: number;
  drillRadiusTiles: number;
  drillLineTiles: number;
  drillLineHalfTiles: number;
  drillConeTiles: number;
  drillConeDeg: number;
  bossHpMult: number;
  reachTiles: number;
  enemyRingTiles: number;
}
export interface TrainingData {
  tuning: TrainingTuning;
  traitPicks: Record<string, [string, string]>;
  rooms: TrainingRoomDef[];
  text: Record<string, string>;
}

const VERBS: readonly WeaponVerbSlot[] = ['attack', 'signature', 'dash', 'hold'];

function fail(msg: string): never {
  throw new Error(`[data] training: ${msg}`);
}

type RawTask = Partial<TrainingTaskDef> & { on?: string; where?: TrainingEventSpec['where'] };

/** 과제 한 줄 정규화: 위 단축(on·where) → any */
export function normalizeTask(raw: RawTask, at: string): TrainingTaskDef {
  if (typeof raw.id !== 'string' || raw.id === '') fail(`${at}.id`);
  const any: TrainingEventSpec[] = Array.isArray(raw.any)
    ? raw.any.map((e) => ({ on: e.on, ...(e.where ? { where: e.where } : {}) }))
    : raw.on
      ? [{ on: raw.on, ...(raw.where ? { where: raw.where } : {}) }]
      : [];
  if (any.length === 0 && raw.branch === undefined && raw.trait === undefined)
    fail(`${at}: 조건(on·any·branch·trait) 없음`);
  for (const e of any) if (typeof e.on !== 'string' || !e.on.includes(':')) fail(`${at}: 이벤트 이름 '${e.on}'`);
  if (raw.verb !== undefined && !VERBS.includes(raw.verb)) fail(`${at}.verb`);
  if (raw.branch !== undefined && !(raw.branch >= 1 && raw.branch <= 3)) fail(`${at}.branch 1~3`);
  if (raw.trait !== undefined && !(raw.trait >= 1 && raw.trait <= 2)) fail(`${at}.trait 1~2`);
  const count = raw.count ?? 1;
  if (!(count >= 1)) fail(`${at}.count`);
  return {
    id: raw.id,
    ...(raw.verb ? { verb: raw.verb } : {}),
    count,
    any,
    ...(raw.after ? { after: { any: raw.after.any, withinMs: raw.after.withinMs } } : {}),
    ...(raw.dodgeMs !== undefined ? { dodgeMs: raw.dodgeMs } : {}),
    ...(raw.branch !== undefined ? { branch: raw.branch } : {}),
    ...(raw.trait !== undefined ? { trait: raw.trait } : {}),
  };
}

export function validateTraining(raw: unknown): TrainingData {
  const d = raw as {
    tuning: TrainingTuning;
    traitPicks: Record<string, [string, string]>;
    rooms: (Omit<TrainingRoomDef, 'tasks'> & { tasks: RawTask[] })[];
    text: Record<string, string>;
  };
  if (!d || !Array.isArray(d.rooms) || d.rooms.length === 0) fail('rooms 비어 있음');
  const text = d.text ?? {};
  const ids = new Set<string>();
  const rooms = d.rooms.map((r, i) => {
    const at = `rooms[${i}]`;
    if (typeof r.id !== 'string' || ids.has(r.id)) fail(`${at}.id 중복·없음`);
    ids.add(r.id);
    if (r.weapon !== null && !WEAPONS[r.weapon]) fail(`${at}.weapon '${r.weapon}'`);
    for (const e of r.setup?.enemies ?? []) if (!ENEMIES[e.id]) fail(`${at}.setup.enemies '${e.id}'`);
    if (!text[`training.${r.id}.name`]) fail(`${at}: 문장 training.${r.id}.name 없음`);
    const taskIds = new Set<string>();
    const tasks = r.tasks.map((t, j) => {
      const task = normalizeTask(t, `${at}.tasks[${j}]`);
      if (taskIds.has(task.id)) fail(`${at}.tasks '${task.id}' 중복`);
      taskIds.add(task.id);
      if (!text[`training.${r.id}.task.${task.id}`]) fail(`${at}: 문장 training.${r.id}.task.${task.id} 없음`);
      if ((task.branch || task.trait) && !r.weapon) fail(`${at}.${task.id}: 갈래·개성 과제는 무기 방만`);
      return task;
    });
    if (tasks.length === 0) fail(`${at}.tasks 비어 있음`);
    return { id: r.id, weapon: r.weapon, setup: r.setup ?? {}, tasks };
  });
  for (const [wid, picks] of Object.entries(d.traitPicks ?? {})) {
    if (!WEAPONS[wid]) fail(`traitPicks.${wid}`);
    for (const id of picks)
      if (!TRAITS.some((t) => t.id === id && t.weapon === wid && !t.branch))
        fail(`traitPicks.${wid} '${id}' (갈래 없는 이 무기 개성)`);
  }
  for (const k of ['hall.name', 'hall.enter', 'common.stamp', 'choice.training', 'choice.run'])
    if (!text[`training.${k}`]) fail(`문장 training.${k} 없음`);
  return { tuning: d.tuning, traitPicks: d.traitPicks ?? {}, rooms, text };
}

export const TRAINING: TrainingData = validateTraining(trainingJson);

/** 방 정의 (없으면 null) */
export function trainingRoom(id: string): TrainingRoomDef | null {
  return TRAINING.rooms.find((r) => r.id === id) ?? null;
}

/** 문장 (키 training.<key>, {이름} 치환 — 없으면 '') */
export function trainingText(key: string, vars: Record<string, string> = {}): string {
  const s = TRAINING.text[`training.${key}`] ?? '';
  return s.replace(/\{(\w+)\}/g, (_m, k: string) => vars[k] ?? '');
}
