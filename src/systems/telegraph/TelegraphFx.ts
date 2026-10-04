/**
 * 공격 예고 마커 (35라운드 2단계 + 42라운드 Q3 "굵고 선명하게", fx-design §6.3, 계약 art-assets.md §3·§3.2 anchor hitbox_center).
 * - `telegraph_line` 16×16 2프레임 루프, 피벗 (0,8) = 공격자, 두께 4px(기존 2px 의 2배). 길이 방향(x)으로 타일링(TileSprite) + 회전.
 *   코어 토막이 목표 쪽으로 흐르도록 프레임을 번갈아 보인다. 끝에 **화살촉**(Graphics 삼각형, 층 램프 22 몸 + 18 테두리).
 * - `telegraph_circle` 64 진행도 6프레임(`progressDriven`), 피벗 중심, 기준 반지름 22 → scale = R/22.
 *   frame = min(5, floor(progress × 6)) — 바깥 점선 링이 범위 링으로 **닫히는** 그림이 시트에 있다.
 * - `telegraph_cone` 64 4방향 진행도 6프레임, 피벗 = 꼭짓점, 기준 반지름 27 → scale = R/27.
 * - `telegraph_aura` 64 4프레임 루프: **수렴 오라**. 공격자 히트박스 중심에 붙어 `aim()` 으로 따라간다.
 *   46라운드 Q3: 보스의 모든 예고(돌진·부채꼴·정렬 사격·내리찍기)에 붙이고, 일반 적은 결사병 돌진만. 내리찍기처럼 마커가
 *   공격자와 떨어진 곳에 있으면 `auraAt` 으로 오라를 공격자 위치에 따로 두고, `aim()` 이 오라를 옮기지 않는다.
 * - 마감 `BOLD.FINAL_MS` 전에는 깜빡임이 `BOLD.FINAL_BLINK_DIV` 배 빨라진다(선 프레임·오라 애니·진행도 시트 알파·화살촉).
 * 전부 바닥 깊이(`DEPTH.FX_GROUND`), 예고 시간이 끝나면 제거(`durationMs`). 시트가 없으면 Graphics 점선(4px)·원(+ 닫히는 안쪽 원)·
 * 부채꼴·오라 원을 같은 주기로 깜빡인다. 핸들의 `aim()` 으로 예고 중 위치·방향을 따라가게 할 수 있다.
 * 57라운드 B8 분리: 꺾은선 예고 `pathTelegraph.ts` · 화살촉·오라·플레이스홀더 도형 `shapes.ts` · 공용 타입 `types.ts`.
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX } from '../../core/Constants';
import { PALETTE } from '../../data';
import { hexToInt, rampFor } from '../palette';
import { spriteLibrary } from '../sprites/sprites';
import {
  FX_ACTION,
  facingOf,
  frameDurations,
  frameIndices,
  fxDrawScale,
  progressFrame,
  type Facing,
} from '../sprites/spriteDefs';
import { PathTelegraphs } from './pathTelegraph';
import {
  auraLabel,
  drawCircle,
  drawClosing,
  drawCone,
  drawDashedLine,
  makeAura,
  makeTip,
  placeholderAlpha,
  speedUpAura,
} from './shapes';
import type {
  AuraObject,
  Point,
  TelegraphHandle,
  TelegraphKind,
  TelegraphOptions,
  TelegraphPathHandle,
  TelegraphStyle,
  TelegraphSummary,
} from './types';

interface Marker {
  kind: TelegraphKind;
  obj: Phaser.GameObjects.TileSprite | Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  createdAt: number;
  expireAt: number;
  /** 기본 깜빡임 주기 (선 프레임·플레이스홀더 알파·화살촉) */
  blinkMs: number;
  nextBlinkAt: number;
  /** 깜빡임 위상 0/1 */
  phase: number;
  texture?: string;
  /** 진행도 주도 시트 (원·부채꼴): 프레임 수·현재 방향 */
  progress?: { id: string; frames: number; dir: Facing };
  /** 플레이스홀더 재그리기 용 */
  draw?: (g: Phaser.GameObjects.Graphics) => void;
  lengthPx: number;
  radiusPx: number;
  halfAngle: number;
  angle: number;
  alive: boolean;
  /** 선 끝 화살촉 / 플레이스홀더 닫히는 원 / 수렴 오라 */
  tip?: Phaser.GameObjects.Graphics;
  closing?: Phaser.GameObjects.Graphics;
  aura?: AuraObject;
  /** 오라가 마커와 떨어져 있음 (auraAt) → aim() 이 옮기지 않는다 */
  auraDetached?: boolean;
  /** 마감 직전(가속) 구간 */
  final: boolean;
}

