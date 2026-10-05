/**
 * 61라운드 P9 런 로그 (밸런스 조정용, 순수 — Phaser 의존 없음). 기록기(`runLogRecorder`)가 EventBus 사건을 넘기고,
 * 런이 끝나면 `end()` 요약을 메타 세이브 `runLogs` 에 최근 N개(`RUNLOG.KEEP_RUNS`) 남긴다.
 * - 시간은 호출자가 주는 ms(게임 시계). 일시정지 구간(`pause`~`resume`)은 노드·런 시간에서 뺀다 — 메뉴(3지선다 등)는 플레이 시간에 포함.
 * - 노드 = 노드 지도 노드 하나. 첫 노드 진입 전 사건은 '런 시작' 가짜 노드(`id: '-'`)에 쌓는다.
 * - 사망 원인은 추정: 마지막 피격 직전 `RUNLOG.CAUSE_WINDOW_MS` 안의 마지막 적·보스 공격 사건(접촉·돌진·사격·보스 패턴). 없으면 'unknown'.
 */
import { RUNLOG } from '../../core/Constants';

export const RUNLOG_VERSION = 1;

export type RunLogChoiceKind = 'branch' | 'awaken' | 'reinforce' | 'passive' | 'dualTrait' | 'curse' | 'stat';

export interface RunLogChoice {
  kind: RunLogChoiceKind;
  /** 갈래·각성 = 이름, 강화 = 이름, 패시브·이중 개성·저주·능력치 = id */
  id: string;
  /** 패시브 레벨 · 진화 단계 · 강화 횟수 · 저주 출처 */
  detail?: string | number;
  /** 런 시작부터 (플레이 시간 ms) */
  atMs: number;
}

export interface RunLogNode {
  id: string;
  /** 노드 종류 (birth·road·post·battle·shop·rest·event·boss …) */
  kind: string;
  name: string;
  /** 층 (1부터) */
  floor: number;
  /** 런 시작부터 진입까지 (플레이 시간 ms) */
  enterMs: number;
  /** 노드에 머문 플레이 시간 (일시정지 제외) */
  durationMs: number;
  /** 진입 → 출구 열림(클리어)까지. 클리어 전에 끝났으면 null */
  clearMs: number | null;
  kills: number;
  eliteKills: number;
  /** 적 id 별 처치 수 */
  killsBy: Record<string, number>;
  hitsTaken: number;
  damageTaken: number;
  /** 메뉴(TextMenu) 연 횟수 — 같은 메뉴 다시 열기(reopen)는 세지 않는다 */
  menus: number;
  menuIds: string[];
  choices: RunLogChoice[];
}

export interface RunLogDeath {
  /** 추정 원인 ('enemy:<id>:<contact|dash|shot>' · 'boss:<id>:<패턴>' · 'unknown') */
  cause: string;
  nodeId: string;
  nodeKind: string;
  /** 마지막 피격 피해 · 그 직전 HP */
  lastHit: number;
  hpBefore: number;
  atMs: number;
}

export interface RunLogSummary {
  version: typeof RUNLOG_VERSION;
  seed: string;
  weapon: string;
  /** 세이브 이어하기로 시작했으면 true (그 전 기록 없음) */
  continued: boolean;
  /** 실제 시각 (epoch ms, 런 시작) */
  startedAt: number;
  /** 플레이 시간 합 (일시정지 제외) */
  durationMs: number;
  result: 'death' | 'clear' | 'abandon';
  /** 도달 층 (1부터) */
  floorReached: number;
  nodes: RunLogNode[];
  totals: { kills: number; hitsTaken: number; damageTaken: number; menus: number; nodes: number };
  choices: RunLogChoice[];
  death: RunLogDeath | null;
}

export interface RunLogStart {
  seed: string;
  weapon: string;
  stageIndex: number;
  continued: boolean;
  startedAt: number;
}

function newNode(id: string, kind: string, name: string, floor: number, enterMs: number): RunLogNode {
  return {
    id,
    kind,
    name,
    floor,
    enterMs,
    durationMs: 0,
    clearMs: null,
    kills: 0,
    eliteKills: 0,
    killsBy: {},
    hitsTaken: 0,
    damageTaken: 0,
    menus: 0,
    menuIds: [],
    choices: [],
  };
}

