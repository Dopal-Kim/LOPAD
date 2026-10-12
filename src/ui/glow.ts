import Phaser from 'phaser';
import { accentHex, fontFamily, fontSettled } from './kit';
import type { RasterLayer } from './glowRaster';
import { acquireGlyph, releaseGlyph, type Glyph } from './glyphCache';
import { FONT, type FontKind, type GlowStyle, TEXT_STYLES, type TextStyleName } from './theme';
import { textScale } from './uiPrefs';

/**
 * 발광 글자 (계약 `ui-art-kit.md` 1.2절, 38·39라운드).
 * 구조(아래→위): 그늘 ring(맨해튼 거리 2: (±2,0)(0,±2)(±1,±1)) → 할로 ring(4방향 1px) → 글자 본색.
 * Phaser 재현 (A) 정확한 방법: 같은 글을 ① 그늘색 8개 → ② 할로색 4개(알파) → ③ 본색 1개 순으로 겹친다.
 * 62 루프 2 UI D (렉): 예전엔 Phaser Text 13개를 겹쳤으나(글 하나에 측정 13번·다시 그리기 39번·GPU 업로드 39번) 이제는
 * 2D 캔버스 하나에 같은 순서·알파로 찍어 Image 하나로 그린다 (glowRaster.ts). RenderTexture 는 쓰지 않는다
 * (WebGL 에서 Text 가 그려지지 않는 문제) — 캔버스 2D 라 Canvas 폴백에서도 같다.
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
  /**
   * 62 루프 2 (P1-16): 읽는 글(자막·대사·쪽지 등) — 설정 '글자 크기 크게'면 1.5배(실제 3px 도트라 선명). 줄바꿈 폭은 같은 화면 폭을
   * 지키도록 나눈다. scale 1 일 때만
   */
  readable?: boolean;
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
const BODY: [number, number][] = [[0, 0]];

function resolve(scene: Phaser.Scene, c: string | { accentSlot: number }, stageIndex: number): string {
  return typeof c === 'string' ? c : accentHex(scene, stageIndex, c.accentSlot);
}

export class GlowText extends Phaser.GameObjects.Container {
  private content = '';
  private styleName: TextStyleName;
  private opts: Required<Pick<GlowOptions, 'font' | 'align' | 'stageIndex'>> & { wrap?: number; scale: number };
  /** 62 루프 2 UI D: 그늘·할로·본색을 한 장에 구운 텍스처 (glowRaster.ts) — 같은 글·스타일이면 풀에서 빌린다 (glyphCache.ts) */
  private glyph?: Glyph;
  private img: Phaser.GameObjects.Image;
  private readonly owner: Phaser.Game;
  /** 글자(링 제외) 폭·높이 (1배) */
  textW = 0;
  textH = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, text: string, style: TextStyleName, opts: GlowOptions = {}) {
    super(scene, x, y);
    this.styleName = style;
    const base = opts.scale ?? 1;
    const k = opts.readable && base === 1 ? textScale() : 1;
    this.opts = {
      font: opts.font ?? 'body',
      scale: base * k,
      align: opts.align ?? 'left',
      stageIndex: opts.stageIndex ?? 0,
      wrap: opts.wrap && k !== 1 ? Math.max(40, Math.floor(opts.wrap / k)) : opts.wrap,
    };
    this.owner = scene.game;
    this.img = new Phaser.GameObjects.Image(scene, 0, 0, '__DEFAULT').setOrigin(0, 0);
    this.add(this.img);
    this.setScale(this.opts.scale);
    scene.add.existing(this);
    this.once(Phaser.GameObjects.Events.DESTROY, () => {
      if (this.glyph) releaseGlyph(this.owner, this.glyph);
      this.glyph = undefined;
    });
    this.content = '\u0000';
    this.setText(text);
  }

  get style(): GlowStyle {
    return TEXT_STYLES[this.styleName];
  }

  /** 글이 바뀔 때만 다시 그린다 */
  setText(text: string): this {
    if (text === this.content) return this;
    this.content = text;
    this.redraw();
    this.setSize(this.textW + RING * 2, this.textH + RING * 2);
    if (this.input)
      (this.input.hitArea as Phaser.Geom.Rectangle).setTo(this.width / 2, this.height / 2, this.width, this.height);
    return this;
  }

  setGlowStyle(style: TextStyleName): this {
    if (style === this.styleName) return this;
    this.styleName = style;
    this.redraw();
    return this;
  }

  /** 층이 바뀌면 강조색 할로를 다시 칠한다 (accentSlot 을 쓰는 스타일만) */
  setStageIndex(i: number): this {
    if (i === this.opts.stageIndex) return this;
    this.opts.stageIndex = i;
    const s = this.style;
    const usesAccent = typeof s.body !== 'string' || (s.halo && typeof s.halo.color !== 'string');
    if (usesAccent) this.redraw();
    return this;
  }

  /**
   * 마우스 입력: 글자 상자(링 포함) 사각형.
   * Container 의 입력 판정은 지역 좌표에 displayOrigin(= 폭·높이의 절반)을 더해 검사하므로
   * 사각형을 (w/2, h/2) 에서 시작해야 글자 상자와 겹친다 (45라운드 수정: 이전엔 반 칸 왼쪽 위로 밀려 있었다)
   */
  makeInteractive(): this {
    this.setInteractive(
      new Phaser.Geom.Rectangle(this.width / 2, this.height / 2, this.width, this.height),
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

  /** 겹 (아래→위): 그늘 → 할로 → 본색. 할로가 없는 스타일은 그늘 ring 이 글자 바로 바깥 1px (4방향) */
  private layers(): RasterLayer[] {
    const st = this.style;
    const si = this.opts.stageIndex;
    const out: RasterLayer[] = [];
    if (st.shade) out.push({ color: st.shade.color, alpha: st.shade.alpha, offsets: st.halo ? SHADE_8 : HALO_4 });
    if (st.halo) out.push({ color: resolve(this.scene, st.halo.color, si), alpha: st.halo.alpha, offsets: HALO_4 });
    out.push({ color: resolve(this.scene, st.body, si), alpha: st.bodyAlpha, offsets: BODY });
    return out;
  }

  /** 이 글·스타일의 구운 텍스처를 빌려 건다 (없으면 공유 래스터에 한 번 그리고 겹마다 색을 입혀 굽고 한 번 올린다) */
  private redraw(): void {
    const font = this.opts.font;
    const f = FONT[font];
    const style = {
      fontFamily: fontFamily(font),
      px: f.px,
      align: this.opts.align,
      wrap: this.opts.wrap,
      settled: fontSettled(font),
    };
    const g = acquireGlyph(this.scene, this.content, style, RING, this.content.length === 0 ? [] : this.layers());
    // 새 것을 먼저 빌리고 옛것을 돌려준다 (같은 것이면 풀에서 지워지지 않게)
    if (this.glyph) releaseGlyph(this.owner, this.glyph);
    this.glyph = g;
    this.textW = g.textW;
    this.textH = g.textH;
    // Phaser 형식은 키(문자열)만 받지만 텍스처 관리자는 Texture 객체도 그대로 돌려준다 (목록 밖 텍스처)
    this.img.setTexture(g.tex as unknown as string);
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
