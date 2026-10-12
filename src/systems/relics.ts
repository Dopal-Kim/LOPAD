/**
 * 62 루프 2 시스템 C (P16 §1 · 점검 P1-5) 유품 규칙 (Phaser 의존 없음): 이 무기에게 제시할 유품 · 뽑기 · 수치 틀 채우기 ·
 * 계약 카드(`UiRelic`) · 카드 그림 키(유품 그림 → 없으면 같은 태그 개성 그림 대체). 효과는 같은 id 패시브(`PassiveSet`)가 맡는다 —
 * 같은 유품을 또 고르면 한 단계 깊어진다(패시브 레벨, 최대 maxLevel).
 * 그림 파일 `sprites/ui_relics/<id>.png` → 텍스처 키 `ui_relics/<id>` (씬이 로드한 것만 — `traitArt.iconLoaded`).
 */
import { ASSETS } from '../core/Constants';
import { RELICS, relicDef, relicDetailTemplate, relicLine, type RelicDef } from '../data/relics';
import { TRAITS } from '../data/growth';
import type { FloorScope } from '../data/floorScope';
import type { UiRarity, UiRelic, UiRelicSource, UiTagId } from '../contract/ui';
import { iconLoaded, traitIconKey } from './growth/traitArt';
import { levelParam, type PassiveDef, type PassiveSet } from './passives';
import type { Rng } from './rng';
import { fill } from './story';

/** 유품 카드 그림 폴더 (assets 상대) */
export const RELIC_ICON_DIR = `${ASSETS.SPRITES_DIR}/ui_relics`;

export function relicIconFile(id: string): string {
  return `${id}.png`;
}

export function relicIconKey(id: string): string {
  return `ui_relics/${id}`;
}

/** 대체 그림: 이 무기의 같은 태그 개성 그림 (기본 개성 먼저). 없으면 null */
export function relicFallbackKey(r: Pick<RelicDef, 'tag'>, weapon: string): string | null {
  const same = TRAITS.filter((t) => t.weapon === weapon && t.tag === r.tag);
  const pick = same.find((t) => !t.branch) ?? same[0];
  return pick ? traitIconKey(weapon, pick.id) : null;
}

/** 지금 쓸 그림 키 — 유품 그림이 로드됐으면 그것, 아니면 대체(로드됐을 때만), 둘 다 없으면 undefined */
export function relicIcon(
  r: RelicDef,
  weapon: string,
  loaded: (key: string) => boolean = iconLoaded,
): string | undefined {
  const own = relicIconKey(r.id);
  if (loaded(own)) return own;
  const fb = relicFallbackKey(r, weapon);
  return fb && loaded(fb) ? fb : undefined;
}

/** 이 단계의 패시브 수치 (effects × 단계 · byLevel · rule.params · lowHpThreshold) */
export function relicValues(p: PassiveDef, level: number): Record<string, number> {
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(p.effects ?? {})) if (typeof v === 'number') out[k] = v * level;
  for (const [k, v] of Object.entries(p.byLevel ?? {})) out[k] = levelParam(v, level);
  for (const [k, v] of Object.entries(p.rule?.params ?? {})) {
    const n = levelParam(v, level);
    if (Array.isArray(v) || typeof v === 'number') out[k] = n;
  }
  if (typeof p.lowHpThreshold === 'number') out.lowHpThreshold = p.lowHpThreshold;
  return out;
}

/** 이미 퍼센트로 적힌 값 (×100 하지 않는다) */
const ALREADY_PERCENT = new Set(['critChanceAdd']);

/** 수 쓰기: 소수는 둘째 자리까지 (끝 0 지움) */
function num(v: number): string {
  const r = Math.round(v * 100) / 100;
  return Number.isInteger(r) ? String(r) : String(r).replace(/0+$/, '');
}

/**
 * 수치 틀 채우기 (스토리 63 팩 규칙): '{k}%' = ×100 반올림(critChanceAdd 제외) · '{k}초' = ms ÷1000 · 음수는 절댓값 ·
 * {strongAttack} = 무기별 강공 이름. 모르는 자리표시는 그대로 둔다
 */
