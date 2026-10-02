import Phaser from 'phaser';
import { ACCENT_FIRST_SLOT, FLOOR1_RAMP, FONT, FONT_FILES, GRAY, LAYOUT, hexToNum } from './theme';

/**
 * UI 키트 로더·조립 헬퍼 (계약 `contracts/ui-art-kit.md` v0.4 §2·§4).
 * 파일은 `assets/ui/kit/`(아트 산출물 사본) 에서 `assets-game/ui/kit/...` 로 읽는다.
 * 9-slice 는 Phaser NineSlice(WebGL 전용) 대신 Image 9장 Container 로 조립해 Canvas 폴백에서도 그려진다.
 */

const BASE = 'assets-game/ui/kit/';
const K = (name: string): string => `ui-kit-${name}`;

/** 텍스처 키 */
export const KIT = {
  bookFrame: K('book_frame'),
  panelPaper: K('panel_paper'),
  paperTile: K('paper_tile'),
  stains: K('stains'),
  spine: K('spine'),
  panelInk: K('panel_ink'),
  minimapFrame: K('minimap_frame'),
  gaugeFrame: K('gauge_frame'),
  gaugeBoss: K('gauge_boss'),
  gaugeFill: K('gauge_fill'),
  gaugeFillGray: K('gauge_fill_gray'),
  icons: K('icons'),
  cursor: K('cursor'),
  cursorLight: K('cursor_light'),
  rule: K('rule'),
  ruleLight: K('rule_light'),
  titleDiary: K('title_diary'),
  diaryClosed: K('diary_closed'),
  stampDead: K('stamp_dead'),
  stampClear: K('stamp_clear'),
  palette: K('palette'),
} as const;

/** 9-slice 수치 (계약 §2.1·§2.2 JSON 과 같음) */
export const SLICE = {
  bookFrame: { l: 32, r: 32, t: 32, b: 32, inner: 16 },
  panelPaper: { l: 24, r: 24, t: 24, b: 24, inner: 12 },
  panelInk: { l: 12, r: 12, t: 12, b: 12, inner: 5 },
  minimapFrame: { l: 10, r: 10, t: 10, b: 10, inner: 4 },
  gaugeFrame: { l: 4, r: 4, t: 1, b: 1, inner: 2, h: 10, fillInsetX: 2, fillInsetY: 1 },
  gaugeBoss: { l: 8, r: 8, t: 3, b: 3, inner: 5, h: 14, fillInsetX: 5, fillInsetY: 3 },
} as const;

/** 아이콘 시트 프레임 이름 (icons.json). 16×16 칸, 미니맵 글리프는 칸 안 (+4,+4) 8×8 */
export const ICON = {
  hp: 'icon_hp',
  gold: 'icon_gold',
  potion: 'icon_potion',
  souls: 'icon_souls',
  sense: 'icon_sense',
  save: 'icon_save',
  sound: 'icon_sound',
  mute: 'icon_mute',
  boss: 'icon_boss',
  exit: 'icon_exit',
  miniStart: 'mini_start',
  miniTrial: 'mini_trial',
  miniRest: 'mini_rest',
  miniBoss: 'mini_boss',
} as const;
const ICON_FRAMES: Record<string, [number, number, number, number]> = {
  icon_hp: [0, 0, 16, 16],
  icon_gold: [16, 0, 16, 16],
  icon_potion: [32, 0, 16, 16],
  icon_souls: [48, 0, 16, 16],
  icon_sense: [64, 0, 16, 16],
  icon_save: [80, 0, 16, 16],
  icon_sound: [96, 0, 16, 16],
  icon_mute: [112, 0, 16, 16],
  icon_boss: [0, 16, 16, 16],
  icon_exit: [16, 16, 16, 16],
  mini_start: [36, 20, 8, 8],
  mini_trial: [52, 20, 8, 8],
  mini_rest: [68, 20, 8, 8],
  mini_boss: [84, 20, 8, 8],
};
export const STAIN = ['stain_ring', 'stain_burn', 'stain_blot', 'stain_smudge'] as const;

