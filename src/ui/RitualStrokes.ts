import Phaser from 'phaser';
import { UI_SCREEN, uiCommands, type UiRitual, type UiRitualLegend, type UiRitualPoint } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { KIT, NinePanel, SLICE, weaponIconKey } from './kit';
import { darkBackdrop, hintRow, inkBleed, ritualMeta, ritualTex } from './ritualArt';
import { pushPoint, sealStates } from './ritualView';
import { StrokeInk } from './ritualBrush';
import { HEALTH_BAR } from './themeR61';
import { ritualText } from './textRitual';
import { SEPIA, hexToNum } from './theme';
import { RITUAL_UI as R } from './themeRitual';
import type { RitualPage } from './RitualScene';

/**
 * 62 루프 1 P0-2 3획 장 (계약 §20 phase 'strokes') — 등 그림(art §30 `ritual/back_canvas`, 없으면 코드로 그린 등) 위에 먹 붓으로
 * 세 획을 긋는다(ritualBrush StrokeInk — 640×360 도트 화폭에 ink_brush 스탬프). 누름 → 뗌까지 점을 모아 `ritual.stroke(points)`
 * (논리 화면 좌표, 판정은 시스템). 느리면 굵은 붓끝, 빠르면 마른 붓. 판정(RITUAL_STROKE_JUDGED)마다 그 획이 불씨 먹으로 빛나고
 * 위 가운데 낙관 칸에 붉은 도장.
 * 오른쪽 종이: 획 ↔ 무기 규칙(`strokes.legend`). 3획이 끝나면(`lastWeapon`) 등 아래에 큰 낙관. 판정 수치는 그리지 않는다.
 */
export class RitualStrokesPage implements RitualPage {
  private root: Phaser.GameObjects.Container;
  private ink: StrokeInk;
  private seals: Phaser.GameObjects.Graphics;
  private cur?: { points: UiRitualPoint[]; speed: number; dir: { dx: number; dy: number } };
  private done = 0;
  /** 낙관 칸 자리 (규칙 종이 아래 — 없으면 위 가운데) */
  private sealAt: { x: number; y: number } | null = null;
  private sealed = false;

  constructor(
    private scene: Phaser.Scene,
    r: UiRitual,
  ) {
    this.root = scene.add.container(0, 0).setDepth(R.depth);
    this.root.add(darkBackdrop(scene, 1));
    const clip = this.drawBack();
    this.ink = new StrokeInk(scene, clip);
    this.root.add([this.ink.glow, this.ink.rt]);
    this.seals = scene.add.graphics();
    this.root.add(this.seals);
    this.drawHead(r);
    this.drawLegend(r.strokes?.legend ?? []);
    this.root.add(hintRow(scene, r.hint, UI_SCREEN.WIDTH / 2, UI_SCREEN.HEIGHT - R.hintBottom));
    this.update(r);
    scene.input.on('pointerdown', this.onDown);
    scene.input.on('pointermove', this.onMove);
    scene.input.on('pointerup', this.onUp);
    scene.input.on('pointerupoutside', this.onUp);
  }

  update(r: UiRitual): void {
    const s = r.strokes;
    this.done = s?.done ?? 0;
    this.drawSeals(this.done, s?.total ?? 3);
    if (s?.lastWeapon && !this.sealed) this.bigSeal(s.lastWeapon, r.strokes?.legend ?? []);
  }

  /** RITUAL_STROKE_JUDGED: 그 획이 불씨 먹으로 (art §30 — #e8b858 + 빛무리 #d67a11) */
  judged(p: unknown): void {
    const o = p && typeof p === 'object' ? (p as { index?: unknown }) : {};
    this.ink.ember(typeof o.index === 'number' ? o.index : this.ink.count - 1);
  }

  key(e: KeyboardEvent): boolean {
    if (e.key === 'Escape') {
      uiCommands.ritual.back();
      return true;
    }
    return false;
  }

