/**
 * 62라운드 P0-8 적 등장 예고 (점검 '첫 전투 노드 입장 유예'): 웨이브가 나오기 전 ms 동안, 나올 자리마다 바닥에 먹이 번지고
 * 불씨 고리가 맥박친다(쿼터뷰라 납작한 타원). 끝나면 짧게 흐려진다. 문양 자리 = 실제로 나오는 자리 (RoomDirector 가 미리 고른다).
 * 바닥 깊이(라이트맵 아래)라 어둠 속에서 읽히도록 붉은 작은 광원을 같은 시간 함께 켠다.
 * 아트 시트가 생기면 그것으로 바꿀 자리 (요청: `fx/v3/spawn_ink` — CHANGELOG 62).
 */
import Phaser from 'phaser';
import { DEPTH, ENEMY_INCOMING } from '../../core/Constants';
import { lightRegistryOf } from '../../systems/lighting/lightRegistry';

/** 쿼터뷰 바닥 타원 세로 비 */
const FLAT = 0.55;

export class SpawnMarks {
  private readonly live = new Set<Phaser.GameObjects.Graphics>();
  /** 디버그: 지금까지 그린 문양 수 */
  shown = 0;

  constructor(private readonly scene: Phaser.Scene) {
    scene.events.once(Phaser.Scenes.Events.SHUTDOWN, () => this.destroy());
  }

  show(points: readonly { x: number; y: number }[], ms: number): void {
    const M = ENEMY_INCOMING.MARK;
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
  }
}
