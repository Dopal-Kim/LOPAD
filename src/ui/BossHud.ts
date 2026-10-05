import Phaser from 'phaser';
import { UI_SCREEN, type UiSnapshot } from '../contract/ui';
import {
  breakLabelKey,
  candleGuides,
  phaseNameOf,
  phaseNamesFor,
  phaseStrip,
  readBoss,
  readBossBreak,
  readBossEvent,
  tickXs,
  type BossLook,
} from './bossView';
import { bossLeft } from './combatView';
import { debugExpose } from './debug';
import { GlowText } from './glow';
import { Gauge, ICON, SLICE, icon } from './kit';
import { swatch } from './StructureHud';
import { fill, storyText } from './text';
import { BOSS_DARK_PHASE_BY_FLOOR, BOSS_UI as B } from './themeStory';
import { TimedCard, cardTotalMs } from './timedCard';
import { sequenceExtend, sequenceGone, sequenceShown } from './uiSequence';

/** 보스 막대 높이 (보스 틀 9-slice) */
const BAR_H = SLICE.gaugeBoss.h;
/** 처치 카드 메뉴 차례 이름 (uiSequence) */
export const BOSS_DEFEAT_SEQ = 'bossDefeat';

type Glow = Parameters<GlowText['setGlowStyle']>[0];

/**
 * 61라운드 단계 3 보스 UI (P6·P10, 플레이 점검 #5·#6) — CombatHud 에서 보스 막대를 옮겨 와 한 곳에 모았다.
 *  - 보스 막대 (아래 가운데, 전투 묶음과 겹치면 비킴): 이름 · 국면 이름, **국면 눈금**(1층 65%·30%), 무너진 동안 '무너짐' 깜빡임.
 *  - 이름 카드 (BOSS_ROAR — 61 단계 4, 등장 연출의 포효 순간. BOSS_STARTED 때는 띄우지 않는다): 층 제목(흐림) · 보스 이름 2배 · 괘선 ·
 *    국면 띠 '얼큰 → 만취 → 인사불성'.
 *  - 국면 카드 (BOSS_PHASE): 'n국면' · 국면 이름 2배 · 국면 띠 (어둠 국면이면 촛대 안내 한 줄).
 *  - 파훼·결정타 문구 (BOSS_BREAK, 계약 추가 예정): '파훼' 2배 + 파훼 이름 · '무너진 동안 더 아프다' / '결정타'.
 *  - 촛대 안내 (어둠 국면, 스냅샷 `boss.candles` 가 있을 때): 화면 안 꺼진 촛대 위 까딱이는 표지, 화면 밖은 가장자리 화살.
 *  - 처치 카드 (BOSS_DIED): 어둠 띠 + 이름 + '쓰러졌다'. 카드가 끝날 때까지 보상 메뉴가 기다린다(uiSequence, 처치에서 최대 4.5초).
 * 새 값은 `bossView.ts` 가 있으면 쓰고 없으면 기본값으로 읽는다(시스템 D 가 계약에 넣기 전에도 동작).
 */
export class BossHud {
  private si: number;
  private gauge: Gauge;
  private bossIcon: Phaser.GameObjects.Image;
  private nameText: GlowText;
  private brokenText: GlowText;
  private ticks: Phaser.GameObjects.Graphics;
  private candles: Phaser.GameObjects.Graphics;
  private barX = 0;
  private tickSig = '';
  private candleSig = '';
  private nameCard?: TimedCard;
  private phaseCard?: TimedCard;
  private stamp?: TimedCard;
  private defeat?: TimedCard;
  private band?: Phaser.GameObjects.Graphics;
  /** 처치 시각 (보스 대사·한마디가 이어지면 메뉴 기다림을 늘인다) */
  private defeatAt = -1;

  constructor(
    private scene: Phaser.Scene,
    stageIndex: number,
  ) {
    this.si = stageIndex;
    this.gauge = new Gauge(scene, 0, 0, B.barW, 'health').setVisible(false);
    this.ticks = scene.add.graphics();
    this.bossIcon = icon(scene, 0, 0, ICON.boss).setVisible(false);
    this.nameText = new GlowText(scene, 0, 0, '', 'ink_accent', { stageIndex }).setVisible(false);
    this.brokenText = new GlowText(scene, 0, 0, storyText('brokenTag'), 'ink_body', { stageIndex }).setVisible(false);
    this.candles = scene.add.graphics().setDepth(B.depth - 1);
  }

