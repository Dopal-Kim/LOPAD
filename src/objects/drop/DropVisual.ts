/**
 * 61 단계 5 (P13 §4) 바닥 줍기 물건 그림 (전표·물약·소모품 공용 — 물리·줍기 판정은 쓰는 쪽).
 * 그림 우선순위: 아트 `items/v3/<id>`(행 = 무더기 크기·종류, idle·spawn·pickup 상태, 메타 shadow) → 소모품 시트 `consumable_f1`
 * (행 = 종류, idle 만 — 그림자 포함) → 임시 도형(원형 동전 무더기·병 모양, 반짝 그림 한 장 더).
 * 연출: 바닥 그림자 · 튀어나와 떨어짐(spawn 그림이 없으면 높이 곡선) · 반짝임 루프 · 자석 흡수 때 움직이는 축으로 늘어남 · 획득 팝.
 * 시계는 부르는 쪽 시각(now)으로만 — 히트스톱·메뉴 정지 동안 씬 시계와 함께 멈춘다.
 */
import Phaser from 'phaser';
import { DEPTH, DROP_ART } from '../../core/Constants';
import { ITEM_ACTION, ITEM_SHEET } from '../../systems/bundle2/bundleSheets';
import { dropFrames, stretchScale, type DropSheetMeta, type VoucherSize } from '../../systems/drops/dropRules';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { artScale, frameDurations } from '../../systems/sprites/spriteDefs';

interface DropArt {
  tex: string;
  /** 반짝 그림 (임시 도형만 — 시트는 idle 루프가 반짝임) */
  glintTex: string | null;
  scale: number;
  originX: number;
  originY: number;
  idle: number[];
  spawn: number[];
  pickup: number[];
  /** 자석으로 끌려가는 동안 반복 (그린 축 '위' — 돌려 쓴다). 없으면 늘어남 배율 */
  magnet: number[];
  durations: number[];
  shadowBaked: boolean;
  /** 그림 폭 (월드 px — 그림자 크기) */
  widthPx: number;
  source: 'items' | 'consumable' | 'fallback';
}

/** 디버그·검증: 마지막으로 고른 그림 출처 */
export const dropArtLog: { kind: string; source: string }[] = [];

export class DropVisual {
  readonly sprite: Phaser.GameObjects.Sprite;
  private readonly shadow: Phaser.GameObjects.Ellipse;
  private art: DropArt | null = null;
  private x = 0;
  private y = 0;
  private spawnAt = 0;
  /** 튀어나오는 동안 바닥 자리가 from → (x, y) 로 흩뿌려진다 (spawnMs 동안) */
  private from: { x: number; y: number } | null = null;
  private spawnMs = 0;
  private pulling = false;
  private hopping = false;
  private onLand: (() => void) | null = null;
  private anim: { frames: number[]; i: number; nextAt: number; loop: boolean; done?: () => void } | null = null;
  private popping = false;
  private popTween: Phaser.Tweens.Tween | null = null;
  private ring: Phaser.GameObjects.Arc | null = null;

  constructor(private readonly scene: Phaser.Scene) {
    this.sprite = scene.add.sprite(0, 0, '__DEFAULT').setDepth(DEPTH.PICKUP).setVisible(false);
    this.shadow = scene.add
      .ellipse(0, 0, 6, 2, 0x000000, DROP_ART.SHADOW.ALPHA)
      .setDepth(DEPTH.SHADOW)
      .setVisible(false);
  }

  get source(): string {
    return this.art?.source ?? 'none';
  }

