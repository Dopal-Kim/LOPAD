import Phaser from 'phaser';
import type { UiGrowth, UiWeaponResource } from '../contract/ui';
import { gaugeLayout } from './growthView';
import { resourceRatio } from './resourceView';
import { voiceWeapon } from './storyView';
import { swatch } from './StructureHud';
import { GRAY, hexToNum } from './theme';
import { DIET as D } from './themeAlerts';
import { WEAPON_HUE } from './themeWeapon';

/**
 * 62 P1-15 HUD 다이어트 — 각성 띠: 체력 막대 바로 밑 얇은 띠(무기 색 채움 + 눈금 1px). 숫자·'1차 각성까지 n' 문구는 지웠다
 * (Tab 빌드 보기·성장도에 있다). 다음 눈금은 강조색, 지난 눈금은 무기 색, 큰 눈금(각성)은 띠 위아래로 더 튀어나온다.
 * `ui:growth-gain` 이면 찬 부분이 한 번 하얗게 반짝인다.
 */
export class GrowthBand {
  private g: Phaser.GameObjects.Graphics;
  private flash: Phaser.GameObjects.Graphics;
  private sig = '';
  private lastFill = { x: 0, y: 0, w: 0 };

  constructor(private scene: Phaser.Scene) {
    this.g = scene.add.graphics();
    this.flash = scene.add.graphics().setAlpha(0);
  }

  /** (x, y) = 띠 왼쪽 위, w = 폭 (체력 막대 폭). growth 가 없으면 숨긴다 */
  render(gr: UiGrowth | null | undefined, x: number, y: number, w: number): void {
    const on = Boolean(gr);
    this.g.setVisible(on);
    this.flash.setVisible(on);
    if (!gr) return;
    const layout = gaugeLayout(gr, w);
    const sig = `${gr.weaponName}|${x}|${y}|${w}|${layout.fillW}|${layout.ticks.map((t) => `${t.x}${t.state}${t.big ? 'B' : ''}`).join(',')}`;
    if (sig === this.sig) return;
    this.sig = sig;
    const hue = hexToNum(WEAPON_HUE[voiceWeapon(gr.weaponName)].main);
    const sc = this.scene;
    const g = this.g.clear();
    const h = D.growthBandH;
    // 바탕 그늘 1px 둘레 + 길
    g.fillStyle(hexToNum(GRAY[0]), 1).fillRect(x - 1, y - 1, w + 2, h + 2);
    g.fillStyle(swatch(sc, 0, { gray: 3 }), 1).fillRect(x, y, w, h);
    if (layout.fillW > 0) g.fillStyle(hue, 1).fillRect(x, y, layout.fillW, h);
    this.lastFill = { x, y, w: layout.fillW };
    for (const t of layout.ticks) {
      const out = t.big ? D.bigTickOut : D.tickOut;
      const tx = x + Math.min(w - 1, Math.max(0, t.x));
      const col =
        t.state === 'next'
          ? swatch(sc, 0, { slot: 25 })
          : t.state === 'done'
            ? hexToNum(GRAY[15])
            : swatch(sc, 0, { gray: t.big ? 11 : 8 });
      g.fillStyle(hexToNum(GRAY[0]), 1).fillRect(tx - 1, y - out - 1, 3, h + out * 2 + 2);
      g.fillStyle(col, 1).fillRect(tx, y - out, 1, h + out * 2);
    }
  }

  gain(): void {
    const f = this.lastFill;
    if (f.w <= 0) return;
    this.scene.tweens.killTweensOf(this.flash);
    this.flash.clear().fillStyle(hexToNum(GRAY[15]), 1).fillRect(f.x, f.y, f.w, D.growthBandH).setAlpha(D.flashAlpha);
    this.scene.tweens.add({ targets: this.flash, alpha: 0, duration: D.flashMs });
  }

  setDepth(d: number): this {
    this.g.setDepth(d);
    this.flash.setDepth(d);
    return this;
  }
}

/**
 * 62 P1-15 — 보조 자원(고유 자원과 함께 오는 기력 등)을 무기 줄 오른쪽 작은 원으로: 남은 비율만큼 부채꼴(시계 방향, 위에서),
 * 바닥(exhausted)이면 회색 테가 깜빡인다. 낮으면 강조 20, 보통 강조 23. 글은 없다 (Tab·일기장에 이름).
 */
export class ResourceDot {
  private g: Phaser.GameObjects.Graphics;
  private sig = '';

  constructor(private scene: Phaser.Scene) {
    this.g = scene.add.graphics();
  }

  /** 원 가운데 (cx, cy). 그린 오른쪽 끝을 돌려준다 (숨김이면 cx) */
  render(r: UiWeaponResource | null, cx: number, cy: number, now: number): number {
    this.g.setVisible(Boolean(r));
    if (!r) return cx;
    const R = D.ringR;
    const ratio = resourceRatio(r);
    const blink = r.state === 'exhausted' && Math.floor(now / D.ringBlinkMs) % 2 === 0;
    const sig = `${cx}|${cy}|${Math.round(ratio * 48)}|${r.state}|${blink}`;
    if (sig !== this.sig) {
      this.sig = sig;
      const sc = this.scene;
      const g = this.g.clear();
      g.fillStyle(hexToNum(GRAY[0]), 1).fillCircle(cx, cy, R + 1);
      g.fillStyle(swatch(sc, 0, { gray: 3 }), 1).fillCircle(cx, cy, R);
      if (ratio > 0) {
        const col = r.state === 'low' ? swatch(sc, 0, { slot: 20 }) : swatch(sc, 0, { slot: 23 });
        const a0 = -Math.PI / 2;
        g.fillStyle(col, 1)
          .beginPath()
          .moveTo(cx, cy)
          .arc(cx, cy, R, a0, a0 + Math.PI * 2 * ratio, false)
          .closePath()
          .fillPath();
      }
      const edge = r.state === 'exhausted' ? (blink ? GRAY[13] : GRAY[6]) : GRAY[9];
      g.lineStyle(1, hexToNum(edge), 1).strokeCircle(cx, cy, R);
    }
    return cx + R + 1;
  }

  setDepth(d: number): this {
    this.g.setDepth(d);
    return this;
  }
}