  /** 보스 막대가 보이는가 */
  get on(): boolean {
    return this.nameText.visible;
  }

  /** 막대 위 이름 줄 위 끝 (자막을 그 위에) */
  get top(): number {
    return this.nameText.y - 4;
  }

  /** 막대가 아직 안 그려졌지만 곧 그려질 때(BOSS_STARTED 프레임) 자막이 비킬 높이 */
  static readonly reserveH = BAR_H + 22;

  setStageIndex(si: number): void {
    if (si === this.si) return;
    this.si = si;
    this.nameText.setStageIndex(si);
    this.brokenText.setStageIndex(si);
    this.tickSig = '';
  }

  render(s: UiSnapshot, now: number, bundleRight: number, overlay: boolean): void {
    const look = readBoss(s.boss, this.si, storyText('phaseN'));
    const on = Boolean(look);
    this.gauge.setVisible(on);
    this.bossIcon.setVisible(on);
    this.nameText.setVisible(on);
    this.ticks.setVisible(on);
    if (!look) {
      this.brokenText.setVisible(false);
      this.drawCandles(null, now, false);
      return;
    }
    const bx = bossLeft(UI_SCREEN.WIDTH, B.barW, bundleRight, B.barGap);
    const by = UI_SCREEN.HEIGHT - B.barBottom - BAR_H;
    if (bx !== this.barX) {
      this.barX = bx;
      this.gauge.setPositionX(bx);
    }
    this.gauge.setPositionY(by).set(look.ratio);
    this.bossIcon.setPosition(bx - 22, by - 1);
    const label = look.name ? fill(storyText('barName'), { name: look.name, phase: look.phaseName }) : look.phaseName;
    this.nameText.setText(label).placeCenter(bx + B.barW / 2, by - 18);
    // 무너진 동안: 이름 줄 오른쪽에 '무너짐' 깜빡임 (받는 피해 증가 — P6)
    const broken = Boolean(look.broken);
    this.brokenText.setVisible(broken);
    if (broken) {
      const blink = Math.floor(now / B.brokenBlinkMs) % 2 === 0;
      this.brokenText
        .setGlowStyle(blink ? 'ink_accent' : 'ink_body')
        .setPosition(this.nameText.x + this.nameText.displayWidth + 6, this.nameText.y);
    }
    this.drawTicks(look, bx, by);
    this.drawCandles(look, now, !overlay);
  }

  /** BOSS_STARTED: 지난 보스전 카드만 치운다 — 이름 카드는 포효(BOSS_ROAR) 때 (61 단계 4 §17.1) */
  started(): void {
    this.clearCards();
    debugExpose('bossCard', null);
  }

  /** BOSS_ROAR `{ name }`: 이름 카드 (층 제목 · 이름 · 국면 띠). 등장 연출의 포효 프레임에 한 번 (introMs 0 이면 시작 직후) */
  roared(p: unknown, s: UiSnapshot): void {
    const e = readBossEvent(p);
    const name = e.name || s.boss?.name || '';
    if (!name) return;
    this.clearCards();
    const given = p && typeof p === 'object' && typeof (p as { phase?: unknown }).phase === 'number';
    const phase = given ? e.phase : Math.max(1, Math.round(s.boss?.phase ?? 1));
    const names = phaseNamesFor(this.si, (s.boss as unknown as { phaseNames?: unknown } | null)?.phaseNames);
    const box = this.scene.add.container(0, B.nameCard.top).setDepth(B.depth);
    let y = 0;
    const floor = s.floorTitle || s.stageName;
    if (floor) y = this.addCentered(box, floor, 'ink_faint', y, 1) + 4;
    y = this.addCentered(box, name, 'ink_accent', y, 2) + 4;
    const g = this.scene.add.graphics();
    g.fillStyle(swatch(this.scene, this.si, { slot: 20 }), 1).fillRect(
      Math.round(UI_SCREEN.WIDTH / 2 - B.nameCard.ruleW / 2),
      y,
      B.nameCard.ruleW,
      1,
    );
    box.add(g);
    y += 6;
    if (names.length > 1) y = this.addStrip(box, names, phase, y);
    this.addBand(box, y);
    this.nameCard = new TimedCard(this.scene, box, B.nameCard);
    debugExpose('bossCard', { kind: 'name', name, phase });
  }

