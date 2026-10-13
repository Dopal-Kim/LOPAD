/**
 * 62 루프 3 시스템 I (P0-N2·P1-N3): E 대상 하나 고르기 — 화면 프롬프트와 E 가 같은 판정을 쓴다.
 *
 * 방 안의 E 대상은 네 곳에서 온다 — 구조물(StructureSystem) · 종군 상인(ShopKeeper) · 장터 노점 칸(ShopStalls) ·
 * 사연·단서·초소 소품(BundleProps). 예전에는 곳마다 따로 '가장 가까운 것'을 고르고, 프롬프트는 구조물 → 상인 → 소품 순서로,
 * E 는 각자 받아서 프롬프트에 보이는 것과 다른 것이 열렸다(노점 앞 E → 옆 장부대 · 사연 NPC 앞 프롬프트 = 궤짝).
 *
 * 규칙: 각 곳이 자기 반경 안 후보 하나와 **대상 중심까지 거리**를 내고, 가장 가까운 한 곳만 프롬프트에 보이고 E 를 받는다.
 * 거리가 같으면 FOCUS_ORDER 앞쪽. Phaser 의존 없음.
 */
export type FocusSource = 'structure' | 'keeper' | 'stall' | 'prop';

/** 같은 거리일 때 앞선다 */
export const FOCUS_ORDER: readonly FocusSource[] = ['keeper', 'stall', 'prop', 'structure'];

export interface FocusCandidate {
  source: FocusSource;
  /** 플레이어 → 대상 중심 (월드 px) */
  dist: number;
}

/** 후보 중 가장 가까운 곳 (없으면 null) */
export function pickFocus(cands: readonly (FocusCandidate | null | undefined)[]): FocusSource | null {
  let best: FocusCandidate | null = null;
  for (const c of cands) {
    if (!c || !Number.isFinite(c.dist)) continue;
    if (
      !best ||
      c.dist < best.dist ||
      (c.dist === best.dist && FOCUS_ORDER.indexOf(c.source) < FOCUS_ORDER.indexOf(best.source))
    )
      best = c;
  }
  return best?.source ?? null;
}