export class TelegraphFx {
  private readonly markers = new Set<Marker>();
  private paused = false;
  /** 화살촉·플레이스홀더 오라 색 (층 램프) — 경로 예고와 같은 객체를 함께 쓴다 */
  private readonly style: TelegraphStyle = {
    tipColor: ENEMY_FX.PLACEHOLDER.COLOR,
    tipEdge: ENEMY_FX.PLACEHOLDER.COLOR,
  };
  /** 54라운드 꺾은선 예고 */
  private readonly paths: PathTelegraphs;

  constructor(private readonly scene: Phaser.Scene) {
    this.paths = new PathTelegraphs(scene, this.style);
  }

  /** 층 진입: 화살촉 색 = 층 램프 (적·보스 예고는 층 램프 + 코어만, 무기 보조색 금지) */
  setFloor(floor: number): void {
    const ramp = rampFor(PALETTE, floor);
    const B = ENEMY_FX.BOLD;
    const body = ramp?.[B.TIP_RAMP_INDEX];
    const edge = ramp?.[B.TIP_EDGE_RAMP_INDEX];
    this.style.tipColor = body ? hexToInt(body) : ENEMY_FX.PLACEHOLDER.COLOR;
    this.style.tipEdge = edge ? hexToInt(edge) : ENEMY_FX.PLACEHOLDER.COLOR;
  }

  /** 시트 유무 (디버그) */
  has(kind: TelegraphKind | 'aura'): boolean {
    const tex = spriteLibrary.textureKey(kind === 'aura' ? ENEMY_FX.AURA_ID : this.idOf(kind), FX_ACTION);
    return Boolean(tex && this.scene.textures.exists(tex));
  }

  /** 선: 시작점 (x, y) 에서 angle 방향으로 lengthPx */
  line(
    x: number,
    y: number,
    angle: number,
    lengthPx: number,
    durationMs: number,
    opts: TelegraphOptions = {},
  ): TelegraphHandle {
    const id = this.idOf('line');
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    let m: Marker;
    if (def && texture && this.scene.textures.exists(texture)) {
      // 53라운드 v3: 도트 배율 k — 타일 폭은 도트 단위, 화면 굵기는 기존과 같게
      const k = fxDrawScale(def);
      const ts = this.scene.add
        .tileSprite(x, y, Math.max(1, Math.round(lengthPx / k)), def.frameHeight, texture, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(k, ENEMY_FX.BOLD.LINE_SCALE_Y * k)
        .setRotation(angle)
        .setDepth(DEPTH.FX_GROUND);
      m = this.make('line', ts, durationMs, frameDurations(def)[0], texture);
    } else {
      const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND).setPosition(x, y).setRotation(angle);
      m = this.make('line', g, durationMs, ENEMY_FX.PLACEHOLDER.BLINK_MS);
      m.draw = (gg) => drawDashedLine(gg, m.lengthPx);
    }
    m.lengthPx = lengthPx;
    m.angle = angle;
    m.tip = makeTip(this.scene, this.style);
    this.redraw(m);
    this.placeTip(m, x, y);
    this.attachAura(m, x, y, opts);
    return this.handle(m);
  }

