import type { UiCurse, UiWeaponGauge, UiWeaponResource } from '../contract/ui';

/**
 * 61라운드 P10 전투 HUD 다이어트 — 순수 계산 (Phaser 없음).
 * 전투 중 크게 보이는 것은 체력 · 무기 고유 자원 1개 · 소모품(독주·소모품 칸) · 전표뿐.
 */

/**
 * 무기 자원 고르기 (61 P1 '무기당 화면에 보이는 자원은 1개'). 고유 자원(`gauge`, 계약 §13)이 있으면 그것이 주인공 자원,
 * 없으면 무기 자원(`resource`, §11.1). 시스템 개편 중 둘 다 오면 `resource` 는 작은 보조 줄로 (기력 그로기·화살 장전처럼
 * 싸움에 바로 걸리는 상태라 감추지 않는다).
 */
export function pickResources(
  gauge: UiWeaponGauge | null | undefined,
  resource: UiWeaponResource | null | undefined,
): { main: 'gauge' | 'resource' | null; sub: boolean } {
  const g = Boolean(gauge && gauge.kind);
  const r = Boolean(resource && resource.kind);
  if (g) return { main: 'gauge', sub: r };
  if (r) return { main: 'resource', sub: false };
  return { main: null, sub: false };
}

/** 체력이 낮은가 (수치 강조) */
export function hpLow(hp: number, maxHp: number, ratio: number): boolean {
  return maxHp > 0 && hp > 0 && hp / maxHp <= ratio;
}

export interface CombatRows {
  /** 묶음 위 끝에서 행마다 y */
  hp: number;
  weapon: number;
  /** 보조 자원 줄 (없으면 null) */
  sub: number | null;
  /** 각성 게이지 줄 (스냅샷 growth 가 없으면 null) */
  growth: number | null;
  slots: number;
  /** 묶음 높이 */
  h: number;
}

/**
 * 묶음 행 배치: 체력 → 무기·자원(눈금 2배면 bigRowH) → (보조 자원) → (각성 게이지 — 61 단계 4 P12) → 독주·소모품·전표.
 * 무기 줄은 자원이 없어도 남긴다(무기 아이콘). 옛 2px 개성 진행선은 각성 게이지 줄로 바뀌었다.
 */
export function combatRows(
  spec: { padY: number; rowH: number; bigRowH: number; rowGap: number; growthRowH: number },
  opts: { big: boolean; sub: boolean; growth: boolean },
): CombatRows {
  let y = spec.padY;
  const hp = y;
  y += spec.rowH + spec.rowGap;
  const weapon = y;
  y += (opts.big ? spec.bigRowH : spec.rowH) + spec.rowGap;
  let sub: number | null = null;
  if (opts.sub) {
    sub = y;
    y += spec.rowH + spec.rowGap;
  }
  let growth: number | null = null;
  if (opts.growth) {
    growth = y;
    y += spec.growthRowH + spec.rowGap;
  }
  const slots = y;
  y += spec.rowH;
  return { hp, weapon, sub, growth, slots, h: y + spec.padY };
}

/** 저주 남은 기간 짧은 꼴의 숫자·단위 (노드 우선). 둘 다 없으면 null */
export function curseShort(c: UiCurse | null | undefined): { n: number; unit: 'node' | 'kill' } | null {
  if (!c) return null;
  if (typeof c.nodesLeft === 'number') return { n: Math.max(0, c.nodesLeft), unit: 'node' };
  if (typeof c.killsLeft === 'number') return { n: Math.max(0, c.killsLeft), unit: 'kill' };
  return null;
}

/**
 * 보스 막대 왼쪽 x: 화면 가운데에 두되, 왼쪽 묶음(오른쪽 끝 `bundleRight`)과 `gap` 이상 띄운다 (아이콘 22px 포함).
 */
export function bossLeft(screenW: number, bossW: number, bundleRight: number, gap: number, iconW = 22): number {
  const centered = Math.round(screenW / 2 - bossW / 2);
  return Math.max(centered, bundleRight + gap + iconW);
}

/**
 * 61 단계 4 체력 피격 잔상 상태 (순수 계산). `last` = 지난 체력 비율, 잔상은 `from` 에서 `hitAt + holdMs` 부터
 * `fallMs` 동안 `last` 까지 줄어든다. `last < 0` 이면 아직 본 적 없음.
 */
export interface HpTrail {
  from: number;
  last: number;
  hitAt: number;
}

export const HP_TRAIL_START: HpTrail = { from: 0, last: -1, hitAt: 0 };

function trailAt(t: HpTrail, now: number, spec: { holdMs: number; fallMs: number }): number {
  const k = spec.fallMs > 0 ? (now - t.hitAt - spec.holdMs) / spec.fallMs : 1;
  const c = Math.max(0, Math.min(1, k));
  return t.from + (t.last - t.from) * c;
}

/**
 * 체력 비율 `ratio` 를 받아 다음 잔상 상태와 지금 그릴 잔상 비율(늘 `ratio` 이상)을 돌려준다.
 * 맞으면(비율이 줄면) 지금 보이는 잔상 위치에서 다시 머물기 시작하고, 회복하면 잔상이 채움보다 앞서지 않게 바로 따라간다.
 */
export function hpTrailStep(
  t: HpTrail,
  ratio: number,
  now: number,
  spec: { holdMs: number; fallMs: number },
): { trail: HpTrail; ghost: number } {
  const r = Math.max(0, Math.min(1, ratio));
  let next = t;
  if (t.last < 0) next = { from: r, last: r, hitAt: now };
  else if (r < t.last) next = { from: Math.max(trailAt(t, now, spec), t.last), last: r, hitAt: now };
  else if (r > t.last) {
    const shown = trailAt(t, now, spec);
    next = shown > r ? { from: shown, last: r, hitAt: now - spec.holdMs } : { from: r, last: r, hitAt: now };
  }
  return { trail: next, ghost: Math.max(r, trailAt(next, now, spec)) };
}