  /** 바닥 (x, y) 에 나타남 — from(떨군 자리)에서 흩뿌려지며 튀어나와 떨어진 뒤 onLand 한 번 */
  show(
    x: number,
    y: number,
    kind: string,
    size: VoucherSize | null,
    now: number,
    onLand?: () => void,
    from?: { x: number; y: number },
  ): void {
    this.stopPop();
    const art = resolveDropArt(this.scene, kind, size);
    this.art = art;
    this.x = x;
    this.y = y;
    this.spawnAt = now;
    this.onLand = onLand ?? null;
    this.popping = false;
    this.pulling = false;
    this.from = from ? { x: from.x, y: from.y } : null;
    const H = DROP_ART.HOP;
    this.spawnMs = art.spawn.length > 0 ? art.spawn.reduce((a, f) => a + this.durOf(art, f), 0) : H.UP_MS + H.DOWN_MS;
    const s = this.sprite;
    s.setTexture(art.tex, art.idle.length > 0 ? String(art.idle[0]) : undefined)
      .setOrigin(art.originX, art.originY)
      .setScale(art.scale)
      .setAlpha(1)
      .setRotation(0)
      .setVisible(true)
      .clearTint();
    const S = DROP_ART.SHADOW;
    this.shadow
      .setSize(Math.max(S.MIN_W, art.widthPx * S.W_MULT), Math.max(1, art.widthPx * S.W_MULT * S.H_RATIO))
      .setVisible(!art.shadowBaked)
      .setAlpha(1);
    // spawn 그림이 있으면 그것(튀어나옴이 그림에 있다), 없으면 높이 곡선
    if (art.spawn.length > 0) {
      this.hopping = false;
      this.play(art.spawn, false, now, () => this.land(now));
    } else {
      this.hopping = true;
      this.play(art.idle, true, now);
    }
    this.place(0, 1, 1);
  }

  private land(now: number): void {
    const art = this.art;
    if (art) this.play(art.idle, true, now);
    const f = this.onLand;
    this.onLand = null;
    f?.();
  }

  private play(frames: number[], loop: boolean, now: number, done?: () => void): void {
    if (frames.length === 0) {
      this.anim = null;
      done?.();
      return;
    }
    this.sprite.setFrame(String(frames[0]));
    this.anim = { frames, i: 0, nextAt: now + this.dur(frames[0]), loop, done };
  }

  private dur(frame: number): number {
    return this.art ? this.durOf(this.art, frame) : 110;
  }

  private durOf(art: DropArt, frame: number): number {
    const d = art.durations;
    if (d.length === 0) return 110;
    return d[frame % d.length] ?? 110;
  }

  /** 높이 곡선 (월드 px): 올라감 → 떨어짐 → 작은 튕김. 끝나면 null */
  private hopLift(t: number): number | null {
    const H = DROP_ART.HOP;
    if (t < H.UP_MS) {
      const k = t / H.UP_MS;
      return H.HEIGHT * (1 - (1 - k) * (1 - k));
    }
    if (t < H.UP_MS + H.DOWN_MS) {
      const k = (t - H.UP_MS) / H.DOWN_MS;
      return H.HEIGHT * (1 - k * k);
    }
    const b = t - H.UP_MS - H.DOWN_MS;
    if (b < H.BOUNCE_MS) return Math.sin((b / H.BOUNCE_MS) * Math.PI) * H.BOUNCE;
    return null;
  }

