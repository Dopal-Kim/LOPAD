import Phaser from 'phaser';
import { UI_EVENTS, UI_SCREEN, type UiSnapshot } from '../contract/ui';
import { GlowText } from './glow';
import { buildOf } from './buildView';
import { lookImage, pairPips, scaledKey, traitIconCard, traitIconOuter } from './growthArt';
import { iconWeapon, readAwaken, readResonance, readTrait, verbKey } from './growthView';
import { inkPanel } from './kit';
import { swatch } from './StructureHud';
import { fill, growthText } from './text';
import { GRAY, hexToNum } from './theme';
import { GROWTH_BANNER as BN, RESONANCE_UI as RS, TRAIT_ICON as TI } from './themeGrowth';
import { TimedCard } from './timedCard';
import type { AlertSpec } from './HudAlerts';
import type { AlertKind } from './alertPlan';
import { WEAPON_HUE } from './themeWeapon';
import { voiceWeapon } from './storyView';

/** 62 P0-6: 개성 알림 key (같은 개성의 옛 진화 배너 `WEAPON_EVOLVED` 와 한 장으로 합친다) */
export function traitAlertKey(name: string): string {
  return `trait:${name.split(' — ')[0].trim()}`;
}

/**
 * 각성 배너 (`ui:awaken` — 시스템이 게임을 0.8/1.0초 멈추는 동안과 그 뒤): 어둠 띠 + '1차 각성'(흐림) + 무기 모양 그림 +
 * 이름 2배(강조) + 한 줄. 개성 알림 (`ui:trait-gained`): 위 가운데 잉크 칩 — 키 그림 · '개성 발현 · 이름' · 한 문장.
 * 62 P0-6: 개성·공명 알림은 위 가운데 알림 줄(`HudAlerts`, 종류 'growth')로 — 같은 개성의 진화 배너와 합쳐 한 장만.
 * 각성 배너는 큰 순간이라 따로 그리고, 뜰 때 알림 줄을 비운다(보스 카드만 남김).
 */
export class GrowthLayer {
  private banner?: TimedCard;
  private band?: Phaser.GameObjects.Graphics;

  constructor(
    private scene: Phaser.Scene,
    private deps: {
      gain: (now: number) => void;
      snapshot: () => UiSnapshot;
      alert: (spec: AlertSpec) => void;
      clearAlerts: (keep?: readonly AlertKind[]) => void;
    },
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
    this.deps.clearAlerts(['boss']);
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
    // 61 단계 6 (P14 §2): 띠 위·아래 1px 무기 색
    const hue = hexToNum(
      WEAPON_HUE[voiceWeapon(this.deps.snapshot().growth?.weaponName, this.deps.snapshot().weapon?.name)].main,
    );
    band
      .fillStyle(hue, 1)
      .fillRect(0, BN.awaken.top - 10, W, 1)
      .fillRect(0, BN.awaken.top + y + 9, W, 1);
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
    const snap = this.deps.snapshot();
    const vk = verbKey(t.verb, snap.weaponVerbs);
    const head = `${growthText('traitGained')} · ${t.name}`;
    const weapon = iconWeapon(t.icon, snap.weapon?.name, snap.growth?.weaponName);
    // 같은 개성의 진화 배너가 먼저 와 있으면 이 칩으로 바꾼다 (merge 없음 = 바꿈)
    this.deps.alert({
      kind: 'growth',
      key: traitAlertKey(t.name),
      label: head,
      timing: { ...BN.trait },
      build: () => this.chip(t.icon, weapon, head, vk ? { key: vk.key, label: vk.name } : null, t.line),
    });
  }

  /** 옛 `WEAPON_EVOLVED` 배너 (개성 칩과 같은 key — 칩이 있으면 버리고, 없으면 짧은 칩) */
  evolved(text: string): void {
    const name = text.trim();
    if (!name) return;
    this.deps.alert({
      kind: 'growth',
      key: traitAlertKey(name),
      label: name,
      timing: { ...BN.trait },
      build: () => this.chip(null, 'katana', name, null, ''),
      merge: (prev) => prev,
    });
  }

  /**
   * §18.1 공명 알림 (`ui:resonance` — 개성 알림과 같은 틀): 그림(`iconKey`, 없으면 짝 마름모 ◆◆) · '공명 · 이름' ·
   * '연쇄 개성 두 장이 엮였다' · 한 문장. 개성 알림과 같은 때 오면 알림 줄이 그 아래에 쌓는다.
   */
  resonance(p: unknown): void {
    const snap = this.deps.snapshot();
    const r = readResonance(p, buildOf(snap));
    if (!r) return;
    const weapon = iconWeapon(r.icon, snap.weapon?.name, snap.growth?.weaponName);
    const sub = r.tag ? fill(growthText('resPair'), { tag: r.tag }) : '';
    const head = `${growthText('resGained')} · ${r.name}`;
    this.deps.alert({
      kind: 'growth',
      key: `res:${r.name}`,
      label: head,
      timing: { ...BN.trait },
      build: () => this.chip(r.icon, weapon, head, null, r.line, sub, true),
    });
  }

  /**
   * 알림 칩 하나 (개성·공명 공용). 그림이 있으면 왼쪽에 그림 칸, 없으면 머리 앞에 키(개성) 또는 짝 마름모(공명).
   * 글: 머리(강조) / 둘째 줄(흐림 — 그림 칩의 키 줄 또는 공명 짝) / 한 문장.
   */
  private chip(
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
    const box = sc.add.container(Math.round(W / 2 - w / 2), 0, parts);
    return { box, h };
  }

  clear(): void {
    this.clearBanner();
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