export function relicDetailText(template: string, values: Record<string, number>, weapon: string): string {
  return template.replace(/\{(\w+)\}(%|초)?/g, (all, key: string, unit: string | undefined) => {
    if (key === 'strongAttack') return (RELICS.ui.strongAttack[weapon] ?? '') + (unit ?? '');
    const v = values[key];
    if (typeof v !== 'number') return all;
    const a = Math.abs(v);
    if (unit === '%') return `${ALREADY_PERCENT.has(key) ? num(a) : Math.round(a * 100)}%`;
    if (unit === '초') return `${num(a / 1000)}초`;
    return num(a);
  });
}

/** 유품이 아닌 패시브 · 이 무기 문장이 없는 유품 · 최대 단계 → 뽑기에서 뺄 id */
export function relicExclude(weapon: string, passives: Pick<PassiveSet, 'defs' | 'level' | 'maxLevel'>): string[] {
  return passives.defs
    .filter((p) => {
      const r = relicDef(p.id);
      return !r || !relicLine(r, weapon) || passives.level(p.id) >= passives.maxLevel;
    })
    .map((p) => p.id);
}

/** 희귀도 가중 n장 (PassiveSet.rollChoices — 테마 가중·확정 희귀도 그대로) */
export function rollRelics(
  passives: PassiveSet,
  weapon: string,
  rng: Rng,
  rarityWeights: Record<string, number>,
  count: number,
  opts: {
    rarities?: readonly string[];
    guaranteed?: { rarities: readonly string[]; count: number };
    themeTag?: UiTagId | null;
    themeMult?: number;
    floor?: FloorScope;
  } = {},
): PassiveDef[] {
  return passives.rollChoices(rng, rarityWeights, count, {
    ...opts,
    exclude: relicExclude(weapon, passives),
  });
}

const RARITIES: readonly UiRarity[] = ['common', 'rare', 'epic', 'legendary'];

/**
 * 계약 카드 (`UiRelic`) — 이 무기 문장이 없으면 null. level = 이 카드가 보여 주는 단계(고르면 될 단계 · 지닌 목록이면 지금 단계)
 */
export function uiRelic(
  p: PassiveDef,
  weapon: string,
  level: number,
  maxLevel: number,
  opts: { source?: UiRelicSource; owned?: boolean; loaded?: (key: string) => boolean } = {},
): UiRelic | null {
  const r = relicDef(p.id);
  if (!r) return null;
  const line = relicLine(r, weapon);
  if (!line) return null;
  const lv = Math.max(1, Math.min(maxLevel, level));
  const icon = relicIcon(r, weapon, opts.loaded ?? iconLoaded);
  return {
    id: r.id,
    name: r.name,
    line,
    detail: relicDetailText(relicDetailTemplate(r, weapon), relicValues(p, lv), weapon),
    tag: r.tag as UiTagId,
    rarity: (RARITIES as readonly string[]).includes(p.rarity) ? (p.rarity as UiRarity) : 'common',
    level: lv,
    maxLevel,
    levelText: fill(RELICS.ui.level, { n: lv }),
    ...(r.flavor ? { flavor: r.flavor } : {}),
    ...(opts.owned ? { owned: true } : {}),
    ...(icon ? { iconKey: icon } : {}),
    ...(opts.source ? { source: opts.source } : {}),
  };
}

/** 가진 유품 (얻은 순서, 지금 단계) — 이 무기 문장이 없는 옛 패시브는 빠진다 */
export function ownedRelics(passives: Pick<PassiveSet, 'owned' | 'def' | 'maxLevel'>, weapon: string): UiRelic[] {
  const out: UiRelic[] = [];
  for (const [id, lv] of Object.entries(passives.owned)) {
    const p = passives.def(id);
    const u = p ? uiRelic(p, weapon, lv, passives.maxLevel) : null;
    if (u) out.push(u);
  }
  return out;
}