export class RunLog {
  private readonly nodes: RunLogNode[] = [];
  private node: RunLogNode;
  /** 일시정지 누계·시작 시각 (null = 진행 중) */
  private pausedTotal = 0;
  private pausedAt: number | null = null;
  private readonly startNow: number;
  private nodeEnterNow: number;
  private nodePausedBase = 0;
  private lastThreat: { cause: string; at: number } | null = null;
  private lastHit: { amount: number; hpBefore: number } = { amount: 0, hpBefore: 0 };
  private death: RunLogDeath | null = null;
  private floorReached: number;
  private ended: RunLogSummary | null = null;

  constructor(
    private readonly start: RunLogStart,
    now: number,
  ) {
    this.startNow = now;
    this.nodeEnterNow = now;
    this.floorReached = start.stageIndex + 1;
    this.node = newNode('-', 'start', '', this.floorReached, 0);
    this.nodes.push(this.node);
  }

  get isEnded(): boolean {
    return this.ended !== null;
  }

  /** 런 시작부터 플레이 시간 (일시정지 제외) */
  playMs(now: number): number {
    const paused = this.pausedTotal + (this.pausedAt !== null ? now - this.pausedAt : 0);
    return Math.max(0, Math.round(now - this.startNow - paused));
  }

  pause(now: number): void {
    if (this.pausedAt === null) this.pausedAt = now;
  }

  resume(now: number): void {
    if (this.pausedAt === null) return;
    this.pausedTotal += now - this.pausedAt;
    this.pausedAt = null;
  }

  enterNode(p: { id: string; kind: string; name: string; stageIndex: number }, now: number): void {
    if (this.ended) return;
    this.closeNode(now);
    const floor = p.stageIndex + 1;
    this.floorReached = Math.max(this.floorReached, floor);
    // 첫 진입 전 가짜 노드가 비어 있으면 버린다
    const pre = this.nodes[this.nodes.length - 1];
    if (pre && pre.id === '-' && this.nodes.length === 1 && isEmpty(pre)) this.nodes.pop();
    this.node = newNode(p.id, p.kind, p.name, floor, this.playMs(now));
    this.nodes.push(this.node);
    this.nodeEnterNow = now;
    this.nodePausedBase = this.pausedNow(now);
  }

  /** 층 이동 (노드 지도 밖 전환 포함) — 도달 층만 갱신 */
  stage(stageIndex: number): void {
    this.floorReached = Math.max(this.floorReached, stageIndex + 1);
  }

  /** 출구 열림 = 노드 클리어 (처음 한 번) */
  cleared(now: number): void {
    if (this.ended || this.node.clearMs !== null) return;
    this.node.clearMs = this.nodeMs(now);
  }

  kill(enemyId: string, elite: boolean): void {
    if (this.ended) return;
    this.node.kills += 1;
    if (elite) this.node.eliteKills += 1;
    this.node.killsBy[enemyId] = (this.node.killsBy[enemyId] ?? 0) + 1;
  }

  /** 적·보스 공격 사건 (사망 원인 추정용) */
  threat(cause: string, now: number): void {
    this.lastThreat = { cause, at: now };
  }

  /** 피격: 받은 피해는 그 직전 HP 를 넘지 않게 센다 (한 방에 죽을 때 넘친 피해 제외) */
  hit(amount: number, hpAfter: number, maxHp: number = Infinity): void {
    if (this.ended || amount <= 0) return;
    const hpBefore = Math.min(maxHp, hpAfter + amount);
    const taken = Math.max(0, hpBefore - hpAfter);
    this.node.hitsTaken += 1;
    this.node.damageTaken += taken;
    this.lastHit = { amount: taken, hpBefore };
  }

  menu(id: string, reopen: boolean): void {
    if (this.ended || reopen) return;
    this.node.menus += 1;
    if (!this.node.menuIds.includes(id)) this.node.menuIds.push(id);
  }

  choice(kind: RunLogChoiceKind, id: string, detail: string | number | undefined, now: number): void {
    if (this.ended || this.node.choices.length >= RUNLOG.MAX_CHOICES_PER_NODE) return;
    this.node.choices.push({ kind, id, ...(detail !== undefined ? { detail } : {}), atMs: this.playMs(now) });
  }

  died(now: number): void {
    if (this.ended || this.death) return;
    const t = this.lastThreat;
    this.death = {
      cause: t && now - t.at <= RUNLOG.CAUSE_WINDOW_MS ? t.cause : 'unknown',
      nodeId: this.node.id,
      nodeKind: this.node.kind,
      lastHit: this.lastHit.amount,
      hpBefore: this.lastHit.hpBefore,
      atMs: this.playMs(now),
    };
  }