/** 무기 아이콘 (30라운드, `assets/ui/weapons/<id>_icon.png`). 스냅샷에 `weapon.id` 가 없어 이름으로 매핑한다 */
export const WEAPON_ICON_IDS: Record<string, string> = {
  '사무라이 칼': 'katana',
  대검: 'greatsword',
  단검: 'dagger',
  활: 'bow',
};
export const weaponIconKey = (id: string): string => `ui-weapon-${id}`;

/**
 * 48라운드 노드 지도 아이콘 시트 (아트 계약 `art-assets.md` §6.5, 승인 #18): 32×32, 열 = 종류
 * (journey, battle, shop, rest, event, boss), 행 0 = 기본 · 1 = 지나옴(식음) · 2 = 잠김(흐림).
 * 아트 산출물 사본 `assets/ui/kit/node_icons.png` (48라운드 복사). `available` 을 false 로 두면 Graphics 마름모 +
 * 키트 글리프 폴백으로 그린다 (없는 파일을 읽어 404 를 내지 않게 플래그로 둔다).
 * 강조 1점(슬롯 20~22)은 1층 램프로 그려져 있다 — 2층부터 `nodeIconKey` 가 그 층 램프로 바꾼 사본을 만든다.
 */
export const NODE_ICON_SHEET: { key: string; file: string; size: number; order: readonly string[]; available: boolean } = {
  key: K('node_icons'),
  file: 'node_icons',
  size: 32,
  order: ['journey', 'battle', 'shop', 'rest', 'event', 'boss'],
  available: true,
};

/** 노드 아이콘 시트 텍스처 키 (층 강조색 적용). 1층·시트 없음이면 원본 키. 프레임 = 행 × 6 + 열 */
export function nodeIconKey(scene: Phaser.Scene, stageIndex: number): string {
  const base = NODE_ICON_SHEET.key;
  if (stageIndex <= 0 || !scene.textures.exists(base)) return base;
  const key = `${base}@${stageIndex}`;
  if (scene.textures.exists(key)) return key;
  const src = scene.textures.get(base).getSourceImage() as HTMLImageElement | HTMLCanvasElement;
  const tex = scene.textures.createCanvas(key, src.width, src.height);
  if (!tex) return base;
  const ctx = tex.getContext();
  ctx.drawImage(src, 0, 0);
  const img = ctx.getImageData(0, 0, src.width, src.height);
  const swap = new Map<number, number>();
  for (let slot = ACCENT_FIRST_SLOT; slot <= ACCENT_FIRST_SLOT + 11; slot++)
    swap.set(hexToNum(accentHex(scene, 0, slot)), hexToNum(accentHex(scene, stageIndex, slot)));
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] === 0) continue;
    const to = swap.get((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]);
    if (to === undefined) continue;
    d[i] = (to >> 16) & 255;
    d[i + 1] = (to >> 8) & 255;
    d[i + 2] = to & 255;
  }
  ctx.putImageData(img, 0, 0);
  const n = NODE_ICON_SHEET.size;
  const cols = Math.floor(src.width / n);
  const rows = Math.floor(src.height / n);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) tex.add(r * cols + c, 0, c * n, r * n, n, n);
  tex.refresh();
  return key;
}

