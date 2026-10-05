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

/** 0~1 (임계가 0 이하면 0) */
export function personalityRatio(w: { personality: number; threshold: number }): number {
  if (!(w.threshold > 0)) return 0;
  return Math.max(0, Math.min(1, w.personality / w.threshold));
}

export interface CombatRows {
  /** 묶음 위 끝에서 행마다 y */
  hp: number;
  weapon: number;
  /** 보조 자원 줄 (없으면 null) */
  sub: number | null;
  slots: number;
  /** 묶음 높이 */
  h: number;
}

/**
 * 묶음 행 배치: 체력 → 무기·자원(눈금 2배면 bigRowH) → (보조 자원) → 독주·소모품·전표 → 개성 진행선.
 * 무기 줄은 자원이 없어도 남긴다(무기 아이콘 · 넣기/뽑기).
 */
export function combatRows(
  spec: { padY: number; rowH: number; bigRowH: number; rowGap: number; personalityH: number; personalityInset: number },
  opts: { big: boolean; sub: boolean },
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
  const slots = y;
  y += spec.rowH;
  // 개성 진행선은 아래 여백 안 (personalityInset 위)
  const h = y + Math.max(spec.padY, spec.personalityInset + spec.personalityH + 2);
  return { hp, weapon, sub, slots, h };
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
