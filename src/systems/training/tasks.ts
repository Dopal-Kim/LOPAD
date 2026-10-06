/**
 * 61 단계 6 (P14 §1) 수련장 과제 판정 — 순수 규칙 (Phaser 의존 없음, 단위 테스트).
 * 과제 = 시스템 EventBus 사건 조건(data/training.json). 씬(TrainingMode)이 사건을 넘기면 새로 끝난 과제 id 를 돌려준다.
 * - any: 사건 하나라도 (where = 페이로드 일부: 값 · 목록(하나라도) · {gte, lte})
 * - count: 그만큼 모이면 · after: 앞선 사건 뒤 withinMs 안에 온 것만 · dodgeMs: 사건 뒤 그 시간 동안 맞지 않으면(PLAYER_DAMAGED 없음)
 * - branch n / trait n: 씬이 무기의 갈래 id·대표 개성 id 를 넘겨 사건 조건으로 푼다
 */
import type { TrainingEventSpec, TrainingTaskDef, TrainingWhereValue } from '../../data/training';

/** 피격 사건 (회피 창을 깬다) */
export const DAMAGE_EVENT = 'player:damaged';

export function matchValue(v: unknown, spec: TrainingWhereValue): boolean {
  if (Array.isArray(spec)) return spec.some((s) => s === v);
  if (spec !== null && typeof spec === 'object') {
    if (typeof v !== 'number') return false;
    if (spec.gte !== undefined && v < spec.gte) return false;
    if (spec.lte !== undefined && v > spec.lte) return false;
    return true;
  }
  return v === spec;
}

export function matchEvent(spec: TrainingEventSpec, event: string, payload: unknown): boolean {
  if (spec.on !== event) return false;
  if (!spec.where) return true;
  const p = (payload ?? {}) as Record<string, unknown>;
  return Object.entries(spec.where).every(([k, s]) => matchValue(p[k], s));
}

/** branch·trait 과제를 사건 조건으로 푼다 (갈래 id = WEAPON_AWAKEN.branch, 개성 id = TRAIT_PROC.trait) */
export function resolveTask(
  t: TrainingTaskDef,
  ctx: { branches: readonly string[]; traits: readonly string[] },
): TrainingTaskDef {
  if (t.branch !== undefined) {
    const b = ctx.branches[t.branch - 1];
    return { ...t, any: b ? [{ on: 'weapon:awaken', where: { stage: 1, branch: b } }] : [] };
  }
  if (t.trait !== undefined) {
    const id = ctx.traits[t.trait - 1];
    return { ...t, any: id ? [{ on: 'weapon:trait-proc', where: { trait: id } }] : [] };
  }
  return t;
}

export class TaskTracker {
  private readonly tasks: TrainingTaskDef[];
  private readonly counts = new Map<string, number>();
  private readonly doneSet: Set<string>;
  /** after 조건: 과제 id → 앞선 사건 시각 */
  private readonly afterAt = new Map<string, number>();
  /** 열린 회피 창 */
  private dodges: { id: string; until: number }[] = [];

  constructor(
    tasks: readonly TrainingTaskDef[],
    ctx: { branches: readonly string[]; traits: readonly string[] },
    private readonly defaultDodgeMs: number,
    done: Iterable<string> = [],
  ) {
    this.tasks = tasks.map((t) => resolveTask(t, ctx));
    const ids = new Set(this.tasks.map((t) => t.id));
    this.doneSet = new Set([...done].filter((id) => ids.has(id)));
  }

  /** 들어야 할 사건 이름 (피격 포함) */
  events(): string[] {
    const s = new Set<string>([DAMAGE_EVENT]);
    for (const t of this.tasks) {
      for (const e of t.any) s.add(e.on);
      for (const e of t.after?.any ?? []) s.add(e.on);
    }
    return [...s];
  }

  get done(): ReadonlySet<string> {
    return this.doneSet;
  }

  get allDone(): boolean {
    return this.tasks.every((t) => this.doneSet.has(t.id));
  }

  isDone(id: string): boolean {
    return this.doneSet.has(id);
  }

  /** 진행 수 (count 과제 표시용) */
  countOf(id: string): number {
    return this.doneSet.has(id) ? (this.tasks.find((t) => t.id === id)?.count ?? 1) : (this.counts.get(id) ?? 0);
  }

  /** 사건 하나 → 새로 끝난 과제 id */
  onEvent(event: string, payload: unknown, now: number): string[] {
    if (event === DAMAGE_EVENT) this.dodges = [];
    const out: string[] = [];
    for (const t of this.tasks) {
      if (this.doneSet.has(t.id)) continue;
      if (t.after?.any.some((e) => matchEvent(e, event, payload))) this.afterAt.set(t.id, now);
      if (!t.any.some((e) => matchEvent(e, event, payload))) continue;
      if (t.after) {
        const at = this.afterAt.get(t.id);
        if (at === undefined || now - at > t.after.withinMs) continue;
      }
      if (t.dodgeMs !== undefined) {
        const ms = t.dodgeMs > 0 ? t.dodgeMs : this.defaultDodgeMs;
        if (!this.dodges.some((d) => d.id === t.id)) this.dodges.push({ id: t.id, until: now + ms });
        continue;
      }
      if (this.bump(t)) out.push(t.id);
    }
    return out;
  }

  /** 매 프레임: 회피 창이 맞지 않고 지나갔으면 완료 */
  tick(now: number): string[] {
    const out: string[] = [];
    this.dodges = this.dodges.filter((d) => {
      if (now < d.until) return true;
      const t = this.tasks.find((x) => x.id === d.id);
      if (t && !this.doneSet.has(t.id) && this.bump(t)) out.push(t.id);
      return false;
    });
    return out;
  }

  /** 과제 하나 직접 완료 (디버그·씬 규칙) */
  complete(id: string): boolean {
    const t = this.tasks.find((x) => x.id === id);
    if (!t || this.doneSet.has(id)) return false;
    this.doneSet.add(id);
    return true;
  }

  private bump(t: TrainingTaskDef): boolean {
    const n = (this.counts.get(t.id) ?? 0) + 1;
    this.counts.set(t.id, n);
    if (n < t.count) return false;
    this.doneSet.add(t.id);
    return true;
  }
}