  /**
   * 매 프레임: (x, y) = 바닥 자리(물리 바디), vx·vy = 자석 흡수 속도(없으면 0) · maxSpeed = 늘어남 기준 · alpha = 수명 끝 깜빡임
   */
  update(now: number, x = this.x, y = this.y, vx = 0, vy = 0, maxSpeed = 1, alpha = 1): void {
    if (!this.art || !this.sprite.visible) return;
    const a = this.anim;
    if (a && now >= a.nextAt) {
      a.i++;
      if (a.i >= a.frames.length) {
        if (a.loop) a.i = 0;
        else {
          this.anim = null;
          a.done?.();
        }
      }
      if (this.anim === a) {
        this.sprite.setFrame(String(a.frames[a.i]));
        a.nextAt = now + this.dur(a.frames[a.i]);
      }
    }
    if (this.popping) return;
    // 흩뿌림: 튀어나오는 동안 떨군 자리 → 바닥 자리 (높이는 그림·곡선)
    const k = this.from && this.spawnMs > 0 ? Math.min(1, (now - this.spawnAt) / this.spawnMs) : 1;
    if (k >= 1) this.from = null;
    this.x = this.from ? this.from.x + (x - this.from.x) * k : x;
    this.y = this.from ? this.from.y + (y - this.from.y) * k : y;
    let lift = 0;
    if (this.hopping) {
      const l = this.hopLift(now - this.spawnAt);
      if (l === null) {
        this.hopping = false;
        this.land(now);
      } else lift = l;
    }
    // 임시 도형 반짝임 · 둥실 (시트는 idle 루프가 한다)
    const S = DROP_ART.SHIMMER;
    if (this.art.glintTex && !this.hopping) {
      const phase = (now - this.spawnAt) % S.PERIOD_MS;
      const tex = phase < S.FLASH_MS ? this.art.glintTex : this.art.tex;
      if (this.sprite.texture.key !== tex) this.sprite.setTexture(tex);
      lift += (Math.sin(((now - this.spawnAt) / S.BOB_MS) * Math.PI) + 1) * 0.5 * S.BOB_PX;
    }
    // 자석 흡수: 시트 magnet 행이 있으면 그것을 주인공 쪽으로 돌려(그린 축 '위'), 없으면 움직이는 축으로 늘어남
    const pulled = vx !== 0 || vy !== 0;
    const art = this.art;
    if (art.magnet.length > 0 && !this.hopping && this.onLand === null) {
      if (pulled && !this.pulling) this.play(art.magnet, true, now);
      else if (!pulled && this.pulling) this.play(art.idle, true, now);
      this.pulling = pulled;
      this.sprite.setRotation(pulled ? Math.atan2(vy, vx) + Math.PI / 2 : 0);
      this.place(lift, 1, 1);
    } else {
      const [sx, sy] = stretchScale(vx, vy, maxSpeed, DROP_ART.MAGNET.STRETCH);
      this.place(lift, sx, sy);
    }
    this.sprite.setAlpha(alpha);
    this.shadow.setAlpha(alpha);
  }

  private place(lift: number, sx: number, sy: number): void {
    const art = this.art;
    if (!art) return;
    this.sprite.setPosition(this.x, this.y - lift).setScale(art.scale * sx, art.scale * sy);
    // 높이 뜨면 그림자가 작아진다
    const k = Math.max(0.5, 1 - lift / (DROP_ART.HOP.HEIGHT * 2));
    this.shadow.setPosition(this.x, this.y).setScale(k);
  }

  /** 획득 팝: pickup 그림이 있으면 그것, 없으면 커지며 사라짐 + 반짝 고리. 끝나면 숨기고 done */
  pop(now: number, done?: () => void): void {
    const art = this.art;
    if (!art || !this.sprite.visible) {
      done?.();
      return;
    }
    this.popping = true;
    this.hopping = false;
    this.pulling = false;
    this.sprite.setRotation(0);
    this.shadow.setVisible(false);
    const finish = () => {
      this.hide();
      done?.();
    };
    if (art.pickup.length > 0) {
      this.sprite.setScale(art.scale).setAlpha(1);
      this.play(art.pickup, false, now, finish);
      return;
    }
    const P = DROP_ART.POP;
    if (art.glintTex) this.sprite.setTexture(art.glintTex);
    this.popTween = this.scene.tweens.add({
      targets: this.sprite,
      scaleX: art.scale * P.SCALE,
      scaleY: art.scale * P.SCALE,
      alpha: 0,
      y: this.sprite.y - 3,
      duration: P.MS,
      ease: 'Quad.easeOut',
      onComplete: finish,
    });
    this.ring?.destroy();
    const ring = this.scene.add
      .circle(this.x, this.y - 3, 1, 0, 0)
      .setStrokeStyle(1, P.RING_COLOR, 1)
      .setDepth(DEPTH.PICKUP);
    this.ring = ring;
    this.scene.tweens.add({
      targets: ring,
      radius: P.RING_R,
      alpha: 0,
      duration: P.MS,
      onComplete: () => {
        ring.destroy();
        if (this.ring === ring) this.ring = null;
      },
    });
  }

