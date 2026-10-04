/**
 * 53라운드 Q3: 획을 긋는 화면 = **화면 가득 찬 주인공의 등** (재 껍데기 · 굳은 실금 · 어깨 혼불).
 * 아트 산출물이 오기 전 시스템 임시 그림 — 캔버스 2D 로 실제 캔버스 해상도(1920×1080)에 그린다(좌표는 논리 px).
 * 주인공 v3 뒷모습 시트를 확대하지 않은 이유: 64×96 도트를 화면 가득(약 10배) 키우면 도트 한 칸이 획 폭(1~3px)보다
 * 수십 배 커서 매끄러운 획과 문체가 어긋나고, 시트에 이미 그려진 등 균열이 플레이어 획과 겹친다. 색만 시트에서 따왔다
 * (재 껍데기 = gray, 혼불·균열 = 1층 호박 램프).
 * - `paintBack`: 등 정지 그림 (Phaser 없음)
 * - `ShoulderFire`: 어깨 혼불 (파티클 + 일렁이는 빛, Phaser)
 * 수치는 전부 시스템 임시값.
 */
import Phaser from 'phaser';
import { GAME } from '../../core/Constants';
import { CANVAS_H, CANVAS_W, RES } from '../display';
import { rgba, type Ctx } from './strokeFxPaint';

export const BACK = {
  KEY: 'setup_back',
  /** 머리 뒤통수 (중심·반지름, 위가 화면 밖으로 잘린다) */
  HEAD: { x: 480, y: 4, rx: 86, ry: 100 },
  /** 목 (윗변 y · 폭) */
  NECK: { y: 100, w: 112 },
  /** 어깨 꼭대기(화면 왼쪽 기준, 오른쪽은 대칭) · 삼각근 바깥 · 팔 바깥 아래 */
  SHOULDER: { x: 232, y: 182 },
  DELTOID: { x: 120, y: 304 },
  ARM_BOTTOM: { x: 132, y: 540 },
  /** 팔과 몸통 사이 그늘 (겨드랑이 → 아래) */
  ARMPIT: { x: 218, y: 352, bottomX: 240 },
  /** 견갑골 (왼쪽, 오른쪽 대칭): 중심·반지름·기울기 */
  BLADE: { x: 374, y: 292, rx: 90, ry: 72, rot: -0.28 },
  /** 상흔 기준 사각형 (등 중앙, 논리 px) — 획 좌표를 이 사각형으로 정규화해 저장한다(scarAnchor 에 맞춰 줄여 그릴 기준) */
  SCAR_RECT: { x: 250, y: 112, w: 460, h: 420 },
  /** 재 껍데기 색 (팔레트 gray 인덱스): 밝은 면 · 기본 · 그늘 */
  GRAY_LIGHT: 4,
  GRAY_BASE: 2,
  GRAY_SHADE: 1,
  /** 얼룩 두 겹(저해상 잡음 칸 수 · 알파) · 고운 결 세기 */
  MOTTLE: [
    { cols: 64, alpha: 0.14 },
    { cols: 240, alpha: 0.1 },
  ],
  GRAIN: 0.1,
  /** 부드러운 그늘 흐림 (논리 px): 윤곽 · 해부 */
  EDGE_BLUR: 16,
  SHADE_BLUR: 7,
  /** 굳은 실금(원래 있던 재 껍데기 금, 빛 없음) · 들뜬 비늘 */
  CRACKS: 14,
  CRACK_LEN: [26, 88] as [number, number],
  FLAKES: 46,
  /** 혼불이 등을 비추는 테두리 빛 (램프 인덱스·알파·반지름) */
  RIM: { ramp: 6, alpha: 0.2, radius: 300 },
};

/** 혼불 (어깨 위): 자리·파티클·빛 (램프 인덱스는 1층 호박 램프) */
export const SHOULDER_FIRE = {
  x: 250,
  y: 170,
  ZONE_R: 9,
  FREQ_MS: 26,
  SPEED_Y: [-95, -40] as [number, number],
  SPEED_X: [-14, 14] as [number, number],
  LIFE_MS: [420, 820] as [number, number],
  SCALE: [0.62, 0.04] as [number, number],
  TINTS: [11, 10, 9, 7],
  GLOW: { ramp: 7, alpha: 0.34, scale: 4.2, flicker: 0.1 },
};