  /** 원: 중심 (x, y), 반지름 radiusPx */
  circle(x: number, y: number, radiusPx: number, durationMs: number, opts: TelegraphOptions = {}): TelegraphHandle {
    const m = this.roundMarker('circle', x, y, radiusPx, durationMs, 0, 'down');
    if (!m.progress) {
      // 플레이스홀더 닫히는 원: 남은 시간 비율로 반지름이 줄어드는 안쪽 원 (시트는 그림에 들어 있다)
      m.closing = this.scene.add
        .graphics()
        .setDepth(DEPTH.FX_GROUND + 0.001)
        .setPosition(x, y);
      drawClosing(m.closing, m.radiusPx, 1);
    }
    this.attachAura(m, x, y, opts);
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
    opts: TelegraphOptions = {},
  ): TelegraphHandle {
    if (Phaser.Math.RadToDeg(halfAngleRad) * 2 > ENEMY_FX.CONE_MAX_SPREAD_DEG)
      return this.circle(x, y, radiusPx, durationMs, opts);
    const dir = facingOf(Math.cos(angle), Math.sin(angle), 'down');
    const m = this.roundMarker('cone', x, y, radiusPx, durationMs, halfAngleRad, dir);
    m.angle = angle;
    if (m.obj instanceof Phaser.GameObjects.Graphics) m.obj.setRotation(angle);
    this.attachAura(m, x, y, opts);
    return this.handle(m);
  }

  /** 54라운드: 꺾은선 예고 (points 를 잇는 선, 끝에 화살촉, opts.aura 면 첫 점에 수렴 오라) */
  path(points: readonly Point[], durationMs: number, opts: TelegraphOptions = {}): TelegraphPathHandle {
    return this.paths.create(points, durationMs, opts);
  }

  /** 매 프레임: 만료·진행도 프레임·깜빡임(마감 직전 가속)·닫히는 원 */
  update(time: number): void {
    if (this.paused) return;
    this.paths.update(time);
    const B = ENEMY_FX.BOLD;
    for (const m of this.markers) {
      if (time >= m.expireAt) {
        this.release(m);
        continue;
      }
      const total = m.expireAt - m.createdAt;
      const remaining = m.expireAt - time;
      const progress = total > 0 ? 1 - remaining / total : 1;
      if (!m.final && remaining <= B.FINAL_MS) {
        m.final = true;
        speedUpAura(m.aura);
        m.nextBlinkAt = Math.min(m.nextBlinkAt, time); // 가속 구간 진입 즉시 한 번 깜빡
      }
      if (m.progress && m.obj instanceof Phaser.GameObjects.Sprite) {
        const def = spriteLibrary.sheet(m.progress.id, FX_ACTION);
        if (def) {
          const col = progressFrame(progress, m.progress.frames, B.PROGRESS_DIVISOR);
          const frame = (frameIndices(def, m.progress.dir)[0] ?? 0) + col;
          if (m.obj.frame.name !== String(frame)) m.obj.setFrame(frame);
        }
      }
      if (time >= m.nextBlinkAt) {
        m.nextBlinkAt = time + (m.final ? m.blinkMs / B.FINAL_BLINK_DIV : m.blinkMs);
        m.phase = m.phase === 0 ? 1 : 0;
        this.applyBlink(m);
      }
      if (m.closing) drawClosing(m.closing, m.radiusPx, total > 0 ? remaining / total : 0);
    }
  }

  /** 히트스톱: 시트 애니 정지 */
  setPaused(on: boolean): void {
    this.paused = on;
    this.paths.setPaused(on);
    for (const m of this.markers) {
      for (const s of [m.obj, m.aura]) {
        if (!(s instanceof Phaser.GameObjects.Sprite)) continue;
        if (on) s.anims.pause();
        else s.anims.resume();
      }
    }
  }

