/**
 * 공격 예고 마커 (35라운드 2단계, 계약 art-assets.md §3 anchor hitbox_center, spawn telegraph).
 * - `telegraph_line` 8×8 2프레임 루프, 피벗 (0,4) = 공격자. 길이 방향(x)으로 타일링(TileSprite) + 회전 → 돌진 경로·조준선.
 * - `telegraph_circle` 32×32 2프레임 루프, 피벗 중심. 반지름 15 기준 scale = R / 15 → 내리찍기 범위.
 * - `telegraph_cone` 32×32 4방향 2프레임 루프, 피벗 = 꼭짓점. 반각 32°·반지름 15 기준 scale → 부채꼴 발사.
 * 전부 바닥 깊이(`DEPTH.FX_GROUND`), 예고 시간이 끝나면 제거(`durationMs`). 시트가 없으면 Graphics 점선·원·부채꼴을
 * 같은 주기로 깜빡인다. 핸들의 `aim()` 으로 예고 중 위치·방향을 따라가게 할 수 있다(결사병 돌진 방향은 예고 끝에 정해진다).
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX } from '../core/Constants';
import { spriteLibrary } from './sprites';
import { FX_ACTION, facingOf, frameDurations, type Facing } from './spriteDefs';

export type TelegraphKind = 'line' | 'circle' | 'cone';

export interface TelegraphHandle {
  readonly kind: TelegraphKind;
  /** 위치·방향 갱신 (각도 rad, 선·부채꼴만 의미) */
  aim(x: number, y: number, angle?: number): void;
  /** 조기 종료 (경직·사망) */
  end(): void;
  readonly active: boolean;
}

interface Marker {
  kind: TelegraphKind;
  obj: Phaser.GameObjects.TileSprite | Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  expireAt: number;
  /** 플레이스홀더·TileSprite 의 프레임 깜빡임 */
  blinkMs: number;
  nextBlinkAt: number;
  frame: number;
  texture?: string;
  /** 플레이스홀더 재그리기 용 */
  draw?: (g: Phaser.GameObjects.Graphics) => void;
  lengthPx: number;
  radiusPx: number;
  halfAngle: number;
  angle: number;
  alive: boolean;
}

export class TelegraphFx {
  private readonly markers = new Set<Marker>();
  private paused = false;

  constructor(private readonly scene: Phaser.Scene) {}

  /** 시트 유무 (디버그) */
  has(kind: TelegraphKind): boolean {
    const tex = spriteLibrary.textureKey(this.idOf(kind), FX_ACTION);
    return Boolean(tex && this.scene.textures.exists(tex));
  }

  /** 선: 시작점 (x, y) 에서 angle 방향으로 lengthPx */
  line(x: number, y: number, angle: number, lengthPx: number, durationMs: number): TelegraphHandle {
    const id = this.idOf('line');
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    let m: Marker;
    if (def && texture && this.scene.textures.exists(texture)) {
      const ts = this.scene.add
        .tileSprite(x, y, Math.max(1, Math.round(lengthPx)), def.frameHeight, texture, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setRotation(angle)
        .setDepth(DEPTH.FX_GROUND);
      m = this.make('line', ts, durationMs, frameDurations(def)[0], texture);
    } else {
      const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND).setPosition(x, y).setRotation(angle);
      m = this.make('line', g, durationMs, ENEMY_FX.PLACEHOLDER.BLINK_MS);
      m.draw = (gg) => this.drawDashedLine(gg, m.lengthPx);
    }
    m.lengthPx = lengthPx;
    m.angle = angle;
    this.redraw(m);
    return this.handle(m);
  }

  /** 원: 중심 (x, y), 반지름 radiusPx */
  circle(x: number, y: number, radiusPx: number, durationMs: number): TelegraphHandle {
    const m = this.roundMarker('circle', x, y, radiusPx, durationMs, 0, 'down');
    return this.handle(m);
  }

