/**
 * 62라운드 P0-6 위 가운데 알림 큐 하나 — 차례 계산 (순수, Phaser 없음).
 *
 * 화면 위 가운데에 '주의'·방 이름·'문이 닫혔다'·'처음 보는 적'·파훼·국면 카드가 한꺼번에 겹치던 문제(점검 P0-6)를
 * 한 줄 세우기로 푼다. 규칙:
 *  - 동시에 보이는 것은 `max`(2) 장까지. 위에서부터 중요도 높은 순(같으면 먼저 뜬 것 위).
 *  - 자리가 없을 때 더 중요한 알림이 오면 보이는 것 중 가장 낮은 것을 접는다(빨리 사라짐, 다시 띄우지 않음).
 *    그렇지 않으면 줄을 선다(중요도 높은 순 → 먼저 온 순).
 *  - 줄에서 `ttlMs` 넘게 기다린 낮은 알림은 버린다(낮은 것 생략). 막혀 있는 동안(전환·탄생 연출)은 기다린 시간을 세지 않는다.
 *  - 같은 `key` 가 보이거나 줄에 있으면 새로 세우지 않고 합친다(HudAlerts 가 그림을 다시 만든다).
 *  - `supersedes`: 이 알림이 오면 그 종류의 보이는 알림은 접고, 줄에 선 것은 버린다(보스 국면이 바뀌면 지난 파훼 카드 등).
 */

export type AlertKind = 'boss' | 'break' | 'enemy' | 'warn' | 'growth' | 'room' | 'info';

/** 중요도: 보스 국면 > 파훼 > 적 소개·주의 > 개성 > 방 이름 > 상태 (점검 P0-6 순서) */
export const ALERT_PRIORITY: Record<AlertKind, number> = {
  boss: 60,
  break: 50,
  enemy: 40,
  warn: 40,
  growth: 30,
  room: 20,
  info: 10,
};

/** 줄에서 기다릴 수 있는 최대 시간 (ms). 넘으면 버린다 */
export const ALERT_TTL_MS: Record<AlertKind, number> = {
  boss: Number.POSITIVE_INFINITY,
  break: 1500,
  enemy: 6000,
  warn: 2500,
  growth: 6000,
  room: 2500,
  info: 3000,
};

export interface AlertEntry {
  id: number;
  kind: AlertKind;
  priority: number;
  key: string | null;
  /** 줄에 선 시각 (막혀 있는 동안은 앞으로 민다) */
  at: number;
  ttlMs: number;
  /** 보인 순서 (같은 중요도에서 위아래) */
  shownSeq: number;
}

export type AlertAction = { type: 'show'; id: number } | { type: 'fold'; id: number } | { type: 'drop'; id: number };

export interface AlertPushOpts {
  key?: string | null;
  supersedes?: readonly AlertKind[];
  /** 기본 ttl 대신 */
  ttlMs?: number;
}

export class AlertPlan {
  private shown: AlertEntry[] = [];
  private waiting: AlertEntry[] = [];
  private nextId = 1;
  private seq = 0;

  constructor(readonly max = 2) {}

  /** 보이는 것 (위에서 아래 순서) */
  get visible(): readonly AlertEntry[] {
    return [...this.shown].sort((a, b) => b.priority - a.priority || a.shownSeq - b.shownSeq);
  }

  get queued(): readonly AlertEntry[] {
    return this.waiting;
  }

  get idle(): boolean {
    return this.shown.length === 0 && this.waiting.length === 0;
  }

  /** 같은 key 의 알림 (보이는 것 먼저) */
  findKey(key: string): AlertEntry | null {
    return this.shown.find((e) => e.key === key) ?? this.waiting.find((e) => e.key === key) ?? null;
  }

  isShown(id: number): boolean {
    return this.shown.some((e) => e.id === id);
  }

  /** 그 종류가 보이거나 줄에 있는가 */
  has(kind: AlertKind): boolean {
    return this.shown.some((e) => e.kind === kind) || this.waiting.some((e) => e.kind === kind);
  }

  /**
   * 새 알림. 돌려주는 id 와 할 일 목록. `blocked` 면(전환·탄생 연출 중) 줄에만 세운다.
   * 같은 key 합치기는 부르는 쪽이 `findKey` 로 먼저 본다.
   */
  push(
    kind: AlertKind,
    now: number,
    blocked: boolean,
    opts: AlertPushOpts = {},
  ): { id: number; actions: AlertAction[] } {
    const actions: AlertAction[] = [];
    for (const k of opts.supersedes ?? []) {
      for (const e of this.shown.filter((s) => s.kind === k)) {
        this.shown = this.shown.filter((s) => s !== e);
        actions.push({ type: 'fold', id: e.id });
      }
      for (const e of this.waiting.filter((s) => s.kind === k)) actions.push({ type: 'drop', id: e.id });
      this.waiting = this.waiting.filter((s) => s.kind !== k);
    }
    const e: AlertEntry = {
      id: this.nextId++,
      kind,
      priority: ALERT_PRIORITY[kind],
      key: opts.key ?? null,
      at: now,
      ttlMs: opts.ttlMs ?? ALERT_TTL_MS[kind],
      shownSeq: 0,
    };
    if (blocked) {
      this.enqueue(e);
      return { id: e.id, actions };
    }
    if (this.shown.length < this.max) {
      this.show(e, actions);
      return { id: e.id, actions };
    }
    const low = this.lowest();
    if (low && e.priority > low.priority) {
      this.shown = this.shown.filter((s) => s !== low);
      actions.push({ type: 'fold', id: low.id });
      this.show(e, actions);
      return { id: e.id, actions };
    }
    this.enqueue(e);
    return { id: e.id, actions };
  }

