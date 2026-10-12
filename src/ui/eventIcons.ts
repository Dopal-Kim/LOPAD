import Phaser from 'phaser';
import type { UiEventIcon } from '../contract/ui';
import { eventIconArt, eventIconText } from './eventView';
import { GlowText } from './glow';
import { KIT, ensureImage } from './kit';
import type { TextStyleName } from './theme';
import { EVENT_ICON_SHEET as SHEET } from './themeLoop2F';

/**
 * 62 루프 2 UI F: 사연·장터 아이콘 (계약 D `UiEventIcon`) — 키트 icons.png(전표·독주·체력) + UI F 시트 event_icons.png(나머지 8종).
 * 시트는 처음 쓸 때 읽는다(HUD 가 만들어질 때 미리 부른다). 아직 안 읽혔으면 그림 없이 글만.
 */

/** 시트를 읽고 프레임 이름을 단다 (여러 번 불러도 한 번만) */
export function ensureEventIcons(scene: Phaser.Scene, done?: (ok: boolean) => void): void {
  ensureImage(scene, SHEET.key, SHEET.url, (ok) => {
    if (ok) addFrames(scene);
    done?.(ok);
  });
}

function addFrames(scene: Phaser.Scene): void {
  if (!scene.textures.exists(SHEET.key)) return;
  const tex = scene.textures.get(SHEET.key);
  SHEET.order.forEach((name, i) => {
    if (!tex.has(name)) tex.add(name, 0, i * SHEET.size, 0, SHEET.size, SHEET.size);
  });
}

/** 아이콘 그림 하나 (왼쪽 위 기준, 16×16). 그림이 아직 없으면 null */
export function eventIconImage(
  scene: Phaser.Scene,
  icon: Pick<UiEventIcon, 'kind' | 'hidden'>,
  x: number,
  y: number,
): Phaser.GameObjects.Image | null {
  const art = eventIconArt(icon);
  const key = art.sheet === 'kit' ? KIT.icons : SHEET.key;
  if (!scene.textures.exists(key)) return null;
  if (art.sheet === 'event') addFrames(scene);
  const tex = scene.textures.get(key);
  if (!tex.has(art.frame)) return null;
  return scene.add.image(x, y, key, art.frame).setOrigin(0, 0);
}

export interface IconListOpts {
  style?: TextStyleName;
  stageIndex?: number;
  /** 'col' = 아이콘마다 한 줄 (표 칸) · 'row' = 한 줄에 이어서 */
  layout?: 'col' | 'row';
  lineH?: number;
  /** row 에서 아이콘 사이 */
  gap?: number;
  /** 글 줄바꿈 폭 (col) */
  wrap?: number;
}

/**
 * 아이콘 줄 (컨테이너 지역 좌표 0,0 = 왼쪽 위). 아이콘 16 + 2 + 글. 숨은 보상은 '?' 그림만.
 * 반환 = 컨테이너와 그린 폭·높이 (아이콘이 없으면 0×0)
 */
export function iconList(
  scene: Phaser.Scene,
  icons: readonly UiEventIcon[],
  opts: IconListOpts = {},
): { box: Phaser.GameObjects.Container; w: number; h: number } {
  const style = opts.style ?? 'page_body';
  const lineH = opts.lineH ?? 18;
  const gap = opts.gap ?? 10;
  const box = scene.add.container(0, 0);
  let x = 0;
  let y = 0;
  let w = 0;
  for (const ic of icons) {
    const img = eventIconImage(scene, ic, x, y + Math.max(0, Math.round((lineH - 16) / 2) - 1));
    const text = eventIconText(ic);
    let cx = x;
    if (img) {
      box.add(img);
      cx += 16 + 2;
    }
    let th = lineH;
    if (text || !img) {
      const t = new GlowText(scene, cx, y + 1, text || '?', style, {
        stageIndex: opts.stageIndex ?? 0,
        wrap: opts.layout === 'row' ? undefined : opts.wrap,
      });
      box.add(t);
      cx += t.displayWidth;
      th = Math.max(lineH, t.displayHeight + 2);
    }
    w = Math.max(w, cx);
    if (opts.layout === 'row') {
      x = cx + gap;
    } else {
      y += th;
    }
  }
  const h = icons.length === 0 ? 0 : opts.layout === 'row' ? lineH : y;
  return { box, w: opts.layout === 'row' ? Math.max(0, x - gap) : w, h };
}
