/**
 * 62 루프 2 시스템 C (P16 §4 · 점검 P1-8) 메타 해금 '기억' 규칙 (Phaser 의존 없음 — 메타 세이브 `MetaData.memory`).
 * 해금 · 다음 해금 · 일기장 기억 장(계약 `UiMemoryBook`) · 런에 쓰는 효과 모음(잠긴 개성 · 양상 · 소품 · 상점 품목).
 * 능력치 강화(몸의 기억)는 기존 `meta.upgrades`(3줄) — 해금 id 'stat:<강화 id>' 로 같은 장에 싣는다.
 */
import { MEMORY, memoryDef, type KeepsakeEffect, type MemoryDef, type ShopGood } from '../../data/memory';
import { traitDef } from '../../data/growth';
import { WEAPONS } from '../../data';
import type { UiMemoryBook, UiMemoryEntry, UiMemoryKind, UiNextUnlock } from '../../contract/ui';
import { buyUpgrade, upgradeCost, type MetaConfig, type MetaData, type UpgradeId } from '../meta';
import { fill } from '../story';

export const STAT_PREFIX = 'stat:';

/** 연 기억 id */
export function unlockedSet(meta: Pick<MetaData, 'memory'>): Set<string> {
  return new Set((meta.memory?.unlocked ?? []).filter((id) => Boolean(memoryDef(id))));
}

export function isUnlocked(meta: Pick<MetaData, 'memory'>, id: string): boolean {
  return unlockedSet(meta).has(id);
}

/** 연다 — 영혼이 모자라거나 이미 열렸거나 모르는 id 면 null. stat:<id> 는 능력치 강화 한 단계 */
export function unlockMemory(meta: MetaData, id: string, cfg?: MetaConfig): MetaData | null {
  if (id.startsWith(STAT_PREFIX)) return buyUpgrade(meta, id.slice(STAT_PREFIX.length) as UpgradeId, cfg);
  const def = memoryDef(id);
  if (!def || isUnlocked(meta, id) || meta.souls < def.cost) return null;
  const unlocked = [...unlockedSet(meta), id];
  // 첫 소품이면 다음 생에 바로 지닌다
  const keepsake = def.kind === 'keepsake' && !meta.memory?.keepsake ? id : (meta.memory?.keepsake ?? null);
  return { ...meta, souls: meta.souls - def.cost, memory: { unlocked, keepsake } };
}

/** 다음 생에 지닐 소품을 정한다 (null = 빈손). 안 열린 소품이면 null */
export function setKeepsake(meta: MetaData, id: string | null): MetaData | null {
  if (id !== null && (memoryDef(id)?.kind !== 'keepsake' || !isUnlocked(meta, id))) return null;
  return { ...meta, memory: { unlocked: [...unlockedSet(meta)], keepsake: id } };
}

/** 열린 기억의 소품 (데이터 순서) */
export function openKeepsakes(meta: Pick<MetaData, 'memory'>): MemoryDef[] {
  const u = unlockedSet(meta);
  return MEMORY.items.filter((m) => m.kind === 'keepsake' && u.has(m.id));
}

/** 다음 생에 지닐 소품 기본값 (마지막 고른 것 · 없거나 잠겼으면 첫 열린 소품 · 고른 적 있는 빈손이면 null) */
export function defaultKeepsake(meta: Pick<MetaData, 'memory'>): string | null {
  const open = openKeepsakes(meta);
  const k = meta.memory?.keepsake;
  if (k === null) return null;
  if (k && open.some((m) => m.id === k)) return k;
  return open[0]?.id ?? null;
}

/** 이 무기의 열린 양상 (없으면 null) */
export function openAspect(meta: Pick<MetaData, 'memory'>, weapon: string): MemoryDef | null {
  const u = unlockedSet(meta);
  return MEMORY.items.find((m) => m.kind === 'aspect' && m.weapon === weapon && u.has(m.id)) ?? null;
}

