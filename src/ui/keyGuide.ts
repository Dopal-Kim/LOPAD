import Phaser from 'phaser';
import { GlowText } from './glow';
import { KeyCap } from './keycap';
import { type KeyGlyph, type KeyGuideItem, KEY_GLYPH, glyphWidth, parseKey, rowOffsets } from './keyGuideView';
import { swatch } from './StructureHud';
import { GRAY, type TextStyleName, hexToNum } from './theme';
import { KEY_GUIDE } from './themeR61';

/**
 * 마우스 그림 11×16 (윤곽 'x', 왼·오른 단추 칸 'l'·'r', 몸 'b'). 홀드는 맨 아래 2줄 'h' 에 막대.
 * 단추 칸은 눌린 쪽만 층 강조, 나머지는 몸과 같은 G02.
 */
const MOUSE = [
  '..xxxxxxx..',
  '.xlllxrrrx.',
  'xllllxrrrrx',
  'xllllxrrrrx',
  'xllllxrrrrx',
  'xxxxxxxxxxx',
  'xbbbbbbbbbx',
  'xbbbbbbbbbx',
  'xbbbbbbbbbx',
  'xbbbbbbbbbx',
  'xbbbbbbbbbx',
  '.xbbbbbbbx.',
  '..xxxxxxx..',
  '...........',
  'hhhhhhhhhhh',
  'hhhhhhhhhhh',
];

/**
 * 마우스 키 그림 (61라운드 P10). 스킬 버튼 규약대로 Container → Graphics. 좌클릭·우클릭은 눌리는 단추를 층 강조로,
 * 홀드(좌 홀드 = 고유 자원 기술)는 아래에 길게 누르기 막대(2/3 켜짐)를 더 그린다.
 */
export class MouseGlyph extends Phaser.GameObjects.Container {
  private g: Phaser.GameObjects.Graphics;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    glyph: Extract<KeyGlyph, { kind: 'mouse' }>,
    stageIndex = 0,
    dim = false,
  ) {
    super(scene, x, y);
    this.g = scene.add.graphics();
    this.add(this.g);
    this.draw(glyph, stageIndex, dim);
    this.setSize(KEY_GLYPH.mouseW, KEY_GLYPH.h);
    scene.add.existing(this);
  }

  private draw(glyph: Extract<KeyGlyph, { kind: 'mouse' }>, si: number, dim: boolean): void {
    const g = this.g.clear();
    const edge = hexToNum(dim ? GRAY[5] : GRAY[8]);
    const body = hexToNum(GRAY[2]);
    const lit = dim ? hexToNum(GRAY[6]) : swatch(this.scene, si, { slot: KEY_GUIDE.litSlot });
    const off = hexToNum(GRAY[4]);
    const holdOn = Math.round((KEY_GLYPH.mouseW * 2) / 3);
    MOUSE.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const c = row[x];
        let color: number | null = null;
        if (c === 'x') color = edge;
        else if (c === 'b') color = body;
        else if (c === 'l') color = glyph.button === 'left' ? lit : body;
        else if (c === 'r') color = glyph.button === 'right' ? lit : body;
        else if (c === 'h' && glyph.hold) color = x < holdOn ? lit : off;
        if (color !== null) g.fillStyle(color, 1).fillRect(x, y, 1, 1);
      }
    });
  }
}

export interface KeyHintOptions {
  /** 잉크(HUD·어두운 바탕) / 종이(일기장) — 동작 이름 글자 스타일이 다르다 */
  surface?: 'ink' | 'page';
  stageIndex?: number;
}

/**
 * 키 이름 하나 → 키 그림 (마우스 단추·홀드 막대 / 키캡, 넓은 키는 최소 폭). (0,0) 왼쪽 위, 높이 16.
 * 튜토리얼 안내·단계 카드·일기장·시험장이 같이 쓴다 (61라운드 4동사 key: '좌클릭'·'우클릭'·'Space'·'좌클릭 길게').
 */
export function keyGlyph(
  scene: Phaser.Scene,
  key: string,
  stageIndex = 0,
  dim = false,
): { obj: Phaser.GameObjects.Container; width: number } {
  const glyph = parseKey(key);
  if (glyph.kind === 'mouse')
    return { obj: new MouseGlyph(scene, 0, 0, glyph, stageIndex, dim), width: KEY_GLYPH.mouseW };
  const cap = new KeyCap(scene, 0, 0, glyph.label, dim);
  // 넓은 키(Space)는 최소 폭까지 늘린다 — KeyCap 은 글 폭만큼이라 가운데 맞춤은 KeyCap 이 한다
  const w = glyphWidth(glyph, cap.width - KEY_GLYPH.padX * 2);
  if (w > cap.width) cap.setMinWidth(w);
  return { obj: cap, width: cap.width };
}

/**
 * 키캡 안내 한 줄: 키 그림(키캡·마우스) 여럿 + 동작 이름. Container → (Graphics·KeyCap) → 글.
 * (x, y) 는 왼쪽 위, 높이 16. `w` 는 전체 폭.
 */
