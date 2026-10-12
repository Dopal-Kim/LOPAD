import Phaser from 'phaser';

/**
 * 62 타이틀 로고 쓰기 (art §30 `title_logo_reveal` + title.json `logoReveal`): 진행도 p(0..1)에서 마스크 값 ≤ p·255 인 로고 화소만 보인다.
 * 마스크 값이 획 순서(L→O→P→A→D → 부제 → 무기 불씨)라 붓으로 써 내려가는 것처럼 드러난다. 문턱 바로 아래(softBand) 화소는
 * 붓 머리 빛(#faeec0 쪽으로 60%)으로 한 단 밝게 — 먹이 막 닿는 빛. 끝나면(p = 1) 이 그림은 치우고 원래 로고 그림을 쓴다.
 * 화소는 값별 묶음(0~254)으로 한 번만 나눠 두고, p 가 오를 때 새로 넘은 묶음만 옮겨 쓴다(매 프레임 전체를 다시 훑지 않는다).
 */
export class LogoReveal {
  readonly image: Phaser.GameObjects.Image;
  private tex: Phaser.Textures.CanvasTexture;
  private out: ImageData;
  private src: Uint8ClampedArray;
  /** 마스크 값별 화소 번호 */
  private buckets: number[][] = Array.from({ length: 256 }, () => []);
  private thr = -1;
  private band: number;
  private done = false;

  constructor(
    scene: Phaser.Scene,
    logoKey: string,
    maskKey: string,
    texKey: string,
    x: number,
    y: number,
    scale: number,
    depth: number,
    softBand: number,
  ) {
    const logo = scene.textures.get(logoKey).getSourceImage() as HTMLImageElement;
    const mask = scene.textures.get(maskKey).getSourceImage() as HTMLImageElement;
    const w = logo.width;
    const h = logo.height;
    this.src = readPixels(logo, w, h);
    const m = readPixels(mask, w, h);
    for (let i = 0, n = w * h; i < n; i++) {
      if (this.src[i * 4 + 3] === 0) continue;
      const v = m[i * 4];
      if (v < 255) this.buckets[v].push(i);
    }
    if (scene.textures.exists(texKey)) scene.textures.remove(texKey);
    this.tex = scene.textures.createCanvas(texKey, w, h)!;
    this.out = this.tex.getContext().createImageData(w, h);
    this.band = Math.max(0, Math.round(softBand * 255));
    this.image = scene.add.image(x, y, texKey).setOrigin(0, 0).setScale(scale).setDepth(depth);
  }

  get finished(): boolean {
    return this.done;
  }

  /** 진행도 p 로 (뒤로 가지 않는다). p ≥ 1 이면 끝 */
  set(p: number): void {
    if (this.done) return;
    const thr = Math.min(254, Math.floor(Math.max(0, Math.min(1, p)) * 255));
    if (thr === this.thr && p < 1) return;
    const d = this.out.data;
    const s = this.src;
    const put = (i: number, glow: boolean): void => {
      const o = i * 4;
      if (glow) {
        d[o] = s[o] + (0xfa - s[o]) * 0.6;
        d[o + 1] = s[o + 1] + (0xee - s[o + 1]) * 0.6;
        d[o + 2] = s[o + 2] + (0xc0 - s[o + 2]) * 0.6;
      } else {
        d[o] = s[o];
        d[o + 1] = s[o + 1];
        d[o + 2] = s[o + 2];
      }
      d[o + 3] = s[o + 3];
    };
    // 지난번 빛 띠였던 화소는 본색으로, 새로 넘은 묶음은 띠 안이면 빛으로
    for (let v = Math.max(0, this.thr - this.band); v <= this.thr; v++) for (const i of this.buckets[v]) put(i, false);
    for (let v = Math.max(0, this.thr + 1); v <= thr; v++) for (const i of this.buckets[v]) put(i, false);
    if (p < 1) for (let v = Math.max(0, thr - this.band); v <= thr; v++) for (const i of this.buckets[v]) put(i, true);
    this.thr = thr;
    this.tex.getContext().putImageData(this.out, 0, 0);
    this.tex.refresh();
    if (p >= 1) this.done = true;
  }

  destroy(): void {
    this.image.destroy();
    this.tex.destroy();
  }
}

function readPixels(img: CanvasImageSource, w: number, h: number): Uint8ClampedArray {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const ctx = c.getContext('2d', { willReadFrequently: true })!;
  ctx.drawImage(img, 0, 0, w, h);
  return ctx.getImageData(0, 0, w, h).data;
}
