import Phaser from 'phaser';
import { GlowText } from './glow';
import { traitIconBox } from './growthArt';
import { GRAY, SEPIA, hexToNum } from './theme';

/**
 * 62 루프 2 UI E: 카드 줄 아래 '상세 칸' (계약 C — 유품·기억 카드의 수치는 카드 앞면에 그리지 않고 상세 보기에서만).
 * 탁자 깔개(잉크) 안 카드 아래 한 칸에 고름 자리 카드의 수치 한 줄(ink_body) + 흐린 한 줄(ink_faint)을 가운데로 적는다.
 * 고름 자리가 바뀔 때(카드 `onPaint(true)`) `show` — 입력은 받지 않는다(그리기만).
 */
export const CARD_ZOOM = {
  /** 칸 높이 (수치 한 줄 + 흐린 한 줄) */
  h: 36,
  /** 카드 아래와의 틈 */
  gap: 6,
  /** 카드 그림 칸 (아트 128×128 → 64, 무기 빛 테 대신 세피아 테) */
  icon: 64,
  iconFrame: 2,
  iconGap: 6,
} as const;

export interface CardZoom {
  show(z: { detail: string; flavor: string } | undefined): void;
}

/** (cx, y) = 칸 위 가운데, w = 줄바꿈 폭 */
export function cardZoom(scene: Phaser.Scene, cx: number, y: number, w: number, depth = 3): CardZoom {
  const detail = new GlowText(scene, 0, y, '', 'ink_body', { wrap: w, align: 'center' }).setDepth(depth);
  const flavor = new GlowText(scene, 0, y, '', 'ink_faint', { wrap: w, align: 'center' }).setDepth(depth);
  let sig = '';
  return {
    show(z) {
      const next = z ? `${z.detail}\u0001${z.flavor}` : '';
      if (next === sig) return;
      sig = next;
      detail.setText(z?.detail ?? '').placeCenter(cx, y);
      const fy = y + (z?.detail ? detail.displayHeight + 2 : 0);
      flavor.setText(z?.flavor ?? '').placeCenter(cx, fy);
    },
  };
}

/** 카드 그림 칸 바깥 높이 (테 포함 + 아래 틈) */
export function cardIconH(): number {
  return CARD_ZOOM.icon + (CARD_ZOOM.iconFrame + 1) * 2 + CARD_ZOOM.iconGap;
}

/**
 * 카드 그림 (카드 지역 좌표, (cx, y) = 그림 칸 위 가운데 — 테 바깥 포함). 텍스처가 없으면 null.
 * `size` 기본 64 — 64×64 소품 그림은 1배, 128×128 유품·개성 그림은 1/2 (도트가 정수 배로 줄어든다).
 */
export function cardIcon(
  scene: Phaser.Scene,
  key: string | null | undefined,
  cx: number,
  y: number,
  frameColor = hexToNum(SEPIA[5]),
): Phaser.GameObjects.GameObject[] | null {
  const Z = CARD_ZOOM;
  const o = Z.iconFrame + 1;
  return traitIconBox(
    scene,
    key,
    Math.round(cx - Z.icon / 2),
    y + o,
    Z.icon,
    frameColor,
    Z.iconFrame,
    hexToNum(GRAY[1]),
  );
}
