import Phaser from 'phaser';
import type { UiNodeType } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { NODE_ICON_SHEET, derivedTexture, ensureImage, keyartKey, keyartUrl } from './kit';
import { paperCanvas } from './paintFx';
import { makeGlyph } from './routeGlyph';
import {
  fadeIn,
  kenBurnsCrop,
  kenBurnsZoom,
  placePreview,
  type Box,
  type Obstacle,
  type PreviewArt,
  type PreviewText,
} from './previewView';
import { GRAY, SEPIA, hexToNum } from './theme';
import { PREVIEW } from './themeTransition';

type Obj = Phaser.GameObjects.GameObject & Phaser.GameObjects.Components.Transform;

/** 그림 출처: 텍스처 키 · 지역 키아트 · 그림 조각(수련장 지도) · 종이 */
export type PreviewSource = PreviewArt | { kind: 'crop'; key: string; rect: Box };

export interface PreviewRequest {
  /** 같은 id 면 다시 그리지 않는다 */
  id: string;
  /** 가리킨 곳 (화면 좌표) — 카드는 그 옆 빈자리에 */
  anchor: { x: number; y: number };
  art: PreviewSource;
  /** 시스템이 아직 받는 중인 미리보기 텍스처 키 — 오면(`addtexture-<키>`) 같은 자리에서 그 그림으로 교차 페이드 */
  pending?: string | null;
  text: PreviewText;
  /** 이름 앞 종류 아이콘 (왼쪽 위 (0,0), 16×16) */
  icon?: (scene: Phaser.Scene) => Obj | null;
  /** 종이 그림일 때 가운데에 그릴 것 (카드 그림 칸 기준 좌표) */
  paperDraw?: (scene: Phaser.Scene, w: number, h: number) => Obj[];
  /** 피할 것 (가리킨 곳 자체 포함) */
  obstacles: readonly Obstacle[];
}

interface Card {
  id: string;
  box: Phaser.GameObjects.Container;
  img?: Phaser.GameObjects.Image;
  texW: number;
  texH: number;
  bornAt: number;
  diedAt: number;
  /** 켄번스 치우침 (-1~1) */
  pan: number;
  /** 이미지 아래 끼울 자리 (먹 띠보다 아래) */
  under: Phaser.GameObjects.GameObject;
  /** 받는 중인 텍스처를 기다리는 처리기 (카드가 사라지면 뗀다) */
  unwait?: () => void;
}

const PAPER_KEY = 'ui-preview-paper';

/** 노드 종류 아이콘 16×16 (노드 시트 32 의 0.5배, 없으면 키트 글리프) */
export function nodeIcon(scene: Phaser.Scene, type: UiNodeType, stageIndex: number): Obj | null {
  if (NODE_ICON_SHEET.available && scene.textures.exists(NODE_ICON_SHEET.key)) {
    const col = Math.max(0, NODE_ICON_SHEET.order.indexOf(type));
    return scene.add
      .image(0, 0, NODE_ICON_SHEET.key, col)
      .setOrigin(0, 0)
      .setScale(PREVIEW.iconSize / NODE_ICON_SHEET.size);
  }
  const g = makeGlyph(scene, type, stageIndex) as Obj;
  g.setPosition(g.x + PREVIEW.iconSize / 2, g.y + PREVIEW.iconSize / 2);
  return g;
}

/** 종이 그림 가운데 종류 아이콘 크게 (시트 32 의 2배 = 64, 가운데보다 조금 위 — 아래는 먹 띠) */
export function nodeEmblem(scene: Phaser.Scene, type: UiNodeType, stageIndex: number, w: number, h: number): Obj[] {
  const ic = nodeIcon(scene, type, stageIndex);
  if (!ic) return [];
  const s = 4;
  ic.setScale((ic as Obj & { scaleX: number }).scaleX * s);
  ic.setPosition(Math.round(w / 2 - (PREVIEW.iconSize * s) / 2), Math.round(h * 0.36 - (PREVIEW.iconSize * s) / 2));
  if (ic instanceof Phaser.GameObjects.Image) ic.setAlpha(0.85);
  return [ic];
}