/** 등 그림 텍스처 (실제 해상도, 한 번 만들어 재사용) */
export function ensureBackTexture(scene: Phaser.Scene, gray: number[], ramp: number[], rnd: () => number): void {
  const tex = scene.textures;
  if (tex.exists(BACK.KEY)) return;
  const canvas = tex.createCanvas(BACK.KEY, CANVAS_W, CANVAS_H)!;
  paintBack(canvas.context, gray, ramp, rnd);
  canvas.refresh();
}

/** 등 정지 그림 (ctx = 실제 해상도 캔버스, 논리 좌표로 그린다) */
export function paintBack(ctx: Ctx, gray: number[], ramp: number[], rnd: () => number): void {
  const W = GAME.WIDTH;
  const H = GAME.HEIGHT;
  const g = (i: number) => gray[i] ?? 0x2f3033;
  const r = (i: number) => ramp[i] ?? 0xd67a11;
  ctx.setTransform(RES, 0, 0, RES, 0, 0);
  // 바탕: 어둠 + 혼불 쪽으로 옅은 잔열
  ctx.fillStyle = rgba(0x050506, 1);
  ctx.fillRect(0, 0, W, H);
  const haze = ctx.createRadialGradient(SHOULDER_FIRE.x, SHOULDER_FIRE.y, 0, SHOULDER_FIRE.x, SHOULDER_FIRE.y, 420);
  haze.addColorStop(0, rgba(r(1), 0.5));
  haze.addColorStop(1, rgba(r(0), 0));
  ctx.fillStyle = haze;
  ctx.fillRect(0, 0, W, H);

  // 몸(등·팔·목·머리)은 따로 그려 얼룩·결을 몸 안에만 입힌 뒤 얹는다
  const body = document.createElement('canvas');
  body.width = CANVAS_W;
  body.height = CANVAS_H;
  const b = body.getContext('2d')!;
  b.setTransform(RES, 0, 0, RES, 0, 0);
  const torso = torsoPath();
  b.fillStyle = rgba(g(BACK.GRAY_BASE), 1);
  b.fill(torso);
  b.globalCompositeOperation = 'source-atop';
  // 빛: 혼불 쪽(왼쪽 위)이 밝고, 오른쪽 아래로 어둠에 잠긴다
  const key = b.createRadialGradient(
    SHOULDER_FIRE.x + 120,
    SHOULDER_FIRE.y + 60,
    0,
    SHOULDER_FIRE.x + 120,
    SHOULDER_FIRE.y + 60,
    720,
  );
  key.addColorStop(0, rgba(g(BACK.GRAY_LIGHT + 1), 0.8));
  key.addColorStop(0.55, rgba(g(BACK.GRAY_BASE), 0));
  b.fillStyle = key;
  b.fillRect(0, 0, W, H);
  const fall = b.createLinearGradient(0, 160, 0, H);
  fall.addColorStop(0, rgba(g(0), 0));
  fall.addColorStop(1, rgba(g(0), 0.6));
  b.fillStyle = fall;
  b.fillRect(0, 0, W, H);
  b.filter = `blur(${BACK.SHADE_BLUR * RES}px)`;
  paintAnatomy(b, g);
  b.filter = 'none';
  paintMottle(b, rnd);
  // 테두리 그늘 (부피감): 윤곽을 흐리게 어둡게
  b.filter = `blur(${BACK.EDGE_BLUR * RES}px)`;
  b.lineWidth = 56;
  b.strokeStyle = rgba(g(0), 0.75);
  b.stroke(torso);
  b.filter = 'none';
  // 혼불 테두리 빛 (왼쪽 어깨)
  const R = BACK.RIM;
  const rim = b.createRadialGradient(SHOULDER_FIRE.x, SHOULDER_FIRE.y, 0, SHOULDER_FIRE.x, SHOULDER_FIRE.y, R.radius);
  rim.addColorStop(0, rgba(r(R.ramp), R.alpha));
  rim.addColorStop(1, rgba(r(R.ramp), 0));
  b.fillStyle = rim;
  b.fillRect(0, 0, W, H);
  paintOldCracks(b, g, rnd);
  b.globalCompositeOperation = 'source-over';
  paintHead(b, g, r);
  paintGrain(b, rnd);
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(body, 0, 0);
  ctx.restore();
}

