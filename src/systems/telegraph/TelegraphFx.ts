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
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_FX } from '../core/Constants';
import { PALETTE } from '../data';
import { hexToInt, rampFor } from './palette';
import { spriteLibrary } from './sprites';
import {
  FX_ACTION,
  facingOf,
  frameDurations,
  frameIndices,
  fxDrawScale,
  progressFrame,
  type Facing,
} from './spriteDefs';

export type TelegraphKind = 'line' | 'circle' | 'cone';

export interface TelegraphOptions {
  /** 공격자 위치(선 시작·부채꼴 꼭짓점·원 중심)에 수렴 오라 (46라운드 Q3: 보스 예고 전부 + 결사병 돌진) */
  aura?: boolean;
  /** 오라를 마커와 다른 곳(공격자)에 둔다 (내리찍기: 원 = 착지점, 오라 = 보스). `aim()` 은 이 오라를 옮기지 않는다 */
  auraAt?: { x: number; y: number };
}

export interface TelegraphHandle {
  readonly kind: TelegraphKind | 'path';
  /** 위치·방향 갱신 (각도 rad, 선·부채꼴만 의미) */
  aim(x: number, y: number, angle?: number): void;
  /** 조기 종료 (경직·사망) */
  end(): void;
  readonly active: boolean;
}

/** 54라운드: 꺾은선·곡선 예고 (휘는 돌진·술통 튕김 경로·술 뿌리기). setPoints 로 예고 중 경로를 다시 그린다 */
export interface TelegraphPathHandle extends TelegraphHandle {
  setPoints(points: readonly { x: number; y: number }[]): void;
}

/** 꺾은선 예고: 선 시트 토막을 마디마다 이어 붙인다 (시트가 없으면 Graphics 점선). 끝에 화살촉 */
interface PathMarker {
  points: { x: number; y: number }[];
  segs: Phaser.GameObjects.TileSprite[];
  gfx: Phaser.GameObjects.Graphics | null;
  tip: Phaser.GameObjects.Graphics;
  aura?: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  texture?: string;
  scale: number;
  originX: number;
  originY: number;
  frameH: number;
  createdAt: number;
  expireAt: number;
  blinkMs: number;
  nextBlinkAt: number;
  phase: number;
  final: boolean;
  alive: boolean;
}

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
  aura?: Phaser.GameObjects.Sprite | Phaser.GameObjects.Graphics;
  /** 오라가 마커와 떨어져 있음 (auraAt) → aim() 이 옮기지 않는다 */
  auraDetached?: boolean;
  /** 마감 직전(가속) 구간 */
  final: boolean;
}

export class TelegraphFx {
  private readonly markers = new Set<Marker>();
  private readonly paths = new Set<PathMarker>();
  private paused = false;
  private tipColor: number = ENEMY_FX.PLACEHOLDER.COLOR;
  private tipEdge: number = ENEMY_FX.PLACEHOLDER.COLOR;

  constructor(private readonly scene: Phaser.Scene) {}

  /** 층 진입: 화살촉 색 = 층 램프 (적·보스 예고는 층 램프 + 코어만, 무기 보조색 금지) */
  setFloor(floor: number): void {
    const ramp = rampFor(PALETTE, floor);
    const B = ENEMY_FX.BOLD;
    const body = ramp?.[B.TIP_RAMP_INDEX];
    const edge = ramp?.[B.TIP_EDGE_RAMP_INDEX];
    this.tipColor = body ? hexToInt(body) : ENEMY_FX.PLACEHOLDER.COLOR;
    this.tipEdge = edge ? hexToInt(edge) : ENEMY_FX.PLACEHOLDER.COLOR;
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
      m.draw = (gg) => this.drawDashedLine(gg, m.lengthPx);
    }
    m.lengthPx = lengthPx;
    m.angle = angle;
    m.tip = this.makeTip();
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
      this.drawClosing(m, 1);
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
  path(
    points: readonly { x: number; y: number }[],
    durationMs: number,
    opts: TelegraphOptions = {},
  ): TelegraphPathHandle {
    const id = this.idOf('line');
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    const now = this.scene.time.now;
    const sheet = Boolean(def && texture && this.scene.textures.exists(texture));
    const blink = sheet ? frameDurations(def!)[0] || ENEMY_FX.PLACEHOLDER.BLINK_MS : ENEMY_FX.PLACEHOLDER.BLINK_MS;
    const m: PathMarker = {
      points: [],
      segs: [],
      gfx: sheet ? null : this.scene.add.graphics().setDepth(DEPTH.FX_GROUND),
      tip: this.makeTip(),
      texture: sheet ? texture! : undefined,
      scale: sheet ? fxDrawScale(def!) : 1,
      originX: sheet ? def!.pivot.x / def!.frameWidth : 0,
      originY: sheet ? def!.pivot.y / def!.frameHeight : 0,
      frameH: sheet ? def!.frameHeight : 0,
      createdAt: now,
      expireAt: now + durationMs,
      blinkMs: blink,
      nextBlinkAt: now + blink,
      phase: 0,
      final: false,
      alive: true,
    };
    this.paths.add(m);
    this.drawPath(m, points);
    if (opts.aura && points.length > 0)
      m.aura = this.makeAura(opts.auraAt?.x ?? points[0].x, opts.auraAt?.y ?? points[0].y);
    return {
      kind: 'path',
      aim: (x, y) => {
        if (!m.alive || m.points.length === 0) return;
        const dx = x - m.points[0].x;
        const dy = y - m.points[0].y;
        this.drawPath(
          m,
          m.points.map((p) => ({ x: p.x + dx, y: p.y + dy })),
        );
      },
      setPoints: (pts) => {
        if (m.alive) this.drawPath(m, pts);
      },
      end: () => this.releasePath(m),
      get active() {
        return m.alive;
      },
    };
  }

