/**
 * P19 적 무리 조율 (방향 문서 ④C · 계약 free-combat §2) — 순수 로직, 씬마다 하나 (MobContext.squad).
 * - 공격 토큰: 예고·공격을 시작하려는 일반 적은 토큰을 받아야 한다 (최대 ENEMY_SQUAD.TOKENS, 정예 따로, 종류별 상한).
 *   공격이 끝나거나 끊기면(움찔·경직·사망) 반납한다.
 * - 북 오라 (깃발 고수): 반경 안 적의 공격 속도 배율.
 */
import { ENEMY_SQUAD } from '../core/Constants';

interface Holder {
  kind: string;
  elite: boolean;
}

interface DrumAura {
  x: number;
  y: number;
  r2: number;
  until: number;
  mult: number;
}

export class MobSquad {
  private readonly holders = new Map<object, Holder>();
  private drums: DrumAura[] = [];

  constructor(
    private readonly max = ENEMY_SQUAD.TOKENS,
    private readonly eliteMax = ENEMY_SQUAD.ELITE_TOKENS,
    private readonly kindMax: Readonly<Record<string, number>> = ENEMY_SQUAD.KIND_MAX,
  ) {}

  /** 토큰 받기 (이미 가졌으면 true). 사라진 개체(active false)의 토큰은 먼저 거둔다 */
  take(who: object, kind: string, elite: boolean): boolean {
    if (this.holders.has(who)) return true;
    let pool = 0;
    let same = 0;
    for (const [w, h] of this.holders) {
      if ((w as { active?: boolean }).active === false) {
        this.holders.delete(w);
        continue;
      }
      if (h.elite === elite) pool++;
      if (!elite && !h.elite && h.kind === kind) same++;
    }
    if (pool >= (elite ? this.eliteMax : this.max)) return false;
    if (!elite && same >= (this.kindMax[kind] ?? Infinity)) return false;
    this.holders.set(who, { kind, elite });
    return true;
  }

  /** P19 2단계: 지금 이 종류가 토큰을 받을 수 있는가 (받지는 않는다 — 다가가기 시작 판단) */
  available(kind: string, elite: boolean): boolean {
    let pool = 0;
    let same = 0;
    for (const [w, h] of this.holders) {
      if ((w as { active?: boolean }).active === false) continue;
      if (h.elite === elite) pool++;
      if (!elite && !h.elite && h.kind === kind) same++;
    }
    return pool < (elite ? this.eliteMax : this.max) && (elite || same < (this.kindMax[kind] ?? Infinity));
  }

  release(who: object): void {
    this.holders.delete(who);
  }

  holds(who: object): boolean {
    return this.holders.has(who);
  }

  /** 토큰을 가진 일반 적 수 (디버그) */
  get count(): number {
    let n = 0;
    for (const h of this.holders.values()) if (!h.elite) n++;
    return n;
  }

  /** 북 한 번: (x, y) 반경 radiusPx 안 적의 공격 속도 × mult, until 까지 */
  drum(x: number, y: number, radiusPx: number, until: number, mult: number): void {
    this.drums.push({ x, y, r2: radiusPx * radiusPx, until, mult });
  }

  /** 이 자리의 북 배율 (오라가 없으면 1, 겹쳐도 가장 큰 것 하나) */
  drumMult(x: number, y: number, now: number): number {
    if (this.drums.length === 0) return 1;
    this.drums = this.drums.filter((d) => d.until > now);
    let m = 1;
    for (const d of this.drums) if ((d.x - x) ** 2 + (d.y - y) ** 2 <= d.r2) m = Math.max(m, d.mult);
    return m;
  }

  clear(): void {
    this.holders.clear();
    this.drums = [];
  }
}

/** 북채가 북면에 닿는 시각 ms (시트 `beatFrames` — 프레임 시작 = 앞 프레임 길이 합). 시트가 없으면 [] */
export function beatTimesMs(def: { beatFrames?: unknown; frameDurationsMs?: unknown } | undefined): number[] {
  const frames = Array.isArray(def?.beatFrames) ? (def.beatFrames as number[]) : [];
  const durs = Array.isArray(def?.frameDurationsMs) ? (def.frameDurationsMs as number[]) : [];
  return frames.map((f) => durs.slice(0, f).reduce((a, b) => a + b, 0));
}
