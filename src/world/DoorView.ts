/**
 * 62 루프 2 시스템 E — 외벽 문 연출 (그림 쪽). 문 그림 자체는 외벽 테두리(BorderView — `doors.<west|east>`)가 그리고,
 * 여기서는 그 위에 닫힘 막힘 판 · 열린 문 빛 · '오르는 길' 방향 갈매기를 얹는다. 문 그림이 없으면(테두리 없음·로드 실패)
 * 문 자리를 어둠으로 파 둔다 (가장 가까운 외벽 틈 — 벽 칸은 그대로 막힌 채, 지나가는 것은 자동 걸음만).
 * 배치는 `systems/doors/doorPlan` (Phaser 없음).
 * 62 루프 2 F (art §31-10): 테두리에 널문 그림(닫힘 덮개·열림 시트)이 있으면 도형 막힘 판 대신 그 그림을 열고 닫는다(`DoorLeafControl`).
 */
import Phaser from 'phaser';
import { DOORS, TILE, entityDepth } from '../core/Constants';
import { lightRegistryOf, type LightSource } from '../systems/lighting/lightRegistry';
import type { DoorSpot } from '../systems/doors/doorPlan';

/** 널문 그림 (BorderView — 그림이 늦게 와도 상태를 기억한다) */
export interface DoorLeafControl {
  setOpen(open: boolean, animate: boolean): void;
}

export class DoorView {
  /** 도형 막힘 판 — 널문 그림이 있으면 null */
  private readonly barrier: Phaser.GameObjects.Graphics | null;
  private readonly dark: Phaser.GameObjects.Graphics | null;
  private readonly chevrons: Phaser.GameObjects.Graphics;
  private light: LightSource | null = null;
  private readonly tweens: Phaser.Tweens.Tween[] = [];
  private chevronTween: Phaser.Tweens.Tween | null = null;
  isOpen = false;
  /** 막힘 판·어둠 깊이: 문 그림 위 (그림이 없으면 그 줄의 쿼터뷰 벽 그림 위 — Y 정렬) */
  private readonly depth: number;

  constructor(
    private readonly scene: Phaser.Scene,
    readonly spot: DoorSpot,
    /** 문 그림이 있는가 (없으면 어둠으로 문 자리) */
    hasArt: boolean,
    open: boolean,
    /** 널문 그림 (art §31-10) — 있으면 도형 막힘 판을 그리지 않는다 */
    private readonly leaf: DoorLeafControl | null = null,
  ) {
    this.depth = hasArt ? DOORS.DEPTH_BARRIER : entityDepth(spot.span[1]) + 1e-4;
    this.dark = hasArt ? null : this.drawDark();
    this.barrier = leaf ? null : this.drawBarrier();
    leaf?.setOpen(false, false);
    this.chevrons = this.drawChevrons();
    this.chevrons.setAlpha(0).setVisible(false);
    if (open) this.open(false);
  }

  /** 막힘 판의 사각형 (월드): 바닥 끝 선에서 바깥으로 BARRIER_DEPTH_TILES, 문 폭 전체 */
  private openingRect(depthPx: number): Phaser.Geom.Rectangle {
    const s = this.spot;
    const [a0, a1] = s.span;
    const m = s.mouth;
    if (s.out.x !== 0) {
      const x = s.out.x > 0 ? m.x : m.x - depthPx;
      return new Phaser.Geom.Rectangle(x, a0, depthPx, a1 - a0);
    }
    const y = s.out.y > 0 ? m.y : m.y - depthPx;
    return new Phaser.Geom.Rectangle(a0, y, a1 - a0, depthPx);
  }

