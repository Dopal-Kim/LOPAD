/**
 * P21 잔혹 전투 규칙 (계약 dark-brutal §3~§6) — Phaser 의존 없음 (단위 테스트).
 * 상처 단계 · 사망 변형 선택 · 처형 조건 · 적중 결 · 데칼/시체 상한 목록.
 */
import { BRUTAL } from '../../core/constants/brutal';
import type { DeathVariant, GoreCut, GoreWeapon } from '../../core/eventsP21';
import type { UiGoreLevel } from '../../contract/ui';

/** 주인공 상처 단계 (HP 비율 > 75% → 0, ≤ 75% → 1, ≤ 50% → 2, ≤ 25% → 3) */
export function heroWoundStage(hp: number, maxHp: number): 0 | 1 | 2 | 3 {
  const r = maxHp > 0 ? hp / maxHp : 1;
  const [a, b, c] = BRUTAL.HERO.STAGES;
  return r <= c ? 3 : r <= b ? 2 : r <= a ? 1 : 0;
}

/** 적 상처 단계 (≤ 66% → 1, ≤ 33% → 2) */
export function enemyWoundStage(hp: number, maxHp: number): 0 | 1 | 2 {
  const r = maxHp > 0 ? hp / maxHp : 1;
  const [a, b] = BRUTAL.ENEMY.STAGES;
  return r <= b ? 2 : r <= a ? 1 : 0;
}

/** 이번 단계까지 붙어 있어야 할 스탬프 수 (rand 0~1) */
export function stampTarget(stage: 0 | 1 | 2, rand: number): number {
  const [lo, hi] = BRUTAL.ENEMY.STAMPS[stage];
  return lo + Math.floor(rand * (hi - lo + 1));
}

export function isGoreWeapon(w: string | null | undefined): w is GoreWeapon {
  return w === 'katana' || w === 'greatsword' || w === 'dagger' || w === 'bow';
}

/** 적중 결: 칼 = 베기 · 대검 = 부숨(막타·내려치기) 또는 베기 · 단검 = 찌르기 · 활 = 꿰뚫기 · 그 밖(환경) = 부숨 */
export function cutOf(weapon: GoreWeapon | null, heavy: boolean): GoreCut {
  switch (weapon) {
    case 'katana':
      return 'slash';
    case 'greatsword':
      return heavy ? 'crush' : 'slash';
    case 'dagger':
      return 'stab';
    case 'bow':
      return 'pierce';
    default:
      return 'crush';
  }
}

/** 분출 양 1~3: 처치·막타·치명 = 크게 */
export function goreAmount(o: { died: boolean; heavy: boolean; crit: boolean; overkillRatio: number }): 1 | 2 | 3 {
  if (o.died && (o.overkillRatio >= BRUTAL.DEATH.OVERKILL_RATIO || o.heavy)) return 3;
  if (o.died || o.heavy || o.crit) return 2;
  return 1;
}

export interface DeathContext {
  /** 막타 무기 (환경 피해면 null) */
  weapon: GoreWeapon | null;
  /** 넘친 피해 / 최대 HP */
  overkillRatio: number;
  /** 활 막타일 때 맞은 방향 1.5칸 안에 벽 */
  wallNear: boolean;
  /** 불 위험물 · 물 낙하 */
  fire: boolean;
  drown: boolean;
  /** 처형이면 그 변형 (무기별 — executeVariant) */
  execute?: DeathVariant | null;
  boss: boolean;
}

/** §5 사망 변형 (gore 적용 전). 군주는 collapse 만 */
export function pickDeathVariant(c: DeathContext): DeathVariant {
  if (c.boss) return 'collapse';
  if (c.execute) return c.execute;
  if (c.drown) return 'drown';
  if (c.fire) return 'burn';
  const big = c.overkillRatio >= BRUTAL.DEATH.OVERKILL_RATIO;
  if (c.weapon === 'greatsword' && big) return 'bisect';
  if (c.weapon === 'katana' && big) return 'behead';
  if (c.weapon === 'bow' && c.wallNear) return 'pinned';
  return 'collapse';
}

/** §1·§5 고어 반영: 1 = 절단(behead·bisect) → collapse · 0 = 모두 collapse */
export function goreVariant(v: DeathVariant, gore: UiGoreLevel): DeathVariant {
  if (gore === 0) return 'collapse';
  if (gore === 1 && (v === 'behead' || v === 'bisect')) return 'collapse';
  return v;
}

/** 잘린 조각을 남기는 변형 (gore 2 만) */
export function severs(v: DeathVariant): boolean {
  return v === 'behead' || v === 'bisect';
}

/** §4 무기별 처형 변형: 칼 목 베기 · 대검 두 동강 · 단검 collapse(+큰 분출) · 활 pinned */
export function executeVariant(weapon: GoreWeapon): DeathVariant {
  return weapon === 'katana' ? 'behead' : weapon === 'greatsword' ? 'bisect' : weapon === 'bow' ? 'pinned' : 'collapse';
}

export interface ExecCandidate {
  boss: boolean;
  elite: boolean;
  hp: number;
  maxHp: number;
  /** 버팀이 깨진 상태 (stagger — flinch 아님) */
  broken: boolean;
  /** 주인공 → 대상 (월드 px) · 대상 몸 반지름 */
  dx: number;
  dy: number;
  radius: number;
}

/**
 * §4 처형 조건: 군주 제외 · 엘리트는 HP ≤ 15% 일 때만 · 일반은 버팀 깨짐 또는 HP ≤ 15% · 주인공 앞(aim) 부채꼴 1.2칸 안.
 * 반환 = 거리(px — 가까운 대상 고르기), 조건 밖이면 null
 */
export function execDistance(c: ExecCandidate, aimAngle: number, tilePx: number): number | null {
  const E = BRUTAL.EXEC;
  if (c.boss || c.hp <= 0) return null;
  const low = c.hp <= c.maxHp * E.HP_RATIO;
  if (!(low || (!c.elite && c.broken))) return null;
  const d = Math.hypot(c.dx, c.dy);
  if (d - c.radius > E.RANGE_TILES * tilePx) return null;
  if (d > c.radius) {
    let diff = Math.atan2(c.dy, c.dx) - aimAngle;
    diff = Math.atan2(Math.sin(diff), Math.cos(diff));
    if (Math.abs(diff) > E.HALF_ANGLE) return null;
  }
  return d;
}

/**
 * 상한 있는 목록 (FIFO): 넣고, 넘친 오래된 것들을 돌려준다 (호출 쪽이 서서히 지운다). 지운 것은 목록에서 바로 빠진다
 */
export class CappedList<T> {
  private readonly items: T[] = [];
  constructor(readonly max: number) {}

  push(item: T): T[] {
    this.items.push(item);
    const over = this.items.length - this.max;
    return over > 0 ? this.items.splice(0, over) : [];
  }

  remove(item: T): void {
    const i = this.items.indexOf(item);
    if (i >= 0) this.items.splice(i, 1);
  }

  clear(): T[] {
    return this.items.splice(0, this.items.length);
  }

  get size(): number {
    return this.items.length;
  }
}

/** §1 고어 피 양 (데칼 수에 곱한다): 2 → 1 · 1 → 1/3 · 0 → 0 (반올림 — 1/3 은 확률로) */
export function goreCount(base: number, gore: UiGoreLevel, rand: number): number {
  if (gore === 0) return 0;
  if (gore === 2) return base;
  const v = base * BRUTAL.GORE1.AMOUNT;
  return Math.floor(v) + (rand < v - Math.floor(v) ? 1 : 0);
}