  destroy(): void {
    this.scene.input.off('pointerdown', this.onDown);
    this.scene.input.off('pointermove', this.onMove);
    this.scene.input.off('pointerup', this.onUp);
    this.scene.input.off('pointerupoutside', this.onUp);
    this.scene.tweens.killTweensOf(this.root.list);
    this.ink.destroy();
    this.root.destroy();
  }

  // ---- 붓

  private world(p: Phaser.Input.Pointer): { x: number; y: number } {
    const w = this.scene.cameras.main.getWorldPoint(p.x, p.y);
    return { x: w.x, y: w.y };
  }

  private onDown = (p: Phaser.Input.Pointer): void => {
    if (this.sealed || this.done >= 3) return;
    const { x, y } = this.world(p);
    if (!this.ink.canStart(x, y)) return;
    const points: UiRitualPoint[] = [];
    pushPoint(points, { x, y, t: performance.now() }, 0, R.brush.maxPoints);
    this.cur = { points, speed: 0, dir: { dx: 1, dy: 0 } };
    this.ink.begin(x, y);
  };

  private onMove = (p: Phaser.Input.Pointer): void => {
    const c = this.cur;
    if (!c || !p.isDown) return;
    const { x, y } = this.world(p);
    const t = performance.now();
    const prev = c.points[c.points.length - 1];
    if (!pushPoint(c.points, { x, y, t }, R.brush.minDist, R.brush.maxPoints)) return;
    const speed = Math.hypot(x - prev.x, y - prev.y) / Math.max(1, t - prev.t);
    c.speed += (speed - c.speed) * R.brush.smooth * 2;
    c.dir = { dx: x - prev.x, dy: y - prev.y };
    this.ink.move(x, y, c.speed);
  };

  private onUp = (): void => {
    const c = this.cur;
    if (!c) return;
    this.cur = undefined;
    const idx = this.ink.end(c.dir, c.speed);
    const ok = c.points.length >= 2 && uiCommands.ritual.stroke(c.points);
    debugExpose('ritualStroke', { points: c.points.length, ok, index: idx });
    if (!ok) {
      // 획으로 치지 않았다 (너무 짧다) — 화폭에서 지운다
      this.ink.dropLast();
      return;
    }
    const last = c.points[c.points.length - 1];
    inkBleed(this.scene, last.x, last.y, R.depth + 1);
  };

  // ---- 그림

  /**
   * 등 그림: art §30 back_canvas(1920 렌더 그림 → 논리 0.5배로 화면 가득) + 빛무리 ADD(숨 4.2초). 붓 자르기 다각형(strokeClip,
   * 렌더 px → 도트)을 돌려준다. 그림이 없으면 계단 명암 코드 등과 그 사각형.
   */
  private drawBack(): (readonly [number, number])[] | null {
    const sc = this.scene;
    const C = R.canvas;
    const art = ritualTex(sc, 'back');
    if (art) {
      this.root.add(sc.add.image(0, 0, art).setOrigin(0, 0).setScale(C.renderScale));
      const meta = ritualMeta<{ glow?: { x: number; y: number }; strokeClip?: [number, number][] }>(sc, 'back');
      const glowKey = ritualTex(sc, 'glow');
      if (glowKey) {
        const g = sc.add
          .image((meta?.glow?.x ?? 0) * C.renderScale, (meta?.glow?.y ?? 0) * C.renderScale, glowKey)
          .setOrigin(0, 0)
          .setScale(C.renderScale)
          .setBlendMode(Phaser.BlendModes.ADD)
          .setAlpha(0.6);
        sc.tweens.add({
          targets: g,
          alpha: 1,
          duration: C.glowBreathMs / 2,
          yoyo: true,
          repeat: -1,
          ease: 'Sine.easeInOut',
        });
        this.root.add(g);
      }
      // 렌더 px(1920) → 도트(640) = ÷3
      const k = C.renderScale / C.dotScale;
      return meta?.strokeClip?.map(([x, y]) => [x * k, y * k] as const) ?? null;
    }
    const B = R.back;
    const d0 = StrokeInk.dot(B.x, B.y);
    const d1 = StrokeInk.dot(B.x + B.w, B.y + B.h);
    this.codeBack();
    return [
      [d0.x, d0.y],
      [d1.x, d0.y],
      [d1.x, d1.y],
      [d0.x, d1.y],
    ];
  }