/**
 * 62 루프 3 UI G (도영 님 추가 지시) 지도 미리보기 카드 — 노드 지도·수련장 지도에서 가리킨 곳의 그림(시스템 `previewKey` →
 * 지역 키아트 → 그림 조각 → 종이)을 작은 액자 카드로. 그림 아래 먹 띠에 [종류 아이콘] 이름 · 종류 / 고유 한 줄 / 보상·위험 /
 * 위험 한 줄. 자리는 가리킨 곳 옆 지도 빈자리(`placePreview` — 노드·이름표와 덜 겹치는 쪽, 왼/오 자동).
 * 가리킨 곳이 바뀌면 0.15초 교차 페이드, 그림은 아주 느린 켄번스(1.03배). 입력은 받지 않는다(아래 노드를 가리지 않게 상호작용 없음).
 */
export class RoutePreview {
  private root: Phaser.GameObjects.Container;
  private cur?: Card;
  private old: Card[] = [];
  private dead = false;
  /** 그림 칸 크기 (논리) */
  private pw: number;
  private ph: number;

  constructor(
    private scene: Phaser.Scene,
    private opts: { area: Box; depth: number; stageIndex: number; picW?: number; picH?: number },
  ) {
    this.pw = opts.picW ?? PREVIEW.picW;
    this.ph = opts.picH ?? PREVIEW.picH;
    this.root = scene.add.container(0, 0).setDepth(opts.depth);
    scene.events.on(Phaser.Scenes.Events.UPDATE, this.tick);
    // 씬이 화면을 통째로 비울 때(메뉴 다시 그리기 등)도 갱신을 멈춘다
    this.root.once(Phaser.GameObjects.Events.DESTROY, () => this.stop());
  }

  /** 지금 보이는 카드 id (없으면 null) */
  get shownId(): string | null {
    return this.cur?.id ?? null;
  }

  /** 가리킨 곳 미리보기 (null = 걷기). 같은 id 면 그대로 */
  show(req: PreviewRequest | null): void {
    if (this.dead) return;
    if (req && this.cur?.id === req.id) return;
    const now = this.scene.time.now;
    this.retire(now);
    if (!req) {
      debugExpose('routePreview', null);
      return;
    }
    this.cur = this.build(req, now);
    this.tick();
  }

  destroy(): void {
    if (this.dead) return;
    this.stop();
    this.root.destroy();
  }

  /** 지금 카드를 사라지는 쪽으로 (들어오던 중이면 지금 밝기에서 — 교차 페이드가 튀지 않게) */
  private retire(now: number): void {
    const c = this.cur;
    if (!c) return;
    c.unwait?.();
    c.unwait = undefined;
    const a = fadeIn(now - c.bornAt, PREVIEW.fadeMs);
    c.diedAt = now - (1 - a) * PREVIEW.fadeMs;
    this.old.push(c);
    this.cur = undefined;
  }

  private stop(): void {
    if (this.dead) return;
    this.dead = true;
    this.scene.events.off(Phaser.Scenes.Events.UPDATE, this.tick);
    for (const c of [this.cur, ...this.old]) c?.unwait?.();
    this.cur = undefined;
    this.old = [];
    debugExpose('routePreview', null);
  }

  /** 받는 중이던 그림이 왔다: 같은 곳을 가리키고 있으면 그 그림으로 바꿔 끼운다 (같은 자리, 교차 페이드) */
  private waitFor(card: Card, req: PreviewRequest): void {
    const key = req.pending;
    if (!key) return;
    const ev = `${Phaser.Textures.Events.ADD_KEY}${key}`;
    const textures = this.scene.textures;
    const on = (): void => {
      card.unwait = undefined;
      if (this.dead || this.cur !== card) return;
      const now = this.scene.time.now;
      this.retire(now);
      this.cur = this.build({ ...req, art: { kind: 'texture', key }, pending: null }, now);
    };
    textures.once(ev, on);
    card.unwait = () => textures.off(ev, on);
  }