  private drawPath(m: PathMarker, points: readonly { x: number; y: number }[]): void {
    m.points = points.map((p) => ({ x: p.x, y: p.y }));
    const n = Math.max(0, m.points.length - 1);
    if (m.texture) {
      while (m.segs.length < n)
        m.segs.push(
          this.scene.add
            .tileSprite(0, 0, 1, m.frameH, m.texture, m.phase)
            .setOrigin(m.originX, m.originY)
            .setScale(m.scale, ENEMY_FX.BOLD.LINE_SCALE_Y * m.scale)
            .setDepth(DEPTH.FX_GROUND),
        );
      for (let i = 0; i < m.segs.length; i++) {
        const seg = m.segs[i];
        if (i >= n) {
          seg.setVisible(false);
          continue;
        }
        const a = m.points[i];
        const b = m.points[i + 1];
        const len = Math.hypot(b.x - a.x, b.y - a.y);
        // 마디 사이 틈이 보이지 않게 1px 겹친다
        seg
          .setVisible(len > 0.01)
          .setPosition(a.x, a.y)
          .setRotation(Math.atan2(b.y - a.y, b.x - a.x))
          .setSize(Math.max(1, Math.round((len + 1) / m.scale)), m.frameH);
      }
    } else if (m.gfx) {
      const g = m.gfx;
      const P = ENEMY_FX.PLACEHOLDER;
      g.clear();
      g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
      // 점선: 누적 거리로 DASH·GAP 을 이어 간다
      let acc = 0;
      for (let i = 0; i < n; i++) {
        const a = m.points[i];
        const b = m.points[i + 1];
        const len = Math.hypot(b.x - a.x, b.y - a.y);
        if (len <= 0) continue;
        const ux = (b.x - a.x) / len;
        const uy = (b.y - a.y) / len;
        for (let t = 0; t < len;) {
          const cyc = (acc + t) % (P.DASH_PX + P.GAP_PX);
          if (cyc < P.DASH_PX) {
            const e = Math.min(len, t + (P.DASH_PX - cyc));
            g.beginPath();
            g.moveTo(a.x + ux * t, a.y + uy * t);
            g.lineTo(a.x + ux * e, a.y + uy * e);
            g.strokePath();
            t = e;
          } else t += P.DASH_PX + P.GAP_PX - cyc;
        }
        acc += len;
      }
      g.setAlpha(P.ALPHA);
    }
    if (n >= 1) {
      const a = m.points[n - 1];
      const b = m.points[n];
      m.tip
        .setVisible(true)
        .setPosition(Math.round(b.x), Math.round(b.y))
        .setRotation(Math.atan2(b.y - a.y, b.x - a.x));
    } else m.tip.setVisible(false);
  }

  private updatePath(m: PathMarker, time: number): void {
    const B = ENEMY_FX.BOLD;
    if (time >= m.expireAt) {
      this.releasePath(m);
      return;
    }
    if (!m.final && m.expireAt - time <= B.FINAL_MS) {
      m.final = true;
      if (m.aura instanceof Phaser.GameObjects.Sprite) m.aura.anims.timeScale = B.FINAL_BLINK_DIV;
      m.nextBlinkAt = Math.min(m.nextBlinkAt, time);
    }
    if (time < m.nextBlinkAt) return;
    m.nextBlinkAt = time + (m.final ? m.blinkMs / B.FINAL_BLINK_DIV : m.blinkMs);
    m.phase = m.phase === 0 ? 1 : 0;
    const low = m.phase === 1;
    for (const seg of m.segs) {
      seg.setFrame(m.phase);
      if (m.final) seg.setAlpha(low ? B.FINAL_LOW_ALPHA : 1);
    }
    m.gfx?.setAlpha(low ? ENEMY_FX.PLACEHOLDER.ALPHA * 0.45 : ENEMY_FX.PLACEHOLDER.ALPHA);
    if (m.aura instanceof Phaser.GameObjects.Graphics)
      m.aura.setAlpha(low ? ENEMY_FX.PLACEHOLDER.ALPHA * 0.45 : ENEMY_FX.PLACEHOLDER.ALPHA);
    m.tip.setAlpha(low ? 0.6 : 1);
  }