  /** 문 그림이 없을 때: 문 자리 어둠 (바깥으로 갈수록 짙게) */
  private drawDark(): Phaser.GameObjects.Graphics {
    const r = this.openingRect(DOORS.FALLBACK_DARK_PX);
    const g = this.scene.add.graphics().setDepth(this.depth);
    const c = DOORS.BARRIER_COLOR;
    const o = this.spot.out;
    // 바깥 끝 = 알파 1, 바닥 끝 = 0.55 (fillGradientStyle: 왼위·오위·왼아래·오아래)
    const near = 0.55;
    const a =
      o.x > 0 ? [near, 1, near, 1] : o.x < 0 ? [1, near, 1, near] : o.y > 0 ? [near, near, 1, 1] : [1, 1, near, near];
    g.fillGradientStyle(c, c, c, c, a[0], a[1], a[2], a[3]);
    g.fillRect(r.x, r.y, r.width, r.height);
    return g;
  }

  /**
   * 닫힌 문: 문 안 어둠(바깥으로 갈수록 짙게) + 바닥 끝 선을 따라 선 널문 (벽과 나란한 판자 BARRIER_PLANKS 장 — 문을 막는다)
   */
  private drawBarrier(): Phaser.GameObjects.Graphics {
    const r = this.openingRect(DOORS.BARRIER_DEPTH_TILES * TILE);
    const g = this.scene.add.graphics().setDepth(this.depth + 1e-5);
    const c = DOORS.BARRIER_COLOR;
    const o = this.spot.out;
    const near = DOORS.BARRIER_ALPHA * 0.7;
    const far = DOORS.BARRIER_ALPHA;
    const a =
      o.x > 0
        ? [near, far, near, far]
        : o.x < 0
          ? [far, near, far, near]
          : o.y > 0
            ? [near, near, far, far]
            : [far, far, near, near];
    g.fillGradientStyle(c, c, c, c, a[0], a[1], a[2], a[3]);
    g.fillRect(r.x, r.y, r.width, r.height);
    // 널문: 바닥 끝 선 바로 바깥에 벽과 나란한 판자 (두께 PLANK_PX, 사이 PLANK_GAP_PX)
    g.fillStyle(DOORS.BARRIER_PLANK_COLOR, 1);
    const m = this.spot.mouth;
    const [a0, a1] = this.spot.span;
    for (let i = 0; i < DOORS.BARRIER_PLANKS; i++) {
      const d = 1 + i * (DOORS.PLANK_PX + DOORS.PLANK_GAP_PX);
      if (o.x !== 0) {
        const x = o.x > 0 ? m.x + d : m.x - d - DOORS.PLANK_PX;
        g.fillRect(x, a0 + 1, DOORS.PLANK_PX, a1 - a0 - 2);
      } else {
        const y = o.y > 0 ? m.y + d : m.y - d - DOORS.PLANK_PX;
        g.fillRect(a0 + 1, y, a1 - a0 - 2, DOORS.PLANK_PX);
      }
    }
    return g;
  }

  /** '오르는 길': 문턱 앞 바닥 갈매기 (바깥을 가리킴) */
  private drawChevrons(): Phaser.GameObjects.Graphics {
    const g = this.scene.add.graphics().setDepth(DOORS.DEPTH_CHEVRON);
    const s = this.spot;
    const o = s.out;
    const px = { x: -o.y, y: o.x }; // 문 폭 방향
    g.lineStyle(DOORS.CHEVRON_LINE_PX, DOORS.CHEVRON_COLOR, 1);
    for (let i = 0; i < DOORS.CHEVRON_COUNT; i++) {
      // 바닥 끝 선에서 안쪽으로 (가장 안쪽이 첫째)
      const back = TILE * 0.9 + (DOORS.CHEVRON_COUNT - 1 - i) * DOORS.CHEVRON_GAP_PX;
      const tip = { x: s.mouth.x - o.x * back, y: s.mouth.y - o.y * back };
      const tail = { x: tip.x - o.x * DOORS.CHEVRON_LEN_PX, y: tip.y - o.y * DOORS.CHEVRON_LEN_PX };
      const h = DOORS.CHEVRON_HALF_PX;
      g.beginPath();
      g.moveTo(tail.x + px.x * h, tail.y + px.y * h);
      g.lineTo(tip.x, tip.y);
      g.lineTo(tail.x - px.x * h, tail.y - px.y * h);
      g.strokePath();
    }
    return g;
  }

