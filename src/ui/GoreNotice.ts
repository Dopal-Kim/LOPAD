import Phaser from 'phaser';
import { UI_SCREEN } from '../contract/ui';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { takeKey } from './keyGate';
import { inkPanel } from './kit';
import { goreDesc } from './SettingsRows';
import { commitSettings, currentSettings } from './settingsStore';
import { GORE_LEVELS } from './settingsView';
import { markGoreNoticeSeen, stepGoreIndex } from './p21View';
import { p21Text } from './text';
import { ROUTE, hexToNum } from './theme';
import { DARK } from './themeP21';
import { playUiSound } from './uiSound';

const W = 560;
const PAD = 16;
const OPT_W = 112;
const OPT_H = 24;
const OPT_GAP = 10;

interface Btn {
  c: Phaser.GameObjects.Container;
  g: Phaser.GameObjects.Graphics;
  t: GlowText;
  w: number;
}

/**
 * P21 첫 실행 잔혹 묘사 안내 카드 (contracts/dark-brutal §1 — 한 번, localStorage `lopad.goreNotice`).
 * 타이틀 첫 입력 뒤 메뉴 앞에 뜬다. 66 팩: 버튼 셋(그대로 본다 2 · 줄인다 1 · 끈다 0)이 곧 고르기 — 고르면 설정으로 넣고 덮는다.
 * 기본 포커스 = 지금 설정(처음이면 그대로 본다). 버튼은 Container → Graphics → GlowText.
 * 조작: ←→·A/D 옮기기 · Enter·스페이스 고른다 · 1~3 바로 고른다 · 마우스 누르기.
 */
export class GoreNotice {
  private box: Phaser.GameObjects.Container;
  private opts: Btn[] = [];
  private desc: GlowText;
  private idx: number;
  private done = false;

  constructor(
    private scene: Phaser.Scene,
    depth: number,
    private onDone: () => void,
  ) {
    this.idx = Math.max(0, GORE_LEVELS.indexOf(currentSettings().gore));
    const sc = scene;
    const block = sc.add
      .rectangle(0, 0, UI_SCREEN.WIDTH, UI_SCREEN.HEIGHT, hexToNum(DARK.ink), ROUTE.dimAlpha)
      .setOrigin(0)
      .setInteractive();
    const parts: Phaser.GameObjects.GameObject[] = [];
    let y = PAD;
    const title = new GlowText(sc, 0, y, p21Text('goreNoticeTitle'), 'ink_accent', { font: 'title' });
    title.placeCenter(W / 2, y);
    y += title.displayHeight + 8;
    const body = new GlowText(sc, PAD, y, p21Text('goreNoticeBody'), 'ink_body', {
      wrap: W - PAD * 2,
      readable: true,
    });
    y += body.displayHeight + 12;
    parts.push(title, body);
    // 잔혹 묘사 3단 (왼쪽부터 2 · 1 · 0)
    const labels = [p21Text('goreNoticeFull'), p21Text('goreNoticeReduced'), p21Text('goreNoticeOff')];
    const rowW = labels.length * OPT_W + (labels.length - 1) * OPT_GAP;
    labels.forEach((label, i) => {
      const b = this.button(Math.round(W / 2 - rowW / 2 + i * (OPT_W + OPT_GAP)), y, OPT_W, OPT_H, label);
      b.c.on('pointerover', () => this.select(i));
      b.c.on('pointerdown', () => {
        this.select(i);
        this.finish();
      });
      this.opts.push(b);
      parts.push(b.c);
    });
    y += OPT_H + 6;
    this.desc = new GlowText(sc, 0, y, '', 'ink_faint', { wrap: W - PAD * 2, align: 'center' });
    parts.push(this.desc);
    y += 16 + 10;
    const hint = new GlowText(sc, 0, y, p21Text('goreNoticeHint'), 'ink_faint');
    hint.placeCenter(W / 2, y);
    parts.push(hint);
    y += hint.displayHeight + PAD - 4;
    const panel = inkPanel(sc, 0, 0, W, y);
    const card = sc.add.container(Math.round(UI_SCREEN.WIDTH / 2 - W / 2), Math.round(UI_SCREEN.HEIGHT / 2 - y / 2), [
      panel,
      ...parts,
    ]);
    this.box = sc.add.container(0, 0, [block, card]).setDepth(depth).setAlpha(0);
    sc.tweens.add({ targets: this.box, alpha: 1, duration: 500 });
    sc.input.keyboard?.on('keydown', this.onKey);
    this.paint();
  }