/** 목 → 어깨 → 삼각근 → 팔 바깥 (좌우 대칭), 아래는 화면 밖 */
function torsoPath(): Path2D {
  const { NECK: N, SHOULDER: S, DELTOID: D, ARM_BOTTOM: A } = BACK;
  const cx = GAME.WIDTH / 2;
  const m = (x: number) => 2 * cx - x;
  const p = new Path2D();
  const nl = cx - N.w / 2;
  p.moveTo(nl, N.y - 20);
  p.lineTo(nl + 4, N.y + 8);
  p.quadraticCurveTo(nl - 70, N.y + 20, S.x, S.y);
  p.bezierCurveTo(S.x - 60, S.y + 6, D.x - 4, D.y - 70, D.x, D.y);
  p.bezierCurveTo(D.x + 2, D.y + 90, A.x - 10, A.y - 120, A.x, A.y + 10);
  p.lineTo(m(A.x), A.y + 10);
  p.bezierCurveTo(m(A.x - 10), A.y - 120, m(D.x + 2), D.y + 90, m(D.x), D.y);
  p.bezierCurveTo(m(D.x - 4), D.y - 70, m(S.x - 60), S.y + 6, m(S.x), S.y);
  p.quadraticCurveTo(m(nl - 70), N.y + 20, m(nl + 4), N.y + 8);
  p.lineTo(m(nl), N.y - 20);
  p.closePath();
  return p;
}

/** 등뼈 골 · 척추 세움근 · 견갑골 · 겨드랑이 그늘 */
function paintAnatomy(b: Ctx, g: (i: number) => number): void {
  const cx = GAME.WIDTH / 2;
  const H = GAME.HEIGHT;
  // 등뼈 골 (가로 그라데이션 띠)
  const spine = b.createLinearGradient(cx - 26, 0, cx + 26, 0);
  spine.addColorStop(0, rgba(g(0), 0));
  spine.addColorStop(0.5, rgba(g(0), 0.55));
  spine.addColorStop(1, rgba(g(0), 0));
  b.fillStyle = spine;
  b.fillRect(cx - 26, 120, 52, H);
  for (const s of [-1, 1]) {
    const x = cx + s * 30;
    const ridge = b.createLinearGradient(x - 18, 0, x + 18, 0);
    ridge.addColorStop(0, rgba(g(BACK.GRAY_LIGHT + 1), 0));
    ridge.addColorStop(0.5, rgba(g(BACK.GRAY_LIGHT + 1), 0.22));
    ridge.addColorStop(1, rgba(g(BACK.GRAY_LIGHT + 1), 0));
    b.fillStyle = ridge;
    b.fillRect(x - 18, 300, 36, H);
  }
  const B = BACK.BLADE;
  for (const s of [-1, 1]) {
    const x = s < 0 ? B.x : 2 * cx - B.x;
    b.save();
    b.translate(x, B.y);
    b.rotate(B.rot * s);
    // 위쪽 밝은 면
    const hi = b.createRadialGradient(-s * 16, -26, 4, 0, 0, B.rx);
    hi.addColorStop(0, rgba(g(BACK.GRAY_LIGHT + 1), 0.32));
    hi.addColorStop(1, rgba(g(BACK.GRAY_LIGHT), 0));
    b.fillStyle = hi;
    b.beginPath();
    b.ellipse(0, 0, B.rx, B.ry, 0, 0, Math.PI * 2);
    b.fill();
    // 아래·안쪽 가장자리 그늘 (견갑골 끝선)
    b.lineWidth = 10;
    b.strokeStyle = rgba(g(0), 0.3);
    b.beginPath();
    b.ellipse(0, 4, B.rx * 0.92, B.ry * 0.9, 0, Math.PI * 0.15, Math.PI * 0.95);
    b.stroke();
    b.restore();
  }
  // 겨드랑이 → 아래: 팔과 몸통 사이
  const A = BACK.ARMPIT;
  for (const s of [-1, 1]) {
    const x0 = s < 0 ? A.x : 2 * cx - A.x;
    const x1 = s < 0 ? A.bottomX : 2 * cx - A.bottomX;
    b.lineWidth = 16;
    b.strokeStyle = rgba(g(0), 0.85);
    b.beginPath();
    b.moveTo(x0, A.y);
    b.quadraticCurveTo(x0 + s * -8, (A.y + H) / 2, x1, H + 4);
    b.stroke();
  }
}