/** 씬 preload 에서 호출. 이미 있는 텍스처는 건너뛴다 (UI 씬 어느 것이 먼저 떠도 된다) */
export function preloadKit(scene: Phaser.Scene): void {
  const img = (key: string, file: string) => {
    if (!scene.textures.exists(key)) scene.load.image(key, `${BASE}${file}.png`);
  };
  img(KIT.bookFrame, 'book_frame');
  img(KIT.panelPaper, 'panel_paper');
  img(KIT.paperTile, 'paper_tile');
  img(KIT.spine, 'spine');
  img(KIT.panelInk, 'panel_ink');
  img(KIT.minimapFrame, 'minimap_frame');
  img(KIT.gaugeFrame, 'gauge_frame');
  img(KIT.gaugeBoss, 'gauge_boss');
  img(KIT.gaugeFill, 'gauge_fill');
  img(KIT.gaugeFillGray, 'gauge_fill_gray');
  img(KIT.rule, 'rule');
  img(KIT.ruleLight, 'rule_light');
  img(KIT.titleDiary, 'title_diary');
  img(KIT.diaryClosed, 'diary_closed');
  img(KIT.stampDead, 'stamp_dead');
  img(KIT.stampClear, 'stamp_clear');
  if (!scene.textures.exists(KIT.icons)) scene.load.image(KIT.icons, `${BASE}icons.png`);
  if (!scene.textures.exists(KIT.stains))
    scene.load.spritesheet(KIT.stains, `${BASE}stains.png`, { frameWidth: 32, frameHeight: 32 });
  if (!scene.textures.exists(KIT.cursor))
    scene.load.spritesheet(KIT.cursor, `${BASE}cursor.png`, { frameWidth: 8, frameHeight: 8 });
  if (!scene.textures.exists(KIT.cursorLight))
    scene.load.spritesheet(KIT.cursorLight, `${BASE}cursor_light.png`, { frameWidth: 8, frameHeight: 8 });
  if (NODE_ICON_SHEET.available && !scene.textures.exists(NODE_ICON_SHEET.key))
    scene.load.spritesheet(NODE_ICON_SHEET.key, `${BASE}${NODE_ICON_SHEET.file}.png`, {
      frameWidth: NODE_ICON_SHEET.size,
      frameHeight: NODE_ICON_SHEET.size,
    });
  if (!scene.cache.json.exists(KIT.palette)) scene.load.json(KIT.palette, `${BASE}palette.json`);
  for (const id of Object.values(WEAPON_ICON_IDS)) {
    const key = weaponIconKey(id);
    if (!scene.textures.exists(key)) scene.load.image(key, `assets-game/ui/weapons/${id}_icon.png`);
  }
}

/** create 에서 호출: 아이콘 프레임·커서 애니 등록 (1회) */
export function setupKit(scene: Phaser.Scene): void {
  if (scene.textures.exists(KIT.icons)) {
    const tex = scene.textures.get(KIT.icons);
    for (const [name, [x, y, w, h]] of Object.entries(ICON_FRAMES)) if (!tex.has(name)) tex.add(name, 0, x, y, w, h);
  }
  for (const key of [KIT.cursor, KIT.cursorLight]) {
    if (scene.textures.exists(key) && !scene.anims.exists(key)) {
      scene.anims.create({
        key,
        frames: [
          { key, frame: 0, duration: 420 },
          { key, frame: 1, duration: 260 },
        ],
        repeat: -1,
      });
    }
  }
}

// ---------------------------------------------------------------------------------------------
// 글꼴 (34·39라운드): Galmuri11 은 style.css @font-face, Galmuri14 는 여기서 FontFace 로 직접 등록
let fontPromise: Promise<void> | null = null;
const fontOk = new Map<string, boolean>();