  private button(x: number, y: number, w: number, h: number, label: string): Btn {
    const g = this.scene.add.graphics();
    const t = new GlowText(this.scene, 0, 0, label, 'ink_faint');
    t.setPosition(Math.round(w / 2 - t.displayWidth / 2), Math.round((h - t.displayHeight) / 2));
    const c = this.scene.add.container(x, y, [g, t]).setSize(w, h);
    c.setInteractive(new Phaser.Geom.Rectangle(w / 2, h / 2, w, h), Phaser.Geom.Rectangle.Contains);
    if (c.input) c.input.cursor = 'pointer';
    return { c, g, t, w };
  }

  private onKey = (e: KeyboardEvent): void => {
    if (this.done || e.repeat) return;
    const k = e.key;
    if (k === 'ArrowLeft' || k === 'a' || k === 'A') {
      if (takeKey(e)) this.select(stepGoreIndex(this.idx, -1));
    } else if (k === 'ArrowRight' || k === 'd' || k === 'D') {
      if (takeKey(e)) this.select(stepGoreIndex(this.idx, 1));
    } else if (k === '1' || k === '2' || k === '3') {
      if (takeKey(e)) {
        this.select(Number(k) - 1);
        this.finish();
      }
    } else if (k === 'Enter' || k === ' ') {
      if (takeKey(e)) this.finish();
    } else takeKey(e); // 다른 키는 메뉴로 새지 않게 삼킨다
  };

  private select(i: number): void {
    if (this.done || i === this.idx) return;
    this.idx = i;
    playUiSound(this.scene, 'move');
    this.paint();
  }

  private paint(): void {
    const gore = GORE_LEVELS[this.idx];
    this.opts.forEach((b, i) => {
      const sel = i === this.idx;
      b.g.clear();
      b.g.fillStyle(hexToNum(sel ? DARK.bloodDeep : DARK.ink), sel ? 0.9 : 0.6).fillRect(0, 0, b.w, OPT_H);
      b.g.lineStyle(1, hexToNum(sel ? DARK.blood : DARK.boneDead), 1).strokeRect(0.5, 0.5, b.w - 1, OPT_H - 1);
      b.t.setGlowStyle(sel ? 'ink_body' : 'ink_faint');
    });
    this.desc.setText(goreDesc(gore)).placeCenter(W / 2, this.desc.y);
    debugExpose('goreNotice', { open: true, gore });
  }

  private finish(): void {
    if (this.done) return;
    this.done = true;
    playUiSound(this.scene, 'select');
    const gore = GORE_LEVELS[this.idx];
    const cur = currentSettings();
    if (cur.gore !== gore) commitSettings({ ...cur, gore });
    markGoreNoticeSeen(safeStorage());
    debugExpose('goreNotice', { open: false, gore });
    this.scene.input.keyboard?.off('keydown', this.onKey);
    this.scene.tweens.add({
      targets: this.box,
      alpha: 0,
      duration: 400,
      onComplete: () => {
        this.box.destroy();
        this.onDone();
      },
    });
  }

  destroy(): void {
    this.done = true;
    this.scene.input.keyboard?.off('keydown', this.onKey);
    this.box.destroy();
  }
}

/** localStorage (막힌 환경이면 null) */
export function safeStorage(): Storage | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null;
  } catch {
    return null;
  }
}