/** 아직 잠긴 개성 (풀 확장을 열지 않은 무기의 개성 두 장) */
export function lockedTraits(meta: Pick<MetaData, 'memory'>, weapon?: string): Set<string> {
  const u = unlockedSet(meta);
  const out = new Set<string>();
  for (const m of MEMORY.items)
    if (m.kind === 'pool' && !u.has(m.id) && (!weapon || m.weapon === weapon))
      for (const t of m.traits ?? []) out.add(t);
  return out;
}

/** 진열에 오를 상점 품목 (연 것만) */
export function openShopGoods(meta: Pick<MetaData, 'memory'>): ShopGood[] {
  const u = unlockedSet(meta);
  return MEMORY.items.filter((m) => m.kind === 'shop' && u.has(m.id) && m.good).map((m) => m.good!);
}

/** 소품 효과 (없으면 빈 값) */
export function keepsakeEffect(id: string | null | undefined): KeepsakeEffect {
  const d = id ? memoryDef(id) : undefined;
  return d?.kind === 'keepsake' ? { ...(d.effect ?? {}) } : {};
}

/** 수치 설명 (모양·풀은 개성 이름 · 장터는 품목 · 소품은 effect 값) */
export function memoryDetail(m: MemoryDef): string {
  const P = MEMORY.pick;
  if (m.kind === 'aspect') return fill(P.aspectDetail, { trait: traitDef(m.trait ?? '')?.name ?? m.trait ?? '' });
  if (m.kind === 'pool')
    return fill(P.poolDetail, {
      traits: (m.traits ?? []).map((id) => `'${traitDef(id)?.name ?? id}'`).join(' · '),
    });
  if (m.kind === 'shop' && m.good) return P.shopDetail[m.good] ?? '';
  const vars: Record<string, number> = {};
  for (const [k, v] of Object.entries(m.effect ?? {})) if (typeof v === 'number') vars[k] = v;
  return fill(m.detail ?? '', vars);
}

/** 소품 그림 키 (아트 §31-4 `ui_relics/keepsake_<id>`) */
export function keepsakeIconKey(id: string): string {
  return `ui_relics/keepsake_${id}`;
}

/** 62 I: 아트 기억 칸 그림 키 (`data/memory.json icons` — 장터의 것·몸의 기억·빈손). 표에 없으면 null */
export function memoryArtKey(id: string): string | null {
  const f = MEMORY.icons?.[id];
  return f ? `ui_relics/${f}` : null;
}

/** 그림 키: 아트 기억 칸 그림(icons) · 소품 = `ui_relics/keepsake_<id>` · 모양 = 그 개성 그림 · 풀 = 첫 개성 그림 — 로드된 것만 */
export function memoryIconKey(m: MemoryDef, loaded: (key: string) => boolean): string | undefined {
  const art = memoryArtKey(m.id);
  if (art && loaded(art)) return art;
  if (m.kind === 'keepsake') {
    const own = keepsakeIconKey(m.id);
    return loaded(own) ? own : undefined;
  }
  const t = m.kind === 'aspect' ? m.trait : m.kind === 'pool' ? m.traits?.[0] : undefined;
  if (t && m.weapon) {
    const fb = `ui_traits/${m.weapon}_${t}`;
    if (loaded(fb)) return fb;
  }
  return undefined;
}

export function memoryEntry(
  m: MemoryDef,
  meta: Pick<MetaData, 'memory' | 'souls'>,
  loaded: (key: string) => boolean = () => false,
): UiMemoryEntry {
  const unlocked = isUnlocked(meta, m.id);
  const icon = memoryIconKey(m, loaded);
  return withState({
    id: m.id,
    kind: m.kind,
    name: m.name,
    line: m.line,
    detail: memoryDetail(m),
    cost: unlocked ? 0 : m.cost,
    unlocked,
    affordable: !unlocked && meta.souls >= m.cost,
    ...(m.weapon ? { weapon: m.weapon, weaponName: WEAPONS[m.weapon]?.name ?? m.weapon } : {}),
    ...(icon ? { iconKey: icon } : {}),
    ...(m.flavor ? { flavor: m.flavor } : {}),
  });
}

/** 상태 한 줄을 붙인다 */
function withState(e: Omit<UiMemoryEntry, 'state'>): UiMemoryEntry {
  return { ...e, state: memoryState(e) };
}