  /** 활성 마커 요약 (디버그) */
  summary(): TelegraphSummary[] {
    const now = this.scene.time.now;
    return [
      ...this.paths.summary(now),
      ...[...this.markers].map((m) => {
        const total = m.expireAt - m.createdAt;
        return {
          kind: m.kind,
          x: Math.round(m.obj.x),
          y: Math.round(m.obj.y),
          angle: +m.angle.toFixed(3),
          length: Math.round(m.lengthPx),
          radius: Math.round(m.radiusPx),
          sheet: !(m.obj instanceof Phaser.GameObjects.Graphics),
          remainingMs: Math.max(0, Math.round(m.expireAt - now)),
          final: m.final,
          frame: m.obj instanceof Phaser.GameObjects.Graphics ? null : Number(m.obj.frame.name),
          scale: +m.obj.scaleX.toFixed(3),
          closingRatio: m.closing ? +Math.max(0, Math.min(1, (m.expireAt - now) / total)).toFixed(3) : null,
          tip: Boolean(m.tip),
          aura: auraLabel(m.aura),
          alpha: +m.obj.alpha.toFixed(2),
        };
      }),
    ];
  }

  get count(): number {
    return this.markers.size + this.paths.size;
  }

  /**
   * 50라운드 조명: 예고 마커 자리 (어둠 속에서도 읽히게 경고광을 단다). 선은 가운데·길이 절반, 원·부채꼴은 중심·반경
   */
  lightPoints(): { x: number; y: number; radius: number }[] {
    const out: { x: number; y: number; radius: number }[] = [];
    for (const m of this.markers) {
      if (!m.alive) continue;
      if (m.kind === 'line')
        out.push({
          x: m.obj.x + (Math.cos(m.angle) * m.lengthPx) / 2,
          y: m.obj.y + (Math.sin(m.angle) * m.lengthPx) / 2,
          radius: m.lengthPx / 2,
        });
      else out.push({ x: m.obj.x, y: m.obj.y, radius: m.radiusPx });
    }
    this.paths.lightPoints(out);
    return out;
  }

  destroy(): void {
    for (const m of [...this.markers]) this.release(m);
    this.paths.destroy();
  }

  // --- 내부 ---

  private idOf(kind: TelegraphKind): string {
    const T = ENEMY_FX.TELEGRAPH_IDS;
    return kind === 'line' ? T.LINE : kind === 'circle' ? T.CIRCLE : T.CONE;
  }

  private make(kind: TelegraphKind, obj: Marker['obj'], durationMs: number, blinkMs: number, texture?: string): Marker {
    const now = this.scene.time.now;
    const blink = blinkMs > 0 ? blinkMs : ENEMY_FX.PLACEHOLDER.BLINK_MS;
    const m: Marker = {
      kind,
      obj,
      createdAt: now,
      expireAt: now + durationMs,
      blinkMs: blink,
      nextBlinkAt: now + blink,
      phase: 0,
      texture,
      lengthPx: 0,
      radiusPx: 0,
      halfAngle: 0,
      angle: 0,
      alive: true,
      final: false,
    };
    this.markers.add(m);
    return m;
  }

  /** 원·부채꼴 공통: 시트가 있으면 진행도 프레임 스프라이트(scale = R / 기준 반지름), 없으면 Graphics */
  private roundMarker(
    kind: 'circle' | 'cone',
    x: number,
    y: number,
    radiusPx: number,
    durationMs: number,
    halfAngle: number,
    dir: Facing,
  ): Marker {
    const B = ENEMY_FX.BOLD;
    const id = this.idOf(kind);
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    let m: Marker;
    if (def && texture && this.scene.textures.exists(texture)) {
      const base = kind === 'circle' ? B.CIRCLE_BASE_RADIUS : B.CONE_BASE_RADIUS;
      const s = this.scene.add
        .sprite(x, y, texture, frameIndices(def, dir)[0] ?? 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale((radiusPx / base) * fxDrawScale(def))
        .setDepth(DEPTH.FX_GROUND);
      m = this.make(kind, s, durationMs, ENEMY_FX.PLACEHOLDER.BLINK_MS, texture);
      if (def.progressDriven) m.progress = { id, frames: def.frames, dir };
      else {
        // 진행도 필드가 없는 옛 시트: 루프 애니
        const anim = spriteLibrary.animKey(id, FX_ACTION, dir);
        if (anim) s.play(anim, true);
      }
    } else {
      const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND).setPosition(x, y);
      m = this.make(kind, g, durationMs, ENEMY_FX.PLACEHOLDER.BLINK_MS);
      m.draw = kind === 'circle' ? (gg) => drawCircle(gg, m.radiusPx) : (gg) => drawCone(gg, m.radiusPx, m.halfAngle);
    }
    m.radiusPx = radiusPx;
    m.halfAngle = halfAngle;
    this.redraw(m);
    return m;
  }