export function fontsReady(): Promise<void> {
  if (fontPromise) return fontPromise;
  const fonts = typeof document !== 'undefined' ? document.fonts : undefined;
  if (!fonts) return (fontPromise = Promise.resolve());
  const jobs = Object.values(FONT).map(async (f) => {
    const spec = `${f.px}px '${f.family}'`;
    try {
      // 선언이 없으면(style.css 에 없는 Galmuri14 등) UI 소유 파일로 직접 등록
      if (!fonts.check(spec) && typeof FontFace !== 'undefined') {
        let declared = false;
        fonts.forEach((face) => {
          if (face.family.replace(/["']/g, '') === f.family) declared = true;
        });
        if (!declared) {
          const face = new FontFace(f.family, `url(${FONT_FILES[f.family]}) format('woff2')`, { display: 'block' });
          fonts.add(face);
        }
      }
      const faces = await fonts.load(spec);
      fontOk.set(f.family, faces.length > 0 && fonts.check(spec));
    } catch {
      fontOk.set(f.family, false);
    }
  });
  const timeout = new Promise<void>((r) => setTimeout(r, 3000));
  fontPromise = Promise.race([Promise.all(jobs).then(() => undefined), timeout]);
  return fontPromise;
}

/** 로드된 글꼴이면 그 이름, 아니면 폴백 monospace */
export function fontFamily(kind: keyof typeof FONT): string {
  const f = FONT[kind];
  return fontOk.get(f.family) === false ? 'monospace' : f.family;
}

// ---------------------------------------------------------------------------------------------
// 팔레트: 층 강조 램프
interface PaletteJson {
  floors?: { floor: number; ramp: string[] }[];
}
let paletteCache: PaletteJson | null = null;

/** 층(0부터) 강조 램프 슬롯(16~27) 색. 팔레트가 없으면 1층 램프 */
export function accentHex(scene: Phaser.Scene, stageIndex: number, slot: number): string {
  if (!paletteCache && scene.cache.json.exists(KIT.palette))
    paletteCache = scene.cache.json.get(KIT.palette) as PaletteJson;
  const floors = paletteCache?.floors ?? [];
  const idx = Math.max(0, Math.min(ACCENT_FIRST_SLOT + 11, slot) - ACCENT_FIRST_SLOT);
  const ramp = floors[Math.max(0, Math.min(floors.length - 1, stageIndex))]?.ramp;
  return ramp?.[idx] ?? FLOOR1_RAMP[idx];
}

// ---------------------------------------------------------------------------------------------
// 9-slice (Image 9장) — 모든 좌표 정수
interface Slice9 {
  l: number;
  r: number;
  t: number;
  b: number;
}

/** 텍스처에 9조각 프레임을 등록하고 이름 접두어를 돌려준다 */
function sliceFrames(scene: Phaser.Scene, key: string, s: Slice9): string[] {
  const tex = scene.textures.get(key);
  const src = tex.getSourceImage() as { width: number; height: number };
  const W = src.width;
  const H = src.height;
  const xs = [0, s.l, W - s.r];
  const ws = [s.l, W - s.l - s.r, s.r];
  const ys = [0, s.t, H - s.b];
  const hs = [s.t, H - s.t - s.b, s.b];
  const names: string[] = [];
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const name = `s9-${row}${col}`;
      if (!tex.has(name)) tex.add(name, 0, xs[col], ys[row], Math.max(1, ws[col]), Math.max(1, hs[row]));
      names.push(name);
    }
  }
  return names;
}

/** 9-slice 패널. 반환 Container 의 (x,y) 가 왼쪽 위. `resize` 로 다시 늘릴 수 있다 */
export class NinePanel extends Phaser.GameObjects.Container {
  private parts: Phaser.GameObjects.Image[] = [];
  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    key: string,
    private slice: Slice9,
    w: number,
    h: number,
  ) {
    super(scene, x, y);
    const names = sliceFrames(scene, key, slice);
    for (const n of names) {
      const img = scene.add.image(0, 0, key, n).setOrigin(0, 0);
      this.parts.push(img);
      this.add(img);
    }
    this.resize(w, h);
    scene.add.existing(this);
  }

  resize(w: number, h: number): this {
    const s = this.slice;
    const W = Math.max(w, s.l + s.r);
    const H = Math.max(h, s.t + s.b);
    const xs = [0, s.l, W - s.r];
    const ws = [s.l, W - s.l - s.r, s.r];
    const ys = [0, s.t, H - s.b];
    const hs = [s.t, H - s.t - s.b, s.b];
    this.parts.forEach((img, i) => {
      const row = Math.floor(i / 3);
      const col = i % 3;
      img.setPosition(xs[col], ys[row]);
      const vw = ws[col];
      const vh = hs[row];
      img.setVisible(vw > 0 && vh > 0);
      if (vw > 0 && vh > 0) img.setDisplaySize(vw, vh);
    });
    this.setSize(W, H);
    return this;
  }
}

export function inkPanel(scene: Phaser.Scene, x: number, y: number, w: number, h: number): NinePanel {
  return new NinePanel(scene, x, y, KIT.panelInk, SLICE.panelInk, w, h);
}

// ---------------------------------------------------------------------------------------------
// 종이 페이지·책 틀 (계약 §2.1 조립 순서: book_frame → panel_paper → paper_tile → stains → 글)