export class KeyHint extends Phaser.GameObjects.Container {
  private glyphs: Phaser.GameObjects.Container[] = [];
  private label: GlowText;
  /** 키 그림 묶음 폭 (세로 배치에서 이름 칸을 맞출 때) */
  keysW = 0;
  /** 전체 폭 (`w` 는 Phaser Transform 좌표라 쓰지 않는다) */
  boxW = 0;

  constructor(scene: Phaser.Scene, x: number, y: number, item: KeyGuideItem, opts: KeyHintOptions = {}) {
    super(scene, x, y);
    const si = opts.stageIndex ?? 0;
    const dim = Boolean(item.dim);
    const widths: number[] = [];
    for (const k of item.keys) {
      const gl = keyGlyph(scene, k, si, dim);
      this.glyphs.push(gl.obj);
      widths.push(gl.width);
    }
    const { xs, w } = rowOffsets(widths, KEY_GUIDE.keyGap);
    this.glyphs.forEach((gl, i) => gl.setPosition(xs[i], 0));
    this.keysW = w;
    const style: TextStyleName =
      opts.surface === 'page' ? (dim ? 'page_faint' : 'page_body') : dim ? 'ink_faint' : 'ink_body';
    this.label = new GlowText(scene, 0, 0, item.label, style, { stageIndex: si });
    this.add([...this.glyphs, this.label]);
    this.setLabelX(w + (w > 0 ? KEY_GUIDE.labelGap : 0));
    scene.add.existing(this);
  }

  /** 이름 시작 x (세로 배치에서 줄마다 같은 칸으로) */
  setLabelX(x: number): this {
    // 글 상자(링 2px 포함) 높이 16 — 키 높이와 같아 위쪽을 맞춘다
    this.label.setPosition(Math.round(x), 0);
    this.boxW = Math.round(x) + this.label.displayWidth;
    this.setSize(this.boxW, KEY_GLYPH.h);
    return this;
  }
}

/**
 * 키캡 안내 묶음: 여러 줄을 가로(`row`, 동작 사이 12) 또는 세로(`column`, 이름 칸을 맞춤)로. 세로는 `cols` 단으로 나눌 수 있다
 * (차례대로 왼쪽 → 오른쪽, 단마다 이름 칸을 맞춤). `items` 만 바꾸면 다시 만든다.
 * 4동사 데이터는 `verbItems()` 로 만들어 넘긴다 (keyGuideView.ts).
 */
export class KeyGuide extends Phaser.GameObjects.Container {
  private hints: KeyHint[] = [];
  private sig = '';
  /** 전체 폭·높이 (`w` 는 Phaser Transform 좌표라 쓰지 않는다) */
  boxW = 0;
  boxH = 0;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    private layout: 'row' | 'column' = 'column',
    private opts: KeyHintOptions & { cols?: number } = {},
  ) {
    super(scene, x, y);
    scene.add.existing(this);
  }

  setItems(items: KeyGuideItem[]): this {
    const sig = JSON.stringify([items, this.opts.stageIndex ?? 0]);
    if (sig === this.sig) return this;
    this.sig = sig;
    for (const h of this.hints) h.destroy();
    this.hints = items.map((it) => new KeyHint(this.scene, 0, 0, it, this.opts));
    this.add(this.hints);
    if (this.layout === 'row') {
      const { xs, w } = rowOffsets(
        this.hints.map((h) => h.boxW),
        KEY_GUIDE.itemGap,
      );
      this.hints.forEach((h, i) => h.setPosition(xs[i], 0));
      this.boxW = w;
      this.boxH = this.hints.length ? KEY_GLYPH.h : 0;
    } else {
      const cols = Math.max(1, Math.floor(this.opts.cols ?? 1));
      const colOf = (i: number): KeyHint[] => this.hints.filter((_, j) => j % cols === i);
      const colW: number[] = [];
      for (let c = 0; c < cols; c++) {
        const hs = colOf(c);
        // 한 단이면 이름 칸을 맞추고, 여러 단이면 키 그림 바로 뒤에 (Space 처럼 넓은 키가 단 전체를 밀지 않게)
        if (cols === 1) {
          const labelX = Math.max(0, ...hs.map((h) => h.keysW)) + KEY_GUIDE.labelGap;
          for (const h of hs) h.setLabelX(labelX);
        }
        colW.push(Math.max(0, ...hs.map((h) => h.boxW)));
      }
      const { xs, w } = rowOffsets(colW, KEY_GUIDE.itemGap);
      this.hints.forEach((h, i) => h.setPosition(xs[i % cols], Math.floor(i / cols) * KEY_GUIDE.rowH));
      const rows = Math.ceil(this.hints.length / cols);
      this.boxW = w;
      this.boxH = rows ? (rows - 1) * KEY_GUIDE.rowH + KEY_GLYPH.h : 0;
    }
    this.setSize(this.boxW, this.boxH);
    return this;
  }
}