  /** BOSS_PHASE: 국면 카드 (1국면은 이름 카드가 대신한다) */
  phase(p: unknown, s: UiSnapshot): void {
    const e = readBossEvent(p);
    if (e.phase <= 1) return;
    const names = phaseNamesFor(this.si, (s.boss as unknown as { phaseNames?: unknown } | null)?.phaseNames);
    const phaseName = e.phaseName ?? phaseNameOf(e.phase, names, storyText('phaseN'));
    this.nameCard?.cancel();
    this.phaseCard?.cancel();
    const box = this.scene.add.container(0, B.phaseCard.top).setDepth(B.depth);
    let y = this.addCentered(box, fill(storyText('phaseOrdinal'), { n: e.phase }), 'ink_faint', 0, 1) + 2;
    y = this.addCentered(box, phaseName, 'ink_accent', y, 2) + 6;
    if (names.length > 1) y = this.addStrip(box, names, e.phase, y) + 6;
    const dark = BOSS_DARK_PHASE_BY_FLOOR[this.si];
    if (dark !== undefined && e.phase === dark) y = this.addCentered(box, storyText('darkHint'), 'ink_body', y, 1);
    this.addBand(box, y);
    this.phaseCard = new TimedCard(this.scene, box, B.phaseCard);
    debugExpose('bossCard', { kind: 'phase', phase: e.phase, name: phaseName });
  }

  /** BOSS_BREAK: 파훼 · 결정타 문구 (가운데 위, 짧게 흔들림) */
  broke(p: unknown): void {
    const v = readBossBreak(p);
    if (!v) return;
    this.stamp?.cancel();
    const box = this.scene.add.container(0, B.breakStamp.top).setDepth(B.depth + 1);
    const head = v.finisher ? storyText('finisherHead') : storyText('breakHead');
    let y = this.addCentered(box, head, 'ink_accent', 0, 2) + 2;
    const label = v.finisher ? null : (v.label ?? storyText(breakLabelKey(v.kind)));
    const sub = v.text ?? (v.finisher ? storyText('finisherSub') : storyText('breakSub'));
    if (label) y = this.addCentered(box, label, 'ink_body', y, 1) + 2;
    this.addCentered(box, sub, 'ink_faint', y, 1);
    this.stamp = new TimedCard(this.scene, box, B.breakStamp);
    // 찍힌 직후 짧게 좌우 흔들림 (정수 px)
    const t0 = this.scene.time.now;
    const shake = this.scene.time.addEvent({
      delay: B.breakStamp.shakeMs,
      loop: true,
      callback: () => {
        const el = this.scene.time.now - t0 - B.breakStamp.inMs;
        if (!box.active || el > B.breakStamp.shakeForMs) {
          if (box.active) box.setX(0);
          shake.remove();
          return;
        }
        if (el >= 0) box.setX(box.x === 0 ? B.breakStamp.shakeAmp : box.x > 0 ? -B.breakStamp.shakeAmp : 0);
      },
    });
    debugExpose('bossCard', { kind: v.finisher ? 'finisher' : 'break', label, sub });
  }

  /** BOSS_DIED: 처치 카드 — 끝날 때까지 보상 메뉴가 기다린다 (uiSequence, 처치에서 최대 menuWaitMaxMs) */
  died(p: unknown, s: UiSnapshot, finisherSeen: boolean): void {
    const e = readBossEvent(p);
    const name = e.name || s.boss?.name || '';
    this.clearCards();
    const D = B.defeat;
    const band = this.scene.add.graphics().setDepth(B.depth - 1);
    band.fillStyle(swatch(this.scene, this.si, { gray: 0 }), 0.5).fillRect(0, D.top - 14, UI_SCREEN.WIDTH, D.bandH);
    band.setAlpha(0);
    this.scene.tweens.add({ targets: band, alpha: 1, duration: D.inMs });
    this.band = band;
    const box = this.scene.add.container(0, D.top).setDepth(B.depth);
    let y = 0;
    if (name) y = this.addCentered(box, name, 'ink_accent', y, 2) + 4;
    const g = this.scene.add.graphics();
    g.fillStyle(swatch(this.scene, this.si, { slot: 20 }), 1).fillRect(
      Math.round(UI_SCREEN.WIDTH / 2 - D.ruleW / 2),
      y,
      D.ruleW,
      1,
    );
    box.add(g);
    y += 6;
    const line = e.finisher || finisherSeen ? storyText('defeatFinisher') : storyText('defeatLine');
    this.addCentered(box, line, 'ink_body', y, 1);
    this.defeatAt = this.scene.time.now;
    this.defeat = new TimedCard(this.scene, box, D, () => {
      this.defeat = undefined;
      this.fadeBand();
    });
    sequenceShown(BOSS_DEFEAT_SEQ, cardTotalMs(D), { deadlineMs: B.menuWaitMaxMs });
    debugExpose('bossCard', { kind: 'defeat', name, line });
  }

