/**
 * 53라운드 Q59·Q69: 큰 소품 아트 `placement` 힌트 → 배치 규칙 (Phaser 없음). 배치 자체는 `bigProps.planBigProps`.
 *
 * - 힌트 속 규칙어(QUARTER.BIG_PROPS.HINTS)를 적힌 순서대로 ('벽 앞·구석' = 북쪽 벽 앞에 못 놓으면 구석)
 * - 규칙어가 없으면 52라운드 이름 규칙(`LEGACY_RULES` — 가로등·화로·우물·좌판·상자 더미), 그것도 없으면 벽가(`DEFAULT_RULE`, Q69 '그 외 = 벽가')
 * - Q69: 북쪽을 피해야 하는(avoidNearBorder 에 north) '벽 앞' 소품은 북쪽 벽 앞 대신 서·동 벽가
 */
import { QUARTER } from '../core/Constants';

/**
 * 배치 규칙: 북쪽 벽 앞 · 광장 고리(화로) · 구석 · 서·동 벽가 (Q59) ·
 * 출구 좌우 짝 · 서·동 벽가 세로 · 가운데 축 좌우 짝 · 탁자 옆 (Q69)
 */
export type BigPropRule = 'north' | 'ring' | 'corner' | 'cover' | 'exit' | 'column' | 'mirror' | 'table';

export interface BigPropShape {
  name: string;
  footprint: [number, number];
  /** 계약 §14 아트 배치 힌트 ('floor (벽 앞)' 등) */
  placement?: string;
  /** 계약 §14: 테두리 그림에 같은 물건이 이미 있는 쪽 (north·south·west·east) */
  avoidNearBorder?: readonly string[];
  /** 아트 JSON solid: false 면 걷기 통과(53라운드 후속 — 황무지 weapons_stuck 등). 없거나 true 면 막힘 */
  solid?: boolean;
}

/** 소품 하나의 규칙 목록 (앞이 우선, 중복 없음) */
export function bigPropRules(s: Pick<BigPropShape, 'name' | 'placement' | 'avoidNearBorder'>): BigPropRule[] {
  const B = QUARTER.BIG_PROPS;
  const hint = s.placement ?? '';
  const found: { rule: BigPropRule; at: number }[] = [];
  for (const [rule, words] of Object.entries(B.HINTS) as [BigPropRule, readonly string[]][]) {
    const at = Math.min(...words.map((w) => hint.indexOf(w)).filter((i) => i >= 0));
    if (Number.isFinite(at)) found.push({ rule, at });
  }
  const legacy = (B.LEGACY_RULES as Record<string, BigPropRule | undefined>)[s.name];
  const rules: BigPropRule[] =
    found.length > 0 ? found.sort((a, b) => a.at - b.at).map((f) => f.rule) : [legacy ?? B.DEFAULT_RULE];
  const avoidNorth = (s.avoidNearBorder ?? []).includes('north');
  const out: BigPropRule[] = [];
  for (const r of rules) {
    const rule: BigPropRule = r === 'north' && avoidNorth ? 'cover' : r;
    if (!out.includes(rule)) out.push(rule);
  }
  return out;
}