function statEntries(meta: MetaData, cfg: MetaConfig, loaded: (key: string) => boolean = () => false): UiMemoryEntry[] {
  return cfg.upgrades.map((u) => {
    const art = memoryArtKey(`${STAT_PREFIX}${u.id}`);
    const lv = meta.upgrades[u.id] ?? 0;
    const maxed = lv >= u.maxLevel;
    const cost = maxed ? 0 : upgradeCost(u, lv);
    // 수치 = 다음 단계까지의 합계 (다 떠올렸으면 지금 합계)
    const n = u.perLevel * Math.min(u.maxLevel, lv + (maxed ? 0 : 1));
    return withState({
      id: `${STAT_PREFIX}${u.id}`,
      kind: 'stat' as const,
      name: u.name,
      line: u.line ?? u.name,
      detail: fill(u.detail ?? u.name, { n }),
      cost,
      unlocked: maxed,
      affordable: !maxed && meta.souls >= cost,
      level: { n: lv, max: u.maxLevel },
      ...(art && loaded(art) ? { iconKey: art } : {}),
    });
  });
}

/** 다음 해금: 아직 못 연 기억 중 가장 싼 것 (다 열었으면 가장 싼 남은 몸의 기억). 없으면 null */
export function nextUnlock(meta: MetaData, cfg: MetaConfig): UiNextUnlock | null {
  const u = unlockedSet(meta);
  const locked = MEMORY.items.filter((m) => !u.has(m.id));
  const pick = locked.reduce<MemoryDef | null>((a, m) => (!a || m.cost < a.cost ? m : a), null);
  if (pick) return { id: pick.id, name: pick.name, cost: pick.cost, left: Math.max(0, pick.cost - meta.souls) };
  const stat = statEntries(meta, cfg)
    .filter((e) => !e.unlocked)
    .reduce<UiMemoryEntry | null>((a, e) => (!a || e.cost < a.cost ? e : a), null);
  return stat ? { id: stat.id, name: stat.name, cost: stat.cost, left: Math.max(0, stat.cost - meta.souls) } : null;
}

/** 지금 열 수 있는 것이 있나 (의식 귀퉁이 canBuy) */
export function canUnlockAny(meta: MetaData, cfg: MetaConfig): boolean {
  return (
    MEMORY.items.some((m) => !isUnlocked(meta, m.id) && meta.souls >= m.cost) ||
    statEntries(meta, cfg).some((e) => e.affordable)
  );
}

/** 일기장 '기억' 장 (계약 `UiMemoryBook`) */
export function memoryBook(
  meta: MetaData,
  cfg: MetaConfig,
  loaded: (key: string) => boolean = () => false,
): UiMemoryBook {
  const chapters = MEMORY.chapters.map((c) => ({
    kind: c.kind as UiMemoryKind,
    name: c.name,
    entries:
      c.kind === 'stat'
        ? statEntries(meta, cfg, loaded)
        : MEMORY.items.filter((m) => m.kind === c.kind).map((m) => memoryEntry(m, meta, loaded)),
  }));
  return {
    title: MEMORY.title,
    intro: [...MEMORY.intro],
    soulsText: fill(MEMORY.souls, { n: meta.souls }),
    souls: meta.souls,
    chapters,
    next: nextUnlock(meta, cfg),
    keepsake: defaultKeepsake(meta),
  };
}

/** 칸 상태 한 줄 — '떠올렸다' · '떠올린다 · 영혼 {n}' · '영혼이 모자란다 · 영혼 {n}' */
export function memoryState(e: Pick<UiMemoryEntry, 'unlocked' | 'affordable' | 'cost'>): string {
  const S = MEMORY.states;
  if (e.unlocked) return S.recalled;
  return fill(e.affordable ? S.affordable : S.short, { n: e.cost });
}

/** 메뉴 줄 detail (목록 화면용 — 한 문장 · 수치 · 상태). 몸의 기억은 '{n}단계' 를 붙인다 */
export function memoryLineDetail(e: UiMemoryEntry, levelText: (n: number) => string): string {
  const lv = e.level ? ` · ${levelText(e.level.n)}` : '';
  return `${e.line} — ${e.detail}${lv} · ${memoryState(e)}`;
}
