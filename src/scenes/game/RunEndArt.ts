/**
 * 62 루프 2 시스템 C 그림 로드 (아트 §31-4·5): 유품 카드 `ui_relics/<passiveId>` · 기억의 소품 `ui_relics/keepsake_<id>` ·
 * 처치자 초상 `ui_portraits/<적 id>`·`boss1`. 매니페스트에 있는 것만 받고, 받으면 `traitArt.markIconLoaded` — 스냅샷 쪽(Phaser 없음)이
 * '로드된 것만' 키를 내보낸다. 이미 있으면 바로 표시. 씬 사이 중복 받기는 `systems/sprites/imageOnce` 가 막는다.
 */
import type Phaser from 'phaser';
import { ASSETS } from '../../core/Constants';
import { RELICS } from '../../data/relics';
import { MEMORY } from '../../data/memory';
import { ENEMIES } from '../../data';
import { assetListed } from '../../systems/sprites/sheetLoader';
import { queueImageOnce } from '../../systems/sprites/imageOnce';
import { RELIC_ICON_DIR, relicIconFile, relicIconKey } from '../../systems/relics';
import { keepsakeIconKey } from '../../systems/memory/memory';
import { TRAIT_ICON_DIR, markIconLoaded, traitIconFile, traitIconKey } from '../../systems/growth/traitArt';

const PORTRAIT_DIR = `${ASSETS.SPRITES_DIR}/ui_portraits`;
/** 군주 초상 파일 id (층 → 파일) */
export const BOSS_PORTRAIT: Readonly<Record<string, string>> = { stage1: 'boss1' };

export function portraitKey(id: string): string {
  return `ui_portraits/${id}`;
}

/** 기억 장 그림 — 소품 `ui_relics/keepsake_<id>` · (memoryTraits) 모양·떠올릴 개성 칸의 대체 그림 = 그 개성 카드 그림 */
function memoryWanted(memoryTraits: boolean): { key: string; rel: string }[] {
  const out: { key: string; rel: string }[] = [];
  if (memoryTraits)
    for (const m of MEMORY.items)
      for (const t of m.kind === 'aspect' ? [m.trait] : m.kind === 'pool' ? (m.traits ?? []).slice(0, 1) : [])
        if (t && m.weapon)
          out.push({ key: traitIconKey(m.weapon, t), rel: `${TRAIT_ICON_DIR}/${traitIconFile(m.weapon, t)}` });
  for (const m of MEMORY.items)
    if (m.kind === 'keepsake') out.push({ key: keepsakeIconKey(m.id), rel: `${RELIC_ICON_DIR}/keepsake_${m.id}.png` });
  return out;
}

function wanted(memoryTraits: boolean): { key: string; rel: string }[] {
  const out = memoryWanted(memoryTraits);
  for (const r of RELICS.items) out.push({ key: relicIconKey(r.id), rel: `${RELIC_ICON_DIR}/${relicIconFile(r.id)}` });
  for (const id of [...Object.keys(ENEMIES), ...Object.values(BOSS_PORTRAIT)])
    out.push({ key: portraitKey(id), rel: `${PORTRAIT_DIR}/${id}.png` });
  return out;
}

/** 매니페스트에 있는(또는 이미 있는) 것만 큐에 — 새로 넣었으면 true */
function queueAll(scene: Phaser.Scene, list: readonly { key: string; rel: string }[]): boolean {
  let queued = false;
  for (const w of list) {
    if (!scene.textures.exists(w.key) && !assetListed(w.rel)) continue;
    // 62 루프 2 F: 씬 사이 한 번만 — 노드 이동(씬 재시작) 중 받던 그림을 새 씬이 다시 넣어 'key already in use' 가 나던 것
    if (queueImageOnce(scene, w.key, `${ASSETS.URL}/${w.rel}`, () => markIconLoaded(w.key))) queued = true;
  }
  return queued;
}

/** 유품·소품·초상 그림(+ memoryTraits = 기억 장 개성 그림)을 (매니페스트에 있으면) 받아 둔다. 작은 정지 그림 — 씬 시작에 한 번 */
export function loadRunEndArt(scene: Phaser.Scene, opts: { memoryTraits?: boolean } = {}): void {
  if (queueAll(scene, wanted(Boolean(opts.memoryTraits))) && !scene.load.isLoading()) scene.load.start();
}

/**
 * 62 루프 2 G (UI 요청): 기억 장 그림(소품 4 · 모양·떠올릴 개성 8 — 128px 정지 그림)을 **부팅 로더에** 넣는다.
 * 타이틀(UI 씬)·결과 화면에서 일기장 기억 장을 열 때 `UiMemoryEntry.iconKey` 가 비어 글자로 대체되던 것 — 텍스처는 씬과 무관하게
 * 남으므로 Preloader 에서 한 번 받으면 의식·결과·타이틀 모두 채워진다. 호출한 쪽(Preloader)이 load.start 를 챙긴다
 */
export function queueMemoryArt(scene: Phaser.Scene): boolean {
  return queueAll(scene, memoryWanted(true));
}
