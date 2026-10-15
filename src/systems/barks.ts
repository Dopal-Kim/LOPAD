/**
 * P19 2단계 적의 지나가는 대사 (스토리 65 팩 barks — enemies.json `barks`): 같은 적은 PER_MOB_MS, 전체는 GLOBAL_MS 간격.
 * 순수 — 시각은 부르는 쪽 (GameCombat.bark 가 UI `ui:enemy-bark` 로 내보낸다)
 */
export const BARK = { PER_MOB_MS: 4000, GLOBAL_MS: 1500 } as const;

export class BarkGate {
  private readonly last = new WeakMap<object, number>();
  private lastAny = -Infinity;

  /** 말할 문장 (간격 안이거나 후보가 없으면 null). rand 0..1 */
  pick(who: object, lines: readonly string[] | undefined, now: number, rand: number): string | null {
    if (!lines || lines.length === 0) return null;
    if (now - this.lastAny < BARK.GLOBAL_MS || now - (this.last.get(who) ?? -Infinity) < BARK.PER_MOB_MS) return null;
    this.lastAny = now;
    this.last.set(who, now);
    return lines[Math.min(lines.length - 1, Math.floor(rand * lines.length))];
  }
}
