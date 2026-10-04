/**
 * 57라운드 빌드 축 상태 장부 (Phaser 의존 없음, 시간은 호출 쪽이 넣는다):
 * - `MarkBook` 표식(표식 태그 — 같은 적 n타마다 1, 최대치·수명)
 * - `DotBook` 출혈·화상(상흔 태그 — 적마다 지속 피해, 남은 피해 합·폭발·옮겨붙기)
 * - `DrunkTimer` 취기 상태(취기 태그 — 마시기마다 새로 고침, 상한, 취보 1회)
 * - `EvadeTracker` 완벽 회피(57 Q28 — 적 공격 판정 직전 0.15초 안 대쉬·그림자 걸음)
 */

interface MarkEntry {
  marks: number;
  hits: number;
  lastAt: number;
}

export class MarkBook<K> {
  private readonly entries = new Map<K, MarkEntry>();

  /** 타격 1회: hitsPer 타마다 표식 1 (최대 max). 표식이 늘었으면 새 표식 수, 아니면 null */
  hit(target: K, now: number, hitsPer: number, max: number): number | null {
    const e = this.entries.get(target) ?? { marks: 0, hits: 0, lastAt: now };
    e.hits += 1;
    e.lastAt = now;
    let gained: number | null = null;
    if (e.hits >= Math.max(1, hitsPer)) {
      e.hits = 0;
      if (e.marks < max) {
        e.marks += 1;
        gained = e.marks;
      }
    }
    this.entries.set(target, e);
    return gained;
  }

  marks(target: K): number {
    return this.entries.get(target)?.marks ?? 0;
  }

  /** 표식을 직접 정한다 (옮겨감) */
  set(target: K, marks: number, now: number): void {
    if (marks <= 0) this.entries.delete(target);
    else this.entries.set(target, { marks, hits: 0, lastAt: now });
  }

  /** 표식을 전부 꺼낸다 (기폭·옮겨감) */
  take(target: K): number {
    const m = this.marks(target);
    this.entries.delete(target);
    return m;
  }

  expire(now: number, lifeMs: number, alive: (k: K) => boolean = () => true): void {
    for (const [k, e] of this.entries) if (!alive(k) || now - e.lastAt > lifeMs) this.entries.delete(k);
  }

  list(): [K, number][] {
    return [...this.entries].filter(([, e]) => e.marks > 0).map(([k, e]) => [k, e.marks]);
  }

  clear(): void {
    this.entries.clear();
  }
}

export type DotKind = 'bleed' | 'burn';

interface DotEntry {
  until: number;
  nextAt: number;
  tickMs: number;
  dmg: number;
}

/** 적마다 출혈·화상 (같은 종류를 다시 걸면 남은 시간을 새로 — 틱 피해는 큰 쪽) */
export class DotBook<K> {
  private readonly entries = new Map<K, Partial<Record<DotKind, DotEntry>>>();

  apply(target: K, kind: DotKind, now: number, ms: number, tickMs: number, dmg: number): void {
    const cur = this.entries.get(target) ?? {};
    const prev = cur[kind];
    cur[kind] = {
      until: now + ms,
      nextAt: prev && prev.until > now ? prev.nextAt : now + tickMs,
      tickMs,
      dmg: Math.max(dmg, prev && prev.until > now ? prev.dmg : 0),
    };
    this.entries.set(target, cur);
  }

  has(target: K, kind: DotKind, now: number): boolean {
    const e = this.entries.get(target)?.[kind];
    return Boolean(e && e.until > now);
  }

  /** 지속 피해 중인가 (종류 무관) */
  any(target: K, now: number): boolean {
    return this.has(target, 'bleed', now) || this.has(target, 'burn', now);
  }

  /** 남은 틱 피해 합 (지금부터 끝까지) */
  remaining(target: K, now: number): number {
    let sum = 0;
    for (const e of Object.values(this.entries.get(target) ?? {})) {
      if (!e || e.until <= now) continue;
      const ticks = Math.max(0, Math.floor((e.until - e.nextAt) / e.tickMs) + 1);
      sum += ticks * e.dmg;
    }
    return sum;
  }

  /** 남은 피해를 꺼내고 지운다 (끓음 폭발) */
  take(target: K, now: number): number {
    const r = this.remaining(target, now);
    this.entries.delete(target);
    return r;
  }

