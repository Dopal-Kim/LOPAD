import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, type UiGrowth, type UiSnapshot } from '../contract/ui';
import { GlowText } from './glow';
import { buildOf } from './buildView';
import { diamond, lookImage, pairPips, scaledKey, traitIconCard, traitIconOuter } from './growthArt';
import { gaugeLayout, iconWeapon, readAwaken, readResonance, readTrait, remainText, verbKey } from './growthView';
import { inkPanel } from './kit';
import { swatch } from './StructureHud';
import { fill, growthText } from './text';
import { GRAY, hexToNum } from './theme';
import { GROWTH_BANNER as BN, GROWTH_HUD as G, RESONANCE_UI as RS, TRAIT_ICON as TI } from './themeGrowth';
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
  /** 개성 알림 아래 끝 (공명 알림이 그 아래에 붙는다) */
  private toastBottom = 0;
  private resToast?: TimedCard;

  constructor(
    private scene: Phaser.Scene,
    private deps: { gain: (now: number) => void; snapshot: () => UiSnapshot },
  ) {}

  subscribe(on: <T>(event: string, handler: (p: T) => void) => void): void {
    on(UI_EVENTS.GROWTH_GAIN, () => this.deps.gain(this.scene.time.now));
    on(UI_EVENTS.AWAKEN, (p: unknown) => this.awaken(p));
    on(UI_EVENTS.TRAIT_GAINED, (p: unknown) => this.trait(p));
    on(UI_EVENTS.RESONANCE, (p: unknown) => this.resonance(p));
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

  /**
   * 개성 알림 (`ui:trait-gained`): 위 가운데 잉크 칩. §18.1 그림이 있으면 [그림 64 · 무기 빛 테두리] 오른쪽에
   * '개성 발현 · 이름' / [키] 동작 / 한 문장, 없으면 지금처럼 [키] '개성 발현 · 이름' / 한 문장.
   */
  trait(p: unknown): void {
    const t = readTrait(p);
    if (!t) return;
    this.toast?.cancel();
    const snap = this.deps.snapshot();
    const vk = verbKey(t.verb, snap.weaponVerbs);
    const head = `${growthText('traitGained')} · ${t.name}`;
    const weapon = iconWeapon(t.icon, snap.weapon?.name, snap.growth?.weaponName);
    const chip = this.chip(BN.trait.top, t.icon, weapon, head, vk ? { key: vk.key, label: vk.name } : null, t.line);
    this.toastBottom = BN.trait.top + chip.h;
    this.toast = new TimedCard(this.scene, chip.box, BN.trait);
  }

  /**
   * §18.1 공명 알림 (`ui:resonance` — 개성 알림과 같은 틀): 그림(`iconKey`, 없으면 짝 마름모 ◆◆) · '공명 · 이름' ·
   * '연쇄 개성 두 장이 엮였다' · 한 문장. 같은 순간 개성 알림이 떠 있으면 그 아래에 붙는다.
   */
  resonance(p: unknown): void {
    const snap = this.deps.snapshot();
    const r = readResonance(p, buildOf(snap));
    if (!r) return;
    this.resToast?.cancel();
    const top = this.toast?.alive ? this.toastBottom + RS.stackGap : BN.trait.top;
    const weapon = iconWeapon(r.icon, snap.weapon?.name, snap.growth?.weaponName);
    const sub = r.tag ? fill(growthText('resPair'), { tag: r.tag }) : '';
    const chip = this.chip(top, r.icon, weapon, `${growthText('resGained')} · ${r.name}`, null, r.line, sub, true);
    this.resToast = new TimedCard(this.scene, chip.box, BN.trait);
  }

  /**
   * 알림 칩 하나 (개성·공명 공용). 그림이 있으면 왼쪽에 그림 칸, 없으면 머리 앞에 키(개성) 또는 짝 마름모(공명).
   * 글: 머리(강조) / 둘째 줄(흐림 — 그림 칩의 키 줄 또는 공명 짝) / 한 문장.
   */
  private chip(
    top: number,
    icon: string | null,
    weapon: Parameters<typeof traitIconCard>[4],
    headText: string,
    key: { key: string; label: string } | null,
    lineText: string,
    subText = '',
    pairMark = false,
  ): { box: Phaser.GameObjects.Container; h: number } {
    const sc = this.scene;
    const W = UI_SCREEN.WIDTH;
    const parts: Phaser.GameObjects.GameObject[] = [];
    const px = BN.traitPadX;
    const py = BN.traitPadY;
    const art = icon && sc.textures.exists(icon) ? traitIconOuter(TI.size, TI.frame) : 0;
    const textX = px + (art ? art + 8 : 0);
    // 머리 앞 표식 (그림이 없을 때만): 키 그림 또는 짝 마름모
    const keyObj = !art && key ? scaledKey(sc, key.key, 1) : null;
    const pipsW = RS.pipR * 4 + RS.pipGap;
    const markW = keyObj ? keyObj.width + 6 : !art && pairMark ? pipsW + 6 : 0;
    const head = new GlowText(sc, 0, 0, headText, 'ink_accent');
    // 그림 칩의 둘째 줄: [키] 동작 이름 (개성) 또는 공명 짝 글
    const rowKey = art && key ? scaledKey(sc, key.key, 1) : null;
    const rowLabel = art && key?.label ? key.label : '';
    const sub = subText || rowLabel ? new GlowText(sc, 0, 0, subText || rowLabel, 'ink_faint') : null;
    const line = lineText ? new GlowText(sc, 0, 0, lineText, 'ink_body', { wrap: art ? 300 : 360 }) : null;
    const subW = (rowKey ? rowKey.width + 5 : 0) + (sub?.displayWidth ?? 0);
    const textW = Math.max(markW + head.displayWidth, subW, line?.displayWidth ?? 0);
    const subH = sub || rowKey ? Math.max(sub?.displayHeight ?? 0, rowKey?.height ?? 0) + 1 : 0;
    const textH = head.displayHeight + subH + (line ? line.displayHeight + 2 : 0);
    const w = textX + textW + px;
    const h = Math.max(24, py * 2 + Math.max(textH, art));
    parts.push(inkPanel(sc, 0, 0, w, h));
    if (art) {
      const o = TI.frame + 1;
      const iconParts = traitIconCard(sc, icon, px + o, Math.round((h - art) / 2) + o, weapon);
      if (iconParts) parts.push(...iconParts);
    }
    let y = py + (art ? Math.max(0, Math.round((art - textH) / 2)) : 0);
    let x = textX;
    if (keyObj) {
      keyObj.obj.setPosition(x, y);
      parts.push(keyObj.obj);
      x += markW;
    } else if (markW) {
      const g = sc.add.graphics();
      pairPips(
        g,
        x + RS.pipR,
        y + Math.round(head.displayHeight / 2),
        2,
        2,
        RS.pipR,
        RS.pipGap,
        swatch(sc, 0, { slot: RS.onSlot }),
        swatch(sc, 0, { slot: RS.onSlot }),
      );
      parts.push(g);
      x += markW;
    }
    head.setPosition(x, y - 1);
    parts.push(head);
    y += head.displayHeight;
    if (subH) {
      let sx = textX;
      if (rowKey) {
        rowKey.obj.setPosition(sx, y);
        parts.push(rowKey.obj);
        sx += rowKey.width + 5;
      }
      if (sub) {
        sub.setPosition(sx, y);
        parts.push(sub);
      }
      y += subH;
    }
    if (line) {
      line.setPosition(art ? textX : px, y + 1);
      parts.push(line);
    }
    const box = sc.add.container(Math.round(W / 2 - w / 2), top, parts).setDepth(BN.depth);
    return { box, h };
  }

  clear(): void {
    this.clearBanner();
    this.toast?.cancel();
    this.toast = undefined;
    this.resToast?.cancel();
    this.resToast = undefined;
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
