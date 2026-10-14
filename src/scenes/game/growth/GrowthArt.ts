/**
 * 무기 성장 정지 그림 로드 (씬 쪽 — 61 G GrowthFlow 에서 분리, 61 단계 5 개성 카드 그림 추가):
 * - art §26 미리보기 `sprites/looks/<무기>_base·<무기>_<갈래>_a1·<무기>_<갈래>_a2_<길>.png` → 키 `growth_look_<파일 이름>`
 * - art §27·UI §18.1 개성 카드 그림 `sprites/ui_traits/<무기>_<개성 id>.png` → 키 `ui_traits/<무기>_<개성 id>`
 * 매니페스트에 있는 이 무기 것만 씬 시작에 받는다. 키 조회는 로드돼 있을 때만 값(없으면 undefined — UI 는 키캡으로).
 */
import type Phaser from 'phaser';
import { ASSETS } from '../../../core/Constants';
import { GROWTH, TRAITS } from '../../../data/growth';
import {
  TRAIT_ICON_DIR,
  markIconLoaded,
  resonanceIconFile,
  resonanceIconKey,
  traitIconFile,
  traitIconCandidates,
  traitIconKey,
} from '../../../systems/growth/traitArt';
import { resonancesOf } from '../../../systems/growth/resonance';
import { assetListed } from '../../../systems/sprites/sheetLoader';
import { queueImageOnce } from '../../../systems/sprites/imageOnce';

/** art §26 미리보기 파일: `<무기>_base` · `<무기>_<갈래>_a1` · `<무기>_<갈래>_a2_<길>`(길 색을 구운 완성 그림) */
function lookFile(weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string): string {
  if (!branch || stage === 0) return `${weapon}_base.png`;
  return stage === 2 && path ? `${weapon}_${branch}_a2_${path}.png` : `${weapon}_${branch}_a${stage}.png`;
}

const lookTexture = (file: string) => `growth_look_${file.replace('.png', '')}`;

/**
 * 62 계약 UI §20 운명 공개: 무기 기본 미리보기(`looks/<무기>_base`)를 받아 둔다 — 이미 있거나 매니페스트에 없으면 바로 done.
 * done(key) = 로드된 텍스처 키 (없으면 undefined)
 */
export function loadBaseLook(scene: Phaser.Scene, weapon: string, done: (key: string | undefined) => void): void {
  const file = lookFile(weapon, null, 0);
  const key = lookTexture(file);
  const rel = `${ASSETS.LOOKS_DIR}/${file}`;
  let called = false;
  const ready = () => {
    if (called) return;
    called = true;
    done(scene.textures.exists(key) ? key : undefined);
  };
  if (scene.textures.exists(key) || !assetListed(rel)) return ready();
  // 62 루프 2 F: 다른 씬이 받는 중이면 다시 넣지 않고 들어오는 순간을 기다린다 (imageOnce)
  if (!queueImageOnce(scene, key, `${ASSETS.URL}/${rel}`, ready)) return;
  scene.load.once('complete', ready);
  if (!scene.load.isLoading()) scene.load.start();
}

export class GrowthArt {
  constructor(private readonly scene: Phaser.Scene) {}

  /** 로드된 미리보기 텍스처 키 (없으면 undefined) */
  lookKey(weapon: string, branch: string | null, stage: 0 | 1 | 2, path?: string): string | undefined {
    const key = lookTexture(lookFile(weapon, branch, stage, path));
    return this.scene.textures.exists(key) ? key : undefined;
  }

  /** 로드된 개성 카드 그림 키 (없으면 같은 태그 개성 그림 — 62 루프 4, 그것도 없으면 undefined) */
  iconKey(weapon: string, traitId: string): string | undefined {
    return traitIconCandidates(weapon, traitId).find((key) => this.scene.textures.exists(key));
  }

  /** 씬 시작 — 이 무기의 미리보기(기본·갈래 3·길 6)와 개성 카드 그림 14장을 (매니페스트에 있으면) 받아 둔다 */
  load(weapon: string): void {
    const want: { key: string; rel: string }[] = [];
    const files = [lookFile(weapon, null, 0)];
    for (const b of GROWTH.weapons[weapon]?.branches ?? []) {
      files.push(lookFile(weapon, b.id, 1));
      for (const p of b.paths) files.push(lookFile(weapon, b.id, 2, p.id));
    }
    for (const f of files) want.push({ key: lookTexture(f), rel: `${ASSETS.LOOKS_DIR}/${f}` });
    for (const t of TRAITS)
      if (t.weapon === weapon)
        want.push({ key: traitIconKey(weapon, t.id), rel: `${TRAIT_ICON_DIR}/${traitIconFile(weapon, t.id)}` });
    for (const r of resonancesOf(weapon))
      want.push({ key: resonanceIconKey(r.id), rel: `${TRAIT_ICON_DIR}/${resonanceIconFile(r.id)}` });
    const s = this.scene;
    let queued = false;
    for (const w of want) {
      if (!s.textures.exists(w.key) && !assetListed(w.rel)) continue;
      // 62 루프 2 F: 씬 사이 한 번만 (imageOnce — 이미 있으면 바로 표시)
      if (queueImageOnce(s, w.key, `${ASSETS.URL}/${w.rel}`, () => markIconLoaded(w.key))) queued = true;
    }
    if (queued && !s.load.isLoading()) s.load.start();
  }
}
