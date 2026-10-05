import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, type UiGrowth, type UiSnapshot } from '../contract/ui';
import { GlowText } from './glow';
import { diamond, lookImage, scaledKey } from './growthArt';
import { gaugeLayout, readAwaken, readTrait, remainText, verbKey } from './growthView';
import { inkPanel } from './kit';
import { swatch } from './StructureHud';
import { growthText } from './text';
import { GRAY, hexToNum } from './theme';
import { GROWTH_BANNER as BN, GROWTH_HUD as G } from './themeGrowth';
import { TimedCard } from './timedCard';

/**
 * 61 단계 4 P12 HUD 각성 게이지 한 줄 (전투 묶음 무기·자원 줄 아래, 옛 2px 개성 진행선 대체):
 * 아이콘 칸 마름모 · 게이지 숫자 · 막대 + 눈금(작은 ◇ 개성 발현·단련 / 큰 ◆ 1차·2차 각성 — 지난 것 채움, 다음 것 밝은 테) ·
 * '1차 각성까지 40'. `ui:growth-gain` 이면 찬 부분이 하얗게 한 번 반짝이고 숫자가 잠깐 강조색.
 */
export class GrowthGauge {
  private icon: Phaser.GameObjects.Graphics;
  private num: GlowText;
  private bar: Phaser.GameObjects.Graphics;
  private flash: Phaser.GameObjects.Graphics;
  private rem: GlowText;
  private sig = '';
  private accentUntil = 0;
  private lastFill = { x: 0, y: 0, w: 0 };

  constructor(private scene: Phaser.Scene) {
    this.icon = scene.add.graphics();
    this.num = new GlowText(scene, 0, 0, '', 'ink_body');
    this.bar = scene.add.graphics();
    this.flash = scene.add.graphics().setAlpha(0);
    this.rem = new GlowText(scene, 0, 0, '', 'ink_faint');
  }

  /** 줄 왼쪽 위 (x = 아이콘 칸 왼쪽), 아이콘 칸 폭. 오른쪽 끝 x 를 돌려준다 (growth 가 null 이면 숨기고 x) */
  render(g: UiGrowth | null | undefined, x: number, y: number, iconCol: number, now: number): number {
    const on = Boolean(g);
    for (const o of [this.icon, this.num, this.bar, this.rem]) o.setVisible(on);
    if (!g) {
      this.flash.setVisible(false);
      return x;
    }
    this.flash.setVisible(true);
    this.num
      .setText(String(Math.max(0, Math.floor(g.gauge))))
      .setGlowStyle(now < this.accentUntil ? 'ink_accent' : 'ink_body')
      .setPosition(x + iconCol, y);
    const bx = Math.round(this.num.x + this.num.displayWidth + G.gap);
    const layout = gaugeLayout(g, G.barW, G.bigTickR);
    this.rem.setText(remainText(layout.remain, growthText)).setPosition(bx + G.barW + G.gap, y);
    const sig = `${x}|${y}|${bx}|${layout.fillW}|${layout.ticks.map((t) => `${t.x}${t.state}`).join(',')}`;
    if (sig !== this.sig) {
      this.sig = sig;
      this.draw(layout, x, y, bx, iconCol);
    }
    return this.rem.x + this.rem.displayWidth;
  }

  /** ui:growth-gain: 짧은 반짝 */
  gain(now: number): void {
    this.accentUntil = now + G.numAccentMs;
    const f = this.lastFill;
    if (f.w <= 0) return;
    this.scene.tweens.killTweensOf(this.flash);
    this.flash
      .clear()
      .fillStyle(hexToNum(GRAY[15]), 1)
      .fillRect(f.x, f.y - 1, f.w, G.barH + 2)
      .setAlpha(G.flashAlpha);
    this.scene.tweens.add({ targets: this.flash, alpha: 0, duration: G.flashMs });
  }

  setDepth(d: number): this {
    for (const o of [this.icon, this.num, this.bar, this.flash, this.rem]) o.setDepth(d);
    return this;
  }

  private draw(layout: ReturnType<typeof gaugeLayout>, x: number, y: number, bx: number, iconCol: number): void {
    const sc = this.scene;
    const cy = y + G.barY + Math.floor(G.barH / 2);
    // 아이콘 칸: 큰 마름모 (채움 = 강조 25, 테 = G00)
    const ic = this.icon.clear();
    const icx = x + Math.floor((iconCol - 4) / 2);
    diamond(ic, icx, cy, 5, swatch(sc, 0, { slot: G.bigDoneSlot }), true);
    diamond(ic, icx, cy, 5, hexToNum(GRAY[0]), false);
    const g = this.bar.clear();
    g.fillStyle(swatch(sc, 0, { gray: G.trackGray }), 1).fillRect(bx, y + G.barY, G.barW, G.barH);
    if (layout.fillW > 0)
      g.fillStyle(swatch(sc, 0, { slot: G.fillSlot }), 1).fillRect(bx, y + G.barY, layout.fillW, G.barH);
    this.lastFill = { x: bx, y: y + G.barY, w: layout.fillW };
    for (const t of layout.ticks) {
      const r = t.big ? G.bigTickR : G.tickR;
      const tx = bx + t.x;
      // 바탕 G00 로 한 겹 깔아 막대 위에서 또렷하게
      diamond(g, tx, cy, r + 1, hexToNum(GRAY[0]), true);
      if (t.state === 'done') diamond(g, tx, cy, r, swatch(sc, 0, { slot: t.big ? G.bigDoneSlot : G.doneSlot }), true);
      else {
        const edge = t.state === 'next' ? { slot: G.nextSlot } : t.big ? { slot: G.bigTodoSlot } : { gray: G.todoGray };
        diamond(g, tx, cy, r, swatch(sc, 0, edge), false);
      }
    }
  }
}