  /** 그림이 없을 때: 계단 명암 등(목·어깨·척추·견갑) */
  private codeBack(): void {
    const sc = this.scene;
    const B = R.back;
    const g = sc.add.graphics();
    const cx = B.x + B.w / 2;
    const half = (y: number): number => {
      const t = (y - B.y) / B.h;
      if (t < 0.1) return 34; // 목
      if (t < 0.2) return 34 + (t - 0.1) * 10 * 186; // 어깨로 벌어짐
      if (t < 0.32) return 220 + (t - 0.2) * 40; // 어깨
      return 225 - (t - 0.32) * 120; // 허리로 좁아짐
    };
    const c0 = hexToNum(SEPIA[2]);
    const c1 = hexToNum(SEPIA[3]);
    const c2 = hexToNum(SEPIA[4]);
    for (let y = B.y; y < B.y + B.h; y += 2) {
      const hw = Math.round(half(y));
      g.fillStyle(c1, 1).fillRect(cx - hw, y, hw * 2, 2);
      // 왼쪽 빛 (촛불 쪽) · 오른쪽 그늘 — 계단 두 단
      g.fillStyle(c2, 1).fillRect(cx - hw + 4, y, Math.round(hw * 0.55), 2);
      g.fillStyle(c0, 1).fillRect(cx + Math.round(hw * 0.55), y, Math.round(hw * 0.45), 2);
    }
    // 척추 · 견갑골
    g.fillStyle(c0, 1).fillRect(cx - 1, B.y + Math.round(B.h * 0.16), 3, Math.round(B.h * 0.84));
    g.lineStyle(2, c0, 1);
    g.beginPath()
      .arc(cx - 92, B.y + 190, 56, Math.PI * 1.05, Math.PI * 1.6)
      .strokePath();
    g.beginPath()
      .arc(cx + 92, B.y + 190, 56, Math.PI * 1.4, Math.PI * 1.95)
      .strokePath();
    // 오래된 흉터 몇 줄 (옅게)
    g.lineStyle(1, hexToNum(SEPIA[1]), 0.7);
    g.lineBetween(cx + 60, B.y + 300, cx + 118, B.y + 268);
    g.lineBetween(cx - 140, B.y + 330, cx - 96, B.y + 360);
    this.root.add(g);
  }

  /** 위: 일기장 줄 (잉크 위) */
  private drawHead(r: UiRitual): void {
    let y = 14;
    for (const line of r.lines ?? []) {
      const t = new GlowText(this.scene, 0, 0, line, 'ink_body', { wrap: 600, align: 'center' });
      t.placeCenter(UI_SCREEN.WIDTH / 2, y);
      this.root.add(t);
      y += t.displayHeight + 2;
    }
  }

  /** 3획 낙관 칸: 찍힘 = 붉은 인주 네모(안에 흰 점 두 개), 지금 = 강조 테, 아직 = 흐린 테 */
  private drawSeals(done: number, total: number): void {
    const S = R.seals;
    const states = sealStates(done, total);
    const w = states.length * S.size + (states.length - 1) * S.gap;
    // 규칙 종이 아래(있으면) · 없으면 위 가운데
    let x = this.sealAt ? this.sealAt.x : Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const top = this.sealAt ? this.sealAt.y : S.top;
    const g = this.seals.clear();
    const red = hexToNum(HEALTH_BAR.fill);
    for (const st of states) {
      if (st === 'done') {
        g.fillStyle(red, 1).fillRect(x, top, S.size, S.size);
        g.fillStyle(hexToNum(SEPIA[5]), 0.8)
          .fillRect(x + 4, top + 5, 3, 3)
          .fillRect(x + S.size - 7, top + S.size - 8, 3, 3);
      } else {
        g.lineStyle(1, st === 'now' ? red : hexToNum(SEPIA[3]), 1).strokeRect(
          x + 0.5,
          top + 0.5,
          S.size - 1,
          S.size - 1,
        );
      }
      x += S.size + S.gap;
    }
  }