  private stopPop(): void {
    this.popTween?.stop();
    this.popTween = null;
    this.ring?.destroy();
    this.ring = null;
  }

  hide(): void {
    this.stopPop();
    this.anim = null;
    this.popping = false;
    this.hopping = false;
    this.onLand = null;
    this.sprite.setVisible(false);
    this.shadow.setVisible(false);
  }

  destroy(): void {
    this.stopPop();
    this.sprite.destroy();
    this.shadow.destroy();
  }
}

/** 그림 고르기: items/v3/<kind> → consumable_f1 행 → 임시 도형 */
function resolveDropArt(scene: Phaser.Scene, kind: string, size: VoucherSize | null): DropArt {
  const fromSheet = (name: string, row: string | null, source: DropArt['source']): DropArt | null => {
    const def = spriteLibrary.sheet(name, ITEM_ACTION);
    const tex = spriteLibrary.textureKey(name, ITEM_ACTION);
    if (!def || !tex || !scene.textures.exists(tex)) return null;
    const meta = def as unknown as DropSheetMeta;
    if (source === 'consumable' && !meta.kinds?.includes(kind)) return null;
    const idle = dropFrames(meta, 'idle', row);
    const scale = artScale(def);
    return {
      tex,
      glintTex: null,
      scale,
      originX: def.pivot.x / def.frameWidth,
      originY: def.pivot.y / def.frameHeight,
      idle,
      spawn: dropFrames(meta, 'spawn', row),
      pickup: dropFrames(meta, 'pickup', row),
      magnet: dropFrames(meta, 'magnet', row),
      durations: frameDurations(def),
      // 소모품 시트는 그림자가 그림에 있다 (bobNote) · 새 시트는 메타 shadow
      shadowBaked: typeof meta.shadow === 'boolean' ? meta.shadow : source === 'consumable',
      widthPx: def.frameWidth * scale * 0.5,
      source,
    };
  };
  const row = kind === 'voucher' ? size : kind;
  const art =
    fromSheet(kind, row, 'items') ?? fromSheet(ITEM_SHEET, kind, 'consumable') ?? fallbackArt(scene, kind, size);
  dropArtLog.push({ kind, source: art.source });
  if (dropArtLog.length > 20) dropArtLog.shift();
  return art;
}

/** 임시 도형 (씬 텍스처에 한 번 만든다): 전표 = 원형 동전 무더기(크기별), 그 밖 = 병 모양(종류 색) */
function fallbackArt(scene: Phaser.Scene, kind: string, size: VoucherSize | null): DropArt {
  const R = DROP_ART.FALLBACK_RES;
  const key = kind === 'voucher' ? `drop_fb_voucher_${size ?? 'small'}` : `drop_fb_bottle_${kind}`;
  const glint = `${key}_glint`;
  const dims = kind === 'voucher' ? { w: 14, h: 12 } : { w: 9, h: 13 };
  if (!scene.textures.exists(key)) {
    for (const shine of [false, true]) {
      const g = scene.make.graphics({ x: 0, y: 0 }, false);
      if (kind === 'voucher') drawCoins(g, dims, size ?? 'small', shine);
      else drawBottle(g, dims, DROP_ART.BOTTLE.COLOR[kind] ?? DROP_ART.BOTTLE.COLOR.potion, shine);
      g.generateTexture(shine ? glint : key, dims.w * R, dims.h * R);
      g.destroy();
    }
  }
  return {
    tex: key,
    glintTex: glint,
    scale: 1 / R,
    originX: 0.5,
    originY: (dims.h - 1.5) / dims.h,
    idle: [],
    spawn: [],
    pickup: [],
    magnet: [],
    durations: [],
    shadowBaked: false,
    widthPx: kind === 'voucher' ? DROP_ART.COIN.D + 3 : DROP_ART.BOTTLE.BODY_D + 1,
    source: 'fallback',
  };
}