  private releasePath(m: PathMarker): void {
    if (!m.alive) return;
    m.alive = false;
    this.paths.delete(m);
    for (const s of m.segs) s.destroy();
    m.gfx?.destroy();
    m.tip.destroy();
    m.aura?.destroy();
  }

  /** 매 프레임: 만료·진행도 프레임·깜빡임(마감 직전 가속)·닫히는 원 */
  update(time: number): void {
    if (this.paused) return;
    for (const p of [...this.paths]) this.updatePath(p, time);
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
        if (m.aura instanceof Phaser.GameObjects.Sprite) m.aura.anims.timeScale = B.FINAL_BLINK_DIV;
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
      if (m.closing) this.drawClosing(m, total > 0 ? remaining / total : 0);
    }
  }

  /** 히트스톱: 시트 애니 정지 */
  setPaused(on: boolean): void {
    this.paused = on;
    for (const p of this.paths)
      if (p.aura instanceof Phaser.GameObjects.Sprite) {
        if (on) p.aura.anims.pause();
        else p.aura.anims.resume();
      }
    for (const m of this.markers) {
      for (const s of [m.obj, m.aura]) {
        if (!(s instanceof Phaser.GameObjects.Sprite)) continue;
        if (on) s.anims.pause();
        else s.anims.resume();
      }
    }
  }

  /** 활성 마커 요약 (디버그) */
  summary(): {
    kind: TelegraphKind | 'path';
    x: number;
    y: number;
    angle: number;
    length: number;
    radius: number;
    sheet: boolean;
    remainingMs: number;
    final: boolean;
    frame: number | null;
    scale: number;
    closingRatio: number | null;
    tip: boolean;
    aura: string | null;
    alpha: number;
    points?: number;
  }[] {
    const now = this.scene.time.now;
    const paths = [...this.paths].map((m) => {
      const first = m.points[0] ?? { x: 0, y: 0 };
      const last = m.points[m.points.length - 1] ?? first;
      let length = 0;
      for (let i = 1; i < m.points.length; i++)
        length += Math.hypot(m.points[i].x - m.points[i - 1].x, m.points[i].y - m.points[i - 1].y);
      return {
        kind: 'path' as const,
        x: Math.round(first.x),
        y: Math.round(first.y),
        angle: +Math.atan2(last.y - first.y, last.x - first.x).toFixed(3),
        length: Math.round(length),
        radius: 0,
        sheet: m.segs.length > 0,
        remainingMs: Math.max(0, Math.round(m.expireAt - now)),
        final: m.final,
        frame: m.segs.length > 0 ? m.phase : null,
        scale: m.scale,
        closingRatio: null,
        tip: true,
        aura: m.aura ? (m.aura instanceof Phaser.GameObjects.Sprite ? m.aura.texture.key : 'graphics') : null,
        alpha: 1,
        points: m.points.length,
      };
    });
    return [
      ...paths,
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
          aura: m.aura ? (m.aura instanceof Phaser.GameObjects.Sprite ? m.aura.texture.key : 'graphics') : null,
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
    // 꺾은선: 마디 몇 군데 (어둠 속에서도 경로 전체가 읽히게)
    for (const m of this.paths) {
      if (!m.alive || m.points.length === 0) continue;
      const step = Math.max(1, Math.floor(m.points.length / ENEMY_FX.PATH_LIGHT_POINTS));
      for (let i = 0; i < m.points.length; i += step) out.push({ x: m.points[i].x, y: m.points[i].y, radius: 0 });
    }
    return out;
  }

  destroy(): void {
    for (const m of [...this.markers]) this.release(m);
    for (const m of [...this.paths]) this.releasePath(m);
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

  /** opts.aura 면 수렴 오라를 마커 기준점(x, y) 또는 opts.auraAt 에 붙인다 */
  private attachAura(m: Marker, x: number, y: number, opts: TelegraphOptions): void {
    if (!opts.aura) return;
    const at = opts.auraAt;
    m.aura = this.makeAura(at?.x ?? x, at?.y ?? y);
    m.auraDetached = Boolean(at);
  }

  /** 수렴 오라: telegraph_aura 시트(루프, 배율 AURA_SCALE) → 없으면 Graphics 원 */
  private makeAura(x: number, y: number): Marker['aura'] {
    const B = ENEMY_FX.BOLD;
    const id = ENEMY_FX.AURA_ID;
    const def = spriteLibrary.sheet(id, FX_ACTION);
    const texture = spriteLibrary.textureKey(id, FX_ACTION);
    const anim = spriteLibrary.animKey(id, FX_ACTION, 'down');
    if (def && texture && anim && this.scene.textures.exists(texture)) {
      const s = this.scene.add
        .sprite(x, y, texture, 0)
        .setOrigin(def.pivot.x / def.frameWidth, def.pivot.y / def.frameHeight)
        .setScale(B.AURA_SCALE * fxDrawScale(def))
        .setDepth(DEPTH.FX_GROUND + 0.002);
      s.play(anim, true);
      return s;
    }
    const g = this.scene.add
      .graphics()
      .setDepth(DEPTH.FX_GROUND + 0.002)
      .setPosition(x, y);
    g.lineStyle(ENEMY_FX.PLACEHOLDER.LINE_WIDTH, this.tipColor, 1);
    g.strokeCircle(0, 0, B.AURA_PLACEHOLDER_RADIUS);
    g.setAlpha(ENEMY_FX.PLACEHOLDER.ALPHA);
    return g;
  }

  /** 화살촉: +x 를 향한 삼각형(끝 = 원점), 층 램프 몸 + 테두리 1px */
  private makeTip(): Phaser.GameObjects.Graphics {
    const B = ENEMY_FX.BOLD;
    const g = this.scene.add.graphics().setDepth(DEPTH.FX_GROUND + 0.001);
    g.fillStyle(this.tipColor, 1);
    g.fillTriangle(0, 0, -B.TIP_LENGTH, -B.TIP_HALF_WIDTH, -B.TIP_LENGTH, B.TIP_HALF_WIDTH);
    g.lineStyle(1, this.tipEdge, 1);
    g.strokeTriangle(0, 0, -B.TIP_LENGTH, -B.TIP_HALF_WIDTH, -B.TIP_LENGTH, B.TIP_HALF_WIDTH);
    return g;
  }

  /** 깜빡임 한 번: 선 시트 프레임 / 플레이스홀더 알파 / 진행도 시트는 가속 구간에서만 알파 / 화살촉·오라 */
  private applyBlink(m: Marker): void {
    const P = ENEMY_FX.PLACEHOLDER;
    const low = m.phase === 1;
    if (m.obj instanceof Phaser.GameObjects.TileSprite) {
      if (m.texture) m.obj.setFrame(m.phase);
      if (m.final) m.obj.setAlpha(low ? ENEMY_FX.BOLD.FINAL_LOW_ALPHA : 1);
    } else if (m.obj instanceof Phaser.GameObjects.Graphics) m.obj.setAlpha(low ? P.ALPHA * 0.45 : P.ALPHA);
    else m.obj.setAlpha(m.final && low ? ENEMY_FX.BOLD.FINAL_LOW_ALPHA : 1);
    if (m.aura instanceof Phaser.GameObjects.Graphics) m.aura.setAlpha(low ? P.ALPHA * 0.45 : P.ALPHA);
    m.tip?.setAlpha(low ? 0.6 : 1);
  }

  private drawClosing(m: Marker, ratio: number): void {
    const g = m.closing;
    if (!g) return;
    const B = ENEMY_FX.BOLD;
    const r = Math.max(1, Math.round(m.radiusPx * Math.max(B.CLOSING_MIN_RATIO, ratio)));
    g.clear();
    g.fillStyle(ENEMY_FX.PLACEHOLDER.COLOR, B.CLOSING_FILL_ALPHA);
    g.fillCircle(0, 0, r);
    g.lineStyle(B.CLOSING_LINE_WIDTH, ENEMY_FX.PLACEHOLDER.COLOR, B.CLOSING_LINE_ALPHA);
    g.strokeCircle(0, 0, r);
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

  // --- 플레이스홀더 (시트가 없을 때) ---

  private drawDashedLine(g: Phaser.GameObjects.Graphics, lengthPx: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
    for (let x = 0; x < lengthPx; x += P.DASH_PX + P.GAP_PX) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(Math.min(lengthPx, x + P.DASH_PX), 0);
      g.strokePath();
    }
  }

  private drawCircle(g: Phaser.GameObjects.Graphics, r: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
    g.strokeCircle(0, 0, r);
  }

  private drawCone(g: Phaser.GameObjects.Graphics, r: number, half: number): void {
    const P = ENEMY_FX.PLACEHOLDER;
    g.lineStyle(ENEMY_FX.BOLD.PLACEHOLDER_LINE_WIDTH, P.COLOR, 1);
    g.beginPath();
    g.moveTo(0, 0);
    g.lineTo(Math.cos(-half) * r, Math.sin(-half) * r);
    g.arc(0, 0, r, -half, half, false);
    g.lineTo(0, 0);
    g.strokePath();
  }
}