/** 재 얼룩: 저해상 잡음을 부드럽게 늘려 덮는다 (밝게·어둡게 섞임) */
function paintMottle(b: Ctx, rnd: () => number): void {
  const W = GAME.WIDTH;
  const H = GAME.HEIGHT;
  for (const m of BACK.MOTTLE) {
    const cols = m.cols;
    const rows = Math.ceil((cols * H) / W);
    const c = document.createElement('canvas');
    c.width = cols;
    c.height = rows;
    const cx = c.getContext('2d')!;
    const img = cx.createImageData(cols, rows);
    for (let k = 0; k < cols * rows; k++) {
      const v = rnd();
      const dark = v < 0.5;
      img.data[k * 4] = dark ? 0 : 120;
      img.data[k * 4 + 1] = dark ? 0 : 118;
      img.data[k * 4 + 2] = dark ? 0 : 116;
      img.data[k * 4 + 3] = Math.round(255 * Math.abs(v - 0.5) * 2);
    }
    cx.putImageData(img, 0, 0);
    b.globalAlpha = m.alpha;
    b.imageSmoothingEnabled = true;
    b.drawImage(c, 0, 0, W, H);
    b.globalAlpha = 1;
  }
}

/** 원래 있던 재 껍데기 실금 (빛 없음 — 빛나는 균열은 플레이어가 긋는 획뿐) + 들뜬 비늘 */
function paintOldCracks(b: Ctx, g: (i: number) => number, rnd: () => number): void {
  const W = GAME.WIDTH;
  const S = BACK.SCAR_RECT;
  const range = ([a, c]: [number, number]) => a + (c - a) * rnd();
  for (let i = 0; i < BACK.CRACKS; i++) {
    // 가운데(상흔 자리)는 피해서 어깨·팔·옆구리에서 시작
    let x = 0;
    let y = 0;
    for (let t = 0; t < 12; t++) {
      x = 90 + rnd() * (W - 180);
      y = 130 + rnd() * 400;
      const inScar = x > S.x + 40 && x < S.x + S.w - 40 && y > S.y + 30;
      if (!inScar) break;
    }
    let a = rnd() * Math.PI * 2;
    const len = range(BACK.CRACK_LEN);
    const pts: [number, number][] = [[x, y]];
    for (let d = 0; d < len; d += 5) {
      a += (rnd() - 0.5) * 0.9;
      x += Math.cos(a) * 5;
      y += Math.sin(a) * 5;
      pts.push([x, y]);
    }
    for (const [off, color, alpha, w] of [
      [0.6, g(BACK.GRAY_LIGHT + 2), 0.16, 0.6],
      [0, g(0), 0.55, 0.75],
    ] as [number, number, number, number][]) {
      b.beginPath();
      pts.forEach(([px, py], k) => (k ? b.lineTo(px + off, py + off) : b.moveTo(px + off, py + off)));
      b.strokeStyle = rgba(color, alpha);
      b.lineWidth = w;
      b.lineJoin = 'round';
      b.stroke();
    }
  }
  for (let i = 0; i < BACK.FLAKES; i++) {
    const x = 100 + rnd() * (W - 200);
    const y = 140 + rnd() * 380;
    const s = 2 + rnd() * 5;
    b.fillStyle = rgba(g(BACK.GRAY_LIGHT + (rnd() < 0.5 ? 0 : 1)), 0.2 + rnd() * 0.15);
    b.beginPath();
    for (let k = 0; k < 5; k++) {
      const t = (k / 5) * Math.PI * 2 + rnd() * 0.5;
      const rr = s * (0.6 + rnd() * 0.5);
      const px = x + Math.cos(t) * rr;
      const py = y + Math.sin(t) * rr * 0.7;
      if (k) b.lineTo(px, py);
      else b.moveTo(px, py);
    }
    b.closePath();
    b.fill();
  }
}

