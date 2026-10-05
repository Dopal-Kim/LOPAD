/**
 * 54라운드 Q6 약점 잔 (BossArena 에서 분리 — 61라운드 E 6-1 정리) + 61 E 파훼 표시(아트 2 `fx/v3/boss1_cup_glint`).
 * - 판정: 잔 둘레 + 보스 바디 윗부분 (근접 사각형·화살 선분·화살 점). 맞을 때마다 1회 — hits 번째에 깨짐(onHit), 그 전은 struck.
 * - 그림: 깰 수 있는 동안(등록 + 그 프레임 cupAnchors.visible) glint 행 반복, 맞았지만 안 깨짐 = struck 행 1회, 깨짐 = cup_shatter.
 *   잔 시트 앵커가 없으면 임시 잔(채움) + 깜빡이는 테두리 (기존).
 */
import Phaser from 'phaser';
import { BOSS_ART, BOSS_FX, DEPTH } from '../../core/Constants';
import type { Mob } from '../../objects/Mob';
import type { WeakPointSpec } from '../../objects/boss/types';
import type { FxHandle, FxPool } from '../fx/fx';

/** 잔 깨짐 흔들림 · 맞음(안 깨짐) 흔들림 (논리 px, ms) */
const CUP_BREAK_SHAKE = { PX: 4, MS: 160 };
const CUP_STRUCK_SHAKE = { PX: 2, MS: 90 };
/** 같은 휘두름이 겹쳐 두 번 세지 않게 (ms) */
const CUP_HIT_GAP_MS = 120;

export interface CupHost {
  scene: Phaser.Scene;
  fx: FxPool;
  boss(): Mob | null;
  shake(px: number, ms: number): void;
  /** 맞았지만 아직 안 깨짐 (음향 BOSS_ACTION cupStruck) */
  onStruck(): void;
}

export class CupWeakPoint {
  private wp: (WeakPointSpec & { left: number }) | null = null;
  private readonly gfx: Phaser.GameObjects.Graphics;
  /** 화살 1발이 같은 잔을 두 번 세지 않게 (Projectile.registerHit) */
  hitToken: object = {};
  private lastHitAt = -Infinity;
  private glint: FxHandle | null = null;
  private readonly glintAt = { x: 0, y: 0, active: true, depth: DEPTH.HIT_FX, rotation: 0 };
  hits = 0;

  constructor(private readonly host: CupHost) {
    this.gfx = host.scene.add.graphics().setDepth(DEPTH.LIGHTMAP + 0.06);
  }

  get active(): boolean {
    return this.wp !== null;
  }

  set(wp: WeakPointSpec | null): void {
    this.wp = wp ? { ...wp, left: Math.max(1, Math.round(wp.hits ?? 1)) } : null;
    this.hitToken = {};
    if (!wp) {
      this.gfx.clear();
      this.stopGlint();
    }
  }

  rect(): { x: number; y: number; w: number; h: number } | null {
    return this.wp ? this.wp.rect() : null;
  }

  /**
   * 잔 맞힘 판정 사각형: 잔 + 둘레 여유, 아래로는 보스 바디 윗변 + 바디 높이 × HIT_DOWN_RATIO 까지 (머리 높이 잔을 몸 높이
   * 근접 판정이 닿게). 54라운드 Q24: 좌우는 잔 폭과 **보스 바디 폭** 중 넓은 쪽 — 몸에 맞닿은 옆에서 베어도 닿는다.
   */
  hitRect(): Phaser.Geom.Rectangle | null {
    if (!this.wp) return null;
    const cr = this.wp.rect();
    const C = BOSS_FX.CUP;
    const b = this.host.boss();
    const pad = C.HIT_PAD_PX;
    const left = Math.min(cr.x - pad, b ? b.body.x : Infinity);
    const right = Math.max(cr.x + cr.w + pad, b ? b.body.right : -Infinity);
    const bottom = Math.max(cr.y + cr.h + pad, b ? b.body.y + b.body.height * C.HIT_DOWN_RATIO : 0);
    return new Phaser.Geom.Rectangle(left, cr.y - pad, right - left, bottom - (cr.y - pad));
  }

