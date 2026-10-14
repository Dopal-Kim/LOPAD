/**
 * 62 루프 2 시스템 C (P16 §4 · 점검 P1-8) 메타 해금 '기억' 데이터 (Phaser 의존 없음). `data/memory.json`.
 * 규칙(해금·책·효과 모음)은 `systems/memory/memory.ts`.
 */
import memoryJson from '../../data/memory.json';
import { TRAITS } from './growth';
import { WEAPONS } from './index';

export type MemoryKind = 'keepsake' | 'aspect' | 'pool' | 'shop';
export type MemoryChapterKind = MemoryKind | 'stat';
/** 장터에 놓일 것 — inkBottle 먹물 한 병(개성 다시 뽑기) · bellows 풀무질 한 번(단련 1회) */
export type ShopGood = 'inkBottle' | 'bellows';

/** 기억의 소품 효과 (런 시작에 적용) */
export interface KeepsakeEffect {
  /** 시작 전표 */
  startGold?: number;
  /** 첫 개성 발현 카드 + */
  firstTraitCards?: number;
  /** 이 생의 첫 피격 피해 0 (횟수) */
  firstHitBlock?: number;
  /** 대쉬 충전 + */
  dashCharges?: number;
}

export interface MemoryDef {
  id: string;
  kind: MemoryKind;
  name: string;
  /** 한 문장 (수치 없음) */
  line: string;
  /** 수치 틀 ({키} = effect 값 — aspect·pool·shop 은 pick 틀로 만든다) */
  detail?: string;
  /** 상세 보기 아래 흐린 한 줄 */
  flavor?: string;
  cost: number;
  /** aspect·pool: 무기 id */
  weapon?: string;
  effect?: KeepsakeEffect;
  /** aspect: 시작 개성 id */
  trait?: string;
  /** pool: 풀에 들이는 개성 id (열기 전에는 풀에 없음) */
  traits?: string[];
  /** shop: 상점 품목 */
  good?: ShopGood;
}

export interface MemoryData {
  title: string;
  /** 62 I: 기억 칸 그림 파일 이름 (`ui_relics/<이름>`) — 키 = 기억 id · `stat:<강화 id>` · 'none'(빈손) */
  icons?: Record<string, string>;
  /** 기억 장 머리 문장 (위 → 아래) */
  intro: string[];
  /** '지닌 영혼 {n}' */
  souls: string;
  firstUnlockCost: number;
  chapters: { kind: MemoryChapterKind; name: string }[];
  /** 칸 상태 글 (locked · affordable · short · recalled · equipped · equip · unequip) */
  states: Record<string, string>;
  recalledNotice: string;
  firstOpen: string;
  openKey: string;
  pick: {
    aspectTitle: string;
    aspectHint: string;
    aspectBase: string;
    aspectBaseLine: string;
    keepsakeTitle: string;
    keepsakeNone: string;
    keepsakeNoneLine: string;
    aspectDetail: string;
    poolDetail: string;
    shopDetail: Record<ShopGood, string>;
  };
  items: MemoryDef[];
}

const KINDS: readonly MemoryKind[] = ['keepsake', 'aspect', 'pool', 'shop'];
const DIGIT = /[0-9]/;

export function validateMemory(d: MemoryData): MemoryData {
  const fail = (m: string): never => {
    throw new Error(`[data] memory: ${m}`);
  };
  if (!d.title || !d.intro?.length || !d.souls) fail('title·intro·souls 없음');
  for (const k of ['affordable', 'short', 'recalled', 'equipped']) if (!d.states?.[k]) fail(`states.${k} 없음`);
  if (!(d.firstUnlockCost > 0)) fail('firstUnlockCost 는 양수');
  if (!Array.isArray(d.items) || d.items.length === 0) fail('items 비어 있음');
  const seen = new Set<string>();
  const pooled = new Set<string>();
  for (const m of d.items) {
    if (seen.has(m.id)) fail(`중복 id ${m.id}`);
    seen.add(m.id);
    if (!KINDS.includes(m.kind)) fail(`${m.id}.kind 알 수 없음`);
    if (!m.name || !m.line) fail(`${m.id}: name·line 없음`);
    if (DIGIT.test(m.line)) fail(`${m.id}.line: 문장에 숫자 금지 (수치는 detail)`);
    if (!(m.cost > 0)) fail(`${m.id}.cost 는 양수`);
    if (m.kind === 'aspect' || m.kind === 'pool') {
      if (!m.weapon || !WEAPONS[m.weapon]) fail(`${m.id}.weapon 알 수 없음`);
    }
    if (m.kind === 'aspect') {
      const t = TRAITS.find((x) => x.id === m.trait);
      if (!t || t.weapon !== m.weapon || t.branch || t.memory) fail(`${m.id}.trait: 그 무기의 기본 개성이어야 한다`);
    }
    if (m.kind === 'pool') {
      if (!m.traits?.length) fail(`${m.id}.traits 비어 있음`);
      for (const id of m.traits ?? []) {
        const t = TRAITS.find((x) => x.id === id);
        if (!t || t.weapon !== m.weapon || !t.memory)
          fail(`${m.id}.traits.${id}: 그 무기의 기억 개성(memory)이어야 한다`);
        if (pooled.has(id)) fail(`${m.id}.traits.${id}: 두 기억이 같은 개성을 잠근다`);
        pooled.add(id);
      }
    }
    if (m.kind === 'keepsake' && (!m.effect || Object.keys(m.effect).length === 0)) fail(`${m.id}.effect 없음`);
    if (m.kind === 'shop' && m.good !== 'inkBottle' && m.good !== 'bellows') fail(`${m.id}.good 알 수 없음`);
  }
  // 62 루프 4: 기억 개성은 모두 어느 풀 칸에 들어 있어야 한다 (아니면 영영 못 얻는다)
  for (const t of TRAITS) if (t.memory && !pooled.has(t.id)) fail(`traits.${t.id}: 기억 개성인데 떠올릴 칸이 없다`);
  // 양상 개성이 풀 확장에 잠겨 있으면 안 된다 (시작에 쥐는 카드)
  for (const m of d.items)
    if (m.kind === 'aspect' && m.trait && pooled.has(m.trait)) fail(`${m.id}.trait 이 풀 확장에 잠겨 있다`);
  const cheapest = Math.min(...d.items.map((m) => m.cost));
  if (cheapest > d.firstUnlockCost)
    fail(`가장 싼 기억(${cheapest})이 firstUnlockCost(${d.firstUnlockCost})보다 비싸다`);
  return d;
}

export const MEMORY: MemoryData = validateMemory(memoryJson as unknown as MemoryData);

export function memoryDef(id: string): MemoryDef | undefined {
  return MEMORY.items.find((m) => m.id === id);
}
