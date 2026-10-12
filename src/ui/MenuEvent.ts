import Phaser from 'phaser';
import { UI_SCREEN, type UiMenu } from '../contract/ui';
import { armBar } from './choiceArm';
import { debugExpose } from './debug';
import { ensureEventIcons, iconList } from './eventIcons';
import { eventPage, greetText, listFocusMove, portraitFit, type EventPage, type EventRow } from './eventView';
import { GlowText } from './glow';
import { accentHex, book, cursor as makeCursor, rule } from './kit';
import { CardRow, menuCloseButton, type CardPage, type CardPageCtx, type CardSlot } from './MenuCards';
import { LAYOUT, SEPIA, hexToNum } from './theme';
import { EVENT_PAGE as P } from './themeLoop2F';
import { playUiSound } from './uiSound';

/**
 * 62 루프 2 UI F (계약 D P1-12·13): 사연 메뉴(`event` + `UiMenu.event`) · 종군 상인과 말하기(`shopTalk`) — 일기장 한 쪽.
 *  위: 제목(2배) · 괘선 · [말하는 이 초상] 이름 / 첫 마디(말이면 「」) / 설명 문단 (읽는 글 — 글자 크기 설정 따름)
 *  아래: '하나를 고른다 · 내준다 · 얻는다' 머리 · 선택지 표 (줄마다 [키] 이름 | 대가 아이콘 | 보상 아이콘, 숨은 보상은 '?')
 *  아이콘을 그린 줄은 detail 글을 숨긴다(못 고르는 까닭만 흐리게). 상인 줄의 값은 대가 칸 전표 아이콘으로.
 * 고르기는 CardRow(무장 게이트 · 눌렀다 뗀 클릭만 · ↑↓ 세로 이동) — 그만두기 줄('0' 지나간다)도 표의 한 줄이다.
 * 쪽이 화면에 들지 않으면 null (MenuScene 이 목록으로 그린다).
 */