  /** 처치 뒤 이어지는 보스 대사·원한의 한마디가 뜨면 메뉴 기다림을 늘인다 (처치에서 menuWaitMaxMs 안) */
  storyShown(holdMs: number): void {
    if (this.defeatAt < 0 || this.scene.time.now - this.defeatAt > B.menuWaitMaxMs) return;
    sequenceExtend(BOSS_DEFEAT_SEQ, holdMs);
  }

  reset(): void {
    this.clearCards();
    this.drawCandles(null, 0, false);
  }

  destroy(): void {
    this.clearCards();
  }

  // ---- 그리기 조각

  /** 가운데 맞춘 발광 글 한 줄을 넣고 아래 끝 y 를 돌려준다 */
  private addCentered(box: Phaser.GameObjects.Container, text: string, style: Glow, y: number, scale: 1 | 2): number {
    const t = new GlowText(this.scene, 0, y, text, style, { scale, stageIndex: this.si });
    t.placeCenter(UI_SCREEN.WIDTH / 2, y);
    box.add(t);
    return y + t.displayHeight;
  }

  /** 국면 띠 '얼큰 → 만취 → 인사불성' (지금 = 강조, 지난 = 흐림, 다음 = 본문) — 아래 끝 y */
  private addStrip(box: Phaser.GameObjects.Container, names: string[], phase: number, y: number): number {
    const items = phaseStrip(names, phase);
    const words = items.map((it) => {
      const style: Glow = it.state === 'now' ? 'ink_accent' : it.state === 'past' ? 'ink_faint' : 'ink_body';
      return new GlowText(this.scene, 0, y, it.text, style, { stageIndex: this.si });
    });
    // 낱말 사이 픽셀 화살 (Galmuri 에 '→' 글리프가 없다) — 간격 + 화살 폭 + 간격
    const A = B.stripArrowW;
    const gap = B.stripGap;
    const w = words.reduce((a, t) => a + t.displayWidth, 0) + (words.length - 1) * (gap * 2 + A);
    let x = Math.round(UI_SCREEN.WIDTH / 2 - w / 2);
    const g = this.scene.add.graphics();
    const h = words[0]?.displayHeight ?? 0;
    const midY = y + Math.round(h / 2);
    const ink = swatch(this.scene, this.si, { gray: 0 });
    const col = swatch(this.scene, this.si, { gray: B.stripArrowGray });
    words.forEach((t, i) => {
      t.setX(x);
      x += t.displayWidth;
      if (i < words.length - 1) {
        const ax = x + gap;
        // 그늘 1px 둘레 + 몸통 (가로 줄 + 머리 3단)
        g.fillStyle(ink, 1)
          .fillRect(ax - 1, midY - 1, A - 1, 3)
          .fillRect(ax + A - 4, midY - 3, 3, 7);
        g.fillStyle(col, 1)
          .fillRect(ax, midY, A - 2, 1)
          .fillRect(ax + A - 4, midY - 2, 1, 5)
          .fillRect(ax + A - 3, midY - 1, 1, 3)
          .fillRect(ax + A - 2, midY, 1, 1);
        x += gap * 2 + A;
      }
    });
    box.add([g, ...words]);
    return y + h;
  }

  /** 카드 뒤 어둠 띠 (월드 글·그림 위에서도 읽히게, G00 α0.5) — 카드와 함께 사라진다 */
  private addBand(box: Phaser.GameObjects.Container, h: number): void {
    const g = this.scene.add.graphics();
    g.fillStyle(swatch(this.scene, this.si, { gray: 0 }), 0.5).fillRect(
      0,
      -B.bandPad,
      UI_SCREEN.WIDTH,
      h + B.bandPad * 2,
    );
    box.addAt(g, 0);
  }