  /** 문 열림: 막힘 판이 바깥으로 밀리며 걷히고, 빛이 차오르고, 갈매기가 맥박친다 */
  open(animate = true): void {
    if (this.isOpen) return;
    this.isOpen = true;
    const scene = this.scene;
    const o = this.spot.out;
    const ms = animate ? DOORS.OPEN_MS : 0;
    const reg = lightRegistryOf(scene);
    this.light = reg.add(
      { color: DOORS.LIGHT_COLOR, radius: DOORS.LIGHT_RADIUS_PX, intensity: 0, flicker: DOORS.LIGHT_FLICKER },
      { x: this.spot.mouth.x + o.x * TILE * 0.5, y: this.spot.mouth.y + o.y * TILE * 0.5 },
    );
    const light = this.light;
    this.leaf?.setOpen(true, ms > 0);
    const barrier = this.barrier;
    if (ms <= 0) {
      barrier?.setAlpha(0).setVisible(false);
      light.intensity = DOORS.LIGHT_INTENSITY;
    } else {
      if (barrier)
        this.tweens.push(
          scene.tweens.add({
            targets: barrier,
            alpha: 0,
            x: o.x * TILE * 0.5,
            y: o.y * TILE * 0.5,
            duration: ms,
            ease: 'Cubic.easeIn',
            onComplete: () => barrier.setVisible(false),
          }),
        );
      this.tweens.push(
        scene.tweens.addCounter({
          from: 0,
          to: DOORS.LIGHT_INTENSITY,
          duration: DOORS.LIGHT_MS,
          ease: 'Sine.easeOut',
          onUpdate: (tw) => {
            light.intensity = tw.getValue() ?? DOORS.LIGHT_INTENSITY;
          },
        }),
      );
    }
    this.setChevrons(true);
  }

  /** 문 닫힘 (입구 문 — 들어온 뒤): 막힘 판이 돌아오고 빛이 꺼진다 */
  close(animate = true): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.setChevrons(false);
    const light = this.light;
    this.light = null;
    const reg = lightRegistryOf(this.scene);
    this.leaf?.setOpen(false, animate);
    const barrier = this.barrier;
    barrier?.setVisible(true);
    if (!animate) {
      barrier?.setAlpha(1).setPosition(0, 0);
      reg.remove(light);
      return;
    }
    if (barrier)
      this.tweens.push(
        this.scene.tweens.add({
          targets: barrier,
          alpha: 1,
          x: 0,
          y: 0,
          duration: DOORS.OPEN_MS,
          ease: 'Cubic.easeOut',
        }),
      );
    this.tweens.push(
      this.scene.tweens.addCounter({
        from: light?.intensity ?? 0,
        to: 0,
        duration: DOORS.OPEN_MS,
        onUpdate: (tw) => {
          if (light) light.intensity = tw.getValue() ?? 0;
        },
        onComplete: () => reg.remove(light),
      }),
    );
  }

  /** 방향 갈매기 켜기·끄기 (나가는 걸음·문 안에서는 끈다) */
  setChevrons(on: boolean): void {
    if (on === this.chevrons.visible) return;
    this.chevronTween?.remove();
    this.chevronTween = null;
    this.chevrons.setVisible(on);
    if (!on) return;
    const [lo, hi] = DOORS.CHEVRON_ALPHA;
    this.chevrons.setAlpha(lo);
    this.chevronTween = this.scene.tweens.add({
      targets: this.chevrons,
      alpha: hi,
      duration: DOORS.CHEVRON_PERIOD_MS / 2,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut',
    });
  }

  get lightOn(): boolean {
    return (this.light?.intensity ?? 0) > 0;
  }

  destroy(): void {
    for (const t of this.tweens) t.remove();
    this.tweens.length = 0;
    this.chevronTween?.remove();
    this.chevronTween = null;
    lightRegistryOf(this.scene).remove(this.light);
    this.light = null;
    this.barrier?.destroy();
    this.dark?.destroy();
    this.chevrons.destroy();
  }
}