  /** 잔을 맞힘: 남은 수가 0 이 되면 깨짐 (onHit), 아니면 struck */
  hit(): void {
    const wp = this.wp;
    if (!wp) return;
    const now = this.host.scene.time.now;
    if (now - this.lastHitAt < CUP_HIT_GAP_MS) return;
    this.lastHitAt = now;
    const cr = wp.rect();
    const cx = cr.x + cr.w / 2;
    const cy = cr.y + cr.h / 2;
    this.hits++;
    wp.left--;
    if (wp.left > 0) {
      const id = BOSS_ART.SHEETS.CUP_GLINT;
      if (this.host.fx.has(id))
        this.host.fx.play(id, cx, cy, { dir: 'struck', durationMs: BOSS_ART.CUP_STRUCK_MS, depth: DEPTH.HIT_FX });
      this.host.shake(CUP_STRUCK_SHAKE.PX, CUP_STRUCK_SHAKE.MS);
      this.host.onStruck();
      return;
    }
    this.set(null);
    if (this.host.fx.has(BOSS_FX.SHEETS.CUP_SHATTER))
      this.host.fx.play(BOSS_FX.SHEETS.CUP_SHATTER, cx, cy, { depth: DEPTH.HIT_FX });
    else this.shards(cx, cy);
    this.host.shake(CUP_BREAK_SHAKE.PX, CUP_BREAK_SHAKE.MS);
    wp.onHit();
  }

  /** 매 프레임: 표시 (glint 따라가기 · 임시 잔·테두리) */
  update(time: number): void {
    const wp = this.wp;
    const g = this.gfx;
    g.clear();
    if (!wp) return;
    const r = wp.rect();
    const C = BOSS_FX.CUP;
    if (wp.drawCup) {
      g.fillStyle(C.FILL, 1).fillRect(r.x, r.y, r.w, r.h);
      g.fillStyle(C.LIQUOR, 1).fillRect(r.x + 1, r.y + 1, r.w - 2, Math.max(1, r.h * 0.35));
    }
    const id = BOSS_ART.SHEETS.CUP_GLINT;
    const visible = wp.visible ? wp.visible() : true;
    if (!wp.drawCup && this.host.fx.has(id)) {
      // 아트 glint: 잔 중심을 따라간다. 잔이 안 보이는 프레임은 숨김
      this.glintAt.x = r.x + r.w / 2;
      this.glintAt.y = r.y + r.h / 2;
      if (!this.host.fx.isActive(this.glint))
        this.glint = this.host.fx.play(id, this.glintAt.x, this.glintAt.y, {
          dir: 'glint',
          follow: this.glintAt,
          depth: DEPTH.HIT_FX,
          hooks: false,
        });
      this.glint?.sprite.setVisible(visible);
      return;
    }
    if (Math.floor(time / C.BLINK_MS) % 2 === 0)
      g.lineStyle(C.EDGE_WIDTH, C.EDGE, 1).strokeRect(r.x - 1, r.y - 1, r.w + 2, r.h + 2);
  }

  private stopGlint(): void {
    if (this.glint) this.host.fx.stop(this.glint, 0, false);
    this.glint = null;
  }

  private shards(x: number, y: number): void {
    const S = BOSS_FX.SHARDS;
    const sc = this.host.scene;
    for (let i = 0; i < S.COUNT; i++) {
      const a = (i / S.COUNT) * Math.PI * 2;
      const r = sc.add.rectangle(x, y, S.SIZE, S.SIZE, S.COLOR, 1).setDepth(DEPTH.HIT_FX);
      sc.tweens.add({
        targets: r,
        x: x + Math.cos(a) * S.SPEED_PX * (S.LIFE_MS / 1000),
        y: y + Math.sin(a) * S.SPEED_PX * (S.LIFE_MS / 1000) + 6,
        alpha: 0,
        duration: S.LIFE_MS,
        onComplete: () => r.destroy(),
      });
    }
  }

  destroy(): void {
    this.stopGlint();
    this.gfx.destroy();
  }
}
