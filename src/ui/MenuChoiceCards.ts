import Phaser from 'phaser';
import type { UiBuildState, UiMenu } from '../contract/ui';
import { choiceCards, choiceHint, type ChoiceCardData } from './choiceCardView';
import { GlowText } from './glow';
import { cardPage, cardShell, type ShellSlot } from './cardShell';
import { diamond } from './growthArt';
import { KIT } from './kit';
import type { CardPage, CardPageCtx } from './MenuCards';
import { swatch } from './StructureHud';
import { r60Text } from './text';
import { SEPIA, hexToNum } from './theme';
import { CHOICE_CARD } from './themeBuild';

/** 줄 사이 */
const GAP = { afterTab: 10, afterName: 6, afterPips: 4, afterMeta: 8, afterRule: 10, beforeBottom: 8 } as const;

/** 카드 한 장의 글 (재고 놓기 전) */
interface Face {
  data: ChoiceCardData;
  name: GlowText;
  meta: GlowText | null;
  detail: GlowText | null;
  bottom: GlowText | null;
}

/**
 * 60라운드 Q38 보상·패시브(·성장 칸이 아닌 evolve) 3지선다 = 카드 3장 (61 단계 4 P12 성장 카드는 GrowthCards.ts). 일기장 한 페이지(제목·괘선·footer) 위에 잉크 탁자 깔개(panel_ink)를 펴고
 * 종이 카드(panel_paper + paper_tile) 3장을 나란히 놓는다 — 패 탁자 분위기, 키트만 사용.
 * 카드: 위 가운데 머리표 탭(잉크 + 종류 띠 색, 〔보상〕·〔패시브〕 …) · 왼쪽 위 키 [1] · 이름(2배) ·
 * 희귀도 마름모 · 희귀도·태그 · 괘선 · 설명 · 아래 잠김 조건(자물쇠)·못 고르는 까닭.
 * 고름 자리 = 카드가 들리고(그림자 멀어짐) 층 강조 테 2px, 이름 page_selected. 못 고르는 카드는 흐림, 고르면 좌우로 흔들림.
 * 조작은 CardRow(1·2·3 / ←→ / Enter / 마우스, 그만두기 줄이 있으면 ↓·키·Esc). 페이지가 화면을 넘으면 null(목록으로 그린다).
 */
export function showChoiceCards(
  scene: Phaser.Scene,
  m: UiMenu,
  build: UiBuildState | null | undefined,
  ctx: CardPageCtx,
  maxPageH: number,
): CardPage | null {
  const C = CHOICE_CARD;
  const { stageIndex } = ctx;
  const data = choiceCards(m, build, r60Text);
  const n = data.length;
  const cw = C.w;
  const innerW = cw - C.pad * 2;
  const rowW = n * cw + (n - 1) * C.gap;
  const matW = rowW + C.matPad * 2;

  // ---- 글을 먼저 만들어 높이를 잰다
  const faces: Face[] = data.map((d) => ({
    data: d,
    name: new GlowText(scene, 0, 0, d.name, 'page_unsel', {
      scale: C.nameScale,
      wrap: Math.floor(innerW / C.nameScale),
      align: 'center',
      stageIndex,
    }),
    meta: d.meta ? new GlowText(scene, 0, 0, d.meta, 'page_faint', { wrap: innerW, align: 'center' }) : null,
    detail: d.detail
      ? new GlowText(scene, 0, 0, d.detail, 'page_body', { wrap: innerW, align: 'center', stageIndex })
      : null,
    bottom:
      d.locked || d.note
        ? new GlowText(scene, 0, 0, d.locked || d.note, 'page_faint', { wrap: innerW - 12, align: 'center' })
        : null,
  }));
  const max = (f: (x: Face) => number) => Math.max(0, ...faces.map(f));
  const nameH = max((f) => f.name.displayHeight);
  const pipsH = faces.some((f) => f.data.rarityRank > 0) ? C.pipR * 2 + 1 + GAP.afterPips : 0;
  const metaH = max((f) => (f.meta ? f.meta.displayHeight : 0));
  const detailH = max((f) => (f.detail ? f.detail.displayHeight : 0));
  const bottomH = max((f) => (f.bottom ? f.bottom.displayHeight : 0));
  // 이름·괘선·설명 줄을 세 장이 같은 높이에 두도록 칸마다 가장 큰 값으로
  const ruleY = C.tabTop + C.tabH + GAP.afterTab + nameH + GAP.afterName + pipsH + metaH + GAP.afterMeta;
  const detailY = ruleY + 4 + GAP.afterRule;
  const ch = Math.max(C.minH, detailY + detailH + (bottomH ? GAP.beforeBottom + bottomH : 0) + C.pad);

  const matH = ch + C.matPad * 2;
  const page = cardPage(scene, m, ctx, { w: matW, h: matH, pad: C.matPad }, choiceHint(m, r60Text), maxPageH);
  if (!page) return null;
  const slots: ShellSlot[] = faces.map((f, i) =>
    buildCard(scene, f, page.left + i * (cw + C.gap), page.top, ch, { ruleY, detailY, nameH, pipsH }),
  );
  return page.done(slots);
}

