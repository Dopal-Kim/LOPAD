import Phaser from 'phaser';
import { UI_SCREEN, type UiMenu, type UiMenuLine, type UiSnapshot } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { accentHex, book, derivedTexture, ensureImage, rule } from './kit';
import { CardRow, cancelText, menuCloseButton, type CardPage, type CardPageCtx, type CardSlot } from './MenuCards';
import { artJson, artTex, paintUrl, uiCopy } from './paintArt';
import { paperCanvas } from './paintFx';
import { trainingText } from './text';
import { GRAY, LAYOUT, SEPIA, hexToNum } from './theme';
import { HEALTH_BAR } from './themeR61';
import { TRAINING_UI } from './themeTransition';
import { readMapRooms, spotsFor, type MapSpot } from './trainingView';
import { noteTransitionOrigin } from './transitionState';

/** 한 번 읽어 본 키 (실패해도 다시 읽지 않는다) */
const artTried = new Set<string>();

/**
 * 수련장 지도 그림·메타가 아직 없으면 읽는다 (시스템이 `mapKey` 로 알려 줬는데 아직 안 읽힌 경우 포함).
 * 다 읽히면 done(true) — 메뉴가 그대로면 다시 그린다. 이미 있으면 false (다시 그릴 필요 없음)
 */
export function ensureTrainingArt(scene: Phaser.Scene, key: string, done: (ok: boolean) => void): boolean {
  if (artTried.has(key)) return false;
  const needImg = !artTex(scene, key);
  const needJson = !artJson(scene, key);
  const copy = uiCopy(key);
  if (!needImg && !needJson) return false;
  artTried.add(key);
  let left = (needImg ? 1 : 0) + (needJson ? 1 : 0);
  let ok = true;
  const step = (good: boolean): void => {
    ok = ok && good;
    left -= 1;
    if (left === 0) done(ok || Boolean(artTex(scene, key)));
  };
  if (needImg) ensureImage(scene, copy, `${paintUrl(key)}.png`, step);
  if (needJson) {
    const load = scene.load;
    const onDone = (): void => {
      load.off(Phaser.Loader.Events.FILE_LOAD_ERROR, onErr);
      step(true);
    };
    const onErr = (file: Phaser.Loader.File): void => {
      if (file.key !== copy) return;
      load.off(`filecomplete-json-${copy}`, onDone);
      load.off(Phaser.Loader.Events.FILE_LOAD_ERROR, onErr);
      step(false);
    };
    load.once(`filecomplete-json-${copy}`, onDone);
    load.on(Phaser.Loader.Events.FILE_LOAD_ERROR, onErr);
    load.json(copy, `${paintUrl(key)}.json`);
    if (!load.isLoading()) load.start();
  }
  return true;
}

