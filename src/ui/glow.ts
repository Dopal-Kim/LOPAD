import Phaser from 'phaser';
import { accentHex, fontFamily } from './kit';
import { FONT, type FontKind, type GlowStyle, TEXT_STYLES, type TextStyleName } from './theme';

/**
 * 발광 글자 (계약 `ui-art-kit.md` 1.2절, 38·39라운드).
 * 구조(아래→위): 그늘 ring(맨해튼 거리 2: (±2,0)(0,±2)(±1,±1)) → 할로 ring(4방향 1px) → 글자 본색.
 * Phaser 재현 (A) 정확한 방법: 같은 글을 Text 로 복제해 ① 그늘색 8개 → ② 할로색 4개(알파) → ③ 본색 1개 순으로 겹친다.
 * (RenderTexture 에 굽는 방식은 WebGL 에서 Text 가 그려지지 않는 문제가 있어 Container 복제로 둔다.)
 * 8방향(대각) 팽창은 쓰지 않는다 — 1px 획 틈이 메워진다. 흐림(blur) 없음. 모든 좌표 정수.
 * 제목은 Galmuri11/14 를 `scale 2` 정수 확대로 키운다 (비트맵 글꼴은 정수 배수에서만 선명).
 */

export interface GlowOptions {
  font?: FontKind;
  scale?: 1 | 2;
  /** 줄바꿈 폭 (1배 픽셀). 없으면 한 줄 */
  wrap?: number;
  align?: 'left' | 'center' | 'right';
  /** 층 강조색 (스타일에 accentSlot 이 있을 때). 0 = 1층 */
  stageIndex?: number;
}

/** 할로·그늘 때문에 글자 상자가 사방 2px 커진다 */
export const RING = 2;
const SHADE_8: [number, number][] = [
  [-2, 0],
  [2, 0],
  [0, -2],
  [0, 2],
  [-1, -1],
  [1, -1],
  [-1, 1],
  [1, 1],
];
const HALO_4: [number, number][] = [
  [-1, 0],
  [1, 0],
  [0, -1],
  [0, 1],
];

function resolve(scene: Phaser.Scene, c: string | { accentSlot: number }, stageIndex: number): string {
  return typeof c === 'string' ? c : accentHex(scene, stageIndex, c.accentSlot);
}

