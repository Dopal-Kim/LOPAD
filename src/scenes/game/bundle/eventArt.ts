/**
 * 62 루프 2 시스템 D (P1-12 · art §31.7) 사연 결과 컷 그림 지연 로드: `sprites/events/cut_<eventId>.png` (320×180, UI 1배) +
 * 별칭 표 `sprites/events/cuts.json aliases` (`cut_<이벤트>_<선택지>` → 이벤트 컷). 텍스처 키 = `events/<파일 이름>`.
 * 사연 노드에 들어설 때 그 사연 컷 한 장만 받는다. 계약 `UiEventResult.cutKey` 는 로드된 텍스처 키(없으면 생략).
 */
import type Phaser from 'phaser';
import { ASSETS } from '../../../core/Constants';
import { assetListed } from '../../../systems/sprites/sheetLoader';
import { queueImageOnce } from '../../../systems/sprites/imageOnce';

const DIR = 'sprites/events';
const INDEX = 'events/cuts';
const keyOf = (name: string) => `events/${name}`;

/** 사연 컷(+ 별칭 표)을 받아 둔다 — 없는 파일은 매니페스트가 거른다 */
export function loadEventCut(scene: Phaser.Scene, eventId: string): void {
  let queued = false;
  if (!scene.cache.json.exists(INDEX) && assetListed(`${DIR}/cuts.json`)) {
    scene.load.json(INDEX, `${ASSETS.URL}/${DIR}/cuts.json`);
    queued = true;
  }
  const name = `cut_${eventId}`;
  if (assetListed(`${DIR}/${name}.png`) && queueImageOnce(scene, keyOf(name), `${ASSETS.URL}/${DIR}/${name}.png`))
    queued = true;
  if (queued && !scene.load.isLoading()) scene.load.start();
}

/** 선택지 결과 컷 텍스처 키 (별칭 → 이벤트 컷 → 없음) */
export function eventCutKey(scene: Phaser.Scene, eventId: string, option: string): string | undefined {
  const index = scene.cache.json.get(INDEX) as { aliases?: Record<string, string> } | undefined;
  const alias = index?.aliases?.[`cut_${eventId}_${option}`];
  for (const n of [alias, `cut_${eventId}_${option}`, `cut_${eventId}`])
    if (n && scene.textures.exists(keyOf(n))) return keyOf(n);
  return undefined;
}
