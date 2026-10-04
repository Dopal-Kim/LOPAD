/**
 * 53라운드 Q4 등 상흔 (계약 art §13): 플레이어가 그은 획(`gameState.scar`, 정규화)을 몸 시트 프레임별 `scarAnchor` 사각형에 맞춰
 * 은은히 빛나는 균열로 겹친다. 위치 = 몸 바로 위·무기 아래. 뒷모습 = 균열 + 빛, 측면 = 어깨 쪽 빛 점만, visible:false = 숨김.
 * 빛은 조명 영향을 받지 않는다(조명이 켜진 지역이면 라이트맵 위 가산). 획 텍스처는 상흔마다 한 번만 굽는다(텍스처 캐시).
 */
import Phaser from 'phaser';
import { DEPTH, SCAR_FX } from '../../core/Constants';
import { gameState } from '../../core/GameState';
import { spriteLibrary } from '../../systems/sprites/sprites';
import { artScale, parseAnimKey, type Dir8 } from '../../systems/sprites/spriteDefs';
import { scarAt, scarFit } from '../../systems/sprites/spriteMeta';
import type { ScarData } from '../../systems/setup/scar';

const KEY_PREFIX = 'scar_';
const DOT_KEY = 'scar_dot';

export class ScarOverlay {
  private readonly crack: Phaser.GameObjects.Image;
  private readonly glow: Phaser.GameObjects.Image;
  private readonly dot: Phaser.GameObjects.Image;
  private scarKey: string | null = null;
  private aspect = 1;
  /** 조명이 켜진 씬이면 true → 빛을 라이트맵 위에 (Game 이 조명을 만든 뒤 정한다) */
  aboveLight = false;
  /** 디버그: 지난 프레임 상태 */
  state: 'none' | 'back' | 'side' | 'hidden' = 'none';
  lastAnchor: { action: string; dir: Dir8; column: number } | null = null;
  /** 56라운드 2단계 도약 공중 높이 (월드 px, 위 +) */
  lift = 0;

  constructor(
    private readonly host: Phaser.GameObjects.Sprite,
    /** 현재 애니 키 (EntityVisual.current — 프레임 유지 `#hold<c>` 포함) */
    private readonly currentKey: () => string | null,
  ) {
    const scene = host.scene;
    ensureDot(scene);
    const make = (key: string) => scene.add.image(host.x, host.y, key).setVisible(false);
    this.crack = make(DOT_KEY);
    this.glow = make(DOT_KEY).setBlendMode(Phaser.BlendModes.ADD);
    this.dot = make(DOT_KEY).setBlendMode(Phaser.BlendModes.ADD);
    host.once(Phaser.GameObjects.Events.DESTROY, () => {
      this.crack.destroy();
      this.glow.destroy();
      this.dot.destroy();
    });
    this.refresh();
  }

  /** 지금 런의 상흔으로 텍스처를 맞춘다 (없으면 굽는다). 상흔이 없으면 숨김 */
  refresh(): void {
    const scar = gameState.scar;
    const key = scar ? bakeScar(this.host.scene, scar) : null;
    this.scarKey = key;
    this.aspect = scar?.aspect ?? 1;
    if (key) {
      this.crack.setTexture(`${key}_crack`);
      this.glow.setTexture(`${key}_glow`);
    }
  }

  /** 매 프레임 (몸 프레임이 정해진 뒤) */
  update(time: number): void {
    this.state = this.place(time);
    if (this.state !== 'back') {
      this.crack.setVisible(false);
      this.glow.setVisible(false);
    }
    if (this.state !== 'side') this.dot.setVisible(false);
  }

