import Phaser from 'phaser';
import { UI_SCREEN, type UiDeathFx, type UiExitHint, type UiSnapshot } from '../contract/ui';
import { GlowText } from './glow';
import { accentHex } from './kit';
import { GRAY, hexToNum } from './theme';
import { DEATH_VEIL, EXIT_ARROW as A } from './themeLoop2E';

/**
 * 62 루프 2 UI E (계약 C) HUD 두 가지 — HudScene 에서 떼어 둔다(HudScene 840줄).
 *  - `DeathVeil`: DEATH_STARTED 때 알림·자막·쪽지·토스트를 거두고 HUD 카메라를 짧게 걷는다(먹 번짐 위에 남지 않게).
 *    다음 생(STAGE_STARTED·BIRTH_STARTED)이나 씬이 다시 뜨면 되돌린다.
 *  - `ExitArrow`: `snapshot.exitHint` — 출구가 열렸고 화면 밖이면 그 방향 가장자리에 화살 + 글('오르는 길').
 *    다른 화면이 덮였거나 문으로 걸어 나가는 중(door walkOut·inside·walkIn)이면 숨긴다.
 */
export class DeathVeil {
  private active = false;

  constructor(
    private scene: Phaser.Scene,
    private clear: () => void,
  ) {}

  get down(): boolean {
    return this.active;
  }

  start(p?: Partial<UiDeathFx>): void {
    this.clear();
    if (this.active) return;
    this.active = true;
    const cam = this.scene.cameras?.main;
    if (!cam) return;
    this.scene.tweens.killTweensOf(cam);
    // 슬로모 앞쪽 안에 걷는다 (먹 번짐이 시작되기 전)
    const ms = Math.min(DEATH_VEIL.fadeMs, Math.max(80, (p?.slowMs ?? DEATH_VEIL.fadeMs * 2) / 2));
    this.scene.tweens.add({ targets: cam, alpha: 0, duration: ms, ease: 'Quad.easeOut' });
  }

  reset(): void {
    if (!this.active) return;
    this.active = false;
    // 씬이 내려가는 중이면 카메라가 이미 없다
    const cam = this.scene.cameras?.main;
    if (!cam) return;
    this.scene.tweens?.killTweensOf(cam);
    cam.setAlpha(1);
  }
}

type DoorPhase = 'closed' | 'open' | 'walkOut' | 'inside' | 'walkIn';

export class ExitArrow {
  private box: Phaser.GameObjects.Container;
  private g: Phaser.GameObjects.Graphics;
  private label: GlowText;
  private shown = false;
  private text = '';
  private t0 = 0;

  constructor(private scene: Phaser.Scene) {
    this.g = scene.add.graphics();
    this.label = new GlowText(scene, 0, 0, '', 'ink_accent');
    this.box = scene.add.container(0, 0, [this.g, this.label]).setDepth(A.depth).setAlpha(0).setVisible(false);
  }

  /** 매 STATE (hidden = 메뉴·지도·탄생·사망 등이 덮음) */
  render(s: UiSnapshot, hidden: boolean, si: number, now: number): void {
    const h = s.exitHint ?? null;
    const phase = (s as { door?: { phase?: DoorPhase } | null }).door?.phase;
    const walking = phase === 'walkOut' || phase === 'inside' || phase === 'walkIn';
    const want = Boolean(h && !h.onScreen) && !hidden && !walking;
    if (want !== this.shown) {
      this.shown = want;
      this.scene.tweens.killTweensOf(this.box);
      if (want) {
        this.t0 = now;
        this.box.setVisible(true);
      }
      this.scene.tweens.add({
        targets: this.box,
        alpha: want ? 1 : 0,
        duration: A.fadeMs,
        onComplete: () => {
          if (!this.shown) this.box.setVisible(false);
        },
      });
    }
    if (!want || !h) return;
    this.place(h, si, now);
  }

  private place(h: UiExitHint, si: number, now: number): void {
    const W = UI_SCREEN.WIDTH;
    const H = UI_SCREEN.HEIGHT;
    const x = Math.max(A.margin, Math.min(W - A.margin, h.x));
    const y = Math.max(A.margin, Math.min(H - A.marginBottom, h.y));
    const bob = Math.sin(((now - this.t0) / A.bobMs) * Math.PI * 2) * A.bob;
    const ux = Math.cos(h.angle);
    const uy = Math.sin(h.angle);
    const tipX = x + ux * bob;
    const tipY = y + uy * bob;
    // 화살: 끝 = 출구 쪽 (가장자리 점), 꼬리 = 화면 안쪽
    const bx = tipX - ux * A.len;
    const by = tipY - uy * A.len;
    const px = -uy * (A.width / 2);
    const py = ux * (A.width / 2);
    const col = hexToNum(accentHex(this.scene, si, A.slot));
    const g = this.g.clear();
    g.fillStyle(hexToNum(GRAY[0]), 0.85);
    g.fillTriangle(tipX + ux * 2, tipY + uy * 2, bx + px * 1.35, by + py * 1.35, bx - px * 1.35, by - py * 1.35);
    g.fillStyle(col, 1);
    g.fillTriangle(tipX, tipY, bx + px, by + py, bx - px, by - py);
    // 글: 꼬리 뒤 화면 안쪽
    if (h.label !== this.text) {
      this.text = h.label;
      this.label.setText(h.label);
    }
    if (!h.label) return;
    const lx = bx - ux * (A.labelGap + this.label.displayWidth / 2 + 2);
    const ly = by - uy * (A.labelGap + this.label.displayHeight / 2 + 2);
    const half = this.label.displayWidth / 2;
    const cx = Math.max(A.margin + half, Math.min(W - A.margin - half, lx));
    const cy = Math.max(A.margin, Math.min(H - A.marginBottom, ly - this.label.displayHeight / 2));
    this.label.setPosition(Math.round(cx - half), Math.round(cy));
  }

  destroy(): void {
    this.scene.tweens.killTweensOf(this.box);
    this.box.destroy();
  }
}