export function showEventPage(scene: Phaser.Scene, m: UiMenu, ctx: CardPageCtx, maxH: number): CardPage | null {
  ensureEventIcons(scene);
  const page = eventPage(m);
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const si = ctx.stageIndex;
  // 62 루프 2 시스템 F: 렌더러 메뉴는 시스템이 메뉴 소리를 내지 않는다 — 이동·고르기·뒤로는 UI 소리(uiSound).
  // 사연 고르기는 시스템이 늘 event_choice 를 내므로 ui_select 는 생략 (그만두기 줄은 ui_back)
  const send = (key: string): void => {
    if (key === m.cancelKey) playUiSound(scene, 'back');
    else if (m.id !== 'event') playUiSound(scene, 'select');
    ctx.send(key);
  };
  let lastSel = -1;
  const pad = P.pad;
  const made: Phaser.GameObjects.GameObject[] = [];
  const keep = <T extends Phaser.GameObjects.GameObject>(o: T): T => {
    made.push(o);
    return o;
  };

  // ---- 글을 먼저 만들어 폭·높이를 잰다 (쪽은 그 뒤에 깐다 — depth 0)
  const title = keep(new GlowText(scene, 0, 0, page.title, 'page_title', { scale: 2, stageIndex: si }).setDepth(1));
  const close = m.cancelKey ? menuCloseButton(scene, si, () => send(m.cancelKey!)) : null;
  if (close) made.push(close);
  const rows = page.rows.map((r) => rowParts(scene, r, si, P.labelColMin));
  rows.forEach((r) => made.push(r.box));
  const labelCol = Math.max(P.labelColMin, ...rows.map((r) => r.labelW + 8));
  const iconCols = page.hasIcons ? 2 * (P.iconCol + P.colGap) : 0;
  const closeRoom = close ? (close.width + 8) * 2 : 0;
  const pageW = Math.min(P.maxW, Math.max(P.minW, labelCol + iconCols + 16 + pad * 2, title.displayWidth + closeRoom));
  const innerW = pageW - pad * 2;
  const iconColW = page.hasIcons ? Math.floor((innerW - 16 - labelCol) / 2) - P.colGap : 0;

  const portraitTex = portraitReady(scene, page);
  const textX = portraitTex ? P.portraitW + P.portraitGap : 0;
  const textW = innerW - textX;
  const head: GlowText[] = [];
  if (page.speaker) head.push(new GlowText(scene, 0, 0, page.speaker, 'page_faint', { stageIndex: si }));
  const greet = greetText(page);
  if (greet)
    head.push(
      new GlowText(scene, 0, 0, greet, page.greetKind === 'speech' ? 'page_selected' : 'page_unsel', {
        wrap: textW,
        stageIndex: si,
        readable: true,
      }),
    );
  for (const para of page.intro)
    head.push(new GlowText(scene, 0, 0, para, 'page_body', { wrap: textW, stageIndex: si, readable: true }));
  for (const ex of page.extra) head.push(new GlowText(scene, 0, 0, ex, 'page_faint', { wrap: textW }));
  head.forEach((t) => keep(t.setDepth(1)));
  const headTextH = head.reduce((h, t, i) => h + t.displayHeight + (i > 0 ? P.paraGap : 0), 0);
  const headH = Math.max(portraitTex ? P.portraitH : 0, headTextH);

  const pickT = keep(new GlowText(scene, 0, 0, page.pick, 'page_faint').setDepth(1));
  const costT = page.hasIcons ? keep(new GlowText(scene, 0, 0, page.costHead, 'page_faint').setDepth(1)) : null;
  const gainT = page.hasIcons ? keep(new GlowText(scene, 0, 0, page.gainHead, 'page_faint').setDepth(1)) : null;
  const hint = keep(new GlowText(scene, 0, 0, page.hint, 'page_faint', { wrap: innerW, align: 'center' }).setDepth(1));
  // 아이콘 칸 (폭이 정해진 뒤)
  rows.forEach((r, i) => r.fillIcons(page.rows[i], iconColW));
  const rowsH = rows.reduce((h, r) => h + r.h, 0);

  const titleH = title.displayHeight;
  const pageH =
    16 +
    titleH +
    8 +
    4 +
    12 +
    headH +
    12 +
    4 +
    8 +
    pickT.displayHeight +
    P.headGap +
    rowsH +
    8 +
    hint.displayHeight +
    14;
  if (pageH > maxH) {
    for (const o of made) o.destroy();
    debugExpose('eventPage', { id: m.id, drawn: false, pageH, maxH });
    return null;
  }

  // ---- 쪽
  const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
  const pg = bk.pages[0];
  const x0 = pg.x + pad;
  let y = pg.y + 16;
  title.placeCenter(pg.x + pageW / 2, y);
  close?.setPosition(pg.x + pageW - 12 - close.width, pg.y + 12);
  y += titleH + 8;
  rule(scene, x0, y, innerW).setDepth(1);
  if (ctx.gate && !ctx.gate.armed(performance.now()))
    armBar(scene, ctx.gate, x0, y + 1, innerW, hexToNum(accentHex(scene, si, 20)), 2);
  y += 4 + 12;

  // 말하는 이 · 첫 마디 · 설명
  if (portraitTex) portrait(scene, page, x0, y, si);
  let hy = y;
  head.forEach((t, i) => {
    if (i > 0) hy += P.paraGap;
    t.setPosition(x0 + textX, hy);
    hy += t.displayHeight;
  });
  y += headH + 12;
  rule(scene, x0, y, innerW, false).setDepth(1).setAlpha(0.6);
  y += 4 + 8;

  // 머리 줄
  const costX = x0 + 16 + labelCol + P.colGap;
  const gainX = costX + iconColW + P.colGap;
  pickT.setPosition(x0 + 16, y);
  costT?.setPosition(costX, y);
  gainT?.setPosition(gainX, y);
  y += pickT.displayHeight + P.headGap;

  // 선택지 표
  const cur = makeCursor(scene).setDepth(3).setVisible(false);
  const slots: CardSlot[] = [];
  const hovers: (() => void)[] = [];
  const presses: ((p: Phaser.Input.Pointer) => void)[] = [];
  const releases: ((p: Phaser.Input.Pointer) => void)[] = [];
  rows.forEach((r, i) => {
    const rowY = y;
    r.place(x0, rowY, innerW, costX - x0, gainX - x0);
    r.box.setInteractive(new Phaser.Geom.Rectangle(innerW / 2, r.h / 2, innerW, r.h), Phaser.Geom.Rectangle.Contains);
    if (r.box.input) r.box.input.cursor = page.rows[i].enabled ? 'pointer' : 'default';
    r.box.on('pointerover', () => hovers[i]());
    r.box.on('pointerdown', (p: Phaser.Input.Pointer) => presses[i](p));
    r.box.on('pointerup', (p: Phaser.Input.Pointer) => releases[i](p));
    slots.push({
      key: page.rows[i].key,
      hotkey: page.rows[i].hotkey,
      enabled: page.rows[i].enabled,
      paint: (sel) => {
        r.paint(sel, innerW);
        if (sel && lastSel !== i) {
          if (lastSel >= 0) playUiSound(scene, 'move');
          lastSel = i;
        }
        if (sel) cur.setVisible(true).setPosition(x0 + 6, rowY + P.rowPadY + 8);
      },
      reject: () => r.shake(),
    });
    y += r.h;
  });
  y += 8;
  hint.placeCenter(pg.x + pageW / 2, y);

  const row = new CardRow(scene, slots, null, send, ctx.keepCursor, ctx.gate, listFocusMove);
  slots.forEach((_, i) => {
    hovers[i] = () => row.hover(i);
    presses[i] = (p) => row.press(i, p);
    releases[i] = (p) => row.release(i, p);
  });
  debugExpose('eventPage', {
    id: m.id,
    drawn: true,
    title: page.title,
    speaker: page.speaker,
    portrait: Boolean(portraitTex),
    rows: page.rows.map((r) => ({
      key: r.key,
      hotkey: r.hotkey,
      costs: r.costs.length,
      rewards: r.rewards.length,
      note: r.note,
    })),
    rowY: rows.map((r) => Math.round(r.box.y)),
    page: { x: pg.x, y: pg.y, w: pageW, h: pageH },
  });
  return { row, bottom: { x: pg.x + pageW / 2, y: pg.y + pageH } };
}