export class GlowText extends Phaser.GameObjects.Container {
  private content = '';
  private styleName: TextStyleName;
  private opts: Required<Pick<GlowOptions, 'font' | 'scale' | 'align' | 'stageIndex'>> & { wrap?: number };
  private shade: Phaser.GameObjects.Text[] = [];
  private halo: Phaser.GameObjects.Text[] = [];
  private main: Phaser.GameObjects.Text;
  /** 글자(링 제외) 폭·높이 (1배) */
  textW = 0;
  textH = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, text: string, style: TextStyleName, opts: GlowOptions = {}) {
    super(scene, x, y);
    this.styleName = style;
    this.opts = {
      font: opts.font ?? 'body',
      scale: opts.scale ?? 1,
      align: opts.align ?? 'left',
      stageIndex: opts.stageIndex ?? 0,
      wrap: opts.wrap,
    };
    const mk = (dx: number, dy: number): Phaser.GameObjects.Text => {
      const t = scene.add.text(RING + dx, RING + dy, '', this.textStyle()).setOrigin(0, 0);
      this.add(t);
      return t;
    };
    for (const [dx, dy] of SHADE_8) this.shade.push(mk(dx, dy));
    for (const [dx, dy] of HALO_4) this.halo.push(mk(dx, dy));
    this.main = mk(0, 0);
    this.setScale(this.opts.scale);
    scene.add.existing(this);
    this.content = '\u0000';
    this.setText(text);
  }

  get style(): GlowStyle {
    return TEXT_STYLES[this.styleName];
  }

  private textStyle(): Phaser.Types.GameObjects.Text.TextStyle {
    const f = FONT[this.opts.font];
    return {
      fontFamily: fontFamily(this.opts.font),
      fontSize: `${f.px}px`,
      color: '#ffffff',
      align: this.opts.align,
      // 할로·그늘 때문에 줄 간격 ≥ 글꼴 높이 + 4 (계약 1.2절)
      lineSpacing: 4,
      wordWrap: this.opts.wrap ? { width: this.opts.wrap, useAdvancedWrap: false } : undefined,
    };
  }

  private all(): Phaser.GameObjects.Text[] {
    return [...this.shade, ...this.halo, this.main];
  }

  /** 글이 바뀔 때만 다시 그린다 */
  setText(text: string): this {
    if (text === this.content) return this;
    this.content = text;
    for (const t of this.all()) t.setText(text);
    this.textW = Math.ceil(this.main.width);
    this.textH = Math.ceil(this.main.height);
    this.setSize(this.textW + RING * 2, this.textH + RING * 2);
    if (this.input) this.input.hitArea.setSize(this.width, this.height);
    this.applyStyle();
    return this;
  }

  setGlowStyle(style: TextStyleName): this {
    if (style === this.styleName) return this;
    this.styleName = style;
    this.applyStyle();
    return this;
  }

  /** 층이 바뀌면 강조색 할로를 다시 칠한다 (accentSlot 을 쓰는 스타일만) */
  setStageIndex(i: number): this {
    if (i === this.opts.stageIndex) return this;
    this.opts.stageIndex = i;
    const s = this.style;
    const usesAccent = typeof s.body !== 'string' || (s.halo && typeof s.halo.color !== 'string');
    if (usesAccent) this.applyStyle();
    return this;
  }

  /** 마우스 입력: 글자 상자(링 포함) 사각형 */
  makeInteractive(): this {
    this.setInteractive(
      new Phaser.Geom.Rectangle(0, 0, this.width, this.height),
      Phaser.Geom.Rectangle.Contains,
      false,
    );
    if (this.input) this.input.cursor = 'pointer';
    return this;
  }

  /** 가운데 정렬 등: origin 대신 정수 위치로 맞춘다 (비정수 origin 은 흐려진다) */
  placeCenter(cx: number, y: number): this {
    this.setPosition(Math.round(cx - this.displayWidth / 2), y);
    return this;
  }
  placeRight(right: number, y: number): this {
    this.setPosition(Math.round(right - this.displayWidth), y);
    return this;
  }

  private applyStyle(): void {
    const st = this.style;
    const scene = this.scene;
    const si = this.opts.stageIndex;
    const empty = this.content.length === 0;
    if (st.shade) {
      // 할로가 없는 스타일은 그늘 ring 이 글자 바로 바깥 1px (4방향)
      const offsets = st.halo ? SHADE_8 : HALO_4;
      this.shade.forEach((t, i) => {
        const o = offsets[i];
        t.setVisible(!empty && Boolean(o));
        if (o)
          t.setPosition(RING + o[0], RING + o[1])
            .setColor(st.shade!.color)
            .setAlpha(st.shade!.alpha);
      });
    } else for (const t of this.shade) t.setVisible(false);
    if (st.halo) {
      const color = resolve(scene, st.halo.color, si);
      for (const t of this.halo) t.setVisible(!empty).setColor(color).setAlpha(st.halo.alpha);
    } else for (const t of this.halo) t.setVisible(false);
    this.main
      .setVisible(!empty)
      .setColor(resolve(scene, st.body, si))
      .setAlpha(st.bodyAlpha);
  }
}

/** 공용 헬퍼: 발광 글자 한 줄. (x,y) 는 글자 상자(링 포함) 왼쪽 위 */
export function glowText(
  scene: Phaser.Scene,
  x: number,
  y: number,
  text: string,
  style: TextStyleName,
  opts?: GlowOptions,
): GlowText {
  return new GlowText(scene, x, y, text, style, opts);
}
