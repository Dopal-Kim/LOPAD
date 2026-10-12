/**
 * 62라운드 P0-8 적 등장 예고 (점검 '첫 전투 노드 입장 유예'): 웨이브가 나오기 전 ms 동안, 나올 자리마다 바닥에 먹이 번지고
 * 불씨 고리가 맥박친다(쿼터뷰라 납작한 타원). 끝나면 짧게 흐려진다. 문양 자리 = 실제로 나오는 자리 (RoomDirector 가 미리 고른다).
 * 바닥 깊이(라이트맵 아래)라 어둠 속에서 읽히도록 붉은 작은 광원을 같은 시간 함께 켠다.
 * 62 루프 2 시스템 D: 아트 `fx/v3/spawn_ink`(art §31.2)가 올라와 있으면 그 시트로 그린다 (도형은 대체).
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_INCOMING } from '../../core/Constants';
import { lightRegistryOf } from '../../systems/lighting/lightRegistry';

/** 쿼터뷰 바닥 타원 세로 비 */
const FLAT = 0.55;

/** 62 D (art §31.2): 아트 먹 번짐 시트 — 피벗 = 적 발 · spawnAtMs(900) 에 적이 선다 · 경고가 더 길면 holdFrame 에서 멈춤 */
const INK_FX = 'spawn_ink';
const INK_SPAWN_AT_MS = 900;

/** fx 재생만 (FxPool 의 일부 — 테스트·시험장에서 없을 수 있다) */
export interface SpawnInkFx {
  has(id: string): boolean;
  play(
    id: string,
    x: number,
    y: number,
    opts: { depth?: number; staticFrame?: number; durationMs?: number },
  ): { sprite: Phaser.GameObjects.Sprite } | null;
}

export class SpawnMarks {
  private readonly live = new Set<Phaser.GameObjects.Graphics>();
  private readonly timers = new Set<Phaser.Time.TimerEvent>();
  /** 디버그: 지금까지 그린 문양 수 · 아트 시트로 그린 수 */
  shown = 0;
  shownInk = 0;

  constructor(
    private readonly scene: Phaser.Scene,
    private readonly fx: SpawnInkFx | null = null,
  ) {
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  /** 62 D: 아트 spawn_ink 가 있으면 그것 — 시트 900ms 칸이 소환 순간에 오게. 경고가 더 길면 앞은 holdFrame 직전 칸에서 기다림 없이 그대로 시작을 늦춘다 */
  private showInk(points: readonly { x: number; y: number }[], ms: number): boolean {
    const fx = this.fx;
    if (!fx || !fx.has(INK_FX)) return false;
    const lead = Math.max(0, ms - INK_SPAWN_AT_MS);
    const play = () => {
      for (const p of points) {
        fx.play(INK_FX, p.x, p.y, { depth: DEPTH.FX_GROUND });
        this.shownInk += 1;
      }
    };
    // 경고가 900ms 보다 길면: 먼저 젖은 칸(holdFrame)을 띄워 두고, 남은 900ms 에 시트 전체를 재생
    if (lead > 0) {
      for (const p of points) fx.play(INK_FX, p.x, p.y, { depth: DEPTH.FX_GROUND, staticFrame: 1, durationMs: lead });
      const t = this.scene.time.delayedCall(lead, () => {
        this.timers.delete(t);
        play();
      });
      this.timers.add(t);
    } else play();
    this.shown += points.length;
    return true;
  }

  show(points: readonly { x: number; y: number }[], ms: number): void {
    const M = ENEMY_INCOMING.MARK;
    if (this.showInk(points, ms)) {
      // 어둠 속에서 읽히게 작은 광원은 그대로
      const lights = lightRegistryOf(this.scene);
      for (const p of points) lights.add(M.LIGHT, { x: p.x, y: p.y, until: this.scene.time.now + ms });
      return;
    }
    const scene = this.scene;
    const now = scene.time.now;
    const lights = lightRegistryOf(scene);
    for (const p of points) {
      const g = scene.add.graphics().setPosition(p.x, p.y).setDepth(DEPTH.FX_GROUND);
      this.live.add(g);
      this.shown += 1;
      lights.add(M.LIGHT, { x: p.x, y: p.y, until: now + ms });
      const draw = (t: number) => {
        // t 0..1: 먹이 번지며(빠르게 퍼졌다 느리게) 고리가 2번 맥박친다
        const e = 1 - (1 - t) * (1 - t);
        const r = M.R_FROM + (M.R_TO - M.R_FROM) * e;
        const pulse = 0.55 + 0.45 * Math.sin(t * Math.PI * 4 - Math.PI / 2);
        g.clear();
        g.fillStyle(M.INK, M.INK_ALPHA * Math.min(1, t * 3));
        g.fillEllipse(0, 0, r * 2, r * 2 * FLAT);
        g.lineStyle(M.RING_PX, M.EMBER, 0.35 + 0.55 * pulse);
        g.strokeEllipse(0, 0, (r + 1.5) * 2, (r + 1.5) * 2 * FLAT);
        // 안쪽 소용돌이 점 넷 (먹이 모여드는 결)
        g.fillStyle(M.EMBER, 0.5 * pulse);
        for (let i = 0; i < 4; i++) {
          const a = t * Math.PI * 3 + (i * Math.PI) / 2;
          const rr = r * (0.75 - 0.5 * e);
          g.fillRect(Math.cos(a) * rr - 0.5, Math.sin(a) * rr * FLAT - 0.5, 1, 1);
        }
      };
      draw(0);
      scene.tweens.addCounter({
        from: 0,
        to: 1,
        duration: ms,
        onUpdate: (tw) => draw(tw.getValue() ?? 1),
        onComplete: () => {
          scene.tweens.add({
            targets: g,
            alpha: 0,
            duration: M.FADE_MS,
            onComplete: () => this.drop(g),
          });
        },
      });
    }
  }

  /** 디버그: 떠 있는 문양 수 */
  get count(): number {
    return this.live.size;
  }

  private drop(g: Phaser.GameObjects.Graphics): void {
    this.live.delete(g);
    g.destroy();
  }

  destroy(): void {
    for (const g of this.live) g.destroy();
    this.live.clear();
    for (const t of this.timers) t.remove(false);
    this.timers.clear();
  }
}