  /** 보이던 알림이 다 사라졌다 (또는 접힘이 끝났다) — 다음 차례 */
  gone(id: number, now: number, blocked: boolean): AlertAction[] {
    this.shown = this.shown.filter((e) => e.id !== id);
    return this.tick(now, blocked);
  }

  /** 매 프레임: 오래 기다린 것은 버리고, 자리가 나면 띄운다. 막혀 있으면 기다린 시각을 민다 */
  tick(now: number, blocked: boolean): AlertAction[] {
    const actions: AlertAction[] = [];
    if (blocked) {
      for (const e of this.waiting) e.at = now;
      return actions;
    }
    const keep: AlertEntry[] = [];
    for (const e of this.waiting) {
      if (now - e.at > e.ttlMs) actions.push({ type: 'drop', id: e.id });
      else keep.push(e);
    }
    this.waiting = keep;
    while (this.shown.length < this.max && this.waiting.length) {
      const e = this.waiting.shift()!;
      this.show(e, actions);
    }
    return actions;
  }

  /** 하나를 지금 접는다 (보이면 fold, 줄이면 drop) */
  remove(id: number): AlertAction[] {
    if (this.shown.some((e) => e.id === id)) {
      this.shown = this.shown.filter((e) => e.id !== id);
      return [{ type: 'fold', id }];
    }
    if (this.waiting.some((e) => e.id === id)) {
      this.waiting = this.waiting.filter((e) => e.id !== id);
      return [{ type: 'drop', id }];
    }
    return [];
  }

  /** 모두 치운다 (방을 떠남·런 끝·큰 연출) — 보이는 것은 fold, 줄은 drop. `keep` 종류는 남긴다 */
  clear(keep: readonly AlertKind[] = []): AlertAction[] {
    const actions: AlertAction[] = [];
    for (const e of this.shown) if (!keep.includes(e.kind)) actions.push({ type: 'fold', id: e.id });
    for (const e of this.waiting) if (!keep.includes(e.kind)) actions.push({ type: 'drop', id: e.id });
    this.shown = this.shown.filter((e) => keep.includes(e.kind));
    this.waiting = this.waiting.filter((e) => keep.includes(e.kind));
    return actions;
  }

  private show(e: AlertEntry, actions: AlertAction[]): void {
    e.shownSeq = ++this.seq;
    this.shown.push(e);
    actions.push({ type: 'show', id: e.id });
  }

  private enqueue(e: AlertEntry): void {
    // 중요도 높은 순, 같으면 먼저 온 순
    const i = this.waiting.findIndex((w) => w.priority < e.priority);
    if (i < 0) this.waiting.push(e);
    else this.waiting.splice(i, 0, e);
  }

  /** 보이는 것 중 가장 낮은 것 (같으면 먼저 뜬 것) */
  private lowest(): AlertEntry | null {
    let low: AlertEntry | null = null;
    for (const e of this.shown) if (!low || e.priority < low.priority) low = e;
    return low;
  }
}

/** 알림 낱말 비교용: 공백·문장부호를 뺀다 ('문이 닫혔다.' = '문이 닫혔다') */
export function alertNorm(text: string): string {
  return text.replace(/[\s.,!?·…'"“”‘’()[\]]/g, '');
}

/** 시스템 공지 중 '주의' 카드와 한 장으로 합칠 것인가 (방 시작 '문이 닫혔다' 계열) */
export function isRoomLockNotice(text: string, lockTexts: readonly string[]): boolean {
  const n = alertNorm(text);
  return n.length > 0 && lockTexts.some((t) => alertNorm(t) === n);
}

/** 사라지는 중인 카드의 자리 (위 끝 y · 높이 · 다 사라지는 시각) */
export interface LeavingSlot {
  y: number;
  h: number;
  endsAt: number;
}

/**
 * 62 루프 3 UI H (점검 P0-N3): 같은 레인 교차 페이드 금지 — 새 카드(또는 자리 옮김)가 들어갈 [y, y+h] 와 겹치는
 * 사라지는 중인 카드가 있으면, 그 카드가 다 사라진 뒤에 들어온다. 기다릴 ms (0 = 바로).
 */
export function laneDelay(y: number, h: number, leaving: readonly LeavingSlot[], now: number): number {
  let until = now;
  for (const l of leaving) {
    if (l.endsAt <= now) continue;
    if (y < l.y + l.h && l.y < y + h) until = Math.max(until, l.endsAt);
  }
  return Math.max(0, Math.ceil(until - now));
}