  /**
   * 부채꼴: 꼭짓점 (x, y), angle 방향, 반각 halfAngleRad, 반지름 radiusPx.
   * 시트는 4방향 행이라 지배 축 방향으로 놓이고(각도는 행 선택에만), 반각이 시트 기준(32°)을 크게 넘으면 원으로 대신한다
   */
  cone(
    x: number,
    y: number,
    angle: number,
    halfAngleRad: number,
    radiusPx: number,
    durationMs: number,
  ): TelegraphHandle {
    if (Phaser.Math.RadToDeg(halfAngleRad) * 2 > ENEMY_FX.CONE_MAX_SPREAD_DEG)
      return this.circle(x, y, radiusPx, durationMs);
    const dir = facingOf(Math.cos(angle), Math.sin(angle), 'down');
    const m = this.roundMarker('cone', x, y, radiusPx, durationMs, halfAngleRad, dir);
    m.angle = angle;
    if (m.obj instanceof Phaser.GameObjects.Graphics) m.obj.setRotation(angle);
    return this.handle(m);
  }

  /** 매 프레임: 만료·깜빡임 */
  update(time: number): void {
    if (this.paused) return;
    for (const m of this.markers) {
      if (time >= m.expireAt) {
        this.release(m);
        continue;
      }
      if (time >= m.nextBlinkAt) {
        m.nextBlinkAt = time + m.blinkMs;
        m.frame = m.frame === 0 ? 1 : 0;
        if (m.obj instanceof Phaser.GameObjects.TileSprite && m.texture) m.obj.setFrame(m.frame);
        else if (m.obj instanceof Phaser.GameObjects.Graphics)
          m.obj.setAlpha(m.frame === 0 ? ENEMY_FX.PLACEHOLDER.ALPHA : ENEMY_FX.PLACEHOLDER.ALPHA * 0.45);
      }
    }
  }

  /** 히트스톱: 깜빡임·만료 정지 (호출 쪽이 update 를 건너뛰어도 되지만 애니 스프라이트는 여기서 멈춘다) */
  setPaused(on: boolean): void {
    this.paused = on;
    for (const m of this.markers) {
      if (m.obj instanceof Phaser.GameObjects.Sprite) {
        if (on) m.obj.anims.pause();
        else m.obj.anims.resume();
      }
    }
  }

  /** 활성 마커 요약 (디버그) */
  summary(): {
    kind: TelegraphKind;
    x: number;
    y: number;
    angle: number;
    length: number;
    radius: number;
    sheet: boolean;
  }[] {
    return [...this.markers].map((m) => ({
      kind: m.kind,
      x: Math.round(m.obj.x),
      y: Math.round(m.obj.y),
      angle: +m.angle.toFixed(3),
      length: Math.round(m.lengthPx),
      radius: Math.round(m.radiusPx),
      sheet: !(m.obj instanceof Phaser.GameObjects.Graphics),
    }));
  }

  get count(): number {
    return this.markers.size;
  }

  destroy(): void {
    for (const m of [...this.markers]) this.release(m);
  }

  // --- 내부 ---

  private idOf(kind: TelegraphKind): string {
    const T = ENEMY_FX.TELEGRAPH_IDS;
    return kind === 'line' ? T.LINE : kind === 'circle' ? T.CIRCLE : T.CONE;
  }

  private make(kind: TelegraphKind, obj: Marker['obj'], durationMs: number, blinkMs: number, texture?: string): Marker {
    const now = this.scene.time.now;
    const m: Marker = {
      kind,
      obj,
      expireAt: now + durationMs,
      blinkMs: blinkMs > 0 ? blinkMs : ENEMY_FX.PLACEHOLDER.BLINK_MS,
      nextBlinkAt: now + (blinkMs > 0 ? blinkMs : ENEMY_FX.PLACEHOLDER.BLINK_MS),
      frame: 0,
      texture,
      lengthPx: 0,
      radiusPx: 0,
      halfAngle: 0,
      angle: 0,
      alive: true,
    };
    this.markers.add(m);
    return m;
  }