// ---------------------------------------------------------------------------------------------

interface RowParts {
  box: Phaser.GameObjects.Container;
  labelW: number;
  h: number;
  fillIcons(r: EventRow, colW: number): void;
  place(x: number, y: number, w: number, costDx: number, gainDx: number): void;
  paint(sel: boolean, w: number): void;
  shake(): void;
}

/** 표 한 줄: 고름 띠 · [키] 이름 · (흐린 한 줄) · 대가 아이콘 · 보상 아이콘 */
function rowParts(scene: Phaser.Scene, r: EventRow, si: number, labelMax: number): RowParts {
  const band = scene.add.graphics();
  const label = new GlowText(
    scene,
    16,
    P.rowPadY,
    `[${r.hotkey}] ${r.label}`,
    r.enabled ? 'page_unsel' : 'page_faint',
    {
      stageIndex: si,
    },
  );
  const note = r.note
    ? new GlowText(scene, 16 + 12, P.rowPadY + label.displayHeight, r.note, 'page_faint', {
        wrap: Math.max(labelMax, label.displayWidth) + 120,
      })
    : null;
  const box = scene.add.container(0, 0, [band, label, ...(note ? [note] : [])]).setDepth(1);
  if (!r.enabled) label.setAlpha(LAYOUT.disabledAlpha);
  let h = P.rowPadY * 2 + label.displayHeight + (note ? note.displayHeight : 0);
  let costs: Phaser.GameObjects.Container | null = null;
  let gains: Phaser.GameObjects.Container | null = null;
  let baseX = 0;
  const parts: RowParts = {
    box,
    labelW: label.displayWidth,
    h,
    fillIcons(row, colW) {
      if (colW <= 0) return;
      const style = row.enabled ? 'page_body' : 'page_faint';
      const c = iconList(scene, row.costs, { style, stageIndex: si, lineH: P.iconLineH, wrap: colW - 18 });
      const g = iconList(scene, row.rewards, { style, stageIndex: si, lineH: P.iconLineH, wrap: colW - 18 });
      costs = c.box;
      gains = g.box;
      box.add([c.box, g.box]);
      if (!row.enabled) {
        c.box.setAlpha(LAYOUT.disabledAlpha);
        g.box.setAlpha(LAYOUT.disabledAlpha);
      }
      h = Math.max(h, P.rowPadY * 2 + Math.max(c.h, g.h));
      parts.h = h;
    },
    place(x, y, _w, costDx, gainDx) {
      baseX = x;
      box.setPosition(x, y);
      costs?.setPosition(costDx, P.rowPadY);
      gains?.setPosition(gainDx, P.rowPadY);
    },
    paint(sel, w) {
      band.clear();
      if (sel) {
        band.fillStyle(hexToNum(SEPIA[4]), P.selAlpha).fillRect(0, 0, w, h);
        band.fillStyle(hexToNum(accentHex(scene, si, 20)), 1).fillRect(0, h - 1, w, 1);
      }
      label.setGlowStyle(!r.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel');
    },
    shake() {
      scene.tweens.killTweensOf(box);
      box.setX(baseX);
      scene.tweens.add({
        targets: box,
        x: baseX + 3,
        duration: 40,
        yoyo: true,
        repeat: 2,
        onComplete: () => box.setX(baseX),
      });
    },
  };
  return parts;
}

/** 초상 텍스처가 쓸 수 있나 (키·프레임) */
function portraitReady(scene: Phaser.Scene, page: EventPage): boolean {
  const p = page.portrait;
  if (!p || !scene.textures.exists(p.key)) return false;
  return scene.textures.get(p.key).has(String(p.frame));
}

/** 말하는 이 초상: 가죽(S1) 칸 + S4 테 + NPC 시트 0프레임 1배(키트 밀도 — 상반신) — 머리를 위에 맞추고 칸 밖(발)은 자른다 */
function portrait(scene: Phaser.Scene, page: EventPage, x: number, y: number, si: number): void {
  const p = page.portrait!;
  const BW = P.portraitW;
  const BH = P.portraitH;
  const g = scene.add.graphics().setDepth(1);
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(x, y, BW, BH);
  g.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(x + 1, y + Math.round(BH * 0.62), BW - 2, Math.round(BH * 0.38) - 1);
  const s = P.portraitScale;
  const img = scene.add.image(0, 0, p.key, String(p.frame)).setOrigin(0, 0).setScale(s).setDepth(1);
  const f = img.frame;
  // Frame.x·y = 잘린 그림의 실제 칸 안 자리 (trim 이 없으면 0)
  const fit = portraitFit(
    { realW: f.realWidth, realH: f.realHeight, trimX: f.x, trimY: f.y, w: f.width, h: f.height },
    { x: x + 1, y: y + 1, w: BW - 2, h: BH - 3 },
    s,
    P.portraitPad,
  );
  img.setPosition(fit.x, fit.y).setCrop(fit.crop.x, fit.crop.y, fit.crop.w, fit.crop.h);
  // 테: S4 1px + 아래 강조 1px (말하는 이)
  g.lineStyle(1, hexToNum(SEPIA[4]), 1).strokeRect(x + 0.5, y + 0.5, BW - 1, BH - 1);
  const edge = scene.add.graphics().setDepth(1);
  edge.fillStyle(hexToNum(accentHex(scene, si, 20)), 1).fillRect(x + 1, y + BH - 2, BW - 2, 1);
}
