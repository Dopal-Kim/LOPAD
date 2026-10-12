import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { GlowText } from './glow';
import { keyGlyph } from './keyGuide';
import { fontFamily } from './kit';
import { parseHint } from './ritualView';
import { GRAY, SEPIA, hexToNum } from './theme';
import { RITUAL_UI as R } from './themeRitual';

/**
 * 62 루프 1 P0-2 첫 생 의식 UI 공용 조각 (RitualScene 의 각 장이 같이 쓴다): 아트 그림 찾기·읽기, 아래 안내 줄(키캡),
 * 먹 글씨, 단추(Container → Graphics → Text), 어둠 바탕.
 */

type ArtName = keyof typeof R.art;

/** 그림 텍스처 키 (읽혔으면) */
export function ritualTex(scene: Phaser.Scene, name: ArtName): string | null {
  const key = R.art[name];
  return scene.textures.exists(key) ? key : null;
}

/** 그림 메타 JSON (art §30 — nameField·strokeArea·slice 등). 없으면 null */
export function ritualMeta<T = Record<string, unknown>>(scene: Phaser.Scene, name: ArtName): T | null {
  const k = `${R.art[name]}.json`;
  return scene.cache.json.exists(k) ? (scene.cache.json.get(k) as T) : null;
}

/** 의식 그림을 한 번에 읽는다 (art §30: 일기장 첫 장·등 화폭·빛무리·먹 붓 아틀라스·운명 액자 + 메타 JSON). 다 끝나면 done */
export function loadRitualArt(scene: Phaser.Scene, done: () => void): void {
  const L = scene.load;
  const base = R.artUrl;
  const file = (k: string): string => k.replace(/^ritual\//, '');
  let n = 0;
  for (const name of ['page', 'back', 'frame'] as const) {
    const k = R.art[name];
    if (!scene.textures.exists(k)) {
      L.image(k, `${base}${file(k)}.png`);
      n++;
    }
    if (!scene.cache.json.exists(`${k}.json`)) {
      L.json(`${k}.json`, `${base}${file(k)}.json`);
      n++;
    }
  }
  if (!scene.textures.exists(R.art.glow)) {
    L.image(R.art.glow, `${base}${file(R.art.glow)}.png`);
    n++;
  }
  if (!scene.textures.exists(R.art.brush)) {
    L.atlas(R.art.brush, `${base}${file(R.art.brush)}.png`, `${base}${file(R.art.brush)}.json`);
    n++;
  }
  if (!n) {
    done();
    return;
  }
  L.once(Phaser.Loader.Events.COMPLETE, done);
  if (!L.isLoading()) L.start();
}

/** 화면 전체 어둠 (G00) — 가장자리는 한 단 더 어둡게 (계단 2단, 흐림 없음) */
export function darkBackdrop(scene: Phaser.Scene, alpha: number): Phaser.GameObjects.Graphics {
  const W = UI_SCREEN.WIDTH;
  const H = UI_SCREEN.HEIGHT;
  const g = scene.add.graphics();
  g.fillStyle(hexToNum(GRAY[0]), alpha).fillRect(0, 0, W, H);
  g.fillStyle(hexToNum(GRAY[0]), Math.min(1, alpha + 0.08));
  g.fillRect(0, 0, W, 24)
    .fillRect(0, H - 24, W, 24)
    .fillRect(0, 24, 24, H - 48)
    .fillRect(W - 24, 24, 24, H - 48);
  return g;
}

/**
 * 아래 가운데 안내 줄: 시스템 `hint`('[Enter] 적는다 · …')를 키캡 + 동작으로. surface 'page' 면 종이 글색.
 * (cx, bottom) 기준 가운데·아래 맞춤. 단추처럼 누를 수 있게 하려면 `onPart(i)` 를 준다.
 */
export function hintRow(
  scene: Phaser.Scene,
  hint: string | null | undefined,
  cx: number,
  bottom: number,
  surface: 'ink' | 'page' = 'ink',
  /** 따로 단추로 그린 키는 줄에서 뺀다 */
  omitKeys: readonly string[] = [],
): Phaser.GameObjects.Container {
  const parts = parseHint(hint).filter((p) => !p.keys.some((k) => omitKeys.includes(k)));
  const box = scene.add.container(0, 0);
  const items: { objs: Phaser.GameObjects.GameObject[]; w: number }[] = [];
  for (const p of parts) {
    const objs: Phaser.GameObjects.GameObject[] = [];
    let x = 0;
    for (const k of p.keys) {
      const gl = keyGlyph(scene, k);
      gl.obj.setPosition(x, 0);
      objs.push(gl.obj);
      x += gl.width + 3;
    }
    if (p.label) {
      const t = new GlowText(
        scene,
        x + (p.keys.length ? 2 : 0),
        0,
        p.label,
        surface === 'page' ? 'page_body' : 'ink_body',
      );
      objs.push(t);
      x = t.x + t.displayWidth;
    }
    items.push({ objs, w: x });
  }
  const gap = 18;
  const total = items.reduce((s, it) => s + it.w, 0) + Math.max(0, items.length - 1) * gap;
  let x = Math.round(cx - total / 2);
  for (const it of items) {
    const c = scene.add.container(x, bottom - 16, it.objs);
    box.add(c);
    x += it.w + gap;
  }
  return box;
}

/**
 * 먹 글씨: Galmuri14 정수 확대 + 먹 번짐 1px(옅은 먹) 네 방향 — 종이 위 붓글씨 느낌. (x, y) 왼쪽 위.
 * `alpha` 로 흐리게(번진 이름).
 */
export class InkText extends Phaser.GameObjects.Container {
  private texts: Phaser.GameObjects.Text[] = [];
  private value = '';

  constructor(scene: Phaser.Scene, x: number, y: number, text: string, scale: number) {
    super(scene, x, y);
    const mk = (dx: number, dy: number, color: string, alpha: number): void => {
      const t = scene.add
        .text(dx, dy, '', { fontFamily: fontFamily('title'), fontSize: '14px', color })
        .setOrigin(0, 0)
        .setAlpha(alpha);
      this.texts.push(t);
      this.add(t);
    };
    for (const [dx, dy] of [
      [-1, 0],
      [1, 0],
      [0, 1],
      [0, -1],
    ] as const)
      mk(dx, dy, R.inkBleed, 0.6);
    mk(0, 0, R.ink, 1);
    this.setScale(scale);
    scene.add.existing(this);
    this.setText(text);
  }

  setText(text: string): this {
    if (text === this.value) return this;
    this.value = text;
    for (const t of this.texts) t.setText(text);
    return this;
  }

  /** 글 폭 (확대 반영) */
  get textW(): number {
    const main = this.texts[this.texts.length - 1];
    return Math.ceil(main.width * this.scaleX);
  }

  get textH(): number {
    const main = this.texts[this.texts.length - 1];
    return Math.ceil(main.height * this.scaleY);
  }

  /** 앞 n 글자까지의 폭 (먹 번짐 자리) */
  prefixW(n: number): number {
    const main = this.texts[this.texts.length - 1];
    const keep = main.text;
    main.setText(Array.from(this.value).slice(0, n).join(''));
    const w = main.width;
    main.setText(keep);
    return Math.ceil(w * this.scaleX);
  }
}

/** 먹 번짐: (x, y) 둘레에 점이 퍼지며 옅어진다 (새 글자·획 끝) */
export function inkBleed(scene: Phaser.Scene, x: number, y: number, depth: number): void {
  const P = R.page;
  const g = scene.add.graphics().setDepth(depth);
  const dots = Array.from({ length: P.bleedDots }, () => ({
    a: Math.random() * Math.PI * 2,
    d: 2 + Math.random() * P.bleedR,
    r: 1 + Math.floor(Math.random() * 2),
  }));
  const o = { k: 0 };
  scene.tweens.add({
    targets: o,
    k: 1,
    duration: P.bleedMs,
    onUpdate: () => {
      g.clear();
      for (const d of dots) {
        g.fillStyle(hexToNum(R.inkBleed), 0.7 * (1 - o.k));
        g.fillCircle(Math.round(x + Math.cos(d.a) * d.d * o.k), Math.round(y + Math.sin(d.a) * d.d * o.k), d.r);
      }
    },
    onComplete: () => g.destroy(),
  });
}

/**
 * 작은 단추 (Container → Graphics → 키캡·Text): 잉크 바탕 + 1px 테, 마우스를 올리면 테가 강조색. 누르면 onClick.
 * (x, y) 왼쪽 위. 폭을 돌려준다.
 */
export function ritualButton(
  scene: Phaser.Scene,
  x: number,
  y: number,
  key: string,
  label: string,
  onClick: () => void,
  accent = false,
): { box: Phaser.GameObjects.Container; w: number; h: number } {
  const pad = 6;
  const gl = keyGlyph(scene, key);
  const t = new GlowText(scene, 0, 0, label, accent ? 'ink_accent' : 'ink_body');
  const w = pad + gl.width + 5 + t.displayWidth + pad;
  const h = 24;
  const g = scene.add.graphics();
  const draw = (hover: boolean): void => {
    g.clear();
    g.fillStyle(hexToNum(GRAY[1]), 0.92).fillRect(0, 0, w, h);
    g.lineStyle(1, hexToNum(hover ? SEPIA[5] : SEPIA[3]), 1).strokeRect(0.5, 0.5, w - 1, h - 1);
  };
  draw(false);
  gl.obj.setPosition(pad, 4);
  t.setPosition(pad + gl.width + 5, 4);
  const box = scene.add.container(x, y, [g, gl.obj, t]);
  box.setSize(w, h);
  box.setInteractive(new Phaser.Geom.Rectangle(w / 2, h / 2, w, h), Phaser.Geom.Rectangle.Contains);
  box.input!.cursor = 'pointer';
  box.on('pointerover', () => draw(true));
  box.on('pointerout', () => draw(false));
  box.on('pointerup', onClick);
  return { box, w, h };
}

/**
 * 붓 이름 (art §30 nameBrush 제안): 글자 모양은 Galmuri14 를 따르고, 화면에는 먹 붓 스탬프(`ink_brush` tip_d2)로 찍는다.
 * 새로 적힌 글자는 왼쪽 → 오른쪽 열 차례로 찍혀 나타나고(붓이 지나가는 듯), 앞 글자는 그대로 남는다. 칸 = 논리 1px = 도트 1.
 * (x, y) = 칸 왼쪽 위, baseline = 칸 안 글자 바닥선(y 기준 상대). 붓 아틀라스가 없으면 쓰지 않는다(RitualName 이 InkText 로).
 */
export class BrushName {
  readonly rt: Phaser.GameObjects.RenderTexture;
  private value = '';
  private timer?: Phaser.Time.TimerEvent;
  private widths: number[] = [];

  constructor(
    private scene: Phaser.Scene,
    x: number,
    y: number,
    private w: number,
    h: number,
    private baseline: number,
  ) {
    this.rt = scene.add.renderTexture(x, y, w, h).setOrigin(0, 0);
    // 장이 통째로 치워져도(그릇 destroy) 찍던 타이머가 남지 않게
    this.rt.once(Phaser.GameObjects.Events.DESTROY, () => {
      this.timer?.remove();
      this.timer = undefined;
    });
  }

  /** 지금 글 폭 (커서 자리) */
  get textW(): number {
    return this.widths[this.widths.length - 1] ?? 0;
  }

  /** 앞 n 글자 폭 */
  prefixW(n: number): number {
    return n <= 0 ? 0 : (this.widths[Math.min(n, this.widths.length) - 1] ?? 0);
  }

  /** 글을 바꾼다. 같은 앞부분은 그대로 두고, 그 뒤 글자는 찍어 나타낸다 (animate=false 면 바로) */
  setText(text: string, animate: boolean): void {
    if (text === this.value) return;
    this.value = text;
    this.timer?.remove();
    this.timer = undefined;
    const g = glyphPixels(text, this.w - 6, this.baseline);
    this.widths = g.widths;
    this.rt.clear();
    const chars = Array.from(text);
    // 바로 찍을 글자 / 찍어 나타낼 글자 (마지막 글자 — 한글 조합 중에도 마지막만 바뀐다)
    const live = animate && chars.length ? chars.length - 1 : chars.length;
    const now = g.pixels.filter((p) => p.ci < live);
    const later = g.pixels.filter((p) => p.ci >= live).sort((a, b) => a.x - b.x || a.y - b.y);
    this.stampAll(now);
    if (!later.length) return;
    const per = Math.max(4, Math.ceil(later.length / 8));
    let i = 0;
    this.timer = this.scene.time.addEvent({
      delay: 22,
      loop: true,
      callback: () => {
        this.stampAll(later.slice(i, i + per));
        i += per;
        if (i >= later.length) {
          this.timer?.remove();
          this.timer = undefined;
        }
      },
    });
  }

  destroy(): void {
    this.timer?.remove();
    this.rt.destroy();
  }

  private stampAll(ps: { x: number; y: number }[]): void {
    if (!this.rt.active) return;
    const key = R.art.brush;
    for (const p of ps) this.rt.stamp(key, 'tip_d2', p.x + 3, p.y, { tint: R.stamp.ink, originX: 0, originY: 0 });
  }
}

/**
 * 글자 화소 (Galmuri14 28px → 칸이 좁으면 14px — 정수 배만): 2D 캔버스에 그려 알파 > 128 인 점. ci = 몇 번째 글자.
 * widths[i] = 앞 i+1 글자 폭.
 */
function glyphPixels(
  text: string,
  maxW: number,
  baseline: number,
): { pixels: { x: number; y: number; ci: number }[]; widths: number[]; px: number } {
  const chars = Array.from(text);
  if (typeof document === 'undefined' || !chars.length) return { pixels: [], widths: [], px: 28 };
  const c = document.createElement('canvas');
  const ctx = c.getContext('2d', { willReadFrequently: true });
  if (!ctx) return { pixels: [], widths: [], px: 28 };
  let px = 28;
  ctx.font = `${px}px ${fontFamily('title')}`;
  if (ctx.measureText(text).width > maxW) {
    px = 14;
    ctx.font = `${px}px ${fontFamily('title')}`;
  }
  const widths = chars.map((_, i) => Math.ceil(ctx.measureText(chars.slice(0, i + 1).join('')).width));
  const W = Math.max(1, widths[widths.length - 1] + 2);
  const H = baseline + 6;
  c.width = W;
  c.height = H;
  ctx.font = `${px}px ${fontFamily('title')}`;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#fff';
  ctx.fillText(text, 0, baseline);
  const data = ctx.getImageData(0, 0, W, H).data;
  const pixels: { x: number; y: number; ci: number }[] = [];
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      if (data[(y * W + x) * 4 + 3] <= 128) continue;
      let ci = widths.findIndex((w) => x < w);
      if (ci < 0) ci = chars.length - 1;
      pixels.push({ x, y, ci });
    }
  return { pixels, widths, px };
}