  /** 국면 눈금: 막대 위로 튀어나온 1px 선 (아직 = 강조 22, 지남 = 무채) */
  private drawTicks(look: BossLook, bx: number, by: number): void {
    const inner = SLICE.gaugeBoss.fillInsetX;
    const ticks = tickXs(look.marks, bx + inner, B.barW - inner * 2, look.ratio);
    const sig = `${bx}|${by}|${this.si}|${ticks.map((t) => `${t.x}${t.passed ? 'p' : ''}`).join(',')}`;
    if (sig === this.tickSig) return;
    this.tickSig = sig;
    const g = this.ticks.clear();
    for (const t of ticks) {
      const c = t.passed
        ? swatch(this.scene, this.si, { gray: B.tickPassedGray })
        : swatch(this.scene, this.si, { slot: B.tickSlot });
      g.fillStyle(swatch(this.scene, this.si, { gray: 0 }), 1).fillRect(t.x - 1, by - B.tickOut, 3, B.tickOut + BAR_H);
      g.fillStyle(c, 1).fillRect(t.x, by - B.tickOut, 1, B.tickOut + BAR_H);
    }
  }

  /** 촛대 안내: 어둠 국면 + 촛대 값이 있을 때만 (까딱임 주기마다 다시 그림) */
  private drawCandles(look: BossLook | null, now: number, show: boolean): void {
    const C = B.candle;
    const guides =
      show && look?.dark ? candleGuides(look.candles, { w: UI_SCREEN.WIDTH, h: UI_SCREEN.HEIGHT }, C.edge) : [];
    const bob = Math.floor(now / C.bobMs) % 2;
    const sig = guides.length ? `${bob}|${this.si}|${guides.map((g) => `${g.kind}${g.x},${g.y}`).join(';')}` : '';
    if (sig === this.candleSig) return;
    this.candleSig = sig;
    const g = this.candles.clear();
    debugExpose('bossCandles', guides);
    if (!guides.length) return;
    const lit = swatch(this.scene, this.si, { slot: C.slot });
    const ink = swatch(this.scene, this.si, { gray: 0 });
    const flame = swatch(this.scene, this.si, { slot: C.hintSlot });
    const a = C.arrow;
    for (const v of guides) {
      if (v.kind === 'mark') {
        // 촛대 위 아래 꼭지 세모 (까딱임 1px) + 작은 불씨 점
        const y = v.y - C.markUp - bob;
        g.fillStyle(ink, 1).fillTriangle(v.x - a - 1, y - 1, v.x + a + 1, y - 1, v.x, y + a + 1);
        g.fillStyle(lit, 1).fillTriangle(v.x - a, y, v.x + a, y, v.x, y + a);
        g.fillStyle(flame, 1).fillRect(v.x - 1, y - 4, 2, 2);
        continue;
      }
      // 화면 밖: 가장자리에서 촛대 쪽을 가리키는 세모 + 안쪽 불씨 점
      const px = -v.dy;
      const py = v.dx;
      const tipX = Math.round(v.x + v.dx * (a + bob));
      const tipY = Math.round(v.y + v.dy * (a + bob));
      const bx1 = Math.round(v.x - v.dx * a + px * a);
      const by1 = Math.round(v.y - v.dy * a + py * a);
      const bx2 = Math.round(v.x - v.dx * a - px * a);
      const by2 = Math.round(v.y - v.dy * a - py * a);
      g.lineStyle(2, ink, 1).strokeTriangle(tipX, tipY, bx1, by1, bx2, by2);
      g.fillStyle(lit, 1).fillTriangle(tipX, tipY, bx1, by1, bx2, by2);
      const fx = Math.round(v.x - v.dx * (a + 5));
      const fy = Math.round(v.y - v.dy * (a + 5));
      g.fillStyle(ink, 1).fillRect(fx - 2, fy - 3, 4, 5);
      g.fillStyle(flame, 1).fillRect(fx - 1, fy - 2, 2, 3);
    }
  }

  private fadeBand(): void {
    const band = this.band;
    if (!band) return;
    this.band = undefined;
    this.scene.tweens.add({ targets: band, alpha: 0, duration: B.defeat.outMs, onComplete: () => band.destroy() });
  }

  private clearCards(): void {
    this.nameCard?.cancel();
    this.phaseCard?.cancel();
    this.stamp?.cancel();
    this.defeat?.cancel();
    this.nameCard = this.phaseCard = this.stamp = this.defeat = undefined;
    if (this.band) {
      this.scene.tweens.killTweensOf(this.band);
      this.band.destroy();
      this.band = undefined;
    }
    if (this.defeatAt >= 0) sequenceGone(BOSS_DEFEAT_SEQ);
    this.defeatAt = -1;
  }
}