  // -------------------------------------------------------------------------------------------
  private build(req: PreviewRequest, now: number): Card {
    const scene = this.scene;
    const P = PREVIEW;
    const fw = P.frame;
    const W = this.pw + fw * 2;
    const H = this.ph + fw * 2;
    const place = placePreview(req.anchor, { w: W + P.shadow, h: H + P.shadow }, this.opts.area, req.obstacles, P.gap);
    const box = scene.add.container(place.x, place.y).setAlpha(0);
    this.root.add(box);
    // 그늘 · 액자 (옻칠 테 S1 · 바랜 금 선 S5 · 안쪽 먹 선)
    const g = scene.add.graphics();
    g.fillStyle(hexToNum(GRAY[0]), 0.5).fillRect(P.shadow, P.shadow, W, H);
    g.fillStyle(hexToNum(SEPIA[1]), 1).fillRect(0, 0, W, H);
    g.fillStyle(hexToNum(SEPIA[0]), 1).fillRect(fw - 1, fw - 1, this.pw + 2, this.ph + 2);
    g.lineStyle(1, hexToNum(SEPIA[3]), 1).strokeRect(0.5, 0.5, W - 1, H - 1);
    g.lineStyle(1, hexToNum(SEPIA[5]), 0.85).strokeRect(fw - 1.5, fw - 1.5, this.pw + 3, this.ph + 3);
    box.add(g);
    // 그림 자리 (그림이 늦으면 어두운 종이색)
    const hold = scene.add.rectangle(fw, fw, this.pw, this.ph, hexToNum(GRAY[1]), 1).setOrigin(0, 0);
    box.add(hold);
    const card: Card = {
      id: req.id,
      box,
      texW: 0,
      texH: 0,
      bornAt: now,
      diedAt: -1,
      pan: (hashId(req.id) % 3) - 1,
      under: hold,
    };
    this.band(box, req);
    this.picture(card, req);
    this.waitFor(card, req);
    debugExpose('routePreview', {
      id: req.id,
      x: place.x,
      y: place.y,
      w: W,
      h: H,
      side: place.side,
      art: req.art.kind,
      key: 'key' in req.art ? req.art.key : 'art' in req.art ? req.art.art : null,
      pending: req.pending ?? null,
    });
    return card;
  }

  /** 그림 아래 먹 띠 + 글 (아래에서 위로 쌓는다) */
  private band(box: Phaser.GameObjects.Container, req: PreviewRequest): void {
    const scene = this.scene;
    const P = PREVIEW;
    const si = this.opts.stageIndex;
    const fw = P.frame;
    const tw = this.pw - P.bandPad * 2;
    const t = req.text;
    const rows: { obj: Obj; h: number }[] = [];
    // 이름 줄: [아이콘] 이름 · 종류
    if (t.name) {
      const row = scene.add.container(0, 0);
      let x = 0;
      const icon = req.icon?.(scene) ?? null;
      if (icon) {
        row.add(icon);
        x += P.iconSize + P.iconGap;
      }
      const name = new GlowText(scene, x, 0, t.name, 'ink_body', { stageIndex: si });
      row.add(name);
      x += name.displayWidth;
      if (t.kind) row.add(new GlowText(scene, x + 2, 0, `· ${t.kind}`, 'ink_faint', { stageIndex: si }));
      if (icon) icon.setY(Math.round((name.displayHeight - P.iconSize) / 2));
      rows.push({ obj: row, h: Math.max(name.displayHeight, P.iconSize) });
    }
    const add = (text: string, style: 'ink_faint' | 'ink_accent'): void => {
      if (!text) return;
      const gt = new GlowText(scene, 0, 0, text, style, { wrap: tw, stageIndex: si });
      rows.push({ obj: gt, h: gt.displayHeight });
    };
    add(t.line, 'ink_faint');
    add(t.marks, 'ink_accent');
    add(t.warn, 'ink_accent');
    if (!rows.length) return;
    const textH = rows.reduce((s, r) => s + r.h, 0) + P.lineGap * (rows.length - 1);
    const bandH = Math.min(this.ph, textH + P.bandPad * 2);
    const bottom = fw + this.ph;
    const top = bottom - bandH;
    const g = scene.add.graphics();
    const ink = hexToNum(GRAY[0]);
    // 위로 번지는 계단 (먹이 옅어지며 그림으로 스민다)
    for (let i = 0; i < P.bandSteps; i++) {
      const a = (P.bandAlpha * (i + 1)) / (P.bandSteps + 1);
      g.fillStyle(ink, a).fillRect(fw, top - (P.bandSteps - i) * P.bandStepH, this.pw, P.bandStepH);
    }
    g.fillStyle(ink, P.bandAlpha).fillRect(fw, top, this.pw, bandH);
    box.add(g);
    let y = top + P.bandPad;
    for (const r of rows) {
      r.obj.setPosition(fw + P.bandPad, Math.round(y));
      box.add(r.obj);
      y += r.h + P.lineGap;
    }
  }