/**
 * 카드 한 장: 껍데기(cardShell — 그림자 · 종이 · 머리표 탭 · 키 · 고름 테) 안에 이름(2배) · 희귀도 마름모 · 희귀도·태그 · 괘선 ·
 * 설명 → 아래 잠김 글·자물쇠(바깥, 흐리지 않음). 못 고르는 카드는 들리지 않는다.
 */
function buildCard(
  scene: Phaser.Scene,
  f: Face,
  x: number,
  y: number,
  ch: number,
  rows: { ruleY: number; detailY: number; nameH: number; pipsH: number },
): ShellSlot {
  const C = CHOICE_CARD;
  const cw = C.w;
  const d = f.data;
  const marks = scene.add.graphics();
  let ny = C.tabTop + C.tabH + GAP.afterTab;
  f.name.placeCenter(cw / 2, ny + Math.round((rows.nameH - f.name.displayHeight) / 2));
  ny += rows.nameH + GAP.afterName;
  // 희귀도 마름모 (찬 칸 = 희귀도, 전설은 밝은 슬롯)
  if (d.rarityRank > 0) {
    const r = C.pipR;
    const step = r * 2 + C.pipGap;
    const total = C.rarityMax * step - C.pipGap;
    const px0 = Math.round(cw / 2 - total / 2) + r;
    const full = swatch(scene, 0, { slot: d.rarityRank >= C.rarityMax ? C.rarityTopSlot : C.raritySlot });
    for (let k = 0; k < C.rarityMax; k++)
      diamond(marks, px0 + k * step, ny + r, r, k < d.rarityRank ? full : hexToNum(SEPIA[4]), k < d.rarityRank);
  }
  ny += rows.pipsH;
  f.meta?.placeCenter(cw / 2, ny);
  const ruleLine = scene.add.tileSprite(C.pad, rows.ruleY, cw - C.pad * 2, 4, KIT.rule).setOrigin(0, 0);
  f.detail?.placeCenter(cw / 2, rows.detailY);
  const parts: Phaser.GameObjects.GameObject[] = [marks, f.name, ruleLine];
  if (f.meta) parts.push(f.meta);
  if (f.detail) parts.push(f.detail);
  const slot = cardShell(
    scene,
    C,
    x,
    y,
    cw,
    ch,
    {
      key: d.key,
      hotkey: d.hotkey,
      enabled: d.enabled,
      head: d.head,
      headSlot: d.headSlot,
      onPaint: (sel) => f.name.setGlowStyle(!d.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel'),
    },
    parts,
  );
  // 아래 잠김 조건·못 고르는 까닭 (카드 흐림과 별개로 읽히게 바깥에)
  const lock = scene.add.graphics().setDepth(3);
  if (f.bottom) {
    const by = y + ch - C.pad - f.bottom.displayHeight;
    const lockW = d.locked ? 12 : 0;
    f.bottom.setDepth(3).placeCenter(x + cw / 2 + lockW / 2, by);
    if (d.locked) drawPadlock(lock, f.bottom.x - lockW, by + 3, hexToNum(SEPIA[5]));
  }
  return slot;
}

/** 작은 자물쇠 (몸통 7×5 + 고리 5×4 테), 왼쪽 위 (x,y) */
function drawPadlock(g: Phaser.GameObjects.Graphics, x: number, y: number, color: number): void {
  g.fillStyle(color, 1).fillRect(x, y + 4, 7, 5);
  g.lineStyle(1, color, 1).strokeRect(x + 1.5, y + 0.5, 4, 4);
}
