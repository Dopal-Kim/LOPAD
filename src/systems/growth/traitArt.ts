/**
 * 61 단계 5 (P13 §1-3) 개성 그림·발동음 이름 규칙 (Phaser 의존 없음 — 계약 art §27 · UI §18.1 · sound §11).
 * - 카드 그림: 파일 `sprites/ui_traits/<무기>_<개성 id>.png` → 텍스처 키 `ui_traits/<무기>_<개성 id>` (시스템이 로드한 것만 iconKey)
 * - 전투 fx: `fx/v3/trait_<무기>_<개성 id>` (+ 부위 접미 `_<part>` — 착지·꽂힘 등). 없으면 기존 fx 변주로 그린다(씬 TraitMoves)
 * - 발동음: `sfx/trait_<무기>_<개성 id>` → 행동 갈래 `sfx/trait_<act>` → 없으면 무음 (manifest 에 생기면 그때부터)
 */
import { ASSETS } from '../../core/Constants';
import type { TraitAct } from '../../data/growthTypes';

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