/**
 * 각성 배너 (`ui:awaken` — 시스템이 게임을 0.8/1.0초 멈추는 동안과 그 뒤): 어둠 띠 + '1차 각성'(흐림) + 무기 모양 그림 +
 * 이름 2배(강조) + 한 줄. 개성 알림 (`ui:trait-gained`): 위 가운데 잉크 칩 — 키 그림 · '개성 발현 · 이름' · 한 문장.
 */
export class GrowthLayer {
  private banner?: TimedCard;
  private band?: Phaser.GameObjects.Graphics;
  private toast?: TimedCard;

  constructor(
    private scene: Phaser.Scene,
    private deps: { gain: (now: number) => void; snapshot: () => UiSnapshot },
  ) {}

  subscribe(on: <T>(event: string, handler: (p: T) => void) => void): void {
    on(UI_EVENTS.GROWTH_GAIN, () => this.deps.gain(this.scene.time.now));
    on(UI_EVENTS.AWAKEN, (p: unknown) => this.awaken(p));
    on(UI_EVENTS.TRAIT_GAINED, (p: unknown) => this.trait(p));
    for (const e of [UI_EVENTS.RUN_ENDED, UI_EVENTS.STAGE_STARTED]) on(e, () => this.clear());
  }

  awaken(p: unknown): void {
    const a = readAwaken(p);
    if (!a) return;
    this.clearBanner();
    const sc = this.scene;
    const W = UI_SCREEN.WIDTH;
    const box = sc.add.container(0, BN.awaken.top).setDepth(BN.depth);
    let y = 0;
    const head = new GlowText(sc, 0, 0, growthText(a.stage === 2 ? 'bannerAwaken2' : 'bannerAwaken1'), 'ink_faint');
    head.placeCenter(W / 2, y);
    box.add(head);
    y += head.displayHeight + 4;
    const img = lookImage(sc, a.look, W / 2, y, 160, BN.lookMaxH);
    if (img) {
      box.add(img);
      y += BN.lookMaxH + 4;
    }
    const name = new GlowText(sc, 0, 0, a.name, 'ink_accent', { scale: 2 }).placeCenter(W / 2, y);
    box.add(name);
    y += name.displayHeight + 2;
    if (a.line) {
      const line = new GlowText(sc, 0, 0, a.line, 'ink_body', { wrap: 420, align: 'center' }).placeCenter(W / 2, y);
      box.add(line);
      y += line.displayHeight;
    }
    const band = sc.add.graphics().setDepth(BN.depth - 1);
    band.fillStyle(hexToNum(GRAY[0]), 0.5).fillRect(0, BN.awaken.top - 10, W, y + 20);
    band.setAlpha(0);
    sc.tweens.add({ targets: band, alpha: 1, duration: BN.awaken.inMs });
    sc.tweens.add({
      targets: band,
      alpha: 0,
      delay: BN.awaken.inMs + BN.awaken.holdMs,
      duration: BN.awaken.outMs,
    });
    this.band = band;
    this.banner = new TimedCard(sc, box, BN.awaken, () => this.dropBand());
  }

  trait(p: unknown): void {
    const t = readTrait(p);
    if (!t) return;
    this.toast?.cancel();
    const sc = this.scene;
    const W = UI_SCREEN.WIDTH;
    const parts: Phaser.GameObjects.GameObject[] = [];
    const vk = verbKey(t.verb, this.deps.snapshot().weaponVerbs);
    const key = vk ? scaledKey(sc, vk.key, 1) : null;
    const head = new GlowText(sc, 0, 0, `${growthText('traitGained')} · ${t.name}`, 'ink_accent');
    const line = t.line ? new GlowText(sc, 0, 0, t.line, 'ink_body', { wrap: 360 }) : null;
    const keyW = key ? key.width + 6 : 0;
    const innerW = Math.max(keyW + head.displayWidth, line?.displayWidth ?? 0);
    const w = innerW + BN.traitPadX * 2;
    const h = BN.traitPadY * 2 + head.displayHeight + (line ? line.displayHeight + 2 : 0);
    const x0 = Math.round(W / 2 - w / 2);
    const panel = inkPanel(sc, 0, 0, w, Math.max(24, h));
    parts.push(panel);
    let cx = BN.traitPadX;
    if (key) {
      key.obj.setPosition(cx, BN.traitPadY);
      parts.push(key.obj);
      cx += keyW;
    }
    head.setPosition(cx, BN.traitPadY - 1);
    parts.push(head);
    if (line) {
      line.setPosition(BN.traitPadX, BN.traitPadY + head.displayHeight + 1);
      parts.push(line);
    }
    const box = sc.add.container(x0, BN.trait.top, parts).setDepth(BN.depth);
    this.toast = new TimedCard(sc, box, BN.trait);
  }

  clear(): void {
    this.clearBanner();
    this.toast?.cancel();
    this.toast = undefined;
  }

  destroy(): void {
    this.clear();
  }

  private clearBanner(): void {
    this.banner?.cancel();
    this.banner = undefined;
    this.dropBand();
  }

  private dropBand(): void {
    if (!this.band) return;
    this.scene.tweens.killTweensOf(this.band);
    this.band.destroy();
    this.band = undefined;
  }
}