  /** 걸린 상태 복사 (옮겨붙기용 — 남은 시간·틱 그대로) */
  snapshot(target: K, now: number): { kind: DotKind; ms: number; tickMs: number; dmg: number }[] {
    const out: { kind: DotKind; ms: number; tickMs: number; dmg: number }[] = [];
    for (const [kind, e] of Object.entries(this.entries.get(target) ?? {}) as [DotKind, DotEntry | undefined][])
      if (e && e.until > now) out.push({ kind, ms: e.until - now, tickMs: e.tickMs, dmg: e.dmg });
    return out;
  }

  /** 지금 틱이 도는 것 [대상, 종류, 피해]. 끝난 것은 지운다 */
  tick(now: number): [K, DotKind, number][] {
    const out: [K, DotKind, number][] = [];
    for (const [k, rec] of this.entries) {
      for (const kind of ['bleed', 'burn'] as const) {
        const e = rec[kind];
        if (!e) continue;
        while (e.nextAt <= now && e.nextAt <= e.until) {
          out.push([k, kind, e.dmg]);
          e.nextAt += e.tickMs;
        }
        if (e.until <= now || e.nextAt > e.until) delete rec[kind];
      }
      if (!rec.bleed && !rec.burn) this.entries.delete(k);
    }
    return out;
  }

  forget(target: K): void {
    this.entries.delete(target);
  }

  clear(): void {
    this.entries.clear();
  }

  list(): K[] {
    return [...this.entries.keys()];
  }
}

/** 취기 상태 (취기 세트 2 '한 잔' · 4 '취보' · 6 '술바다', 만취 서약 상시) */
export class DrunkTimer {
  until = -Infinity;
  durationMs = 0;
  /** 이번 취기 상태에서 휘청(취보)을 썼는가 */
  staggerUsed = false;
  /** 휘청 직후 '취권 반격' 창 */
  counterUntil = -Infinity;

  active(now: number): boolean {
    return now < this.until;
  }

  /** 마시기: ms 로 새로 고침 (합산 아님), 상한 maxMs. 새 취기 상태면 휘청 1회 다시 */
  drink(now: number, ms: number, maxMs = ms): void {
    if (!this.active(now)) this.staggerUsed = false;
    const target = now + Math.min(ms, maxMs);
    this.until = Math.max(this.until, target);
    this.durationMs = Math.min(ms, maxMs);
  }

  /** 술바다: 취기 중 처치·마시기로 늘어날 때 상한 */
  extend(now: number, ms: number, maxMs: number): void {
    if (!this.active(now)) return;
    this.until = Math.min(now + maxMs, this.until + ms);
  }

  remainMs(now: number): number {
    return Math.max(0, this.until - now);
  }

  /** 취보: 이번 취기에서 처음 받는 공격이면 휘청을 쓰고 true */
  tryStagger(now: number, counterMs: number): boolean {
    if (!this.active(now) || this.staggerUsed) return false;
    this.staggerUsed = true;
    this.counterUntil = now + counterMs;
    return true;
  }

  /** 취권 반격 (휘청 뒤 첫 공격 1회) */
  takeCounter(now: number): boolean {
    if (now >= this.counterUntil) return false;
    this.counterUntil = -Infinity;
    return true;
  }

  reset(): void {
    this.until = -Infinity;
    this.durationMs = 0;
    this.staggerUsed = false;
    this.counterUntil = -Infinity;
  }
}

/**
 * 완벽 회피 (57 Q28): 대쉬·그림자 걸음을 시작한 자리·시각을 무장해 두고, windowMs 안에 그 자리(반경 안)를 노린 적 공격 판정이
 * 오면 완벽 회피 1회 (한 번 쓰면 끝)
 */
export class EvadeTracker {
  private at = -Infinity;
  private x = 0;
  private y = 0;
  private used = true;

  arm(now: number, x: number, y: number): void {
    this.at = now;
    this.x = x;
    this.y = y;
    this.used = false;
  }

  /** 지금 창 안인가 */
  armed(now: number, windowMs: number): boolean {
    return !this.used && now - this.at >= 0 && now - this.at <= windowMs;
  }

  /** (x, y) 반경 r 판정이 무장한 자리를 덮으면 완벽 회피 (1회) */
  check(now: number, windowMs: number, x: number, y: number, r: number): boolean {
    if (!this.armed(now, windowMs)) return false;
    if (Math.hypot(x - this.x, y - this.y) > r) return false;
    this.used = true;
    return true;
  }

  /** 무적으로 흘려 낸 피격 (자리 무관) */
  consume(now: number, windowMs: number): boolean {
    if (!this.armed(now, windowMs)) return false;
    this.used = true;
    return true;
  }

  get origin(): { x: number; y: number } {
    return { x: this.x, y: this.y };
  }
}
