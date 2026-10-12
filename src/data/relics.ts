/**
 * 62 루프 2 시스템 C (P16 §1 · 점검 P1-5) '유품' 카드 데이터 (Phaser 의존 없음). `data/relics.json` — 문장은 스토리 63 팩.
 * 효과는 같은 id 의 패시브(`data/passives.json`)가 맡는다 — 이 파일은 카드 문법(이름·무기별 한 문장·수치 detail 틀·태그 1개)만.
 * lines 에 무기가 없으면 그 무기에게는 제시하지 않는다('*' = 공통). detail 틀 채우기는 `systems/relics.relicDetailText`.
 */
import relicsJson from '../../data/relics.json';
import passivesJson from '../../data/passives.json';
import { isTagId, type TagId } from './buildTypes';

export const RELIC_ANY = '*';

export interface RelicDef {
  id: string;
  name: string;
  /** 카드에 보이는 태그 1개 (1층에서 켜진 태그) */
  tag: TagId;
  /** 무기 id → 조건 → 행동 한 문장 (수치 없음). '*' = 공통 */
  lines: Record<string, string>;
  /** 무기 id → 수치 틀 (상세 보기 D — 자리표시는 패시브 수치 키). '*' = 공통 */
  detail: Record<string, string>;
  /** 상세 보기 아래 흐린 한 줄 */
  flavor?: string;
}

export interface RelicsUi {
  bossTitle: string;
  bossSub: Record<string, string>;
  bossNotice: string;
  eliteTitle: string;
  eliteSub: string;
  rewardTitle: string;
  rewardSub: string;
  eventTitle: string;
  curseTitle: string;
  footer: string;
  owned: string;
  level: string;
  maxed: string;
  emptyPool: string;
  picked: string;
  strongAttack: Record<string, string>;
}

export interface RelicsData {
  bossChoices: number;
  ui: RelicsUi;
  items: RelicDef[];
}

/** 카드 문장 금지 — 아라비아 숫자 · ×·% (용어집 digitsInCardLine · multSign) */
const CARD_BANNED = /[0-9×%]/;

export function validateRelics(d: RelicsData, passiveIds: readonly string[]): RelicsData {
  const fail = (m: string): never => {
    throw new Error(`[data] relics: ${m}`);
  };
  for (const k of ['bossTitle', 'rewardTitle', 'footer', 'level', 'picked'] as const)
    if (typeof d.ui?.[k] !== 'string' || !d.ui[k]) fail(`ui.${k} 없음`);
  if (!(d.bossChoices >= 1)) fail('bossChoices 는 1 이상');
  if (!Array.isArray(d.items) || d.items.length === 0) fail('items 비어 있음');
  const seen = new Set<string>();
  for (const r of d.items) {
    if (seen.has(r.id)) fail(`중복 id ${r.id}`);
    seen.add(r.id);
    if (!passiveIds.includes(r.id)) fail(`${r.id}: 같은 id 의 패시브가 없다 (효과 원천)`);
    if (!r.name) fail(`${r.id}.name 없음`);
    if (!isTagId(r.tag)) fail(`${r.id}.tag 알 수 없음`);
    const lineKeys = Object.keys(r.lines ?? {});
    if (lineKeys.length === 0) fail(`${r.id}.lines 비어 있음`);
    for (const [w, line] of Object.entries(r.lines)) {
      if (typeof line !== 'string' || !line) fail(`${r.id}.lines.${w} 비어 있음`);
      if (CARD_BANNED.test(line)) fail(`${r.id}.lines.${w}: 카드 문장에 숫자·×·% 금지 (수치는 detail)`);
    }
    for (const w of lineKeys) if (!r.detail?.[w] && !r.detail?.[RELIC_ANY]) fail(`${r.id}.detail: ${w} 수치 틀 없음`);
  }
  return d;
}

const PASSIVE_IDS = (passivesJson as unknown as { items: { id: string }[] }).items.map((p) => p.id);

export const RELICS: RelicsData = validateRelics(relicsJson as unknown as RelicsData, PASSIVE_IDS);

export function relicDef(id: string): RelicDef | undefined {
  return RELICS.items.find((r) => r.id === id);
}

/** 이 무기에게 보이는 문장 (없으면 null — 이 무기에게는 제시하지 않는다) */
export function relicLine(r: RelicDef, weapon: string): string | null {
  return r.lines[weapon] ?? r.lines[RELIC_ANY] ?? null;
}

/** 이 무기의 수치 틀 */
export function relicDetailTemplate(r: RelicDef, weapon: string): string {
  return r.detail[weapon] ?? r.detail[RELIC_ANY] ?? '';
}