/** 뒤통수 (투구 같은 재 껍데기) + 작은 호박 금 하나 (시트 뒷모습과 맞춤) */
function paintHead(b: Ctx, g: (i: number) => number, r: (i: number) => number): void {
  const Hd = BACK.HEAD;
  // 머리 아래 목에 지는 그늘 (머리보다 먼저)
  b.filter = `blur(${BACK.SHADE_BLUR * RES}px)`;
  b.fillStyle = rgba(g(0), 0.6);
  b.beginPath();
  b.ellipse(Hd.x, Hd.y + Hd.ry + 2, Hd.rx * 0.7, 14, 0, 0, Math.PI * 2);
  b.fill();
  b.filter = 'none';
  const grad = b.createRadialGradient(Hd.x - 30, Hd.y + 10, 10, Hd.x, Hd.y, Hd.ry * 1.05);
  grad.addColorStop(0, rgba(g(BACK.GRAY_LIGHT), 1));
  grad.addColorStop(0.7, rgba(g(BACK.GRAY_BASE - 1), 1));
  grad.addColorStop(1, rgba(g(BACK.GRAY_SHADE), 1));
  b.fillStyle = grad;
  b.beginPath();
  b.ellipse(Hd.x, Hd.y, Hd.rx, Hd.ry, 0, 0, Math.PI * 2);
  b.fill();
  b.strokeStyle = rgba(r(6), 0.75);
  b.lineWidth = 1.2;
  b.beginPath();
  b.moveTo(Hd.x - 52, Hd.y + 30);
  b.lineTo(Hd.x - 44, Hd.y + 42);
  b.lineTo(Hd.x - 50, Hd.y + 55);
  b.lineTo(Hd.x - 42, Hd.y + 68);
  b.stroke();
}

/** 고운 결: 몸 화소마다 밝기 ±GRAIN (실제 해상도) */
function paintGrain(b: Ctx, rnd: () => number): void {
  const img = b.getImageData(0, 0, CANVAS_W, CANVAS_H);
  const d = img.data;
  const k = BACK.GRAIN;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] === 0) continue;
    const f = 1 + (rnd() * 2 - 1) * k;
    d[i] = Math.min(255, d[i] * f);
    d[i + 1] = Math.min(255, d[i + 1] * f);
    d[i + 2] = Math.min(255, d[i + 2] * f);
  }
  b.putImageData(img, 0, 0);
}

/** 어깨 혼불: 위로 피어오르는 불꽃 파티클 + 일렁이는 빛. boost(0~) 로 획이 타오를 때 함께 커진다 */
export class ShoulderFire {
  private readonly flame: Phaser.GameObjects.Particles.ParticleEmitter;
  private readonly glow: Phaser.GameObjects.Image;
  private boost = 0;

  constructor(scene: Phaser.Scene, texKey: string, ramp: number[], depth: number) {
    const F = SHOULDER_FIRE;
    const tint = (i: number) => ramp[i] ?? 0xe2a33c;
    this.glow = scene.add
      .image(F.x, F.y, texKey)
      .setBlendMode(Phaser.BlendModes.ADD)
      .setTint(tint(F.GLOW.ramp))
      .setScale(F.GLOW.scale)
      .setAlpha(F.GLOW.alpha)
      .setDepth(depth);
    this.flame = scene.add.particles(F.x, F.y, texKey, {
      frequency: F.FREQ_MS,
      speedY: { min: F.SPEED_Y[0], max: F.SPEED_Y[1] },
      speedX: { min: F.SPEED_X[0], max: F.SPEED_X[1] },
      lifespan: { min: F.LIFE_MS[0], max: F.LIFE_MS[1] },
      scale: { start: F.SCALE[0], end: F.SCALE[1] },
      alpha: { start: 0.9, end: 0 },
      tint: F.TINTS.map(tint),
      blendMode: Phaser.BlendModes.ADD,
      emitZone: {
        type: 'random',
        source: new Phaser.Geom.Circle(0, 0, F.ZONE_R),
      } as Phaser.Types.GameObjects.Particles.EmitZoneData,
    });
    this.flame.setDepth(depth);
  }

  setBoost(v: number): void {
    this.boost = Math.max(0, v);
  }

  update(time: number): void {
    const G = SHOULDER_FIRE.GLOW;
    const flick = Math.sin(time / 83) * 0.6 + Math.sin(time / 37 + 1.3) * 0.4;
    this.glow
      .setAlpha(Math.min(1, G.alpha * (1 + this.boost * 0.8) + G.flicker * flick))
      .setScale(G.scale * (1 + this.boost * 0.35 + 0.04 * flick));
  }

  setVisible(v: boolean): void {
    this.glow.setVisible(v);
    this.flame.setVisible(v);
    if (!v) this.flame.stop();
  }

  destroy(): void {
    this.glow.destroy();
    this.flame.destroy();
  }
}
