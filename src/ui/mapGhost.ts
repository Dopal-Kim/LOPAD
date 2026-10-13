import Phaser from 'phaser';
import { SEPIA, hexToNum } from './theme';
import { RESULT_UI as R } from './themeLoop2E';

/**
 * 지도 표식 '먹 붓 망령' (아트 §31-9 `sprites/ui/map_marker_ghost` 40×56 × 6, 160ms 반복, 피벗 (20,53), UI 1배).
 * 62 루프 2 UI E 결산 미니맵에서 쓰던 로드·애니 방식을 62 루프 3 UI H 노드 지도(고르기·M 보기)와 함께 쓴다.
 * 먹 망령은 어두운 종이 위에서 묻히므로 발밑부터 몸까지 옅은 종이빛 번짐을 깐다.
 */
export const MAP_GHOST = R.ghost;

/** 보이는 몸 상자 (6칸 합친 불투명 영역, 피벗 기준) — 이름표·미리보기 카드가 피할 자리 */
export const GHOST_BODY = { left: -12, right: 13, top: -50, bottom: 1 } as const;

export function preloadMapGhost(scene: Phaser.Scene): void {
  const G = MAP_GHOST;
  if (!scene.textures.exists(G.key)) scene.load.spritesheet(G.key, G.url, { frameWidth: G.w, frameHeight: G.h });
}

/** 텍스처가 있으면 반복 애니를 만들어 두고 true */
export function ensureGhostAnim(scene: Phaser.Scene): boolean {
  const G = MAP_GHOST;
  if (!scene.textures.exists(G.key)) return false;
  if (!scene.anims.exists(G.key))
    scene.anims.create({
      key: G.key,
      frames: scene.anims.generateFrameNumbers(G.key, { start: 0, end: G.frames - 1 }),
      frameRate: 1000 / G.ms,
      repeat: -1,
    });
  return true;
}

/** 발(피벗)을 (x, y) 에 둔 망령 + 종이빛 번짐. 텍스처가 없으면 null (부르는 쪽이 대체 표식) */
export function addMapGhost(scene: Phaser.Scene, x: number, y: number): Phaser.GameObjects.GameObject[] | null {
  if (!ensureGhostAnim(scene)) return null;
  const G = MAP_GHOST;
  const halo = scene.add.graphics();
  halo.fillStyle(hexToNum(SEPIA[5]), 0.18).fillEllipse(x, y - 24, 34, 50);
  halo.fillStyle(hexToNum(SEPIA[5]), 0.22).fillEllipse(x, y - 22, 22, 36);
  const s = scene.add.sprite(Math.round(x), Math.round(y), G.key, 0).setOrigin(G.pivotX / G.w, G.pivotY / G.h);
  s.play(G.key);
  return [halo, s];
}
