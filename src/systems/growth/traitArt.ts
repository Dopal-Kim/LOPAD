/**
 * 61 단계 5 (P13 §1-3) 개성 그림·발동음 이름 규칙 (Phaser 의존 없음 — 계약 art §27 · UI §18.1 · sound §11).
 * - 카드 그림: 파일 `sprites/ui_traits/<무기>_<개성 id>.png` → 텍스처 키 `ui_traits/<무기>_<개성 id>` (시스템이 로드한 것만 iconKey)
 * - 전투 fx: `fx/v3/trait_<무기>_<개성 id>` (+ 부위 접미 `_<part>` — 착지·꽂힘 등). 없으면 기존 fx 변주로 그린다(씬 TraitMoves)
 * - 발동음: `sfx/trait_<무기>_<개성 id>` → 행동 갈래 `sfx/trait_<act>` → 없으면 무음 (manifest 에 생기면 그때부터)
 */
import { ASSETS } from '../../core/Constants';
import type { TraitAct } from '../../data/growthTypes';
import { TRAITS } from '../../data/growth';

/** 카드 그림 폴더 (assets 상대) */
export const TRAIT_ICON_DIR = `${ASSETS.SPRITES_DIR}/ui_traits`;

/** 카드 그림 파일 이름 (확장자 포함) */
export function traitIconFile(weapon: string, traitId: string): string {
  return `${weapon}_${traitId}.png`;
}

/** 카드 그림 텍스처 키 (아트 그림 키 규칙 — 계약 UI §18.1) */
export function traitIconKey(weapon: string, traitId: string): string {
  return `ui_traits/${weapon}_${traitId}`;
}

/**
 * 62 루프 4: 그림이 아직 없을 때 대신 쓸 카드 그림 후보 — 자기 그림 → 같은 무기·같은 태그 개성 그림(기본 먼저, 칼 취기처럼 기본에
 * 없으면 갈래) → 같은 동사 칸 기본 개성 그림. 앞에서부터 로드된 것 (새 기억 개성 8장 그림이 들어오기 전 — 아트 작업 중)
 */
export function traitIconCandidates(weapon: string, traitId: string): string[] {
  const t = TRAITS.find((x) => x.id === traitId);
  const out = [traitIconKey(weapon, traitId)];
  if (!t) return out;
  const others = TRAITS.filter((o) => o.weapon === weapon && o.id !== t.id && !o.memory);
  const pick = (list: typeof others) => list.forEach((o) => out.push(traitIconKey(weapon, o.id)));
  pick(others.filter((o) => o.tag === t.tag && !o.branch));
  pick(others.filter((o) => o.tag === t.tag && o.branch));
  pick(others.filter((o) => o.verb === t.verb && o.tag !== t.tag && !o.branch));
  return out;
}

/** 공명 카드 그림 (`sprites/ui_traits/<공명 id>.png` → 키 `ui_traits/<공명 id>` — 계약 UI §18.1) */
export function resonanceIconFile(resId: string): string {
  return `${resId}.png`;
}
export function resonanceIconKey(resId: string): string {
  return `ui_traits/${resId}`;
}

/** 씬이 실제로 로드한 카드 그림 키 (Phaser 없는 스냅샷 쪽이 '로드된 것만' 넘기도록) */
const loadedIcons = new Set<string>();
export function markIconLoaded(key: string): void {
  loadedIcons.add(key);
}
export function iconLoaded(key: string): boolean {
  return loadedIcons.has(key);
}

/** 개성 전투 fx id (`fx/v3/trait_<무기>_<개성 id>[_<part>]`) · 공명은 `trait_<공명 id>[_<part>]` (공명 id 에 무기가 들어 있다) */
export function traitFxId(weapon: string, traitId: string, part?: string): string {
  const base = traitId.startsWith('res_') ? `trait_${traitId}` : `trait_${weapon}_${traitId}`;
  return `${base}${part ? `_${part}` : ''}`;
}

/** 발동음 후보 (앞에서부터 manifest 에 있는 첫 소리) */
export function traitProcSfx(weapon: string, traitId: string, act: TraitAct | undefined): string[] {
  const out = [`sfx/trait_${weapon}_${traitId}`];
  if (act) out.push(`sfx/trait_${act}`);
  return out;
}

/** 공명 켜짐 소리 후보 (공명 전용 → 개성 발현 → 옛 이중 개성) */
export const RESONANCE_SFX: readonly string[] = ['sfx/resonance_on', 'sfx/trait_manifest', 'sfx/dual_trait'];