  /** 그림: 출처에 따라 렌더 배율 텍스처를 만들어 그림 자리에 (늦게 오면 그때 끼운다) */
  private picture(card: Card, req: PreviewRequest): void {
    const scene = this.scene;
    const P = PREVIEW;
    const tw = this.pw * P.res;
    const th = this.ph * P.res;
    const place = (key: string | null): void => {
      if (!key || this.dead || card.diedAt >= 0 || !card.box.active) return;
      scene.textures.get(key).setFilter(Phaser.Textures.FilterMode.LINEAR);
      const img = scene.add
        .image(P.frame, P.frame, key)
        .setOrigin(0, 0)
        .setScale(1 / P.res);
      card.box.addAt(img, card.box.getIndex(card.under) + 1);
      card.img = img;
      card.texW = tw;
      card.texH = th;
    };
    const art = req.art;
    if (art.kind === 'texture') place(derivedTexture(scene, art.key, tw, th, 'cover'));
    else if (art.kind === 'keyart') {
      const k = keyartKey(art.art);
      if (scene.textures.exists(k)) place(derivedTexture(scene, k, tw, th, 'cover'));
      else ensureImage(scene, k, keyartUrl(art.art), (ok) => ok && place(derivedTexture(scene, k, tw, th, 'cover')));
    } else if (art.kind === 'crop') place(cropTexture(scene, art.key, art.rect, tw, th));
    else {
      place(paperKey(scene, tw, th));
      for (const o of req.paperDraw?.(scene, this.pw, this.ph) ?? []) {
        o.setPosition(o.x + P.frame, o.y + P.frame);
        card.box.addAt(o, card.box.getIndex(card.img ?? card.under) + 1);
      }
    }
  }

  private tick = (): void => {
    if (this.dead) return;
    const now = this.scene.time.now;
    const c = this.cur;
    if (c) {
      c.box.setAlpha(fadeIn(now - c.bornAt, PREVIEW.fadeMs));
      this.ken(c, now);
    }
    if (this.old.length) {
      this.old = this.old.filter((o) => {
        const a = 1 - fadeIn(now - o.diedAt, PREVIEW.fadeMs);
        if (a <= 0 || !o.box.active) {
          o.box.destroy();
          return false;
        }
        o.box.setAlpha(a);
        return true;
      });
    }
  };

  /** 아주 느린 켄번스: 그림 칸 크기는 그대로, 자르기를 좁혀 1 → 1.03 배 */
  private ken(c: Card, now: number): void {
    const img = c.img;
    if (!img || !img.active || c.texW <= 0) return;
    const z = kenBurnsZoom(now - c.bornAt, PREVIEW.kenZoom, PREVIEW.kenPeriodMs);
    const r = kenBurnsCrop(c.texW, c.texH, z, c.pan * 0.6, 0);
    const s = (this.pw / c.texW) * z;
    img.setCrop(r.x, r.y, r.w, r.h).setScale(s);
    img.setPosition(PREVIEW.frame - r.x * s, PREVIEW.frame - r.y * s);
  }
}

function hashId(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return h;
}

/** 종이 한 장 (렌더 배율 크기, 한 번만) */
function paperKey(scene: Phaser.Scene, w: number, h: number): string | null {
  const key = `${PAPER_KEY}@${w}x${h}`;
  if (!scene.textures.exists(key)) scene.textures.addCanvas(key, paperCanvas(w, h, 6262));
  return scene.textures.exists(key) ? key : null;
}

/** 그림 조각 (수련장 지도의 방 자리 둘레) → w×h 텍스처 (같은 조각이면 다시 만들지 않는다) */
function cropTexture(scene: Phaser.Scene, src: string, r: Box, w: number, h: number): string | null {
  if (!scene.textures.exists(src)) return null;
  const key = `${src}@crop${r.x},${r.y},${r.w},${r.h}@${w}x${h}`;
  if (scene.textures.exists(key)) return key;
  const img = scene.textures.get(src).getSourceImage() as HTMLImageElement | HTMLCanvasElement;
  const tex = scene.textures.createCanvas(key, w, h);
  if (!tex) return null;
  const ctx = tex.getContext();
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, r.x, r.y, r.w, r.h, 0, 0, w, h);
  tex.refresh();
  return key;
}