  /** 오른쪽 종이: 획이 부르는 무기 (무기 아이콘 · 획 모양 · 무기 이름) */
  private drawLegend(legend: UiRitualLegend[]): void {
    if (!legend.length) return;
    const sc = this.scene;
    const L = R.legend;
    const head = new GlowText(sc, 0, 0, ritualText('legendHead'), 'page_title');
    const h = L.pad * 2 + head.displayHeight + 6 + legend.length * L.rowH;
    const panel = new NinePanel(sc, L.x, L.y, KIT.panelPaper, SLICE.panelPaper, L.w, h);
    head.setPosition(L.x + L.pad, L.y + L.pad);
    const objs: Phaser.GameObjects.GameObject[] = [panel, head];
    let y = L.y + L.pad + head.displayHeight + 6;
    for (const row of legend) {
      const key = weaponIconKey(row.weapon);
      let x = L.x + L.pad;
      if (sc.textures.exists(key)) {
        objs.push(sc.add.image(x, y, key).setOrigin(0, 0).setDisplaySize(16, 16));
        x += 20;
      }
      const name = new GlowText(sc, x, y, row.weaponName, 'page_title');
      const line = new GlowText(sc, x + name.displayWidth + 6, y, row.line, 'page_body');
      objs.push(name, line);
      y += L.rowH;
    }
    // 세 획 낙관 칸: 종이 아래 '세 획' + 칸 셋
    const sh = new GlowText(sc, L.x + 2, L.y + h + 10, ritualText('sealsHead'), 'ink_faint');
    objs.push(sh);
    this.sealAt = { x: L.x + 2 + sh.displayWidth + 10, y: L.y + h + 10 };
    this.root.add(objs);
  }

  /** 3획 끝: 등 아래 오른쪽에 큰 낙관 (무기 이름) — 찍히며 번진다 */
  private bigSeal(weapon: string, legend: UiRitualLegend[]): void {
    this.sealed = true;
    const sc = this.scene;
    const name = legend.find((l) => l.weapon === weapon)?.weaponName ?? '';
    const size = 54;
    const x = R.back.x + R.back.w - size - 24;
    const y = R.back.y + R.back.h - size - 30;
    const g = sc.add.graphics();
    g.fillStyle(hexToNum(HEALTH_BAR.fill), 1).fillRect(0, 0, size, size);
    g.lineStyle(2, hexToNum(SEPIA[5]), 0.85).strokeRect(4, 4, size - 8, size - 8);
    const t = new GlowText(sc, 0, 0, name, 'page_title', { scale: 2 });
    t.setPosition(Math.round(size / 2 - t.displayWidth / 2), Math.round(size / 2 - t.displayHeight / 2));
    const box = sc.add.container(x + size / 2, y + size / 2, [g, t]);
    g.setPosition(-size / 2, -size / 2);
    t.setPosition(t.x - size / 2, t.y - size / 2);
    box.setScale(1.5).setAlpha(0);
    this.root.add(box);
    sc.tweens.add({
      targets: box,
      scale: 1,
      alpha: 1,
      duration: 180,
      ease: 'Quad.easeIn',
      onComplete: () => inkBleed(sc, x + size / 2, y + size / 2, R.depth + 1),
    });
    debugExpose('ritualSeal', { weapon, name });
  }
}