/** 그림 없는 두루마리 종이 텍스처 (크기별 한 번) */
function scrollPaperKey(scene: Phaser.Scene, w: number, h: number): string {
  const key = `ui-training-scroll@${w}x${h}`;
  if (!scene.textures.exists(key)) {
    const tex = scene.textures.addCanvas(key, paperCanvas(w, h, 4242, [0x8f, 0x76, 0x5c]));
    tex?.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
  return key;
}

/** 방 자리 그림: 작은 액자 입구(옻칠 테 · 어두운 아치 · 바랜 금 선). 지역 (0,0) 가운데. sel = 고름 고리 */
function paintSpot(scene: Phaser.Scene, g: Phaser.GameObjects.Graphics, sel: boolean, enabled: boolean): void {
  const r = TRAINING_UI.spotR;
  const w = r * 1.5;
  const h = r * 1.9;
  g.clear();
  g.fillStyle(hexToNum(GRAY[0]), 0.45).fillEllipse(0, h / 2 + 2, w * 1.3, 6);
  g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(-w / 2 - 3, -h / 2 - 3, w + 6, h + 6);
  g.fillStyle(hexToNum(SEPIA[3]), 1).fillRect(-w / 2 - 1, -h / 2 - 1, w + 2, h + 2);
  // 아치 입구
  g.fillStyle(hexToNum(GRAY[1]), 1);
  g.fillRect(-w / 2 + 3, -h / 2 + w / 2, w - 6, h - w / 2 - 3);
  g.fillCircle(0, -h / 2 + w / 2, w / 2 - 3);
  g.fillStyle(hexToNum(SEPIA[5]), enabled ? 0.35 : 0.15).fillEllipse(0, h / 2 - 7, w * 0.5, 5);
  g.lineStyle(1, hexToNum(SEPIA[5]), 0.9).strokeRect(-w / 2 - 2.5, -h / 2 - 2.5, w + 5, h + 5);
  if (sel) g.lineStyle(2, hexToNum(accentHex(scene, 0, 20)), 1).strokeRect(-w / 2 - 6, -h / 2 - 6, w + 12, h + 12);
}

/** 그림 지도 위 방 자리: 그림에 이미 입구가 그려져 있으므로 고리만 (고름 = 강조 고리 두 겹) */
function paintRing(scene: Phaser.Scene, g: Phaser.GameObjects.Graphics, sel: boolean, enabled: boolean): void {
  const r = TRAINING_UI.spotR * 1.3;
  g.clear();
  g.lineStyle(2, hexToNum(GRAY[0]), enabled ? 0.55 : 0.3).strokeCircle(0, 0, r + 1);
  g.lineStyle(1, hexToNum(SEPIA[5]), enabled ? 0.8 : 0.4).strokeCircle(0, 0, r);
  if (sel) {
    const a = hexToNum(accentHex(scene, 0, 20));
    g.lineStyle(2, a, 1).strokeCircle(0, 0, r + 4);
    g.lineStyle(1, a, 0.5).strokeCircle(0, 0, r + 8);
  }
}

/** 작은 인주 도장 (방 자리 오른쪽 위) */
function paintStampMark(g: Phaser.GameObjects.Graphics, x: number, y: number, s: number): void {
  g.fillStyle(hexToNum(HEALTH_BAR.fill), 0.2).fillRect(x - s / 2, y - s / 2, s, s);
  g.lineStyle(2, hexToNum(HEALTH_BAR.fill), 1).strokeRect(x - s / 2 + 1, y - s / 2 + 1, s - 2, s - 2);
  g.lineStyle(1, hexToNum(HEALTH_BAR.fill), 1).lineBetween(x - s / 4, y, x + s / 4, y);
  g.lineBetween(x, y - s / 4, x, y + s / 4);
}

/**
 * 61 단계 6 (P14 §1, 계약 §19) 수련장 지도 — 시스템 메뉴 'training'(줄 `room` = 방 id, `stamped`, cancelKey '0' = 나가기)를
 * 그림 두루마리로: 그림 `training.mapKey`(`paint/map_training`, 메타 rooms 자리) 또는 코드 두루마리(종이 + 양끝 축 + 먹 길).
 * 방 8 자리 = 작은 액자 입구 + 번호 + 이름 + 도장. 1~8 · ←→ · Enter·클릭, ↓ 그만두기 칸, Esc·0 나가기.
 * 고르면 그 자리를 적어 둔다(그림 속 입구 전환이 그 입구로 파고든다 — transitionState).
 */
export function showTrainingMap(scene: Phaser.Scene, m: UiMenu, snap: UiSnapshot, ctx: CardPageCtx): CardPage | null {
  // 취소(나가기) 줄: cancelKey, 없으면 '0' 줄 (계약 §19 — 취소 키 '0')
  const cancelKey = m.cancelKey ?? (m.lines.some((l) => l.key === '0') ? '0' : undefined);
  m = { ...m, cancelKey };
  const rooms = m.lines.filter((l) => l.key !== cancelKey);
  if (!rooms.length) return null;
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const U = TRAINING_UI;
  const si = ctx.stageIndex;
  const mw = U.mapW;
  const mh = U.mapH;
  const x0 = Math.round((W - mw) / 2);
  const y0 = Math.round((H - mh) / 2);
  scene.add.rectangle(0, 0, W, H, hexToNum(GRAY[0]), 0.55).setOrigin(0, 0).setInteractive();
  // 두루마리: 양끝 축(어두운 나무 원통) + 종이
  const rollW = 14;
  const axis = scene.add.graphics();
  for (const ax of [x0 - rollW, x0 + mw]) {
    axis.fillStyle(hexToNum(SEPIA[0]), 1).fillRect(ax, y0 - 10, rollW, mh + 20);
    axis.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(ax + 3, y0 - 10, 4, mh + 20);
    axis
      .fillStyle(hexToNum(SEPIA[4]), 1)
      .fillRect(ax + 2, y0 - 14, rollW - 4, 4)
      .fillRect(ax + 2, y0 + mh + 10, rollW - 4, 4);
  }
  const artKey = snap.training?.mapKey || 'paint/map_training';
  const mapKey = artTex(scene, artKey);
  let metaSpots: MapSpot[] = [];
  if (mapKey) {
    const src = scene.textures.get(mapKey).getSourceImage() as { width: number; height: number };
    const dk = derivedTexture(scene, mapKey, mw, mh, 'stretch');
    if (dk) scene.add.image(x0, y0, dk).setOrigin(0, 0);
    const meta = artJson(scene, artKey);
    metaSpots = readMapRooms(meta, src.width, src.height);
  } else {
    scene.add.image(x0, y0, scrollPaperKey(scene, mw, mh)).setOrigin(0, 0);
  }
  const ids = rooms.map((l) => l.room ?? l.key);
  const spots = spotsFor(ids, metaSpots);
  const pos = spots.map((sp) => ({ x: Math.round(x0 + sp.u * mw), y: Math.round(y0 + sp.v * mh) }));
  // 그림이 없으면 먹 길 (방 자리 차례로 잇는 굵은 붓선 + 점)
  if (!mapKey) {
    const path = scene.add.graphics();
    path.lineStyle(5, hexToNum(SEPIA[2]), 0.55);
    path.beginPath();
    pos.forEach((p, i) => (i ? path.lineTo(p.x, p.y + 8) : path.moveTo(p.x, p.y + 8)));
    path.strokePath();
    path.lineStyle(1, hexToNum(SEPIA[1]), 0.8);
    path.beginPath();
    pos.forEach((p, i) => (i ? path.lineTo(p.x, p.y + 8) : path.moveTo(p.x, p.y + 8)));
    path.strokePath();
  }
  const title = new GlowText(scene, 0, 0, m.title || trainingText('mapTitle'), 'page_title', {
    scale: 2,
    stageIndex: si,
  });
  title.placeCenter(W / 2, y0 + 12).setDepth(2);
  const sub = new GlowText(scene, 0, 0, m.footer || trainingText('mapSub'), 'page_faint');
  sub.placeCenter(W / 2, y0 + 14 + title.displayHeight).setDepth(2);
  const close = m.cancelKey ? menuCloseButton(scene, si, () => ctx.send(m.cancelKey!)) : null;
  close?.setPosition(x0 + mw - 12 - close.width, y0 + 10);

  const slots: CardSlot[] = [];
  const picks: (() => void)[] = [];
  const hovers: (() => void)[] = [];
  rooms.forEach((l, i) => {
    const p = pos[i];
    const g = scene.add.graphics();
    const num = new GlowText(scene, -U.spotR - 6, -U.spotR - 12, String(i + 1), 'page_body', { stageIndex: si });
    const marks = scene.add.graphics();
    if (l.stamped) paintStampMark(marks, U.spotR, -U.spotR, 14);
    const box = scene.add
      .container(p.x, p.y, [g, marks, num])
      .setSize(U.spotR * 3, U.spotR * 3)
      .setDepth(3);
    box.setInteractive(
      new Phaser.Geom.Rectangle(U.spotR * 1.5, U.spotR * 1.5, U.spotR * 3, U.spotR * 3),
      Phaser.Geom.Rectangle.Contains,
    );
    if (box.input) box.input.cursor = l.enabled ? 'pointer' : 'default';
    box.on('pointerover', () => hovers[i]());
    box.on('pointerdown', () => picks[i]());
    const label = new GlowText(scene, 0, 0, l.label, 'page_unsel', {
      wrap: 132,
      align: 'center',
      stageIndex: si,
    }).setDepth(3);
    label.placeCenter(p.x, p.y + U.spotR + U.labelGap + 4);
    const detail = l.stamped ? new GlowText(scene, 0, 0, trainingText('mapStamped'), 'page_faint').setDepth(3) : null;
    detail?.placeCenter(p.x, p.y + U.spotR + U.labelGap + 4 + label.displayHeight);
    slots.push({
      key: l.key,
      hotkey: String(i + 1),
      enabled: l.enabled,
      paint: (sel) => {
        if (mapKey) paintRing(scene, g, sel, l.enabled);
        else paintSpot(scene, g, sel, l.enabled);
        box.setY(sel && l.enabled ? p.y - 3 : p.y).setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
        label
          .setGlowStyle(!l.enabled ? 'page_faint' : sel ? 'page_selected' : 'page_unsel')
          .setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
      },
    });
  });
  const cancel = cancelText(scene, m, si);
  const hint = new GlowText(scene, 0, 0, trainingText('mapHint'), 'page_faint').setDepth(2);
  const bottom = y0 + mh - 14 - hint.displayHeight;
  hint.placeCenter(W / 2, bottom);
  cancel?.text.placeCenter(W / 2, bottom - 4 - cancel.text.displayHeight).setDepth(3);
  // 고르면 그 방 자리를 적어 두고 보낸다 (그림 속 입구 전환이 그 입구로 파고든다)
  const send = (key: string): void => {
    const i = rooms.findIndex((l) => l.key === key);
    if (i >= 0) noteTransitionOrigin('training', ids[i], pos[i].x, pos[i].y, performance.now());
    ctx.send(key);
  };
  const row = new CardRow(scene, slots, cancel, send, ctx.keepCursor);
  slots.forEach((_, i) => {
    hovers[i] = () => row.hover(i);
    picks[i] = () => row.choose(i);
  });
  debugExpose('trainingMap', { spots: ids.map((id, i) => ({ id, ...pos[i] })), meta: metaSpots.length > 0 });
  return { row, bottom: { x: W / 2, y: y0 + mh } };
}

/**
 * 61 단계 6: 첫 생 '수련장부터 / 바로 벽 밖으로' (메뉴 'trainingChoice', 줄 key 'training'·'run') — 일기장 한 페이지 위 카드 2장.
 * 수련장 카드는 작은 입구 그림, 런 카드는 열린 길. 1·2 · ←→ · Enter·클릭.
 */
export function showTrainingChoice(scene: Phaser.Scene, m: UiMenu, ctx: CardPageCtx): CardPage | null {
  const lines = m.lines.filter((l) => l.key !== m.cancelKey);
  if (lines.length < 2 || lines.length > 3) return null;
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const si = ctx.stageIndex;
  const cw = 200;
  const ch = 168;
  const gap = 24;
  const n = lines.length;
  const rowW = n * cw + (n - 1) * gap;
  const padX = 24;
  const title = new GlowText(scene, 0, 0, m.title, 'page_title', { scale: 2, stageIndex: si }).setDepth(1);
  const footer = m.footer
    ? new GlowText(scene, 0, 0, m.footer, 'page_faint', { wrap: rowW, align: 'center' }).setDepth(1)
    : null;
  const hint = new GlowText(scene, 0, 0, trainingText('choiceHint'), 'page_faint').setDepth(1);
  const pageW = Math.max(rowW + padX * 2, title.displayWidth + padX * 2);
  const footerH = footer ? footer.displayHeight + 8 : 0;
  const pageH = 16 + title.displayHeight + 8 + 4 + 14 + footerH + ch + 12 + hint.displayHeight + 14;
  const bk = book(scene, Math.round(W / 2), Math.round(H / 2), pageW, pageH, 1, `menu:${m.id}`);
  const pg = bk.pages[0];
  let y = pg.y + 16;
  title.placeCenter(pg.x + pageW / 2, y);
  y += title.displayHeight + 8;
  rule(scene, pg.x + padX, y, pageW - padX * 2).setDepth(1);
  y += 4 + 14;
  if (footer) {
    footer.placeCenter(pg.x + pageW / 2, y);
    y += footerH;
  }
  const cx0 = Math.round(pg.x + pageW / 2 - rowW / 2);
  const slots: CardSlot[] = [];
  const picks: (() => void)[] = [];
  const hovers: (() => void)[] = [];
  lines.forEach((l: UiMenuLine, i) => {
    const x = cx0 + i * (cw + gap);
    const g = scene.add.graphics();
    const art = scene.add.graphics();
    // 계약 §19: '1' 수련장부터 / '2' 바로 벽 밖으로 (옛 키 'training'·'run' 도 읽는다)
    const training = l.key === 'training' || (l.key !== 'run' && i === 0);
    // 그림 칸: 수련장 = 작은 입구, 런 = 지평선으로 열린 길
    const ax = cw / 2;
    const ay = 52;
    if (training) {
      art.setPosition(ax, ay);
      paintSpot(scene, art, false, true);
      art.setScale(1.6);
    } else {
      art.fillStyle(hexToNum(SEPIA[2]), 1).fillRect(24, 70, cw - 48, 2);
      art.fillStyle(hexToNum(SEPIA[3]), 1);
      art.fillTriangle(ax - 10, 72, ax + 10, 72, ax + 34, 100);
      art.fillTriangle(ax - 10, 72, ax - 34, 100, ax + 34, 100);
      art.fillStyle(hexToNum(SEPIA[5]), 0.6).fillCircle(ax + 40, 40, 9);
    }
    const key = new GlowText(scene, 8, 7, `[${i + 1}]`, 'page_body', { stageIndex: si });
    const label = new GlowText(scene, 0, 0, l.label, 'page_unsel', { wrap: cw - 16, align: 'center', stageIndex: si });
    label.setPosition(Math.round(cw / 2 - label.displayWidth / 2), 108);
    const sub = new GlowText(
      scene,
      0,
      0,
      l.detail || trainingText(training ? 'choiceTraining' : 'choiceRun'),
      'page_faint',
      { wrap: cw - 16, align: 'center' },
    );
    sub.setPosition(Math.round(cw / 2 - sub.displayWidth / 2), 108 + label.displayHeight + 2);
    const box = scene.add.container(x, y, [g, art, key, label, sub]).setSize(cw, ch).setDepth(1);
    box.setInteractive(new Phaser.Geom.Rectangle(cw / 2, ch / 2, cw, ch), Phaser.Geom.Rectangle.Contains);
    if (box.input) box.input.cursor = 'pointer';
    box.on('pointerover', () => hovers[i]());
    box.on('pointerdown', () => picks[i]());
    const baseY = y;
    slots.push({
      key: l.key,
      hotkey: String(i + 1),
      enabled: l.enabled,
      paint: (sel) => {
        g.clear();
        g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, cw, ch);
        g.lineStyle(1, hexToNum(SEPIA[4]), 1).strokeRect(4.5, 4.5, cw - 9, ch - 9);
        g.lineStyle(sel ? 2 : 1, sel ? hexToNum(accentHex(scene, si, 20)) : hexToNum(SEPIA[0]), 1);
        if (sel) g.strokeRect(1, 1, cw - 2, ch - 2);
        else g.strokeRect(0.5, 0.5, cw - 1, ch - 1);
        box.setY(sel ? baseY - 4 : baseY).setAlpha(l.enabled ? 1 : LAYOUT.disabledAlpha);
        label.setGlowStyle(sel ? 'page_selected' : 'page_unsel');
      },
    });
  });
  y += ch + 12;
  hint.placeCenter(pg.x + pageW / 2, y);
  const row = new CardRow(scene, slots, null, ctx.send, ctx.keepCursor);
  slots.forEach((_, i) => {
    hovers[i] = () => row.hover(i);
    picks[i] = () => row.choose(i);
  });
  return { row, bottom: { x: pg.x + pageW / 2, y: pg.y + pageH } };
}