  /** 원·부채꼴 공통: 시트가 있으면 애니 스프라이트(scale = R / 기준 반지름), 없으면 Graphics */
  private roundMarker(
    kind: 'circle' | 'cone',
    x: number,
    y: number,
    radiusPx: number,
    durationMs: number,
    halfAngle: number,
    dir: Facing,
  ): Marker {
    const id = this.idOf(kind);
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    const anim = spriteLibrary.animKey(id, FX_ACTION, dir);
    let m: Marker;
    if (def && texture && anim && this.scene.textures.exists(texture)) {
      const s = this.scene.add
        .sprite(x, y, texture, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(radiusPx / ENEMY_FX.MARKER_BASE_RADIUS)
        .setDepth(DEPTH.FX_GROUND);
      s.play(anim, true);
      m = this.make(kind, s, durationMs, frameDurations(def)[0], texture);
    } else {
      const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND).setPosition(x, y);
      m = this.make(kind, g, durationMs, ENEMY_FX.PLACEHOLDER.BLINK_MS);
      m.draw =
        kind === 'circle'
          ? (gg) => this.drawCircle(gg, m.radiusPx)
          : (gg) => this.drawCone(gg, m.radiusPx, m.halfAngle);
    }
    m.radiusPx = radiusPx;
    m.halfAngle = halfAngle;
    this.redraw(m);
    return m;
  }

  private redraw(m: Marker): void {
    if (m.obj instanceof Phaser.GameObjects.Graphics && m.draw) {
      m.obj.clear();
      m.draw(m.obj);
      m.obj.setAlpha(ENEMY_FX.PLACEHOLDER.ALPHA);
    } else if (m.obj instanceof Phaser.GameObjects.TileSprite) {
      m.obj.setSize(Math.max(1, Math.round(m.lengthPx)), m.obj.height);
    }
  }

  private handle(m: Marker): TelegraphHandle {
    return {
      kind: m.kind,
      aim: (x, y, angle) => {
        if (!m.alive) return;
        m.obj.setPosition(x, y);
        if (angle !== undefined && m.kind !== 'circle') {
          m.angle = angle;
          if (m.kind === 'line') m.obj.setRotation(angle);
          else if (m.obj instanceof Phaser.GameObjects.Sprite) {
            // 4방향 시트: 지배 축이 바뀌면 행을 바꾼다
            const anim = spriteLibrary.animKey(
              this.idOf('cone'),
              FX_ACTION,
              facingOf(Math.cos(angle), Math.sin(angle), 'down'),
            );
            if (anim && m.obj.anims.currentAnim?.key !== anim) m.obj.play(anim, true);
          } else m.obj.setRotation(angle); // Graphics 부채꼴: +x 기준으로 그려 두고 통째로 회전
        }
      },
      end: () => this.release(m),
      get active() {
        return m.alive;
      },
    };
  }

  private release(m: Marker): void {
    if (!m.alive) return;
    m.alive = false;
    this.markers.delete(m);
    m.obj.destroy();
  }

  // --- 플레이스홀더 (시트가 없을 때) ---

  private drawDashedLine(g: Phaser.GameObjects.Graphics, lengthPx: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(P.LINE_WIDTH, P.COLOR, 1);
    for (let x = 0; x < lengthPx; x += P.DASH_PX + P.GAP_PX) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(Math.min(lengthPx, x + P.DASH_PX), 0);
      g.strokePath();
    }
  }

  private drawCircle(g: Phaser.GameObjects.Graphics, r: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(P.LINE_WIDTH, P.COLOR, 1);
    g.strokeCircle(0, 0, r);
  }

  private drawCone(g: Phaser.GameObjects.Graphics, r: number, half: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(P.LINE_WIDTH, P.COLOR, 1);
    g.beginPath();
    g.moveTo(0, 0);
    g.lineTo(Math.cos(-half) * r, Math.sin(-half) * r);
    g.arc(0, 0, r, -half, half, false);
    g.lineTo(0, 0);
    g.strokePath();
  }
}