  private place(time: number): ScarOverlay['state'] {
    const host = this.host;
    if (!this.scarKey) return 'none';
    if (!host.visible) return 'hidden';
    const key = host.anims.isPlaying ? (host.anims.currentAnim?.key ?? null) : this.currentKey();
    const parsed = key ? parseAnimKey(key, 'player') : null;
    const def = parsed ? spriteLibrary.sheet('player', parsed.action) : undefined;
    const fi = Number(host.frame?.name);
    if (!parsed || !def || !Number.isFinite(fi)) return 'hidden';
    const row = Math.floor(fi / def.frames);
    const dir = (def.directions[row] as Dir8 | undefined) ?? parsed.dir;
    const column = fi % def.frames;
    this.lastAnchor = { action: parsed.action, dir, column };
    const a = scarAt(def, dir, column);
    if (!a || !a.visible) return 'hidden';
    const k = artScale(def);
    const flip = host.flipX ? -1 : 1;
    const x = host.x + (a.x - def.pivot.x) * k * flip;
    // 56라운드 2단계: 도약 공중 높이만큼 몸과 같이
    const y = host.y + (a.y - def.pivot.y) * k - this.lift;
    const rot = Phaser.Math.DegToRad(a.rot) * flip;
    const pulse = 1 - SCAR_FX.PULSE_AMP * (0.5 - 0.5 * Math.sin((time / 1000) * Math.PI * 2 * SCAR_FX.PULSE_HZ));
    const flicker = 1 - SCAR_FX.FLICKER_AMP * (0.5 + 0.5 * Math.sin(time * 0.0173) * Math.sin(time * 0.0071));
    const alpha = SCAR_FX.ALPHA * pulse * flicker * host.alpha;
    const glowDepth = this.aboveLight ? SCAR_FX.GLOW_DEPTH : host.depth + DEPTH.OVERLAY_STEP * SCAR_FX.DEPTH_STEP;
    if (dir === 'left' || dir === 'right') {
      // 측면: 어깨 쪽 빛만 살짝
      const size = Math.min(a.w, a.h) * k * SCAR_FX.SIDE_SIZE;
      this.dot
        .setPosition(x, y)
        .setDisplaySize(size, size)
        .setAlpha(alpha * SCAR_FX.SIDE_ALPHA)
        .setDepth(glowDepth)
        .setVisible(true);
      return 'side';
    }
    const fit = scarFit({ w: a.w * k, h: a.h * k }, this.aspect);
    const s = fit.h / SCAR_FX.TEX_H;
    for (const img of [this.crack, this.glow])
      img
        .setPosition(x, y)
        .setScale(s * flip, s)
        .setRotation(rot)
        .setVisible(true);
    this.crack.setAlpha(host.alpha).setDepth(host.depth + DEPTH.OVERLAY_STEP * SCAR_FX.DEPTH_STEP);
    this.glow.setAlpha(alpha).setDepth(glowDepth);
    return 'back';
  }
}

/** 상흔 텍스처 키 (획 내용 해시) */
function scarHash(scar: ScarData): string {
  const text = JSON.stringify(scar.strokes) + scar.aspect;
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 16777619);
  return (h >>> 0).toString(36);
}

/** 균열(`<key>_crack`)·빛(`<key>_glow`) 두 장을 굽는다. 이미 있으면 그대로, 다른 런의 상흔 텍스처는 내린다 */
export function bakeScar(scene: Phaser.Scene, scar: ScarData): string {
  const key = `${KEY_PREFIX}${scarHash(scar)}`;
  if (scene.textures.exists(`${key}_crack`)) return key;
  for (const k of scene.textures.getTextureKeys())
    if (k.startsWith(KEY_PREFIX) && k !== DOT_KEY) scene.textures.remove(k);
  const H = SCAR_FX.TEX_H;
  const W = Math.max(1, Math.round(H * (scar.aspect > 0 ? scar.aspect : 1)));
  const P = SCAR_FX.PAD;
  const draw = (suffix: string, paint: (ctx: CanvasRenderingContext2D, path: () => void) => void) => {
    const tex = scene.textures.createCanvas(`${key}_${suffix}`, W + P * 2, H + P * 2)!;
    const ctx = tex.context;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const path = () => {
      ctx.beginPath();
      for (const s of scar.strokes) {
        for (let i = 0; i + 1 < s.length; i += 2) {
          const px = P + s[i] * W;
          const py = P + s[i + 1] * H;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
      }
    };
    paint(ctx, path);
    tex.refresh();
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
  };
  draw('crack', (ctx, path) => {
    path();
    ctx.globalAlpha = SCAR_FX.CRACK_ALPHA;
    ctx.strokeStyle = SCAR_FX.CRACK_COLOR;
    ctx.lineWidth = SCAR_FX.CRACK_WIDTH;
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = SCAR_FX.CORE_COLOR;
    ctx.lineWidth = SCAR_FX.CORE_WIDTH;
    ctx.stroke();
  });
  draw('glow', (ctx, path) => {
    path();
    ctx.shadowColor = SCAR_FX.GLOW_COLOR;
    ctx.shadowBlur = SCAR_FX.GLOW_BLUR;
    ctx.strokeStyle = SCAR_FX.GLOW_COLOR;
    ctx.lineWidth = SCAR_FX.GLOW_WIDTH;
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = SCAR_FX.GLOW_HOT;
    ctx.lineWidth = SCAR_FX.GLOW_HOT_WIDTH;
    ctx.stroke();
  });
  return key;
}

/** 측면용 둥근 빛 점 (흰색 방사형 — 호박 틴트) */
function ensureDot(scene: Phaser.Scene): void {
  if (scene.textures.exists(DOT_KEY)) return;
  const n = 32;
  const tex = scene.textures.createCanvas(DOT_KEY, n, n)!;
  const ctx = tex.context;
  const g = ctx.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
  g.addColorStop(0, 'rgba(255,214,150,1)');
  g.addColorStop(0.35, 'rgba(255,140,50,0.55)');
  g.addColorStop(1, 'rgba(255,120,40,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, n, n);
  tex.refresh();
  tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
}