/** 고정 seed 의 작은 난수 (얼룩 배치용, 화면마다 같은 자리) */
function seededRandom(seed: string): () => number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
}

/** 페이지 한 장: panel_paper + paper_tile + 얼룩 3~5 (seed 고정). (x,y) 왼쪽 위, 크기 w×h */
export function paperPage(scene: Phaser.Scene, x: number, y: number, w: number, h: number, seed: string): void {
  new NinePanel(scene, x, y, KIT.panelPaper, SLICE.panelPaper, w, h);
  const inset = SLICE.panelPaper.inner;
  const iw = w - inset * 2;
  const ih = h - inset * 2;
  // panel_paper 가운데 띠 위에 질감 타일. 패널 가장자리의 손때 띠·찢김은 타일보다 위에 있어야 하므로
  // 타일을 inner 안에만 깐다 (계약: inner 안에 tileSprite)
  scene.add.tileSprite(x + inset, y + inset, iw, ih, KIT.paperTile).setOrigin(0, 0);
  if (!scene.textures.exists(KIT.stains)) return;
  const rnd = seededRandom(seed);
  const count = 3 + Math.floor(rnd() * 3); // 3~5
  let blots = 0;
  for (let i = 0; i < count; i++) {
    let frame = Math.floor(rnd() * 4);
    if (frame === 2 && blots >= 1) frame = 3; // 잉크 얼룩은 페이지당 1개 이하
    if (frame === 2) blots++;
    let sx: number;
    let sy: number;
    let flipX = rnd() < 0.5;
    let flipY = rnd() < 0.5;
    if (frame === 1) {
      // 그을림: 심(우하단)이 페이지 가장자리·모서리를 향하게 — 모서리 쪽에 놓고 반전으로 방향을 맞춘다
      const right = rnd() < 0.5;
      const bottom = rnd() < 0.5;
      sx = right ? x + w - inset - 32 : x + inset;
      sy = bottom ? y + h - inset - 32 : y + inset;
      flipX = !right;
      flipY = !bottom;
    } else {
      sx = x + inset + Math.floor(rnd() * Math.max(1, iw - 32));
      sy = y + inset + Math.floor(rnd() * Math.max(1, ih - 32));
    }
    scene.add.image(sx, sy, KIT.stains, frame).setOrigin(0, 0).setFlip(flipX, flipY);
  }
}

/**
 * 책 틀 + 페이지. 한 페이지면 pages=1, 두 페이지 펼침이면 pages=2 (사이 spine 16).
 * pageW/pageH 는 페이지 한 장 크기. 반환: 틀 왼쪽 위와 페이지 원점들.
 */
export function book(
  scene: Phaser.Scene,
  cx: number,
  cy: number,
  pageW: number,
  pageH: number,
  pages: 1 | 2,
  seed: string,
): { x: number; y: number; w: number; h: number; pages: { x: number; y: number }[] } {
  const inner = SLICE.bookFrame.inner;
  const spineW = pages === 2 ? 16 : 0;
  const w = pageW * pages + spineW + inner * 2;
  const h = pageH + inner * 2;
  const x = Math.round(cx - w / 2);
  const y = Math.round(cy - h / 2);
  new NinePanel(scene, x, y, KIT.bookFrame, SLICE.bookFrame, w, h);
  const origins: { x: number; y: number }[] = [];
  for (let i = 0; i < pages; i++) {
    const px = x + inner + i * (pageW + spineW);
    const py = y + inner;
    if (i === 1) scene.add.tileSprite(px - spineW, py, spineW, pageH, KIT.spine).setOrigin(0, 0);
    paperPage(scene, px, py, pageW, pageH, `${seed}#${i}`);
    origins.push({ x: px, y: py });
  }
  return { x, y, w, h, pages: origins };
}

/** 종이 괘선 (rule 1×4 가로 반복). 잉크 패널용은 light=true */
export function rule(
  scene: Phaser.Scene,
  x: number,
  y: number,
  w: number,
  light = false,
): Phaser.GameObjects.TileSprite {
  return scene.add.tileSprite(x, y, w, 4, light ? KIT.ruleLight : KIT.rule).setOrigin(0, 0);
}