  /** 런 끝 → 요약 (한 번만, 이후 같은 값) */
  end(result: RunLogSummary['result'], now: number): RunLogSummary {
    if (this.ended) return this.ended;
    if (this.pausedAt !== null) this.resume(now);
    this.closeNode(now);
    this.ended = this.summarize(this.nodes.map(cloneNode), result, now);
    return this.ended;
  }

  /** 진행 중 모습 (디버그 dump — 지금 노드 시간 포함, 상태는 바꾸지 않음). 결과는 사망 기록이 있으면 death, 아니면 abandon */
  peek(now: number): RunLogSummary {
    if (this.ended) return this.ended;
    const nodes = this.nodes.map(cloneNode);
    nodes[nodes.length - 1].durationMs = this.nodeMs(now);
    return this.summarize(nodes, this.death ? 'death' : 'abandon', now);
  }

  private summarize(all: RunLogNode[], result: RunLogSummary['result'], now: number): RunLogSummary {
    const nodes = all.filter((n) => !(n.id === '-' && isEmpty(n)));
    const sum = (k: 'kills' | 'hitsTaken' | 'damageTaken' | 'menus') => nodes.reduce((a, n) => a + n[k], 0);
    return {
      version: RUNLOG_VERSION,
      seed: this.start.seed,
      weapon: this.start.weapon,
      continued: this.start.continued,
      startedAt: this.start.startedAt,
      durationMs: this.playMs(now),
      result,
      floorReached: this.floorReached,
      nodes,
      totals: {
        kills: sum('kills'),
        hitsTaken: sum('hitsTaken'),
        damageTaken: sum('damageTaken'),
        menus: sum('menus'),
        nodes: nodes.filter((n) => n.id !== '-').length,
      },
      choices: nodes.flatMap((n) => n.choices.map((c) => ({ ...c }))),
      death: result === 'death' ? (this.death ?? { ...unknownDeath(this.node), atMs: this.playMs(now) }) : null,
    };
  }

  private pausedNow(now: number): number {
    return this.pausedTotal + (this.pausedAt !== null ? now - this.pausedAt : 0);
  }

  private nodeMs(now: number): number {
    return Math.max(0, Math.round(now - this.nodeEnterNow - (this.pausedNow(now) - this.nodePausedBase)));
  }

  private closeNode(now: number): void {
    this.node.durationMs = this.nodeMs(now);
  }
}

function isEmpty(n: RunLogNode): boolean {
  return n.kills === 0 && n.hitsTaken === 0 && n.menus === 0 && n.choices.length === 0;
}

function cloneNode(n: RunLogNode): RunLogNode {
  return { ...n, killsBy: { ...n.killsBy }, menuIds: [...n.menuIds], choices: n.choices.map((c) => ({ ...c })) };
}

function unknownDeath(n: RunLogNode): Omit<RunLogDeath, 'atMs'> {
  return { cause: 'unknown', nodeId: n.id, nodeKind: n.kind, lastHit: 0, hpBefore: 0 };
}

/** 메타에 남길 목록: 새 요약을 뒤에 붙이고 최근 keep 개만 */
export function appendRunLog(
  list: readonly RunLogSummary[] | undefined,
  s: RunLogSummary,
  keep: number = RUNLOG.KEEP_RUNS,
): RunLogSummary[] {
  const out = [...(list ?? []), s];
  return out.slice(Math.max(0, out.length - keep));
}

/** 밸런스 표 한 줄씩: 노드 종류별 평균 시간·처치·피격·받은 피해·메뉴 (여러 런 합산) */
export function aggregateByKind(
  runs: readonly RunLogSummary[],
): Record<
  string,
  { n: number; avgSec: number; avgKills: number; avgHits: number; avgDamage: number; avgMenus: number }
> {
  const acc: Record<string, { n: number; ms: number; kills: number; hits: number; dmg: number; menus: number }> = {};
  for (const r of runs)
    for (const node of r.nodes) {
      const a = (acc[node.kind] ??= { n: 0, ms: 0, kills: 0, hits: 0, dmg: 0, menus: 0 });
      a.n += 1;
      a.ms += node.durationMs;
      a.kills += node.kills;
      a.hits += node.hitsTaken;
      a.dmg += node.damageTaken;
      a.menus += node.menus;
    }
  const r1 = (v: number) => Math.round(v * 10) / 10;
  return Object.fromEntries(
    Object.entries(acc).map(([k, a]) => [
      k,
      {
        n: a.n,
        avgSec: r1(a.ms / a.n / 1000),
        avgKills: r1(a.kills / a.n),
        avgHits: r1(a.hits / a.n),
        avgDamage: r1(a.dmg / a.n),
        avgMenus: r1(a.menus / a.n),
      },
    ]),
  );
}