/** 동전 무더기 (해상도 배 도트, 바닥 = 아래에서 1.5px) */
function drawCoins(
  g: Phaser.GameObjects.Graphics,
  dims: { w: number; h: number },
  size: VoucherSize,
  shine: boolean,
): void {
  const R = DROP_ART.FALLBACK_RES;
  const C = DROP_ART.COIN;
  const offsets = [
    [0, 0],
    [-2.5, -0.5],
    [2.5, -0.5],
    [0, -2.2],
    [-1.2, -4],
  ];
  const n = C.COUNT[size];
  const cx = dims.w / 2;
  const by = dims.h - 1.5 - C.D * 0.3;
  for (let i = 0; i < n; i++) {
    const [ox, oy] = offsets[i];
    const x = (cx + ox) * R;
    const y = (by + oy) * R;
    const w = C.D * R;
    const h = C.D * 0.6 * R;
    g.fillStyle(C.RIM, 1).fillEllipse(x, y + R * 0.6, w, h);
    g.fillStyle(C.FACE, 1).fillEllipse(x, y, w, h);
    g.fillStyle(C.RIM, 1).fillEllipse(x, y, w * 0.45, h * 0.45);
    g.fillStyle(C.FACE, 1).fillEllipse(x, y - R * 0.2, w * 0.3, h * 0.3);
  }
  // 전표 띠 (맨 위 동전에 걸친 작은 종이)
  const [tx, ty] = offsets[n - 1];
  g.fillStyle(C.TAG, 1).fillRect((cx + tx - 0.5) * R, (by + ty - 2) * R, R * 1, R * 2.2);
  if (shine) {
    g.fillStyle(C.SHINE, 1).fillRect((cx + tx - 1.6) * R, (by + ty - 0.9) * R, R, R * 0.6);
    g.fillStyle(0xffffff, 1).fillRect((cx + tx + 1.2) * R, (by + ty - 3.2) * R, R * 0.6, R * 0.6);
  }
}

/** 병 (해상도 배 도트, 바닥 = 아래에서 1.5px) */
function drawBottle(
  g: Phaser.GameObjects.Graphics,
  dims: { w: number; h: number },
  color: number,
  shine: boolean,
): void {
  const R = DROP_ART.FALLBACK_RES;
  const B = DROP_ART.BOTTLE;
  const cx = (dims.w / 2) * R;
  const bodyY = (dims.h - 1.5 - B.BODY_D / 2) * R;
  const d = B.BODY_D * R;
  g.fillStyle(B.GLASS_EDGE, 1).fillCircle(cx, bodyY, d / 2 + R * 0.5);
  g.fillStyle(color, 1).fillCircle(cx, bodyY, d / 2);
  const neckTop = bodyY - d / 2 - B.NECK_H * R;
  g.fillStyle(B.GLASS_EDGE, 1).fillRect(cx - (B.NECK_W / 2 + 0.5) * R, neckTop, (B.NECK_W + 1) * R, B.NECK_H * R + R);
  g.fillStyle(color, 1).fillRect(cx - (B.NECK_W / 2) * R, neckTop + R * 0.5, B.NECK_W * R, B.NECK_H * R);
  g.fillStyle(B.CORK, 1).fillRect(cx - (B.NECK_W / 2) * R, neckTop - R * 1.2, B.NECK_W * R, R * 1.4);
  // 유리 반사 (늘 한 점, 반짝일 때 더 크게)
  g.fillStyle(B.SHINE, shine ? 1 : 0.7).fillRect(
    cx - d * 0.28,
    bodyY - d * 0.28,
    R * (shine ? 1.4 : 0.8),
    R * (shine ? 1.4 : 0.8),
  );
  if (shine) g.fillStyle(0xffffff, 1).fillRect(cx + d * 0.1, neckTop - R * 2.6, R * 0.7, R * 0.7);
}