/** 아이콘 (16×16 또는 미니맵 8×8). 왼쪽 위 기준 */
export function icon(scene: Phaser.Scene, x: number, y: number, name: string): Phaser.GameObjects.Image {
  return scene.add.image(x, y, KIT.icons, name).setOrigin(0, 0);
}

/** 깜빡이는 커서 (피벗 4,4). page 용 `cursor`, 잉크 바탕용 `cursor_light` */
export function cursor(scene: Phaser.Scene, light = false): Phaser.GameObjects.Sprite {
  const key = light ? KIT.cursorLight : KIT.cursor;
  const s = scene.add.sprite(0, 0, key, 0).setOrigin(0.5, 0.5);
  if (scene.anims.exists(key)) s.play(key);
  return s;
}

// ---------------------------------------------------------------------------------------------
// 게이지: 틀 9-slice + 채움 1×8 가로 늘림. 층 램프 틴트는 gray 띠 × 램프 23(light1) 곱 틴트
export class Gauge {
  private frame: NinePanel;
  private fill: Phaser.GameObjects.Image;
  private innerW: number;
  private tintSlot: number | null;
  constructor(
    scene: Phaser.Scene,
    private x: number,
    private y: number,
    w: number,
    kind: 'frame' | 'boss' | 'gray',
    stageIndex = 0,
  ) {
    const spec = kind === 'boss' ? SLICE.gaugeBoss : SLICE.gaugeFrame;
    const key = kind === 'boss' ? KIT.gaugeBoss : KIT.gaugeFrame;
    this.frame = new NinePanel(scene, x, y, key, spec, w, spec.h);
    this.innerW = w - spec.fillInsetX * 2;
    this.tintSlot = kind === 'gray' ? null : 23;
    // 1층은 그려진 amber 띠 그대로, 다른 층은 gray 띠에 그 층 램프 23 을 곱한다 (gauge_fill_gray.json)
    const authored = kind !== 'gray' && stageIndex === 0;
    this.fill = scene.add
      .image(x + spec.fillInsetX, y + spec.fillInsetY, authored ? KIT.gaugeFill : KIT.gaugeFillGray)
      .setOrigin(0, 0);
    if (!authored && this.tintSlot !== null) this.fill.setTint(hexToNum(accentHex(scene, stageIndex, this.tintSlot)));
    this.set(0);
  }

  /** 층이 바뀌면 채움 띠 색을 바꾼다 */
  setStage(scene: Phaser.Scene, stageIndex: number): void {
    if (this.tintSlot === null) return;
    if (stageIndex === 0) {
      this.fill.setTexture(KIT.gaugeFill).clearTint();
    } else {
      this.fill.setTexture(KIT.gaugeFillGray).setTint(hexToNum(accentHex(scene, stageIndex, this.tintSlot)));
    }
  }

  set(ratio: number): this {
    const r = Math.max(0, Math.min(1, ratio));
    const w = Math.round(this.innerW * r);
    this.fill.setVisible(w > 0);
    if (w > 0) this.fill.setDisplaySize(w, 8);
    return this;
  }

  setVisible(v: boolean): this {
    this.frame.setVisible(v);
    this.fill.setVisible(v && this.fill.displayWidth > 0);
    return this;
  }

  setPositionX(x: number): this {
    if (x === this.x) return this;
    const dx = x - this.x;
    this.x = x;
    this.frame.setX(this.frame.x + dx);
    this.fill.setX(this.fill.x + dx);
    return this;
  }

  setDepth(d: number): this {
    this.frame.setDepth(d);
    this.fill.setDepth(d);
    return this;
  }

  get width(): number {
    return this.frame.width;
  }
  get left(): number {
    return this.x;
  }
  get top(): number {
    return this.y;
  }
}

/** 어두운 바탕 색 (타이틀·결과 화면 배경) */
export const DARK_BG = GRAY[0];
export const MINI = LAYOUT.miniCell;