  /** opts.aura 면 수렴 오라를 마커 기준점(x, y) 또는 opts.auraAt 에 붙인다 */
  private attachAura(m: Marker, x: number, y: number, opts: TelegraphOptions): void {
    if (!opts.aura) return;
    const at = opts.auraAt;
    m.aura = makeAura(this.scene, at?.x ?? x, at?.y ?? y, this.style);
    m.auraDetached = Boolean(at);
  }

  /** 깜빡임 한 번: 선 시트 프레임 / 플레이스홀더 알파 / 진행도 시트는 가속 구간에서만 알파 / 화살촉·오라 */
  private applyBlink(m: Marker): void {
    const low = m.phase === 1;
    if (m.obj instanceof Phaser.GameObjects.TileSprite) {
      if (m.texture) m.obj.setFrame(m.phase);
      if (m.final) m.obj.setAlpha(low ? ENEMY_FX.BOLD.FINAL_LOW_ALPHA : 1);
    } else if (m.obj instanceof Phaser.GameObjects.Graphics) m.obj.setAlpha(placeholderAlpha(low));
    else m.obj.setAlpha(m.final && low ? ENEMY_FX.BOLD.FINAL_LOW_ALPHA : 1);
    if (m.aura instanceof Phaser.GameObjects.Graphics) m.aura.setAlpha(placeholderAlpha(low));
    m.tip?.setAlpha(low ? 0.6 : 1);
  }

  private placeTip(m: Marker, x: number, y: number): void {
    m.tip
      ?.setPosition(Math.round(x + Math.cos(m.angle) * m.lengthPx), Math.round(y + Math.sin(m.angle) * m.lengthPx))
      .setRotation(m.angle);
  }

  private redraw(m: Marker): void {
    if (m.obj instanceof Phaser.GameObjects.Graphics && m.draw) {
      m.obj.clear();
      m.draw(m.obj);
      m.obj.setAlpha(ENEMY_FX.PLACEHOLDER.ALPHA);
    } else if (m.obj instanceof Phaser.GameObjects.TileSprite) {
      m.obj.setSize(Math.max(1, Math.round(m.lengthPx / m.obj.scaleX)), m.obj.height);
    }
  }

  private handle(m: Marker): TelegraphHandle {
    return {
      kind: m.kind,
      aim: (x, y, angle) => {
        if (!m.alive) return;
        m.obj.setPosition(x, y);
        m.closing?.setPosition(x, y);
        if (!m.auraDetached) m.aura?.setPosition(x, y);
        if (angle !== undefined && m.kind !== 'circle') {
          m.angle = angle;
          if (m.kind === 'line') m.obj.setRotation(angle);
          else if (m.progress) {
            // 4방향 시트: 지배 축이 바뀌면 행을 바꾼다 (프레임은 다음 update 에서 진행도로)
            m.progress.dir = facingOf(Math.cos(angle), Math.sin(angle), 'down');
          } else if (m.obj instanceof Phaser.GameObjects.Sprite) {
            const anim = spriteLibrary.animKey(
              this.idOf('cone'),
              FX_ACTION,
              facingOf(Math.cos(angle), Math.sin(angle), 'down'),
            );
            if (anim && m.obj.anims.currentAnim?.key !== anim) m.obj.play(anim, true);
          } else m.obj.setRotation(angle); // Graphics 부채꼴: +x 기준으로 그려 두고 통째로 회전
        }
        if (m.tip) this.placeTip(m, x, y);
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
    m.tip?.destroy();
    m.closing?.destroy();
    m.aura?.destroy();
  }
}
